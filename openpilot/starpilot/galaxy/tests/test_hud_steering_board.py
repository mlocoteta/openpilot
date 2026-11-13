"""9G Accord: POST /api/hud/steeringBoard (TI or SSV3 for the next start) and the /api/hud steeringBoard object."""

import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

from openpilot.starpilot.galaxy.access import GalaxyAccessOwner
from openpilot.starpilot.galaxy.server import make_server


class FakeParams:
  writes = []
  def put(self, key, value):
    FakeParams.writes.append((key, value))
  def put_bool(self, key, value):
    FakeParams.writes.append((key, value))


class HudSteeringBoardTest(unittest.TestCase):
  def setUp(self):
    FakeParams.writes = []
    self.directory = tempfile.TemporaryDirectory()
    owner = GalaxyAccessOwner(Path(self.directory.name) / 'access')
    self.server = make_server(port=0, owner=owner)
    self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    self.thread.start()
    status, _, headers = self.req('GET', '/api/auth/session')
    self.assertEqual(status, 200)
    self.cookie = headers['Set-Cookie'].split(';', 1)[0]
    fake = types.ModuleType('openpilot.common.params'); fake.Params = FakeParams
    self.patch = mock.patch.dict(sys.modules, {'openpilot.common.params': fake})
    self.patch.start()

  def tearDown(self):
    self.patch.stop()
    self.server.shutdown(); self.thread.join(2); self.server.server_close(); self.directory.cleanup()

  def req(self, method, path, body=None, cookie=None):
    c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
    try:
      h = {'Cookie': cookie} if cookie else {}
      if method == 'POST': h['Origin'] = f'http://127.0.0.1:{self.server.server_port}'   # Galaxy mutations: same-origin only
      data = None
      if body is not None:
        data = json.dumps(body).encode(); h['Content-Type'] = 'application/json'; h['Content-Length'] = str(len(data))
      c.request(method, path, body=data, headers=h)
      r = c.getresponse()
      return r.status, r.read(), dict(r.getheaders())
    finally:
      c.close()

  def test_auth_required(self):
    self.assertEqual(self.req('POST', '/api/hud/steeringBoard', {'board': 'ssv3'})[0], 401)
    self.assertEqual(FakeParams.writes, [])

  def test_writes_params_for_next_start(self):
    status, body, _ = self.req('POST', '/api/hud/steeringBoard', {'board': 'ssv3'}, self.cookie)
    self.assertEqual(status, 200, body)
    self.assertEqual(json.loads(body), {'applied': 'next_start', 'board': 'ssv3'})
    time.sleep(1.05)
    status, body, _ = self.req('POST', '/api/hud/steeringBoard', {'board': 'ti'}, self.cookie)
    self.assertEqual(json.loads(body), {'applied': 'next_start', 'board': 'ti'})
    self.assertEqual(FakeParams.writes, [('TorqueInterceptorEnabled', False), ('AccordSteeringBoard', 'auto'),
                                         ('TorqueInterceptorEnabled', True), ('AccordSteeringBoard', 'auto')])

  def test_only_ti_or_ssv3(self):
    for bad in ({'board': 'TI'}, {'board': 'eps'}, {'board': 1}, {}, {'key': 'TorqueInterceptorEnabled', 'value': 1}):
      self.assertEqual(self.req('POST', '/api/hud/steeringBoard', bad, self.cookie)[0], 400, bad)
    self.assertEqual(FakeParams.writes, [])

  def test_one_change_per_second(self):
    self.assertEqual(self.req('POST', '/api/hud/steeringBoard', {'board': 'ti'}, self.cookie)[0], 200)
    self.assertEqual(self.req('POST', '/api/hud/steeringBoard', {'board': 'ssv3'}, self.cookie)[0], 429)
    self.assertEqual(len(FakeParams.writes), 2)

  def test_commalink_allowlist(self):
    from openpilot.starpilot.commalink.daemon import Allow
    import inspect
    self.assertIn('"/api/hud/steeringBoard"', inspect.getsource(Allow))


class SteeringBoardHudTest(unittest.TestCase):
  def test_board_frames(self):
    from openpilot.starpilot.galaxy.hud import board_frames
    F = types.SimpleNamespace
    batches = [[F(src=0, address=0x24A, dat=bytes(8)), F(src=2, address=0x208, dat=bytes([0x42, 0, 0]))],
               [F(src=0, address=0x190, dat=bytes(5)), F(src=0, address=0x208, dat=bytes([0x43, 0x00, 0x16]))]]
    self.assertEqual(board_frames(batches), (True, True, 3))
    self.assertEqual(board_frames([[F(src=0, address=0x190, dat=bytes(4))]]), (False, False, None))

  def test_object(self):
    from openpilot.starpilot.galaxy.hud import empty, steering_board, TI_SAFETY_PARAM
    def cp(param):
      return types.SimpleNamespace(brand='honda', safetyConfigs=[types.SimpleNamespace(safetyModel='hondaNidec', safetyParam=param)])
    on_ti = steering_board(cp(548 | TI_SAFETY_PARAM), False, 'auto', {'ti': True, 'ssv3': True, 'version': 3})
    self.assertEqual(on_ti, {'configured': 'ssv3', 'active': 'ti', 'tiPresent': True, 'ssv3Present': True, 'ssv3Firmware': 3,
                             'pendingRestart': True})
    same = steering_board(cp(548), False, '', {'ssv3': True})
    self.assertEqual((same['active'], same['pendingRestart'], same['tiPresent'], same['ssv3Firmware']), ('ssv3', False, False, None))
    self.assertEqual(steering_board(cp(548), True, 'ssv3', {})['configured'], 'ssv3')
    unknown = steering_board(None, None, None, None)
    self.assertEqual((unknown['configured'], unknown['active'], unknown['pendingRestart']), (None, None, False))
    self.assertTrue(empty()['steeringBoardWrite'])
    self.assertIsNone(empty()['steeringBoard'])


if __name__ == '__main__':
  unittest.main()
