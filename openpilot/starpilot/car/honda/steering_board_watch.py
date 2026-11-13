"""card.py side of the 9G TI -> SSV3 fallback (opendbc/car/honda/steering_board.py).

On a TI drive: when the TI never answers while the SSV3 reports (CarState.ti_presence.missing), write
TorqueInterceptorMissing=1 once, so the next start uses the SSV3. When the TI does answer, clear a stale
record once. Each param write happens at most once per drive; nothing runs on non-TI drives.
"""
from openpilot.common.swaglog import cloudlog

PARAM = "TorqueInterceptorMissing"


class SteeringBoardWatch:
  def __init__(self, car_state, params):
    self.cs = car_state
    self.params = params
    self.recorded = False
    self.cleared = False

  def update(self) -> None:
    presence = self.cs.ti_presence
    if presence.missing and not self.recorded:
      self.recorded = True
      try:
        self.params.put_bool_nonblocking(PARAM, True)
      except Exception:
        cloudlog.exception("steering_board_watch: could not record TorqueInterceptorMissing")
      cloudlog.event("accord_ti_missing", frames=presence.frames, status_frames=presence.status_frames)
    elif self.cs.ti.feedback_seen and not self.cleared:
      self.cleared = True
      try:
        if self.params.get_bool(PARAM):
          self.params.put_bool_nonblocking(PARAM, False)
          cloudlog.event("accord_ti_missing_cleared")
      except Exception:
        cloudlog.exception("steering_board_watch: could not clear TorqueInterceptorMissing")


def install(CI, params):
  cs = getattr(CI, "CS", None)
  if getattr(cs, "ti_presence", None) is None or getattr(cs, "ti", None) is None:
    return None
  return SteeringBoardWatch(cs, params)
