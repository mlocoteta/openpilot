from types import SimpleNamespace

import pytest

from opendbc.car.subaru.avh import AVH_REQUEST, AVH_STATUS, INPUTS, AvhStartup, avh_request, checksum
from opendbc.car.subaru.carcontroller import CarController
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR, SubaruSafetyFlags
from opendbc.car import Bus


def sample(address, counter):
  data = bytearray(8)
  data[1] = counter & 15
  if address == AVH_REQUEST:
    data[3], data[5], data[6] = 1, 0x80, 0x0E  # captured Legacy payload, not Outback constants
  elif address == 0x40:
    data[2:4] = (800).to_bytes(2, 'little')
  elif address == 0x48:
    data[3] = 4
  elif address == 0x174:
    data[2] = 8
  data[0] = checksum(address, data)
  return bytes(data)


def prepare(fast_counter_step=1):
  policy = AvhStartup()
  frames = {}
  for tick in range(101):
    now = 100 + tick / 10
    for address in INPUTS:
      if address != AVH_REQUEST or tick % 10 == 0:
        counter = tick // 10 if address == AVH_REQUEST else tick * (1 if address == AVH_STATUS else fast_counter_step)
        frames[address] = (now, sample(address, counter))
    sent = policy.update(now, frames, True, True, False)
    if tick < 100:
      assert sent == []
  assert sent == [avh_request(frames[AVH_REQUEST][1], 1)]
  return policy, frames


def test_captured_legacy_press_bytes():
  template = bytes.fromhex('5b0b000100800e00')
  assert avh_request(template, 1) == (0x6BB, bytes.fromhex('5e0c020100800e00'), 1)
  assert avh_request(template, 2) == (0x6BB, bytes.fromhex('5f0d020100800e00'), 1)
  wrap = sample(AVH_REQUEST, 15)
  assert avh_request(wrap, 1)[1][1] == 0
  assert avh_request(wrap, 2)[1][1] == 1


def test_two_frames_only_and_no_retry():
  policy, frames = prepare()
  assert policy.update(110.04, frames, True, True, False) == []
  assert policy.update(110.06, frames, True, True, False) == [avh_request(frames[AVH_REQUEST][1], 2)]
  assert policy.update(110.07, frames, True, True, False) == []
  assert policy.update(111, frames, True, True, False) == []


def test_controller_snapshots_may_skip_fast_can_samples():
  policy, frames = prepare(fast_counter_step=2)
  assert policy.update(110.06, frames, True, True, False) == [avh_request(frames[AVH_REQUEST][1], 2)]


@pytest.mark.parametrize('reason', ['late', 'new_template', 'manual', 'ack', 'moving', 'gas', 'gear', 'invalid', 'disabled', 'engaged', 'stale'])
def test_followup_aborts_permanently(reason):
  policy, frames = prepare()
  address, offset, value = {
    'manual': (AVH_REQUEST, 2, 1), 'ack': (AVH_STATUS, 5, 32),
    'moving': (0x13A, 2, 1), 'gas': (0x40, 4, 1), 'gear': (0x48, 3, 3),
    'new_template': (AVH_REQUEST, 1, 11),
  }.get(reason, (None, None, None))
  if address is not None:
    data = bytearray(frames[address][1])
    data[1] = (data[1] + 1) & 15
    data[offset] = value
    data[0] = checksum(address, data)
    frames[address] = (110.05, bytes(data))
  if reason == 'stale':
    frames[0x40] = (109, frames[0x40][1])
  now = 110.08 if reason == 'late' else 110.06
  assert policy.update(now, frames, reason != 'disabled', reason != 'invalid', reason == 'engaged') == []
  assert policy.done
  assert policy.update(111, frames, True, True, False) == []


def test_only_legacy_has_avh_safety_permission():
  for car in CAR:
    cp = CarInterface.get_non_essential_params(car)
    assert bool(cp.safetyConfigs[0].safetyParam & SubaruSafetyFlags.AVH_STARTUP) == (car == CAR.SUBARU_LEGACY_2025)


def test_existing_required_messages_keep_alive_checks():
  cp = CarInterface.get_non_essential_params(CAR.SUBARU_LEGACY_2025)
  parser = CarInterface.CarState.get_can_parsers(cp)[Bus.alt]
  assert not parser.message_states[0x13A].ignore_alive
  assert not parser.message_states[0x174].ignore_alive
  assert parser.message_states[AVH_REQUEST].ignore_alive
  assert parser.message_states[AVH_STATUS].ignore_alive


def test_controller_sends_only_when_opted_in():
  cp = CarInterface.get_non_essential_params(CAR.SUBARU_LEGACY_2025)
  controller = CarController({}, cp)
  cc = SimpleNamespace(enabled=False, latActive=False, longActive=False,
                       actuators=SimpleNamespace(as_builder=lambda: SimpleNamespace(steeringAngleDeg=0)),
                       hudControl=SimpleNamespace(leadVisible=False), cruiseControl=SimpleNamespace(cancel=False))
  cs = SimpleNamespace(out=SimpleNamespace(canValid=True), avh_frames={})
  toggles = SimpleNamespace(subaru_stop_start_off=False, subaru_avh_on=False, subaru_sng=False)
  controller.frame = 1
  _, sent = controller.update(cc, cs, 100_000_000_000, toggles)
  assert not any(m[0] in (AVH_REQUEST, AVH_STATUS) for m in sent)
