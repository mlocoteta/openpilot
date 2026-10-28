"""Bounded, read-only driving snapshot for an external head-unit HUD.

Modeled on plots.py: the worker owns its IPC sockets, no subscription exists
until an authenticated request arrives, and the worker leaves after six seconds
without a viewer. Requests are served from the last cached projection. Absent or
stale inputs stay null; nothing here writes Params, files or logs.

Schema 2 (F29, Accord head unit, accord-head-unit/upper-screen/HUD-V2.md) adds, all optional:
- model: modelV2 laneLines/laneLineProbs/roadEdges/roadEdgeStds/position as 14 [x fwd m, y m] points (grid 0,2,..,26)
- road: mapdOut lanes/estimatedRoadWidth/roadName
- lead.yRel (right positive) + lead.trackId (radarTrackId, -1 = vision-only lead)
- tracks (v2.1): credible radarTracks points, moving with us or stopped after being seen moving
- fuel (v2.2, Accord 9G only): the car's own trip-fuel counter (CAN 0x324 bytes 2-3) as mL + mpg
"""

from collections import deque

import math
import secrets
import threading
import time
from dataclasses import dataclass

from openpilot.starpilot.galaxy.plots import CLOCK_PAIR_MAX_SKEW_NS, finite, paired_boot_offset_ns


SAMPLE_INTERVAL_S = 0.25
CLIENT_IDLE_S = 6.0
STALE_AFTER_S = 1.5
SOURCE_MAX_AGE_S = 1.0
# Slow publishers get a wider window; carParams (0.02 Hz) is per-drive static data.
MAX_AGE_S = {'deviceState': 2.0, 'chestnutState': 1.5, 'peripheralState': 2.0}
STATIC_SERVICES = ('carParams',)
PARAMS_RETRY_S = 10.0
SERVICES = ('deviceState', 'selfdriveState', 'carState', 'carControl', 'radarState', 'slcState',
            'chestnutState', 'drivingModelData', 'peripheralState', 'carParams', 'modelV2', 'radarTracks', 'mapdOut')

# v2 model geometry: every other point of the 33-point modelV2 grid -> 14 points, x 0..~126 m.
MODEL_IDX = tuple(range(0, 27, 2))
# v2.1 tracks: the Nidec radar has 16 slots. "Moving" = over-ground speed of at least 2.5 m/s.
TRACKS_MAX = 16
TRACK_MOVING = 2.5
TRACK_D_RANGE = (1.0, 150.0)
TRACK_Y_MAX = 12.0
# v2.2 fuel (Accord 9G): CAN 0x324 bytes 2-3 big-endian = trip fuel since ignition, 0.1 mL per count (checked against
# EPA highway/city on 10-26 rlogs), wraps at 65536, 10 Hz on the powertrain bus.
FUEL_CAR = 'HONDA_ACCORD_9G'
FUEL_ADDR = 0x324
FUEL_BUS = 0
FUEL_ML_PER_COUNT = 0.1
FUEL_SCAN_BATCHES = 12      # 0x324 is in every 10th 100 Hz batch: the newest 12 always hold one
FUEL_GAP_S = 2.0            # longer sample gaps add neither fuel nor distance
FUEL_WINDOW_S = 2.0
FUEL_MPG_CAP = 99.9
FUEL_AVG_MIN_M = 400.0
FUEL_BUCKET_MI = 0.25
FUEL_HIST_MAX = 120
M_PER_MI = 1609.344
ML_PER_GAL = 3785.41

# opendbc HondaSafetyFlags.TORQUE_INTERCEPTOR (F01): set in the Nidec safety word only when the TI drives lateral.
TI_SAFETY_PARAM = 4096
CV_KPH_TO_MS = 1 / 3.6
V_CRUISE_UNSET_KPH = 255
CHESTNUT_MIN_SUPPLY_MV = 10_000
# panda harness voltage (car 12 V bus); outside this range it is a bad read, not a battery value.
BATTERY_MV_RANGE = (5_000, 20_000)

STATUS_NAMES = {'disabled': 'disengaged', 'preEnabled': 'preEnabled', 'enabled': 'engaged',
                'softDisabling': 'softDisabling', 'overriding': 'overriding'}
