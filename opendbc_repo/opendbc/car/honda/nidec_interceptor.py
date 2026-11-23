import math

import numpy as np

from opendbc.car import ACCELERATION_DUE_TO_GRAVITY, DT_CTRL, structs
from opendbc.car.can_definitions import CanData
from opendbc.car.carlog import carlog
from opendbc.car.honda.pedal_learner import WIND_FACTOR_HOLD, PedalGasFactorGuard, applied_gas_factor
from opendbc.car.honda.values import CAR, HondaFlags, HondaSafetyFlags

LongCtrlState = structs.CarControl.Actuators.LongControlState
# Log the learned gas/wind factors this often (frames at 100 Hz), so per-drive drift is visible in the carlog.
PEDAL_LEARNER_LOG_INTERVAL_FRAMES = 6000
NIDEC_INTERCEPTOR_CARS = frozenset((
  CAR.ACURA_ILX,
  CAR.HONDA_CRV,
  CAR.HONDA_CRV_EU,
  CAR.HONDA_CRV_SA,
  CAR.HONDA_FIT,
  CAR.HONDA_FREED,
  CAR.HONDA_HRV,
  CAR.HONDA_CLARITY,
  CAR.HONDA_ODYSSEY,
  CAR.HONDA_ODYSSEY_TWN,
  CAR.ACURA_RDX,
  CAR.HONDA_PILOT,
  CAR.HONDA_RIDGELINE,
  CAR.HONDA_CIVIC,
  CAR.HONDA_ACCORD_9G,
  CAR.ACURA_MDX_3G,
  CAR.ACURA_MDX_3G_MMR,
  CAR.ACURA_TLX_1G,
))


def qualified(cp):
  configs = [config for config in cp.safetyConfigs if config.safetyModel != structs.CarParams.SafetyModel.noOutput]
  return (cp.brand == "honda" and cp.carFingerprint in NIDEC_INTERCEPTOR_CARS and
          not cp.flags & HondaFlags.BOSCH and cp.flags & HondaFlags.GAS_INTERCEPTOR and
          cp.openpilotLongitudinalControl and not cp.pcmCruise and
          not cp.passive and not cp.dashcamOnly and not cp.notCar and len(configs) == 1 and
          configs[0].safetyModel == structs.CarParams.SafetyModel.hondaNidec and
          # the 9G Torque Interceptor bit is independent of the pedal (torque_interceptor.py)
          ((configs[0].safetyParam & ~int(HondaSafetyFlags.TORQUE_INTERCEPTOR)) == (36 if cp.flags & HondaFlags.NIDEC_ALT_SCM_MESSAGES else 32) or
           (len(cp.safetyConfigs) == 1 and cp.alternativeExperience == 32 and
            (configs[0].safetyParam & ~int(HondaSafetyFlags.TORQUE_INTERCEPTOR)) ==
            ((36 if cp.flags & HondaFlags.NIDEC_ALT_SCM_MESSAGES else 32) | 512 |
             (256 if cp.carFingerprint == CAR.HONDA_ODYSSEY_TWN else 0)))))


def create_command(packer, gas_amount, counter):
  enabled = gas_amount > 0.001
  values = {"ENABLE": enabled, "COUNTER_PEDAL": counter & 0xF}
  if enabled:
    values.update(GAS_COMMAND=gas_amount * 255.0, GAS_COMMAND2=gas_amount * 255.0)
  message = packer.make_can_msg("GAS_COMMAND", 0, values)
  data = bytearray(message[1])
  data[5] = pedal_crc(data)
  return CanData(0x200, bytes(data), 0)


def pedal_crc(data):
  crc = 0xFF
  for byte in reversed(data[:5]):
    crc ^= byte
    for _ in range(8):
      crc = ((crc << 1) ^ (0xD5 if crc & 0x80 else 0)) & 0xFF
  return crc


