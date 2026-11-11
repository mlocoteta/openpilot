"""Honda 9G Accord + Torque Interceptor (TI): lateral torque controller.

Port of StarPilot 6.x feature F03 ("TI lateral controls", 6.x commit 531d436634d, final behaviour as on
6.x accord-features-6x 4c89c24dc). On 6.x this lived inside the generic LatControlTorque and controlsd;
on 7.0 it is a separate controller, selected by lateral_controller_factory only when ti_qualified(CP)
holds (the TI safety bit was set at startup), so no other car can reach this code.

What it reproduces from 6.x, for the 9G TI car:
- the 6.x torque control law as it ran on the 9G (curvature request buffer scaled by v^2, jerk-based
  setpoint, low-speed factor, unwind integrator freeze, roll/offset fade, center-chatter friction jerk
  deadzone, standard friction threshold, PID with measurement-rate error)
- the sigmoid+linear torque curve (TISigmoidA/B/C, TISigmoidEnabled, TISigmoidLive)
- TISteerKp replacing the proportional gain table every frame
- the low-speed loop-gain schedule (x0.5 below 7 m/s, full above 10 m/s)
- soft recapture after a real driver override
- the two opt-in low-speed damping policies (TILowSpeedDamping*, TILowSpeedCenterDamping*)
- steer_limited_by_safety from carOutput against the last 3 requests, a driver override only when the TI
  driver-torque limiter binds, and a sustained-limit integrator freeze (update_steer_limited)

Learning is excluded on purpose: this controller is not a LatControlTorque, so 7.0's FLM Auto Learn
(stages, native refinement, global runtime, torque host) and torqued live parameters never touch it;
controlsd also skips constructing them for the TI car. The 6.x car took latAccelFactor/latAccelOffset
from torqued; here they come from CarParams (plus the user's SteerLatAccel/SteerFriction override).
"""
import math
import time
from collections import deque

import numpy as np

from openpilot.cereal import log
from opendbc.car import structs
from opendbc.car.lateral import get_friction
from opendbc.car.honda.torque_interceptor import TI_LIMITS, ti_driver_limiter_binds, ti_driver_torque_limits, ti_qualified  # noqa: F401
from openpilot.common.constants import ACCELERATION_DUE_TO_GRAVITY, CV
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.pid import PIDController
from openpilot.common.swaglog import cloudlog
from openpilot.selfdrive.controls.lib.drive_helpers import MIN_SPEED
from openpilot.selfdrive.controls.lib.latcontrol import LatControl

# ---- 6.x LatControlTorque constants (the values the 9G TI ran with) ----
KP = 0.6
KI = 0.35
INTERP_SPEEDS = [1, 1.5, 2.0, 3.0, 5, 7.5, 10, 15, 30]
KP_INTERP = [250, 120, 65, 30, 11.5, 5.5, 3.5, 2.0, KP]

LOW_SPEED_X = [0, 10, 20, 30]
LOW_SPEED_Y = [12, 10.5, 8, 5]
MAX_LAT_JERK_UP = 2.5            # m/s^3

LP_FILTER_CUTOFF_HZ = 1.2
JERK_GAIN = 0.22
LAT_ACCEL_REQUEST_BUFFER_SECONDS = 1.0
VERSION = 2
UNWIND_D_DES_THRESHOLD = -1.0
UNWIND_LAT_ACCEL_NEAR_ZERO = 0.3
MIN_LATERAL_CONTROL_SPEED = 0.3

# Small planner jerk changes around the lane center can repeatedly re-trigger the friction term.
CENTER_CHATTER_JERK_DEADZONE_SPEED_BP = [0.0, 5.0, 12.0, 25.0]  # m/s
CENTER_CHATTER_JERK_DEADZONE_SPEED_V = [0.08, 0.12, 0.18, 0.18]  # m/s^3
CENTER_CHATTER_JERK_DEADZONE_LAT_ACCEL_BP = [0.0, 0.18, 0.35]  # m/s^2
CENTER_CHATTER_JERK_DEADZONE_LAT_ACCEL_V = [1.0, 1.0, 0.0]

# Roll compensation and latAccelOffset fade out below walking pace.
FF_ROLL_OFFSET_FADE_BP = [0.5, 2.5]  # m/s
FF_ROLL_OFFSET_FADE_V = [0.0, 1.0]

STANDARD_FRICTION_THRESHOLD = 0.30

# Low-speed loop-gain schedule: the TI-driven EPS is 2-3x more responsive at ~2 Hz below 18 mph, so the
# low-speed factor (proportional, friction window, integrator rate) and the friction amplitude are halved
# there (2026-09-26 low-speed ping-pong). Nothing changes above ~22 mph.
TI_9G_LOW_SPEED_GAIN_BP = [7.0, 10.0]  # m/s (15.7 mph -> 22.4 mph)
TI_9G_LOW_SPEED_GAIN_V = [0.5, 1.0]

