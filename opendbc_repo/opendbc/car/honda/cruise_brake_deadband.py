"""Accord 9G (Nidec + pedal interceptor) cruise-hold brake deadband.

At a steady set speed on a slight downhill the I-only long PID crossed the friction-brake onset
(cmd about -0.30 m/s^2 at 65 mph) every ~5 s. The 1-4 count Nidec brake gives a -0.1..-0.35 m/s^2 step
with the pedal still open, so speed hunted 64.4 <-> 65.5 mph (routes 33d and 352).

While cruising at or just above the planner's cruise speed with no real decel demand, this gate holds
the friction brake off. The pedal keeps following the accel command down to closed, so the car coasts
and may drift up to BAND_EXIT over the set speed. The brakes come back at once for a real demand
(planner aTarget < A_TARGET_MIN, stop, lead/e2e plan source, closing lead, curve control, accel cmd < ACCEL_CMD_MIN),
and they ramp in at OVERSPEED_RAMP when the only reason is overspeed past the band.

card.py runs CruiseBrakeDeadband with the plan inputs and the real friction request. LongControl runs its own
copy (same plan inputs, friction_request() estimate) and, while that copy is suppressing, freezes I so the output
can't wind below pedal_close_accel(): otherwise the brake would come on hard when the deadband releases.
After an overspeed release the gate stays stock until the stock request is 0 again (steep hills keep a steady brake).
Kill switch: touch /data/cruise_brake_deadband_disabled (checked about once a second, no restart).
"""
import os

import numpy as np

KILL_FILE = "/data/cruise_brake_deadband_disabled"
KILL_FILE_CHECK_FRAMES = 100

MPH = 0.44704
MIN_SPEED = 10.0  # m/s; cruise hold only (22 mph)
BAND_EXIT = 2.0 * MPH  # over the planner cruise speed: brakes allowed again
BAND_REENTER = 1.0 * MPH  # back under this: hold them off again
A_TARGET_MIN = -0.5  # planner decel below this is a real demand
ACCEL_CMD_MIN = -1.5  # PID output below this always gets the brakes
LEAD_TTC_MIN = 8.0  # s; a closing lead nearer than this in time gets the brakes
LEAD_GAP_MIN = 1.0  # s; a lead nearer than this time gap gets the brakes
OVERSPEED_RAMP = 0.25  # brake units/s when the brakes return only because of overspeed
RELEASE_CLEAR_S = 1.0  # after an overspeed release, re-arm only once the stock request has been 0 this long
ACCORD_9G_BRAKE_ACCEL_PER_UNIT = 3.6  # carcontroller.ACCORD_9G_BRAKE_ACCEL_PER_UNIT

# The pedal closes at accel = -0.75 * wind_factor * wind_brake_mps2 (carcontroller's wind term).
# The learned wind factor sits at ~5 on the 9G, so this is about -0.89 m/s^2 at 65 mph.
PEDAL_CLOSE_WIND_FACTOR = 5.0
I_FLOOR_MIN, I_FLOOR_MAX = -1.0, -0.3


def wind_brake_mps2(v_ego: float) -> float:
  # same table as carcontroller.get_honda_bosch_wind_brake_mps2 (kept here to avoid a circular import)
  return float(np.interp(v_ego, [0.0, 13.4, 22.4, 31.3, 40.2], [0.000, 0.049, 0.136, 0.267, 0.441]))


def pedal_close_accel(v_ego: float) -> float:
  return float(np.clip(-0.75 * PEDAL_CLOSE_WIND_FACTOR * wind_brake_mps2(v_ego), I_FLOOR_MIN, I_FLOOR_MAX))


def lead_needs_brake(v_ego: float, lead_status: bool, d_rel: float, v_rel: float) -> bool:
  if not lead_status:
    return False
  if d_rel < LEAD_GAP_MIN * max(v_ego, 1.0):
    return True
  closing = -v_rel
  return closing > 0.1 and d_rel / closing < LEAD_TTC_MIN


def real_demand(v_ego: float, a_target: float, should_stop: bool, lead_brake: bool, plan_source: str = "cruise") -> bool:
  """True when the planner wants real decel; the brakes must work exactly as before."""
  return (v_ego < MIN_SPEED or should_stop or lead_brake or a_target < A_TARGET_MIN or
          plan_source not in ("cruise", ""))


def friction_request(accel: float, v_ego: float) -> float:
  """Approximate stock 9G friction request (brake units) for an accel command, for LongControl's copy of the gate."""
  return max(0.0, -accel / ACCORD_9G_BRAKE_ACCEL_PER_UNIT - wind_brake_mps2(v_ego) / ACCORD_9G_BRAKE_ACCEL_PER_UNIT - 0.02)


_kill_cache = {"frame": 0, "value": False}


def kill_file_present() -> bool:
  if _kill_cache["frame"] <= 0:
    _kill_cache["value"] = os.path.exists(KILL_FILE)
    _kill_cache["frame"] = KILL_FILE_CHECK_FRAMES
  _kill_cache["frame"] -= 1
  return _kill_cache["value"]


class CruiseBrakeDeadband:
  def __init__(self):
    self.overspeed = False
    self.ramp = 0.0  # friction allowed during an overspeed release (brake units)
    self.clear_t = 0.0
    self.suppressing = False
    self.inputs_valid = False
    self.v_cruise = 0.0
    self.a_target = 0.0
    self.should_stop = False
    self.plan_source = "cruise"
    self.lead_brake = False
    self.csc_active = False

  def set_plan(self, valid: bool, v_cruise: float = 0.0, a_target: float = 0.0, should_stop: bool = False,
               plan_source: str = "cruise", lead_brake: bool = False, csc_active: bool = False):
    """card.py: latest plan inputs (m/s, m/s^2)."""
    self.inputs_valid = bool(valid) and np.isfinite(v_cruise) and np.isfinite(a_target)
    self.v_cruise, self.a_target = float(v_cruise), float(a_target)
    self.should_stop, self.plan_source, self.lead_brake = bool(should_stop), str(plan_source), bool(lead_brake)
    self.csc_active = bool(csc_active)

  def reset(self):
    self.overspeed = False
    self.suppressing = False
    self.ramp = 0.0
    self.clear_t = 0.0

  def update(self, long_pid: bool, v_ego: float, accel_cmd: float, friction_req: float, dt: float) -> float | None:
    """Returns the max friction brake (units) to allow: 0.0 = hold it off, a ramp value after an
    overspeed release, or None = no limit (stock behaviour).
    friction_req: the stock friction request (units) this frame, used to re-arm after an overspeed release."""
    if (not long_pid or not self.inputs_valid or kill_file_present() or accel_cmd < ACCEL_CMD_MIN or self.csc_active or
        real_demand(v_ego, self.a_target, self.should_stop, self.lead_brake, self.plan_source)):
      self.reset()
      return None

    over = v_ego - self.v_cruise
    if over > BAND_EXIT and not self.overspeed:
      self.overspeed = True
      self.ramp = 0.0
      self.clear_t = 0.0
    if self.overspeed:
      # sticky: on a hill that needs the brake, stay stock until the stock request itself lets go
      self.clear_t = self.clear_t + dt if (friction_req <= 0.0 and over < BAND_REENTER) else 0.0
      if self.clear_t < RELEASE_CLEAR_S:
        self.suppressing = False
        self.ramp = min(self.ramp + OVERSPEED_RAMP * dt, 1.0)
        return self.ramp
      self.overspeed = False

    self.suppressing = True
    self.ramp = 0.0
    return 0.0
