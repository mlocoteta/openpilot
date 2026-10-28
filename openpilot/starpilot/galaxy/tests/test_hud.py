"""HUD projection, bounded worker, actual IPC and authenticated HTTP."""

import http.client
import json
from pathlib import Path
from types import SimpleNamespace as NS
import tempfile
import threading
import time
import unittest
import uuid
from unittest import mock

from opendbc.car.structs import car
from openpilot.cereal import messaging
from openpilot.starpilot.galaxy.access import GalaxyAccessOwner
from openpilot.starpilot.galaxy.hud import SERVICES, TI_SAFETY_PARAM, Hud, HudReading, MessagingHudReader, empty, extract, ti_car
from openpilot.starpilot.galaxy.server import make_server

CONTRACT_KEYS = {'schemaVersion', 'state', 'sessionId', 'seq', 'ageSeconds', 'error', *empty()}


def event(service, **fields):
  msg = messaging.new_message(service, valid=True)
  body = getattr(msg, service)
  for name, value in fields.items():
    if isinstance(value, dict):
      child = getattr(body, name)
      for child_name, child_value in value.items():
        setattr(child, child_name, child_value)
    else:
      setattr(body, name, value)
  return msg


def car_params(safety_param, brand='honda', model='hondaNidec'):
  params = car.CarParams.new_message()
  params.brand = brand
  config = params.init('safetyConfigs', 1)[0]
  config.safetyModel = model
  config.safetyParam = safety_param
  return params.as_reader()


def drive(**overrides):
  events = {
    'deviceState': event('deviceState', started=True, chestnutPresent=True),
    'selfdriveState': event('selfdriveState', enabled=True, active=True, engageable=True, state='enabled',
                            experimentalMode=False, personality='standard', alertSize='none'),
    'carState': event('carState', vEgo=29.0, vCruise=112.65408, vCruiseCluster=112.0, leftBlinker=False, rightBlinker=True,
                      gearShifter='drive', cruiseState={'available': True, 'enabled': True}),
    'carControl': event('carControl', latActive=True, longActive=True),
    'radarState': event('radarState'),
    'slcState': event('slcState', enabled=True, observationKind='valid', source='map', speedLimit=24.5872, offset=2.2352,
                      hasCeiling=True, effectiveCap=26.8224, status='active'),
    'chestnutState': event('chestnutState', tempC=61.0, supplyVoltage=14100),
    'drivingModelData': event('drivingModelData', big=True),
    'peripheralState': event('peripheralState', voltage=12_640),
  }
  lead = events['radarState'].radarState.leadOne
  lead.present, lead.dRel, lead.vRel, lead.vLead, lead.radar = True, 41.5, -1.25, 27.75, True
  events.update(overrides)
  msgs = {name: getattr(msg.as_reader(), name) if msg is not None else None for name, msg in events.items()}
  msgs['carParams'] = car_params(36 | 512 | 4096)
  fresh = {name: msgs.get(name) is not None for name in SERVICES}
  return msgs, fresh


