import pytest

from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.tesla.carstate import update_tesla_gas_pressed
from opendbc.car.tesla.teslacan import TeslaCAN
from opendbc.car.tesla.values import CarControllerParams


class RecordingPacker:
  def make_can_msg(self, name, bus, values):
    return name, bus, values


@pytest.mark.parametrize(
  ("v_ego", "accel", "expected_set_speed"),
  [
    (20.0, 1.0, 21.0 * CV.MS_TO_KPH),
    (20.0, -2.0, 18.0 * CV.MS_TO_KPH),
    (1.0, -2.0, 0.0),
    (120.0, 2.0, 400.0),
  ],
)
def test_longitudinal_set_speed_tracks_accel_continuously(v_ego, accel, expected_set_speed):
  _, _, values = TeslaCAN(RecordingPacker()).create_longitudinal_command(4, accel, 0, 200, v_ego, False)

  assert values["DAS_setSpeed"] == pytest.approx(expected_set_speed)


def test_longitudinal_jerk_ramps_after_gas_release():
  can = TeslaCAN(RecordingPacker())

  _, _, pressed = can.create_longitudinal_command(4, 0, 0, 20, 20, True)
  _, _, halfway = can.create_longitudinal_command(4, 0, 1, 70, 20, False)
  _, _, complete = can.create_longitudinal_command(4, 0, 2, 120, 20, False)

  assert pressed["DAS_jerkMin"] == pytest.approx(0.0)
  assert pressed["DAS_jerkMax"] == pytest.approx(0.0)
  assert halfway["DAS_jerkMin"] == pytest.approx(-CarControllerParams.JERK_LIMIT_MAX / 2)
  assert halfway["DAS_jerkMax"] == pytest.approx(CarControllerParams.JERK_LIMIT_MAX / 2)
  assert complete["DAS_jerkMin"] == pytest.approx(-CarControllerParams.JERK_LIMIT_MAX)
  assert complete["DAS_jerkMax"] == pytest.approx(CarControllerParams.JERK_LIMIT_MAX)


def test_longitudinal_jerk_release_timer_resets_while_gas_is_pressed():
  can = TeslaCAN(RecordingPacker())

  can.create_longitudinal_command(4, 0, 0, 20, 20, True)
  _, _, values = can.create_longitudinal_command(4, 0, 1, 80, 20, True)

  assert values["DAS_jerkMin"] == pytest.approx(0.0)
  assert values["DAS_jerkMax"] == pytest.approx(0.0)


def test_tesla_gas_pressed_hysteresis_prevents_release_chatter():
  assert update_tesla_gas_pressed(False, 0.4) is False
  assert update_tesla_gas_pressed(False, 0.8) is False
  assert update_tesla_gas_pressed(False, 1.2) is True
  assert update_tesla_gas_pressed(True, 0.4) is False
  assert update_tesla_gas_pressed(True, 0.8) is True