ALERT_STATUS = ('normal', 'userPrompt', 'critical')
ALERT_SIZE = ('none', 'small', 'mid', 'full')
PERSONALITIES = ('aggressive', 'standard', 'relaxed')


def empty():
  return {
    'onroad': None, 'isMetric': None,
    'engaged': None, 'active': None, 'available': None, 'engageable': None, 'status': None,
    'vEgo': None, 'vCruise': None, 'vCruiseCluster': None,
    'lead': None,
    'steering': {'latActive': None, 'source': 'unknown', 'detail': None, 'fault': None},
    'alert': None,
    'experimental': None, 'personality': None,
    'slc': None,
    'egpu': None,
    'blinker': None, 'gear': None,
    'batteryVolts': None,
    'model': None, 'road': None, 'tracks': None, 'fuel': None,
  }


def _field(source, name):
  try:
    return getattr(source, name)
  except (AttributeError, ValueError, RuntimeError, TypeError):
    return None


def _bool(source, name):
  value = _field(source, name)
  return value if isinstance(value, bool) else None


def _text(source, name, limit=160):
  value = _field(source, name)
  if value is None:
    return None
  try:
    text = str(value)
  except (ValueError, UnicodeError):
    return None
  return text[:limit]


def _enum(source, name):
  value = _text(source, name, 40)
  return value if value else None


def _speed_kph(value):
  kph = finite(value)
  if kph is None or kph <= 0 or kph >= V_CRUISE_UNSET_KPH:
    return None
  return round(kph * CV_KPH_TO_MS, 4)


def _positive(value):
  number = finite(value)
  return number if number is not None and number > 0 else None


def ti_car(car_params):
  """True/False once CarParams are known: the TI safety bit on a Honda Nidec config (F01 ti_qualified)."""
  if car_params is None:
    return None
  try:
    configs = list(car_params.safetyConfigs)
    if _text(car_params, 'brand', 40) != 'honda' or not configs:
      return False
    return any(str(config.safetyModel) == 'hondaNidec' and int(config.safetyParam) & TI_SAFETY_PARAM for config in configs)
  except (AttributeError, ValueError, RuntimeError, TypeError):
    return None


def _steering(msgs, fresh, selfdrive_active):
  car_state = msgs.get('carState') if fresh.get('carState') else None
  car_control = msgs.get('carControl') if fresh.get('carControl') else None
  ti = ti_car(msgs.get('carParams') if fresh.get('carParams') else None)
  lat_active = _bool(car_control, 'latActive') if car_control is not None else None
  temporary = _bool(car_state, 'steerFaultTemporary') if car_state is not None else None
  permanent = _bool(car_state, 'steerFaultPermanent') if car_state is not None else None
  fault = None if temporary is None or permanent is None else bool(temporary or permanent)
  source = 'unknown' if ti is None else 'ti' if ti else 'lkas'
  if permanent:
    detail = 'permanent fault'
  elif temporary:
    # On the TI car F04 raises steerFaultTemporary while the board is locked out (auto cold-reset runs);
    # the stock EPS STEER_STATUS can raise it too, so the two are not separable from carState.
    detail = 'TI lockout or EPS fault' if ti else 'temporary fault'
  elif lat_active is None:
    detail = None
  elif lat_active:
    detail = 'steering' if selfdrive_active else 'always-on lateral'
  else:
    detail = 'standby'
  return {'latActive': lat_active, 'source': source, 'detail': detail, 'fault': fault}


def _lead(radar):
  lead = _field(radar, 'leadOne')
  if lead is None or _field(lead, 'present') is not True:
    return None
  d_rel, v_rel, v_lead = finite(_field(lead, 'dRel')), finite(_field(lead, 'vRel')), finite(_field(lead, 'vLead'))
  if d_rel is None or v_rel is None or v_lead is None:
    return None
  y_rel = finite(_field(lead, 'yRel'))
  radar = _bool(lead, 'radar')
  track = _field(lead, 'radarTrackId')
  track_id = int(track) if isinstance(track, int) and radar else -1
  return {'status': True, 'dRel': d_rel, 'vRel': v_rel, 'vLead': v_lead, 'radar': radar,
          'yRel': -y_rel if y_rel is not None else None, 'trackId': track_id}


def _r2(value):
  return round(value, 2)


