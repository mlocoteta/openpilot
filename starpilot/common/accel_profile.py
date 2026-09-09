#!/usr/bin/env python3
from __future__ import annotations

import math

from openpilot.common.constants import CV

ACCELERATION_PROFILES = {
  "STANDARD": 0,
  "ECO": 1,
  "SPORT": 2,
  "SPORT_PLUS": 3,
}

DECELERATION_PROFILES = {
  "STANDARD": 0,
  "ECO": 1,
  "SPORT": 2,
}

# MPH = [0.0, 11, 22, 34, 45, 56, 89]
A_CRUISE_MAX_BP_CUSTOM = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 40.0]

CUSTOM_ACCEL_PROFILE_PARAM_SPECS = [
  ("CustomAccelProfile0MPH", 0),
  ("CustomAccelProfile11MPH", 11),
  ("CustomAccelProfile22MPH", 22),
  ("CustomAccelProfile34MPH", 34),
  ("CustomAccelProfile45MPH", 45),
  ("CustomAccelProfile56MPH", 56),
  ("CustomAccelProfile89MPH", 89),
]
CUSTOM_ACCEL_PROFILE_PARAM_KEYS = [key for key, _ in CUSTOM_ACCEL_PROFILE_PARAM_SPECS]
CUSTOM_ACCEL_PROFILE_INITIALIZED_KEY = "CustomAccelProfileInitialized"
CUSTOM_ACCEL_PROFILE_VALUE_MIN = 0.0
CUSTOM_ACCEL_PROFILE_VALUE_MAX = 6.0

CUSTOM_ACCEL_PROFILE_BREAKPOINTS_INITIALIZED_KEY = "CustomAccelProfileBreakpointsInitialized"
CUSTOM_ACCEL_PROFILE_POINT_COUNT_KEY = "CustomAccelProfilePointCount"
CUSTOM_ACCEL_PROFILE_MIN_POINTS = 2
CUSTOM_ACCEL_PROFILE_MAX_POINTS = 12
CUSTOM_ACCEL_PROFILE_BREAKPOINT_MIN_MPH = 0.0
CUSTOM_ACCEL_PROFILE_BREAKPOINT_MAX_MPH = 150.0
CUSTOM_ACCEL_PROFILE_DEFAULT_POINT_COUNT = len(A_CRUISE_MAX_BP_CUSTOM)
CUSTOM_ACCEL_PROFILE_DEFAULT_BREAKPOINTS_MPH = [
  speed / CV.MPH_TO_MS
  for speed in (*A_CRUISE_MAX_BP_CUSTOM, 45.0, 50.0, 55.0, 60.0, 65.0)
]
CUSTOM_ACCEL_PROFILE_BREAKPOINT_PARAM_KEYS = [
  f"CustomAccelProfileBreakpoint{index + 1}MPH"
  for index in range(CUSTOM_ACCEL_PROFILE_MAX_POINTS)
]
CUSTOM_ACCEL_PROFILE_POINT_VALUE_PARAM_KEYS = [
  f"CustomAccelProfilePoint{index + 1}Accel"
  for index in range(CUSTOM_ACCEL_PROFILE_MAX_POINTS)
]
CUSTOM_ACCEL_PROFILE_CURVE_PARAM_KEYS = [
  CUSTOM_ACCEL_PROFILE_POINT_COUNT_KEY,
  *CUSTOM_ACCEL_PROFILE_BREAKPOINT_PARAM_KEYS,
  *CUSTOM_ACCEL_PROFILE_POINT_VALUE_PARAM_KEYS,
]
CUSTOM_ACCEL_PROFILE_EXTRA_POINT_VALUES = [0.55, 0.50, 0.45, 0.40, 0.35]

