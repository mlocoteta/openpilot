"""Accord 9G (Nidec + pedal interceptor) long-PID brake-onset hold, 7.0 port of 6.x F09 (66485e4a2, on the car
2026-10-10 to the 7.0 port).

The brake reaches the wheels ~0.35 s after the command, so during the first (longitudinalActuatorDelay + 0.15) s of a
braking request the aEgo error is lag, not a model error. Integrating it wound I down to -0.85 (p10) and over-braked
after gas releases (6.x drives 314-318). During that window, while the plan asks for real decel and the car is not yet
decelerating, freeze I and keep it >= I_FLOOR. Stops, low speed and closing leads (TTC < 5 s) are left alone: the
held-back I takes ~2 s to catch up once the hold ends.

Events that open the window (tracked every LongControl.update, active or not, so they survive the per-frame reset
while long is inactive): the longActive rising edge, the gas-pedal release, and aTarget crossing below ONSET_TARGET.
"""
import math

from openpilot.common.realtime import DT_CTRL

ONSET_TARGET = -0.3  # m/s^2; plan decel below this is a braking request
MIN_ERROR = 0.3  # m/s^2; aEgo still this far above aTarget = brake not there yet
I_FLOOR = -0.4  # m/s^2; I is kept at or above this during the hold
EXTRA_TIME = 0.15  # s on top of the actuator delay
DEFAULT_DELAY = 0.30  # s; 6.x LongitudinalActuatorDelay on the 9G
MAX_DELAY = 1.0
MIN_LEAD_TTC = 5.0  # s; a closing lead nearer than this in time: no hold
MIN_SPEED = 8.0  # m/s; no hold below this (stops and close leads follow quickly)
NEVER = 1 << 30


def window_frames(delay) -> int:
  try:
    delay = float(delay)
  except (TypeError, ValueError):
    delay = DEFAULT_DELAY
  if not math.isfinite(delay) or delay <= 0.0:
    delay = DEFAULT_DELAY
  return int(round((min(delay, MAX_DELAY) + EXTRA_TIME) / DT_CTRL))


def has_close_lead(v_ego, leads) -> bool:
  for lead in leads or ():
    if lead is None or not bool(getattr(lead, "status", False)):
      continue
    v_rel = getattr(lead, "vRel", None)
    closing = -float(v_rel) if v_rel is not None else float(v_ego) - float(getattr(lead, "vLead", v_ego))
    d_rel = float(getattr(lead, "dRel", float("inf")))
    if closing > 1e-3 and d_rel / closing < MIN_LEAD_TTC:
      return True
  return False


class HondaBrakeOnsetHold:
  def __init__(self, actuator_delay):
    self.window = window_frames(actuator_delay)
    self.frames = NEVER
    self.prev_active = False
    self.prev_gas_pressed = False
    self.prev_a_target = 0.0

  def track(self, active, gas_pressed, a_target):
    """Once per LongControl.update with the planner's aTarget. Not cleared by LongControl.reset()."""
    active = bool(active)
    gas_pressed = bool(gas_pressed)
    a_target = float(a_target)
    event = ((active and not self.prev_active) or
             (self.prev_gas_pressed and not gas_pressed) or
             (a_target < ONSET_TARGET <= self.prev_a_target))
    self.frames = 0 if event else min(self.frames + 1, NEVER)
    self.prev_active = active
    self.prev_gas_pressed = gas_pressed
    self.prev_a_target = a_target

  def hold(self, pid, a_target, CS, should_stop, leads) -> bool:
    """Returns True to freeze I (and raises I to I_FLOOR). leads None = radar unknown: no hold."""
    if should_stop or CS.vEgo < MIN_SPEED or self.frames >= self.window:
      return False
    if a_target >= ONSET_TARGET or CS.aEgo - a_target <= MIN_ERROR:
      return False
    if leads is None or has_close_lead(CS.vEgo, leads):
      return False
    pid.i = max(pid.i, I_FLOOR)
    return True
