"""TI always-on lateral (F05), controller side: torque only with ACC main on.

The panda drops non-zero 0x249 the moment MAIN goes off (honda_stock_aol.h); the host's native
lateralAllowed follows at ~10 Hz. TorqueInterceptor also checks cruiseState.available (the same
0x1A6 MAIN_ON) every frame, so torque goes to neutral in the same frame instead of being dropped.
"""
from opendbc.car.honda.tests.test_torque_interceptor import run_frame, ti_car, ti_feedback  # noqa: F401
from opendbc.car.honda.torque_interceptor import TI_LIMITS, TI_STATE


def test_main_off_zeroes_ti_torque_same_frame(ti_car):  # noqa: F811
  ci, packer = ti_car
  for frame in range(5):
    request = run_frame(ci, packer, frame, ti_feedback(TI_STATE.RUN))[0]
  assert request == TI_LIMITS.TI_STEER_DELTA_UP * 5
  assert ci.CS.out.cruiseState.available
  request = run_frame(ci, packer, 5, ti_feedback(TI_STATE.RUN), main_on=False)[0]
  assert not ci.CS.out.cruiseState.available
  assert request == 0
  # MAIN back on: ramps again from zero at the normal rate
  requests = [run_frame(ci, packer, 6 + i, ti_feedback(TI_STATE.RUN))[0] for i in range(3)]
  assert requests == [TI_LIMITS.TI_STEER_DELTA_UP * (i + 1) for i in range(3)]
