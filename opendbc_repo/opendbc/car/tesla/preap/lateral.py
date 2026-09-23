from opendbc.car import structs
from opendbc.safety import ALTERNATIVE_EXPERIENCE


def preap_lateral_authorized(CP, CS, panda_states, panda_states_valid: bool) -> bool:
  """Match Pre-AP's existing safety authorization without treating software CC availability as ACC main."""
  if not panda_states_valid or CS.out.gearShifter != structs.CarState.GearShifter.drive or CS.out.doorOpen or CS.out.steeringDisengage:
    return False
  if CS.engagement.lateralRearmRequired:
    return False
  config = CP.safetyConfigs[0]
  matching = [p for p in panda_states if p.safetyModel == config.safetyModel and p.safetyParam == config.safetyParam]
  if len(matching) != 1 or matching[0].safetyRxChecksInvalid:
    return False
  panda = matching[0]
  # Physical cancel/override/gear changes clear this latch immediately, whereas
  # Panda telemetry can lag. Longitudinal software cancellation leaves it intact.
  stalk_authorized = CS.engagement.lateralEnabled and panda.controlsAllowed
  stock_main = CS.di_cruise_state in ("STANDBY", "ENABLED", "STANDSTILL", "OVERRIDE", "PRE_FAULT", "PRE_CANCEL")
  aol_authorized = bool(panda.alternativeExperience & ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL) and stock_main
  return bool(stalk_authorized or aol_authorized)
