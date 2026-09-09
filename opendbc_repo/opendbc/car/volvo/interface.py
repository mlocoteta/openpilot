from opendbc.car import structs, get_safety_config
from opendbc.car.interfaces import CarInterfaceBase
from opendbc.car.volvo.carcontroller import CarController
from opendbc.car.volvo.carstate import CarState
from opendbc.car.volvo.values import VolvoSPAPlatformConfig, CAR

TransmissionType = structs.CarParams.TransmissionType

VOLVO_FLAG_SPA = 1
SAFETY_VOLVO = structs.CarParams.SafetyModel.volvo


class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, alpha_long, is_release, docs) -> structs.CarParams:
    ret.brand = 'volvo'

    safety_param = 0
    if isinstance(CAR(candidate).config, VolvoSPAPlatformConfig):
      safety_param = VOLVO_FLAG_SPA
    ret.safetyConfigs = [get_safety_config(SAFETY_VOLVO, safety_param)]
    #ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.noOutput)]

    ret.dashcamOnly = False

    ret.steerActuatorDelay = 0.3
    ret.steerLimitTimer = 0.1
    ret.steerAtStandstill = True

    # Use angle-based steering control for Volvo CMA platform
    ret.steerControlType = structs.CarParams.SteerControlType.angle
    # Note: No lateral tuning configuration needed for basic angle control
    ret.radarUnavailable = True

    ret.alphaLongitudinalAvailable = False

    ret.pcmCruise = True

    return ret