class HudProjectionTest(unittest.TestCase):
  def test_engaged_highway_projection(self):
    msgs, fresh = drive()
    out = extract(msgs, fresh, is_metric=False)
    self.assertEqual(set(out), set(empty()))
    self.assertEqual((out['onroad'], out['isMetric'], out['engaged'], out['active'], out['available'], out['status']),
                     (True, False, True, True, True, 'engaged'))
    self.assertAlmostEqual(out['vEgo'], 29.0)
    self.assertAlmostEqual(out['vCruise'], 31.2928, places=3)  # 70 mph set
    self.assertAlmostEqual(out['vCruiseCluster'], 31.1111, places=3)
    self.assertEqual(out['lead'], {'status': True, 'dRel': 41.5, 'vRel': -1.25, 'vLead': 27.75, 'radar': True})
    self.assertEqual(out['steering'], {'latActive': True, 'source': 'ti', 'detail': 'steering', 'fault': False})
    self.assertIsNone(out['alert'])
    self.assertEqual((out['experimental'], out['personality'], out['blinker'], out['gear']), (False, 'standard', 'right', 'drive'))
    self.assertAlmostEqual(out['slc']['limit'], 24.5872, places=3)
    self.assertAlmostEqual(out['slc']['target'], 26.8224, places=3)
    self.assertEqual((out['slc']['source'], out['slc']['state'], out['slc']['pending']), ('map', 'active', None))
    self.assertEqual(out['egpu']['state'], 'active')
    self.assertEqual(out['egpu']['supplyVolts'], 14.1)
    self.assertEqual(out['batteryVolts'], 12.64)
    json.dumps(out)

  def test_battery_volts_bad_read_is_null(self):
    msgs, fresh = drive(peripheralState=event('peripheralState', voltage=0))
    self.assertIsNone(extract(msgs, fresh)['batteryVolts'])
    msgs, fresh = drive()
    fresh['peripheralState'] = False
    self.assertIsNone(extract(msgs, fresh)['batteryVolts'])

  def test_null_on_missing_or_stale(self):
    msgs, fresh = drive()
    out = extract(msgs, dict.fromkeys(SERVICES, False))
    self.assertEqual(out, empty())
    self.assertIsNone(extract({}, {})['vEgo'])
    # A stale carState hides speed/cruise/gear but leaves fresh selfdrive fields.
    fresh['carState'] = False
    out = extract(msgs, fresh)
    self.assertIsNone(out['vEgo'])
    self.assertIsNone(out['vCruise'])
    self.assertIsNone(out['blinker'])
    self.assertIsNone(out['gear'])
    self.assertIsNone(out['steering']['fault'])
    self.assertTrue(out['engaged'])
    # Fresh but default (zero) speeds are real; only the cruise sentinel/unset becomes null.
    msgs, fresh = drive(carState=event('carState', vEgo=0.0, vCruise=0.0, vCruiseCluster=0.0))
    out = extract(msgs, fresh)
    self.assertEqual(out['vEgo'], 0.0)
    self.assertIsNone(out['vCruise'])
    self.assertIsNone(out['vCruiseCluster'])

  def test_cruise_unset_sentinel(self):
    msgs, fresh = drive(carState=event('carState', vEgo=0.0, vCruise=255.0, vCruiseCluster=255.0, gearShifter='park'))
    out = extract(msgs, fresh)
    self.assertIsNone(out['vCruise'])
    self.assertIsNone(out['vCruiseCluster'])
    self.assertEqual(out['gear'], 'park')
    self.assertEqual(out['blinker'], 'none')
    msgs, fresh = drive(carState=event('carState', vCruise=float('nan')))
    self.assertIsNone(extract(msgs, fresh)['vCruise'])

  def test_alert_and_status_mapping(self):
    state = event('selfdriveState', enabled=True, active=False, state='preEnabled', alertText1='TAKE CONTROL',
                  alertText2='Steering Temporarily Unavailable', alertStatus='userPrompt', alertSize='mid', alertType='steerTempUnavailable/warning')
    out = extract(*drive(selfdriveState=state))
    self.assertEqual(out['alert'], {'text1': 'TAKE CONTROL', 'text2': 'Steering Temporarily Unavailable', 'status': 'userPrompt',
                                    'size': 'mid', 'type': 'steerTempUnavailable/warning'})
    self.assertEqual((out['engaged'], out['active'], out['status']), (True, False, 'preEnabled'))
    for name, expected in (('disabled', 'disengaged'), ('softDisabling', 'softDisabling'), ('overriding', 'overriding')):
      self.assertEqual(extract(*drive(selfdriveState=event('selfdriveState', state=name)))['status'], expected)
    # Size none or empty text -> no alert.
    self.assertIsNone(extract(*drive(selfdriveState=event('selfdriveState', alertText1='x', alertSize='none')))['alert'])
    self.assertIsNone(extract(*drive(selfdriveState=event('selfdriveState', alertSize='small')))['alert'])
    critical = extract(*drive(selfdriveState=event('selfdriveState', alertText1='DISENGAGE', alertStatus='critical', alertSize='full')))
    self.assertEqual((critical['alert']['status'], critical['alert']['size'], critical['alert']['text2']), ('critical', 'full', ''))

  def test_lead_absent(self):
    out = extract(*drive(radarState=event('radarState')))
    self.assertIsNone(out['lead'])
    msgs, fresh = drive()
    fresh['radarState'] = False
    self.assertIsNone(extract(msgs, fresh)['lead'])

  def test_ti_mapping(self):
    self.assertEqual(TI_SAFETY_PARAM, 4096)
    try:
      from opendbc.car.honda.values import HondaSafetyFlags
    except ImportError:
      pass
    else:
      self.assertEqual(int(HondaSafetyFlags.TORQUE_INTERCEPTOR), TI_SAFETY_PARAM)
    self.assertTrue(ti_car(car_params(36 | 4096)))
    self.assertFalse(ti_car(car_params(36 | 512)))
    self.assertFalse(ti_car(car_params(4096, brand='toyota', model='toyota')))
    self.assertIsNone(ti_car(None))

    msgs, fresh = drive(carState=event('carState', steerFaultTemporary=True))
    steering = extract(msgs, fresh)['steering']
    self.assertEqual(steering, {'latActive': True, 'source': 'ti', 'detail': 'TI lockout or EPS fault', 'fault': True})
    msgs['carParams'] = car_params(36 | 512)
    self.assertEqual(extract(msgs, fresh)['steering']['source'], 'lkas')
    self.assertEqual(extract(msgs, fresh)['steering']['detail'], 'temporary fault')
    fresh['carParams'] = False
    self.assertEqual(extract(msgs, fresh)['steering']['source'], 'unknown')

    # Always-on lateral: steering without openpilot engaged.
    aol = extract(*drive(selfdriveState=event('selfdriveState', enabled=False, active=False, state='disabled'),
                         carControl=event('carControl', latActive=True)))
    self.assertEqual((aol['engaged'], aol['steering']['latActive'], aol['steering']['detail']), (False, True, 'always-on lateral'))
    standby = extract(*drive(carControl=event('carControl', latActive=False)))['steering']
    self.assertEqual(standby['detail'], 'standby')
    permanent = extract(*drive(carState=event('carState', steerFaultPermanent=True)))['steering']
    self.assertEqual((permanent['fault'], permanent['detail']), (True, 'permanent fault'))

  def test_egpu_mapping(self):
    self.assertEqual(extract(*drive())['egpu']['state'], 'active')
    self.assertEqual(extract(*drive(drivingModelData=event('drivingModelData', big=False)))['egpu']['state'], 'error')
    loading = extract(*drive(drivingModelData=None))['egpu']
    self.assertEqual((loading['state'], loading['bigModel']), ('recovering', None))
    absent = extract(*drive(deviceState=event('deviceState', started=True, chestnutPresent=False),
                            chestnutState=event('chestnutState', supplyVoltage=0)))['egpu']
    self.assertEqual((absent['state'], absent['detail'], absent['supplyVolts']), ('absent', 'not on USB, no 12 V input', 0.0))
    self.assertEqual(extract(*drive(deviceState=event('deviceState', started=True), chestnutState=None))['egpu']['detail'], 'not detected on USB')
    fault = extract(*drive(chestnutState=event('chestnutState', supplyFault=True, supplyVoltage=9000)))['egpu']
    self.assertEqual(fault['state'], 'error')
    parked = extract(*drive(deviceState=event('deviceState', started=False, chestnutPresent=True)))['egpu']
    self.assertEqual((parked['state'], parked['detail']), ('unknown', 'detected; not driving'))
    self.assertIsNone(extract(*drive(deviceState=None))['egpu'])

  def test_slc_and_personality(self):
    pending = event('slcState', enabled=True, observationKind='valid', source='dashboard', speedLimit=29.0576, hasPending=True,
                    pendingSpeedLimit=29.0576, status='pending', offset=0.0)
    slc = extract(*drive(slcState=pending))['slc']
    self.assertEqual((slc['source'], slc['state'], slc['target']), ('dashboard', 'pending', None))
    self.assertAlmostEqual(slc['pending'], 29.0576, places=3)
    stale_obs = extract(*drive(slcState=event('slcState', enabled=True, observationKind='stale', speedLimit=20.0, lastReceivedSpeedLimit=20.0)))['slc']
    self.assertEqual((stale_obs['limit'], stale_obs['source'], stale_obs['offset'], stale_obs['kind']), (None, None, None, 'stale'))
    self.assertAlmostEqual(stale_obs['lastLimit'], 20.0)
    self.assertIsNone(extract(*drive(slcState=event('slcState', enabled=False, observationKind='valid', speedLimit=20.0)))['slc'])
    traffic = event('slcState', enabled=True)
    traffic.slcState.trafficMode.effective = True
    self.assertEqual(extract(*drive(slcState=traffic))['personality'], 'traffic')
    self.assertEqual(extract(*drive(selfdriveState=event('selfdriveState', personality='relaxed')))['personality'], 'relaxed')

  def test_offroad_device_only(self):
    msgs = {'deviceState': event('deviceState', started=False, chestnutPresent=False).deviceState}
    out = extract(msgs, {'deviceState': True})
    self.assertEqual((out['onroad'], out['engaged'], out['egpu']['state']), (False, None, 'absent'))

  def test_namespace_inputs_and_bad_types(self):
    msgs = {'carState': NS(vEgo='x', vCruise=None, leftBlinker=1, rightBlinker=False, cruiseState=None, gearShifter=None)}
    out = extract(msgs, {'carState': True})
    self.assertIsNone(out['vEgo'])
    self.assertIsNone(out['blinker'])
    self.assertIsNone(out['available'])


