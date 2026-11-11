"""card.py feed of the Accord 9G cruise-hold brake deadband."""
from types import SimpleNamespace

from opendbc.car.honda import cruise_brake_deadband as cbd
from openpilot.starpilot.car.honda.cruise_brake_caller import STALE_NS, CruiseBrakeFeed

V65 = 65 * cbd.MPH
NOW = 10_000_000_000


class FakeSM(dict):
  def __init__(self, ok=True, age_ns=10_000_000, slc=True):
    lead = SimpleNamespace(status=False, dRel=100.0, vRel=0.0)
    super().__init__(longitudinalPlan=SimpleNamespace(aTarget=0.05, shouldStop=False, longitudinalPlanSource="cruise"),
                     radarState=SimpleNamespace(leadOne=lead, leadTwo=lead),
                     slcState=SimpleNamespace(hasCeiling=True, effectiveCap=25.0,
                                              curve=SimpleNamespace(applied=False, controlling=False)))
    names = ('longitudinalPlan', 'radarState', 'slcState')
    self.seen = {n: ok and (slc or n != 'slcState') for n in names}
    self.valid = dict(self.seen)
    self.alive = dict(self.seen)
    self.logMonoTime = {n: NOW - age_ns for n in names}
    self.updates = 0

  def update(self, timeout):
    self.updates += 1


class FakeParams:
  def __init__(self, value=True):
    self.value = value

  def get_bool(self, key):
    assert key == "AccordCruiseBrakeDeadband"
    return self.value


CS = SimpleNamespace(vEgo=V65, vCruise=110.0)


def test_fresh_inputs_feed_the_gate():
  gate = cbd.CruiseBrakeDeadband()
  CruiseBrakeFeed(gate, FakeParams(), FakeSM()).update(CS, NOW)
  assert gate.inputs_valid and gate.enabled
  assert gate.v_cruise == 25.0 and gate.a_target == 0.05 and gate.plan_source == "cruise"


def test_stale_invalid_or_disabled_is_stock():
  for sm, params in ((FakeSM(age_ns=STALE_NS + 1), FakeParams()), (FakeSM(ok=False), FakeParams()), (FakeSM(), FakeParams(False))):
    gate = cbd.CruiseBrakeDeadband()
    CruiseBrakeFeed(gate, params, sm).update(CS, NOW)
    assert not gate.inputs_valid or not gate.enabled
    gate.set_plan  # noqa: B018
    assert gate.update(True, V65, -0.8, 0.1, 0.02) is None


def test_missing_slc_uses_the_set_speed():
  gate = cbd.CruiseBrakeDeadband()
  CruiseBrakeFeed(gate, FakeParams(), FakeSM(slc=False)).update(CS, NOW)
  assert gate.inputs_valid and abs(gate.v_cruise - 110.0 / 3.6) < 1e-6
