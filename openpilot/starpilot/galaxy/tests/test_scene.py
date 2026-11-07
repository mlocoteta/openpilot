"""Scene stream (GET /api/hud/scene): frame shape and signs, rate limit, size, keep-alive, limits, idle close, auth, IPC."""

import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import uuid
import unittest
from unittest import mock

from openpilot.cereal import messaging
from openpilot.starpilot.galaxy import scene
from openpilot.starpilot.galaxy.access import GalaxyAccessOwner
from openpilot.starpilot.galaxy.hud import MODEL_IDX
from openpilot.starpilot.galaxy.scene import MessagingSceneReader, SceneStreams, frame_body
from openpilot.starpilot.galaxy.server import make_server

X_IDXS = [192.0 * (i / 32) ** 2 for i in range(33)]
FRAME_KEYS = {'s', 'a', 'v', 'yr', 'c', 'm', 'l', 'lc', 'ld'}


def model_msg(curve=0.0012, lane_change='off'):
  msg = messaging.new_message('modelV2', valid=True)
  model = msg.modelV2

  def fill(xyz, y0):
    xyz.x = X_IDXS
    xyz.y = [y0 + curve * x * x / 2 for x in X_IDXS]   # right positive, like the model
    xyz.z = [1.2] * 33
    xyz.t = [i * 0.3 for i in range(33)]

  lines, edges = model.init('laneLines', 4), model.init('roadEdges', 2)
  for line, y0 in zip(lines, (-5.4, -1.82, 1.87, 5.53), strict=True):
    fill(line, y0)
  for edge, y0 in zip(edges, (-7.31, 3.66), strict=True):
    fill(edge, y0)
  fill(model.position, 0.03)
  model.laneLineProbs = [0.2134, 0.9871, 0.9912, 0.3045]
  model.roadEdgeStds = [0.6123, 0.4071]
  model.meta.laneChangeState = lane_change
  model.meta.laneChangeDirection = 'none'
  return msg


def messages(z=0.0213, curvature=0.0011, lead=True):
  car_state = messaging.new_message('carState', valid=True)
  car_state.carState.vEgo = 27.4567
  motion = messaging.new_message('deviceMotion', valid=True)
  motion.deviceMotion.angularVelocityDevice.z = z
  motion.deviceMotion.angularVelocityDevice.valid = True
  controls = messaging.new_message('controlsState', valid=True)
  controls.controlsState.desiredCurvature = curvature
  radar = messaging.new_message('radarState', valid=True)
  if lead:
    one = radar.radarState.leadOne
    one.present, one.radar, one.radarTrackId = True, True, 7
    one.dRel, one.yRel, one.vRel, one.vLead = 41.234, 0.41, -1.256, 26.2
  return {'modelV2': model_msg(), 'carState': car_state, 'deviceMotion': motion, 'controlsState': controls, 'radarState': radar}


def readers(msgs):
  return {key: getattr(msg, key) for key, msg in msgs.items()}


def parse(body, seq=1, age=0.01):
  return json.loads(f'{{"s":{seq},"a":{age},{body}')


class FrameTest(unittest.TestCase):
  def test_frame_shape_signs_and_size(self):
    frame = parse(frame_body(readers(messages())))
    self.assertEqual(set(frame), FRAME_KEYS)
    self.assertEqual(frame['v'], 27.46)
    # deviceMotion z and desiredCurvature are positive turning right; the frame is positive turning left
    self.assertEqual((frame['yr'], frame['c']), (-0.0213, -0.0011))
    self.assertEqual(frame['l'], {'d': 41.2, 'y': -0.41, 'vr': -1.26, 'id': 7})   # radar yRel left+ -> right+
    model = frame['m']
    self.assertEqual(set(model), {'ll', 're', 'pa', 'pr', 'sd'})
    self.assertEqual([len(line) for line in model['ll'] + model['re'] + [model['pa']]], [2 * len(MODEL_IDX)] * 7)
    self.assertEqual(model['ll'][1][:4], [0, -1.82, 0.8, -1.82])   # x (1 decimal), y (2 decimals), flattened
    self.assertEqual(model['ll'][1][-2], round(X_IDXS[MODEL_IDX[-1]], 1))
    self.assertAlmostEqual(model['ll'][2][-1], round(1.87 + 0.0012 * X_IDXS[26] ** 2 / 2, 2))
    self.assertEqual((model['pr'], model['sd']), ([0.21, 0.99, 0.99, 0.3], [0.61, 0.41]))
    self.assertEqual((frame['lc'], frame['ld']), ('off', 'none'))
    line = f'{{"s":123456,"a":0.051,{frame_body(readers(messages()))}\n'.encode()
    self.assertLessEqual(len(line), 1200)

  def test_absent_or_invalid_inputs_are_null(self):
    msgs = readers(messages(lead=False))
    invalid = messaging.new_message('deviceMotion', valid=True)
    invalid.deviceMotion.angularVelocityDevice.z = 0.3   # valid flag unset
    msgs['deviceMotion'] = invalid.deviceMotion
    short = messaging.new_message('modelV2', valid=True)
    short.modelV2.init('laneLines', 4)
    msgs['modelV2'] = short.modelV2
    frame = parse(frame_body(msgs))
    self.assertEqual((frame['yr'], frame['l'], frame['m']), (None, None, None))
    frame = parse(frame_body({}))
    self.assertEqual(set(frame), FRAME_KEYS)
    self.assertTrue(all(frame[key] is None for key in FRAME_KEYS - {'s', 'a'}))