# Soft recapture after a driver override: the error-driven terms (proportional + friction relay) are held
# at zero while the driver holds the wheel against the controller, then ramped back over TI_RECAPTURE_TIME.
# An override is steeringPressed, or the TI driver-torque limiter holding the output back while the TI
# sensor reads a hand. Rate-limit and guard mismatches are not overrides (2026-09-30 turn-recovery report).
TI_RECAPTURE_TIME = 0.6              # s, ramp of the error-driven terms after release
TI_RECAPTURE_DRIVER_TORQUE = 6       # TI torque sensor counts
TI_RECAPTURE_HOLD_TIME = 0.2         # s, keeps a limiter-detected override latched across short gaps

# carOutput answers the request of 1-3 frames earlier (2 on the 2026-09-26 logs).
TI_OUTPUT_PIPELINE_FRAMES = 3
# A TI output limit that is not a driver override (rate limit, guards) freezes the integrator only once
# it has lasted this long.
TI_SUSTAINED_LIMIT_FRAMES = 10

# Live params cadence (6.x controlsd: every 100th frame, ~1 s).
TI_LIVE_PARAMS_INTERVAL = 100

# ---- 2026-11-11 feed-forward tuning (all opt-in; the defaults reproduce the controller above exactly) ----
# TIOffsetFF: constant lateral-accel offset added to the feed-forward (m/s^2, signed). The 9G TI needs about
# -0.10..-0.15 of full-scale torque to hold a straight, unbanked line, which the integrator carried
# (I mean -0.14/-0.16/-0.18 m/s^2 at 30-45/45-60/60+ mph on Nov 5-11). It is scheduled by speed like the
# measured integrator bias, so city driving is untouched. Recommended trial value -0.15.
TI_OFFSET_FF_SPEED_BP = [8.0, 11.0, 17.0, 22.0]  # m/s (18 / 25 / 38 / 49 mph)
TI_OFFSET_FF_SPEED_V = [0.0, 0.45, 0.85, 1.0]
TI_OFFSET_FF_LIMIT = 0.4
# TIRollCompRatio: share of road roll (roll * g) the feed-forward subtracts. 1.0 = as before; the logs fit
# 0.74-0.88 (Nov 8-11: 0.81 at 30-45 mph, 0.74 at 45-60). Recommended trial value 0.8.
TI_ROLL_RATIO_MIN, TI_ROLL_RATIO_MAX = 0.5, 1.0
# TIFrictionHighway: friction feed-forward amplitude above 45 mph (blended in from 38 mph). 0 = off (SteerFriction
# everywhere). The on-centre EPS dead band is 0.29-0.50 of full-scale torque wide; SteerFriction 0.19 covers about
# half. Candidates 0.25 / 0.30 (replay: 0.30 cuts tracking error 14 %, raises torque spread 20 %).
TI_FRICTION_HWY_SPEED_BP = [17.0, 20.0]  # m/s (38 -> 45 mph)
TI_FRICTION_HWY_MIN, TI_FRICTION_HWY_MAX = 0.10, 0.40
# TIABEnabled: interleaved A/B. The three settings above apply only in B slots; A slots run the baseline.
# Slots alternate every TI_AB_SLOT_S of time.monotonic() (= the logMonoTime clock), so the slot of any logged
# frame is floor(logMonoTime / 1e9 / TI_AB_SLOT_S) % 2 (1 = B). Changes ramp over TI_AB_RAMP_S.
TI_AB_SLOT_S = 300.0
TI_AB_RAMP_S = 2.0


