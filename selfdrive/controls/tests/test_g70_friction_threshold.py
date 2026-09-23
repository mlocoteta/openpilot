import math

import numpy as np
import pytest

from opendbc.car import structs
from opendbc.car.lateral import get_friction
from openpilot.selfdrive.controls.lib import latcontrol_vehicle_tunes as tunes


def legacy_threshold(speed, accel, jerk):
  def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))
  gain = (0.10 * sigmoid((speed - 10.0) / 3.0) * sigmoid((35.0 - speed) / 6.0) *
          sigmoid((0.28 - abs(accel)) / 0.10) * sigmoid((0.35 - abs(jerk)) / 0.10))
  return tunes.get_standard_friction_threshold(speed) * (1.0 + gain)


@pytest.mark.parametrize('speed,scale', [(0, 1), (5, 1), (10, 1), (15, 1.5), (20, 2), (35, 2), (45, 2)])
@pytest.mark.parametrize('accel,jerk', [(0, 0), (0.1, 0.2), (0.8, 0.3), (1.5, -0.5), (-0.8, -0.3)])
def test_speed_blend(speed, scale, accel, jerk):
  assert tunes.get_genesis_g70_friction_threshold(speed, accel, jerk) == pytest.approx(
    legacy_threshold(speed, accel, jerk) * scale)


def test_small_error_gain_and_full_compensation():
  params = structs.CarParams.LateralTorqueTuning.new_message(friction=0.08, latAccelFactor=2.96)
  old = legacy_threshold(30, 0.8, 0.2)
  new = tunes.get_genesis_g70_friction_threshold(30, 0.8, 0.2)
  for error in (-0.1, 0.1):
    assert get_friction(error, 0, new, params) == pytest.approx(get_friction(error, 0, old, params) / 2)
  for error in (-2, 2):
    assert get_friction(error, 0, new, params) == pytest.approx(get_friction(error, 0, old, params))


def test_symmetric_and_continuous():
  for speed in np.linspace(0, 45, 100):
    assert tunes.get_genesis_g70_friction_threshold(speed, 0.8, 0.2) == pytest.approx(
      tunes.get_genesis_g70_friction_threshold(speed, -0.8, -0.2))
  for speed in (10, 20):
    assert abs(tunes.get_genesis_g70_friction_threshold(speed + 1e-6) -
               tunes.get_genesis_g70_friction_threshold(speed - 1e-6)) < 1e-6