class FakeReader:
  """modelV2 at `rate` Hz (or never), like the polled SubMaster."""

  def __init__(self, rate=20.0, body=None):
    self.rate, self.body, self.closed = rate, body or frame_body(readers(messages())), False
    self.next = time.monotonic()

  def read(self):
    if not self.rate:
      time.sleep(0.02)
      return None
    delay = self.next - time.monotonic()
    if delay > 0:
      time.sleep(delay)
    self.next += 1 / self.rate
    return time.monotonic_ns(), self.body

  def close(self):
    self.closed = True


class StreamTest(unittest.TestCase):
  def run_stream(self, source, hz, seconds):
    lines = []
    self.assertTrue(source.acquire())
    try:
      source.stream(lines.append, hz, duration=seconds)
    finally:
      source.release()
    return [json.loads(line) for line in lines]

  def test_rate_limit(self):
    source = SceneStreams(lambda: FakeReader(20.0))
    try:
      for hz, low, high in ((5, 4.5, 5.6), (10, 9.0, 10.6), (15, 13.5, 15.6), (20, 18.0, 20.6)):
        frames = self.run_stream(source, hz, 2.0)
        rate = len(frames) / 2.0
        self.assertTrue(low <= rate <= high, (hz, rate))
        seqs = [f['s'] for f in frames]
        self.assertEqual(seqs, sorted(set(seqs)))   # never the same frame twice
        self.assertTrue(all(0 <= f['a'] < 0.2 for f in frames))
    finally:
      source.close()

  def test_keepalive_without_new_models(self):
    source = SceneStreams(lambda: FakeReader(0))
    with mock.patch.object(scene, 'KEEPALIVE_S', 0.2):
      try:
        frames = self.run_stream(source, 10, 1.05)
      finally:
        source.close()
    self.assertTrue(4 <= len(frames) <= 6, len(frames))
    self.assertTrue(all(f == {'k': 1} for f in frames))

  def test_two_streams_max_and_idle_worker_exit(self):
    made = []

    def factory():
      made.append(FakeReader(20.0))
      return made[-1]

    source = SceneStreams(factory)
    with mock.patch.object(scene, 'SCENE_IDLE_S', 0.2):
      try:
        self.assertTrue(source.acquire())
        self.assertTrue(source.acquire())
        self.assertFalse(source.acquire())
        source.release()
        self.assertTrue(source.acquire())
        source.release()
        source.release()
        deadline = time.monotonic() + 2
        while source.worker is not None and time.monotonic() < deadline:
          time.sleep(0.02)
        self.assertIsNone(source.worker)
        self.assertEqual(len(made), 1)
        self.assertTrue(made[0].closed)
      finally:
        source.close()

  def test_failed_write_ends_the_stream(self):
    source = SceneStreams(lambda: FakeReader(20.0))
    calls = []

    def write(line):
      calls.append(line)
      if len(calls) == 3:
        raise BrokenPipeError

    try:
      self.assertTrue(source.acquire())
      with self.assertRaises(BrokenPipeError):
        source.stream(write, 20, duration=5)
      source.release()
      self.assertEqual(source.streams, 0)
    finally:
      source.close()


