"""Accord 4.2: POST /api/hud/personality (head-unit speed profiles v1): auth, names only, 1 per second, the param write."""

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


class HudPersonalityTest(unittest.TestCase):
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
    self.assertEqual(self.req('POST', '/api/hud/personality', {'personality': 'relaxed'})[0], 401)
    self.assertEqual(FakeParams.writes, [])

  def test_writes_the_cereal_value(self):
    for i, (name, value) in enumerate((('aggressive', 0), ('standard', 1), ('relaxed', 2))):
      if i: time.sleep(1.05)
      status, body, _ = self.req('POST', '/api/hud/personality', {'personality': name}, self.cookie)
      self.assertEqual(status, 200, body)
      self.assertEqual(json.loads(body), {'personality': name})
    self.assertEqual(FakeParams.writes, [('LongitudinalPersonality', 0), ('LongitudinalPersonality', 1), ('LongitudinalPersonality', 2)])

  def test_only_the_three_names(self):
    for bad in ({'personality': 'traffic'}, {'personality': 3}, {'personality': 'madmax'}, {}, {'key': 'LongitudinalPersonality', 'value': 0}):
      self.assertEqual(self.req('POST', '/api/hud/personality', bad, self.cookie)[0], 400, bad)
    self.assertEqual(FakeParams.writes, [])

  def test_one_change_per_second(self):
    self.assertEqual(self.req('POST', '/api/hud/personality', {'personality': 'relaxed'}, self.cookie)[0], 200)
    self.assertEqual(self.req('POST', '/api/hud/personality', {'personality': 'standard'}, self.cookie)[0], 429)
    self.assertEqual(len(FakeParams.writes), 1)

  def test_get_not_allowed(self):
    self.assertIn(self.req('GET', '/api/hud/personality', cookie=self.cookie)[0], (404, 405))


if __name__ == '__main__':
  unittest.main()