def _line(xyz):
  """14 [x, y] points of a modelV2 XYZTData, or None when short or non-finite."""
  xs, ys = _field(xyz, 'x'), _field(xyz, 'y')
  try:
    if xs is None or ys is None or len(xs) <= MODEL_IDX[-1] or len(ys) <= MODEL_IDX[-1]:
      return None
    points = [(finite(xs[i]), finite(ys[i])) for i in MODEL_IDX]
  except (IndexError, TypeError, ValueError):
    return None
  if any(x is None or y is None for x, y in points):
    return None
  return [[_r2(x), _r2(y)] for x, y in points]


def _floats(values, count):
  try:
    out = [finite(v) for v in values] if values is not None else []
  except (TypeError, ValueError):
    return None
  return [_r2(v) for v in out] if len(out) == count and all(v is not None for v in out) else None


def _model(model):
  lines = [_line(line) for line in (_field(model, 'laneLines') or [])]
  edges = [_line(edge) for edge in (_field(model, 'roadEdges') or [])]
  if len(lines) != 4 or len(edges) != 2 or any(line is None for line in lines + edges):
    return None
  return {'laneLines': lines, 'laneLineProbs': _floats(_field(model, 'laneLineProbs'), 4), 'roadEdges': edges,
          'roadEdgeStds': _floats(_field(model, 'roadEdgeStds'), 2), 'path': _line(_field(model, 'position'))}


def _road(mapd):
  lanes = _field(mapd, 'lanes')
  width = finite(_field(mapd, 'estimatedRoadWidth'))
  name = _text(mapd, 'roadName', 80)
  return {'lanes': lanes if isinstance(lanes, int) and 0 < lanes <= 8 else None,
          'width': _r2(width) if width is not None and width > 0 else None,
          'name': name or None}


def tracks(radar_tracks, v_ego, seen_moving):
  """Credible radar tracks (HUD-V2.md v2.1). seen_moving: {trackId: True} kept by the caller across samples; ids that
  disappear are dropped from it. radar yRel is +left, the HUD's is +right."""
  points = _field(radar_tracks, 'points')
  if points is None or v_ego is None:
    return None
  out, live = [], set()
  try:
    ordered = sorted(points, key=lambda point: point.dRel)
  except (AttributeError, TypeError, ValueError):
    return None
  for point in ordered:
    d_rel, y_rel, v_rel = finite(_field(point, 'dRel')), finite(_field(point, 'yRel')), finite(_field(point, 'vRel'))
    track_id = _field(point, 'trackId')
    if d_rel is None or y_rel is None or v_rel is None or not isinstance(track_id, int):
      continue
    live.add(track_id)
    v_lead = v_ego + v_rel
    if v_lead >= TRACK_MOVING:
      seen_moving[track_id] = True
    if not TRACK_D_RANGE[0] < d_rel < TRACK_D_RANGE[1] or abs(y_rel) > TRACK_Y_MAX or v_lead <= -TRACK_MOVING:
      continue
    stopped = v_lead < TRACK_MOVING
    if stopped and not seen_moving.get(track_id):
      continue
    out.append({'id': track_id, 'dRel': _r2(d_rel), 'yRel': _r2(-y_rel), 'vRel': _r2(v_rel), 'vLead': _r2(v_lead),
                'stopped': stopped})
  for gone in [track_id for track_id in seen_moving if track_id not in live]:
    del seen_moving[gone]
  return out[:TRACKS_MAX]


