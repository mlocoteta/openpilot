import math


class SpeedLimitPulse:
  def __init__(self):
    self.last_limit = 0.0
    self.start_time = -math.inf
    self._started_frame: int | None = None

  def clear(self) -> None:
    self.start_time = -math.inf

  def reset(self) -> None:
    self.last_limit = 0.0
    self._started_frame = None
    self.clear()

  def update(self, source: str, limit: float, speed_conversion: float, now: float, started_frame: int) -> None:
    if started_frame != self._started_frame:
      self.reset()
      self._started_frame = started_frame

    if not math.isfinite(limit) or limit <= 0:
      self.clear()
      return

    if source != "Vision":
      self.clear()
    elif round(limit * speed_conversion) != round(self.last_limit * speed_conversion):
      self.start_time = now

    self.last_limit = limit
