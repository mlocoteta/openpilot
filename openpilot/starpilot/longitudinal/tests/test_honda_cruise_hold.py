"""LongControl copy of the Accord 9G cruise-hold brake deadband: I freezes at the pedal-close point."""
from types import SimpleNamespace

import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda import cruise_brake_deadband as cbd
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.controls.lib.longcontrol import LongControl
from openpilot.starpilot.longitudinal.extension import HondaCruiseHold, LongitudinalContext, create_extension

V65 = 65 * cbd.MPH


def cp(identity=CAR.HONDA_ACCORD_9G, pedal=True):
  fp = gen_empty_fingerprint()
  if pedal:
    fp[0][0x201] = 6
  return CarInterface.get_params(identity, fp, [], False, False, False)


def inputs(**kw):
  return dict(dict(v_cruise=V65, a_target=0.0, should_stop=False, plan_source="cruise", lead_brake=False, curve_active=False), **kw)


def run(controller, honda_cruise, frames=3000, a_ego=0.3, a_target=0.0):
  # gentle downgrade: the car accelerates slightly with the pedal closed, plan at 0 -> I winds down
  state = SimpleNamespace(vEgo=V65, aEgo=a_ego, brakePressed=False, gasPressed=False, canValid=True, canTimeout=False,
                          cruiseState=SimpleNamespace(standstill=False))
  ctx = LongitudinalContext(honda_cruise=honda_cruise)
  return [controller.update(True, state, a_target, False, (-3.5, 2.0), context=ctx) for _ in range(frames)]


def test_extension_only_on_the_9g_pedal_car():
  assert create_extension(cp()).honda_cruise is not None
  for other in (cp(pedal=False), cp(CAR.HONDA_CIVIC)):
    ext = create_extension(other)
    assert ext is None or ext.honda_cruise is None


def test_i_holds_at_pedal_close_while_suppressing():
  out = run(LongControl(cp()), inputs())
  close = cbd.pedal_close_accel(V65)
  assert min(out) >= close - 0.02
  assert out[-1] == pytest.approx(close, abs=0.02)


def test_without_inputs_or_with_real_demand_i_winds_as_before():
  base = LongControl(cp())
  base.extension.honda_cruise = None
  ref = run(base, None)
  assert run(LongControl(cp()), None) == ref  # no plan inputs (disabled / stale): unchanged
  assert min(ref) < cbd.pedal_close_accel(V65) - 0.2
  base2 = LongControl(cp())
  base2.extension.honda_cruise = None
  ref2 = run(base2, inputs(a_target=-0.5), a_target=-0.5)
  assert run(LongControl(cp()), inputs(a_target=-0.5), a_target=-0.5) == ref2


def test_hold_resets():
  h = HondaCruiseHold()
  h.gate.suppressing = True
  h.reset()
  assert not h.gate.suppressing