class FuelTrip:
  """v2.2 fuel from the 0x324 trip counter. Fuel and distance only accumulate across consecutive samples at most
  FUEL_GAP_S apart, so both cover exactly the time the HUD watched; a counter drop that is not a wrap = new ignition."""

  def __init__(self):
    self.reset()

  def reset(self):
    self.count = None
    self.at = None
    self.v = None
    self.ml = 0.0
    self.m = 0.0
    self.window = deque()
    self.hist = []
    self.bucket = (0.0, 0.0)   # (miles, mL) at the start of the open bucket
    self.seen = False

  def update(self, count, v_ego, now, onroad):
    if onroad is not True:
      if onroad is False:
        self.reset()
      return
    if count is None or v_ego is None:
      return
    delta = None
    if self.count is not None and self.at is not None and 0 < now - self.at <= FUEL_GAP_S:
      delta = count - self.count
      if delta < 0:
        if self.count - count > 30_000:
          delta += 65_536
        else:
          self.reset()   # the car zeroes the counter at ignition: a new trip starts at this sample
          delta = None
    if delta is not None:
      self.ml += delta * FUEL_ML_PER_COUNT
      self.m += (v_ego + self.v) / 2 * (now - self.at)
      mi = self.m / M_PER_MI
      start_mi, start_ml = self.bucket
      if mi - start_mi >= FUEL_BUCKET_MI:
        used = self.ml - start_ml
        if used > 0:
          self.hist = (self.hist + [[_r2(mi), round(min(FUEL_MPG_CAP, (mi - start_mi) / (used / ML_PER_GAL)), 1)]])[-FUEL_HIST_MAX:]
        self.bucket = (mi, self.ml)
    self.count, self.at, self.v, self.seen = count, now, v_ego, True
    self.window.append((now, self.ml, self.m))
    while self.window and self.window[0][0] < now - FUEL_WINDOW_S:
      self.window.popleft()

  def value(self):
    if not self.seen:
      return None
    rate = inst = None
    if self.window:
      t0, ml0, m0 = self.window[0]
      t1, ml1, m1 = self.window[-1]
      span = t1 - t0
      if span >= 0.5:
        rate = round((ml1 - ml0) / span, 3)
        if (m1 - m0) / span >= 1.0:
          used = ml1 - ml0
          inst = FUEL_MPG_CAP if used <= 0 else round(min(FUEL_MPG_CAP, ((m1 - m0) / M_PER_MI) / (used / ML_PER_GAL)), 1)
    avg = None
    if self.m > FUEL_AVG_MIN_M and self.ml > 0:
      avg = round(min(FUEL_MPG_CAP, (self.m / M_PER_MI) / (self.ml / ML_PER_GAL)), 1)
    return {'tripMl': round(self.ml, 1), 'tripM': round(self.m), 'rateMlS': rate, 'instMpg': inst, 'avgMpg': avg,
            'hist': [list(item) for item in self.hist]}


def fuel_count(batches):
  """Newest 0x324 trip counter in drained CAN batches (oldest first), scanning at most FUEL_SCAN_BATCHES from the end."""
  for can in reversed(batches[-FUEL_SCAN_BATCHES:]):
    try:
      for frame in can:
        if frame.address == FUEL_ADDR and frame.src == FUEL_BUS:
          data = bytes(frame.dat)
          if len(data) >= 4:
            return int.from_bytes(data[2:4], 'big')
    except (AttributeError, TypeError, ValueError):
      continue
  return None


def _alert(state):
  size = _enum(state, 'alertSize')
  status = _enum(state, 'alertStatus')
  if size not in ALERT_SIZE or size == 'none' or status not in ALERT_STATUS:
    return None
  text1, text2 = _text(state, 'alertText1') or '', _text(state, 'alertText2') or ''
  if not text1 and not text2:
    return None
  return {'text1': text1, 'text2': text2, 'status': status, 'size': size, 'type': _text(state, 'alertType', 80)}


def _slc(slc):
  if not (_field(slc, 'enabled') is True or _field(slc, 'displayOnly') is True):
    return None
  valid = _field(slc, 'observationKind') == 'valid'
  limit = _positive(_field(slc, 'speedLimit')) if valid else None
  return {
    'limit': limit,
    'offset': finite(_field(slc, 'offset')) if limit is not None else None,
    'target': _positive(_field(slc, 'effectiveCap')) if _field(slc, 'hasCeiling') is True else None,
    'source': (_text(slc, 'source', 40) or None) if valid else None,
    'pending': _positive(_field(slc, 'pendingSpeedLimit')) if valid and _field(slc, 'hasPending') is True else None,
    'state': _text(slc, 'status', 80) or None,
    'kind': _text(slc, 'observationKind', 20) or None,
    'lastLimit': _positive(_field(slc, 'lastReceivedSpeedLimit')),
    'displayOnly': _bool(slc, 'displayOnly'),
  }


