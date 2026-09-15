import pytest

from opendbc.can import CANPacker
from opendbc.car import create_gas_interceptor_command
from opendbc.car.structs import CarParams
from opendbc.safety.tests.libsafety import libsafety_py


@pytest.mark.parametrize("param", [0x9405, 0x9C05, 0x9401, 0x1005, 0])
def test_ray_pedal_tx_isolation_and_limits(param):
  safety = libsafety_py.libsafety
  safety.set_safety_hooks(CarParams.SafetyModel.hyundai, param)
  safety.init_tests()
  safety.set_controls_allowed(True)
  packer = CANPacker("hyundai_kia_ray_pedal")

  def tx(gas):
    addr, dat, bus = create_gas_interceptor_command(packer, gas, 3)
    return safety.safety_tx_hook(libsafety_py.make_CANPacket(addr, bus, dat))

  has_ray_signature = param in (0x9405, 0x9C05)
  assert tx(0) is has_ray_signature
  assert tx(0.35) is has_ray_signature
  assert not tx(0.36)  # above the Ray-only initial command cap
  assert not tx(1.0)

  if has_ray_signature:
    safety.set_controls_allowed(False)
    assert tx(0)
    assert not tx(0.1)
    safety.set_controls_allowed(True)
    safety.set_gas_pressed_prev(True)
    assert not tx(0.1)
    safety.set_gas_pressed_prev(False)
    addr, dat, bus = create_gas_interceptor_command(packer, 0.1, 3)
    bad_crc = bytearray(dat)
    bad_crc[-1] ^= 1
    assert not safety.safety_tx_hook(libsafety_py.make_CANPacket(addr, bus, bytes(bad_crc)))


def test_ray_pedal_rx_crc_is_checked_only_for_ray_signature():
  safety = libsafety_py.libsafety
  safety.set_safety_hooks(CarParams.SafetyModel.hyundai, 0x9405)
  safety.init_tests()
  dat = bytes.fromhex("01f403d55de8")
  assert safety.safety_rx_hook(libsafety_py.make_CANPacket(0x201, 0, dat))
  bad_crc = bytearray(dat)
  bad_crc[-1] ^= 1
  assert not safety.safety_rx_hook(libsafety_py.make_CANPacket(0x201, 0, bytes(bad_crc)))
