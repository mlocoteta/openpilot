"""Accord 9G pedal long actuator delay 0.30 s (7.0 port of 6.x F12, c75153aab).

6.x ran LongitudinalActuatorDelay 0.30 on the 9G pedal car (planner action_t and modeld long_delay); the 7.0 port
fell back to the 0.15 default. Only the 9G with a pedal interceptor changes; every other Honda keeps its value.
"""
import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import ACCORD_9G_PEDAL_LONG_ACTUATOR_DELAY, CarInterface
from opendbc.car.honda.values import CAR, HondaFlags


def params(identity, pedal):
  fp = gen_empty_fingerprint()
  if pedal:
    fp[0][0x201] = 6
  return CarInterface.get_params(identity, fp, [], False, False, False)


def test_9g_pedal_delay_is_6x_value():
  cp = params(CAR.HONDA_ACCORD_9G, pedal=True)
  assert cp.flags & HondaFlags.GAS_INTERCEPTOR
  assert ACCORD_9G_PEDAL_LONG_ACTUATOR_DELAY == pytest.approx(0.30)
  assert cp.longitudinalActuatorDelay == pytest.approx(0.30)


def test_9g_without_pedal_keeps_default():
  cp = params(CAR.HONDA_ACCORD_9G, pedal=False)
  assert not cp.flags & HondaFlags.GAS_INTERCEPTOR
  assert cp.longitudinalActuatorDelay == pytest.approx(0.15)


@pytest.mark.parametrize("identity", [c for c in CAR if c != CAR.HONDA_ACCORD_9G])
def test_other_hondas_unchanged(identity):
  for pedal in (False, True):
    cp = params(identity, pedal)
    # no other Honda uses 0.30 (0.05 / 0.15 / 0.4 / 0.5), so any 0.30 here would be this override leaking
    assert cp.longitudinalActuatorDelay != pytest.approx(ACCORD_9G_PEDAL_LONG_ACTUATOR_DELAY), (identity, pedal)
