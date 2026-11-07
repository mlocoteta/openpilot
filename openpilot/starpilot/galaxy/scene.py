"""Bounded, read-only scene stream for an external head-unit HUD (Botty Car 4.1).

GET /api/hud/scene streams one compact JSON line per NEW modelV2 (20 Hz), rate-limited to the client's `hz`, so the head
unit can draw lane lines, road edges, the path and the lead at 10-20 Hz and dead-reckon between frames with vEgo and the
yaw rate. Everything else stays on /api/hud polling. Contract: accord-head-unit/state/handoff/scene-stream-contract.md.

Like hud.py: the worker owns its IPC sockets, subscribes only while a stream is open and leaves SCENE_IDLE_S after the
last one; each frame is built once and shared by every stream; nothing here writes Params, files or logs.

Signs: model and lead y are right positive (as /api/hud). deviceMotion.angularVelocityDevice.z and
controlsState.desiredCurvature are z-down (positive = turning RIGHT, checked on the car's 11-07 rlog), so `yr` and `c`
are negated here: positive = turning LEFT.
"""

import math
import threading
import time

from openpilot.starpilot.galaxy.hud import LANE_CHANGE_STATES, LANE_CHANGE_DIRECTIONS, MODEL_IDX, _enum, _field

SERVICES = ('modelV2', 'carState', 'deviceMotion', 'radarState', 'controlsState')
HZ_DEFAULT = 10
HZ_RANGE = (5, 20)
MAX_STREAMS = 2
STREAM_MAX_S = 60.0
KEEPALIVE_S = 2.0
KEEPALIVE = b'{"k":1}\n'
SCENE_IDLE_S = 6.0
SOURCE_MAX_AGE_S = 0.5
POLL_MS = 100
# a frame may go out this much before its slot; absorbs modelV2 jitter so hz=10 or 20 does not drop to 6.7 or 10
SEND_SLACK_S = 0.01


def _num(value, digits):
  """Shortest fixed-point text of a finite number ('12', '-0.5', '3.05'), or None."""
  try:
    number = float(value)
  except (TypeError, ValueError, OverflowError):
    return None
  if not math.isfinite(number):
    return None
  text = f'{number:.{digits}f}'
  if '.' in text:
    text = text.rstrip('0').rstrip('.')
  return '0' if text in ('-0', '') else text


def _line(xyz):
  """'[x,y,x,y,...]' of the 14 MODEL_IDX points (x 1 decimal, y 2 decimals), or None when short or non-finite."""
  xs, ys = _field(xyz, 'x'), _field(xyz, 'y')
  try:
    if xs is None or ys is None or len(xs) <= MODEL_IDX[-1] or len(ys) <= MODEL_IDX[-1]:
      return None
    out = []
    for i in MODEL_IDX:
      x, y = _num(xs[i], 1), _num(ys[i], 2)
      if x is None or y is None:
        return None
      out += (x, y)
  except (IndexError, TypeError, ValueError):
    return None
  return '[' + ','.join(out) + ']'


def _floats(values, count):
  try:
    out = [_num(v, 2) for v in values] if values is not None else []
  except (TypeError, ValueError):
    return None
  return '[' + ','.join(out) + ']' if len(out) == count and None not in out else None


def model_json(model):
  if model is None:
    return 'null'
  lines = [_line(line) for line in (_field(model, 'laneLines') or [])]
  edges = [_line(edge) for edge in (_field(model, 'roadEdges') or [])]
  if len(lines) != 4 or len(edges) != 2 or None in lines or None in edges:
    return 'null'
  parts = ['"ll":[' + ','.join(lines) + ']', '"re":[' + ','.join(edges) + ']']
  for key, value in (('pa', _line(_field(model, 'position'))), ('pr', _floats(_field(model, 'laneLineProbs'), 4)),
                     ('sd', _floats(_field(model, 'roadEdgeStds'), 2))):
    if value is not None:
      parts.append(f'"{key}":{value}')
  return '{' + ','.join(parts) + '}'


def lead_json(radar):
  lead = _field(radar, 'leadOne')
  if lead is None or _field(lead, 'present') is not True:
    return 'null'
  d, vr, y = _num(_field(lead, 'dRel'), 1), _num(_field(lead, 'vRel'), 2), _field(lead, 'yRel')
  if d is None or vr is None:
    return 'null'
  y = _num(-y, 2) if isinstance(y, (int, float)) else None   # radar yRel is left positive
  track = _field(lead, 'radarTrackId')
  track_id = int(track) if isinstance(track, int) and _field(lead, 'radar') is True else -1
  return '{"d":' + d + ',"y":' + (y or 'null') + ',"vr":' + vr + ',"id":' + str(track_id) + '}'


def lane_change(model):
  meta = _field(model, 'meta')
  state, direction = _enum(meta, 'laneChangeState'), _enum(meta, 'laneChangeDirection')
  if state not in LANE_CHANGE_STATES:
    return 'null', 'null'
  return f'"{state}"', f'"{direction}"' if direction in LANE_CHANGE_DIRECTIONS else 'null'


