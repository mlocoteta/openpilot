"""Accord 9G cruise-hold brake deadband (7.0 port of 6.x 66485e4a2)."""
import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda import carcontroller, cruise_brake_deadband as cbd
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.pedal_learner import WIND_FACTOR_HOLD
from opendbc.car.honda.values import CAR

MPH = cbd.MPH
V65 = 65 * MPH
DT = 0.02
CREATE_BRAKE_COMMAND = carcontroller.hondacan.create_brake_command


def gate(**plan):
  g = cbd.CruiseBrakeDeadband()
  kw = dict(v_cruise=V65, a_target=0.0, should_stop=False, plan_source="cruise", lead_brake=False, curve_active=False)
  kw.update(plan)
  g.set_plan(True, **kw)
  for _ in range(int(cbd.DEMAND_HOLD_S / DT) + 1):  # past the post-demand hold
    g.update(True, V65, 0.0, 0.0, DT)
  return g


class TestGate:
  def test_cruise_hold_holds_brake_off(self):
    g = gate()
    for v in (V65 - 1.0 * MPH, V65, V65 + 1.9 * MPH):
      assert g.update(True, v, -0.7, 0.05, DT) == 0.0
      assert g.suppressing
    assert g.held_frames == 3

  @pytest.mark.parametrize("plan", [dict(a_target=-0.35), dict(should_stop=True), dict(plan_source="lead0"),
                                    dict(plan_source="e2e"), dict(lead_brake=True), dict(curve_active=True),
                                    dict(enabled=False)])
  def test_real_demand_or_disabled_is_stock(self, plan):
    g = gate(**plan)
    assert g.update(True, V65, -0.7, 0.05, DT) is None
    assert not g.suppressing

  def test_hard_command_low_speed_invalid_or_not_pid_is_stock(self):
    assert gate().update(True, V65, cbd.ACCEL_CMD_MIN - 0.01, 0.3, DT) is None
    assert gate().update(True, cbd.MIN_SPEED - 0.1, -0.7, 0.05, DT) is None
    assert gate().update(False, V65, -0.7, 0.05, DT) is None
    g = cbd.CruiseBrakeDeadband()
    g.set_plan(False)
    assert g.update(True, V65, -0.7, 0.05, DT) is None
    for bad in (dict(v_cruise=float("nan")), dict(v_cruise=0.0), dict(a_target=float("inf"))):
      g.set_plan(True, **{**dict(v_cruise=V65, a_target=0.0), **bad})
      assert g.update(True, V65, -0.7, 0.05, DT) is None

  def test_brakes_return_immediately_when_demand_appears_and_stay_stock_after(self):
    g = gate()
    assert g.update(True, V65, -0.7, 0.05, DT) == 0.0
    g.set_plan(True, V65, -0.8)
    assert g.update(True, V65, -1.0, 0.2, DT) is None
    g.set_plan(True, V65, 0.0)  # demand gone (or the plan source flickered back to cruise)
    lims = [g.update(True, V65, -0.7, 0.05, DT) for _ in range(int(cbd.DEMAND_HOLD_S / DT) + 2)]
    assert all(lim is None for lim in lims[:-3]) and lims[-1] == 0.0

  def test_overspeed_ramps_brake_in_and_stays_stock_until_request_clears(self):
    g = gate()
    v = V65 + 2.1 * MPH
    lims = [g.update(True, v, -1.0, 0.2, DT) for _ in range(50)]  # 1 s
    assert lims[0] == pytest.approx(cbd.OVERSPEED_RAMP * DT)
    assert lims[-1] == pytest.approx(cbd.OVERSPEED_RAMP * 1.0)
    for _ in range(200):  # back inside the band but the brake is still needed (steep hill)
      assert g.update(True, V65 + 0.5 * MPH, -1.0, 0.1, DT) > 0.0
    lims = [g.update(True, V65 + 0.5 * MPH, -0.3, 0.0, DT) for _ in range(int(cbd.RELEASE_CLEAR_S / DT) + 2)]
    assert all(lim > 0.0 for lim in lims[:-3]) and lims[-1] == 0.0 and g.suppressing

  def test_leads(self):
    assert not cbd.lead_needs_brake(V65, False, 10.0, -10.0)
    assert not cbd.lead_needs_brake(V65, True, 100.0, 3.0)  # pulling away
    assert not cbd.lead_needs_brake(V65, True, 130.0, -0.2)  # far, holding
    assert not cbd.lead_needs_brake(V65, True, 105.0, -4.5)  # TTC 23 s
    assert cbd.lead_needs_brake(V65, True, 85.0, -4.5)  # TTC 19 s
    assert cbd.lead_needs_brake(V65, True, 28.0, 0.0)  # inside 1 s
    assert cbd.lead_needs_brake(V65, True, 25.0, 1.0)  # inside 1 s even if pulling away

  def test_actuator_mapping_matches_the_7_0_carcontroller(self):
    # friction onset: brake = -accel/4.8 exceeds wind_brake(v); pedal closes at 0.75 * WIND_FACTOR_HOLD * wind_brake
    assert cbd.PEDAL_WIND_FACTOR == WIND_FACTOR_HOLD
    gas, brake = carcontroller.compute_gb_honda_nidec(-0.7, V65)
    assert gas == 0.0 and brake == pytest.approx(0.7 / cbd.BRAKE_ACCEL_PER_UNIT)
    assert cbd.friction_request(-0.7, V65) == pytest.approx(brake - cbd.wind_brake(V65))
    assert cbd.friction_request(-4.8 * cbd.wind_brake(V65) + 0.01, V65) == 0.0
    close = cbd.pedal_close_accel(V65)
    assert -1.2 < close < -0.9
    assert cbd.pedal_close_accel(8.0) == cbd.I_FLOOR_MAX  # low speed: clipped


