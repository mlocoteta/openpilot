"""A fresh physical MAIN waits for its own current fault observation."""
from types import SimpleNamespace

from opendbc.car import structs
from openpilot.starpilot.aol.intent import AolSettings
from openpilot.starpilot.car.subaru.aol import SubaruStockCardIntent


def state():
  cs = structs.CarState(canValid=True, gearShifter=structs.CarState.GearShifter.drive)
  cs.cruiseState.available = False
  return cs


def observe(owner, cs, now, event, fault):
  sm = SimpleNamespace(logMonoTime={'onroadEvents': event}, valid={'onroadEvents': True})
  owner.observe_startup_readiness(sm, cs, now_ns=now)
  owner.update(cs, now_ns=now, fault_active=fault)


def owner():
  return SubaruStockCardIntent(AolSettings(True, 0., 0, 0, (0, 0, 0), (0, 0, 0)), main_arm=True)


def test_main_waits_for_post_edge_observation_and_allows_stopped_intent():
  intent, cs = owner(), state()
  cs.standstill = cs.brakePressed = True
  observe(intent, cs, 1_000_000, 1_000_000, True)
  cs.cruiseState.available = True
  observe(intent, cs, 10_000_000, 1_000_000, True)
  assert not intent.allowed_latch
  observe(intent, cs, 20_000_000, 10_000_000, False)
  assert intent.allowed_latch
  assert not cs.cruiseState.enabled


def test_new_post_main_fault_consumes_gesture_without_rearming_when_it_clears():
  intent, cs = owner(), state()
  observe(intent, cs, 1_000_000, 1_000_000, False)
  cs.cruiseState.available = True
  observe(intent, cs, 10_000_000, 1_000_000, False)
  observe(intent, cs, 20_000_000, 10_000_000, True)
  observe(intent, cs, 30_000_000, 20_000_000, False)
  assert not intent.allowed_latch


def test_expired_main_edge_and_startup_held_main_cannot_arm():
  intent, cs = owner(), state()
  cs.cruiseState.available = True
  observe(intent, cs, 1_000_000, 1_000_000, False)
  assert not intent.allowed_latch
  cs.cruiseState.available = False
  observe(intent, cs, 2_000_000, 2_000_000, False)
  cs.cruiseState.available = True
  observe(intent, cs, 10_000_000, 2_000_000, False)
  observe(intent, cs, 211_000_000, 2_000_000, False)
  observe(intent, cs, 220_000_000, 220_000_000, False)
  assert not intent.allowed_latch


def test_physical_acc_fault_cancels_pending_main_edge():
  intent, cs = owner(), state()
  observe(intent, cs, 1_000_000, 1_000_000, False)
  cs.cruiseState.available = True
  observe(intent, cs, 10_000_000, 1_000_000, False)
  cs.accFaulted = True
  observe(intent, cs, 20_000_000, 10_000_000, False)
  cs.accFaulted = False
  observe(intent, cs, 30_000_000, 20_000_000, False)
  assert not intent.allowed_latch
