from types import SimpleNamespace

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.starpilot.car.honda.steering_board_watch import install
from openpilot.starpilot.vehicle_preferences import VehicleStartupPreferences


class FakeParams:
  def __init__(self, missing=False):
    self.values = {"TorqueInterceptorMissing": missing}
    self.writes = []

  def get_bool(self, key):
    return self.values.get(key, False)

  def put_bool_nonblocking(self, key, value):
    self.values[key] = value
    self.writes.append((key, value))


def cp_9g():
  return CarInterface.get_params(CAR.HONDA_ACCORD_9G, gen_empty_fingerprint(), [], False, False, False)


def fp(ssv3: bool):
  f = gen_empty_fingerprint()
  if ssv3:
    f[0][0x190] = 5
  return f


def test_startup_selection_ti_unchanged_and_fallback():
  ti_bit = 4096
  for prefs, ssv3, ti in (
    (VehicleStartupPreferences(honda_torque_interceptor=True), True, True),        # today
    (VehicleStartupPreferences(honda_torque_interceptor=True, honda_ti_missing=True), True, False),
    (VehicleStartupPreferences(honda_torque_interceptor=True, honda_ti_missing=True), False, True),
    (VehicleStartupPreferences(honda_torque_interceptor=True, honda_board_override="ssv3"), True, False),
    (VehicleStartupPreferences(honda_torque_interceptor=False), True, False),
  ):
    cp = cp_9g()
    base = int(cp.safetyConfigs[0].safetyParam)
    prefs.prepare(cp, fingerprints=fp(ssv3))
    assert bool(int(cp.safetyConfigs[0].safetyParam) & ti_bit) is ti
    if not ti:
      assert int(cp.safetyConfigs[0].safetyParam) == base


def test_watch_records_once_and_clears_once():
  cp = cp_9g()
  from opendbc.car.honda.torque_interceptor import apply_torque_interceptor
  apply_torque_interceptor(cp, True)
  ci = CarInterface(cp)
  params = FakeParams(missing=True)
  watch = install(ci, params)
  ci.CS.ti.feedback_seen = True
  watch.update()
  watch.update()
  assert params.writes == [("TorqueInterceptorMissing", False)]
  ci.CS.ti.feedback_seen = False
  ci.CS.ti_presence.missing = True
  watch.update()
  watch.update()
  assert params.writes[-1] == ("TorqueInterceptorMissing", True) and len(params.writes) == 2


def test_no_watch_off_the_ti_path():
  assert install(CarInterface(cp_9g()), FakeParams()) is None
  assert install(SimpleNamespace(CS=None), FakeParams()) is None
