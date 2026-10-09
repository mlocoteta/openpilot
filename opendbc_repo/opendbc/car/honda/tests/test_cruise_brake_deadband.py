import pytest

from opendbc.car import structs
from opendbc.car.honda import carcontroller, cruise_brake_deadband as cbd
from opendbc.car.honda.tests.test_honda_ti import DT_NS, pedal_interface

MPH = cbd.MPH
V65 = 65 * MPH
DT = 0.02
CREATE_BRAKE_COMMAND = carcontroller.hondacan.create_brake_command


@pytest.fixture(autouse=True)
def no_kill_file(monkeypatch, tmp_path):
  monkeypatch.setattr(cbd, "KILL_FILE", str(tmp_path / "cruise_brake_deadband_disabled"))
  monkeypatch.setitem(cbd._kill_cache, "frame", 0)


def gate(**plan):
  g = cbd.CruiseBrakeDeadband()
  kw = dict(v_cruise=V65, a_target=0.0, should_stop=False, plan_source="cruise", lead_brake=False, csc_active=False)
  kw.update(plan)
  g.set_plan(True, **kw)
  return g


class TestGate:
  def test_cruise_hold_holds_brake_off(self):
    g = gate()
    for v in (V65 - 1.0 * MPH, V65, V65 + 1.9 * MPH):
      assert g.update(True, v, -0.4, 0.05, DT) == 0.0
      assert g.suppressing

  @pytest.mark.parametrize("plan", [dict(a_target=-0.6), dict(should_stop=True), dict(plan_source="lead0"),
                                    dict(plan_source="e2e"), dict(lead_brake=True), dict(csc_active=True)])
  def test_real_demand_is_stock(self, plan):
    g = gate(**plan)
    assert g.update(True, V65, -0.4, 0.05, DT) is None
    assert not g.suppressing

  def test_hard_command_low_speed_invalid_or_not_pid_is_stock(self):
    assert gate().update(True, V65, cbd.ACCEL_CMD_MIN - 0.01, 0.3, DT) is None
    assert gate().update(True, cbd.MIN_SPEED - 0.1, -0.4, 0.05, DT) is None
    assert gate().update(False, V65, -0.4, 0.05, DT) is None
    g = cbd.CruiseBrakeDeadband()
    g.set_plan(False)
    assert g.update(True, V65, -0.4, 0.05, DT) is None
    g.set_plan(True, float("nan"), 0.0)
    assert g.update(True, V65, -0.4, 0.05, DT) is None

  def test_brakes_return_immediately_when_demand_appears(self):
    g = gate()
    assert g.update(True, V65, -0.4, 0.05, DT) == 0.0
    g.set_plan(True, V65, -0.8)
    assert g.update(True, V65, -1.0, 0.2, DT) is None

  def test_overspeed_ramps_brake_in_and_stays_stock_until_request_clears(self):
    g = gate()
    v = V65 + 2.1 * MPH
    lims = [g.update(True, v, -1.0, 0.2, DT) for _ in range(50)]  # 1 s
    assert lims[0] == pytest.approx(cbd.OVERSPEED_RAMP * DT)
    assert lims[-1] == pytest.approx(cbd.OVERSPEED_RAMP * 1.0)
    # back inside the band but the brake is still needed (steep hill): stay stock-ish, no re-suppress
    for _ in range(200):
      assert g.update(True, V65 + 0.5 * MPH, -1.0, 0.1, DT) > 0.0
    # stock request 0 inside the re-arm band for RELEASE_CLEAR_S -> hold off again
    lims = [g.update(True, V65 + 0.5 * MPH, -0.3, 0.0, DT) for _ in range(int(cbd.RELEASE_CLEAR_S / DT) + 2)]
    assert all(lim > 0.0 for lim in lims[:-3]) and lims[-1] == 0.0 and g.suppressing

  def test_kill_file(self, tmp_path):
    (tmp_path / "cruise_brake_deadband_disabled").touch()
    cbd._kill_cache["frame"] = 0
    assert gate().update(True, V65, -0.4, 0.05, DT) is None

  def test_leads(self):
    assert not cbd.lead_needs_brake(V65, False, 10.0, -10.0)
    assert not cbd.lead_needs_brake(V65, True, 100.0, 3.0)  # pulling away
    assert not cbd.lead_needs_brake(V65, True, 60.0, -5.0)  # TTC 12 s
    assert cbd.lead_needs_brake(V65, True, 60.0, -8.0)  # TTC 7.5 s
    assert cbd.lead_needs_brake(V65, True, 25.0, 1.0)  # inside 1 s

  def test_pedal_close_accel(self):
    assert cbd.pedal_close_accel(V65) == pytest.approx(-0.75 * 5.0 * carcontroller.get_honda_bosch_wind_brake_mps2(V65))
    assert cbd.wind_brake_mps2(V65) == carcontroller.get_honda_bosch_wind_brake_mps2(V65)
    assert cbd.ACCORD_9G_BRAKE_ACCEL_PER_UNIT == carcontroller.ACCORD_9G_BRAKE_ACCEL_PER_UNIT
    assert cbd.pedal_close_accel(12.0) == cbd.I_FLOOR_MAX


class TestCarController:
  def _run(self, monkeypatch, accel, plan, frames=60, v_ego=V65):
    CI, toggles = pedal_interface(monkeypatch, True)
    brakes = []

    def capture(packer, CAN, apply_brake, *args):
      brakes.append(apply_brake)
      return CREATE_BRAKE_COMMAND(packer, CAN, apply_brake, *args)
    monkeypatch.setattr(carcontroller.hondacan, "create_brake_command", capture)
    CC = structs.CarControl()
    CC.enabled = CC.longActive = True
    CC.actuators.accel = accel
    CC.actuators.longControlState = structs.CarControl.Actuators.LongControlState.pid
    CC = CC.as_reader()
    gases = []
    for frame in range(frames):
      CI.update([(frame * DT_NS, [])], toggles)
      CI.CS.out.vEgo = v_ego
      if plan is not None:
        CI.CC.cruise_brake_deadband.set_plan(True, **plan)
      CI.apply(CC, frame * DT_NS, toggles)
      gases.append(CI.CC.gas)
    return brakes, gases, CI.CC

  def test_only_9g_pedal_has_the_gate(self, monkeypatch):
    assert pedal_interface(monkeypatch, True)[0].CC.cruise_brake_deadband is not None
    assert pedal_interface(monkeypatch, False)[0].CC.cruise_brake_deadband is None

  def test_cruise_hold_brake_held_off_pedal_still_follows(self, monkeypatch):
    stock, stock_gas, _ = self._run(monkeypatch, -0.5, None)
    held, held_gas, _ = self._run(monkeypatch, -0.5, dict(v_cruise=V65, a_target=0.0))
    assert max(stock) > 0  # -0.5 at 65 mph is past the friction onset
    assert max(held) == 0
    assert held_gas[-1] == pytest.approx(stock_gas[-1])  # pedal command unchanged

  def test_real_demand_brakes_like_stock(self, monkeypatch):
    stock, _, _ = self._run(monkeypatch, -1.2, None)
    demand, _, _ = self._run(monkeypatch, -1.2, dict(v_cruise=V65, a_target=-1.0))
    assert demand == stock and max(demand) > 0
