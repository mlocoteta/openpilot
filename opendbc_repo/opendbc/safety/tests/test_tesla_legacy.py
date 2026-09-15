import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus
from opendbc.car.tesla.teslacan_legacy import TeslaCANRaven
from opendbc.car.tesla.values import CANBUS, CAR, DBC, TeslaSafetyFlags
from opendbc.safety.tests.libsafety import libsafety_py


@pytest.fixture
def legacy_safety():
  safety = libsafety_py.libsafety
  packer = CANPacker(DBC[CAR.TESLA_MODEL_S_HW1][Bus.pt])
  return safety, TeslaCANRaven({CANBUS.party: packer})


def tx(safety, msg):
  addr, data, bus = msg
  return safety.safety_tx_hook(libsafety_py.make_CANPacket(addr, bus, data))


def test_hw1_steering_requires_controls_allowed(legacy_safety):
  safety, can = legacy_safety
  safety.set_safety_hooks(10, TeslaSafetyFlags.FLAG_HW1.value)
  safety.init_tests()
  safety.set_angle_meas(0, 0)
  safety.set_controls_allowed(False)
  assert tx(safety, can.create_steering_control(0, 0, False))
  assert not tx(safety, can.create_steering_control(0, 0, True))
  safety.set_controls_allowed(True)
  assert tx(safety, can.create_steering_control(0, 0, True))


@pytest.mark.parametrize("alpha_long", [False, True])
def test_hw1_accel_only_allowed_with_alpha_long_and_engagement(legacy_safety, alpha_long):
  safety, can = legacy_safety
  param = TeslaSafetyFlags.FLAG_HW1.value | (TeslaSafetyFlags.LONG_CONTROL.value if alpha_long else 0)
  safety.set_safety_hooks(10, param)
  safety.init_tests()
  safety.set_controls_allowed(True)
  assert tx(safety, can.create_longitudinal_command(13, 0, 0, 10, False, False))
  assert tx(safety, can.create_longitudinal_command(4, 1, 0, 10, True, False)) == alpha_long
  safety.set_controls_allowed(False)
  assert not tx(safety, can.create_longitudinal_command(4, 1, 0, 10, True, False))


def test_hw1_stock_ap_steer_and_acc_are_blocked_from_forwarding(legacy_safety):
  safety, _ = legacy_safety
  safety.set_safety_hooks(10, TeslaSafetyFlags.FLAG_HW1.value)
  safety.init_tests()
  assert safety.safety_fwd_hook(2, 0x488) == -1
  assert safety.safety_fwd_hook(2, 0x2b9) == -1
  assert safety.safety_fwd_hook(2, 0x370) == 0


def test_hw1_flag_dispatch_does_not_change_modern_or_preap_hooks(legacy_safety):
  safety, can = legacy_safety
  steer = can.create_steering_control(0, 0, False)
  safety.set_safety_hooks(10, TeslaSafetyFlags.FLAG_HW1.value)
  safety.init_tests()
  assert tx(safety, steer)

  # APS monitor exists only in the modern Tesla TX whitelist; HW1 must not
  # accidentally inherit it from the unflagged hook.
  monitor = libsafety_py.make_CANPacket(0x27d, 0, bytes(3))
  assert not safety.safety_tx_hook(monitor)
  safety.set_safety_hooks(10, 0)
  safety.init_tests()
  assert safety.safety_tx_hook(monitor)

  safety.set_safety_hooks(35, 0)
  safety.init_tests()
  assert safety.safety_fwd_hook(2, 0x370) == -1