def ti_ab_slot_is_b(mono_s: float) -> bool:
  return int(mono_s // TI_AB_SLOT_S) % 2 == 1


def ti_offset_ff_scale(v_ego: float) -> float:
  return float(np.interp(v_ego, TI_OFFSET_FF_SPEED_BP, TI_OFFSET_FF_SPEED_V))

# Sigmoid+linear torque curve: torque(x) = b*sign(a*x)*(sigmoid(|a*x|) - 0.5) + c*x, x = lateral accel.
# Slope at x=0 is a*b/4 + c. Defaults are the code defaults of 6.x (used when a param is unset/invalid).
TI_SIGMOID_DEFAULT = (15.0, 0.72, 0.16)
TI_DEFAULT_KP = 0.3

# Low-speed damping (opt-in): reversal-gated Accord TI policy.
HONDA_ACCORD_LOW_SPEED_DAMPING_MIN_SPEED = 2.5
HONDA_ACCORD_LOW_SPEED_DAMPING_MAX_SPEED = 8.2
HONDA_ACCORD_LOW_SPEED_DAMPING_SPEED_WIDTH = 0.70
HONDA_ACCORD_LOW_SPEED_DAMPING_LAT_ACCEL = 1.20
HONDA_ACCORD_LOW_SPEED_DAMPING_LAT_WIDTH = 0.25
HONDA_ACCORD_LOW_SPEED_DAMPING_ALPHA_REDUCTION = 0.35
# MoreTore-style continuous center damper (opt-in, mutually exclusive with the reversal-gated policy).
HONDA_ACCORD_CENTER_DAMPING_MIN_SPEED = 2.5
HONDA_ACCORD_CENTER_DAMPING_MIN_SPEED_WIDTH = 0.7
HONDA_ACCORD_CENTER_DAMPING_MAX_SPEED = 8.2
HONDA_ACCORD_CENTER_DAMPING_MAX_SPEED_WIDTH = 0.6
HONDA_ACCORD_CENTER_DAMPING_LAT_ACCEL = 0.17
HONDA_ACCORD_CENTER_DAMPING_LAT_WIDTH = 0.04
HONDA_ACCORD_CENTER_DAMPING_OUTPUT_LIMIT = 0.38
HONDA_ACCORD_CENTER_DAMPING_OUTPUT_SCALE_MIN = 0.62
HONDA_ACCORD_CENTER_DAMPING_OUTPUT_ALPHA_MIN = 0.28


def ti_lateral_qualified(CP) -> bool:
  """The TI lateral controller drives this car: TI is on for the drive and the car is torque-steered."""
  return bool(ti_qualified(CP) and CP.steerControlType == structs.CarParams.SteerControlType.torque and
              CP.lateralTuning.which() == 'torque')


def build_sigmoid_tables(a, b, c):
  lataccel_values = np.arange(-8.0, 8.0, 0.01)
  sig_input = a * lataccel_values
  sig = np.sign(sig_input) * (1.0 / (1.0 + np.exp(-np.abs(sig_input))) - 0.5)
  torque_values = sig * b + lataccel_values * c
  return torque_values, lataccel_values


def get_ti_9g_low_speed_gain_scale(v_ego):
  return float(np.interp(v_ego, TI_9G_LOW_SPEED_GAIN_BP, TI_9G_LOW_SPEED_GAIN_V))


def get_center_chatter_friction_jerk_deadzone(v_ego, setpoint, vehicle_deadzone=0.0):
  speed_deadzone = np.interp(max(v_ego, 0.0), CENTER_CHATTER_JERK_DEADZONE_SPEED_BP, CENTER_CHATTER_JERK_DEADZONE_SPEED_V)
  center_weight = np.interp(abs(setpoint), CENTER_CHATTER_JERK_DEADZONE_LAT_ACCEL_BP, CENTER_CHATTER_JERK_DEADZONE_LAT_ACCEL_V)
  return max(float(vehicle_deadzone), float(speed_deadzone * center_weight))


def get_standard_friction_threshold(v_ego: float) -> float:
  base = float(np.interp(v_ego, [1 * CV.MPH_TO_MS, 20 * CV.MPH_TO_MS, 75 * CV.MPH_TO_MS], [0.16, 0.19, 0.27]))
  return max(base, STANDARD_FRICTION_THRESHOLD)


def _sigmoid(x: float) -> float:
  if x >= 0.0:
    return 1.0 / (1.0 + math.exp(-x))
  z = math.exp(x)
  return z / (1.0 + z)


def get_honda_accord_low_speed_damped_output(output_torque: float, prev_output_torque: float,
                                              desired_lateral_accel: float, v_ego: float,
                                              max_reduction: float, activation: float = 1.0) -> tuple[float, float, float]:
  """Smooth TI output only during a detected low-speed reversal episode (opt-in)."""
  speed_weight = (_sigmoid((v_ego - HONDA_ACCORD_LOW_SPEED_DAMPING_MIN_SPEED) / HONDA_ACCORD_LOW_SPEED_DAMPING_SPEED_WIDTH) *
                  _sigmoid((HONDA_ACCORD_LOW_SPEED_DAMPING_MAX_SPEED - v_ego) / HONDA_ACCORD_LOW_SPEED_DAMPING_SPEED_WIDTH))
  lat_weight = _sigmoid((HONDA_ACCORD_LOW_SPEED_DAMPING_LAT_ACCEL - abs(desired_lateral_accel)) / HONDA_ACCORD_LOW_SPEED_DAMPING_LAT_WIDTH)
  envelope = speed_weight * lat_weight * float(np.clip(activation, 0.0, 1.0))
  reduction = min(max(float(max_reduction), 0.0), 0.25) * envelope
  scale = 1.0 - reduction
  alpha = 1.0 - HONDA_ACCORD_LOW_SPEED_DAMPING_ALPHA_REDUCTION * envelope
  damped = prev_output_torque + alpha * ((output_torque * scale) - prev_output_torque)
  return float(damped), float(scale), float(envelope)


def get_honda_accord_continuous_center_damped_output(output_torque: float, prev_output_torque: float,
                                                      desired_lateral_accel: float, v_ego: float,
                                                      max_reduction: float = 0.62) -> tuple[float, float, float]:
  """MoreTore-style continuous small-signal center damping (opt-in)."""
  speed_weight = (_sigmoid((v_ego - HONDA_ACCORD_CENTER_DAMPING_MIN_SPEED) / HONDA_ACCORD_CENTER_DAMPING_MIN_SPEED_WIDTH) *
                  _sigmoid((HONDA_ACCORD_CENTER_DAMPING_MAX_SPEED - v_ego) / HONDA_ACCORD_CENTER_DAMPING_MAX_SPEED_WIDTH))
  center_weight = _sigmoid((HONDA_ACCORD_CENTER_DAMPING_LAT_ACCEL - abs(desired_lateral_accel)) / HONDA_ACCORD_CENTER_DAMPING_LAT_WIDTH)
  envelope = speed_weight * center_weight
  capped_reduction = float(np.clip(max_reduction, 0.0, 0.75))
  output_limit = 1.0 - (capped_reduction * envelope)
  limited_output = float(np.clip(output_torque, -output_limit, output_limit))
  output_scale = 1.0 - ((1.0 - HONDA_ACCORD_CENTER_DAMPING_OUTPUT_SCALE_MIN) * envelope)
  output_alpha = 1.0 - ((1.0 - HONDA_ACCORD_CENTER_DAMPING_OUTPUT_ALPHA_MIN) * envelope)
  damped = prev_output_torque + output_alpha * ((limited_output * output_scale) - prev_output_torque)
  return float(damped), float(output_scale), float(envelope)


class TiLiveParams:
  """Typed reads of the TI params with the 6.x semantics (unset/0 -> code default)."""
  def __init__(self, params=None):
    self._params = params

  @property
  def params(self):
    if self._params is None:
      from openpilot.common.params import Params
      self._params = Params()
    return self._params

  def _get(self, key):
    getter = getattr(self.params, 'get_value', None)
    if getter is not None:  # test doubles
      return getter(key)
    return self.params.get(key, return_default=True)

  def get_bool(self, key) -> bool:
    value = self._get(key)
    if isinstance(value, (bytes, str)):
      return value in (b'1', '1')
    return bool(value)

  def get_float(self, key) -> float:
    value = self._get(key)
    if value is None or value == b'' or value == '':
      return 0.0
    value = float(value)
    return value if math.isfinite(value) else 0.0

  def get_optional_float(self, key):
    try:
      value = self._get(key)
      value = None if value is None or value in (b'', '') else float(value)
    except (TypeError, ValueError):
      return None
    return value if value is not None and math.isfinite(value) else None


def _user_override(value, stock_marker, cp_value):
  """6.x/7.0 legacy SteerLatAccel/SteerFriction semantics: custom only if set and not the stock value."""
  if value is None or value <= 0.0:
    return cp_value
  if round(value, 2) == round(cp_value, 2) or (stock_marker is not None and math.isclose(value, stock_marker, abs_tol=1e-6)):
    return cp_value
  return value


class LatControlTorqueTI(LatControl):
  def __init__(self, CP, CI, dt, params=None):
    super().__init__(CP, CI, dt)
    self.live_params = TiLiveParams(params)
    self.torque_params = CP.lateralTuning.torque.as_builder()
    self.pid = PIDController([INTERP_SPEEDS, KP_INTERP], KI, rate=1/self.dt)
    self.steering_angle_deadzone_deg = self.torque_params.steeringAngleDeadzoneDeg
    self.request_buffer_len = int(LAT_ACCEL_REQUEST_BUFFER_SECONDS / self.dt)
    self.curvature_request_buffer = deque([0.] * self.request_buffer_len, maxlen=self.request_buffer_len)
    self.jerk_filter = FirstOrderFilter(0.0, 1 / (2 * np.pi * LP_FILTER_CUTOFF_HZ), self.dt)
    self.previous_measurement = 0.0
    self.measurement_rate_filter = FirstOrderFilter(0.0, 1 / (2 * np.pi * (MAX_LAT_JERK_UP - 0.5)), self.dt)
    self.low_speed_reset_threshold = max(CP.minSteerSpeed, MIN_LATERAL_CONTROL_SPEED)
    self.steer_release_i_decay = 0.8
    self.prev_steering_pressed = False
    self.prev_output_torque = 0.0
    self.prev_desired_lateral_accel = 0.0

    # Low-speed damping policies (opt-in params).
    self.honda_accord_low_speed_damping_enabled = False
    self.honda_accord_low_speed_damping_max = 0.12
    self.honda_accord_continuous_center_damping_enabled = False
    self.honda_accord_continuous_center_damping_max_reduction = 0.62
    self.honda_accord_damping_prev_raw_output = 0.0
    self.honda_accord_damping_prev_error = 0.0
    self.honda_accord_damping_prev_setpoint = 0.0
    self.honda_accord_damping_hold_frames = 0
    self.ti_low_speed_damping_active = False
    self.ti_low_speed_damping_scale = 1.0

    # Always on for the TI car (6.x controlsd enabled both at startup).
    self.ti_low_speed_gain_schedule_enabled = True
    self.ti_recapture_enabled = True
    self.ti_recapture_gain = 1.0
    self.ti_override_hold = 0.0
    self.ti_driver_override = False

    # steer_limited_by_safety state (6.x controlsd _update_ti_steer_limited).
    self.steer_limited_by_safety = False
    self._ti_torque_requests = deque([0.0] * TI_OUTPUT_PIPELINE_FRAMES, maxlen=TI_OUTPUT_PIPELINE_FRAMES)
    self._ti_driver_bound = deque([False] * TI_OUTPUT_PIPELINE_FRAMES, maxlen=TI_OUTPUT_PIPELINE_FRAMES)
    self._ti_limited_frames = 0

    # Telemetry kept on the controller (no capnp fields on 7.0, see the F03 port notes).
    self.low_speed_factor = 0.0
    self.friction_threshold = 0.0
    self.friction_scale = 0.0
    self.feedforward = 0.0
    self.unwind_detected = False

    # Feed-forward tuning (TIOffsetFF / TIRollCompRatio / TIFrictionHighway / TIABEnabled), see the constants.
    self.offset_ff = 0.0
    self.roll_comp_ratio = 1.0
    self.friction_hwy = 0.0
    self.ab_enabled = False
    self.ab_slot_b = False
    self.ab_weight = 1.0  # 0 = baseline, 1 = the configured values
    self._mono = time.monotonic  # replaceable clock (tests / replay)

    self._frame = 0
    self._kp = None
    self._error_logged_time = -1e9
    self.sigmoid_params = None
    self._apply_user_torque_overrides()
    self._init_torque_curve()
    self.refresh_live_params()

  # ---- torque curve ----
  def _init_torque_curve(self):
    """Startup curve, as 6.x CarInterface.torque_from_lateral_accel() chose it for the TI car."""
    try:
      if self.live_params.get_bool("TISigmoidEnabled"):
        a, b, c = (self.live_params.get_float(k) for k in ("TISigmoidA", "TISigmoidB", "TISigmoidC"))
        self.set_sigmoid(*((a, b, c) if a > 0 and b > 0 and c > 0 else TI_SIGMOID_DEFAULT))
        return
    except Exception:
      cloudlog.exception("latcontrol_torque_ti: TI sigmoid params unreadable at startup, using the code default")
      self.set_sigmoid(*TI_SIGMOID_DEFAULT)
      return
    self.reset_to_linear()

  def set_sigmoid(self, a, b, c):
    torque_values, lataccel_values = build_sigmoid_tables(a, b, c)
    self.torque_from_lateral_accel = lambda lat_accel, tp: float(np.interp(lat_accel, lataccel_values, torque_values))
    self.lateral_accel_from_torque = lambda torque, tp: float(np.interp(torque, torque_values, lataccel_values))
    self.sigmoid_params = (a, b, c)
    self.update_limits()

  def reset_to_linear(self):
    self.torque_from_lateral_accel = lambda lat_accel, tp: lat_accel / float(tp.latAccelFactor)
    self.lateral_accel_from_torque = lambda torque, tp: torque * float(tp.latAccelFactor)
    self.sigmoid_params = None
    self.update_limits()

  def update_limits(self):
    self.pid.set_limits(self.lateral_accel_from_torque(self.steer_max, self.torque_params),
                        self.lateral_accel_from_torque(-self.steer_max, self.torque_params))

  def _apply_user_torque_overrides(self):
    lp = self.live_params
    try:
      self.torque_params.latAccelFactor = _user_override(lp.get_optional_float("SteerLatAccel"), lp.get_optional_float("SteerLatAccelStock"),
                                                         float(self.torque_params.latAccelFactor))
      self.torque_params.friction = _user_override(lp.get_optional_float("SteerFriction"), lp.get_optional_float("SteerFrictionStock"),
                                                   float(self.torque_params.friction))
    except Exception:
      cloudlog.exception("latcontrol_torque_ti: SteerLatAccel/SteerFriction unreadable, using CarParams")

  # ---- live params (6.x controlsd _update_ti_live_params) ----
  def _read_kp(self):
    kp = self.live_params.get_float("TISteerKp") or TI_DEFAULT_KP
    return [[0], [kp]] if kp > 0 else [[0], [TI_DEFAULT_KP]]

  def refresh_live_params(self):
    lp = self.live_params
    try:
      if not lp.get_bool("TISigmoidEnabled"):
        if self.sigmoid_params is not None:
          self.reset_to_linear()
      elif lp.get_bool("TISigmoidLive"):
        a, b, c = lp.get_float("TISigmoidA"), lp.get_float("TISigmoidB"), lp.get_float("TISigmoidC")
        if a > 0 and b > 0 and c > 0 and (a, b, c) != self.sigmoid_params:
          self.set_sigmoid(a, b, c)
      self._kp = self._read_kp()
      self.update_low_speed_damping(lp.get_bool("TILowSpeedDampingEnabled"),
                                    lp.get_float("TILowSpeedDampingMax") or 0.12,
                                    lp.get_bool("TILowSpeedCenterDampingEnabled"),
                                    lp.get_float("TILowSpeedCenterDampingMaxReduction") or 0.62)
      self.update_ff_tuning(lp.get_optional_float("TIOffsetFF"), lp.get_optional_float("TIRollCompRatio"),
                            lp.get_optional_float("TIFrictionHighway"), lp.get_bool("TIABEnabled"))
    except Exception:
      # Keep the last good values, but never fail silently (rate-limited).
      now = time.monotonic()
      if now - self._error_logged_time > 60.0:
        self._error_logged_time = now
        cloudlog.exception("latcontrol_torque_ti: TI live parameter update failed")

  def lateral_kp(self):
    return self._kp if self._kp is not None else [[0], [TI_DEFAULT_KP]]

  def update_low_speed_damping(self, enabled, max_reduction, continuous_center_enabled=False, continuous_center_max_reduction=0.62):
    self.honda_accord_low_speed_damping_enabled = bool(enabled)
    self.honda_accord_low_speed_damping_max = float(np.clip(max_reduction, 0.0, 0.25))
    self.honda_accord_continuous_center_damping_enabled = bool(continuous_center_enabled)
    self.honda_accord_continuous_center_damping_max_reduction = float(np.clip(continuous_center_max_reduction, 0.0, 0.75))
    # A/B alternatives: the continuous policy takes priority, they never stack.
    if self.honda_accord_continuous_center_damping_enabled:
      self.honda_accord_low_speed_damping_enabled = False
    if not self.honda_accord_low_speed_damping_enabled:
      self.honda_accord_damping_prev_raw_output = 0.0
      self.honda_accord_damping_prev_error = 0.0
      self.honda_accord_damping_prev_setpoint = 0.0
      self.honda_accord_damping_hold_frames = 0

  def update_ff_tuning(self, offset_ff, roll_ratio, friction_hwy, ab_enabled=False):
    """Unset, non-finite or out-of-range values fall back to the baseline (offset 0, ratio 1, friction off)."""
    offset_ff, roll_ratio, friction_hwy = (v if v is not None and math.isfinite(v) else None for v in (offset_ff, roll_ratio, friction_hwy))
    self.offset_ff = float(np.clip(offset_ff, -TI_OFFSET_FF_LIMIT, TI_OFFSET_FF_LIMIT)) if offset_ff else 0.0
    self.roll_comp_ratio = (float(np.clip(roll_ratio, TI_ROLL_RATIO_MIN, TI_ROLL_RATIO_MAX))
                            if roll_ratio is not None and roll_ratio > 0.0 else 1.0)
    self.friction_hwy = (float(np.clip(friction_hwy, TI_FRICTION_HWY_MIN, TI_FRICTION_HWY_MAX))
                         if friction_hwy is not None and friction_hwy > 0.0 else 0.0)
    self.ab_enabled = bool(ab_enabled)

  @property
  def ff_tuning_configured(self) -> bool:
    return self.offset_ff != 0.0 or self.roll_comp_ratio != 1.0 or self.friction_hwy > 0.0

  def _update_ab_weight(self) -> float:
    """Blend weight of the configured tuning: 1 without A/B, else ramps to 1 in B slots and to 0 in A slots."""
    if not self.ab_enabled:
      self.ab_slot_b = False
      self.ab_weight = 1.0
      return 1.0
    slot_b = ti_ab_slot_is_b(self._mono())
    if slot_b != self.ab_slot_b:
      self.ab_slot_b = slot_b
      cloudlog.event("ti_ab_slot", slot="B" if slot_b else "A", offset_ff=self.offset_ff, roll_ratio=self.roll_comp_ratio,
                     friction_hwy=self.friction_hwy)
    target = 1.0 if slot_b else 0.0
    step = self.dt / TI_AB_RAMP_S
    self.ab_weight = float(np.clip(target, self.ab_weight - step, self.ab_weight + step))
    return self.ab_weight

  # ---- soft recapture ----
  def set_ti_driver_override(self, override):
    self.ti_driver_override = bool(override)

  def update_ti_recapture(self, CS):
    """Scale for the error-driven terms: 0 during a driver override, ramping to 1 after release."""
    if not self.ti_recapture_enabled:
      return 1.0
    hand_on = abs(float(CS.steeringTorque)) >= TI_RECAPTURE_DRIVER_TORQUE
    if CS.steeringPressed or (self.ti_driver_override and hand_on):
      self.ti_override_hold = TI_RECAPTURE_HOLD_TIME
    else:
      self.ti_override_hold = max(self.ti_override_hold - self.dt, 0.0)
    if CS.steeringPressed or self.ti_override_hold > 0.0:
      self.ti_recapture_gain = 0.0
    else:
      self.ti_recapture_gain = min(self.ti_recapture_gain + self.dt / TI_RECAPTURE_TIME, 1.0)
    return self.ti_recapture_gain

  # ---- steer_limited_by_safety (called from controlsd.publish, after this frame's request) ----
  def update_steer_limited(self, lat_active, requested_torque, ti_output_torque, driver_torque) -> bool:
    """Was the lateral request limited on its way to the TI?

    carOutput reaches controlsd 1-3 frames after the request it answers, so the TI output is compared with
    the recent requests: limited only if it matches none of them. Only a limit caused by the driver (the TI
    driver-torque limiter bound one of the recent requests) is an override; it feeds soft recapture. The
    integrator freezes on an override, or on any other limit that lasts TI_SUSTAINED_LIMIT_FRAMES. The
    driver limiter is evaluated with the carcontroller's pairing: the previous frame's request with this
    frame's TI sensor reading. Runs whenever lateral is active, engaged or not.
    """
    if not lat_active:
      self.steer_limited_by_safety = False
      self.ti_driver_override = False
      self._ti_limited_frames = 0
      self._ti_torque_requests.extend([0.0] * TI_OUTPUT_PIPELINE_FRAMES)
      self._ti_driver_bound.extend([False] * TI_OUTPUT_PIPELINE_FRAMES)
      return False
    last_request = round(self._ti_torque_requests[-1] * TI_LIMITS.TI_STEER_MAX)
    self._ti_driver_bound.append(ti_driver_limiter_binds(last_request, float(driver_torque), TI_LIMITS))
    limited = all(abs(req - ti_output_torque) > 1e-2 for req in self._ti_torque_requests)
    self._ti_limited_frames = self._ti_limited_frames + 1 if limited else 0
    self.ti_driver_override = limited and any(self._ti_driver_bound)
    self.steer_limited_by_safety = self.ti_driver_override or self._ti_limited_frames >= TI_SUSTAINED_LIMIT_FRAMES
    self._ti_torque_requests.append(float(requested_torque))
    return self.steer_limited_by_safety

  def controls_steer_limited(self, CC, CS, CO) -> bool:
    """controlsd hook: same signature-free inputs as the stock check."""
    return self.update_steer_limited(bool(CC.latActive), float(CC.actuators.torque),
                                     float(CO.actuatorsOutput.torque), float(CS.steeringTorque))

  # ---- control law ----
  def update(self, active, CS, VM, params, steer_limited_by_safety, desired_curvature, curvature_limited, lat_delay):
    # 6.x controlsd order: Kp from the last live read, then the ~1 s live read, then the controller.
    self.pid._k_p = self.lateral_kp()
    self._frame += 1
    if self._frame % TI_LIVE_PARAMS_INTERVAL == 0:
      self.refresh_live_params()

    pid_log = log.ControlsState.LateralTorqueState.new_message()
    pid_log.version = VERSION
    measured_curvature = -VM.calc_curvature(math.radians(CS.steeringAngleDeg - params.angleOffsetDeg), CS.vEgo, params.roll)
    measurement = measured_curvature * CS.vEgo ** 2
    future_desired_lateral_accel = desired_curvature * CS.vEgo ** 2
    if not active:
      output_torque = 0.0
      self.prev_output_torque = 0.0
      pid_log.active = False
      self._clear_telemetry()
      self.pid.reset()
      # Keep the request buffer primed with the live command (it tracks the measured curvature while inactive).
      self.curvature_request_buffer.append(desired_curvature)
      self.previous_measurement = measurement
      self.measurement_rate_filter.x = 0.0
      self.jerk_filter.x = 0.0
      self.prev_desired_lateral_accel = future_desired_lateral_accel
      self.ti_recapture_gain = 1.0
      self.ti_override_hold = 0.0
    else:
      if self.prev_steering_pressed and not CS.steeringPressed:
        self.pid.i *= self.steer_release_i_decay

      tuning_weight = self._update_ab_weight() if self.ff_tuning_configured else 0.0
      roll_offset_fade = np.interp(CS.vEgo, FF_ROLL_OFFSET_FADE_BP, FF_ROLL_OFFSET_FADE_V)
      roll_compensation = params.roll * ACCELERATION_DUE_TO_GRAVITY * roll_offset_fade
      if tuning_weight > 0.0 and self.roll_comp_ratio != 1.0:
        roll_compensation *= 1.0 + tuning_weight * (self.roll_comp_ratio - 1.0)
      curvature_deadzone = abs(VM.calc_curvature(math.radians(self.steering_angle_deadzone_deg), CS.vEgo, 0.0))
      lateral_accel_deadzone = curvature_deadzone * CS.vEgo ** 2

      delay_frames = int(np.clip(lat_delay / self.dt, 1, self.request_buffer_len))
      expected_lateral_accel = self.curvature_request_buffer[-delay_frames] * CS.vEgo ** 2
      self.curvature_request_buffer.append(desired_curvature)
      raw_lateral_jerk = (future_desired_lateral_accel - expected_lateral_accel) / max(lat_delay, self.dt)
      raw_lateral_jerk = np.clip(raw_lateral_jerk, -MAX_LAT_JERK_UP, MAX_LAT_JERK_UP)
      desired_lateral_jerk = np.clip(self.jerk_filter.update(raw_lateral_jerk), -MAX_LAT_JERK_UP, MAX_LAT_JERK_UP)
      gravity_adjusted_future_lateral_accel = future_desired_lateral_accel - roll_compensation
      setpoint = expected_lateral_accel + desired_lateral_jerk * lat_delay
      desired_lateral_accel_rate = (setpoint - self.prev_desired_lateral_accel) / self.dt
      unwind_detected = desired_lateral_accel_rate < UNWIND_D_DES_THRESHOLD and abs(setpoint) < UNWIND_LAT_ACCEL_NEAR_ZERO
      self.prev_desired_lateral_accel = setpoint

      measurement_rate = self.measurement_rate_filter.update((measurement - self.previous_measurement) / self.dt)
      measurement_rate = np.clip(measurement_rate, -MAX_LAT_JERK_UP, MAX_LAT_JERK_UP)
      self.previous_measurement = measurement

      low_speed_factor = (np.interp(CS.vEgo, LOW_SPEED_X, LOW_SPEED_Y) / max(CS.vEgo, MIN_SPEED)) ** 2
      ti_low_speed_gain_scale = get_ti_9g_low_speed_gain_scale(CS.vEgo) if self.ti_low_speed_gain_schedule_enabled else 1.0
      low_speed_factor *= ti_low_speed_gain_scale
      current_kp = np.interp(CS.vEgo, self.pid._k_p[0], self.pid._k_p[1])
      error = setpoint - measurement
      error_with_lsf = error * (1 + low_speed_factor / max(current_kp, 1e-3))
      error_with_lsf *= self.update_ti_recapture(CS)

      pid_log.error = float(error_with_lsf)
      ff = gravity_adjusted_future_lateral_accel
      # latAccelOffset corrects roll compensation bias from device roll misalignment relative to car roll
      ff -= self.torque_params.latAccelOffset * roll_offset_fade
      friction_threshold = get_standard_friction_threshold(CS.vEgo)
      friction_jerk_deadzone = get_center_chatter_friction_jerk_deadzone(CS.vEgo, setpoint)
      friction_jerk = math.copysign(max(abs(desired_lateral_jerk) - friction_jerk_deadzone, 0.0), desired_lateral_jerk)
      friction_scale = ti_low_speed_gain_scale
      friction_ff = friction_scale * get_friction(error_with_lsf + JERK_GAIN * friction_jerk, lateral_accel_deadzone,
                                                  friction_threshold, self.torque_params)
      if tuning_weight > 0.0 and self.friction_hwy > 0.0 and self.torque_params.friction > 0.0:
        hwy = tuning_weight * float(np.interp(CS.vEgo, TI_FRICTION_HWY_SPEED_BP, [0.0, 1.0]))
        friction_ff *= 1.0 + hwy * (self.friction_hwy / float(self.torque_params.friction) - 1.0)
      ff += friction_ff
      if tuning_weight > 0.0 and self.offset_ff != 0.0:
        ff += tuning_weight * self.offset_ff * ti_offset_ff_scale(CS.vEgo)

      if CS.vEgo < self.low_speed_reset_threshold:
        self.pid.reset()
      freeze_integrator = (steer_limited_by_safety or CS.steeringPressed or
                           CS.vEgo < self.low_speed_reset_threshold or unwind_detected)
      output_lataccel = self.pid.update(pid_log.error, error_rate=-measurement_rate, speed=CS.vEgo, feedforward=ff,
                                        freeze_integrator=freeze_integrator)
      output_torque = self.torque_from_lateral_accel(output_lataccel, self.torque_params)

      damping_scale = 1.0
      damping_envelope = 0.0
      if self.honda_accord_continuous_center_damping_enabled:
        output_torque, damping_scale, damping_envelope = get_honda_accord_continuous_center_damped_output(
          output_torque, self.prev_output_torque, setpoint, CS.vEgo, self.honda_accord_continuous_center_damping_max_reduction)
      elif self.honda_accord_low_speed_damping_enabled:
        # Only intervene when the output or tracking error reverses while the requested turn direction stays
        # stable (the TI ping-pong signature); a short hold damps the following limiter steps.
        raw_output_torque = float(output_torque)
        stable_turn = abs(setpoint) > 0.15 and setpoint * self.honda_accord_damping_prev_setpoint > 0.0
        output_reversal = raw_output_torque * self.honda_accord_damping_prev_raw_output < -0.0025
        error_reversal = error * self.honda_accord_damping_prev_error < -0.0025
        if stable_turn and (output_reversal or error_reversal):
          self.honda_accord_damping_hold_frames = max(self.honda_accord_damping_hold_frames, int(0.30 / self.dt))
        activation = min(1.0, self.honda_accord_damping_hold_frames * self.dt / 0.30)
        output_torque, damping_scale, damping_envelope = get_honda_accord_low_speed_damped_output(
          output_torque, self.prev_output_torque, setpoint, CS.vEgo, self.honda_accord_low_speed_damping_max, activation)
        self.honda_accord_damping_hold_frames = max(0, self.honda_accord_damping_hold_frames - 1)
        self.honda_accord_damping_prev_raw_output = raw_output_torque
        self.honda_accord_damping_prev_error = float(error)
        self.honda_accord_damping_prev_setpoint = float(setpoint)

      pid_log.active = True
      pid_log.p = float(self.pid.p)
      pid_log.i = float(self.pid.i)
      pid_log.d = float(self.pid.d)
      pid_log.f = float(self.pid.f)
      pid_log.output = float(-output_torque)
      pid_log.actualLateralAccel = float(measurement)
      pid_log.desiredLateralAccel = float(setpoint)
      pid_log.desiredLateralJerk = float(desired_lateral_jerk)
      self.low_speed_factor = float(low_speed_factor)
      self.friction_threshold = float(friction_threshold)
      self.friction_scale = float(friction_scale)
      self.feedforward = float(ff)
      self.unwind_detected = bool(unwind_detected)
      self.ti_low_speed_damping_active = bool(damping_envelope > 0.05)
      self.ti_low_speed_damping_scale = float(damping_scale)
      pid_log.saturated = bool(self._check_saturation(self.steer_max - abs(output_torque) < 1e-3, CS, steer_limited_by_safety,
                                                      curvature_limited))
      self.prev_output_torque = float(output_torque)

    self.prev_steering_pressed = CS.steeringPressed
    # TODO left is positive in this convention
    return -output_torque, 0.0, pid_log

  def _clear_telemetry(self):
    self.low_speed_factor = self.friction_threshold = self.friction_scale = self.feedforward = 0.0
    self.unwind_detected = False
    self.ti_low_speed_damping_active = False
    self.ti_low_speed_damping_scale = 1.0
