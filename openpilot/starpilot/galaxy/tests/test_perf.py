"""Performance stream: CAN decodes, sample rows, ring buffer + since, bounded worker, actual IPC and authenticated HTTP."""

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
from openpilot.starpilot.galaxy.perf import BRAKE_PRESSURE, BUFFER_SAMPLES, FIELDS, FIRST_BATCH, POWERTRAIN_DATA, VSA_KINEMATICS, \
                                           CanLatest, Perf, PerfReading, accord_9g, empty_slow, motorola, sample_row, slow_values
from openpilot.starpilot.galaxy.server import make_server

CONTRACT_KEYS = {'schemaVersion', 'state', 'sessionId', 'seq', 'hz', 'gap', 'ageSeconds', 'decodes', 'fields', 'samples', 'slow', 'error'}


def put(dat, start, size, value):
  """Inverse of perf.motorola for building test frames."""
  msb = (start // 8) * 8 + (7 - start % 8)
  shift = len(dat) * 8 - msb - size
  whole = int.from_bytes(dat, 'big') & ~(((1 << size) - 1) << shift) | (value << shift)
  return bytearray(whole.to_bytes(len(dat), 'big'))


def vsa(yaw_raw, lat_raw, long_raw):
  dat = bytearray(8)
  dat = put(dat, 7, 10, yaw_raw)
  dat = put(dat, 19, 10, lat_raw)
  return bytes(put(dat, 25, 10, long_raw))


def powertrain(pedal, rpm, brake_pressed=0):
  dat = put(bytearray(8), 7, 8, pedal)
  dat = put(dat, 23, 16, rpm)
  return bytes(put(dat, 53, 1, brake_pressed))


def brake(raw):
  return bytes(put(bytearray(4), 7, 10, raw))


def frame(address, dat, src=0):
  return NS(address=address, dat=dat, src=src)


def accord_params(fingerprint='HONDA_ACCORD_9G', model='hondaNidec'):
  params = car.CarParams.new_message()
  params.brand = 'honda'
  params.carFingerprint = fingerprint
  config = params.init('safetyConfigs', 1)[0]
  config.safetyModel = model
  config.safetyParam = 4644
  return params


class PerfDecodeTest(unittest.TestCase):
  def test_motorola_fields(self):
    dat = bytes([0b10110011, 0b11000000, 0, 0])
    self.assertEqual(motorola(dat, 7, 10), 0b1011001111)
    self.assertEqual(motorola(dat, 7, 8), 0b10110011)
    self.assertEqual(motorola(powertrain(0, 4321), 23, 16), 4321)
    self.assertIsNone(motorola(b'\x00', 7, 10))

  def test_accord_decodes(self):
    can = CanLatest()
    can.update([frame(VSA_KINEMATICS, vsa(512 - 20, 512 - 30, 512 - 50)), frame(POWERTRAIN_DATA, powertrain(128, 2500, 1)),
                frame(BRAKE_PRESSURE, brake(102 + 150))], 1_000_000_000)
    out = can.decode(1_010_000_000)
    # Left turn: raw below 512 on yaw and lat accel = left positive after negation; long accel scale is negative.
    self.assertAlmostEqual(out['yaw'], 20 * 0.00421, places=4)
    self.assertAlmostEqual(out['ay'], 30 * 0.0467, places=3)
    self.assertAlmostEqual(out['ax'], 50 * 0.042, places=3)
    self.assertAlmostEqual(out['gas'], 128 / 255, places=3)
    self.assertEqual(out['rpm'], 2500)
    self.assertAlmostEqual(out['brake'], 0.5, places=3)

  def test_rest_values_and_clamps(self):
    can = CanLatest()
    can.update([frame(VSA_KINEMATICS, vsa(512, 512, 512)), frame(BRAKE_PRESSURE, brake(90)), frame(POWERTRAIN_DATA, powertrain(255, 0))], 0)
    out = can.decode(0)
    self.assertEqual((out['yaw'], out['ay'], out['ax'], out['brake'], out['gas']), (0, 0, 0, 0, 1.0))
    can.update([frame(BRAKE_PRESSURE, brake(1000))], 0)
    self.assertEqual(can.decode(0)['brake'], 1.0)

  def test_other_bus_stale_and_short_frames_are_null(self):
    can = CanLatest()
    can.update([frame(VSA_KINEMATICS, vsa(500, 500, 500), src=128), frame(POWERTRAIN_DATA, b'\x01')], 0)
    out = can.decode(0)
    self.assertIsNone(out['yaw'])
    self.assertIsNone(out['rpm'])
    can.update([frame(VSA_KINEMATICS, vsa(500, 500, 500))], 0)
    self.assertIsNotNone(can.decode(200_000_000)['yaw'])
    self.assertIsNotNone(can.decode(-100_000_000)['yaw'])   # CAN batch logged just after the carState
    self.assertIsNone(can.decode(400_000_000)['yaw'])
    can.update(None, 0)   # bad input is ignored, not raised
    can.update([NS(src=0)], 0)

  def test_accord_9g_gate(self):
    self.assertTrue(accord_9g(accord_params()))
    self.assertFalse(accord_9g(accord_params(fingerprint='HONDA_ACCORD')))
    self.assertFalse(accord_9g(accord_params(model='hondaBosch')))
    self.assertIsNone(accord_9g(None))
    self.assertIsNone(accord_9g(NS(brand='honda')))

  def test_sample_row_and_slow(self):
    car_state = NS(vEgo=12.5, aEgo=-1.25, steeringAngleDeg=-30.5, brakePressed=True, gearShifter='drive')
    row = sample_row(car_state, 12_345_678_900, CanLatest().decode(0))
    self.assertEqual(len(row), len(FIELDS))
    self.assertEqual(dict(zip(FIELDS, row)), {'t': 12.346, 'v': 12.5, 'a': -1.25, 'ax': None, 'ay': None, 'yaw': None, 'steer': -30.5,
                                              'gas': None, 'brake': None, 'brk': 1, 'rpm': None})
    bad = sample_row(NS(vEgo=float('nan'), aEgo='x', brakePressed=1), 0, CanLatest().decode(0))
    self.assertEqual((bad[1], bad[2], bad[6], bad[9]), (None, None, None, None))
    msgs = {'deviceState': NS(started=True), 'carState': car_state, 'peripheralState': NS(voltage=13661)}
    fresh = dict.fromkeys(msgs, True)
    self.assertEqual(slow_values(msgs, fresh, False), {'onroad': True, 'isMetric': False, 'gear': 'drive', 'batteryVolts': 13.66})
    self.assertEqual(slow_values({**msgs, 'peripheralState': NS(voltage=220)}, fresh, None)['batteryVolts'], None)
    self.assertEqual(slow_values(msgs, dict.fromkeys(msgs, False), 'yes'), empty_slow())


class ScriptedReader:
  def __init__(self, rows=None):
    self.closed = False
    self.calls = 0
    self.rows = rows

  def sample(self, now):
    self.calls += 1
    row = [self.calls / 50, 10.0, 1.0, None, None, None, 0.0, None, None, 0, None]
    return PerfReading(row, {'onroad': True, 'isMetric': False, 'gear': 'drive', 'batteryVolts': 14.0}, True, False)

  def close(self):
    self.closed = True


class PerfWorkerTest(unittest.TestCase):
  def wait_for(self, source, predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
      snap = source.snapshot()
      if predicate(snap):
        return snap
      time.sleep(0.005)
    self.fail('condition not reached')

  def test_since_first_batch_gap_and_idle_exit(self):
    readers = []

    def factory():
      readers.append(ScriptedReader())
      return readers[-1]

    source = Perf(reader_factory=factory)
    with mock.patch('openpilot.starpilot.galaxy.perf.SAMPLE_INTERVAL_S', 0.001), mock.patch('openpilot.starpilot.galaxy.perf.CLIENT_IDLE_S', 0.3):
      try:
        first = source.snapshot()
        self.assertEqual(set(first), CONTRACT_KEYS)
        self.assertEqual((first['state'], first['samples'], first['fields'], first['hz']), ('stale', [], list(FIELDS), 50))
        snap = self.wait_for(source, lambda s: s['seq'] >= BUFFER_SAMPLES + 20)
        self.assertEqual(snap['state'], 'current')
        self.assertEqual(snap['slow']['batteryVolts'], 14.0)
        self.assertLessEqual(len(snap['samples']), FIRST_BATCH)
        self.assertFalse(snap['gap'])
        seq = snap['seq']
        later = self.wait_for(source, lambda s: s['seq'] >= seq + 5)
        newer = source.snapshot(since=seq)
        self.assertFalse(newer['gap'])
        self.assertGreaterEqual(len(newer['samples']), newer['seq'] - seq - 1)
        self.assertTrue(all(row[0] > snap['samples'][-1][0] for row in newer['samples']))
        self.assertLessEqual(len(source.snapshot(since=0)['samples']), BUFFER_SAMPLES)
        self.assertTrue(source.snapshot(since=0)['gap'])
        self.assertTrue(source.snapshot(since=later['seq'] + 10_000)['gap'])
      finally:
        pass
      time.sleep(0.45)
      self.assertTrue(readers[0].closed)
      self.assertIsNone(source.worker)
      idle = source.snapshot()
      self.assertEqual((idle['state'], idle['slow']), ('stale', empty_slow()))
      self.assertGreater(idle['seq'], 0)   # seq keeps counting across worker restarts
      source.close()
    self.assertTrue(readers[-1].closed)
    with self.assertRaises(OSError):
      source.snapshot()

  def test_reader_error_is_unavailable(self):
    class Broken:
      def __init__(self):
        raise RuntimeError('no IPC')

    source = Perf(reader_factory=Broken)
    try:
      source.snapshot()
      snap = self.wait_for(source, lambda s: s['state'] == 'unavailable')
      self.assertEqual((snap['error'], snap['samples']), ('RuntimeError', []))
    finally:
      source.close()

  def test_no_new_carstate_means_no_new_rows(self):
    class Still(ScriptedReader):
      def sample(self, now):
        self.calls += 1
        return PerfReading(None, empty_slow(), False, None)

    source = Perf(reader_factory=Still)
    with mock.patch('openpilot.starpilot.galaxy.perf.SAMPLE_INTERVAL_S', 0.001):
      try:
        source.snapshot()
        time.sleep(0.05)
        snap = source.snapshot()
        self.assertEqual((snap['seq'], snap['samples'], snap['state']), (0, [], 'stale'))
      finally:
        source.close()


class FakeParams:
  def __init__(self, car_params):
    self.raw = car_params.to_bytes()

  def get_bool(self, key):
    return key == 'IsMetric' and False

  def get(self, key):
    return self.raw if key == 'CarParams' else None


class PerfHttpTest(unittest.TestCase):
  def test_typed_ipc_through_authenticated_http(self):
    messaging.set_fake_prefix('galaxy_perf_http_' + uuid.uuid4().hex)
    with tempfile.TemporaryDirectory() as directory:
      owner = GalaxyAccessOwner(Path(directory) / 'access')
      owner.configure('password123', lambda: True)
      with mock.patch('openpilot.starpilot.galaxy.perf._read_params', return_value=FakeParams(accord_params())):
        source = Perf()
        server = make_server(port=0, owner=owner, perf=source)
        server_thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        server_thread.start()
        publisher = messaging.PubMaster(['deviceState', 'carState', 'can', 'peripheralState'])

        def request(path, headers=None):
          connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=2)
          try:
            connection.request('GET', path, headers={'Forwarded': 'for=203.0.113.8', **(headers or {})})
            response = connection.getresponse()
            return response.status, json.loads(response.read()), dict(response.getheaders())
          finally:
            connection.close()

        try:
          self.assertEqual(request('/api/perf')[0], 401)
          self.assertIsNone(source.worker)
          origin = f'http://127.0.0.1:{server.server_port}'
          connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=2)
          connection.request('POST', '/api/auth/login', body=json.dumps({'password': 'password123'}),
                             headers={'Content-Type': 'application/json', 'Origin': origin, 'Forwarded': 'for=203.0.113.8'})
          response = connection.getresponse()
          response.read()
          self.assertEqual(response.status, 200)
          cookie = response.getheader('Set-Cookie').split(';', 1)[0]
          connection.close()
          for bad in ('/api/perf?since=abc', '/api/perf?since=-1', '/api/perf?since=1&since=2', '/api/perf?x=1', '/api/perf?since=1234567890123'):
            self.assertEqual(request(bad, {'Cookie': cookie})[0], 400, bad)
          status, first, headers = request('/api/perf', {'Cookie': cookie})
          self.assertEqual((status, headers['Cache-Control']), (200, 'no-store'))
          self.assertEqual(set(first), CONTRACT_KEYS)

          can_msg = messaging.new_message('can', 3, valid=True)
          for slot, (address, dat) in zip(can_msg.can, ((VSA_KINEMATICS, vsa(512 - 20, 512 - 30, 512 - 50)),
                                                        (POWERTRAIN_DATA, powertrain(64, 1800)), (BRAKE_PRESSURE, brake(102)))):
            slot.address, slot.dat, slot.src = address, dat, 0
          device = messaging.new_message('deviceState', valid=True)
          device.deviceState.started = True
          peripheral = messaging.new_message('peripheralState', valid=True)
          peripheral.peripheralState.voltage = 14100
          result = None
          seq = 0
          rows = []
          deadline = time.monotonic() + 4
          while time.monotonic() < deadline:
            car_state = messaging.new_message('carState', valid=True)
            car_state.carState.vEgo = 20.0
            car_state.carState.aEgo = 1.5
            car_state.carState.steeringAngleDeg = 12.0
            car_state.carState.gearShifter = 'drive'
            for name, msg in (('deviceState', device), ('peripheralState', peripheral), ('can', can_msg), ('carState', car_state)):
              msg.clear_write_flag()
              publisher.send(name, msg)
            _, result, _ = request(f'/api/perf?since={seq}', {'Cookie': cookie})
            seq = result['seq']
            rows += result['samples']
            if result['state'] == 'current' and result['decodes'] and any(row[3] is not None for row in rows) and len(rows) >= 5:
              break
            time.sleep(0.02)
          assert result is not None
          self.assertEqual((result['state'], result['decodes'], result['slow']),
                           ('current', True, {'onroad': True, 'isMetric': False, 'gear': 'drive', 'batteryVolts': 14.1}))
          decoded = dict(zip(FIELDS, next(row for row in rows if row[3] is not None)))
          self.assertEqual((decoded['v'], decoded['a'], decoded['steer'], decoded['rpm'], decoded['brake']), (20.0, 1.5, 12.0, 1800, 0.0))
          self.assertAlmostEqual(decoded['yaw'], 0.0842, places=4)
          times = [row[0] for row in rows]
          self.assertEqual(times, sorted(times))
          self.assertEqual(len(times), len(set(times)))   # one row per carState, never repeated
        finally:
          server.shutdown()
          server_thread.join(2)
          server.server_close()
          del publisher
          messaging.delete_fake_prefix()
      self.assertTrue(source.closed)


if __name__ == '__main__':
  unittest.main()
