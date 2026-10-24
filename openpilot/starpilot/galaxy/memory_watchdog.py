"""Offroad-only RSS watchdog for the managed Galaxy service.

Galaxy's caches grow over a drive (seen 73 MB at boot to 420 MB). When the car
is offroad and Galaxy's own RSS stays above the limit, Galaxy stops cleanly and
manager restarts it (restart_on_exit). Onroad it is never touched.
"""

import threading
import time
from collections.abc import Callable

from openpilot.common.swaglog import cloudlog

RSS_LIMIT_BYTES = 200 * 1024 * 1024
CHECK_INTERVAL_S = 60.0
MIN_UPTIME_S = 600.0       # also limits restarts to at most one per 10 min
OVER_LIMIT_CHECKS = 2      # consecutive over-limit samples before a restart


def read_rss_bytes(status_path: str = '/proc/self/status') -> int | None:
  try:
    with open(status_path) as f:
      for line in f:
        if line.startswith('VmRSS:'):
          return int(line.split()[1]) * 1024
  except (OSError, ValueError, IndexError):
    pass
  return None


def params_offroad() -> bool:
  try:
    from openpilot.common.params import Params
    return Params().get_bool('IsOffroad')
  except Exception:
    return False


class GalaxyMemoryWatchdog:
  def __init__(self, rss: Callable[[], int | None] = read_rss_bytes, offroad: Callable[[], bool] = params_offroad,
               clock: Callable[[], float] = time.monotonic, limit: int = RSS_LIMIT_BYTES,
               min_uptime: float = MIN_UPTIME_S, over_checks: int = OVER_LIMIT_CHECKS):
    self.rss = rss
    self.offroad = offroad
    self.clock = clock
    self.limit = limit
    self.min_uptime = min_uptime
    self.over_checks = over_checks
    self.started_at = clock()
    self.over = 0

  def check(self) -> bool:
    """One sample. True means Galaxy should stop now so manager restarts it."""
    rss = self.rss()
    if rss is None or rss <= self.limit:
      self.over = 0
      return False
    self.over += 1
    if self.over < self.over_checks or self.clock() - self.started_at < self.min_uptime:
      return False
    if not self.offroad():
      return False
    cloudlog.warning(f"galaxy memory watchdog: RSS {rss / 1e6:.0f} MB > {self.limit / 1e6:.0f} MB while offroad; restarting galaxy")
    return True


def run(stop: threading.Event, watchdog: GalaxyMemoryWatchdog | None = None, interval: float = CHECK_INTERVAL_S) -> bool:
  """Sample until stop is set. Sets stop and returns True when a restart is due."""
  watchdog = watchdog or GalaxyMemoryWatchdog()
  while not stop.wait(interval):
    try:
      if watchdog.check():
        stop.set()
        return True
    except Exception:
      cloudlog.exception("galaxy memory watchdog check failed")
  return False
