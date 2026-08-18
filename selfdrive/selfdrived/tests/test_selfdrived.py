from cereal import car, custom
from opendbc.car.hyundai.values import CAR as HYUNDAI_CAR
from opendbc.car.nissan.values import CAR as NISSAN_CAR

from openpilot.selfdrive.selfdrived.selfdrived import SelfdriveD, commanded_torque_at_max_for_saturation


class FakeFallbackParams:
  def __init__(self, controls_ready, ecu_disable_failed, fallback_cp, fallback_fpcp):
    self.controls_ready = controls_ready
    self.ecu_disable_failed = ecu_disable_failed
    self.values = {
      "CarParams": fallback_cp.to_bytes(),
      "StarPilotCarParams": fallback_fpcp.to_bytes(),
    }

  def get_bool(self, key):
    return self.controls_ready if key == "ControlsReady" else self.ecu_disable_failed

  def get(self, key):
    return self.values[key]


def test_immediate_max_output_saturation_is_torque_controller_only():
  CP = car.CarParams.new_message()
  CP.steerControlType = car.CarParams.SteerControlType.torque
  CP.lateralTuning.init("torque")

  assert commanded_torque_at_max_for_saturation(CP, 1.0)
  assert not commanded_torque_at_max_for_saturation(CP, 0.99)

  CP.lateralTuning.init("pid")
  assert not commanded_torque_at_max_for_saturation(CP, 1.0)

  CP.lateralTuning.init("torque")
  CP.steerControlType = car.CarParams.SteerControlType.angle
  assert not commanded_torque_at_max_for_saturation(CP, 1.0)


def test_gv70_uses_normal_saturation_timer_at_max_output():
  CP = car.CarParams.new_message()
  CP.carFingerprint = HYUNDAI_CAR.GENESIS_GV70_ELECTRIFIED_1ST_GEN
  CP.steerControlType = car.CarParams.SteerControlType.torque
  CP.lateralTuning.init("torque")

  assert not commanded_torque_at_max_for_saturation(CP, 1.0)


def test_ecu_disable_fallback_synchronizes_behavior_and_safety_params():
  initial_cp = car.CarParams.new_message()
  initial_cp.carFingerprint = NISSAN_CAR.NISSAN_LEAF
  initial_cp.openpilotLongitudinalControl = True
  initial_cp.pcmCruise = False
  initial_cp.safetyConfigs = [car.CarParams.SafetyConfig.new_message(safetyParam=2)]
  initial_fpcp = custom.StarPilotCarParams.new_message()
  initial_fpcp.safetyConfigs = [custom.StarPilotCarParams.SafetyConfig.new_message(safetyParam=2)]

  fallback_cp = car.CarParams.new_message()
  fallback_cp.openpilotLongitudinalControl = False
  fallback_cp.pcmCruise = True
  fallback_cp.safetyConfigs = [car.CarParams.SafetyConfig.new_message(safetyParam=0)]
  fallback_fpcp = custom.StarPilotCarParams.new_message()
  fallback_fpcp.safetyConfigs = [custom.StarPilotCarParams.SafetyConfig.new_message(safetyParam=0)]

  selfdrived = SelfdriveD.__new__(SelfdriveD)
  selfdrived.CP = initial_cp
  selfdrived.FPCP = initial_fpcp
  selfdrived.params = FakeFallbackParams(True, True, fallback_cp, fallback_fpcp)
  selfdrived.ecu_disable_failed = False
  selfdrived.ecu_disable_failed_checked = False

  selfdrived.update_ecu_disable_failed()

  assert selfdrived.ecu_disable_failed
  assert selfdrived.ecu_disable_failed_checked
  assert not selfdrived.CP.openpilotLongitudinalControl
  assert selfdrived.CP.pcmCruise
  assert selfdrived.FPCP.safetyConfigs[0].safetyParam == 0


def test_ecu_disable_fallback_does_not_change_other_cars():
  initial_cp = car.CarParams.new_message()
  initial_cp.carFingerprint = HYUNDAI_CAR.HYUNDAI_SONATA
  initial_cp.openpilotLongitudinalControl = True
  initial_cp.pcmCruise = False
  initial_fpcp = custom.StarPilotCarParams.new_message()
  initial_fpcp.safetyConfigs = [custom.StarPilotCarParams.SafetyConfig.new_message(safetyParam=4)]

  fallback_cp = car.CarParams.new_message()
  fallback_cp.openpilotLongitudinalControl = False
  fallback_cp.pcmCruise = True
  fallback_fpcp = custom.StarPilotCarParams.new_message()
  fallback_fpcp.safetyConfigs = [custom.StarPilotCarParams.SafetyConfig.new_message(safetyParam=0)]

  selfdrived = SelfdriveD.__new__(SelfdriveD)
  selfdrived.CP = initial_cp
  selfdrived.FPCP = initial_fpcp
  selfdrived.params = FakeFallbackParams(True, True, fallback_cp, fallback_fpcp)
  selfdrived.ecu_disable_failed = False
  selfdrived.ecu_disable_failed_checked = False

  selfdrived.update_ecu_disable_failed()

  assert selfdrived.ecu_disable_failed_checked
  assert selfdrived.CP.openpilotLongitudinalControl
  assert not selfdrived.CP.pcmCruise
  assert selfdrived.FPCP.safetyConfigs[0].safetyParam == 4
