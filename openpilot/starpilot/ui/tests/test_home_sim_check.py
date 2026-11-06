"""Accord: tapping the Home sidebar network block asks the modem daemon to re-check the SIM."""
from dataclasses import replace
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from openpilot.selfdrive.ui.lib.cell_status import CellStatus
from openpilot.starpilot.ui import sim_check
from openpilot.starpilot.ui.home_state import HomeAction, HomeActionKind, HomeInput
from openpilot.starpilot.ui.presentation import BitmapFonts, Profile
from openpilot.starpilot.ui.preview_home import reference_state
from openpilot.starpilot.ui.shell import ShellMode
from openpilot.starpilot.ui.sim_check import SimCheckTracker, SimCheckView
from openpilot.starpilot.ui.tests.test_runtime_snapshot import NOW, RuntimeSnapshotAdapter, ui_fake

NO_SIM = {"state": "INITIALIZING", "sim": "absent"}
NO_SIM_CELL = CellStatus("no_sim", "No SIM", 0)


class Clock:
  def __init__(self, t=1000.0):
    self.t = t

  def __call__(self):
    return self.t


def tracker(clock=None):
  writes = []
  t = SimCheckTracker(write=writes.append, clock=clock or Clock())
  return t, writes


def request_id(writes):
  return writes[-1]


class TapTests(unittest.TestCase):
  def tap(self, x, y, state=None):
    actions = []
    handler = HomeInput(Profile.LARGE, actions.append)
    handler.press(x, y, 10)
    handler.release(x, y, 10.1, state or reference_state())
    return actions

  def test_network_block_tap_requests_sim_check(self):
    for point in ((60, 200), (150, 250), (100, 300), (280, 320)):
      with self.subTest(point=point):
        self.assertEqual(self.tap(*point), [HomeAction(HomeActionKind.CHECK_SIM)])

  def test_neighbours_keep_their_targets(self):
    self.assertEqual(self.tap(150, 100), [HomeAction(HomeActionKind.OPEN_SETTINGS)])
    self.assertEqual(self.tap(150, 400), [])  # TEMP tile
    self.assertEqual(self.tap(150, 900), [])  # home button
    self.assertEqual(self.tap(200, 260, replace(reference_state(), recording_audio=True)),
                     [HomeAction(HomeActionKind.OPEN_TOGGLES)])  # mic badge wins

  def test_drag_out_of_block_does_not_fire(self):
    actions = []
    handler = HomeInput(Profile.LARGE, actions.append)
    handler.press(150, 250, 10)
    handler.release(150, 500, 10.2, reference_state())
    self.assertEqual(actions, [])

  def test_compact_profile_has_no_sim_target(self):
    actions = []
    handler = HomeInput(Profile.COMPACT, actions.append)
    handler.press(150, 300, 10)
    handler.release(150, 300, 10.1, reference_state())
    self.assertNotIn(HomeAction(HomeActionKind.CHECK_SIM), actions)


class TrackerTests(unittest.TestCase):
  def test_tap_writes_request_and_shows_checking(self):
    t, writes = tracker()
    self.assertTrue(t.request())
    self.assertEqual(len(writes), 1)
    self.assertRegex(writes[0], r"^\d+\.1\.1000\.000$")
    self.assertEqual(t.view(), SimCheckView("checking", 1.0))

  def test_answer_with_matching_id_flashes_result_then_clears(self):
    clock = Clock()
    t, writes = tracker(clock)
    t.request()
    t.observe({"sim": "absent", "sim_check_id": "older"})
    self.assertEqual(t.view().phase, "checking")
    clock.t += 9
    t.observe({"sim": "absent", "sim_check": 3, "sim_check_id": request_id(writes)})
    self.assertEqual(t.view(), SimCheckView("done", 1.0))
    clock.t += sim_check.FLASH / 2
    self.assertAlmostEqual(t.view().highlight, 0.5)
    clock.t += sim_check.FLASH / 2
    self.assertIsNone(t.view())

  def test_timeout_shows_no_reply(self):
    clock = Clock()
    t, writes = tracker(clock)
    t.request()
    clock.t += sim_check.CHECK_TIMEOUT - 0.1
    self.assertEqual(t.view().phase, "checking")
    clock.t += 0.1
    self.assertEqual(t.view().phase, "no_reply")
    clock.t += sim_check.FLASH
    self.assertIsNone(t.view())
    t.observe({"sim_check_id": request_id(writes)})  # late answer: ignored
    self.assertIsNone(t.view())

  def test_taps_rate_limited(self):
    clock = Clock()
    t, writes = tracker(clock)
    self.assertTrue(t.request())
    clock.t += 5
    self.assertFalse(t.request())
    clock.t += 5
    self.assertTrue(t.request())
    self.assertEqual(len(writes), 2)

  def test_write_failure_starts_nothing(self):
    def fail(_):
      raise OSError("ro")
    t = SimCheckTracker(write=fail)
    self.assertFalse(t.request())
    self.assertIsNone(t.view())

  def test_write_request_file(self):
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
      sim_check.write_request("abc", str(Path(d) / "modem_sim_check"))
      self.assertEqual((Path(d) / "modem_sim_check").read_text(), "abc")
      self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ["modem_sim_check"])


