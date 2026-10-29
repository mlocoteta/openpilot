"""Physical MAIN intent for exactly Crosstrek AOL; no ordinary controls grant."""
import pytest

from opendbc.safety.tests.libsafety import libsafety_py
from opendbc.safety.tests import test_subaru_stock_aol as stock_module


@pytest.fixture
def owner():
  item = stock_module.TestSubaruStockAol(methodName='runTest')
  item.setUp()
  item.configure(17)
  try:
    yield item
  finally:
    item.tearDown()


def neutral(item, **kwargs):
  for _ in range(12):
    assert item.feed(main=False, **kwargs) == 0


def test_physical_main_without_set_grants_only_fresh_lateral(owner):
  neutral(owner)
  assert owner.feed() == 1
  assert not owner.safety.get_controls_allowed()
  owner.safety.aol_set_host_request(3)
  assert owner.safety.aol_get_permission_mask() == 1
  assert owner.feed(brake=True) == 1
  assert owner.feed(gear=3) == 0
  assert owner.feed(gear=121) == 1
  assert owner.feed(main=False) == 0


def test_main_held_at_startup_cannot_invent_a_driver_gesture(owner):
  for _ in range(20):
    assert owner.feed() == 0
  assert not owner.safety.get_controls_allowed()


def test_main_can_record_stopped_intent_but_waits_for_moving_request(owner):
  neutral(owner, speed=0, host_mask=0)
  assert owner.feed(speed=0, host_mask=0) == 0
  for _ in range(30):
    assert owner.feed(speed=0, host_mask=0) == 0
  assert owner.feed(speed=54, host_mask=1) == 1
  assert not owner.safety.get_controls_allowed()


@pytest.mark.parametrize('fault', ('permanent', 'acc_fault'))
def test_fault_clear_with_main_held_cannot_rearm(owner, fault):
  neutral(owner)
  assert owner.feed() == 1
  assert owner.feed(**{fault: True}) == 0
  for _ in range(10):
    assert owner.feed() == 0
  assert owner.feed(main=False) == 0
  assert owner.feed() == 1


def test_new_physical_acc_source_is_required_before_main_edge(owner):
  neutral(owner, omit_distance=True)
  assert owner.feed(omit_distance=True) == 0
  for _ in range(20):
    assert owner.feed() == 0
  assert owner.feed(main=False) == 0
  assert owner.feed() == 1


def test_acc_wire_checksum_and_counter_cannot_be_faked_by_host(owner):
  neutral(owner)
  assert owner.feed() == 1
  bad = owner.frame('ES_Distance', {}, 1)
  raw = bytearray(bytes(bad.data))
  raw[0] ^= 1
  assert not owner.safety.safety_rx_hook(libsafety_py.make_CANPacket(0x221, 1, bytes(raw[:8])))
  assert owner.safety.aol_get_permission_mask() == 0


def test_heartbeat_and_host_lease_still_withdraw(owner):
  neutral(owner)
  assert owner.feed() == 1
  owner.safety.set_aol_test_heartbeat(False)
  assert owner.safety.aol_get_permission_mask() == 0
  owner.safety.set_aol_test_heartbeat(True)
  assert owner.feed() == 0
  assert owner.feed(main=False) == 0
  assert owner.feed() == 1
  owner.safety.set_timer(owner.now + 301_000)
  assert owner.safety.aol_get_permission_mask() == 0


def test_acc_fault_cannot_be_bypassed_by_stock_enable_packets(owner):
  neutral(owner)
  assert owner.feed() == 1
  assert owner.feed(acc_fault=True) == 0
  for enabled in (0, 1):
    assert owner.safety.safety_rx_hook(owner.frame('ES_Status', {'Cruise_Activated': enabled}, 1))
    owner.safety.aol_set_host_request(1)
    assert owner.safety.aol_get_permission_mask() == 0
