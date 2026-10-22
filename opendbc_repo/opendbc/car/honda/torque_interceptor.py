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

import numpy as np

from opendbc.car import structs
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
# KEY field of every TI_STEERING_CONTROL frame (gen1 firmware constant).
TI_KEY = 3294744160


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


def apply_ti_steer_torque_limits(apply_torque, apply_torque_last, driver_torque, LIMITS):
  # Honda 9G Accord Torque Interceptor limiting (mirrors apply_driver_steer_torque_limits
  # but with the TI_* constants and the TI's own driver-torque units).
  driver_max_torque = LIMITS.TI_STEER_MAX + (LIMITS.TI_STEER_DRIVER_ALLOWANCE +
                                             driver_torque * LIMITS.TI_STEER_DRIVER_FACTOR) * LIMITS.TI_STEER_DRIVER_MULTIPLIER
  driver_min_torque = -LIMITS.TI_STEER_MAX + (-LIMITS.TI_STEER_DRIVER_ALLOWANCE +
                                              driver_torque * LIMITS.TI_STEER_DRIVER_FACTOR) * LIMITS.TI_STEER_DRIVER_MULTIPLIER
  max_steer_allowed = max(min(LIMITS.TI_STEER_MAX, driver_max_torque), 0)
  min_steer_allowed = min(max(-LIMITS.TI_STEER_MAX, driver_min_torque), 0)
  apply_torque = np.clip(apply_torque, min_steer_allowed, max_steer_allowed)

  # slow rate if steer torque increases in magnitude
  if apply_torque_last > 0:
    apply_torque = np.clip(apply_torque, max(apply_torque_last - LIMITS.TI_STEER_DELTA_DOWN, -LIMITS.TI_STEER_DELTA_UP),
                           apply_torque_last + LIMITS.TI_STEER_DELTA_UP)
  else:
    apply_torque = np.clip(apply_torque, apply_torque_last - LIMITS.TI_STEER_DELTA_UP,
                           min(apply_torque_last + LIMITS.TI_STEER_DELTA_DOWN, LIMITS.TI_STEER_DELTA_UP))
  return int(round(float(apply_torque)))


def create_ti_steering_control(packer, apply_steer):
  # Separate steering device on bus 0. CHKSUM/KEY are sent verbatim (the DBC signals are
  # named CHKSUM with no COUNTER, so the packer/parser do no checksum/counter validation).
  values = {
    "LKAS_REQUEST": apply_steer,
    "CHKSUM": apply_steer,
    "KEY": TI_KEY,
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

  def update(self, cp, stock_torque, stock_threshold):
    """Per carState frame. Returns (steeringTorque, steeringPressed) for the TI car."""
    # Only consume TI_FEEDBACK when the board actually sent it in this update: vl keeps the
    # last (or the all-zero default) values, vl_all only holds this update's frames.
    ti = cp.vl["TI_FEEDBACK"] if cp.vl_all["TI_FEEDBACK"]["STATE"] else None
    torque, pressed = self.update_driver_torque(ti, stock_torque, stock_threshold)
    self.update_gate(ti)
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


class TorqueInterceptor:
  """0x249 TI_STEERING_CONTROL, sent every frame (zero torque = the discovery handshake)."""

  def __init__(self, cp):
    if not ti_qualified(cp):
      raise ValueError("Torque Interceptor requires the 9G Nidec profile with the TI safety bit")
    self.apply_steer_last = 0

  def update(self, CC, CS, torque_cmd):
    """torque_cmd is the normalized lateral request (-1..1, openpilot sign). Returns the TI command."""
    apply_steer = 0
    # The gen1 board only leaves OFF after a run of zero-torque frames and latches a violation
    # if torque ramps before it reports RUN, so torque is gated on the board's own state. Must
    # also follow latActive: the panda rejects non-zero 0x249 while lateral is not allowed.
    if CC.latActive and CS.ti.lkas_allowed:
      # The TI drives the EPS motor directly with its own sign convention, not the Honda CAN
      # one, so no negation here. Verified on the car: negating steers the wrong way.
      new_steer = int(round(torque_cmd * TI_LIMITS.TI_STEER_MAX))
      apply_steer = apply_ti_steer_torque_limits(new_steer, self.apply_steer_last, CS.out.steeringTorque, TI_LIMITS)
    self.apply_steer_last = apply_steer
    return apply_steer
