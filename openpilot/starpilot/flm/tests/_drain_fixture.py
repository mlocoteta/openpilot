"""Adapt declared callback schedules in daemon units, not production transport.

These tests deliberately drive callback time/source/native boundaries directly.
The actual FIFO merge and bounded wire receiver have their own transport tests.
"""


def separate_drain_fixture(single):
  def paired(control_socket, control, applied_socket, applied, receive, collector, now_ns, _state=None, *, budget_ns=None):
    single(control_socket, control, receive, collector, now_ns)
    single(applied_socket, applied, receive, collector, now_ns)
  return paired
