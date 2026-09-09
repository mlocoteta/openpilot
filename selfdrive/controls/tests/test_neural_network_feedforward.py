from opendbc.car.hyundai.values import CAR as HYUNDAI_CAR

from openpilot.starpilot.controls.lib.neural_network_feedforward import (
  DEFAULT_NNFF_LAT_JERK_FRICTION_FACTOR,
  PALISADE_NNFF_LAT_JERK_FRICTION_FACTOR,
  get_nnff_lat_jerk_friction_factor,
)


def test_palisade_nnff_jerk_friction_factor_is_damped_for_bumps():
  assert get_nnff_lat_jerk_friction_factor(HYUNDAI_CAR.HYUNDAI_PALISADE_2023) == PALISADE_NNFF_LAT_JERK_FRICTION_FACTOR
  assert PALISADE_NNFF_LAT_JERK_FRICTION_FACTOR < DEFAULT_NNFF_LAT_JERK_FRICTION_FACTOR


def test_other_nnff_cars_keep_default_jerk_friction_factor():
  assert get_nnff_lat_jerk_friction_factor(HYUNDAI_CAR.HYUNDAI_SONATA) == DEFAULT_NNFF_LAT_JERK_FRICTION_FACTOR
  assert get_nnff_lat_jerk_friction_factor(HYUNDAI_CAR.HYUNDAI_PALISADE) == DEFAULT_NNFF_LAT_JERK_FRICTION_FACTOR
