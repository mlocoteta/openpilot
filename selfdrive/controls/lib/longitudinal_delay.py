import math


# Bounds for the effective longitudinal actuator delay. The StarPilot "LongitudinalActuatorDelay"
# param (AdvancedLongitudinalTune) is validated to [0, 1] s, but the planner divides by it and uses
# it as a look-ahead, so never let it collapse to ~0.
MIN_LONG_ACTUATOR_DELAY = 0.05
MAX_LONG_ACTUATOR_DELAY = 1.0


def get_long_actuator_delay(CP, starpilot_toggles=None) -> float:
  """Effective longitudinal actuator delay for the planner and modeld.

  The LongitudinalActuatorDelay param only reached LongControl.update_old_long, which nothing
  calls, so the planner and modeld always used CP.longitudinalActuatorDelay (0.15 s on the
  Nidec 9G while the measured command->accel lag is 0.40-0.50 s, 2026-09-26..28 weekend).
  starpilot_toggles.longitudinalActuatorDelay already falls back to the CP value when the
  advanced longitudinal tune is off. CarParams is deliberately not rewritten: StarPilot syncs
  LongitudinalActuatorDelayStock from it.
  """
  delay = getattr(starpilot_toggles, "longitudinalActuatorDelay", None) if starpilot_toggles is not None else None
  try:
    delay = float(delay)
  except (TypeError, ValueError):
    delay = float("nan")
  if not math.isfinite(delay):
    delay = float(CP.longitudinalActuatorDelay)
  return min(max(delay, MIN_LONG_ACTUATOR_DELAY), MAX_LONG_ACTUATOR_DELAY)
