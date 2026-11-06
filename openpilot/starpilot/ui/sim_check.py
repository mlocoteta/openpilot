"""Accord: tap the Home sidebar network block to make the modem daemon re-check the SIM.

The UI writes a request id to SIM_CHECK_PATH; the daemon (common/hardware/comma/modem.py) re-checks the SIM offroad
and republishes /dev/shm/modem with sim_check_id = that id. Until then the sidebar shows "Checking SIM...", then the
result line flashes so it's obvious it updated. No answer within CHECK_TIMEOUT -> "No reply" (onroad, rate limit,
daemon busy).
"""
from collections.abc import Callable
from dataclasses import dataclass
import os
import tempfile
import time

SIM_CHECK_PATH = "/dev/shm/modem_sim_check"  # same path as modem.SIM_CHECK_PATH
MIN_INTERVAL = 10.0  # s between taps (the daemon ignores faster ones too)
CHECK_TIMEOUT = 20.0  # s
FLASH = 3.0  # s the result stays highlighted


@dataclass(frozen=True, slots=True)
class SimCheckView:
  phase: str        # "checking" | "done" | "no_reply"
  highlight: float  # 0..1, fades out over FLASH after the result


def write_request(request_id: str, path: str = SIM_CHECK_PATH) -> None:
  directory = os.path.dirname(path)
  with tempfile.NamedTemporaryFile(mode="w", dir=directory, prefix=".sim_check", delete=False) as f:
    f.write(request_id)
  os.replace(f.name, path)


class SimCheckTracker:
  def __init__(self, write: Callable[[str], None] = write_request, clock: Callable[[], float] = time.monotonic):
    self._write, self._clock = write, clock
    self._seq = 0
    self._id: str | None = None
    self._started: float | None = None
    self._finished: float | None = None
    self._phase: str | None = None

  @property
  def pending(self) -> bool:
    return self._phase == "checking"

  def request(self) -> bool:
    """Tap: write the request unless the last one was under MIN_INTERVAL ago. True = a new check started."""
    now = self._clock()
    if self._started is not None and now - self._started < MIN_INTERVAL:
      return False
    self._seq += 1
    request_id = f"{os.getpid()}.{self._seq}.{now:.3f}"  # unique per UI process and tap
    try:
      self._write(request_id)
    except OSError:
      return False
    self._id, self._started, self._finished, self._phase = request_id, now, None, "checking"
    return True

  def observe(self, modem: dict | None) -> None:
    if self.pending and modem and str(modem.get("sim_check_id", "")) == self._id:
      self._phase, self._finished = "done", self._clock()

  def view(self) -> SimCheckView | None:
    now = self._clock()
    if self._phase == "checking" and self._started is not None and now - self._started >= CHECK_TIMEOUT:
      self._phase, self._finished = "no_reply", self._started + CHECK_TIMEOUT
    if self._phase == "checking":
      return SimCheckView("checking", 1.0)
    if self._phase is not None and self._finished is not None and now - self._finished < FLASH:
      return SimCheckView(self._phase, max(0.0, 1.0 - (now - self._finished) / FLASH))
    return None
