"""Bounded, read-only 50 Hz performance stream for the head-unit Performance app.

Same shape as hud.py: the worker owns its IPC sockets, starts only on an
authenticated request and leaves six seconds after the last one. It samples the
newest carState (and the newest powertrain-bus CAN frames) at 50 Hz into a short
ring buffer; a client pulls everything newer than the last sequence number it
saw (GET /api/perf?since=N), so a 5-10 Hz poll still gets every 50 Hz sample.
Nothing here writes Params, files, logs or CAN; absent or stale inputs stay null.

The extra CAN decodes are 2017 Accord (9G, Nidec) powertrain-bus signals measured
in the 2026-09-30 CAN survey; on any other car they stay null.
"""

import math
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass

from openpilot.starpilot.galaxy.plots import CLOCK_PAIR_MAX_SKEW_NS, finite, paired_boot_offset_ns


SAMPLE_HZ = 50
SAMPLE_INTERVAL_S = 1 / SAMPLE_HZ
BUFFER_SAMPLES = 150
FIRST_BATCH = 25
CLIENT_IDLE_S = 6.0
STALE_AFTER_S = 1.0
SOURCE_MAX_AGE_S = 0.3
MAX_AGE_S = {'deviceState': 2.0, 'peripheralState': 2.0}
CAN_MAX_AGE_NS = 250_000_000
# pycapnp costs ~2-7 us per frame (up to ~370 us per 50-frame batch on a desktop core), so CAN is scanned only
# every ~35 ms (~25 Hz). 0x1E7 is 50 Hz, i.e. in every other 100 Hz batch, and a 50 Hz sampler of a conflated
# socket keeps landing on the same parity (10-26 rlogs: always the batches without it). So the worker drains
# the raw CAN queue, scans the newest batch, and looks for a still-missing frame in the batch before it.
CAN_DECODE_NS = 35_000_000
CAN_WANT_NS = 60_000_000
PARAMS_RETRY_S = 10.0
SERVICES = ('carState', 'deviceState', 'peripheralState')   # + a raw, non-conflated 'can' socket
STATIC_SERVICES = ('carParams',)
# One row per sample, in this order. t: carState logMonoTime (s); v, a: vEgo, aEgo (m/s, m/s^2);
# ax, ay: VSA accelerometer long/lat (m/s^2, forward / left positive); yaw: VSA yaw rate (rad/s, left positive);
# steer: steering wheel angle (deg); gas: accelerator pedal 0..1; brake: brake pressure 0..1; brk: brake pedal 0/1;
# rpm: engine speed.
FIELDS = ('t', 'v', 'a', 'ax', 'ay', 'yaw', 'steer', 'gas', 'brake', 'brk', 'rpm')
BATTERY_MV_RANGE = (5_000, 20_000)

PT_BUS = 0
VSA_KINEMATICS = 0x91      # yaw 7|10, lat accel 19|10, long accel 25|10 (survey 4.2)
POWERTRAIN_DATA = 0x17C    # PEDAL_GAS 7|8, ENGINE_RPM 23|16, BRAKE_PRESSED 53|1
BRAKE_PRESSURE = 0x1E7     # 7|10, raw 102 at rest (survey 4.3)
CAN_IDS = (VSA_KINEMATICS, POWERTRAIN_DATA, BRAKE_PRESSURE)
YAW_SCALE = 0.00421
LAT_SCALE = 0.0467        # raw sign is right-positive like the yaw; both negated to left-positive
LONG_SCALE = -0.042
BRAKE_REST = 102
BRAKE_FULL = 300.0         # raw counts above rest that read as a full bar (hardest logged stop ~3.5 m/s^2 is ~200)
PEDAL_FULL = 255.0
ACCORD_9G = 'HONDA_ACCORD_9G'


