"""Offroad-only Galaxy RSS watchdog: thresholds, onroad guard, rate limit, restart path."""

import tempfile
import threading
import unittest

from openpilot.starpilot.galaxy import managed, memory_watchdog
from openpilot.starpilot.galaxy.memory_watchdog import GalaxyMemoryWatchdog, RSS_LIMIT_BYTES
from openpilot.system.manager.process_config import managed_processes

MB = 1024 * 1024


class FakeEnv:
  def __init__(self):
    self.now = 1000.0
    self.rss = 100 * MB
    self.offroad = True

  def watchdog(self):
    return GalaxyMemoryWatchdog(rss=lambda: self.rss, offroad=lambda: self.offroad, clock=lambda: self.now)


class TestGalaxyMemoryWatchdog(unittest.TestCase):
  def setUp(self):
    self.env = FakeEnv()
    self.wd = self.env.watchdog()
    self.env.now += 3600

  def test_threshold_is_200_mb(self):
    self.assertEqual(RSS_LIMIT_BYTES, 200 * MB)

  def test_below_limit_never_restarts(self):
    self.env.rss = 199 * MB
    self.assertFalse(any(self.wd.check() for _ in range(10)))

  def test_over_limit_offroad_restarts_after_two_samples(self):
    self.env.rss = 420 * MB
    self.assertFalse(self.wd.check())
    self.assertTrue(self.wd.check())

  def test_single_spike_resets(self):
    self.env.rss = 300 * MB
    self.assertFalse(self.wd.check())
    self.env.rss = 150 * MB
    self.assertFalse(self.wd.check())
    self.env.rss = 300 * MB
    self.assertFalse(self.wd.check())

  def test_never_restarts_onroad(self):
    self.env.rss = 420 * MB
    self.env.offroad = False
    self.assertFalse(any(self.wd.check() for _ in range(20)))
    self.env.offroad = True
    self.assertTrue(self.wd.check())

  def test_min_uptime_rate_limits_restarts(self):
    fresh = self.env.watchdog()
    self.env.rss = 420 * MB
    self.env.now += 599
    self.assertFalse(fresh.check())
    self.assertFalse(fresh.check())
    self.env.now += 1
    self.assertTrue(fresh.check())

  def test_unknown_rss_is_ignored(self):
    self.env.rss = None
    self.assertFalse(self.wd.check())

  def test_read_rss_parses_proc_status(self):
    with tempfile.NamedTemporaryFile('w', suffix='status') as f:
      f.write('Name:\tpython\nVmRSS:\t  430080 kB\n')
      f.flush()
      self.assertEqual(memory_watchdog.read_rss_bytes(f.name), 430080 * 1024)
    self.assertIsNone(memory_watchdog.read_rss_bytes('/nonexistent/status'))
    self.assertGreater(memory_watchdog.read_rss_bytes(), 0)

  def test_run_sets_stop_when_due(self):
    self.env.rss = 420 * MB
    stop = threading.Event()
    self.assertTrue(memory_watchdog.run(stop, self.wd, interval=0.001))
    self.assertTrue(stop.is_set())

  def test_run_returns_on_stop_without_restart(self):
    stop = threading.Event()
    stop.set()
    self.assertFalse(memory_watchdog.run(stop, self.wd, interval=0.001))

  def test_run_survives_check_errors(self):
    calls = []
    stop = threading.Event()

    class Boom:
      def check(self):
        calls.append(1)
        if len(calls) >= 3:
          stop.set()
        raise RuntimeError('boom')

    self.assertFalse(memory_watchdog.run(stop, Boom(), interval=0.001))
    self.assertEqual(len(calls), 3)


class FakeServer:
  daemon_threads = False
  block_on_close = True

  def __init__(self):
    self.closed = False
    self._stop = threading.Event()

  def serve_forever(self, poll_interval=0.5):
    self._stop.wait()

  def shutdown(self):
    self._stop.set()

  def drain_requests(self, timeout):
    return True

  def server_close(self, close_sources=True):
    self.closed = True


class TestManagedRestartPath(unittest.TestCase):
  def test_watchdog_stop_exits_serve_managed_cleanly(self):
    server = FakeServer()

    def watchdog(stop):
      stop.set()

    managed.serve_managed(server, watchdog=watchdog)  # no exception = clean exit
    self.assertTrue(server.closed)

  def test_manager_restarts_galaxy_on_exit(self):
    self.assertTrue(managed_processes['galaxy'].restart_on_exit)


if __name__ == '__main__':
  unittest.main()
