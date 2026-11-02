"""Host tests for pigeond's receive loop with a fake serial port and a fake clock (no comma hardware)."""
import types

import pytest

from openpilot.system.ubloxd import pigeond
from openpilot.system.ubloxd.pigeond import AssistBackoff, UbxWatchdog, add_ubx_checksum, has_recent_fix, ubx_frame_ends

# UBX-NAV-PVT-sized frame (class 0x01, id 0x07, 92-byte payload) with a valid checksum
FRAME = add_ubx_checksum(b"\xb5\x62\x01\x07\x5c\x00" + bytes(range(92)))


class FakeClock:
  def __init__(self):
    self.t = 1000.

  def monotonic(self):
    return self.t

  def sleep(self, s):
    self.t += s


class FakePigeon:
  """Fake serial: script(t) returns the bytes the ublox 'sent' since the last read; each read advances 50 ms."""
  def __init__(self, clock, script):
    self.clock, self.script = clock, script

  def receive(self):
    self.clock.t += 0.05
    return self.script(self.clock.t)


class FakePM:
  def __init__(self, *a, **k):
    self.sent = []

  def send(self, name, msg):
    self.sent.append(bytes(msg.ubloxRaw))


@pytest.fixture
def loop(monkeypatch):
  clock = FakeClock()
  fake_time = types.SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep)
  monkeypatch.setattr(pigeond, "time", fake_time)
  pm = FakePM()
  monkeypatch.setattr(pigeond.messaging, "PubMaster", lambda *a, **k: pm)
  monkeypatch.setattr(pigeond.threading, "Thread", lambda *a, **k: types.SimpleNamespace(start=lambda: None))
  inits = []
  monkeypatch.setattr(pigeond, "init", lambda p: inits.append(clock.t))

  def run(script, duration):
    monkeypatch.setattr(pigeond, "TTYPigeon", lambda: FakePigeon(clock, script))
    pigeond.run_receiving(duration)
    return inits[1:], pm.sent  # inits[0] is the startup init
  return run


def test_zero_bursts_do_not_reinit(loop):
  # 10 Hz frames, and every 3rd read a burst of overrun/break 0x00 bytes (alone or in front of a frame)
  n = [0]
  def script(t):
    n[0] += 1
    if n[0] % 3 == 0:
      return b"\x00" * 16
    if n[0] % 3 == 1:
      return b"\x00\x00" + FRAME
    return FRAME
  reinits, sent = loop(script, 60)
  assert reinits == []
  assert sent and all(not s.startswith(b"\x00") for s in sent)


def test_only_zeros_reinit_after_timeout(loop):
  # the receiver died and the line reads as zeros: re-init once it has been without a valid frame for 5 s
  reinits, _ = loop(lambda t: FRAME if t < 1010 else b"\x00" * 64, 20)
  assert len(reinits) >= 1
  assert 1015 - 0.2 <= reinits[0] <= 1015 + 0.2


def test_silence_reinits_after_5s(loop):
  reinits, _ = loop(lambda t: FRAME if t < 1010 else b"", 20)
  assert len(reinits) >= 1
  assert 1015 - 0.2 <= reinits[0] <= 1015 + 0.2


def test_short_silence_does_not_reinit(loop):
  # a 4 s gap (below the 5 s timeout) followed by valid frames again
  reinits, _ = loop(lambda t: b"" if 1010 < t < 1014 else FRAME, 30)
  assert reinits == []


def test_corrupt_frames_count_as_no_data(loop):
  bad = FRAME[:-1] + bytes([FRAME[-1] ^ 0xff])
  reinits, _ = loop(lambda t: FRAME if t < 1010 else bad, 20)
  assert reinits and 1015 - 0.2 <= reinits[0] <= 1015 + 0.2


def test_frame_split_across_reads():
  w = UbxWatchdog(0.)
  w.feed(FRAME[:40], 4.)
  assert w.dead(5.1)
  w.feed(FRAME[40:], 5.2)
  assert not w.dead(10.)
  assert w.dead(10.3)


def test_ubx_frame_ends():
  assert ubx_frame_ends(b"\x00" + FRAME + FRAME) == (2, 1 + 2 * len(FRAME))
  assert ubx_frame_ends(FRAME + FRAME[:10]) == (1, len(FRAME))
  assert ubx_frame_ends(b"\x00" * 20) == (0, 20)


def test_assist_backoff():
  b = AssistBackoff()
  assert b.due(0.)
  delays = [b.failed(0.) for _ in range(10)]
  assert delays[:4] == [10., 20., 40., 80.]
  assert max(delays) == 600. and delays[-1] == 600.
  assert not b.due(599.) and b.due(600.)


def test_has_recent_fix():
  class SM(dict):
    pass
  sm = SM(gpsLocationExternal=types.SimpleNamespace(hasFix=True))
  sm.seen = {'gpsLocationExternal': True}
  sm.recv_time = {'gpsLocationExternal': 100.}
  assert has_recent_fix(sm, 101.)
  assert not has_recent_fix(sm, 103.)
  sm['gpsLocationExternal'] = types.SimpleNamespace(hasFix=False)
  assert not has_recent_fix(sm, 101.)
  sm.seen = {'gpsLocationExternal': False}
  assert not has_recent_fix(sm, 101.)
