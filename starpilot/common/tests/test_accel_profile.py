import pytest

from openpilot.common.constants import CV
from openpilot.starpilot.common.accel_profile import (
  ACCELERATION_PROFILES,
  A_CRUISE_MAX_BP_CUSTOM,
  A_CRUISE_MAX_VALS_ECO_TRUCK,
  A_CRUISE_MAX_VALS_STANDARD_TRUCK,
  A_CRUISE_MAX_VALS_SPORT_PLUS_TRUCK,
  A_CRUISE_MAX_VALS_SPORT_TRUCK,
  get_accel_profile_curve_values,
  interpolate_accel_profile,
  parse_custom_accel_profile_curve,
)


def test_truck_curves_match_expected_values():
  assert get_accel_profile_curve_values(ACCELERATION_PROFILES["ECO"], ev_tuning=False, truck_tuning=True) == A_CRUISE_MAX_VALS_ECO_TRUCK
  values = get_accel_profile_curve_values(ACCELERATION_PROFILES["STANDARD"], ev_tuning=False, truck_tuning=True)
  assert values == A_CRUISE_MAX_VALS_STANDARD_TRUCK
  assert get_accel_profile_curve_values(ACCELERATION_PROFILES["SPORT"], ev_tuning=False, truck_tuning=True) == A_CRUISE_MAX_VALS_SPORT_TRUCK
  assert get_accel_profile_curve_values(ACCELERATION_PROFILES["SPORT_PLUS"], ev_tuning=False, truck_tuning=True) == A_CRUISE_MAX_VALS_SPORT_PLUS_TRUCK


def test_standard_truck_curve_keeps_mid_high_speed_authority():
  values = get_accel_profile_curve_values(ACCELERATION_PROFILES["STANDARD"], ev_tuning=False, truck_tuning=True)

  assert interpolate_accel_profile(20.0, values) >= 1.18
  assert interpolate_accel_profile(25.0, values) >= 0.98
  assert interpolate_accel_profile(30.0, values) >= 0.90


def test_truck_profiles_remain_ordered():
  eco = get_accel_profile_curve_values(ACCELERATION_PROFILES["ECO"], ev_tuning=False, truck_tuning=True)
  standard = get_accel_profile_curve_values(ACCELERATION_PROFILES["STANDARD"], ev_tuning=False, truck_tuning=True)
  sport = get_accel_profile_curve_values(ACCELERATION_PROFILES["SPORT"], ev_tuning=False, truck_tuning=True)
  sport_plus = get_accel_profile_curve_values(ACCELERATION_PROFILES["SPORT_PLUS"], ev_tuning=False, truck_tuning=True)

  for e, s, sp, spp in zip(eco, standard, sport, sport_plus, strict=True):
    assert e < s < sp < spp


def test_custom_accel_profile_accepts_variable_breakpoint_count():
  breakpoints, values = parse_custom_accel_profile_curve(3, [0.0, 20.0, 50.0], [2.0, 1.0, 0.5])

  assert breakpoints == pytest.approx([0.0, 20.0 * CV.MPH_TO_MS, 50.0 * CV.MPH_TO_MS])
  assert values == [2.0, 1.0, 0.5]
  assert interpolate_accel_profile(breakpoints[1], values, breakpoints) == pytest.approx(1.0)


@pytest.mark.parametrize("breakpoints", ([0.0, 20.0, 20.0], [0.0, 30.0, 20.0]))
def test_custom_accel_profile_rejects_non_increasing_breakpoints(breakpoints):
  with pytest.raises(ValueError, match="strictly increasing"):
    parse_custom_accel_profile_curve(3, breakpoints, [2.0, 1.0, 0.5])


def test_custom_accel_profile_rejects_invalid_point_count():
  with pytest.raises(ValueError, match="between 2 and 12"):
    parse_custom_accel_profile_curve(1, [0.0], [2.0])


def test_default_accel_interpolation_still_uses_legacy_breakpoints():
  values = [2.0, 1.8, 1.6, 1.4, 1.2, 1.0, 0.8]

  assert interpolate_accel_profile(A_CRUISE_MAX_BP_CUSTOM[3], values) == pytest.approx(values[3])
