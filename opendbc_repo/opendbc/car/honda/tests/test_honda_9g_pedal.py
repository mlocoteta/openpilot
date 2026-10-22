"""Honda 9G Accord pedal longitudinal (independent of the steering hardware)."""
import pytest

from opendbc.car.honda import carcontroller
from opendbc.car.honda.values import CAR


class TestNidecWindBrake:
  def test_other_nidec_cars_keep_stock_curve(self):
    for v, expected in ((0.0, 0.001), (2.3, 0.002), (35.0, 0.15)):
      assert carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_CIVIC) == pytest.approx(expected)

  def test_accord_9g_brakes_for_mild_decel_at_highway_speed(self):
    v = 22.4  # 50 mph
    stock = carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_CIVIC)
    wind_brake = carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_ACCORD_9G)
    assert wind_brake == pytest.approx(0.136 / carcontroller.ACCORD_9G_BRAKE_ACCEL_PER_UNIT)
    assert wind_brake < stock / 2
    # brakes engage (hysteresis on at 0.02) for requests below ~-0.23 m/s^2 instead of ~-0.55
    assert (wind_brake + 0.02) * carcontroller.ACCORD_9G_BRAKE_ACCEL_PER_UNIT < 0.25

  def test_accord_9g_keeps_low_speed_floor_and_is_monotonic(self):
    assert carcontroller.get_honda_nidec_wind_brake(0.0, CAR.HONDA_ACCORD_9G) == pytest.approx(0.001)
    assert carcontroller.get_honda_nidec_wind_brake(2.3, CAR.HONDA_ACCORD_9G) >= 0.002
    speeds = [0.0, 1.0, 2.3, 5.0, 13.4, 22.4, 31.3, 40.2, 50.0]
    values = [carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_ACCORD_9G) for v in speeds]
    assert values == sorted(values)
    assert all(0.0 < w <= 0.15 for w in values)


class TestNidecBrakeGain:
  def test_other_nidec_cars_keep_stock_gain(self):
    assert carcontroller.compute_gas_brake(-1.2, 20.0, CAR.HONDA_CIVIC) == (0.0, pytest.approx(0.25))
    assert carcontroller.compute_gas_brake(0.96, 20.0, CAR.HONDA_CIVIC) == (pytest.approx(0.2), 0.0)

  def test_accord_9g_brakes_harder_per_request_but_gas_unchanged(self):
    gas, brake = carcontroller.compute_gas_brake(-1.2, 20.0, CAR.HONDA_ACCORD_9G)
    assert gas == 0.0 and brake == pytest.approx(1.2 / 3.6)
    assert carcontroller.compute_gas_brake(0.96, 20.0, CAR.HONDA_ACCORD_9G) == (pytest.approx(0.2), 0.0)

  def test_accord_9g_creep_brake_unchanged_at_standstill(self):
    assert carcontroller.compute_gas_brake(0.0, 0.0, CAR.HONDA_ACCORD_9G)[1] == pytest.approx(0.15)
    assert carcontroller.compute_gas_brake(-3.6, 30.0, CAR.HONDA_ACCORD_9G)[1] == pytest.approx(1.0)
