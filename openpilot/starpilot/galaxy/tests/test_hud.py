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
from openpilot.starpilot.galaxy.hud import (SERVICES, TI_SAFETY_PARAM, FuelTrip, Hud, HudReading, MessagingHudReader, empty, extract,
                                           fuel_count, ti_car, tracks)
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
  lead.yRel, lead.radarTrackId = 0.5, 7
  events.update(overrides)
  msgs = {name: getattr(msg.as_reader(), name) if msg is not None else None for name, msg in events.items()}
  msgs['carParams'] = car_params(36 | 512 | 4096)
  fresh = {name: msgs.get(name) is not None for name in SERVICES}
  return msgs, fresh


def model_event(probs=(0.4, 0.9, 0.9, 0.3), stds=(0.6, 0.7)):
  msg = messaging.new_message('modelV2', valid=True)
  model = msg.modelV2
  xs = [i * 4.0 for i in range(33)]
  for name, count, offsets in (('laneLines', 4, (-5.4, -1.8, 1.8, 5.4)), ('roadEdges', 2, (-7.0, 7.5))):
    lines = model.init(name, count)
    for line, y in zip(lines, offsets, strict=True):
      line.x = xs
      line.y = [y + 0.001 * x for x in xs]
      line.z = [0.0] * 33
  model.laneLineProbs = list(probs)
  model.roadEdgeStds = list(stds)
  model.position.x = xs
  model.position.y = [0.002 * x for x in xs]
  model.position.z = [0.0] * 33
  return msg


def radar_tracks_event(points):
  msg = messaging.new_message('radarTracks', valid=True)
  out = msg.radarTracks.init('points', len(points))
  for point, (track_id, d_rel, y_rel, v_rel) in zip(out, points, strict=True):
    point.trackId, point.dRel, point.yRel, point.vRel = track_id, d_rel, y_rel, v_rel
  return msg


class HudV2Test(unittest.TestCase):
  def test_model_road_and_tracks(self):
    msgs, fresh = drive(modelV2=model_event(), mapdOut=event('mapdOut', lanes=3, estimatedRoadWidth=11.1, roadName='NY-347'),
                        radarTracks=radar_tracks_event([(5, 60.0, 3.4, -2.0), (4, 30.0, 0.2, -1.0)]))
    out = extract(msgs, fresh, is_metric=False)
    self.assertEqual(set(out), set(empty()))
    model = out['model']
    self.assertEqual([len(line) for line in model['laneLines']], [14] * 4)
    self.assertEqual([len(edge) for edge in model['roadEdges']], [14] * 2)
    self.assertEqual(model['laneLines'][1][0], [0.0, -1.8])
    self.assertEqual(model['laneLines'][1][13], [104.0, -1.7])   # grid point 26 (x 104 m here)
    self.assertEqual((model['laneLineProbs'], model['roadEdgeStds']), ([0.4, 0.9, 0.9, 0.3], [0.6, 0.7]))
    self.assertEqual(len(model['path']), 14)
    self.assertEqual(out['road'], {'lanes': 3, 'width': 11.1, 'name': 'NY-347'})
    self.assertEqual([t['id'] for t in out['tracks']], [4, 5])   # sorted by distance
    self.assertEqual(out['tracks'][1], {'id': 5, 'dRel': 60.0, 'yRel': -3.4, 'vRel': -2.0, 'vLead': 27.0, 'stopped': False})
    self.assertIsNone(out['fuel'])
    json.dumps(out)

  def test_v2_fields_null_when_absent_stale_or_short(self):
    msgs, fresh = drive()
    out = extract(msgs, fresh)
    self.assertEqual((out['model'], out['road'], out['tracks'], out['fuel']), (None, None, None, None))
    short = messaging.new_message('modelV2', valid=True)
    lines = short.modelV2.init('laneLines', 4)
    for line in lines:
      line.x, line.y = [1.0] * 5, [0.0] * 5
    msgs, fresh = drive(modelV2=short)
    self.assertIsNone(extract(msgs, fresh)['model'])
    msgs, fresh = drive(modelV2=model_event(), mapdOut=event('mapdOut', lanes=0, estimatedRoadWidth=0.0, roadName=''))
    fresh['modelV2'] = False
    out = extract(msgs, fresh)
    self.assertIsNone(out['model'])
    self.assertEqual(out['road'], {'lanes': None, 'width': None, 'name': None})

  def test_tracks_filter(self):
    seen = {}
    v_ego = 25.0
    msg = radar_tracks_event([
      (1, 40.0, 0.0, -1.0),      # moving with us -> kept
      (2, 30.0, 3.5, -25.0),     # never-moving return (sign, parked car) -> dropped
      (3, 50.0, -3.5, -55.0),    # oncoming -> dropped
      (4, 0.5, 0.0, 0.0),        # too close
      (5, 160.0, 0.0, 0.0),      # too far
      (6, 30.0, 13.0, 0.0),      # too wide
    ]).radarTracks
    out = tracks(msg, v_ego, seen)
    self.assertEqual([t['id'] for t in out], [1])
    self.assertEqual(set(seen), {1, 4, 5, 6})   # moving ids are remembered even when filtered out by range
    # id 1 brakes to a stop (a queue at a light): still shown, as stopped
    out = tracks(radar_tracks_event([(1, 20.0, 0.0, -24.0)]).radarTracks, v_ego, seen)
    self.assertEqual(out, [{'id': 1, 'dRel': 20.0, 'yRel': -0.0, 'vRel': -24.0, 'vLead': 1.0, 'stopped': True}])
    self.assertEqual(set(seen), {1})   # vanished ids are forgotten
    out = tracks(radar_tracks_event([(i, 10.0 + i, 0.0, 0.0) for i in range(20)]).radarTracks, v_ego, seen)
    self.assertEqual(len(out), 16)
    self.assertIsNone(tracks(None, v_ego, seen))
    self.assertIsNone(tracks(msg, None, seen))