def frame_body(msgs):
  """Everything after '{"s":N,"a":A,' of one frame, from the fresh messages (None = stale/absent)."""
  car_state, motion, controls, model = msgs.get('carState'), msgs.get('deviceMotion'), msgs.get('controlsState'), msgs.get('modelV2')
  v = _num(_field(car_state, 'vEgo'), 2) if car_state is not None else None
  yr = c = None
  if motion is not None:
    angular = _field(motion, 'angularVelocityDevice')
    z = _field(angular, 'z')
    if _field(angular, 'valid') is True and isinstance(z, (int, float)):
      yr = _num(-z, 4)
  if controls is not None:
    curvature = _field(controls, 'desiredCurvature')
    c = _num(-curvature, 5) if isinstance(curvature, (int, float)) else None
  lc, ld = lane_change(model) if model is not None else ('null', 'null')
  radar = msgs.get('radarState')
  lead = lead_json(radar) if radar is not None else 'null'
  return f'"v":{v or "null"},"yr":{yr or "null"},"c":{c or "null"},"m":{model_json(model)},"l":{lead},"lc":{lc},"ld":{ld}}}'


class MessagingSceneReader:
  """One SubMaster polled on modelV2; read() returns (modelV2 logMonoTime ns, frame body) for each new model, else None."""

  def __init__(self):
    from openpilot.cereal import messaging

    self.started_ns = time.monotonic_ns()
    self.sm = messaging.SubMaster(list(SERVICES), poll='modelV2')

  def read(self):
    sm = self.sm
    if sm is None:
      raise OSError('scene reader closed')
    sm.update(POLL_MS)
    if not sm.updated['modelV2']:
      return None
    now = time.monotonic()
    msgs = {}
    for key in SERVICES:
      fresh = bool(sm.seen[key] and sm.valid[key] and sm.logMonoTime[key] > self.started_ns and
                   0 <= now - sm.recv_time[key] <= SOURCE_MAX_AGE_S)
      msgs[key] = sm[key] if fresh else None
    return sm.logMonoTime['modelV2'], frame_body(msgs)

  def close(self):
    self.sm = None


class SceneStreams:
  """Shared newest frame + at most MAX_STREAMS writers. stream() blocks its request thread until the stream ends."""

  def __init__(self, reader_factory=MessagingSceneReader, clock=time.monotonic):
    self.reader_factory = reader_factory
    self.clock = clock
    self.cond = threading.Condition()
    self.stop_event = threading.Event()
    self.worker = None
    self.streams = 0
    self.last_stream = 0.0
    self.seq = 0
    self.frame_ns = 0
    self.body = None
    self.error = ''
    self.closed = False

  def acquire(self):
    """True when a stream slot was taken (starts the worker); the caller must release() it."""
    with self.cond:
      if self.closed:
        raise OSError('scene closed')
      if self.streams >= MAX_STREAMS:
        return False
      self.streams += 1
      if self.worker is None or not self.worker.is_alive():
        self.stop_event.clear()
        self.worker = threading.Thread(target=self._run, daemon=True, name='galaxy-scene')
        self.worker.start()
      return True

  def release(self):
    with self.cond:
      self.streams -= 1
      self.last_stream = self.clock()

  def stream(self, write, hz=HZ_DEFAULT, stopped=lambda: False, duration=None):
    """Write frames (newest only, at most `hz`/s) and keep-alives until `duration`, close() or a failed write."""
    duration = STREAM_MAX_S if duration is None else duration
    interval = 1.0 / hz
    started = self.clock()
    with self.cond:
      sent_seq = self.seq    # only frames newer than the stream's start
    next_due = started
    last_write = started
    while True:
      now = self.clock()
      if now - started >= duration or self.closed or stopped():
        return
      with self.cond:
        if self.worker is None:
          return    # the reader failed; the client reconnects and gets a fresh worker
        if self.seq == sent_seq or now < next_due - SEND_SLACK_S:
          wait = min(KEEPALIVE_S - (now - last_write), duration - (now - started), 0.25)
          if self.seq != sent_seq:
            wait = min(wait, next_due - SEND_SLACK_S - now)
          self.cond.wait(max(0.0, wait))
          line = None
        else:
          sent_seq, frame_ns, body = self.seq, self.frame_ns, self.body
          line = b''
      now = self.clock()
      if line is None:
        if now - last_write >= KEEPALIVE_S:
          write(KEEPALIVE)
          last_write = now
        continue
      age = max(0.0, time.monotonic() - frame_ns / 1e9)
      write(f'{{"s":{sent_seq},"a":{math.ceil(age * 1000) / 1000},{body}\n'.encode())
      last_write = now
      next_due = next_due + interval if now - next_due < interval else now + interval

  def _run(self):
    reader = None
    try:
      reader = self.reader_factory()
      while not self.stop_event.is_set():
        with self.cond:
          if self.streams == 0 and self.clock() - self.last_stream >= SCENE_IDLE_S:
            break
        result = reader.read()
        if result is not None:
          with self.cond:
            self.seq += 1
            self.frame_ns, self.body = result
            self.error = ''
            self.cond.notify_all()
    except Exception as error:
      with self.cond:
        self.error = type(error).__name__
    finally:
      if reader is not None:
        try:
          reader.close()
        except Exception:
          pass
      with self.cond:
        self.body = None
        self.worker = None
        self.cond.notify_all()

  def close(self):
    with self.cond:
      self.closed = True
      self.stop_event.set()
      worker = self.worker
      self.cond.notify_all()
    if worker is not None:
      worker.join(timeout=0.25)
