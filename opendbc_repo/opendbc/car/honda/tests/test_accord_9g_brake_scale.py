"""Accord 9G Nidec brake scale 3.6 m/s^2 per brake unit (7.0 port of 6.x 8d1f75031, F06 brake half).

Brake side only: the friction brake (0x1FA COMPUTER_BRAKE) uses accel / 3.6 on the 9G. The pedal interceptor
command, the PCM speed target, the creep brake and the wind brake table are unchanged, and every other Honda keeps
the stock 4.8. The command is still capped at NIDEC_BRAKE_MAX - 1 = 255.
"""
import numpy as np
import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda import carcontroller, cruise_brake_deadband as cbd, nidec_brake_scale
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR, HondaFlags

MPH = 0.44704
CREATE_BRAKE_COMMAND = carcontroller.hondacan.create_brake_command
CREATE_ACC_HUD = carcontroller.hondacan.create_acc_hud
BOSCH_CARS = sorted(c for c in CAR if c.config.flags & HondaFlags.BOSCH)
NIDEC_CARS = sorted(c for c in CAR if c not in BOSCH_CARS)


def wind_brake(v):
  return float(np.interp(v, [0.0, 2.3, 35.0], [0.001, 0.002, 0.15]))


def expected_counts(accel, v, per_unit):
  """Steady 0x1FA count for a constant accel: clip(-accel/scale, 0, 1) - hysteresis gap (0.01) - wind brake."""
  brake = float(np.clip(-accel / per_unit, 0.0, 1.0))
  return int(np.clip((brake - 0.01 - wind_brake(v)) * 256, 0, 255))


def run(monkeypatch, accel, v_ego, identity=CAR.HONDA_ACCORD_9G, pedal=True, frames=300, per_unit=None):
  """Constant accel request through the real CarInterface; returns (0x1FA counts, pedal commands, pcm_speeds, CC)."""
  fp = gen_empty_fingerprint()
  if pedal:
    fp[0][0x201] = 6
  cp = CarInterface.get_params(identity, fp, [], False, False, False)
  ci = CarInterface(cp)
  ci.update([])
  if per_unit is not None:
    ci.CC.brake_accel_per_unit = per_unit
  brakes, pcm_speeds = [], []

  def capture_brake(packer, CAN, apply_brake, *args):
    brakes.append(apply_brake)
    return CREATE_BRAKE_COMMAND(packer, CAN, apply_brake, *args)

  def capture_hud(packer, bus, CP, enabled, pcm_speed, *args):
    pcm_speeds.append(pcm_speed)
    return CREATE_ACC_HUD(packer, bus, CP, enabled, pcm_speed, *args)

  monkeypatch.setattr(carcontroller.hondacan, "create_brake_command", capture_brake)
  monkeypatch.setattr(carcontroller.hondacan, "create_acc_hud", capture_hud)
  command = structs.CarControl(enabled=True, longActive=True, latActive=False)
  command.actuators.accel = accel
  command.actuators.longControlState = "pid"
  command = command.as_reader()
  gases = []
  for tick in range(frames):
    ci.CS.out.vEgo = v_ego
    ci.apply(command, 1_000_000_000 + tick * 10_000_000)
    gases.append(ci.CC.gas)
  return brakes, gases, pcm_speeds, ci.CC


class TestScale:
  def test_constants(self):
    assert nidec_brake_scale.ACCORD_9G_BRAKE_ACCEL_PER_UNIT == 3.6
    assert nidec_brake_scale.NIDEC_ACCEL_PER_UNIT == 4.8
    assert nidec_brake_scale.nidec_brake_accel_per_unit(CAR.HONDA_ACCORD_9G) == 3.6
    for car in CAR:
      if car != CAR.HONDA_ACCORD_9G:
        assert nidec_brake_scale.nidec_brake_accel_per_unit(car) == 4.8

  def test_deadband_uses_the_same_value(self):
    assert cbd.BRAKE_ACCEL_PER_UNIT == nidec_brake_scale.ACCORD_9G_BRAKE_ACCEL_PER_UNIT
    assert cbd.PEDAL_ACCEL_PER_UNIT == nidec_brake_scale.NIDEC_ACCEL_PER_UNIT
    v = 45 * MPH
    assert cbd.friction_request(-2.0, v) == pytest.approx(2.0 / 3.6 - wind_brake(v))

  def test_compute_gb_brake_side_only(self):
    gas, brake = carcontroller.compute_gb_honda_nidec(-1.2, 20.0, 3.6)
    assert gas == 0.0 and brake == pytest.approx(1.2 / 3.6)
    assert carcontroller.compute_gb_honda_nidec(0.96, 20.0, 3.6) == (pytest.approx(0.2), 0.0)  # gas still /4.8
    assert carcontroller.compute_gb_honda_nidec(-1.2, 20.0) == (0.0, pytest.approx(0.25))  # default = stock
    assert carcontroller.compute_gb_honda_nidec(0.0, 0.0, 3.6)[1] == pytest.approx(0.15)  # creep brake unchanged
    assert carcontroller.compute_gb_honda_nidec(-4.0, 30.0, 3.6)[1] == 1.0  # clipped at 1 unit
    assert carcontroller.compute_gb_honda_nidec(-4.0, 30.0)[1] == pytest.approx(4.0 / 4.8)

  def test_compute_gas_brake_is_stock_for_every_car(self):
    # compute_gas_brake feeds the pedal and the PCM speed target: stock 4.8 on the 9G too
    for identity in (CAR.HONDA_ACCORD_9G, CAR.HONDA_CIVIC):
      cp = CarInterface.get_params(identity, gen_empty_fingerprint(), [], False, False, False)
      assert carcontroller.compute_gas_brake(-1.2, 20.0, cp) == (0.0, pytest.approx(0.25))