def motorola(dat, start, size):
  """DBC big-endian (@0) unsigned field: start is the MSB in sawtooth bit numbering."""
  msb = (start // 8) * 8 + (7 - start % 8)
  shift = len(dat) * 8 - msb - size
  if shift < 0:
    return None
  return (int.from_bytes(dat, 'big') >> shift) & ((1 << size) - 1)


def accord_9g(car_params):
  """True/False once CarParams are known: the 2017 Accord on a Honda Nidec safety config."""
  if car_params is None:
    return None
  try:
    if str(car_params.brand) != 'honda' or str(car_params.carFingerprint) != ACCORD_9G:
      return False
    return any(str(config.safetyModel) == 'hondaNidec' for config in car_params.safetyConfigs)
  except (AttributeError, ValueError, RuntimeError, TypeError):
    return None


class CanLatest:
  """Newest frame per wanted address on the powertrain bus, with its log time."""

  def __init__(self):
    self.frames = {}
    self.decoded_ns = None

  def missing(self, mono_ns):
    return [address for address in CAN_IDS if address not in self.frames or mono_ns - self.frames[address][1] > CAN_WANT_NS]

  def offer(self, batches):
    """batches: [(logMonoTime ns, frames)] oldest first, as drained. Returns the number of batches scanned."""
    if not batches:
      return 0
    mono, frames = batches[-1]
    if self.decoded_ns is not None and 0 <= mono - self.decoded_ns < CAN_DECODE_NS:
      return 0
    self.decoded_ns = mono
    self.update(frames, mono)
    scanned = 1
    for older_mono, older in reversed(batches[:-1]):
      want = self.missing(mono)
      if not want:
        break
      self.update(older, older_mono, want)
      scanned += 1
    return scanned

  def update(self, can, mono_ns, only=None):
    """Keep the wanted frames of one batch; with `only`, just those addresses (stops once all are found)."""
    wanted = CAN_IDS if only is None else tuple(only)
    left = len(wanted)
    try:
      for frame in can:
        if frame.address in wanted and frame.src == PT_BUS:
          self.frames[frame.address] = (bytes(frame.dat), mono_ns)
          if only is not None:
            left -= 1
            if left == 0:
              break
    except (AttributeError, ValueError, RuntimeError, TypeError):
      pass

  def get(self, address, now_ns):
    item = self.frames.get(address)
    # A CAN batch can be logged a few ms after the carState it is paired with: compare both ways.
    if item is None or abs(now_ns - item[1]) > CAN_MAX_AGE_NS:
      return None
    return item[0]

  def decode(self, now_ns):
    out = dict.fromkeys(('ax', 'ay', 'yaw', 'gas', 'rpm', 'brake'))
    vsa = self.get(VSA_KINEMATICS, now_ns)
    if vsa is not None and len(vsa) >= 5:
      out['yaw'] = round(-(motorola(vsa, 7, 10) - 512) * YAW_SCALE, 4)
      out['ay'] = round(-(motorola(vsa, 19, 10) - 512) * LAT_SCALE, 3)
      out['ax'] = round((motorola(vsa, 25, 10) - 512) * LONG_SCALE, 3)
    pt = self.get(POWERTRAIN_DATA, now_ns)
    if pt is not None and len(pt) >= 4:
      out['gas'] = round(min(1.0, motorola(pt, 7, 8) / PEDAL_FULL), 3)
      out['rpm'] = motorola(pt, 23, 16)
    brake = self.get(BRAKE_PRESSURE, now_ns)
    if brake is not None and len(brake) >= 2:
      out['brake'] = round(min(1.0, max(0, motorola(brake, 7, 10) - BRAKE_REST) / BRAKE_FULL), 3)
    return out


def _field(source, name):
  try:
    return getattr(source, name)
  except (AttributeError, ValueError, RuntimeError, TypeError):
    return None


def _bool(source, name):
  value = _field(source, name)
  return value if isinstance(value, bool) else None


def sample_row(car_state, mono_ns, decoded):
  """One FIELDS row from a carState reader and CanLatest.decode() (or an all-None dict)."""
  brk = _bool(car_state, 'brakePressed')
  return [
    round(mono_ns / 1e9, 3),
    finite(_field(car_state, 'vEgo')),
    finite(_field(car_state, 'aEgo')),
    decoded['ax'], decoded['ay'], decoded['yaw'],
    finite(_field(car_state, 'steeringAngleDeg')),
    decoded['gas'], decoded['brake'],
    None if brk is None else int(brk),
    decoded['rpm'],
  ]


def slow_values(msgs, fresh, is_metric):
  device = msgs.get('deviceState') if fresh.get('deviceState') else None
  car_state = msgs.get('carState') if fresh.get('carState') else None
  volts = None
  if fresh.get('peripheralState'):
    mv = finite(_field(msgs.get('peripheralState'), 'voltage'))
    if mv is not None and BATTERY_MV_RANGE[0] <= mv <= BATTERY_MV_RANGE[1]:
      volts = round(mv / 1000, 2)
  gear = _field(car_state, 'gearShifter') if car_state is not None else None
  return {
    'onroad': _bool(device, 'started') if device is not None else None,
    'isMetric': is_metric if isinstance(is_metric, bool) else None,
    'gear': str(gear)[:20] if gear is not None else None,
    'batteryVolts': volts,
  }


def empty_slow():
  return {'onroad': None, 'isMetric': None, 'gear': None, 'batteryVolts': None}


@dataclass(frozen=True)
class PerfReading:
  row: list | None        # a new sample, or None when carState has not moved on / is stale
  slow: dict
  fresh: bool
  decodes: bool | None


def _read_params():
  try:
    from openpilot.common.params import Params
    return Params()
  except Exception:
    return None


class MessagingPerfReader:
  def __init__(self):
    from openpilot.cereal import messaging

    self.messaging = messaging
    self.started_ns = time.monotonic_ns()
    self.boot_offset_ns = paired_boot_offset_ns()
    self.sm = messaging.SubMaster(list(SERVICES))
    self.can_sock = None   # opened once CarParams say the decodes apply
    self.can = CanLatest()
    self.last_row_ns = 0
    self.params = _read_params()
    self.is_metric = None
    self.car_params = None
    self.car_params_at = None
    if self.params is not None:
      try:
        self.is_metric = bool(self.params.get_bool('IsMetric'))
      except Exception:
        self.is_metric = None

  def _decodes(self, now):
    """Accord 9G or not, from CarParams in Params, read at most every PARAMS_RETRY_S until the drive's copy exists."""
    if self.car_params is None and self.params is not None and (self.car_params_at is None or now - self.car_params_at >= PARAMS_RETRY_S):
      self.car_params_at = now
      try:
        from opendbc.car.structs import car
        raw = self.params.get('CarParams')
        self.car_params = self.messaging.log_from_bytes(raw, car.CarParams) if raw else None
      except Exception:
        self.car_params = None
    return accord_9g(self.car_params)

  def sample(self, now: float):
    sm = self.sm
    if sm is None:
      raise OSError('perf reader closed')
    sm.update(0)
    now = time.monotonic()
    current_offset = paired_boot_offset_ns()
    clock_ok = True
    if getattr(time, 'CLOCK_BOOTTIME', None) is not None:
      if current_offset is None:
        clock_ok = False
      elif self.boot_offset_ns is None or abs(current_offset - self.boot_offset_ns) > CLOCK_PAIR_MAX_SKEW_NS:
        self.started_ns = time.monotonic_ns()
        self.boot_offset_ns = current_offset
        clock_ok = False
    fresh = {}
    for key in SERVICES:
      event_ns = sm.logMonoTime[key]
      limit = MAX_AGE_S.get(key, SOURCE_MAX_AGE_S)
      fresh[key] = bool(
        clock_ok and sm.valid[key] and sm.seen[key] and sm.recv_time[key] > 0 and event_ns > self.started_ns
        and 0 <= now - sm.recv_time[key] <= limit and 0 <= now - event_ns / 1e9 <= limit
      )
    msgs = {key: sm[key] if fresh[key] else None for key in SERVICES}
    decodes = self._decodes(now)
    if decodes:
      if self.can_sock is None:
        self.can_sock = self.messaging.sub_sock('can', conflate=False)
      batches = []
      for raw in self.messaging.drain_sock_raw(self.can_sock)[-3:]:
        event = self.messaging.log_from_bytes(raw)
        if event.logMonoTime > self.started_ns and 0 <= now - event.logMonoTime / 1e9 <= SOURCE_MAX_AGE_S:
          batches.append((event.logMonoTime, event.can))
      if clock_ok:
        self.can.offer(batches)
    row = None
    car_ns = sm.logMonoTime['carState']
    if fresh['carState'] and car_ns != self.last_row_ns:
      self.last_row_ns = car_ns
      decoded = self.can.decode(car_ns) if decodes else CanLatest().decode(car_ns)
      row = sample_row(msgs['carState'], car_ns, decoded)
    return PerfReading(row, slow_values(msgs, fresh, self.is_metric), bool(fresh['carState']), decodes)

  def close(self):
    self.sm = None
    self.can_sock = None
    self.params = None


class Perf:
  def __init__(self, reader_factory=MessagingPerfReader, clock=time.monotonic):
    self.reader_factory = reader_factory
    self.session_id = secrets.token_hex(8)
    self.clock = clock
    self.lock = threading.Lock()
    self.stop_event = threading.Event()
    self.worker = None
    self.last_request = 0.0
    self.last_row_at = 0.0
    self.rows = deque(maxlen=BUFFER_SAMPLES)   # (seq, row)
    self.seq = 0
    self.slow = None
    self.current = False
    self.decodes = None
    self.error = ''
    self.closed = False

  def snapshot(self, since=None):
    """Rows with seq > since (at most BUFFER_SAMPLES); since=None gives the newest FIRST_BATCH."""
    now = self.clock()
    with self.lock:
      if self.closed:
        raise OSError('perf closed')
      self.last_request = now
      if self.worker is None or not self.worker.is_alive():
        self.stop_event.clear()
        self.worker = threading.Thread(target=self._run, daemon=True, name='galaxy-perf')
        self.worker.start()
      row_age = now - self.last_row_at if self.last_row_at else None
      live = self.slow is not None and row_age is not None and row_age <= STALE_AFTER_S and self.current
      state = 'current' if live else 'unavailable' if self.error and self.slow is None else 'stale'
      oldest = self.rows[0][0] if self.rows else self.seq + 1
      if since is None:
        rows = [row for _, row in list(self.rows)[-FIRST_BATCH:]]
        gap = False
      else:
        rows = [row for seq, row in self.rows if seq > since]
        gap = since < oldest - 1 or since > self.seq
      return {
        'schemaVersion': 1,
        'state': state,
        'sessionId': self.session_id,
        'seq': self.seq,
        'hz': SAMPLE_HZ,
        'gap': gap,
        'ageSeconds': math.ceil(row_age * 1000) / 1000 if row_age is not None else None,
        'decodes': self.decodes,
        'fields': list(FIELDS),
        'samples': rows,
        'slow': dict(self.slow) if self.slow is not None else empty_slow(),
        'error': self.error if self.slow is None else '',
      }

  def _run(self):
    reader = None
    try:
      reader = self.reader_factory()
      while not self.stop_event.is_set():
        with self.lock:
          if self.clock() - self.last_request >= CLIENT_IDLE_S:
            break
        try:
          reading = reader.sample(self.clock())
          with self.lock:
            self.slow = reading.slow
            self.current = reading.fresh
            self.decodes = reading.decodes
            self.error = ''
            if reading.row is not None:
              self.seq += 1
              self.rows.append((self.seq, reading.row))
              self.last_row_at = self.clock()
        except Exception as error:
          with self.lock:
            self.slow = None
            self.current = False
            self.error = type(error).__name__
        self.stop_event.wait(SAMPLE_INTERVAL_S)
    except Exception as error:
      with self.lock:
        self.slow = None
        self.current = False
        self.error = type(error).__name__
    finally:
      if reader is not None:
        try:
          reader.close()
        except Exception:
          pass
      with self.lock:
        self.slow = None
        self.current = False
        self.last_row_at = 0.0
        self.rows.clear()
        self.worker = None

  def close(self):
    with self.lock:
      self.closed = True
      self.stop_event.set()
      worker = self.worker
    if worker is not None:
      worker.join(timeout=0.25)
