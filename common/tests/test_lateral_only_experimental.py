from types import SimpleNamespace

from opendbc.car.hyundai.values import CAR as HYUNDAI_CAR

from openpilot.starpilot.common.lateral_only_experimental import (
  experimental_mode_available,
  lateral_only_experimental_available,
)


def test_telluride_platform_allows_lateral_only_experimental_mode():
  CP = SimpleNamespace(
    carFingerprint=HYUNDAI_CAR.HYUNDAI_PALISADE_2023,
    openpilotLongitudinalControl=False,
  )

  assert lateral_only_experimental_available(CP)
  assert experimental_mode_available(CP)


def test_lateral_only_mode_does_not_expand_other_stock_acc_cars():
  CP = SimpleNamespace(
    carFingerprint=HYUNDAI_CAR.HYUNDAI_SONATA,
    openpilotLongitudinalControl=False,
  )

  assert not lateral_only_experimental_available(CP)
  assert not experimental_mode_available(CP)

  old_palisade = SimpleNamespace(
    carFingerprint=HYUNDAI_CAR.HYUNDAI_PALISADE,
    openpilotLongitudinalControl=False,
  )
  assert not lateral_only_experimental_available(old_palisade)


def test_normal_experimental_mode_remains_available_with_openpilot_long():
  CP = SimpleNamespace(
    carFingerprint=HYUNDAI_CAR.HYUNDAI_SONATA,
    openpilotLongitudinalControl=True,
  )

  assert not lateral_only_experimental_available(CP)
  assert experimental_mode_available(CP)
