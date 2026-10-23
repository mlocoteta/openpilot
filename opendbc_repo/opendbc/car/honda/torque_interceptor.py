"""Honda 9G Accord gen1 Torque Interceptor (TI).

The 9G Accord has no factory LKAS, so 0xE4 STEERING_CONTROL reaches nothing. Lateral exists
only through an aftermarket TI board on bus 0: openpilot sends 0x249 TI_STEERING_CONTROL and
the board reports 0x24A TI_FEEDBACK. Everything TI-specific lives in this module; the shared
Honda files only construct these classes when ti_qualified(CP) holds.

Switching TI on is a startup decision (apply_torque_interceptor, called from openpilot's vehicle
startup preferences): it sets HondaSafetyFlags.TORQUE_INTERCEPTOR in the Nidec safety param,
which is the only thing that lets the panda transmit 0x249 (honda_ti.h). Every other check in
7.0 that compares the exact Nidec safety param (pedal interceptor, stock AOL) sees the param
with this bit masked out, or deliberately does not (stock AOL stays off on the TI car).
"""
import math
from collections import deque

import numpy as np

from opendbc.car import structs
from opendbc.car.carlog import carlog
from opendbc.car.honda.values import CAR, HondaSafetyFlags

TI_SAFETY_PARAM = int(HondaSafetyFlags.TORQUE_INTERCEPTOR)
# Nidec safety words of the 9G with and without the gas pedal interceptor (NIDEC_ALT, + GAS_INTERCEPTOR).
TI_BASE_SAFETY_PARAMS = (int(HondaSafetyFlags.NIDEC_ALT),
                         int(HondaSafetyFlags.NIDEC_ALT | HondaSafetyFlags.GAS_INTERCEPTOR))
# FrogPilot/6.x TI tune; the board adds its own lag on top of the EPS.
TI_STEER_ACTUATOR_DELAY = 0.5


class TI_LIMITS:
  # Honda 9G Accord Torque Interceptor steering limits (separate CAN device).
  TI_STEER_MAX = 599                 # theoretical max_steer 2047
  TI_STEER_DELTA_UP = 15             # torque increase per refresh
  TI_STEER_DELTA_DOWN = 15           # torque decrease per refresh
  TI_STEER_DRIVER_ALLOWANCE = 5      # allowed driver torque before start limiting
  TI_STEER_DRIVER_MULTIPLIER = 40    # weight driver torque
  TI_STEER_DRIVER_FACTOR = 1         # from dbc
  TI_STEER_THRESHOLD = 15            # steeringPressed threshold on the TI torque sensor
  # Output-headroom guard (reports/2026-09-29-ti-lockout-prevention.md, sections 3 and 7 #1). The TI
  # trips VIOL_TORQUE_H/L (0x17/0x18) when its computed output s + cmd/12 (s = TI_TORQUE_SENSOR)
  # leaves ~+62/-55 counts; our driver limiter only clips commands opposing the driver, so a
  # command in the driver's direction adds up with them (13/32 trips). The cap is continuous in s
  # and uses a 0.2 s peak-hold of s ("G2", reports/2026-09-30-drives-312-313.md section 3): the
  # first version (+40/-35, only on the driver's side) switched on and off with sensor noise
  # around s = 0 and chattered hands-off (95 of 108 fast steps re-grew within 50 ms).
  TI_OUTPUT_TORQUE_DIV = 12          # fitted D in s + cmd/D (11-13 fit about equally, 3.02 M RUN frames)
  TI_OUTPUT_GUARD_POS = 50           # window edge +62 measured; hands-off cap +599
  TI_OUTPUT_GUARD_NEG = 45           # window edge -55.5 measured (asymmetric); hands-off cap -540
  TI_OUTPUT_GUARD_HOLD_FRAMES = 20   # peak-hold of s for the guard (0.2 s at 100 Hz)
  TI_STEER_DELTA_DOWN_FAST = 60      # step toward zero while a guard binds (panda checks magnitude only)


