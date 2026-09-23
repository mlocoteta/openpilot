import pytest

from opendbc.car.structs import CarParams
from opendbc.car.subaru.avh import AVH_REQUEST, AVH_STATUS, INPUTS, avh_request, checksum
from opendbc.car.subaru.tests.test_avh import sample
from opendbc.car.subaru.values import SubaruSafetyFlags
from opendbc.safety.tests.libsafety import libsafety_py

FLAGS = int(SubaruSafetyFlags.GEN2 | SubaruSafetyFlags.LKAS_ANGLE | SubaruSafetyFlags.FIXED_ANGLE_LIMITS |
            SubaruSafetyFlags.STOP_START_BUTTON | SubaruSafetyFlags.AVH_STARTUP)


def packet(address, data, bus=1):
  return libsafety_py.make_CANPacket(address, bus, data)


@pytest.fixture
def safety():
  s = libsafety_py.libsafety
  s.set_timer(0)
  assert s.set_safety_hooks(CarParams.SafetyModel.subaru, FLAGS) == 0
  s.set_controls_allowed(False)
  for tick in range(101):
    s.set_timer(tick * 100_000)
    for address in INPUTS:
      if address != AVH_REQUEST or tick % 10 == 0:
        assert s.safety_rx_hook(packet(address, sample(address, tick // 10 if address == AVH_REQUEST else tick)))
  return s


def request(step=1):
  return avh_request(sample(AVH_REQUEST, 10), step)[1]


def test_pair_and_third_frame_blocked(safety):
  assert safety.safety_tx_hook(packet(AVH_REQUEST, request()))
  safety.set_timer(10_050_000)
  assert safety.safety_tx_hook(packet(AVH_REQUEST, request(2)))
  safety.set_timer(10_100_000)
  assert not safety.safety_tx_hook(packet(AVH_REQUEST, request(2)))


@pytest.mark.parametrize('byte', range(8))
def test_payload_mutation_blocked(safety, byte):
  data = bytearray(request())
  data[byte] ^= 4
  if byte:
    data[0] = checksum(AVH_REQUEST, data)
  assert not safety.safety_tx_hook(packet(AVH_REQUEST, data))


@pytest.mark.parametrize('bus', [0, 2])
def test_wrong_bus_blocked(safety, bus):
  assert not safety.safety_tx_hook(packet(AVH_REQUEST, request(), bus))


@pytest.mark.parametrize('delay', [44_999, 80_001])
def test_followup_timing(safety, delay):
  assert safety.safety_tx_hook(packet(AVH_REQUEST, request()))
  safety.set_timer(10_000_000 + delay)
  assert not safety.safety_tx_hook(packet(AVH_REQUEST, request(2)))


@pytest.mark.parametrize('address,offset,value', [(AVH_REQUEST, 2, 1), (AVH_STATUS, 5, 32),
                                                (0x40, 4, 1), (0x48, 3, 3), (0x13A, 2, 1)])
def test_abort_on_manual_ack_or_movement(safety, address, offset, value):
  assert safety.safety_tx_hook(packet(AVH_REQUEST, request()))
  safety.set_timer(10_050_000)
  data = bytearray(sample(address, 11 if address == AVH_REQUEST else 101))
  data[offset] = value
  data[0] = checksum(address, data)
  assert safety.safety_rx_hook(packet(address, data))
  assert not safety.safety_tx_hook(packet(AVH_REQUEST, request(2)))


def test_stale_template_and_status_tx_blocked(safety):
  assert not safety.safety_tx_hook(packet(AVH_STATUS, sample(AVH_STATUS, 1)))
  safety.set_timer(10_030_001)
  assert not safety.safety_tx_hook(packet(AVH_REQUEST, request()))


@pytest.mark.parametrize('flags', [FLAGS & ~1024, FLAGS | 32, FLAGS | 2, FLAGS & ~16, FLAGS | 512])
def test_permission_gates(safety, flags):
  assert safety.set_safety_hooks(CarParams.SafetyModel.subaru, flags) == 0
  assert not safety.safety_tx_hook(packet(AVH_REQUEST, request()))


@pytest.mark.parametrize('reason', ['new_template', 'corrupt', 'engaged', 'expired', 'duplicate'])
def test_extra_failure_gates(safety, reason):
  if reason == 'engaged':
    safety.set_controls_allowed(True)
  elif reason == 'expired':
    safety.set_timer(30_000_001)
  elif reason == 'duplicate':
    safety.set_timer(10_040_000)
    assert safety.safety_rx_hook(packet(AVH_REQUEST, sample(AVH_REQUEST, 10)))
  elif reason == 'corrupt':
    data = bytearray(sample(AVH_REQUEST, 11))
    data[0] ^= 1
    safety.safety_rx_hook(packet(AVH_REQUEST, data))
  else:
    assert safety.safety_tx_hook(packet(AVH_REQUEST, request()))
    safety.set_timer(10_050_000)
    assert safety.safety_rx_hook(packet(AVH_REQUEST, sample(AVH_REQUEST, 11)))
    assert not safety.safety_tx_hook(packet(AVH_REQUEST, request(2)))
    return
  assert not safety.safety_tx_hook(packet(AVH_REQUEST, request()))
