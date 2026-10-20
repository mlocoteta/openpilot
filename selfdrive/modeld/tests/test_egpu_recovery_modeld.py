from types import SimpleNamespace

from cereal import car
from openpilot.selfdrive.modeld import modeld


class FakeSM(dict):
  def __init__(self, cs, cc, alive=True):
    super().__init__(carState=cs, carControl=cc)
    self.seen = {"carState": True, "carControl": True}
    self.alive = {"carState": alive, "carControl": alive}


def test_car_inputs_mapping():
  cs = SimpleNamespace(vEgo=0.0, standstill=True, brakePressed=True, gearShifter=car.CarState.GearShifter.drive)
  cc = SimpleNamespace(enabled=False, latActive=True, longActive=False)
  inputs = modeld._egpu_recovery_car_inputs(FakeSM(cs, cc))
  assert inputs.valid and inputs.standstill and inputs.brake_pressed and inputs.lat_active and not inputs.in_park
  assert modeld.EgpuRecovery.safe_moment(inputs) == "standstill"
  assert not modeld._egpu_recovery_car_inputs(FakeSM(cs, cc, alive=False)).valid
  cs.gearShifter = car.CarState.GearShifter.park
  assert modeld._egpu_recovery_car_inputs(FakeSM(cs, cc)).in_park


def test_supply_uses_published_value_then_direct_read(monkeypatch):
  state = modeld.ChestnutState(None, False)
  reads = []
  monkeypatch.setattr(state, "_read_ina", lambda: reads.append(1) or (13900, 1400, False))
  state.last_supply_mv, state.last_supply_t = 120, 100.0
  assert state.supply_mv(101.0) == 120 and reads == []
  assert state.supply_mv(103.0) == 13900 and reads == [1]


def test_supply_read_failure_is_none(monkeypatch):
  state = modeld.ChestnutState(None, False)
  def fail():
    raise OSError("no device")
  monkeypatch.setattr(state, "_read_ina", fail)
  assert state.supply_mv(5.0) is None