def _egpu(msgs, fresh, onroad):
  device = msgs.get('deviceState') if fresh.get('deviceState') else None
  if device is None:
    return None
  present = _bool(device, 'chestnutPresent')
  telemetry = msgs.get('chestnutState') if fresh.get('chestnutState') else None
  supply_mv = finite(_field(telemetry, 'supplyVoltage')) if telemetry is not None else None
  result = {'state': 'unknown', 'detail': None,
            'tempC': finite(_field(telemetry, 'tempC')) if telemetry is not None else None,
            'supplyVolts': round(supply_mv / 1000, 2) if supply_mv is not None else None,
            'bigModel': None}
  if present is not True:
    result['state'] = 'absent'
    result['detail'] = ('not on USB, no 12 V input' if supply_mv is not None and supply_mv < CHESTNUT_MIN_SUPPLY_MV
                        else 'not detected on USB')
    return result
  if telemetry is not None and _field(telemetry, 'supplyFault') is True:
    result['state'], result['detail'] = 'error', 'supply fault'
    return result
  if not onroad:
    result['detail'] = 'detected; not driving'
    return result
  model = msgs.get('drivingModelData') if fresh.get('drivingModelData') else None
  big = _bool(model, 'big') if model is not None else None
  result['bigModel'] = big
  if big is True:
    result['state'], result['detail'] = 'active', 'driving model on the eGPU'
  elif big is False:
    result['state'], result['detail'] = 'error', 'backup model running on the comma'
  else:
    result['state'], result['detail'] = 'recovering', 'driving model loading'
  return result


def extract(msgs, fresh, is_metric=None, seen_moving=None, fuel=None):
  """Project a fixed allowlist; missing or stale services stay null, never zero.

  msgs: service -> capnp reader (or None); fresh: service -> bool. seen_moving: the caller's v2.1 track memory
  (a fresh dict when omitted); fuel: the v2.2 object from FuelTrip.value(), passed through.
  """
  result = empty()
  result['isMetric'] = is_metric if isinstance(is_metric, bool) else None
  device = msgs.get('deviceState') if fresh.get('deviceState') else None
  state = msgs.get('selfdriveState') if fresh.get('selfdriveState') else None
  car_state = msgs.get('carState') if fresh.get('carState') else None
  onroad = _bool(device, 'started') if device is not None else None
  result['onroad'] = onroad

  if state is not None:
    result['engaged'] = _bool(state, 'enabled')
    result['active'] = _bool(state, 'active')
    result['engageable'] = _bool(state, 'engageable')
    result['status'] = STATUS_NAMES.get(_enum(state, 'state'))
    result['alert'] = _alert(state)
    result['experimental'] = _bool(state, 'experimentalMode')
    personality = _enum(state, 'personality')
    result['personality'] = personality if personality in PERSONALITIES else None

  if car_state is not None:
    v_ego = finite(_field(car_state, 'vEgo'))
    result['vEgo'] = v_ego
    result['vCruise'] = _speed_kph(_field(car_state, 'vCruise'))
    result['vCruiseCluster'] = _speed_kph(_field(car_state, 'vCruiseCluster'))
    result['available'] = _bool(_field(car_state, 'cruiseState'), 'available')
    left, right = _bool(car_state, 'leftBlinker'), _bool(car_state, 'rightBlinker')
    if left is not None and right is not None:
      result['blinker'] = 'both' if left and right else 'left' if left else 'right' if right else 'none'
    result['gear'] = _enum(car_state, 'gearShifter')

  if fresh.get('radarState'):
    result['lead'] = _lead(msgs.get('radarState'))
  result['steering'] = _steering(msgs, fresh, result['active'])

  if fresh.get('slcState'):
    slc = msgs.get('slcState')
    result['slc'] = _slc(slc)
    if result['personality'] is not None and _field(_field(slc, 'trafficMode'), 'effective') is True:
      result['personality'] = 'traffic'
  result['egpu'] = _egpu(msgs, fresh, onroad)
  if fresh.get('peripheralState'):
    mv = finite(_field(msgs.get('peripheralState'), 'voltage'))
    if mv is not None and BATTERY_MV_RANGE[0] <= mv <= BATTERY_MV_RANGE[1]:
      result['batteryVolts'] = round(mv / 1000, 2)
  if fresh.get('modelV2'):
    result['model'] = _model(msgs.get('modelV2'))
  if fresh.get('mapdOut'):
    result['road'] = _road(msgs.get('mapdOut'))
  if fresh.get('radarTracks') and result['vEgo'] is not None:
    result['tracks'] = tracks(msgs.get('radarTracks'), result['vEgo'], {} if seen_moving is None else seen_moving)
  result['fuel'] = fuel if isinstance(fuel, dict) else None
  return result


