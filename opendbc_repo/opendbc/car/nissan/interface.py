from opendbc.car import get_safety_config, structs, uds
from opendbc.car.disable_ecu import disable_ecu, ecu_log
from opendbc.car.interfaces import CarInterfaceBase
from opendbc.car.nissan.carcontroller import CarController
from opendbc.car.nissan.carstate import CarState
from opendbc.car.nissan.values import CAR, CarControllerParams, NissanSafetyFlags, \
                                       NISSAN_DIAGNOSTIC_REQUEST_KWP, NISSAN_DIAGNOSTIC_RESPONSE_KWP, NISSAN_RX_OFFSET


LEAF_ADAS_ECU_ADDR = 0x707
LEAF_ADAS_ECU_BUS = 0
LEAF_2025_SV_PLUS_CAMERA_FW = b'6WK2CDB\x04\x18\x00\x00\x00\x00\x00R=1\x18\x99\x10\x00\x00\x00\x80'


def is_leaf_2025_sv_plus_longitudinal(candidate, car_fw):
  return candidate == CAR.NISSAN_LEAF and any(
    fw.address == LEAF_ADAS_ECU_ADDR and bytes(fw.fwVersion) == LEAF_2025_SV_PLUS_CAMERA_FW
    for fw in car_fw
  )


class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController

  @staticmethod
  def get_pid_accel_limits(CP, current_speed, cruise_speed):
    if CP.carFingerprint == CAR.NISSAN_LEAF and CP.openpilotLongitudinalControl:
      return CarControllerParams.ACCEL_MIN, CarControllerParams.ACCEL_MAX
    return CarInterfaceBase.get_pid_accel_limits(CP, current_speed, cruise_speed)

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, alpha_long, is_release, docs) -> structs.CarParams:
    ret.brand = "nissan"
    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.nissan)]
    ret.autoResumeSng = False

    ret.steerLimitTimer = 1.0

    ret.steerActuatorDelay = 0.1

    ret.steerControlType = structs.CarParams.SteerControlType.angle
    ret.radarUnavailable = True

    ret.alphaLongitudinalAvailable = is_leaf_2025_sv_plus_longitudinal(candidate, car_fw)
    ret.openpilotLongitudinalControl = alpha_long and ret.alphaLongitudinalAvailable
    ret.pcmCruise = not ret.openpilotLongitudinalControl

    if ret.openpilotLongitudinalControl:
      ret.safetyConfigs[0].safetyParam |= NissanSafetyFlags.LONG_CONTROL.value
      ret.autoResumeSng = True
      ret.stopAccel = -2.0
      ret.vEgoStopping = 0.5
      ret.vEgoStarting = 0.5
      ret.stoppingDecelRate = 0.8

    if candidate == CAR.NISSAN_ALTIMA:
      # Altima has EPS on C-CAN unlike the others that have it on V-CAN
      ret.safetyConfigs[0].safetyParam |= NissanSafetyFlags.ALT_EPS_BUS.value

    return ret

  @staticmethod
  def init(CP, can_recv, can_send):
    if not (CP.openpilotLongitudinalControl and CP.carFingerprint == CAR.NISSAN_LEAF):
      return

    from openpilot.common.params import Params
    params = Params()
    communication_control = bytes([uds.SERVICE_TYPE.COMMUNICATION_CONTROL,
                                   uds.CONTROL_TYPE.ENABLE_RX_DISABLE_TX,
                                   uds.MESSAGE_TYPE.NORMAL])
    ecu_disabled = disable_ecu(can_recv, can_send, bus=LEAF_ADAS_ECU_BUS, addr=LEAF_ADAS_ECU_ADDR,
                               com_cont_req=communication_control, require_response=True, response_offset=NISSAN_RX_OFFSET)
    if not ecu_disabled:
      # Nissan firmware queries use the KWP-style default session. Try it after
      # standard UDS extended-session control, but still require a positive 0x68 response.
      ecu_disabled = disable_ecu(can_recv, can_send, bus=LEAF_ADAS_ECU_BUS, addr=LEAF_ADAS_ECU_ADDR,
                                 com_cont_req=communication_control, require_response=True,
                                 diag_request=NISSAN_DIAGNOSTIC_REQUEST_KWP, diag_response=NISSAN_DIAGNOSTIC_RESPONSE_KWP,
                                 response_offset=NISSAN_RX_OFFSET)
    params.put_bool("EcuDisableFailed", not ecu_disabled)
    if ecu_disabled:
      ecu_log("Nissan Leaf ADAS TX disabled; experimental longitudinal control enabled")
    else:
      CP.safetyConfigs[-1].safetyParam &= ~NissanSafetyFlags.LONG_CONTROL.value
      CP.openpilotLongitudinalControl = False
      CP.pcmCruise = True
      ecu_log("Nissan Leaf ADAS TX disable failed; falling back to stock longitudinal control")

  @staticmethod
  def deinit(CP, can_recv, can_send):
    if not (CP.openpilotLongitudinalControl and CP.carFingerprint == CAR.NISSAN_LEAF):
      return

    communication_control = bytes([uds.SERVICE_TYPE.COMMUNICATION_CONTROL,
                                   0x80 | uds.CONTROL_TYPE.ENABLE_RX_ENABLE_TX,
                                   uds.MESSAGE_TYPE.NORMAL])
    disable_ecu(can_recv, can_send, bus=LEAF_ADAS_ECU_BUS, addr=LEAF_ADAS_ECU_ADDR,
                com_cont_req=communication_control, response_offset=NISSAN_RX_OFFSET)