class HudWorkerTest(unittest.TestCase):
  def test_worker_idle_exit_and_restart(self):
    readers = []

    class Reader:
      def __init__(self):
        self.closed = False
        self.calls = 0
        readers.append(self)

      def sample(self, now):
        self.calls += 1
        return HudReading({**empty(), 'onroad': False}, True, 0.0, (self.calls // 3,))

      def close(self):
        self.closed = True

    source = Hud(reader_factory=Reader)
    with mock.patch('openpilot.starpilot.galaxy.hud.SAMPLE_INTERVAL_S', 0.01), mock.patch('openpilot.starpilot.galaxy.hud.CLIENT_IDLE_S', 0.06):
      try:
        first = source.snapshot()
        self.assertEqual(set(first), CONTRACT_KEYS)
        deadline = time.monotonic() + 1
        while source.snapshot()['state'] != 'current' and time.monotonic() < deadline:
          time.sleep(0.005)
        current = source.snapshot()
        self.assertEqual((current['state'], current['onroad'], current['schemaVersion']), ('current', False, 1))
        self.assertGreaterEqual(current['seq'], 1)
        time.sleep(0.15)
        self.assertTrue(readers[0].closed)
        self.assertIsNone(source.worker)
        idle = source.snapshot()
        self.assertEqual(idle['state'], 'stale')
        self.assertIsNone(idle['onroad'])
        deadline = time.monotonic() + 1
        while len(readers) < 2 and time.monotonic() < deadline:
          time.sleep(0.005)
        self.assertEqual(len(readers), 2)
      finally:
        source.close()
    self.assertTrue(readers[-1].closed)

  def test_reader_error_is_unavailable(self):
    class Broken:
      def __init__(self):
        raise OSError('no ipc')

    source = Hud(reader_factory=Broken)
    try:
      source.snapshot()
      deadline = time.monotonic() + 1
      while source.snapshot()['state'] != 'unavailable' and time.monotonic() < deadline:
        time.sleep(0.005)
      result = source.snapshot()
      self.assertEqual((result['state'], result['error'], result['vEgo']), ('unavailable', 'OSError', None))
    finally:
      source.close()

  def test_snapshot_ages_out_without_new_samples(self):
    now = [100.0]

    class Reader:
      def sample(self, timestamp):
        return HudReading({**empty(), 'onroad': True, 'vEgo': 12.0}, True, 0.2, (1,))

      def close(self):
        pass

    source = Hud(reader_factory=Reader, clock=lambda: now[0])
    with mock.patch('openpilot.starpilot.galaxy.hud.SAMPLE_INTERVAL_S', 5.0):
      try:
        source.snapshot()
        deadline = time.monotonic() + 1
        while source.snapshot()['state'] != 'current' and time.monotonic() < deadline:
          time.sleep(0.005)
        self.assertEqual(source.snapshot()['vEgo'], 12.0)
        self.assertAlmostEqual(source.snapshot()['ageSeconds'], 0.2, places=2)
        now[0] += 1.4
        aged = source.snapshot()
        self.assertEqual((aged['state'], aged['vEgo']), ('stale', 12.0))
        now[0] += 0.2
        expired = source.snapshot()
        self.assertEqual((expired['state'], expired['vEgo']), ('stale', None))
      finally:
        source.close()


class HudHttpTest(unittest.TestCase):
  def test_typed_ipc_through_authenticated_http(self):
    messaging.set_fake_prefix('galaxy_hud_http_' + uuid.uuid4().hex)
    with tempfile.TemporaryDirectory() as directory:
      owner = GalaxyAccessOwner(Path(directory) / 'access')
      owner.configure('password123', lambda: True)
      with mock.patch('openpilot.starpilot.galaxy.hud._read_params', return_value=None):
        source = Hud()
        server = make_server(port=0, owner=owner, hud=source)
      server_thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
      server_thread.start()
      publisher = messaging.PubMaster(['deviceState', 'selfdriveState', 'carState', 'carControl', 'drivingModelData', 'carParams'])

      def request(path, method='GET', body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=2)
        try:
          connection.request(method, path, body=body, headers={'Forwarded': 'for=203.0.113.8', **(headers or {})})
          response = connection.getresponse()
          return response.status, json.loads(response.read()), dict(response.getheaders())
        finally:
          connection.close()

      try:
        self.assertEqual(request('/api/hud')[0], 401)
        self.assertIsNone(source.worker)
        origin = f'http://127.0.0.1:{server.server_port}'
        status, _, headers = request('/api/auth/login', 'POST', json.dumps({'password': 'password123'}), {'Content-Type': 'application/json', 'Origin': origin})
        self.assertEqual(status, 200)
        cookie = headers['Set-Cookie'].split(';', 1)[0]
        status, first, headers = request('/api/hud', headers={'Cookie': cookie})
        self.assertEqual((status, first['state'], headers['Cache-Control']), (200, 'stale', 'no-store'))
        self.assertEqual(set(first), CONTRACT_KEYS)
        cp = messaging.new_message('carParams', valid=True)
        cp.carParams.brand = 'honda'
        config = cp.carParams.init('safetyConfigs', 1)[0]
        config.safetyModel = 'hondaNidec'
        config.safetyParam = 36 | 4096
        events = [
          ('deviceState', event('deviceState', started=True, chestnutPresent=True)),
          ('selfdriveState', event('selfdriveState', enabled=True, active=True, state='enabled', personality='relaxed')),
          ('carState', event('carState', vEgo=20.0, vCruise=255.0, gearShifter='drive')),
          ('carControl', event('carControl', latActive=True)),
          ('drivingModelData', event('drivingModelData', big=True)),
          ('carParams', cp),
        ]
        deadline = time.monotonic() + 3
        result = None
        while time.monotonic() < deadline:
          for name, msg in events:
            msg.clear_write_flag()
            publisher.send(name, msg)
          _, result, _ = request('/api/hud', headers={'Cookie': cookie})
          if result['state'] == 'current' and result['steering']['source'] == 'ti' and result['egpu'] is not None:
            break
          time.sleep(0.05)
        assert result is not None
        self.assertEqual(result['state'], 'current')
        self.assertEqual(set(result), CONTRACT_KEYS)
        self.assertEqual((result['onroad'], result['engaged'], result['status'], result['personality']), (True, True, 'engaged', 'relaxed'))
        self.assertEqual((result['vEgo'], result['vCruise'], result['gear']), (20.0, None, 'drive'))
        self.assertEqual(result['steering'], {'latActive': True, 'source': 'ti', 'detail': 'steering', 'fault': False})
        self.assertEqual(result['egpu']['state'], 'active')
        self.assertIsNone(result['lead'])
        self.assertIsNone(result['slc'])
        self.assertGreaterEqual(result['seq'], 1)
        self.assertIsNotNone(result['ageSeconds'])
        status, _, _ = request('/api/auth/logout', 'POST', '{}', {'Content-Type': 'application/json', 'Origin': origin, 'Cookie': cookie})
        self.assertEqual(status, 200)
        self.assertEqual(request('/api/hud', headers={'Cookie': cookie})[0], 401)
      finally:
        server.shutdown()
        server_thread.join(2)
        server.server_close()
        del publisher
        messaging.delete_fake_prefix()
      self.assertTrue(source.closed)

  def test_direct_local_session_cookie(self):
    """The head unit's path: GET /api/auth/session over a direct local socket, then /api/hud with the cookie."""
    snapshots = []

    class Fake:
      closed = False

      def snapshot(self):
        snapshots.append(1)
        return {'schemaVersion': 1, 'state': 'stale', 'seq': 0, **empty()}

      def close(self):
        self.closed = True

    with tempfile.TemporaryDirectory() as directory:
      owner = GalaxyAccessOwner(Path(directory) / 'access')
      fake = Fake()
      server = make_server(port=0, owner=owner, hud=fake)
      server_thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
      server_thread.start()

      def request(path, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=2)
        try:
          connection.request('GET', path, headers=headers or {})
          response = connection.getresponse()
          return response.status, response.read(), dict(response.getheaders())
        finally:
          connection.close()

      try:
        self.assertEqual(request('/api/hud')[0], 401)
        self.assertEqual(snapshots, [])
        status, _, headers = request('/api/auth/session')
        self.assertEqual(status, 200)
        cookie = headers['Set-Cookie'].split(';', 1)[0]
        self.assertTrue(cookie.startswith('galaxy_session='))
        status, body, _ = request('/api/hud', {'Cookie': cookie})
        self.assertEqual((status, json.loads(body)['schemaVersion']), (200, 1))
        # Host must name the socket's own address.
        self.assertEqual(request('/api/hud', {'Cookie': cookie, 'Host': 'comma.local:8082'})[0], 403)
      finally:
        server.shutdown()
        server_thread.join(2)
        server.server_close()
      self.assertTrue(fake.closed)

  def test_reader_rejects_events_from_before_its_start(self):
    class Cached:
      def __init__(self):
        self.seen = dict.fromkeys(SERVICES, True)
        self.valid = dict.fromkeys(SERVICES, True)
        self.recv_time = dict.fromkeys(SERVICES, 100.05)
        self.logMonoTime = dict.fromkeys(SERVICES, 100_050_000_000)
        msgs, _ = drive()
        self.data = msgs

      def update(self, timeout):
        pass

      def __getitem__(self, key):
        return self.data[key]

    reader = object.__new__(MessagingHudReader)
    reader.sm = Cached()
    reader.params = None
    reader.is_metric = True
    reader.car_params = None
    reader.car_params_at = None
    reader.boot_offset_ns = 1_000_000_000
    with (
      mock.patch.object(time, 'CLOCK_BOOTTIME', 7, create=True),
      mock.patch('openpilot.starpilot.galaxy.hud.paired_boot_offset_ns', return_value=1_000_000_000),
      mock.patch('openpilot.starpilot.galaxy.hud.time.monotonic', return_value=100.1),
    ):
      reader.started_ns = 100_000_000_000
      fresh = reader.sample(0)
      self.assertTrue(fresh.fresh)
      self.assertEqual((fresh.values['isMetric'], fresh.values['steering']['source']), (True, 'ti'))
      self.assertAlmostEqual(fresh.source_age_seconds, 0.05, places=3)
      reader.started_ns = 100_060_000_000
      old = reader.sample(0)
      self.assertFalse(old.fresh)
      self.assertIsNone(old.values['vEgo'])
      self.assertEqual(old.signature, (0,) * len(SERVICES))


if __name__ == '__main__':
  unittest.main()