class Modem:
  def __init__(self, value):
    self.value, self.reads = value, 0

  def __call__(self):
    self.reads += 1
    return self.value


class SnapshotTests(unittest.TestCase):
  def adapter(self, modem, network_raw=1):
    ui = ui_fake()
    ui.started = False
    ui.sm['deviceState'].networkType = NS(raw=network_raw)
    clock = Clock()
    t, writes = tracker(clock)
    self.writes = writes
    return RuntimeSnapshotAdapter(ui, modem_state=modem, sim_check=t), t, clock

  def test_checking_then_result_after_daemon_answers(self):
    modem = Modem(NO_SIM)
    adapter, t, clock = self.adapter(modem)
    ns = {"v": NOW}
    with patch('openpilot.starpilot.ui.runtime_snapshot.time.monotonic_ns', lambda: ns["v"]):
      self.assertIsNone(adapter.build(ShellMode.HOME, now_ns=NOW).home.sim_check)
      t.request()
      ns["v"] += 600_000_000
      home = adapter.build(ShellMode.HOME, now_ns=NOW + 1).home
      self.assertEqual(home.sim_check.phase, "checking")
      modem.value = {**NO_SIM, "sim_check": 1, "sim_check_id": request_id(self.writes)}
      ns["v"] += 600_000_000  # pending -> 0.5 s read interval, not 2 s
      home = adapter.build(ShellMode.HOME, now_ns=NOW + 2).home
      self.assertEqual(home.sim_check.phase, "done")
      self.assertEqual(home.cell, CellStatus("no_sim", "No SIM", 0))

  def test_cell_primary_still_reads_modem_while_checking(self):
    modem = Modem(NO_SIM)
    adapter, t, _ = self.adapter(modem, network_raw=4)
    adapter.build(ShellMode.HOME, now_ns=NOW)
    self.assertEqual(modem.reads, 0)
    t.request()
    modem.value = {"sim_check_id": request_id(self.writes)}
    home = adapter.build(ShellMode.HOME, now_ns=NOW + 1).home
    self.assertEqual(modem.reads, 1)
    self.assertIsNone(home.cell)
    self.assertEqual(home.sim_check.phase, "done")

  def test_not_on_home_no_feedback(self):
    adapter, t, _ = self.adapter(Modem(NO_SIM))
    t.request()
    self.assertIsNone(adapter.build(ShellMode.ONROAD, now_ns=NOW).home.sim_check)


class DrawTests(unittest.TestCase):
  def draw(self, check, cell=NO_SIM_CELL):
    from openpilot.starpilot.ui.home import HomeView
    view = HomeView.__new__(HomeView)
    view.fonts = Mock(spec=BitmapFonts, profile=Profile.LARGE)
    state = replace(reference_state(), network="wifi", network_strength=5, cell=cell, sim_check=check)
    with patch.object(view, '_icon'), patch.object(view, '_text') as text, \
         patch.object(view, '_measure', return_value=NS(width=80, height=35)), \
         patch('openpilot.starpilot.ui.home.rl.draw_circle'), \
         patch('openpilot.starpilot.ui.home.clip.begin_scissor_mode'), patch('openpilot.starpilot.ui.home.clip.end_scissor_mode'), \
         patch('openpilot.starpilot.ui.home.outside_rounded_border'), \
         patch('openpilot.starpilot.ui.home.rl.draw_rectangle_rounded') as rect:
      view._sidebar(state)
    return [c.args[0] for c in text.call_args_list], [c.args[0] for c in rect.call_args_list]

  def test_checking_replaces_cell_line(self):
    texts, rects = self.draw(SimCheckView("checking", 1.0))
    self.assertEqual(texts[:2], ["Wi-Fi", "Checking SIM..."])
    self.assertFalse(any(r.y == 186 for r in rects))

  def test_result_flash_highlights_block_with_result_line(self):
    texts, rects = self.draw(SimCheckView("done", 0.8))
    self.assertEqual(texts[:2], ["Wi-Fi", "No SIM"])
    self.assertTrue(any(r.y == 186 for r in rects))

  def test_no_reply_line(self):
    texts, rects = self.draw(SimCheckView("no_reply", 0.5))
    self.assertEqual(texts[1], "No reply")
    self.assertTrue(any(r.y == 186 for r in rects))

  def test_no_check_unchanged(self):
    texts, rects = self.draw(None)
    self.assertEqual(texts[1], "No SIM")
    self.assertFalse(any(r.y == 186 for r in rects))


if __name__ == "__main__":
  unittest.main()
