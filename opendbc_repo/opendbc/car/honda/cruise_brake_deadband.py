"""Accord 9G (Nidec + pedal interceptor) cruise-hold brake deadband, 7.0 port of the 6.x fix (66485e4a2).

At a steady set speed on a slight downgrade the I-only long PID crosses the friction-brake onset and the Nidec
brake comes on for ~0.5-1.5 s with the pedal still open, so speed ripples around the set speed (6.x routes 33d/352;
7.0 Nov 5-9: 46-54 such pulses per hour of free cruise, median 0.5-1 s).

7.0 actuator mapping (carcontroller): brake = -accel / 4.8, friction brake = brake - wind_brake(v) (so it starts at
accel ~ -4.8 * wind_brake(v), -0.4 m/s^2 at 45 mph, -0.6 at 65), and the pedal closes only at
accel = -4.8 * 0.75 * WIND_FACTOR_HOLD * wind_brake(v) (-0.7 / -1.0 m/s^2). Between the two the car brakes with
the pedal open.

While cruising at or just above the planner's cruise speed with no real decel demand, this gate holds the friction
brake off. The pedal keeps following the accel command down to closed, so the car coasts and may drift up to
BAND_EXIT over the cruise speed. The brakes return at once for a real demand (planner aTarget < A_TARGET_MIN, stop,
lead/e2e plan source, a closing or near lead, curve control, accel cmd < ACCEL_CMD_MIN) and stay stock for
DEMAND_HOLD_S after it ends. They ramp in at OVERSPEED_RAMP when the only reason is overspeed past the band.

card.py feeds the plan (set_plan) and the carcontroller caps the friction request. LongControl runs its own copy on
the same plan inputs and freezes I at pedal_close_accel() while that copy holds the brake off, so the brake doesn't
come on hard when the deadband releases. Switch: param AccordCruiseBrakeDeadband (default on, read about once a
second, no restart).
"""
import numpy as np

MPH = 0.44704
MIN_SPEED = 17.0  # m/s; highway cruise hold only (38 mph)
BAND_EXIT = 2.0 * MPH  # over the cruise speed: brakes allowed again
BAND_REENTER = 1.0 * MPH  # back under this: hold them off again
A_TARGET_MIN = -0.3  # planner decel below this is a real demand
DEMAND_HOLD_S = 2.0  # after any real demand stay stock this long (plan source flickers, lead release tails)
ACCEL_CMD_MIN = -1.5  # PID output below this always gets the brakes
LEAD_TTC_MIN = 20.0  # s; a closing lead nearer than this in time gets the brakes
LEAD_GAP_MIN = 1.0  # s; a lead nearer than this time gap gets the brakes
LEAD_CLOSING_MIN = 0.3  # m/s
OVERSPEED_RAMP = 0.25  # brake units (0..1) per second when the brakes return only because of overspeed
RELEASE_CLEAR_S = 1.0  # after an overspeed release, re-arm only once the stock request has been 0 this long

BRAKE_ACCEL_PER_UNIT = 4.8  # carcontroller.compute_gb_honda_nidec
PEDAL_WIND_FACTOR = 2.3  # pedal_learner.WIND_FACTOR_HOLD (the 9G holds its wind factor)
I_FLOOR_MIN, I_FLOOR_MAX = -1.2, -0.3


def wind_brake(v_ego: float) -> float:
  # same table as carcontroller.update (kept here to avoid a circular import)
  return float(np.interp(v_ego, [0.0, 2.3, 35.0], [0.001, 0.002, 0.15]))


def pedal_close_accel(v_ego: float) -> float:
  """Accel command at which the pedal interceptor command reaches 0 (the car coasts)."""
  return float(np.clip(-BRAKE_ACCEL_PER_UNIT * 0.75 * PEDAL_WIND_FACTOR * wind_brake(v_ego), I_FLOOR_MIN, I_FLOOR_MAX))


def friction_request(accel: float, v_ego: float) -> float:
  """Approximate stock friction request (brake units 0..1) for an accel command, for LongControl's copy of the gate."""
  return max(0.0, -accel / BRAKE_ACCEL_PER_UNIT - wind_brake(v_ego))