A_CRUISE_MAX_VALS_ECO_EV =        [1.50, 1.34, 1.18, 1.02, 0.90, 0.74, 0.58]
A_CRUISE_MAX_VALS_STANDARD_EV =   [2.00, 1.84, 1.64, 1.44, 1.24, 1.08, 0.84]
A_CRUISE_MAX_VALS_SPORT_EV =      [2.50, 2.30, 2.06, 1.78, 1.54, 1.34, 1.10]
A_CRUISE_MAX_VALS_SPORT_PLUS_EV = [3.50, 3.26, 2.94, 2.58, 2.22, 1.94, 1.62]

A_CRUISE_MAX_VALS_ECO_GAS =        [1.50, 1.30, 1.10, 0.90, 0.75, 0.55, 0.35]
A_CRUISE_MAX_VALS_STANDARD_GAS =   [2.00, 1.80, 1.55, 1.30, 1.05, 0.85, 0.55]
A_CRUISE_MAX_VALS_SPORT_GAS =      [2.50, 2.25, 1.95, 1.60, 1.30, 1.05, 0.75]
A_CRUISE_MAX_VALS_SPORT_PLUS_GAS = [3.50, 3.20, 2.80, 2.35, 1.90, 1.55, 1.15]

# Traffic Mode: bumper-to-bumper stop-and-go, softer than Eco at every breakpoint.
# Single curve for all vehicle types, derived from manual stop-and-go driving logs.
A_CRUISE_MAX_VALS_TRAFFIC_ALL = [1.10, 0.87, 0.67, 0.53, 0.44, 0.34, 0.23]

A_CRUISE_MAX_VALS_ECO_TRUCK = [3.00, 1.05, 0.60, 0.50, 0.50, 0.45, 0.35]
A_CRUISE_MAX_VALS_STANDARD_TRUCK = [6.00, 1.10, 0.70, 0.60, 0.55, 0.45, 0.35]
A_CRUISE_MAX_VALS_SPORT_TRUCK = [6.00, 1.15, 0.75, 0.70, 0.60, 0.50, 0.40]
A_CRUISE_MAX_VALS_SPORT_PLUS_TRUCK = [6.00, 1.30, 0.90, 0.80, 0.70, 0.60, 0.45]


def akima_interp(x, xp, fp):
  if x <= xp[0]:
    return fp[0]
  if x >= xp[-1]:
    return fp[-1]

  i = max(0, min(len(xp) - 2, int(next(idx for idx, bp in enumerate(xp[1:], start=1) if bp >= x) - 1)))
  t = (x - xp[i]) / float(xp[i + 1] - xp[i])
  t2 = t * t
  t3 = t2 * t
  t4 = t2 * t2
  return (fp[i] * (1 - 10 * t3 + 15 * t4 - 6 * t3 * t2)
          + fp[i + 1] * (10 * t3 - 15 * t4 + 6 * t3 * t2))


def normalize_acceleration_profile(value):
  return _normalize_profile(value, ACCELERATION_PROFILES, ACCELERATION_PROFILES["STANDARD"])


def normalize_deceleration_profile(value):
  return _normalize_profile(value, DECELERATION_PROFILES, DECELERATION_PROFILES["STANDARD"])


def get_accel_profile_curve_values(acceleration_profile, ev_tuning=True, truck_tuning=False):
  profile = normalize_acceleration_profile(acceleration_profile)
  if truck_tuning:
    ev_tuning = False

  if profile == ACCELERATION_PROFILES["ECO"]:
    if ev_tuning:
      return list(A_CRUISE_MAX_VALS_ECO_EV)
    if truck_tuning:
      return list(A_CRUISE_MAX_VALS_ECO_TRUCK)
    return list(A_CRUISE_MAX_VALS_ECO_GAS)

  if profile == ACCELERATION_PROFILES["SPORT"]:
    if ev_tuning:
      return list(A_CRUISE_MAX_VALS_SPORT_EV)
    if truck_tuning:
      return list(A_CRUISE_MAX_VALS_SPORT_TRUCK)
    return list(A_CRUISE_MAX_VALS_SPORT_GAS)

  if profile == ACCELERATION_PROFILES["SPORT_PLUS"]:
    if ev_tuning:
      return list(A_CRUISE_MAX_VALS_SPORT_PLUS_EV)
    if truck_tuning:
      return list(A_CRUISE_MAX_VALS_SPORT_PLUS_TRUCK)
    return list(A_CRUISE_MAX_VALS_SPORT_PLUS_GAS)

  if ev_tuning:
    return list(A_CRUISE_MAX_VALS_STANDARD_EV)
  if truck_tuning:
    return list(A_CRUISE_MAX_VALS_STANDARD_TRUCK)
  return list(A_CRUISE_MAX_VALS_STANDARD_GAS)


