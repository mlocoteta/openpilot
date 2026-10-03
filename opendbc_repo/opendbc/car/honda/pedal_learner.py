"""Guarded gas-factor learner for the Accord 9G Nidec pedal interceptor.

The stock learner (carcontroller.py, enableGasInterceptorDEPRECATED path) integrates
  gas_factor += (accel_cmd - aEgo) / 150 * accel_cmd
at 50 Hz whenever the long PID is active, the driver is off the gas, and gas > 0. Offline replay
of drives 302-31a (2026-09-28..10-02, exact match to the logged learner) showed:
  - it moves 6-14 factor units per drive for a net change of +-1: it integrates aEgo noise and
    the ~0.15-0.7 s pedal lag (rising commands +4.7, falling -5.0 over six drives);
  - the pedal plant gain falls from ~10 m/s^2 per unit pedal below 4 m/s to ~2.4 at highway
    speed, so the factor is pushed down at 3-8 m/s and up at 8-20 m/s and ping-pongs between
    0.7 and 3.0 within one drive;
  - at factors > 1.8, launches and 9-14 m/s pull-aways delivered 1.4-1.5x the commanded accel
    (31a seg 24: +2.6 against +1.6 after the learner added +0.14 during the 0.5 s pedal lag).

The guard keeps the same update law but only learns from samples that measure the steady pedal
gain, learns 10x slower, limits the change per drive, and bounds the factor to the band where
closed-loop tracking was unbiased. The applied factor is additionally capped at low speed, where the
plant gain is highest and the launch overshoots happened.
"""
from collections import deque

import numpy as np

# Closed-loop tracking on drives 302-31a by live factor (aEgo 0.3 s later - cmd, positive demand):
# at >= 10 m/s the bias is -0.07..+0.02 for factors 1.2-1.6 and the >+0.5 m/s^2 overshoot share is 0-6 %;
# above 1.6 it is 4-21 %, above 1.9 14-21 %; below 1.2 it under-delivers (-0.06..-0.14).
GAS_FACTOR_MIN = 1.2
GAS_FACTOR_MAX = 1.6
GAS_FACTOR_DEFAULT = 1.4
LEARN_DIV = 1500.0             # stock 150
MAX_DRIVE_CHANGE = 0.10        # per drive, from the (clamped) drive-start value
MIN_SPEED = 10.0               # m/s; below this the torque converter / gas_mult regime dominates
MIN_GAS = 0.04                 # gas = accel / 4.8, i.e. >= ~0.2 m/s^2 of commanded accel
CMD_WINDOW_STEPS = 25          # 0.5 s at the 50 Hz learner rate
MAX_CMD_CHANGE = 0.15          # m/s^2 over the window: quasi-steady demand only (pedal lag)
BRAKE_HOLDOFF_STEPS = 100      # 2 s at 50 Hz after any brake (openpilot, driver, or stopping)
MAX_HILL = 0.5                 # m/s^2 of grade; the Nidec pedal path has no grade term
MAX_ERROR = 1.0                # m/s^2; larger errors are transients or disturbances

# Applied-factor cap at low speed (launches). Same closed-loop data: unbiased at <= 1.0 for 3-6 m/s
# (1.0-1.6 gave +0.11..+0.21 and 18-25 % overshoot), at 1.0-1.2 for 6-10 m/s (1.6-1.9 gave +0.29 / 30 %),
# and 1.0-1.4 for 0-3 m/s. The pedal gain there is ~10 m/s^2 per unit pedal vs ~2.4 on the highway.
LOW_SPEED_CAP_BP = [6.0, 12.0]
LOW_SPEED_CAP = 1.0


def clamp_gas_factor(gas_factor: float) -> float:
  if not np.isfinite(gas_factor):
    return GAS_FACTOR_DEFAULT
  return float(np.clip(gas_factor, GAS_FACTOR_MIN, GAS_FACTOR_MAX))


def applied_gas_factor(gas_factor: float, v_ego: float) -> float:
  """Factor used for the pedal command: the learned value, capped at launch speeds."""
  cap = float(np.interp(v_ego, LOW_SPEED_CAP_BP, [LOW_SPEED_CAP, GAS_FACTOR_MAX]))
  return min(gas_factor, cap)


class PedalGasFactorGuard:
  REASONS = ("ok", "inactive", "speed", "gas", "cmd_change", "brake", "hill", "error", "drive_limit")

  def __init__(self, gas_factor_start: float):
    self.start = clamp_gas_factor(gas_factor_start)
    self.cmd_hist: deque = deque(maxlen=CMD_WINDOW_STEPS)
    self.steps_since_brake = BRAKE_HOLDOFF_STEPS
    self.counts = dict.fromkeys(self.REASONS, 0)

  def update(self, gas_factor: float, accel_cmd: float, a_ego: float, v_ego: float, gas: float,
             braking: bool, hill: float, learn_allowed: bool) -> float:
    """One learner step at 50 Hz. Call every step so the brake/command history stays continuous;
    learn_allowed is the stock condition (long PID active and the driver off the gas)."""
    self.cmd_hist.append(accel_cmd)
    self.steps_since_brake = 0 if braking else self.steps_since_brake + 1
    reason = "inactive" if not learn_allowed else self._reject_reason(accel_cmd, a_ego, v_ego, gas, hill)
    if reason is None:
      error = accel_cmd - a_ego
      new = gas_factor + error / LEARN_DIV * gas * 4.8
      lo = max(GAS_FACTOR_MIN, self.start - MAX_DRIVE_CHANGE)
      hi = min(GAS_FACTOR_MAX, self.start + MAX_DRIVE_CHANGE)
      gas_factor = float(np.clip(new, lo, hi))
      reason = "drive_limit" if gas_factor != new else "ok"
    self.counts[reason] += 1
    return gas_factor

  def _reject_reason(self, accel_cmd, a_ego, v_ego, gas, hill) -> str | None:
    if v_ego < MIN_SPEED:
      return "speed"
    if gas < MIN_GAS:
      return "gas"
    if self.steps_since_brake < BRAKE_HOLDOFF_STEPS:
      return "brake"
    if len(self.cmd_hist) < CMD_WINDOW_STEPS or max(self.cmd_hist) - min(self.cmd_hist) > MAX_CMD_CHANGE:
      return "cmd_change"
    if abs(hill) > MAX_HILL:
      return "hill"
    if abs(accel_cmd - a_ego) > MAX_ERROR:
      return "error"
    return None
