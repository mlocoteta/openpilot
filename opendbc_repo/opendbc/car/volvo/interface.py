from opendbc.car import structs, get_safety_config
from opendbc.car.interfaces import CarInterfaceBase
from opendbc.car.volvo.carstate import CarState
from opendbc.car.volvo.carcontroller import CarController
from opendbc.car.volvo.values import CAR, VolvoC1PlatformConfig, VolvoSPAPlatformConfig, VolvoSafetyFlags


class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController

  def __init__(self, CP):
    if not isinstance(CAR(CP.carFingerprint).config, VolvoC1PlatformConfig):
      from opendbc.car.volvo.cma_carstate import CarStateCMA
      from opendbc.car.volvo.cma_carcontroller import CarControllerCMA
      self.CarState = CarStateCMA
      self.CarController = CarControllerCMA
    super().__init__(CP)

  @staticmethod
  def _get_params(ret, candidate, fingerprint, car_fw, alpha_long, is_release, docs):
    ret.brand = 'volvo'
    platform = CAR(candidate).config
    c1 = isinstance(platform, VolvoC1PlatformConfig)
    safety_param = VolvoSafetyFlags.C1.value if c1 else VolvoSafetyFlags.SPA.value if isinstance(platform, VolvoSPAPlatformConfig) else 0
    if candidate == CAR.POLESTAR_2:
      safety_param |= VolvoSafetyFlags.LCA2_MOD15.value
    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.volvo, safety_param)]
    ret.steerActuatorDelay = 0.2 if c1 else 0.3
    ret.steerLimitTimer = 0.1
    ret.steerAtStandstill = not c1
    ret.steerControlType = structs.CarParams.SteerControlType.angle
    ret.radarUnavailable = True
    ret.alphaLongitudinalAvailable = False
    ret.pcmCruise = True
    if c1:
      ret.transmissionType = structs.CarParams.TransmissionType.automatic
    return ret