def core_fresh(values, fresh):
  """The snapshot is current when the device heartbeat is fresh and, onroad, the car and selfdrive state are too."""
  if not fresh.get('deviceState'):
    return False
  return values.get('onroad') is not True or bool(fresh.get('selfdriveState') and fresh.get('carState'))


@dataclass(frozen=True)
class HudReading:
  values: dict
  fresh: bool
  source_age_seconds: float | None
  signature: tuple[int, ...]


def _read_params():
  try:
    from openpilot.common.params import Params
    return Params()
  except Exception:
    return None


# Survives worker restarts (the worker exits 6 s after the last request): one drive = one fuel trip.
FUEL = FuelTrip()


class MessagingHudReader:
  def __init__(self):
    from openpilot.cereal import messaging

    self.messaging = messaging
    self.started_ns = time.monotonic_ns()
    self.boot_offset_ns = paired_boot_offset_ns()
    self.sm = messaging.SubMaster(list(SERVICES))
    self.seen_moving = {}
    self.fuel = FUEL
    self.can_sock = None
    self.params = _read_params()
    self.is_metric = None
    self.car_params = None
    self.car_params_at = None
    if self.params is not None:
      try:
        self.is_metric = bool(self.params.get_bool('IsMetric'))
      except Exception:
        self.is_metric = None

  def _cached_car_params(self, now):
    """CarParams from Params, read at most every PARAMS_RETRY_S until the drive's copy exists."""
    if self.car_params is not None or self.params is None:
      return self.car_params
    if self.car_params_at is not None and now - self.car_params_at < PARAMS_RETRY_S:
      return None
    self.car_params_at = now
    try:
      from opendbc.car.structs import car
      raw = self.params.get('CarParams')
      self.car_params = self.messaging.log_from_bytes(raw, car.CarParams) if raw else None
    except Exception:
      self.car_params = None
    return self.car_params

  def sample(self, now: float):
    sm = self.sm
    if sm is None:
      raise OSError('HUD reader closed')
    sm.update(0)
    now = time.monotonic()
    current_offset = paired_boot_offset_ns()
    clock_ok = True
    if getattr(time, 'CLOCK_BOOTTIME', None) is not None:
      if current_offset is None:
        clock_ok = False
      elif self.boot_offset_ns is None or abs(current_offset - self.boot_offset_ns) > CLOCK_PAIR_MAX_SKEW_NS:
        # An old queued message can look MONOTONIC-fresh just after resume.
        self.started_ns = time.monotonic_ns()
        self.boot_offset_ns = current_offset
        clock_ok = False
    ages = {}
    fresh = {}
    for key in SERVICES:
      if key in STATIC_SERVICES:
        fresh[key] = bool(sm.seen[key] and sm.valid[key])
        continue
      event_ns = sm.logMonoTime[key]
      event_age = now - event_ns / 1e9
      receipt_age = now - sm.recv_time[key]
      limit = MAX_AGE_S.get(key, SOURCE_MAX_AGE_S)
      accepted = bool(
        clock_ok
        and sm.valid[key]
        and sm.seen[key]
        and sm.recv_time[key] > 0
        and event_ns > self.started_ns
        and 0 <= receipt_age <= limit
        and 0 <= event_age <= limit
      )
      if accepted:
        ages[key] = max(event_age, receipt_age)
      fresh[key] = accepted
    msgs = {key: sm[key] if fresh[key] else None for key in SERVICES}
    if not fresh['carParams']:
      onroad = fresh['deviceState'] and _bool(sm['deviceState'], 'started') is True
      cached = self._cached_car_params(now) if onroad else None
      msgs['carParams'], fresh['carParams'] = cached, cached is not None
    fuel = None
    if self._fuel_car(msgs['carParams']):
      device = msgs['deviceState']
      onroad = _bool(device, 'started') if device is not None else None
      car_state = msgs['carState']
      v_ego = finite(_field(car_state, 'vEgo')) if car_state is not None else None
      self.fuel.update(self._fuel_count() if onroad else None, v_ego, now, onroad)
      fuel = self.fuel.value()
    values = extract(msgs, fresh, self.is_metric, self.seen_moving, fuel)
    current = core_fresh(values, fresh)
    core = ('selfdriveState', 'carState') if values['onroad'] else ('deviceState',)
    source_age = max(ages[key] for key in core) if current else None
    signature = tuple(sm.logMonoTime[key] if key in ages else 0 for key in SERVICES)
    return HudReading(values, current, source_age, signature)

  def _fuel_car(self, car_params):
    return car_params is not None and _text(car_params, 'carFingerprint', 60) == FUEL_CAR

  def _fuel_count(self):
    """Drain the raw (non-conflated) CAN queue and return the newest 0x324 counter, or None."""
    try:
      if self.can_sock is None:
        self.can_sock = self.messaging.sub_sock('can', conflate=False)
      batches = []
      for raw in self.messaging.drain_sock_raw(self.can_sock)[-FUEL_SCAN_BATCHES:]:
        event = self.messaging.log_from_bytes(raw)
        if event.which() == 'can':
          batches.append(event.can)
      return fuel_count(batches)
    except Exception:
      return None

  def close(self):
    self.sm = None
    self.params = None
    self.can_sock = None