class TI_STATE:
  DISCOVER = 0
  OFF = 1
  DRIVER_OVER = 2
  RUN = 3


# The gen1 TI only leaves OFF after a run of zero-torque commands (2026-09-11 rlog:
# 1571 + 200 frames). If a board never sends TI_FEEDBACK at all (older firmware),
# open the gate after this many silent frames (5 s at 100 Hz) so it is not stranded.
TI_DISCOVERY_FRAMES = 500
# Once feedback has been seen, treat it as lost (gate closed) after this many
# frames without a TI_FEEDBACK message (200 ms at 100 Hz).
TI_FEEDBACK_TIMEOUT_FRAMES = 20
# Only a longer gap counts as a lockout (steerFaultTemporary + carlog). Route 00000310 had 20
# gaps of 0.15-0.23 s with the TI in RUN and VIOL 0 throughout; each flickered a fake lockout
# (lockout-prevention report, section 6 side finding / section 7 #7). The gate above still closes at 0.2 s.
TI_FEEDBACK_LOCKOUT_FRAMES = 50

# Zero the TI command near full lock at low speed (lockout-prevention report, section 7 #2): trips
# #1/#9/#22/#34 were 358-599 counts pushed into the rack stop at 450-454 deg, < 4 m/s. The rack is
# already at the stop there, so the command only uses up output window.
TI_LOCK_ZERO_SPEED = 4.0             # m/s, zero below this ...
TI_LOCK_ZERO_ANGLE = 420.            # ... when |steeringAngleDeg| is above this

# Never hold a small non-zero command steady (lockout-prevention report, section 7 #5): VIOL_LKAS_STUK
# (0x11) = "request does not change when not 0 / +-600"; tripped after -5 was held for 0.72 s.
TI_STUCK_CMD_MAX = 20                # 0 < |cmd| < this ...
TI_STUCK_FRAMES = 30                 # ... unchanged for more than 0.3 s -> send 0 for a frame

# At most one carlog line per guard per this many frames (10 s).
TI_GUARD_LOG_INTERVAL_FRAMES = 1000

# TI_STEERING_CONTROL bytes 4-7 = 24-bit discovery key + 8-bit OPTION (TI gen1 doc, Part 3).
# The DBC keeps them as one 32-bit KEY signal; create_ti_steering_control composes the value.
TI_DISCOVERY_KEY = 0xC461CE


class TI_OPTION:
  NORMAL = 0x60
  COLD_RESET = 0x61  # clears all violations; the board restarts in DISCOVER
  BYPASS = 0x62


# KEY field of a normal TI_STEERING_CONTROL frame (gen1 firmware constant, = 0xC461CE60).
TI_KEY = (TI_DISCOVERY_KEY << 8) | TI_OPTION.NORMAL

# Automatic cold reset after a mid-drive violation lockout (OFF + VIOL != 0 after RUN was
# reached). Weekend 2026-09-26..28 rlogs: 30 lockouts from hard driver input, each OFF with
# VIOL 23/24/17 for ~29.5 s, then OFF + VIOL 0 for 2.0 s, then RUN. The reset is only sent
# while VIOL != 0, so it never interrupts that 2 s restart (or the ~1.6 s startup one).
TI_RESET_HANDS_OFF_FRAMES = 10       # 0.1 s of |TI driver torque| <= TI_RESET_HANDS_OFF_TORQUE
# After 0x61 the board is in DISCOVER/OFF (bypass) until our zero-torque handshake, and with cmd 0 it
# only re-trips at |s| >= 55-62. Lockout #33 waited 7.5 s at 20-52 counts for |s| <= 15
# (lockout-prevention report, section 6 and 7 #6).
TI_RESET_HANDS_OFF_TORQUE = 30
TI_RESET_BURST_FRAMES = 5            # 0.05 s of OPTION 0x61 (zero torque)
TI_RESET_COOLDOWN_FRAMES = 300       # 3 s from the end of a burst before another attempt
TI_RESET_MAX_ATTEMPTS = 3            # without reaching RUN; then wait for RUN or next ignition


