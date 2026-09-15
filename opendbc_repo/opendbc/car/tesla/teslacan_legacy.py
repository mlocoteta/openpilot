from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.interfaces import V_CRUISE_MAX
from opendbc.car.tesla.values import CANBUS, CarControllerParams


class TeslaCANRaven:
  """CAN commands used by the legacy Model S/X powertrain and EPAS buses."""

  def __init__(self, packers):
    self.packers = packers
    self.CCP = CarControllerParams
    self.jerk_upper = self.CCP.JERK_LIMIT_MAX
    self.jerk_lower = self.CCP.JERK_LIMIT_MIN

  @staticmethod
  def checksum(msg_id, dat):
    return ((msg_id & 0xFF) + ((msg_id >> 8) & 0xFF) + sum(dat)) & 0xFF

  def create_steering_control(self, counter, angle, enabled):
    values = {
      "DAS_steeringControlCounter": counter,
      "DAS_steeringAngleRequest": -angle,
      "DAS_steeringHapticRequest": 0,
      "DAS_steeringControlType": 1 if enabled else 0,
    }
    data = self.packers[CANBUS.party].make_can_msg("DAS_steeringControl", CANBUS.party, values)[1]
    values["DAS_steeringControlChecksum"] = self.checksum(0x488, data[:3])
    return self.packers[CANBUS.party].make_can_msg("DAS_steeringControl", CANBUS.party, values)

  def create_longitudinal_command(self, acc_state, accel, counter, v_ego, active, gas_pressed):
    set_speed = max(v_ego * CV.MS_TO_KPH, 0)
    if active:
      set_speed = 0 if accel < 0 else V_CRUISE_MAX

    if gas_pressed:
      self.jerk_upper = self.jerk_lower = 0.0
    else:
      self.jerk_lower = max(self.jerk_lower - self.CCP.JERK_RAMP_RATE, self.CCP.JERK_LIMIT_MIN)
      self.jerk_upper = min(self.jerk_upper + self.CCP.JERK_RAMP_RATE, self.CCP.JERK_LIMIT_MAX)

    values = {
      "DAS_setSpeed": set_speed,
      "DAS_accState": acc_state,
      "DAS_aebEvent": 0,
      "DAS_jerkMin": self.jerk_lower,
      "DAS_jerkMax": self.jerk_upper,
      "DAS_accelMin": accel,
      "DAS_accelMax": max(accel, 0),
      "DAS_controlCounter": counter,
    }
    data = self.packers[CANBUS.party].make_can_msg("DAS_control", CANBUS.party, values)[1]
    values["DAS_controlChecksum"] = self.checksum(0x2b9, data[:7])
    return self.packers[CANBUS.party].make_can_msg("DAS_control", CANBUS.party, values)