def plan(**kw):
  return dict(dict(v_cruise=V65, a_target=0.0, should_stop=False, plan_source="cruise", lead_brake=False,
                   curve_active=False), **kw)


class TestCarController:
  def _run(self, monkeypatch, accel, plan_kw, frames=400, v_ego=V65, identity=CAR.HONDA_ACCORD_9G, pedal=True):
    fp = gen_empty_fingerprint()
    if pedal:
      fp[0][0x201] = 6
    cp = CarInterface.get_params(identity, fp, [], False, False, False)
    ci = CarInterface(cp)
    ci.update([])
    brakes = []

    def capture(packer, CAN, apply_brake, *args):
      brakes.append(apply_brake)
      return CREATE_BRAKE_COMMAND(packer, CAN, apply_brake, *args)
    monkeypatch.setattr(carcontroller.hondacan, "create_brake_command", capture)
    command = structs.CarControl(enabled=True, longActive=True, latActive=False)
    command.actuators.accel = accel
    command.actuators.longControlState = "pid"
    command = command.as_reader()
    gases = []
    for tick in range(frames):
      ci.CS.out.vEgo = v_ego
      if plan_kw is not None and ci.CC.cruise_brake_deadband is not None:
        ci.CC.cruise_brake_deadband.set_plan(True, **plan_kw)
      ci.apply(command, 1_000_000_000 + tick * 10_000_000)
      gases.append(ci.CC.gas)
    return brakes, gases, ci.CC

  def test_only_9g_pedal_has_the_gate(self, monkeypatch):
    assert self._run(monkeypatch, 0.0, None, frames=1)[2].cruise_brake_deadband is not None
    assert self._run(monkeypatch, 0.0, None, frames=1, pedal=False)[2].cruise_brake_deadband is None
    assert self._run(monkeypatch, 0.0, None, frames=1, identity=CAR.HONDA_CIVIC)[2].cruise_brake_deadband is None

  def test_cruise_hold_brake_held_off_pedal_still_follows(self, monkeypatch):
    stock, stock_gas, _ = self._run(monkeypatch, -0.8, None)
    held, held_gas, cc = self._run(monkeypatch, -0.8, plan())
    assert min(stock[-50:]) > 0  # -0.8 at 65 mph is past the friction onset (-0.6)
    assert held[:40] == stock[:40]  # stock for DEMAND_HOLD_S after engage (100 brake frames at 50 Hz)
    assert max(held[-50:]) == 0
    assert held_gas == pytest.approx(stock_gas)  # pedal command unchanged
    assert cc.cruise_brake_deadband.held_frames > 0

  def test_real_demand_or_disabled_brakes_like_stock(self, monkeypatch):
    stock, _, _ = self._run(monkeypatch, -1.2, None)
    for kw in (dict(a_target=-1.0), dict(enabled=False), dict(plan_source="lead0")):
      demand, _, _ = self._run(monkeypatch, -1.2, plan(**kw))
      assert demand == stock and max(demand) > 0

  def test_no_plan_is_stock(self, monkeypatch):
    stock, gas, _ = self._run(monkeypatch, -0.8, None)
    g = cbd.CruiseBrakeDeadband()
    assert not g.inputs_valid and g.update(True, V65, -0.8, 0.1, DT) is None
    assert max(stock) > 0


class _Lead:
  def __init__(self, status=False, d=100.0, v=0.0):
    self.status, self.dRel, self.vRel = status, d, v


class _Curve:
  def __init__(self, applied=False, controlling=False):
    self.applied, self.controlling = applied, controlling


class _Slc:
  def __init__(self, cap=0.0, has=False, curve=None):
    self.hasCeiling, self.effectiveCap, self.curve = has, cap, curve or _Curve()


class _Plan:
  def __init__(self, a=0.0, stop=False, source="cruise"):
    self.aTarget, self.shouldStop, self.longitudinalPlanSource = a, stop, source


class _Radar:
  def __init__(self, one=None, two=None):
    self.leadOne, self.leadTwo = one or _Lead(), two or _Lead()


def test_plan_inputs():
  p = cbd.plan_inputs(V65, 105.0, _Plan(), _Radar(), None)
  assert p == dict(v_cruise=pytest.approx(105.0 / 3.6), a_target=0.0, should_stop=False, plan_source="cruise",
                   lead_brake=False, curve_active=False)
  assert cbd.plan_inputs(V65, 105.0, _Plan(), _Radar(), _Slc(25.0, True))["v_cruise"] == 25.0
  assert cbd.plan_inputs(V65, 105.0, _Plan(), _Radar(), _Slc(40.0, True))["v_cruise"] == pytest.approx(105.0 / 3.6)
  assert cbd.plan_inputs(V65, 105.0, _Plan(), _Radar(), _Slc(curve=_Curve(controlling=True)))["curve_active"]
  assert cbd.plan_inputs(V65, 105.0, _Plan(), _Radar(two=_Lead(True, 20.0, 0.0)), None)["lead_brake"]


def test_eligible_only_on_the_9g_pedal_car():
  def cp(identity, pedal):
    fp = gen_empty_fingerprint()
    if pedal:
      fp[0][0x201] = 6
    return CarInterface.get_params(identity, fp, [], False, False, False)
  assert cbd.eligible(cp(CAR.HONDA_ACCORD_9G, True))
  assert not cbd.eligible(cp(CAR.HONDA_ACCORD_9G, False))
  assert not cbd.eligible(cp(CAR.HONDA_CIVIC, True))
  assert not cbd.eligible(cp(CAR.HONDA_ACCORD, False))