def ti_supported(cp) -> bool:
  """The car could run TI: a controllable 9G on the Nidec safety model with a known 9G safety word."""
  configs = list(cp.safetyConfigs)
  return bool(cp.brand == "honda" and cp.carFingerprint == CAR.HONDA_ACCORD_9G and
              not cp.passive and not cp.dashcamOnly and not cp.notCar and len(configs) == 1 and
              configs[0].safetyModel == structs.CarParams.SafetyModel.hondaNidec and
              (int(configs[0].safetyParam) & ~TI_SAFETY_PARAM) in TI_BASE_SAFETY_PARAMS)


def ti_qualified(cp) -> bool:
  """TI is on for this drive: supported and the TI safety bit was set at startup."""
  return ti_supported(cp) and bool(int(cp.safetyConfigs[0].safetyParam) & TI_SAFETY_PARAM)


def base_safety_param(param: int) -> int:
  """The Nidec safety word without the TI bit, for checks that compare the exact stock word."""
  return int(param) & ~TI_SAFETY_PARAM


def apply_torque_interceptor(cp, requested: bool) -> None:
  """Startup only, before CarState/CarController exist. Sets or clears the TI safety bit."""
  if not ti_supported(cp):
    return
  config = cp.safetyConfigs[0]
  if requested:
    config.safetyParam = int(config.safetyParam) | TI_SAFETY_PARAM
    cp.steerActuatorDelay = TI_STEER_ACTUATOR_DELAY
  else:
    config.safetyParam = base_safety_param(config.safetyParam)


def ti_output_headroom_limits(driver_torque_min, driver_torque_max, LIMITS):
  # (min, max) command keeping the TI's computed output s + cmd/D inside +GUARD_POS/-GUARD_NEG for
  # every s in [driver_torque_min, driver_torque_max] (the caller's peak-hold of s). Continuous in
  # s, so sensor noise around s = 0 cannot switch it on and off.
  max_allowed = min(max((LIMITS.TI_OUTPUT_GUARD_POS - driver_torque_max) * LIMITS.TI_OUTPUT_TORQUE_DIV, 0), LIMITS.TI_STEER_MAX)
  min_allowed = max(min((-LIMITS.TI_OUTPUT_GUARD_NEG - driver_torque_min) * LIMITS.TI_OUTPUT_TORQUE_DIV, 0), -LIMITS.TI_STEER_MAX)
  return min_allowed, max_allowed


def ti_driver_torque_limits(driver_torque, LIMITS):
  # (min, max) command allowed by the driver-torque limiter.
  driver_max_torque = LIMITS.TI_STEER_MAX + (LIMITS.TI_STEER_DRIVER_ALLOWANCE +
                                             driver_torque * LIMITS.TI_STEER_DRIVER_FACTOR) * LIMITS.TI_STEER_DRIVER_MULTIPLIER
  driver_min_torque = -LIMITS.TI_STEER_MAX + (-LIMITS.TI_STEER_DRIVER_ALLOWANCE +
                                              driver_torque * LIMITS.TI_STEER_DRIVER_FACTOR) * LIMITS.TI_STEER_DRIVER_MULTIPLIER
  max_steer_allowed = max(min(LIMITS.TI_STEER_MAX, driver_max_torque), 0)
  min_steer_allowed = min(max(-LIMITS.TI_STEER_MAX, driver_min_torque), 0)
  return min_steer_allowed, max_steer_allowed


def ti_driver_limiter_binds(apply_torque, driver_torque, LIMITS):
  # True when the driver-torque limiter cuts this command (a real driver override).
  min_steer_allowed, max_steer_allowed = ti_driver_torque_limits(driver_torque, LIMITS)
  return not min_steer_allowed <= apply_torque <= max_steer_allowed


