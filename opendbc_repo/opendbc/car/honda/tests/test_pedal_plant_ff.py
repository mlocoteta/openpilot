from types import SimpleNamespace

import numpy as np
import pytest

from opendbc.car import DT_CTRL, gen_empty_fingerprint, structs
from opendbc.car.honda import pedal_plant_ff as FF
from opendbc.car.honda.pedal_plant_ff import PedalPlantFeedforward, accel_for_pedal, pedal_for_accel
from opendbc.car.honda.values import CAR, DBC

DT = DT_CTRL * 2


@pytest.mark.parametrize("v", [3.0, 6.0, 10.0, 16.0, 25.0])
@pytest.mark.parametrize("accel", [0.0, 0.3, 0.8, 1.5])
def test_inverse_round_trip(v, accel):
  p = pedal_for_accel(accel, v)
  if 0.0 < p < FF.MAX_PEDAL:
    assert accel_for_pedal(p, v) == pytest.approx(accel, abs=1e-3)


def test_monotone_in_accel_and_speed():
  for v in (1.0, 4.0, 10.0, 20.0, 30.0):
    ps = [pedal_for_accel(a, v) for a in np.linspace(-0.5, 3.0, 36)]
    assert all(b >= a for a, b in zip(ps, ps[1:], strict=False))
  # the same accel needs more pedal at higher speed (power-limited plant)
  ps = [pedal_for_accel(1.0, v) for v in (2.0, 5.0, 10.0, 15.0, 20.0)]
  assert all(b > a for a, b in zip(ps, ps[1:], strict=False))


def test_identified_anchor_points():
  # sysid_ff_model.json flat-ground table (full-data fit): v 10 m/s, 1.0 m/s^2 -> 0.250; v 20, 1.0 -> 0.554
  assert pedal_for_accel(1.0, 10.0) == pytest.approx(0.250, abs=0.005)
  assert pedal_for_accel(1.0, 20.0) == pytest.approx(0.554, abs=0.005)
  # holding speed on the highway needs throttle, a light request at low speed needs none (idle creep)
  assert pedal_for_accel(0.0, 30.0) > 0.15
  assert pedal_for_accel(0.0, 3.0) == 0.0
  assert pedal_for_accel(9.0, 30.0) == FF.MAX_PEDAL


def test_inactive_returns_guard_pedal_and_keeps_filter_running():
  ff = PedalPlantFeedforward(DT)
  for k in range(50):
    assert ff.update(0.02 * k, 15.0, 0.123, use=False) == 0.123
  assert ff.d_accel > 0.5  # 1 m/s^3 ramp, filtered
  assert ff.active_steps == 0 and ff.total_steps == 50


def test_envelope_around_guard_pedal():
  ff = PedalPlantFeedforward(DT)
  assert ff.update(1.0, 20.0, 0.10, use=True) == pytest.approx(0.10 + FF.ENVELOPE)
  ff = PedalPlantFeedforward(DT)
  assert ff.update(0.0, 20.0, 0.60, use=True) == pytest.approx(0.60 - FF.ENVELOPE)
  ff = PedalPlantFeedforward(DT)
  guard = pedal_for_accel(1.0, 20.0) - 0.05
  assert ff.update(1.0, 20.0, guard, use=True) == pytest.approx(pedal_for_accel(1.0, 20.0))


def test_low_speed_blend():
  ff = PedalPlantFeedforward(DT)
  assert ff.update(1.0, 0.3, 0.07, use=True) == pytest.approx(0.07)   # standstill launch keeps the guarded map
  ff = PedalPlantFeedforward(DT)
  mid = ff.update(1.0, 1.25, 0.07, use=True)
  full = np.clip(pedal_for_accel(1.0, 1.25), 0.07 - FF.ENVELOPE, 0.07 + FF.ENVELOPE)
  assert mid == pytest.approx(0.5 * 0.07 + 0.5 * full)


def test_lead_on_rising_command_is_bounded_and_decays():
  ff = PedalPlantFeedforward(DT)
  v, guard = 12.0, 0.3
  for _ in range(50):
    ff.update(0.5, v, guard, use=True)
  steady = ff.update(0.5, v, guard, use=True)
  assert steady == pytest.approx(pedal_for_accel(0.5, v))
  step = ff.update(1.5, v, guard, use=True)          # 1 m/s^2 step in one 20 ms step
  assert step > pedal_for_accel(1.5, v)               # lead adds pedal for the lag
  assert step <= pedal_for_accel(1.5 + FF.LEAD_CLAMP, v) + 1e-9
  for _ in range(100):
    last = ff.update(1.5, v, guard, use=True)
  assert last == pytest.approx(pedal_for_accel(1.5, v), abs=1e-3)


