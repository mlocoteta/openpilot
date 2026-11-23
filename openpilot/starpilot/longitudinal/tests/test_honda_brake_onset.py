"""Accord 9G pedal long-PID brake-onset hold (7.0 port of 6.x F09, 66485e4a2): the 6.x test cases on 7.0's LongControl."""
from types import SimpleNamespace

import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.controls.lib.longcontrol import LongControl
from openpilot.starpilot.longitudinal import honda_brake_onset as hbo
from openpilot.starpilot.longitudinal.extension import LongitudinalContext, create_extension

NO_LEADS = (SimpleNamespace(status=False), SimpleNamespace(status=False))


def cp(identity=CAR.HONDA_ACCORD_9G, pedal=True):
  fp = gen_empty_fingerprint()
  if pedal:
    fp[0][0x201] = 6
  return CarInterface.get_params(identity, fp, [], False, False, False)


def lc_for(identity=CAR.HONDA_ACCORD_9G, pedal=True):
  params = cp(identity, pedal)
  params.longitudinalTuning.kiBP = [0.]
  params.longitudinalTuning.kiV = [1.0]
  return LongControl(params)


def state(v_ego=20.0, a_ego=0.0, gas=False):
  return SimpleNamespace(vEgo=v_ego, aEgo=a_ego, brakePressed=False, gasPressed=gas, canValid=True, canTimeout=False,
                         cruiseState=SimpleNamespace(standstill=False))


def run(lc, frames, a_target=-1.2, a_ego=-0.2, should_stop=False, leads=NO_LEADS, gas_frames=0, i0=0.0, v_ego=20.0):
  ctx = LongitudinalContext(leads=leads)
  for _ in range(gas_frames):  # gas override: long inactive, as controlsd does
    lc.update(False, state(a_ego=0.3, gas=True), 0.0, False, (-3.5, 2.0), context=ctx)
  lc.update(True, state(), 0.0, False, (-3.5, 2.0), context=ctx)  # cruising
  lc.pid.i = i0
  out = []
  for _ in range(frames):
    out.append((float(lc.update(True, state(v_ego, a_ego), a_target, should_stop, (-3.5, 2.0), context=ctx)), lc.pid.i))
  return out


def test_9g_pedal_delay_gives_the_6x_window():
  assert cp().longitudinalActuatorDelay == pytest.approx(0.30)
  assert hbo.window_frames(0.30) == 45
  assert hbo.window_frames(0.40) == 55
  assert hbo.window_frames(float("nan")) == 45
  assert hbo.window_frames(None) == 45
  assert hbo.window_frames(5.0) == 115  # capped at 1.0 s
  assert create_extension(cp()).honda_onset.window == 45


def test_only_on_the_9g_pedal_car():
  for other in (cp(pedal=False), cp(CAR.HONDA_CIVIC)):
    ext = create_extension(other)
    assert ext is None or ext.honda_onset is None


def test_freezes_integrator_for_the_lag_window():
  out = run(lc_for(), 80)
  # error -1.0 would integrate 0.01 per frame; held at 0 for the 45-frame window (incl. the crossing frame)
  assert out[43][1] == pytest.approx(0.0)
  assert out[43][0] == pytest.approx(-1.2)
  assert out[60][1] < -0.1


def test_clamps_stale_negative_i():
  out = run(lc_for(), 10, i0=-0.9)
  assert out[0][1] == pytest.approx(hbo.I_FLOOR)
  assert out[0][0] == pytest.approx(-1.2 + hbo.I_FLOOR)


def test_after_gas_release():
  lc = lc_for()
  lc.extension.honda_onset.prev_a_target = -1.2  # target already below -0.3: only the gas/longActive edge opens the window
  out = run(lc, 50, gas_frames=30)
  assert all(i == pytest.approx(0.0) for _, i in out[:43])


@pytest.mark.parametrize("case", ["close_lead", "closing_lead", "low_speed", "small_target", "already_braking",
                                  "other_honda", "no_pedal", "radar_unknown"])
def test_does_not_trigger(case):
  kwargs = {}
  lc = lc_for()
  if case == "close_lead":
    kwargs["leads"] = (SimpleNamespace(status=True, dRel=25.0, vRel=-10.0, vLead=10.0),)  # TTC 2.5 s
  elif case == "closing_lead":
    kwargs["leads"] = (None, SimpleNamespace(status=True, dRel=45.0, vRel=-10.0, vLead=10.0))  # TTC 4.5 s, lead two
  elif case == "low_speed":
    kwargs["v_ego"] = 7.5
  elif case == "small_target":
    kwargs["a_target"] = -0.25
  elif case == "already_braking":
    kwargs["a_ego"] = -1.0  # aEgo - aTarget = 0.2 <= 0.3
  elif case == "other_honda":
    lc = lc_for(CAR.HONDA_CIVIC)
  elif case == "no_pedal":
    lc = lc_for(pedal=False)
  elif case == "radar_unknown":
    kwargs["leads"] = None  # 7.0: no usable radarState -> no hold
  out = run(lc, 20, i0=-0.9, **kwargs)
  assert out[0][1] < -0.9  # stale I kept and still integrating


def test_skips_should_stop():
  hold = hbo.HondaBrakeOnsetHold(0.30)
  hold.track(True, False, -1.2)
  assert hold.frames == 0
  pid = SimpleNamespace(i=-0.9)
  assert not hold.hold(pid, -1.2, state(a_ego=-0.2), True, NO_LEADS)
  assert pid.i == pytest.approx(-0.9)
  assert hold.hold(pid, -1.2, state(a_ego=-0.2), False, NO_LEADS)
  assert pid.i == pytest.approx(hbo.I_FLOOR)


def test_ends_after_the_window():
  lc = lc_for()
  run(lc, 50)
  lc.pid.i = -0.9  # 0.5 s after the onset: outside the window, no clamp
  lc.update(True, state(a_ego=-0.2), -1.2, False, (-3.5, 2.0), context=LongitudinalContext(leads=NO_LEADS))
  assert lc.pid.i < -0.9


def test_far_lead_still_holds():
  far = (SimpleNamespace(status=True, dRel=60.0, vRel=-5.0, vLead=15.0),  # TTC 12 s
         SimpleNamespace(status=True, dRel=30.0, vRel=1.0, vLead=21.0))   # pulling away
  out = run(lc_for(), 20, i0=-0.9, leads=far)
  assert out[0][1] == pytest.approx(hbo.I_FLOOR)


def test_tracking_survives_inactive_frames():
  hold = hbo.HondaBrakeOnsetHold(0.30)
  for _ in range(10):
    hold.track(False, False, 0.0)
  assert hold.frames == hbo.NEVER
  hold.track(True, False, 0.0)  # longActive rising edge
  assert hold.frames == 0
  hold.track(True, False, 0.0)
  assert hold.frames == 1