def apply_ti_steer_torque_limits(apply_torque, apply_torque_last, driver_torque, LIMITS, output_guard=False, force_zero=False,
                                 guard_driver_torque=None):
  # Honda 9G Accord Torque Interceptor limiting (mirrors apply_driver_steer_torque_limits
  # but with the TI_* constants and the TI's own driver-torque units).
  # output_guard: also apply ti_output_headroom_limits (driver_torque must be the TI sensor, in TI counts)
  # over guard_driver_torque = (min, max) of the recent TI sensor, or this frame's driver_torque.
  # force_zero: ramp to zero. Either one cutting the command allows TI_STEER_DELTA_DOWN_FAST toward zero
  # (not the driver limiter: a fast step there tripled fast steps and chatter in replay).
  min_steer_allowed, max_steer_allowed = ti_driver_torque_limits(driver_torque, LIMITS)
  apply_torque = np.clip(apply_torque, min_steer_allowed, max_steer_allowed)

  delta_down = LIMITS.TI_STEER_DELTA_DOWN
  if force_zero:
    apply_torque = 0
    delta_down = LIMITS.TI_STEER_DELTA_DOWN_FAST
  elif output_guard:
    guard_min, guard_max = ti_output_headroom_limits(*(guard_driver_torque or (driver_torque, driver_torque)), LIMITS)
    # fast step only toward zero on the side the guard cut
    if (apply_torque > guard_max and apply_torque_last > 0) or (apply_torque < guard_min and apply_torque_last < 0):
      delta_down = LIMITS.TI_STEER_DELTA_DOWN_FAST
    apply_torque = np.clip(apply_torque, guard_min, guard_max)

  # slow rate if steer torque increases in magnitude
  if apply_torque_last > 0:
    apply_torque = np.clip(apply_torque, max(apply_torque_last - delta_down, -LIMITS.TI_STEER_DELTA_UP),
                           apply_torque_last + LIMITS.TI_STEER_DELTA_UP)
  else:
    apply_torque = np.clip(apply_torque, apply_torque_last - LIMITS.TI_STEER_DELTA_UP,
                           min(apply_torque_last + delta_down, LIMITS.TI_STEER_DELTA_UP))
  return int(round(float(apply_torque)))


def create_ti_steering_control(packer, apply_steer, option=TI_OPTION.NORMAL):
  # Separate steering device on bus 0. CHKSUM/KEY are sent verbatim (the DBC signals are
  # named CHKSUM with no COUNTER, so the packer/parser do no checksum/counter validation).
  # KEY is the 24-bit discovery key followed by the 8-bit OPTION byte (byte 7).
  # A non-normal option is only ever sent with zero torque.
  if apply_steer != 0:
    option = TI_OPTION.NORMAL
  values = {
    "LKAS_REQUEST": apply_steer,
    "CHKSUM": apply_steer,
    "KEY": (TI_DISCOVERY_KEY << 8) | option,
  }
  return packer.make_can_msg("TI_STEERING_CONTROL", 0, values)


def ti_can_messages():
  # The board only sends TI_FEEDBACK once openpilot commands it, so it is absent while idle.
  # 7.0's CANParser treats freq 0 as "learn the rate, then require it"; only NaN means
  # ignore_alive. A required TI_FEEDBACK would raise canError before the handshake finishes.
  return [("TI_FEEDBACK", math.nan)]