def interpolate_accel_profile(v_ego, curve_values, breakpoints=None):
  curve_breakpoints = A_CRUISE_MAX_BP_CUSTOM if breakpoints is None else breakpoints
  if len(curve_breakpoints) != len(curve_values) or len(curve_breakpoints) < CUSTOM_ACCEL_PROFILE_MIN_POINTS:
    raise ValueError("Acceleration profile requires matching breakpoint and value arrays")
  return float(akima_interp(v_ego, curve_breakpoints, curve_values))


def get_max_allowed_accel(v_ego, ev_tuning=True, truck_tuning=False):
  return interpolate_accel_profile(v_ego, get_accel_profile_curve_values(ACCELERATION_PROFILES["SPORT_PLUS"], ev_tuning, truck_tuning))


def build_custom_accel_profile_defaults(acceleration_profile, ev_tuning=True, truck_tuning=False):
  curve_values = get_accel_profile_curve_values(acceleration_profile, ev_tuning, truck_tuning)
  return {
    key: float(curve_values[idx])
    for idx, key in enumerate(CUSTOM_ACCEL_PROFILE_PARAM_KEYS)
  }


CUSTOM_ACCEL_PROFILE_STATIC_DEFAULTS = {
  key: float(A_CRUISE_MAX_VALS_SPORT_GAS[idx])
  for idx, key in enumerate(CUSTOM_ACCEL_PROFILE_PARAM_KEYS)
}


def custom_accel_profile_is_initialized(initialized_flag, raw_values_by_key):
  if _coerce_bool(initialized_flag):
    return True

  if not isinstance(raw_values_by_key, dict):
    return False

  for key in CUSTOM_ACCEL_PROFILE_PARAM_KEYS:
    raw_value = raw_values_by_key.get(key)
    if raw_value is None:
      return False

    try:
      value = float(raw_value.decode("utf-8", errors="replace") if isinstance(raw_value, bytes) else raw_value)
    except (TypeError, ValueError):
      return False

    if not math.isclose(value, CUSTOM_ACCEL_PROFILE_STATIC_DEFAULTS[key], abs_tol=1e-6):
      return True

  return False


def coerce_custom_accel_profile_values(raw_values, acceleration_profile, ev_tuning=True, truck_tuning=False, point_count=None):
  defaults = get_accel_profile_curve_values(acceleration_profile, ev_tuning, truck_tuning)
  expected_count = len(defaults) if point_count is None else point_count
  values = []
  for idx in range(expected_count):
    default = defaults[min(idx, len(defaults) - 1)]
    try:
      value = float(raw_values[idx])
    except (IndexError, TypeError, ValueError):
      value = default
    values.append(min(CUSTOM_ACCEL_PROFILE_VALUE_MAX, max(CUSTOM_ACCEL_PROFILE_VALUE_MIN, value)))
  return values