def test_disable_file(tmp_path, monkeypatch):
  flag = tmp_path / "pedal_plant_ff_disabled"
  monkeypatch.setattr(FF, "DISABLE_FILE", str(flag))
  assert not FF.ff_disabled_by_file()
  flag.touch()
  assert FF.ff_disabled_by_file()


class _FakeParams:
  def get_float(self, key, block=False, return_default=False, default=0.0):
    return 1.4 if key == "HondaGasFactorParams" else (5.0 if key == "HondaWindFactorParams" else default)

  def get_bool(self, key, block=False):
    return False

  def get(self, key, block=False, return_default=False):
    return None

  def put_float(self, *args, **kwargs):
    pass

  def put_float_nonblocking(self, *args, **kwargs):
    pass


def _accord_9g_pedal_controller(monkeypatch, disabled):
  from opendbc.car.honda.carcontroller import CarController
  from opendbc.car.honda.interface import CarInterface
  monkeypatch.setattr("opendbc.car.honda.carcontroller.Params", lambda: _FakeParams())
  monkeypatch.setattr("opendbc.car.honda.carcontroller.ff_disabled_by_file", lambda: disabled)
  toggles = SimpleNamespace(always_on_lateral_lkas=False, force_torque_controller=False, nnff=False, nnff_lite=False)
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x201] = 6
  CP = CarInterface.get_params(CAR.HONDA_ACCORD_9G, fingerprint, [], False, False, False, toggles)
  assert CP.enableGasInterceptorDEPRECATED
  return CarController(DBC[CP.carFingerprint], CP), toggles


def _pedal_commands(monkeypatch, controller, toggles, accel, v, lcs, frames=60):
  sent = []
  monkeypatch.setattr("opendbc.car.honda.carcontroller.create_gas_interceptor_command",
                      lambda packer, gas, idx: sent.append(gas) or (0x200, b"", 0))
  monkeypatch.setattr("opendbc.car.honda.carcontroller.hondacan.create_steering_control", lambda *args, **kwargs: (0xE4, b"", 0))
  monkeypatch.setattr("opendbc.car.honda.carcontroller.hondacan.create_lkas_hud", lambda *args, **kwargs: [])
  monkeypatch.setattr("opendbc.car.honda.carcontroller.hondacan.create_acc_hud", lambda *args, **kwargs: (0x30C, b"", 0))
  monkeypatch.setattr("opendbc.car.honda.carcontroller.hondacan.create_brake_command", lambda *args, **kwargs: (0x1FA, b"", 0))
  CC = structs.CarControl.new_message()
  CC.enabled = True
  CC.longActive = True
  CC.actuators.accel = accel
  CC.actuators.longControlState = lcs
  CC.hudControl.visualAlert = structs.CarControl.HUDControl.VisualAlert.none
  CS = SimpleNamespace(out=SimpleNamespace(vEgo=v, aEgo=accel, steeringPressed=False, gasPressed=False, brakePressed=False,
                                           steeringAngleDeg=0.0, steeringRateDeg=0.0, standstill=False,
                                           cruiseState=SimpleNamespace(available=True)),
                       v_cruise_factor=1.0, stock_brake=0, CP=controller.CP, is_metric=False, acc_hud={}, lkas_hud={})
  for _ in range(frames):
    controller.update(CC.as_reader(), CS, 0, toggles)
    controller.frame += 1
  return sent


def test_carcontroller_uses_feedforward_in_pid_and_guard_otherwise(monkeypatch):
  LCS = structs.CarControl.Actuators.LongControlState
  on, toggles = _accord_9g_pedal_controller(monkeypatch, disabled=False)
  off, _ = _accord_9g_pedal_controller(monkeypatch, disabled=True)
  assert on.pedal_ff is not None and off.pedal_ff is None and off.pedal_ff_disabled
  p_on = _pedal_commands(monkeypatch, on, toggles, 1.0, 20.0, LCS.pid)
  p_off = _pedal_commands(monkeypatch, off, toggles, 1.0, 20.0, LCS.pid)
  assert p_on and p_off
  assert abs(p_on[-1] - p_off[-1]) <= FF.ENVELOPE + 1e-6
  assert p_on[-1] == pytest.approx(float(np.clip(pedal_for_accel(1.0, 20.0), p_off[-1] - FF.ENVELOPE, p_off[-1] + FF.ENVELOPE)))
  # outside the PID state (starting) the guarded map is sent unchanged
  on2, _ = _accord_9g_pedal_controller(monkeypatch, disabled=False)
  off2, _ = _accord_9g_pedal_controller(monkeypatch, disabled=True)
  assert _pedal_commands(monkeypatch, on2, toggles, 1.0, 3.0, LCS.starting) == \
         _pedal_commands(monkeypatch, off2, toggles, 1.0, 3.0, LCS.starting)