class TiCarState:
  """0x24A TI_FEEDBACK: driver torque, board state and the command gate."""

  def __init__(self):
    self.ramp_down = False
    self.version = 1
    # The gen1 board starts in OFF and only promotes to RUN after a run of
    # zero-torque TI_STEERING_CONTROL frames, so never assume RUN before it says so.
    self.state = TI_STATE.OFF
    self.feedback_seen = False
    self.no_feedback_frames = 0
    self.lkas_allowed = False
    self.last_torque = 0.0
    # lockout / automatic cold reset (update_reset)
    self.viol = 0
    self.run_seen = False
    self.locked_out = False
    self.option = TI_OPTION.NORMAL
    self.hands_off_frames = 0
    self.reset_burst_left = 0
    self.reset_cooldown = 0
    self.reset_attempts = 0

  def update(self, cp, stock_torque, stock_threshold):
    """Per carState frame. Returns (steeringTorque, steeringPressed) for the TI car."""
    # Only consume TI_FEEDBACK when the board actually sent it in this update: vl keeps the
    # last (or the all-zero default) values, vl_all only holds this update's frames.
    ti = cp.vl["TI_FEEDBACK"] if cp.vl_all["TI_FEEDBACK"]["STATE"] else None
    torque, pressed = self.update_driver_torque(ti, stock_torque, stock_threshold)
    self.update_gate(ti)
    self.update_reset(ti)
    return torque, pressed

  def update_driver_torque(self, ti, stock_torque, stock_threshold):
    """Driver torque and steeringPressed on the TI car. Call before update_gate().

    TI_FEEDBACK is missing from ~0.1% of carState frames (2026-09-26..28 weekend rlogs). The stock
    EPS torque sensor sees the TI's own injected torque (median 64 at highway vs the 9G threshold
    of 30), so falling back to it on each gap made a 1-2 frame fake steeringPressed. Within the
    window the gate tolerates (TI_FEEDBACK_TIMEOUT_FRAMES), hold the last TI reading instead;
    after that, or before any feedback has been seen, use the stock sensor (TI not commanding).
    """
    if ti is not None:
      self.last_torque = ti["TI_TORQUE_SENSOR"]
      return self.last_torque, abs(self.last_torque) > TI_LIMITS.TI_STEER_THRESHOLD
    # no_feedback_frames still counts the *previous* consecutive gaps here
    if self.feedback_seen and self.no_feedback_frames < TI_FEEDBACK_TIMEOUT_FRAMES:
      return self.last_torque, abs(self.last_torque) > TI_LIMITS.TI_STEER_THRESHOLD
    return stock_torque, abs(stock_torque) > stock_threshold

  def update_gate(self, ti):
    """Decide whether the Torque Interceptor may be commanded this frame.

    `ti` is this frame's TI_FEEDBACK signal dict, or None when none arrived.
    Once feedback has been seen, only a live STATE == RUN (without RAMP_DOWN)
    opens the gate; a feedback dropout closes it and never falls back. The
    discovery fallback exists only for firmware that never sends feedback.
    """
    if ti is not None:
      self.feedback_seen = True
      self.no_feedback_frames = 0
      self.version = ti["VERSION_NUMBER"]
      self.state = ti["STATE"]
      if self.version > 1:
        self.ramp_down = (ti["RAMP_DOWN"] == 1)
    else:
      self.no_feedback_frames += 1

    if self.feedback_seen:
      self.lkas_allowed = (self.no_feedback_frames <= TI_FEEDBACK_TIMEOUT_FRAMES and
                           not self.ramp_down and self.state == TI_STATE.RUN)
    else:
      self.lkas_allowed = self.no_feedback_frames >= TI_DISCOVERY_FRAMES
    return self.lkas_allowed

  def update_reset(self, ti):
    """Detect a mid-drive TI lockout and pick this frame's OPTION byte. Call after update_gate().

    Locked out = RUN was reached this ignition and the board has since left it for anything but a
    clean driver override (OFF/DISCOVER, a violation, or feedback lost for TI_FEEDBACK_LOCKOUT_FRAMES).
    The startup OFF phase is never a lockout because RUN has not been seen yet. While locked out and
    VIOL != 0, a cold reset (OPTION 0x61) burst is sent once the driver has been hands-off for
    TI_RESET_HANDS_OFF_FRAMES, with a cooldown between bursts and at most TI_RESET_MAX_ATTEMPTS
    without reaching RUN. The gate is closed whenever this can fire, so the controller is
    commanding zero torque. Returns the OPTION for this frame's TI_STEERING_CONTROL.
    """
    if ti is not None:
      self.viol = ti["VIOL"]
    # gaps shorter than TI_FEEDBACK_LOCKOUT_FRAMES close the gate but are not a lockout (no alert)
    feedback_lost = self.no_feedback_frames >= TI_FEEDBACK_LOCKOUT_FRAMES
    feedback_timeout = self.no_feedback_frames > TI_FEEDBACK_TIMEOUT_FRAMES

    if ti is not None and self.state == TI_STATE.RUN:
      if self.locked_out:
        carlog.warning(f"TI lockout cleared: RUN after {self.reset_attempts} cold reset attempt(s)")
      self.run_seen = True
      self.locked_out = False
      self.hands_off_frames = 0
      self.reset_burst_left = 0
      self.reset_cooldown = 0
      self.reset_attempts = 0
      self.option = TI_OPTION.NORMAL
      return self.option

    locked_out = self.run_seen and (feedback_lost or (self.state != TI_STATE.RUN and
                                                      (self.state != TI_STATE.DRIVER_OVER or self.viol != 0)))
    if locked_out and not self.locked_out:
      carlog.warning(f"TI lockout: STATE {self.state} VIOL {self.viol} feedback_lost {feedback_lost}")
    self.locked_out = locked_out

    resettable = locked_out and not feedback_timeout and not self.lkas_allowed and self.viol != 0
    if not resettable:
      self.hands_off_frames = 0
    elif ti is not None:
      hands_off = abs(ti["TI_TORQUE_SENSOR"]) <= TI_RESET_HANDS_OFF_TORQUE
      self.hands_off_frames = self.hands_off_frames + 1 if hands_off else 0

    self.option = TI_OPTION.NORMAL
    if self.reset_burst_left > 0:
      self.option = TI_OPTION.COLD_RESET
      self.reset_burst_left -= 1
      if self.reset_burst_left == 0:
        self.reset_cooldown = TI_RESET_COOLDOWN_FRAMES
    elif self.reset_cooldown > 0:
      self.reset_cooldown -= 1
    elif (resettable and self.hands_off_frames >= TI_RESET_HANDS_OFF_FRAMES and
          self.reset_attempts < TI_RESET_MAX_ATTEMPTS):
      self.reset_attempts += 1
      self.hands_off_frames = 0
      self.option = TI_OPTION.COLD_RESET
      self.reset_burst_left = TI_RESET_BURST_FRAMES - 1
      carlog.warning(f"TI cold reset attempt {self.reset_attempts}/{TI_RESET_MAX_ATTEMPTS}: STATE {self.state} VIOL {self.viol}")
      if self.reset_attempts == TI_RESET_MAX_ATTEMPTS:
        carlog.warning("TI cold reset: last attempt, waiting for RUN or next ignition after this")
    return self.option