class SceneHttpTest(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    owner = GalaxyAccessOwner(Path(self.directory.name) / 'access')
    self.source = SceneStreams(lambda: FakeReader(20.0))
    self.server = make_server(port=0, owner=owner, scene=self.source)
    self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    self.thread.start()
    status, _, headers = self.get('/api/auth/session')
    self.assertEqual(status, 200)
    self.cookie = headers['Set-Cookie'].split(';', 1)[0]

  def tearDown(self):
    self.server.shutdown()
    self.thread.join(2)
    self.server.server_close()
    self.directory.cleanup()

  def get(self, path, headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
    try:
      connection.request('GET', path, headers=headers or {})
      response = connection.getresponse()
      return response.status, response.read(), dict(response.getheaders())
    finally:
      connection.close()

  def open_stream(self, query=''):
    connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
    connection.request('GET', '/api/hud/scene' + query, headers={'Cookie': self.cookie})
    return connection, connection.getresponse()

  def test_auth_and_parameters(self):
    self.assertEqual(self.get('/api/hud/scene')[0], 401)
    self.assertIsNone(self.source.worker)
    for query in ('?hz=fast', '?hz=10&x=1', '?rate=10'):
      self.assertEqual(self.get('/api/hud/scene' + query, {'Cookie': self.cookie})[0], 400, query)
    self.assertEqual(self.get('/api/hud/scene', {'Cookie': self.cookie, 'Host': 'comma.local:8082'})[0], 403)

  def test_ndjson_stream_rate_size_and_close(self):
    with mock.patch.object(scene, 'STREAM_MAX_S', 1.5):
      connection, response = self.open_stream('?hz=99')   # clamped to 20
      try:
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader('Content-Type'), 'application/x-ndjson')
        self.assertEqual(response.getheader('Connection'), 'close')
        started = time.monotonic()
        lines = []
        while True:
          line = response.readline()
          if not line:
            break   # the server closed after STREAM_MAX_S
          lines.append(line)
        elapsed = time.monotonic() - started
      finally:
        connection.close()
    self.assertTrue(1.3 <= elapsed <= 2.2, elapsed)
    frames = [json.loads(line) for line in lines]
    self.assertTrue(26 <= len(frames) <= 31, len(frames))
    self.assertEqual(set(frames[0]), FRAME_KEYS)
    self.assertLessEqual(max(map(len, lines)), 1200)

  def test_third_stream_refused_and_slots_return_after_disconnect(self):
    first, response1 = self.open_stream()
    second, response2 = self.open_stream('?hz=5')
    try:
      self.assertEqual((response1.status, response2.status), (200, 200))
      json.loads(response1.readline())
      self.assertEqual(self.get('/api/hud/scene', {'Cookie': self.cookie})[0], 429)
    finally:
      for response, connection in ((response1, first), (response2, second)):
        response.close()
        connection.close()
    deadline = time.monotonic() + 3
    while self.source.streams and time.monotonic() < deadline:
      time.sleep(0.02)
    self.assertEqual(self.source.streams, 0)
    third, response3 = self.open_stream()
    try:
      self.assertEqual(response3.status, 200)
      self.assertEqual(set(json.loads(response3.readline())), FRAME_KEYS)
    finally:
      third.close()

  def test_server_close_ends_open_streams(self):
    connection, response = self.open_stream()
    try:
      json.loads(response.readline())
      self.server.shutdown()
      self.server.server_close()
      deadline = time.monotonic() + 2
      while response.readline() and time.monotonic() < deadline:
        pass
      self.assertLess(time.monotonic(), deadline)
      self.assertTrue(self.source.closed)
    finally:
      connection.close()
    self.server = mock.Mock()   # tearDown already done


class SceneIpcTest(unittest.TestCase):
  def test_typed_ipc(self):
    messaging.set_fake_prefix('galaxy_scene_' + uuid.uuid4().hex)
    try:
      reader = MessagingSceneReader()
      publisher = messaging.PubMaster(list(scene.SERVICES))
      time.sleep(0.05)
      frame = None
      deadline = time.monotonic() + 3
      while time.monotonic() < deadline:
        for name, msg in messages().items():
          if name != 'modelV2':
            publisher.send(name, msg)
        time.sleep(0.01)
        publisher.send('modelV2', model_msg())
        result = reader.read()
        if result is not None:
          frame = parse(result[1])
          if frame['yr'] is not None and frame['l'] is not None and frame['m'] is not None:
            break
      reader.close()
      assert frame is not None
      self.assertEqual((frame['v'], frame['yr'], frame['c'], frame['l']['id']), (27.46, -0.0213, -0.0011, 7))
      self.assertEqual(len(frame['m']['ll']), 4)
      del publisher
    finally:
      messaging.delete_fake_prefix()


if __name__ == '__main__':
  unittest.main()