class Hud:
  def __init__(self, reader_factory=MessagingHudReader, clock=time.monotonic):
    self.reader_factory = reader_factory
    self.session_id = secrets.token_hex(8)
    self.clock = clock
    self.lock = threading.Lock()
    self.stop_event = threading.Event()
    self.worker = None
    self.last_request = 0.0
    self.last_sample = 0.0
    self.source_age_seconds = None
    self.signature = None
    self.seq = 0
    self.values = None
    self.current = False
    self.error = ''
    self.closed = False

  def snapshot(self):
    now = self.clock()
    with self.lock:
      if self.closed:
        raise OSError('HUD closed')
      self.last_request = now
      if self.worker is None or not self.worker.is_alive():
        self.stop_event.clear()
        self.worker = threading.Thread(target=self._run, daemon=True, name='galaxy-hud')
        self.worker.start()
      sample_age = max(0.0, now - self.last_sample) if self.last_sample else None
      age = sample_age + self.source_age_seconds if sample_age is not None and self.source_age_seconds is not None else None
      expired = self.values is None or sample_age is None or sample_age > STALE_AFTER_S
      state = 'current' if not expired and self.current and age is not None and age <= STALE_AFTER_S else 'stale'
      if expired and self.error:
        state = 'unavailable'
      return {
        'schemaVersion': 2,
        'state': state,
        'sessionId': self.session_id,
        'seq': self.seq,
        'ageSeconds': math.ceil(age * 1000) / 1000 if age is not None else None,
        **(empty() if expired else self.values),
        'error': self.error if expired else '',
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
          sample_started = self.clock()
          reading = reader.sample(self.clock())
          with self.lock:
            self.values = reading.values
            self.current = reading.fresh
            self.last_sample = self.clock()
            self.source_age_seconds = (
              reading.source_age_seconds + max(0.0, self.last_sample - sample_started) if reading.source_age_seconds is not None else None
            )
            if self.signature != reading.signature:
              self.seq += 1
            self.signature = reading.signature
            self.error = ''
        except Exception as error:
          with self.lock:
            self.values = None
            self.current = False
            self.source_age_seconds = None
            self.error = type(error).__name__
        self.stop_event.wait(SAMPLE_INTERVAL_S)
    except Exception as error:
      with self.lock:
        self.values = None
        self.current = False
        self.source_age_seconds = None
        self.error = type(error).__name__
    finally:
      if reader is not None:
        try:
          reader.close()
        except Exception:
          pass
      with self.lock:
        self.values = None
        self.current = False
        self.last_sample = 0.0
        self.source_age_seconds = None
        self.signature = None
        self.worker = None

  def close(self):
    with self.lock:
      self.closed = True
      self.stop_event.set()
      worker = self.worker
    if worker is not None:
      worker.join(timeout=0.25)
