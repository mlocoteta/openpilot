"""Vehicle-scoped availability for experimental lateral-only testing.

Experimental mode normally implies that openpilot may run its longitudinal
planner.  A few stock-ACC platforms can safely use the mode for model/lateral
testing as long as the longitudinal actuator gate remains closed.  Keep this
allow-list narrow and explicit so stock-ACC vehicles do not gain an
experimental control path accidentally.
"""

from opendbc.car.hyundai.values import CAR as HYUNDAI_CAR


# The 2023+ Hyundai Palisade platform also identifies Kia Telluride routes.
LATERAL_ONLY_EXPERIMENTAL_CARS = frozenset({
  HYUNDAI_CAR.HYUNDAI_PALISADE_2023,
})


def lateral_only_experimental_available(CP) -> bool:
  """Return whether this car may expose Experimental Mode without openpilot long."""
  return (
    not bool(getattr(CP, "openpilotLongitudinalControl", False)) and
    getattr(CP, "carFingerprint", None) in LATERAL_ONLY_EXPERIMENTAL_CARS
  )


def experimental_mode_available(CP) -> bool:
  """Return whether Experimental Mode is valid for the current car."""
  return (
    bool(getattr(CP, "openpilotLongitudinalControl", False)) or
    lateral_only_experimental_available(CP)
  )