def lead_needs_brake(v_ego: float, lead_status: bool, d_rel: float, v_rel: float) -> bool:
  if not lead_status:
    return False
  if d_rel < LEAD_GAP_MIN * max(v_ego, 1.0):
    return True
  closing = -v_rel
  return closing > LEAD_CLOSING_MIN and d_rel / closing < LEAD_TTC_MIN


def real_demand(v_ego: float, a_target: float, should_stop: bool, lead_brake: bool, plan_source: str = "cruise") -> bool:
  """True when the planner wants real decel; the brakes must work exactly as before."""
  return (v_ego < MIN_SPEED or should_stop or lead_brake or a_target < A_TARGET_MIN or
          plan_source not in ("cruise", ""))


class CruiseBrakeDeadband:
  def __init__(self):
    self.enabled = True
    self.overspeed = False
    self.ramp = 0.0  # friction allowed during an overspeed release (brake units)
    self.clear_t = 0.0
    self.demand_t = 0.0  # time since the last real demand
    self.suppressing = False
    self.inputs_valid = False
    self.v_cruise = 0.0
    self.a_target = 0.0
    self.should_stop = False
    self.plan_source = "cruise"
    self.lead_brake = False
    self.curve_active = False
    self.held_frames = 0  # telemetry: frames where a stock friction request was held off

  def set_plan(self, valid: bool, v_cruise: float = 0.0, a_target: float = 0.0, should_stop: bool = False,
               plan_source: str = "cruise", lead_brake: bool = False, curve_active: bool = False, enabled: bool = True):
    """Latest plan inputs (m/s, m/s^2). v_cruise = the speed the planner cruises at (set speed, capped by SLC)."""
    self.enabled = bool(enabled)
    self.inputs_valid = bool(valid) and bool(np.isfinite(v_cruise)) and bool(np.isfinite(a_target)) and v_cruise > 0.0
    self.v_cruise, self.a_target = float(v_cruise), float(a_target)
    self.should_stop, self.plan_source, self.lead_brake = bool(should_stop), str(plan_source), bool(lead_brake)
    self.curve_active = bool(curve_active)

  def reset(self):
    self.overspeed = False
    self.suppressing = False
    self.ramp = 0.0
    self.clear_t = 0.0
    self.demand_t = 0.0

  def update(self, long_pid: bool, v_ego: float, accel_cmd: float, friction_req: float, dt: float) -> float | None:
    """Returns the max friction brake (units 0..1) to allow: 0.0 = hold it off, a ramp value after an overspeed
    release, or None = no limit (stock behaviour). friction_req: the stock friction request (units) this frame."""
    if (not self.enabled or not long_pid or not self.inputs_valid or accel_cmd < ACCEL_CMD_MIN or self.curve_active or
        real_demand(v_ego, self.a_target, self.should_stop, self.lead_brake, self.plan_source)):
      self.reset()
      return None
    self.demand_t += dt
    if self.demand_t < DEMAND_HOLD_S:
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
    if friction_req > 0.0:
      self.held_frames += 1
    return 0.0


def eligible(cp) -> bool:
  """Accord 9G with openpilot long through the pedal interceptor (the only car with this actuator split)."""
  from opendbc.car.honda.nidec_interceptor import qualified as interceptor_qualified
  from opendbc.car.honda.values import CAR
  try:
    return cp.carFingerprint == CAR.HONDA_ACCORD_9G and bool(interceptor_qualified(cp))
  except (AttributeError, TypeError, ValueError):
    return False


def plan_inputs(v_ego: float, set_speed_kph: float, plan, radar, slc) -> dict:
  """Gate inputs from longitudinalPlan, radarState and slcState (slc may be None). Shared by card and controlsd."""
  v_cruise = float(set_speed_kph) / 3.6 if set_speed_kph is not None else 0.0
  curve_active = False
  if slc is not None:
    if bool(slc.hasCeiling) and float(slc.effectiveCap) > 0.0:
      v_cruise = min(v_cruise, float(slc.effectiveCap))
    curve_active = bool(slc.curve.applied or slc.curve.controlling)
  lead_brake = any(lead_needs_brake(v_ego, bool(lead.status), float(lead.dRel), float(lead.vRel))
                   for lead in (radar.leadOne, radar.leadTwo))
  return dict(v_cruise=v_cruise, a_target=float(plan.aTarget), should_stop=bool(plan.shouldStop),
              plan_source=str(plan.longitudinalPlanSource), lead_brake=lead_brake, curve_active=curve_active)
