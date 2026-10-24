"""Accord F16: Small -> Chestnut restart after the Chestnut re-enumerates mid-drive."""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import signal
import unittest

from openpilot.common.hardware.usb import CHESTNUT_USB_PRODUCT
from openpilot.starpilot.models import egpu_return as er
from openpilot.starpilot.models.egpu_return import EgpuReturn, chestnut_usb_identity
from openpilot.starpilot.models.recovery import STARTUP_FALLBACK_EXIT
from openpilot.starpilot.models.recovery_process import ModeldProcess
from openpilot.starpilot.models.status import ModelVariant
from openpilot.starpilot.models.tests.test_recovery import BASE
from openpilot.starpilot.models.tests.test_recovery_process import Feed

S = 1_000_000_000
OLD, NEW = ('4-1', 4, 2), ('4-1', 4, 3)
YES = lambda: True  # noqa: E731


def ready(owner, t0=0., chestnut=NEW, safe=True, small=True, big=YES):
  """Feed 2 Hz ticks for 15 s; returns the first tick time that asked for a restart."""
  for i in range(31):
    t = t0 + i * .5
    if owner.step(BASE + int(t * S), BASE, small, chestnut, safe, big):
      return t
  return None


class TestEgpuReturn(unittest.TestCase):
  def setUp(self):
    patcher = patch.object(er, 'DISABLE_FILE', Path('/nonexistent/egpu_auto_recover_disabled'))
    patcher.start()
    self.addCleanup(patcher.stop)

  def test_new_enumeration_restarts_after_stable_and_safe(self):
    owner = EgpuReturn()
    owner.launched(OLD, small_only=False)
    self.assertEqual(ready(owner), 10.)
    self.assertEqual((owner.attempts, owner.used), (1, NEW))

  def test_chestnut_absent_at_launch_counts_as_new(self):
    owner = EgpuReturn()
    owner.launched(None, small_only=False)
    self.assertEqual(ready(owner), 10.)

  def test_small_only_launch_keeps_the_touched_enumeration(self):
    owner = EgpuReturn()
    owner.launched(OLD, small_only=False)
    owner.launched(NEW, small_only=True)  # stall-path Small started after the Chestnut was already back
    self.assertEqual(ready(owner), 10.)

  def test_same_enumeration_absent_unsafe_big_off_or_disabled_never_restart(self):
    for kwargs in ({'chestnut': OLD}, {'chestnut': None}, {'safe': False}, {'small': False}, {'big': lambda: False}):
      owner = EgpuReturn()
      owner.launched(OLD, small_only=False)
      self.assertIsNone(ready(owner, **kwargs), kwargs)
    owner = EgpuReturn()
    with patch.object(er, 'DISABLE_FILE', Mock(exists=Mock(return_value=True))):
      self.assertIsNone(ready(owner))

  def test_flapping_enumeration_restarts_stability_timer(self):
    owner = EgpuReturn()
    owner.launched(OLD, small_only=False)
    for i in range(20):
      chestnut = ('4-1', 4, 10 + i // 8)  # re-enumerates every 4 s
      self.assertFalse(owner.step(BASE + i * S // 2, BASE, True, chestnut, True, YES))

  def test_engagement_resets_safe_timer(self):
    owner = EgpuReturn()
    for i in range(21):
      self.assertFalse(owner.step(BASE + i * S // 2, BASE, True, NEW, i != 18, YES))
    self.assertFalse(owner.step(BASE + int(11. * S), BASE, True, NEW, True, YES))
    self.assertTrue(owner.step(BASE + int(12.5 * S), BASE, True, NEW, True, YES))

  def test_rate_limit_and_per_drive_budget(self):
    owner = EgpuReturn()
    starts = [ready(owner, t0=60. * k, chestnut=('4-1', 4, 100 + k)) for k in range(10)]
    starts = [t for t in starts if t is not None]
    self.assertEqual(len(starts), er.MAX_ATTEMPTS)
    self.assertTrue(all(b - a >= er.MIN_INTERVAL_NS / S for a, b in zip(starts, starts[1:], strict=False)))
    t = 600.
    # a new drive gets a fresh budget
    self.assertFalse(owner.step(BASE + int(t * S), BASE + 1, True, ('4-1', 4, 999), True, YES))
    self.assertEqual(owner.attempts, 0)

  def test_big_selected_is_read_only_when_everything_else_holds(self):
    owner = EgpuReturn()
    owner.launched(OLD, small_only=False)
    big = Mock(return_value=True)
    for i in range(20):
      owner.step(BASE + i * S // 2, BASE, True, NEW, True, big)
    big.assert_not_called()
    self.assertTrue(owner.step(BASE + 10 * S, BASE, True, NEW, True, big))
    big.assert_called_once_with()

  def test_usb_identity_reads_sysfs(self):
    import tempfile
    with tempfile.TemporaryDirectory() as root:
      for name, vid, pid, product, dev in (('1-1', '3801', 'ddcc', 'panda', 4), ('4-1', '3801', '0001', CHESTNUT_USB_PRODUCT, 7)):
        d = Path(root) / name
        d.mkdir()
        for key, value in (('idVendor', vid), ('idProduct', pid), ('product', product), ('busnum', name[0]), ('devnum', dev)):
          (d / key).write_text(f'{value}\n')
      self.assertEqual(chestnut_usb_identity(Path(root)), ('4-1', 4, 7))
      (Path(root) / '4-1' / 'product').write_text('custom 00000000-DIRTY\n')
      self.assertIsNone(chestnut_usb_identity(Path(root)))


def small_feed(t, engaged=False):
  feed = Feed(t)
  feed['carControl'] = NS(enabled=engaged, latActive=False, longActive=False)
  for d in (feed.seen, feed.valid, feed.alive):
    d['carControl'] = True
  return feed


class TestEgpuRestartWiring(unittest.TestCase):
  def run_ticks(self, owner, child, times, chestnut, engaged=False):
    load = NS(pid=123, process_start_ticks=456, loaded_mono_ns=BASE, variant=ModelVariant.SMALL)
    with patch('openpilot.starpilot.models.recovery_process.process_start_ticks', return_value=456), \
         patch('openpilot.starpilot.models.recovery_process.read_receipt', return_value=load), \
         patch('openpilot.starpilot.models.recovery_process.chestnut_usb_identity', return_value=chestnut), \
         patch('openpilot.starpilot.models.manager.preferences', return_value={'big': 'traintrack'}), \
         patch.object(er, 'DISABLE_FILE', Path('/nonexistent/egpu_auto_recover_disabled')), \
         patch('openpilot.starpilot.models.recovery_process.time.monotonic_ns') as clock, \
         patch.object(owner, 'signal') as send, \
         patch('openpilot.starpilot.models.recovery_process.Process') as spawn:
      for t in times:
        clock.return_value = BASE + int(t * S)
        owner.observe(small_feed(t, engaged), True)
        owner.start()
    return send, spawn

  def latched_owner(self):
    owner = ModeldProcess('modeld', 'module', lambda *args: True)
    child = Mock(pid=123, exitcode=None)
    child.is_alive.return_value = True
    owner.proc = child
    owner.launch_drive_id = BASE
    owner.recovery.drive_id = BASE
    owner.recovery.small_only = True
    owner.recovery.phase = 'small'
    owner.egpu.launched(OLD, small_only=False)
    return owner, child

  def test_restart_clears_latch_and_launches_chestnut_capable(self):
    owner, child = self.latched_owner()
    send, spawn = self.run_ticks(owner, child, [i * .5 for i in range(1, 21)], NEW, engaged=True)
    send.assert_not_called()  # engaged on Small: never pulled
    send, spawn = self.run_ticks(owner, child, [10. + i * .5 for i in range(1, 7)], NEW)  # safe from 10.5 s
    send.assert_not_called()
    send, spawn = self.run_ticks(owner, child, [13.5, 14.], NEW)
    send.assert_called_once_with(signal.SIGINT)
    spawn.assert_not_called()  # nothing new before the Small process exited
    self.assertTrue(owner.recovery.small_only)
    child.is_alive.return_value = False
    child.exitcode = -2
    send, spawn = self.run_ticks(owner, child, [14.5], NEW)
    child.join.assert_called_once_with(timeout=0)
    self.assertFalse(owner.recovery.small_only)
    self.assertEqual((owner.recovery.phase, owner.recovery.drive_id), ('monitor', BASE))
    spawn.assert_called_once()
    self.assertEqual(spawn.call_args.kwargs['args'], ('module', 'modeld', False))
    self.assertEqual(owner.launch_drive_id, BASE)

  def test_failed_chestnut_start_takes_normal_startup_exit_path(self):
    owner, child = self.latched_owner()
    self.run_ticks(owner, child, [i * .5 for i in range(1, 22)], NEW)
    child.is_alive.return_value = False
    child.exitcode = -2
    self.run_ticks(owner, child, [11.], NEW)
    started = owner.proc
    started.pid, started.exitcode = 124, STARTUP_FALLBACK_EXIT
    started.is_alive.return_value = False
    send, spawn = self.run_ticks(owner, started, [60.], NEW)
    self.assertTrue(owner.recovery.small_only)
    self.assertEqual(spawn.call_args.kwargs['args'], ('module', 'modeld', True))
    # same enumeration again: no further restart
    owner.proc.pid, owner.proc.exitcode = 123, None
    owner.proc.is_alive.return_value = True
    send, spawn = self.run_ticks(owner, owner.proc, [300. + i * .5 for i in range(30)], NEW)
    send.assert_not_called()

  def test_stuck_small_gets_sigkill_then_is_left_alone(self):
    owner, child = self.latched_owner()
    send, _ = self.run_ticks(owner, child, [i * .5 for i in range(1, 22)], NEW)
    send.assert_called_once_with(signal.SIGINT)
    send, spawn = self.run_ticks(owner, child, [12.5, 14.5, 16.], NEW)
    self.assertEqual([c.args for c in send.call_args_list], [(signal.SIGKILL,)])
    spawn.assert_not_called()
    self.assertEqual(owner.egpu_deadline_ns, 0)
    self.assertIs(owner.proc, child)

  def test_big_running_is_never_touched(self):
    owner = ModeldProcess('modeld', 'module', lambda *args: True)
    child = Mock(pid=123, exitcode=None)
    child.is_alive.return_value = True
    owner.proc = child
    owner.egpu.launched(OLD, small_only=False)
    load = NS(pid=123, process_start_ticks=456, loaded_mono_ns=BASE, variant=ModelVariant.CHESTNUT)
    with patch('openpilot.starpilot.models.recovery_process.process_start_ticks', return_value=456), \
         patch('openpilot.starpilot.models.recovery_process.read_receipt', return_value=load), \
         patch('openpilot.starpilot.models.recovery_process.chestnut_usb_identity', return_value=NEW) as usb, \
         patch('openpilot.starpilot.models.recovery_process.time.monotonic_ns') as clock, \
         patch.object(owner, 'signal') as send:
      for i in range(1, 40):
        clock.return_value = BASE + i * S // 2
        owner.observe(small_feed(i * .5), True)
      send.assert_not_called()
      usb.assert_not_called()


if __name__ == '__main__':
  unittest.main()
