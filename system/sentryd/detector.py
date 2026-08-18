from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence


class MotionDetector:
  """Detect sustained changes in the accelerometer magnitude.

  The detector deliberately returns edge events instead of owning any I/O. That
  keeps the movement policy testable and lets the daemon decide how to capture
  frames or notify Galaxy.
  """

  def __init__(
    self,
    *,
    sensitivity: float = 0.04,
    warning_trigger_count: int = 10,
    alarm_trigger_count: int = 25,
    alarm_time: float = 30.0,
    reset_time: float = 60.0,
    clock: Callable[[], float] = time.monotonic,
  ):
    self.sensitivity = sensitivity
    self.warning_trigger_count = warning_trigger_count
    self.alarm_trigger_count = alarm_trigger_count
    self.alarm_time = alarm_time
    self.reset_time = reset_time
    self.clock = clock
    self.previous_acceleration: tuple[float, float, float] | None = None
    self.trigger_count = 0
    self.trigger_started_at: float | None = None
    self.alarm_triggered = False

  @staticmethod
  def _magnitude(acceleration: Sequence[float]) -> float:
    if len(acceleration) < 3:
      raise ValueError("accelerometer samples must contain x, y, and z")
    return math.sqrt(sum(float(component) ** 2 for component in acceleration[:3]))

  def reset(self) -> None:
    self.previous_acceleration = None
    self.trigger_count = 0
    self.trigger_started_at = None
    self.alarm_triggered = False

  def update(self, acceleration: Sequence[float], now: float | None = None) -> str | None:
    now = self.clock() if now is None else now
    current = tuple(float(component) for component in acceleration[:3])
    if len(current) < 3:
      raise ValueError("accelerometer samples must contain x, y, and z")

    if self.previous_acceleration is None:
      self.previous_acceleration = current
      return None

    delta = abs(self._magnitude(current) - self._magnitude(self.previous_acceleration))
    self.previous_acceleration = current

    if delta > self.sensitivity:
      self.trigger_count += 1
      if self.trigger_started_at is None:
        self.trigger_started_at = now

      if self.trigger_count == self.warning_trigger_count:
        return "warning"

      if (
        self.trigger_count > self.alarm_trigger_count
        and now - self.trigger_started_at >= self.alarm_time
        and not self.alarm_triggered
      ):
        self.alarm_triggered = True
        return "alarm"

    if self.trigger_started_at is not None and now - self.trigger_started_at >= self.reset_time:
      self.trigger_count = 0
      self.trigger_started_at = None
      self.alarm_triggered = False

    return None
