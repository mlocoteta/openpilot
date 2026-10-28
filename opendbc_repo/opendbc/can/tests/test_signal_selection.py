import pytest

from opendbc.can import CANPacker, CANParser
from opendbc.can.tests import TEST_DBC


@pytest.mark.parametrize('dbc,message,field', [
  (TEST_DBC, 'CAN_FD_MESSAGE', 'SIGNED'),
  ('honda_civic_touring_2016_can_generated', 'STEERING_CONTROL', 'STEER_TORQUE'),
])
def test_selected_values_preserve_integrity_and_freshness(dbc, message, field):
  full = CANParser(dbc, [(message, 100)], 0)
  selected = CANParser(dbc, [(message, 100)], 0, signals={message: [field]})
  packer = CANPacker(dbc)
  frames = [packer.make_can_msg(message, 0, {field: 12}) for _ in range(12)]
  frames += [frames[-1]] * 8  # Repeated counters must still fail.
  damaged = bytearray(frames[-1][1])
  damaged[0] ^= 0x80
  frames += [(frames[-1][0], bytes(damaged), 0)] * 8
  for index, frame in enumerate(frames):
    sample = [(1_000_000_000 + index * 10_000_000, [frame])]
    assert selected.update(sample) == full.update(sample)
    assert selected.can_valid == full.can_valid
    assert selected.bus_timeout == full.bus_timeout
    for key in selected.vl[message]:
      assert selected.vl[message][key] == full.vl[message][key]
      assert selected.vl_all[message][key] == full.vl_all[message][key]
      assert selected.ts_nanos[message][key] == full.ts_nanos[message][key]
    for addr, state in selected.message_states.items():
      reference = full.message_states[addr]
      assert (state.counter, state.counter_fail, list(state.timestamps)) == (reference.counter, reference.counter_fail, list(reference.timestamps))
  for _ in range(5):
    selected.update([(9_000_000_000, [])])
    full.update([(9_000_000_000, [])])
    selected_valid, full_valid = selected.can_valid, full.can_valid
    assert selected_valid == full_valid
  assert not selected_valid and not full_valid
  assert selected.bus_timeout and full.bus_timeout
  for signal in full.message_states[frames[0][0]].signals:
    if signal.type or signal.calc_checksum:
      assert signal.name in selected.vl[message]


def test_unknown_projection_is_rejected_and_lazy_selection_is_honored():
  with pytest.raises(ValueError, match='Unknown signal'):
    CANParser(TEST_DBC, [], 0, signals={'CAN_FD_MESSAGE': ['not_a_signal']})
  with pytest.raises(ValueError, match='Unknown signal'):
    CANParser(TEST_DBC, [], 0, signals={'not_a_message': []})
  parser = CANParser(TEST_DBC, [], 0, signals={'CAN_FD_MESSAGE': ['SIGNED']})
  assert 'SIGNED' in parser.vl['CAN_FD_MESSAGE']
  assert 'COUNTER' in parser.vl['CAN_FD_MESSAGE']
  assert parser.message_states[245].signals
