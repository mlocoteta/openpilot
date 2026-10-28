"""Overloaded FIFO recovery: original events survive, authority never does."""
from dataclasses import replace

import pytest

from openpilot.starpilot.flm import fullrate_collector as module
from openpilot.starpilot.flm.fullrate_collector import FullrateCollector, MAX_DRAIN, MAX_SNAPSHOT_WIRE_BYTES
from openpilot.starpilot.flm.learning_wire import read_applied, read_control
from openpilot.starpilot.flm.tests.test_fullrate_pipeline import SyntheticAdapter, snapshots, serialized_control, serialized_output
from openpilot.starpilot.flm.tests.test_paired_evidence_drain import BASE, small_event, transport


def setup(rows, callbacks=None):
  collector = FullrateCollector(SyntheticAdapter())
  sockets, receive, reads = transport(*rows)
  state = module.PairedDrainState(*sockets) if hasattr(module, 'PairedDrainState') else None
  seen = []
  callbacks = callbacks or tuple((lambda event, _collector, now, side=side: seen.append((side, event, now))) for side in (0, 1))

  def consume(now=BASE):
    args = (sockets[0], callbacks[0], sockets[1], callbacks[1], receive, collector, now)
    return module.drain_pair(*args, state) if state is not None else module.drain_pair(*args)

  return collector, consume, seen, state, sockets, reads


@pytest.mark.parametrize('side', (0, 1))
def test_overrun_does_not_erase_lookahead_or_the_other_fifo_head(side):
  rows = [[], []]
  rows[side] = [small_event(BASE + i) for i in range(MAX_DRAIN + 2)]
  rows[1 - side] = [small_event(BASE + MAX_DRAIN + 2)]
  collector, consume, seen, _, sockets, reads = setup(rows)
  assert not consume()
  assert collector.reason == 'fullrate_overrun' and collector.dropped == 1
  assert len(seen) == MAX_DRAIN and reads[sockets[side]] == MAX_DRAIN + 1
  assert reads[sockets[1 - side]] == 1
  assert not collector.ready and not collector.controls and not collector.applied
  assert consume(BASE + 10_000_000)
  assert [event for actual_side, event, _ in seen if actual_side == side] == rows[side]
  assert [event for actual_side, event, _ in seen if actual_side != side] == rows[1 - side]
  assert all(now == BASE + 10_000_000 for _, _, now in seen[MAX_DRAIN:])
  assert consume(BASE + 20_000_000)
  assert len(seen) == sum(map(len, rows))  # Exactly once, including lookahead.


def test_repeated_overload_stays_bounded_without_frame_sequence_gaps():
  rows = [[small_event(BASE + 2 * i + side) for i in range(4 * MAX_DRAIN + 5)] for side in (0, 1)]
  collector, consume, seen, state, _, _ = setup(rows)
  for tick in range(10):
    before = len(seen)
    done = consume(BASE + tick * 1_000_000)
    assert len(seen) - before <= 2 * MAX_DRAIN
    if state is not None:
      assert len(state.heads) == 2 and sum(h is not None for h in state.heads) <= 2
    if done:
      break
  assert done and collector.dropped > 0
  assert [event.logMonoTime for _, event, _ in seen] == list(range(BASE, BASE + 2 * len(rows[0])))
  assert not collector.ready


@pytest.mark.parametrize('delay,native,expected', [(10_000_000, True, 1), (200_000_000, True, 0), (10_000_000, False, 0)])
def test_carried_actual_wire_uses_new_receipt_clock_and_original_native_refusal(delay, native, expected):
  c, o, _ = snapshots(BASE)
  controls = [small_event(BASE - 100 + i) for i in range(MAX_DRAIN)] + [serialized_control(c)]
  outputs = [serialized_output(replace(o, native_allowed=native))]
  received = []

  def control(event, collector, now):
    if event.which() == 'starpilotLateralState':
      received.append(('control', now, read_control(event).control_ns))
      collector.control(read_control(event), now)

  def output(event, collector, now):
    received.append(('output', now, read_applied(event).apply_ns))
    collector.output(read_applied(event), now)

  collector, consume, _, _, _, _ = setup([controls, outputs], (control, output))
  assert not consume(BASE)
  assert not collector.ready
  assert consume(BASE + delay)
  assert [r[0] for r in received] == ['control', 'output']
  assert all(r[1] == BASE + delay for r in received)
  assert received[0][2] == c.control_ns and received[1][2] == o.apply_ns
  assert len(collector.ready) == expected
  if delay == 200_000_000:
    assert collector.training_interruptions['stale_control'] == 1
  if not native:
    assert not collector.points


@pytest.mark.parametrize('mutation', ('wire_size', 'header', 'callback'))
def test_carried_wire_revalidated_and_malformed_boundary_clears_both_heads(mutation):
  carried = small_event(BASE + MAX_DRAIN)
  rows = [[small_event(BASE + i) for i in range(MAX_DRAIN)] + [carried], [small_event(BASE + 100)]]
  callbacks = None
  if mutation == 'callback':
    def invalid(event, _collector, _now):
      if event is carried:
        raise ValueError('changed source context')
    callbacks = (invalid, invalid)
  collector, consume, _, state, _, _ = setup(rows, callbacks)
  assert not consume()
  if mutation == 'wire_size':
    carried.as_builder = lambda: type('Builder', (), {'to_bytes': lambda self: bytes(MAX_SNAPSHOT_WIRE_BYTES + 1)})()
  elif mutation == 'header':
    carried.logMonoTime = 0
  assert not consume(BASE + 1_000_000)
  assert collector.reason == 'malformed_evidence' and not collector.ready
  assert state.heads == (None, None)
  assert consume(BASE + 2_000_000)


def test_carry_cannot_cross_socket_replacement():
  collector, consume, _, state, sockets, _ = setup([[small_event(BASE + i) for i in range(MAX_DRAIN + 1)], [small_event(BASE + 100)]])
  assert not consume()
  received = []
  assert not module.drain_pair(object(), lambda *args: received.append(args), sockets[1], lambda *args: received.append(args),
                               lambda _socket: None, collector, BASE + 1_000_000, state)
  assert not received and state.heads == (None, None) and collector.reason == 'malformed_evidence'