def parse_custom_accel_profile_curve(raw_count, raw_breakpoints_mph, raw_values):
  try:
    numeric_count = float(_decode_param_value(raw_count))
  except (TypeError, ValueError):
    raise ValueError("Breakpoint count must be a whole number") from None

  if not math.isfinite(numeric_count) or not numeric_count.is_integer():
    raise ValueError("Breakpoint count must be a whole number")

  count = int(numeric_count)
  if not CUSTOM_ACCEL_PROFILE_MIN_POINTS <= count <= CUSTOM_ACCEL_PROFILE_MAX_POINTS:
    raise ValueError(
      f"Breakpoint count must be between {CUSTOM_ACCEL_PROFILE_MIN_POINTS} and {CUSTOM_ACCEL_PROFILE_MAX_POINTS}"
    )

  if len(raw_breakpoints_mph) < count or len(raw_values) < count:
    raise ValueError("The configured breakpoint count exceeds the available curve points")

  breakpoints_mph = []
  values = []
  for index in range(count):
    try:
      breakpoint_mph = float(_decode_param_value(raw_breakpoints_mph[index]))
      value = float(_decode_param_value(raw_values[index]))
    except (TypeError, ValueError):
      raise ValueError(f"Curve point {index + 1} must contain numeric values") from None

    if not math.isfinite(breakpoint_mph) or not CUSTOM_ACCEL_PROFILE_BREAKPOINT_MIN_MPH <= breakpoint_mph <= CUSTOM_ACCEL_PROFILE_BREAKPOINT_MAX_MPH:
      bounds = f"{CUSTOM_ACCEL_PROFILE_BREAKPOINT_MIN_MPH:g} and {CUSTOM_ACCEL_PROFILE_BREAKPOINT_MAX_MPH:g} mph"
      raise ValueError(f"Breakpoint {index + 1} must be between {bounds}")
    if breakpoints_mph and breakpoint_mph <= breakpoints_mph[-1]:
      raise ValueError("Breakpoint speeds must be strictly increasing")
    if not math.isfinite(value) or not CUSTOM_ACCEL_PROFILE_VALUE_MIN <= value <= CUSTOM_ACCEL_PROFILE_VALUE_MAX:
      bounds = f"{CUSTOM_ACCEL_PROFILE_VALUE_MIN:g} and {CUSTOM_ACCEL_PROFILE_VALUE_MAX:g} m/s²"
      raise ValueError(f"Max acceleration at point {index + 1} must be between {bounds}")

    breakpoints_mph.append(breakpoint_mph)
    values.append(value)

  return [speed * CV.MPH_TO_MS for speed in breakpoints_mph], values


def get_custom_accel_profile_curve_defaults(acceleration_profile, ev_tuning=True, truck_tuning=False):
  profile_values = get_accel_profile_curve_values(acceleration_profile, ev_tuning, truck_tuning)
  return {
    CUSTOM_ACCEL_PROFILE_POINT_COUNT_KEY: CUSTOM_ACCEL_PROFILE_DEFAULT_POINT_COUNT,
    **{
      key: CUSTOM_ACCEL_PROFILE_DEFAULT_BREAKPOINTS_MPH[index]
      for index, key in enumerate(CUSTOM_ACCEL_PROFILE_BREAKPOINT_PARAM_KEYS)
    },
    **{
      key: (profile_values[index] if index < len(profile_values) else CUSTOM_ACCEL_PROFILE_EXTRA_POINT_VALUES[index - len(profile_values)])
      for index, key in enumerate(CUSTOM_ACCEL_PROFILE_POINT_VALUE_PARAM_KEYS)
    },
  }


def _normalize_profile(value, profile_map, fallback):
  if isinstance(value, bytes):
    value = value.decode("utf-8", errors="replace")

  if isinstance(value, str):
    normalized = value.strip().upper().replace("+", "_PLUS").replace(" ", "_")
    if normalized in profile_map:
      return profile_map[normalized]

  try:
    return int(float(value))
  except (TypeError, ValueError):
    return fallback


def _decode_param_value(value):
  if isinstance(value, bytes):
    return value.decode("utf-8", errors="replace")
  return value


def _coerce_bool(value):
  if isinstance(value, bytes):
    value = value.decode("utf-8", errors="replace")

  if isinstance(value, str):
    return value.strip() in ("1", "true", "True")

  return bool(value)
