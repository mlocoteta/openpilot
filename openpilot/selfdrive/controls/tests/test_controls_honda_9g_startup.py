"""Controls() startup on both 9G Accord steering boards.

2026-11-22 route 127: controlsd crashed at every TI-path start in create_gain_owner ('LatControlTorqueTI' object has
no attribute 'controller_mode'), so no carControl, no 0x249, a silent TI and a latched TorqueInterceptorMissing.
"""
from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.torque_interceptor import apply_torque_interceptor, ti_qualified
from opendbc.car.honda.values import CAR
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.controls.lib.latcontrol_torque_ti import LatControlTorqueTI
from openpilot.starpilot.flm.tests.test_registered_controls_global import controls_for, feed
from openpilot.starpilot.lateral.gain_runtime import create_gain_owner


def cp_9g(ti: bool):
  fp = gen_empty_fingerprint()
  fp[0][0x201] = 6   # pedal
  cp = CarInterface.get_params(CAR.HONDA_ACCORD_9G, fp, [], False, False, False)
  apply_torque_interceptor(cp, ti)
  assert ti_qualified(cp) is ti
  return cp


def run_frames(controls, n=20):
  now = 100_000_000_000
  for tick in range(n):
    now += int(DT_CTRL * 1e9)
    feed(controls, now, tick, speed=20.0)
    controls.state_control()


def test_ti_controls_init_does_not_crash():
  with controls_for(cp_9g(True)) as controls:
    assert isinstance(controls.LaC, LatControlTorqueTI)
    assert controls.lateral_gain_owner is None
    run_frames(controls)


def test_ti_gain_owner_is_none():
  cp = cp_9g(True)
  controller = LatControlTorqueTI(cp.as_reader(), CarInterface(cp), DT_CTRL)
  assert create_gain_owner(None, cp.as_reader(), controller) is None


def test_ssv3_controls_init_does_not_crash():
  with controls_for(cp_9g(False)) as controls:
    assert not isinstance(controls.LaC, LatControlTorqueTI)
    run_frames(controls)
