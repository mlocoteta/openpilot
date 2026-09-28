from types import SimpleNamespace

import numpy as np
import pytest

from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
import openpilot.selfdrive.controls.lib.longitudinal_planner as longitudinal_planner_module
from openpilot.selfdrive.controls.lib.drive_helpers import CONTROL_N
from openpilot.selfdrive.controls.lib.longitudinal_delay import get_long_actuator_delay, MIN_LONG_ACTUATOR_DELAY
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner, get_accel_from_plan_classic
from openpilot.selfdrive.controls.tests.test_longitudinal_planner import make_sm, make_toggles
from openpilot.common.realtime import DT_MDL


def _cp():
  CP = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_9G)
  assert CP.longitudinalActuatorDelay == pytest.approx(0.15)
  return CP


@pytest.mark.parametrize("toggles, expected", [
  (None, 0.15),                                                   # no toggles -> CarParams
  (SimpleNamespace(), 0.15),                                      # toggle absent -> CarParams
  (SimpleNamespace(longitudinalActuatorDelay=0.3), 0.3),          # the StarPilot param
  (SimpleNamespace(longitudinalActuatorDelay=0.0), MIN_LONG_ACTUATOR_DELAY),  # never ~0 (it is divided by)
  (SimpleNamespace(longitudinalActuatorDelay=float("nan")), 0.15),
  (SimpleNamespace(longitudinalActuatorDelay=3.0), 1.0),
])
def test_get_long_actuator_delay(toggles, expected):
  assert get_long_actuator_delay(_cp(), toggles) == pytest.approx(expected)


def _capture_action_t(monkeypatch, toggles):
  captured = {}
  real = longitudinal_planner_module.get_accel_from_plan

  def fake(speeds, accels, *args, action_t=DT_MDL, **kwargs):
    captured.setdefault("action_t", action_t)
    return real(speeds, accels, *args, action_t=action_t, **kwargs)

  monkeypatch.setattr(longitudinal_planner_module, "get_accel_from_plan", fake)
  planner = LongitudinalPlanner(_cp(), init_v=20.0)
  planner.update(make_sm(20.0, 0.0, -1.0, experimental_mode=False), toggles)
  return planner, captured["action_t"]


def test_planner_uses_the_param_not_carparams(monkeypatch):
  toggles = make_toggles()
  planner, action_t = _capture_action_t(monkeypatch, toggles)
  assert planner.long_actuator_delay == pytest.approx(0.15)
  assert action_t == pytest.approx(0.15 + DT_MDL)

  toggles.longitudinalActuatorDelay = 0.30
  planner, action_t = _capture_action_t(monkeypatch, toggles)
  assert planner.long_actuator_delay == pytest.approx(0.30)
  assert action_t == pytest.approx(0.30 + DT_MDL)


def test_classic_plan_lookahead_follows_the_delay():
  t = longitudinal_planner_module.CONTROL_N_T_IDX
  speeds = 10.0 + 1.0 * np.asarray(t)          # constant +1 m/s^2 plan
  accels = np.ones(CONTROL_N)
  CP = _cp()
  a_cp, _ = get_accel_from_plan_classic(CP, speeds, accels, 0.5)
  a_param, _ = get_accel_from_plan_classic(CP, speeds, accels, 0.5, long_actuator_delay=0.3)
  assert a_cp == pytest.approx(1.0, abs=1e-3) and a_param == pytest.approx(1.0, abs=1e-3)
  # a ramping plan: the longer look-ahead requests the later (higher) accel sooner
  accels_ramp = np.asarray(t) * 0.5
  speeds_ramp = 10.0 + 0.25 * np.asarray(t) ** 2
  a_cp, _ = get_accel_from_plan_classic(CP, speeds_ramp, accels_ramp, 0.5)
  a_param, _ = get_accel_from_plan_classic(CP, speeds_ramp, accels_ramp, 0.5, long_actuator_delay=0.3)
  assert a_param > a_cp