def frame(address, src, dat):
  return NS(address=address, src=src, dat=dat)


class FuelTest(unittest.TestCase):
  def test_counter_scan_uses_the_newest_powertrain_frame(self):
    old = [frame(0x324, 0, bytes([80, 70, 0x01, 0x00, 0, 0, 0, 0]))]
    new = [frame(0x1E7, 0, b'\x00' * 8), frame(0x324, 128, bytes([0, 0, 0xFF, 0xFF])), frame(0x324, 0, bytes([80, 70, 0x01, 0x10]))]
    self.assertEqual(fuel_count([old, [], new]), 0x0110)
    self.assertEqual(fuel_count([old] + [[]] * 12), None)   # only the newest 12 batches are scanned
    self.assertIsNone(fuel_count([[frame(0x324, 0, b'\x01\x02')]]))

  def test_trip_accumulates_only_across_short_gaps(self):
    f = FuelTrip()
    self.assertIsNone(f.value())
    f.update(1000, 30.0, 0.0, True)
    self.assertEqual(f.value()['tripMl'], 0.0)
    for i in range(1, 9):   # 2 s at 30 m/s burning 1 mL/s (10 counts/s)
      f.update(1000 + i * 2.5, 30.0, i * 0.25, True)
    v = f.value()
    self.assertEqual((v['tripMl'], v['tripM'], v['rateMlS']), (2.0, 60, 1.0))
    self.assertAlmostEqual(v['instMpg'], (60 / 1609.344) / (2 / 3785.41), delta=0.1)
    self.assertIsNone(v['avgMpg'])   # under 400 m
    f.update(1100, 30.0, 10.0, True)   # 8 s gap: re-baselines, adds nothing
    self.assertEqual((f.value()['tripMl'], f.value()['tripM']), (2.0, 60))

  def test_wrap_ignition_reset_offroad_and_caps(self):
    f = FuelTrip()
    f.update(65_530, 20.0, 0.0, True)
    f.update(4, 20.0, 0.25, True)   # wrapped: +10 counts
    self.assertEqual(f.value()['tripMl'], 1.0)
    f.update(2, 20.0, 0.5, True)   # small drop = the car reset the counter (new ignition)
    self.assertEqual((f.value()['tripMl'], f.value()['tripM']), (0.0, 0))
    f.update(2, 20.0, 0.75, True)   # coasting: fuel cut
    f.update(2, 20.0, 1.0, True)
    self.assertEqual(f.value()['instMpg'], 99.9)
    f.update(2, 0.0, 1.1, None)   # device state unknown: keep the trip
    self.assertIsNotNone(f.value())
    f.update(2, 0.0, 1.25, False)   # offroad: next drive starts fresh
    self.assertIsNone(f.value())
    f.update(10, 0.5, 2.0, True)
    f.update(12, 0.5, 2.25, True)
    self.assertIsNone(f.value()['instMpg'])   # crawling / stopped: no instant mpg

  def test_average_and_history_buckets(self):
    f = FuelTrip()
    t, count = 0.0, 0
    f.update(count, 30.0, t, True)
    for _ in range(int(60 / 0.25)):   # 60 s at 30 m/s (1.12 mi), 1.5 mL/s
      t += 0.25
      count += 3.75
      f.update(int(count), 30.0, t, True)
    v = f.value()
    self.assertAlmostEqual(v['avgMpg'], (1800 / 1609.344) / (v['tripMl'] / 3785.41), delta=0.1)
    self.assertTrue(30 < v['avgMpg'] < 50)
    self.assertEqual(len(v['hist']), 4)
    self.assertTrue(all(0.24 < b - a < 0.3 for a, b in zip([0.0] + [h[0] for h in v['hist']], [h[0] for h in v['hist']])))
    json.dumps(v)

  def test_fuel_only_read_on_the_accord_9g(self):
    reader = MessagingHudReader.__new__(MessagingHudReader)
    nine = car.CarParams.new_message(carFingerprint='HONDA_ACCORD_9G').as_reader()
    civic = car.CarParams.new_message(carFingerprint='HONDA_CIVIC').as_reader()
    self.assertTrue(reader._fuel_car(nine))
    self.assertFalse(reader._fuel_car(civic))
    self.assertFalse(reader._fuel_car(None))


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
    self.assertEqual(out['lead'], {'status': True, 'dRel': 41.5, 'vRel': -1.25, 'vLead': 27.75, 'radar': True,
                                   'yRel': -0.5, 'trackId': 7})
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
        self.assertEqual((current['state'], current['onroad'], current['schemaVersion']), ('current', False, 2))
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
        self.assertEqual((status, json.loads(body)['schemaVersion']), (200, 1))   # the fake snapshot above
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
        return self.data.get(key)

    reader = object.__new__(MessagingHudReader)
    reader.sm = Cached()
    reader.seen_moving, reader.fuel, reader.can_sock = {}, FuelTrip(), None
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
