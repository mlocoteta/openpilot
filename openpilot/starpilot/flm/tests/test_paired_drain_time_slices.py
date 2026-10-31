"""Time slices preserve FIFO, real receipt clocks and original overload limits."""
from dataclasses import replace
from collections import deque
from types import SimpleNamespace
import pytest
from openpilot.starpilot.flm import fullrate_collector as module
from openpilot.starpilot.flm.fullrate_collector import FullrateCollector, PairedDrainState
from openpilot.starpilot.flm.learning_wire import read_applied, read_control
from openpilot.starpilot.flm.tests.test_fullrate_pipeline import SyntheticAdapter, snapshots, serialized_control, serialized_output
from openpilot.starpilot.flm.tests.test_paired_evidence_drain import BASE, small_event, transport


class WorkClock:
  def __init__(self):
    self.ns = 0

  def __call__(self):
    return self.ns


def test_yield_keeps_every_original_head_and_never_splits_the_maneuver():
  rows = [[small_event(BASE + 2*i + side) for i in range(10)] for side in (0, 1)]
  sockets, receive, _ = transport(*rows)
  collector = FullrateCollector(SyntheticAdapter())
  state = PairedDrainState(*sockets)
  clock = WorkClock()
  seen = []

  def callback(event, current, received):
    assert current is collector
    seen.append((event, received))
    clock.ns += 3_000_000

  for tick in range(20):
    before = len(seen)
    done = module.drain_pair(sockets[0], callback, sockets[1], callback, receive, collector,
      BASE+tick*10_000_000, state, budget_ns=5_000_000, clock=clock)
    assert 0 < len(seen)-before <= 2
    assert collector.dropped == 0
    if done:
      break
    assert any(head is not None for head in state.heads)
  assert done and len(seen) == 20
  assert [event.logMonoTime for event, _ in seen] == list(range(BASE, BASE+20))
  assert len({id(event)for event, _ in seen}) == 20
  assert state.heads == (None, None) and state.counts == (0, 0)


def test_a_stream_already_empty_in_this_batch_is_not_reopened_by_a_yield():
  sockets = object(), object()
  first, newer = small_event(BASE), small_event(BASE+10)
  outputs = [small_event(BASE+20+i)for i in range(3)]
  queues = {sockets[0]:deque([first]),sockets[1]:deque(outputs)}
  collector = FullrateCollector(SyntheticAdapter())
  state = PairedDrainState(*sockets)
  clock = WorkClock()
  seen = []

  def callback(event, _current, _stamp):
    seen.append(event)
    clock.ns += 2_000_000

  def consume():
    return module.drain_pair(sockets[0],callback,sockets[1],callback,
      lambda socket:queues[socket].popleft()if queues[socket]else None,
      collector,BASE,state,budget_ns=1_000_000,clock=clock)

  assert not consume() and seen == [first]
  queues[sockets[0]].append(newer)
  for _ in range(3):
    done = consume()
  assert done and seen == [first,*outputs]
  assert consume() and seen == [first,*outputs,newer]


def test_slicing_cannot_reset_the_original_per_stream_overrun_limit(monkeypatch):
  monkeypatch.setattr(module, 'MAX_DRAIN', 4)
  rows = [small_event(BASE+i)for i in range(7)]
  sockets, receive, _ = transport(rows, [])
  state = PairedDrainState(*sockets)
  collector = FullrateCollector(SyntheticAdapter())
  clock = WorkClock()
  seen = []

  def callback(event, _current, _received):
    seen.append(event)
    clock.ns += 2_000_000

  for tick in range(10):
    done = module.drain_pair(sockets[0], callback, sockets[1], callback, receive, collector,
      BASE+tick, state, budget_ns=1_000_000, clock=clock)
    if collector.dropped:
      assert len(seen) == 4 and collector.reason == 'fullrate_overrun'
      assert state.counts == (0, 0)
      break
  else:
    raise AssertionError('A timed yield bypassed the original overrun guard')
  for tick in range(10):
    done = module.drain_pair(sockets[0], callback, sockets[1], callback, receive, collector,
      BASE+100+tick, state, budget_ns=1_000_000, clock=clock)
    if done:
      break
  assert done and seen == rows and collector.dropped == 1


@pytest.mark.parametrize('delay,native,expected', [(10_000_000, True, 1), (200_000_000, True, 0), (10_000_000, False, 0)])
def test_yielded_output_uses_new_receipt_time_and_unchanged_native_refusal(delay, native, expected):
  control, output, _ = snapshots(BASE)
  sockets, receive, _ = transport([serialized_control(control)], [serialized_output(replace(output,native_allowed=native))])
  state = PairedDrainState(*sockets)
  collector = FullrateCollector(SyntheticAdapter())
  clock = WorkClock()
  received = []

  def consume_control(event, current, stamp):
    received.append(stamp)
    current.control(read_control(event), stamp)
    clock.ns += 2_000_000

  def consume_output(event, current, stamp):
    received.append(stamp)
    current.output(read_applied(event), stamp)
    clock.ns += 2_000_000

  assert not module.drain_pair(sockets[0], consume_control, sockets[1], consume_output,
    receive, collector, BASE, state, budget_ns=1_000_000, clock=clock)
  assert module.drain_pair(sockets[0], consume_control, sockets[1], consume_output,
    receive, collector, BASE+delay, state, budget_ns=1_000_000, clock=clock)
  assert received == [BASE, BASE+delay] and len(collector.ready) == expected


def test_retained_head_wakes_source_receiver_without_waiting_for_another_pose():
  from openpilot.starpilot.flm.steerlearnerd import _SourceDelivery
  calls = []
  sm = SimpleNamespace(update=lambda timeout:calls.append(timeout),
    updated={'deviceMotion':True},logMonoTime={'deviceMotion':BASE})
  receiver = _SourceDelivery()
  assert receiver.next(sm,retained_evidence=True) == BASE
  assert calls == [0] and not receiver.pending and receiver.pose_header == 0
