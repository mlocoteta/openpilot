"""Honda 9G Accord pedal longitudinal (independent of the steering hardware)."""
import pytest

from opendbc.car import structs
from opendbc.car.car_helpers import interfaces
from opendbc.car.honda import carcontroller, carstate, interface
from opendbc.car.honda.accord_9g_tune import TI_CAR, use_tune
from opendbc.car.honda.values import CAR
from opendbc.car.tests.test_car_interfaces import get_test_starpilot_toggles

DT_NS = 10_000_000

@pytest.fixture(autouse=True)
def ti_car_tune():
  # These tests pin the TI car's numbers; the branch default (stock) is covered in test_accord_9g_tune.py.
  with use_tune(TI_CAR):
    yield


class FakeParams:
  def __init__(self, *args, **kwargs):
    pass

  def get_bool(self, key, *args, **kwargs):
    return False

  def get_float(self, key, *args, default=0.0, **kwargs):
    return default

  def get_int(self, key, *args, default=0, **kwargs):
    return default

  def get(self, *args, **kwargs):
    return None

  def put_float(self, *args, **kwargs):
    pass


class TestNidecWindBrake:
  def test_other_nidec_cars_keep_stock_curve(self):
    for v, expected in ((0.0, 0.001), (2.3, 0.002), (35.0, 0.15)):
      assert carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_CIVIC) == pytest.approx(expected)

  def test_accord_9g_brakes_for_mild_decel_at_highway_speed(self):
    v = 22.4  # 50 mph
    stock = carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_CIVIC)
    wind_brake = carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_ACCORD_9G)
    assert wind_brake == pytest.approx(0.136 / TI_CAR.brake_accel_per_unit)
    assert wind_brake < stock / 2
    # brakes engage (hysteresis on at 0.02) for requests below ~-0.23 m/s^2 instead of ~-0.55
    assert (wind_brake + 0.02) * TI_CAR.brake_accel_per_unit < 0.25

  def test_accord_9g_keeps_low_speed_floor_and_is_monotonic(self):
    assert carcontroller.get_honda_nidec_wind_brake(0.0, CAR.HONDA_ACCORD_9G) == pytest.approx(0.001)
    assert carcontroller.get_honda_nidec_wind_brake(2.3, CAR.HONDA_ACCORD_9G) >= 0.002
    speeds = [0.0, 1.0, 2.3, 5.0, 13.4, 22.4, 31.3, 40.2, 50.0]
    values = [carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_ACCORD_9G) for v in speeds]
    assert values == sorted(values)
    assert all(0.0 < w <= 0.15 for w in values)


class TestNidecBrakeGain:
  def test_other_nidec_cars_keep_stock_gain(self):
    assert carcontroller.compute_gas_brake(-1.2, 20.0, CAR.HONDA_CIVIC) == (0.0, pytest.approx(0.25))
    assert carcontroller.compute_gas_brake(0.96, 20.0, CAR.HONDA_CIVIC) == (pytest.approx(0.2), 0.0)

  def test_accord_9g_brakes_harder_per_request_but_gas_unchanged(self):
    gas, brake = carcontroller.compute_gas_brake(-1.2, 20.0, CAR.HONDA_ACCORD_9G)
    assert gas == 0.0 and brake == pytest.approx(1.2 / 3.6)
    assert carcontroller.compute_gas_brake(0.96, 20.0, CAR.HONDA_ACCORD_9G) == (pytest.approx(0.2), 0.0)

  def test_accord_9g_creep_brake_unchanged_at_standstill(self):
    assert carcontroller.compute_gas_brake(0.0, 0.0, CAR.HONDA_ACCORD_9G)[1] == pytest.approx(0.15)
    assert carcontroller.compute_gas_brake(-3.6, 30.0, CAR.HONDA_ACCORD_9G)[1] == pytest.approx(1.0)


class LearnerParams(FakeParams):
  STORE = {"HondaGasFactorParams": 1.13, "HondaWindFactorParams": 5.0}

  def get_float(self, key, *args, default=0.0, **kwargs):
    return self.STORE.get(key, default)

  def put_float(self, key, value):
    pass