class TorqueInterceptor:
  """0x249 TI_STEERING_CONTROL, sent every frame (zero torque = the discovery handshake)."""

  def __init__(self, cp):
    if not ti_qualified(cp):
      raise ValueError("Torque Interceptor requires the 9G Nidec profile with the TI safety bit")
    self.apply_steer_last = 0
    self.frame = 0
    self.driver_torque_hold = deque(maxlen=TI_LIMITS.TI_OUTPUT_GUARD_HOLD_FRAMES)
    self.stuck_frames = 0
    self.guard_active = {"headroom": False, "lock": False, "stuck": False}
    self.guard_log_frame = dict.fromkeys(self.guard_active, -TI_GUARD_LOG_INTERVAL_FRAMES)

  def _log_guard(self, name: str, active: bool, msg: str) -> None:
    if active and not self.guard_active[name] and self.frame - self.guard_log_frame[name] >= TI_GUARD_LOG_INTERVAL_FRAMES:
      self.guard_log_frame[name] = self.frame
      carlog.warning(msg)
    self.guard_active[name] = active

  def _apply_steer(self, CS, new_steer: int) -> int:
    """Limit a TI command; only called while the TI gate is open (lockout-prevention report, section 7)."""
    ti = CS.ti
    # CS.out.steeringTorque is the TI sensor in TI counts (live or held) while feedback is within the gate
    # timeout; before any feedback (feedbackless fallback) it is the stock sensor, so no output guard then.
    driver_torque = CS.out.steeringTorque
    output_guard = ti.feedback_seen and ti.no_feedback_frames <= TI_FEEDBACK_TIMEOUT_FRAMES
    near_lock = CS.out.vEgo < TI_LOCK_ZERO_SPEED and abs(CS.out.steeringAngleDeg) > TI_LOCK_ZERO_ANGLE
    # the headroom guard uses the 0.2 s peak of s on each side (update() fills the hold every frame)
    guard_torque = (min(self.driver_torque_hold), max(self.driver_torque_hold))

    apply_steer = apply_ti_steer_torque_limits(new_steer, self.apply_steer_last, driver_torque, TI_LIMITS,
                                               output_guard=output_guard, force_zero=near_lock,
                                               guard_driver_torque=guard_torque)

    # VIOL_LKAS_STUK: a small non-zero request must not stay unchanged; drop to 0 for one frame
    # (<= 19 counts toward zero), then the normal up-rate brings it back.
    if 0 < abs(apply_steer) < TI_STUCK_CMD_MAX and apply_steer == self.apply_steer_last:
      self.stuck_frames += 1
    else:
      self.stuck_frames = 0
    stuck = self.stuck_frames >= TI_STUCK_FRAMES
    if stuck:
      apply_steer = 0
      self.stuck_frames = 0

    guard_min, guard_max = ti_output_headroom_limits(*guard_torque, TI_LIMITS)
    headroom = output_guard and not near_lock and not guard_min <= new_steer <= guard_max
    held = f"{guard_torque[0]:.0f}..{guard_torque[1]:.0f}"
    self._log_guard("headroom", headroom,
                    f"TI output guard: driver {driver_torque:.0f} (0.2 s {held}) cmd {new_steer} capped to [{guard_min:.0f}, {guard_max:.0f}]")
    self._log_guard("lock", near_lock and new_steer != 0,
                    f"TI near-lock zero: v {CS.out.vEgo:.1f} angle {CS.out.steeringAngleDeg:.0f} cmd {new_steer}")
    self._log_guard("stuck", stuck, f"TI stuck-command zero: held {self.apply_steer_last}")
    return apply_steer

  def update(self, CC, CS, torque_cmd):
    """torque_cmd is the normalized lateral request (-1..1, openpilot sign).

    Returns (TI command, OPTION byte) for this frame's 0x249.
    """
    self.frame += 1
    self.driver_torque_hold.append(CS.out.steeringTorque)
    apply_steer = 0
    # The gen1 board only leaves OFF after a run of zero-torque frames and latches a violation
    # if torque ramps before it reports RUN, so torque is gated on the board's own state. Must
    # also follow latActive: the panda rejects non-zero 0x249 while lateral is not allowed.
    if CC.latActive and CS.ti.lkas_allowed:
      # The TI drives the EPS motor directly with its own sign convention, not the Honda CAN
      # one, so no negation here. Verified on the car: negating steers the wrong way.
      new_steer = int(round(torque_cmd * TI_LIMITS.TI_STEER_MAX))
      apply_steer = self._apply_steer(CS, new_steer)
    else:
      self.stuck_frames = 0
    self.apply_steer_last = apply_steer
    # CS.ti.option is COLD_RESET only during a lockout (gate closed -> zero torque); never with torque.
    option = CS.ti.option if apply_steer == 0 else TI_OPTION.NORMAL
    return apply_steer, option