class NidecInterceptor:
  def __init__(self, cp):
    if not qualified(cp):
      raise ValueError("Honda interceptor requires its admitted Nidec profile")
    self.command = 0.0
    # Accord 9G pedal: bounded, gated, slow gas-factor learner and a launch-speed cap (pedal_learner.py).
    # The stock learner walked 1.557 -> 2.044 on the first 7.0 drive (2026-10-23) and 0.67-3.0 on 6.x.
    self.guarded = cp.carFingerprint == CAR.HONDA_ACCORD_9G
    self.pedal_guard = None
    self.pitch = 0.0
    self.frame = 0
    self.set_factors(1.0, 1.0)

  def set_factors(self, gas, wind):
    self.bosch_gas_factor = float(gas) if math.isfinite(gas) and 0.1 <= gas <= 3.0 else 1.0
    self.bosch_wind_factor = float(wind) if math.isfinite(wind) and 0.1 <= wind <= 5.0 else 1.0
    self.bosch_wind_factor_before_brake = self.bosch_wind_factor
    self.gas_factor_stored = self.bosch_gas_factor
    self.wind_factor_stored = self.bosch_wind_factor
    if self.guarded:
      self.pedal_guard = PedalGasFactorGuard(self.bosch_gas_factor)
      self.bosch_gas_factor = self.pedal_guard.start
      self.bosch_wind_factor = self.bosch_wind_factor_before_brake = WIND_FACTOR_HOLD
    self.learner_start = (self.bosch_gas_factor, self.bosch_wind_factor)

  def observe_orientation(self, orientation):
    if len(orientation) == 3 and math.isfinite(orientation[1]):
      self.pitch = orientation[1]

  def log_learner(self):
    gas0, wind0 = self.learner_start
    gas, wind = self.bosch_gas_factor, self.bosch_wind_factor
    if self.pedal_guard is not None:
      counts = self.pedal_guard.counts
      total = max(1, sum(counts.values()) - counts["inactive"])
      guard = (f"guard: stored {self.gas_factor_stored:.3f}, band {self.pedal_guard.start:.3f}+-0.10 in 1.2-1.6, " +
               "learned " + " ".join(f"{k} {100 * v / total:.0f}%" for k, v in counts.items() if k != "inactive" and v) +
               f"; wind held {WIND_FACTOR_HOLD:.2f} (stored {self.wind_factor_stored:.3f})")
    else:
      guard = "clips gas 0.1-3.0"
    carlog.warning(" ".join((
      f"Honda pedal learner: t {self.frame * DT_CTRL:.0f} s",
      f"gas factor {gas:.3f} (start {gas0:.3f}, {gas - gas0:+.3f})",
      f"wind factor {wind:.3f} (start {wind0:.3f}, {wind - wind0:+.3f}; before brake {self.bosch_wind_factor_before_brake:.3f};",
      f"{guard}; wind clip 0.1-5.0)",
    )))

  def tick(self, frame):
    """Called every carcontroller frame (100 Hz) for the periodic learner log."""
    self.frame = frame
    if self.pedal_guard is not None and frame % PEDAL_LEARNER_LOG_INTERVAL_FRAMES == 0:
      self.log_learner()

  def update(self, CC, CS, gas, brake, wind_brake, apply_brake=0):
    gas_error = CC.actuators.accel - CS.out.aEgo
    learn_allowed = not CS.out.gasPressed and CC.actuators.longControlState == LongCtrlState.pid
    if self.pedal_guard is not None:
      braking = apply_brake > 0 or CS.out.brakePressed or CC.actuators.longControlState == LongCtrlState.stopping
      hill = math.sin(self.pitch) * ACCELERATION_DUE_TO_GRAVITY
      self.bosch_gas_factor = self.pedal_guard.update(self.bosch_gas_factor, CC.actuators.accel, CS.out.aEgo, CS.out.vEgo,
                                                      gas, braking, hill, learn_allowed)
    if learn_allowed and self.pedal_guard is None:  # the 9G holds its wind factor (pedal_learner.WIND_FACTOR_HOLD)
      if gas_error != 0.0 and gas > 0.0:
        self.bosch_gas_factor = float(np.clip(self.bosch_gas_factor + gas_error / 150.0 * (gas * 4.8), 0.1, 3.0))
      if gas_error != 0.0 and not CS.out.brakePressed and CS.out.vEgo > 0.0:
        wind_adjust = 1.0 + (wind_brake * 4.8) / 1000.0
        if gas_error > 0.0:
          self.bosch_wind_factor = float(np.clip(self.bosch_wind_factor * wind_adjust, 0.1, 5.0))
        else:
          self.bosch_wind_factor = float(np.clip(self.bosch_wind_factor / wind_adjust, 0.1, 5.0))
      if gas <= 0.0:
        self.bosch_wind_factor = max(self.bosch_wind_factor, self.bosch_wind_factor_before_brake)
      else:
        self.bosch_wind_factor_before_brake = self.bosch_wind_factor
    gas_mult = float(np.interp(CS.out.vEgo, [0.0, 10.0], [0.4, 1.0]))
    gas_factor = self.bosch_gas_factor if self.pedal_guard is None else applied_gas_factor(self.bosch_gas_factor, CS.out.vEgo)
    self.command = float(np.clip(gas_mult * ((gas * gas_factor) - brake +
                                (wind_brake * self.bosch_wind_factor * 3.0 / 4.0)), 0.0, 1.0)) if CC.longActive else 0.0
    return self.command
