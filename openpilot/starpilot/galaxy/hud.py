"""Bounded, read-only driving snapshot for an external head-unit HUD.

Modeled on plots.py: the worker owns its IPC sockets, no subscription exists
until an authenticated request arrives, and the worker leaves after six seconds
without a viewer. Requests are served from the last cached projection. Absent or
stale inputs stay null; nothing here writes Params, files or logs.
"""

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
MAX_AGE_S = {'deviceState': 2.0, 'chestnutState': 1.5}
STATIC_SERVICES = ('carParams',)
PARAMS_RETRY_S = 10.0
SERVICES = ('deviceState', 'selfdriveState', 'carState', 'carControl', 'radarState', 'slcState',
            'chestnutState', 'drivingModelData', 'carParams')

# opendbc HondaSafetyFlags.TORQUE_INTERCEPTOR (F01): set in the Nidec safety word only when the TI drives lateral.
TI_SAFETY_PARAM = 4096
CV_KPH_TO_MS = 1 / 3.6
V_CRUISE_UNSET_KPH = 255
CHESTNUT_MIN_SUPPLY_MV = 10_000

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
  return {'status': True, 'dRel': d_rel, 'vRel': v_rel, 'vLead': v_lead, 'radar': _bool(lead, 'radar')}


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


def extract(msgs, fresh, is_metric=None):
  """Project a fixed allowlist; missing or stale services stay null, never zero.

  msgs: service -> capnp reader (or None); fresh: service -> bool.
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


class MessagingHudReader:
  def __init__(self):
    from openpilot.cereal import messaging

    self.messaging = messaging
    self.started_ns = time.monotonic_ns()
    self.boot_offset_ns = paired_boot_offset_ns()
    self.sm = messaging.SubMaster(list(SERVICES))
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
    values = extract(msgs, fresh, self.is_metric)
    current = core_fresh(values, fresh)
    core = ('selfdriveState', 'carState') if values['onroad'] else ('deviceState',)
    source_age = max(ages[key] for key in core) if current else None
    signature = tuple(sm.logMonoTime[key] if key in ages else 0 for key in SERVICES)
    return HudReading(values, current, source_age, signature)

  def close(self):
    self.sm = None
    self.params = None


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
        'schemaVersion': 1,
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