class TestAccord9G:
  @pytest.mark.parametrize("accel", [-0.6, -1.0, -2.0, -3.0])
  @pytest.mark.parametrize("v_mph", [20, 45, 65])
  def test_brake_command_is_accel_over_3_6(self, monkeypatch, accel, v_mph):
    v = v_mph * MPH
    brakes = run(monkeypatch, accel, v)[0]
    assert brakes[-1] == expected_counts(accel, v, 3.6)
    if brakes[-1] > 0:
      # decode back: units + hysteresis gap + wind = -accel / 3.6, within one count
      assert (brakes[-1] / 256 + 0.01 + wind_brake(v)) * 3.6 == pytest.approx(-accel, abs=3.6 / 256)
    assert brakes[-1] >= run(monkeypatch, accel, v, per_unit=4.8)[0][-1]

  @pytest.mark.parametrize("v_mph,stock,scaled", [(20, 202, 245), (53, 185, 228), (65, 179, 221)])
  def test_floor_request_uses_more_of_the_range(self, monkeypatch, v_mph, stock, scaled):
    # NIDEC_ACCEL_MIN -4.0: stock 4.8 gives 0.83 units minus wind; 3.6 saturates the 1-unit brake request
    v = v_mph * MPH
    assert run(monkeypatch, -4.0, v, per_unit=4.8)[0][-1] == stock
    assert run(monkeypatch, -4.0, v)[0][-1] == scaled
    assert expected_counts(-4.0, v, 3.6) == scaled

  def test_cap_stays_255(self, monkeypatch):
    for v in (0.5, 5.0, 30.0):
      brakes = run(monkeypatch, -10.0, v)[0]
      assert max(brakes) <= 255
    assert carcontroller.CarControllerParams.NIDEC_BRAKE_MAX == 256

  @pytest.mark.parametrize("accel", [-4.0, -2.0, -1.0, -0.6, -0.3, 0.0, 0.5, 1.5])
  def test_pedal_and_pcm_speed_unchanged(self, monkeypatch, accel):
    v = 50 * MPH
    _, gas, pcm, cc = run(monkeypatch, accel, v)
    _, gas_stock, pcm_stock, cc_stock = run(monkeypatch, accel, v, per_unit=4.8)
    assert cc.brake_accel_per_unit == 3.6 and cc_stock.brake_accel_per_unit == 4.8
    assert gas == gas_stock
    assert pcm == pcm_stock

  def test_no_pedal_9g_also_scaled_but_pcm_speed_unchanged(self, monkeypatch):
    v = 40 * MPH
    brakes, _, pcm, cc = run(monkeypatch, -2.0, v, pedal=False)
    assert cc.brake_accel_per_unit == 3.6
    _, _, pcm_stock, _ = run(monkeypatch, -2.0, v, pedal=False, per_unit=4.8)
    assert pcm == pcm_stock
    assert cc.CP.openpilotLongitudinalControl
    assert brakes[-1] == expected_counts(-2.0, v, 3.6)


class TestOtherHondas:
  @pytest.mark.parametrize("identity", [c for c in NIDEC_CARS if c != CAR.HONDA_ACCORD_9G])
  def test_other_nidec_keep_4_8(self, monkeypatch, identity):
    v = 45 * MPH
    brakes, _, _, cc = run(monkeypatch, -2.0, v, identity=identity, pedal=False, frames=150)
    assert cc.brake_accel_per_unit == 4.8
    assert brakes and brakes[-1] == expected_counts(-2.0, v, 4.8)

  def test_civic_pedal_keeps_4_8(self, monkeypatch):
    v = 45 * MPH
    brakes, _, _, cc = run(monkeypatch, -3.0, v, identity=CAR.HONDA_CIVIC, pedal=True)
    assert cc.brake_accel_per_unit == 4.8 and cc.cruise_brake_deadband is None
    assert brakes[-1] == expected_counts(-3.0, v, 4.8)

  def test_bosch_untouched(self):
    for identity in BOSCH_CARS:
      cp = CarInterface.get_params(identity, gen_empty_fingerprint(), [], False, False, False)
      assert CarInterface(cp).CC.brake_accel_per_unit == 4.8
