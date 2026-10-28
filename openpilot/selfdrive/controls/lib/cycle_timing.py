"""Bounded measurements for the existing post-publication overrun report."""
from collections.abc import Callable
import time

PHASES = ('authority_and_preferences', 'longitudinal', 'lateral_planning', 'learning', 'lateral_controller_and_finish')


class ControlCycleTiming:
  def __init__(self, *, wall_clock: Callable[[], int] = time.perf_counter_ns,
               cpu_clock: Callable[[], int] = time.thread_time_ns):
    self.wall_clock, self.cpu_clock = wall_clock, cpu_clock
    self.wall = [0] * len(PHASES)
    self.cpu = [0] * len(PHASES)
    self.count = 0
    self.last_wall = self.last_cpu = 0
    self.overflow = False

  def start(self) -> None:
    self.count = 0
    self.overflow = False
    self.last_wall, self.last_cpu = self.wall_clock(), self.cpu_clock()

  def mark(self) -> None:
    if self.count >= len(PHASES):
      self.overflow = True
      return
    wall, cpu = self.wall_clock(), self.cpu_clock()
    self.wall[self.count], self.cpu[self.count] = wall - self.last_wall, cpu - self.last_cpu
    self.last_wall, self.last_cpu = wall, cpu
    self.count += 1

  def snapshot(self) -> dict[str, dict[str, float]]:
    return {name: {'wall_ms': self.wall[i] / 1e6, 'cpu_ms': self.cpu[i] / 1e6}
            for i, name in enumerate(PHASES[:self.count])}

  @property
  def complete(self) -> bool:
    return self.count == len(PHASES) and not self.overflow