def pedal_interface(monkeypatch, pedal):
  for module in (carstate, carcontroller, interface):
    monkeypatch.setattr(module, "Params", LearnerParams, raising=False)
  toggles = get_test_starpilot_toggles()
  fingerprint = {bus: {} for bus in range(8)}
  if pedal:
    fingerprint[0] = {0x201: 6}  # pedal interceptor
  CarInterface = interfaces[CAR.HONDA_ACCORD_9G]
  CP = CarInterface.get_params(CAR.HONDA_ACCORD_9G, fingerprint, [], alpha_long=True, is_release=False, docs=False,
                               starpilot_toggles=toggles)
  assert CP.enableGasInterceptorDEPRECATED == pedal
  return CarInterface(CP, CarInterface.get_starpilot_params(CAR.HONDA_ACCORD_9G, fingerprint, [], CP, toggles)), toggles


class TestPedalLearnerLog:
  def test_logged_at_start_and_every_60_s(self, monkeypatch):
    cc = pedal_interface(monkeypatch, True)[0].CC
    assert cc.log_pedal_learner
    lines = []
    monkeypatch.setattr(carcontroller.carlog, "warning", lambda msg, *a: lines.append(msg))
    cc._log_pedal_learner()
    # The stored 1.13 is below the guard band and starts at 1.2.
    assert "(drive start)" in lines[0] and "gas factor 1.200" in lines[0] and "wind factor 5.000" in lines[0]
    assert "stored 1.130" in lines[0]
    cc.frame = carcontroller.PEDAL_LEARNER_LOG_INTERVAL_FRAMES
    cc.bosch_gas_factor = 1.3
    cc._log_pedal_learner()
    assert "drive start" not in lines[1] and "t 60 s" in lines[1] and "gas factor 1.300 (start 1.200, +0.100)" in lines[1]
    assert cc.bosch_gas_factor == 1.3 and cc.bosch_wind_factor == 5.0  # logging never touches the learner

  def test_update_logs_at_start_and_every_60_s(self, monkeypatch):
    CI, toggles = pedal_interface(monkeypatch, True)
    lines = []
    monkeypatch.setattr(carcontroller.carlog, "warning", lambda msg, *a: lines.append(msg))
    CC = structs.CarControl().as_reader()
    for frame in range(2 * carcontroller.PEDAL_LEARNER_LOG_INTERVAL_FRAMES + 1):
      CI.update([(frame * DT_NS, [])], toggles)
      CI.apply(CC, frame * DT_NS, toggles)
    learner = [m for m in lines if m.startswith("Honda pedal learner")]
    assert len(learner) == 3 and "(drive start)" in learner[0] and "t 60 s" in learner[1] and "t 120 s" in learner[2]

  def test_not_logged_without_pedal(self, monkeypatch):
    assert not pedal_interface(monkeypatch, False)[0].CC.log_pedal_learner


class TestPedalGasFactorGuard:
  def _cc(self, accel, long_active=True):
    CC = structs.CarControl()
    CC.enabled = long_active
    CC.longActive = long_active
    CC.actuators.accel = accel
    CC.actuators.longControlState = structs.CarControl.Actuators.LongControlState.pid
    return CC.as_reader()

  def test_guard_only_on_9g_pedal(self, monkeypatch):
    cc = pedal_interface(monkeypatch, True)[0].CC
    assert cc.pedal_guard is not None and cc.bosch_gas_factor == 1.2 and cc.gas_factor_stored == 1.13
    assert pedal_interface(monkeypatch, False)[0].CC.pedal_guard is None

  def test_launch_uses_capped_factor_and_does_not_learn(self, monkeypatch):
    CI, toggles = pedal_interface(monkeypatch, True)
    CC = self._cc(1.6)
    for frame in range(400):  # standstill (vEgo 0), +1.6 requested, aEgo 0: stock would raise the factor
      CI.update([(frame * DT_NS, [])], toggles)
      CI.apply(CC, frame * DT_NS, toggles)
    cc = CI.CC
    assert cc.bosch_gas_factor == 1.2   # below MIN_SPEED: no learning
    gas = 1.6 / 4.8 - 0.15               # compute_gb_honda_nidec at v=0 (creep brake)
    wind = carcontroller.get_honda_nidec_wind_brake(0.0, CAR.HONDA_ACCORD_9G)
    expected = 0.4 * (gas * 1.0 + wind * cc.bosch_wind_factor * 0.75)  # applied factor capped at 1.0
    assert cc.gas == pytest.approx(expected, abs=1e-6)
