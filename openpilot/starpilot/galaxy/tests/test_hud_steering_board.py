"""Head-unit next-start writes: POST /api/hud/steeringBoard (9G TI/SSV3), POST /api/hud/openpilotEnabled (datalogger),
their refusals / no-lock-out rules (galaxy/hud_writes.py) and the /api/hud steeringBoard / openpilotEnabled objects."""

import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock

from openpilot.starpilot.galaxy.access import GalaxyAccessOwner
from openpilot.starpilot.galaxy.server import make_server
from openpilot.starpilot.galaxy import hud_writes

NOW = 1794000000.0
DAY = 86400


class FakeParams:
  """Shared store; the server builds a new Params() per request. Values as 7.0 Params.get returns them (typed)."""
  values = {}
  writes = []
  unreadable = set()

  def get(self, key):
    if key in FakeParams.unreadable:
      raise OSError(key)
    return FakeParams.values.get(key)

  def get_bool(self, key):
    if key in FakeParams.unreadable:
      raise OSError(key)
    return bool(FakeParams.values.get(key))

  def put(self, key, value, block=False):
    FakeParams.values[key] = value
    FakeParams.writes.append((key, value))

  def put_bool(self, key, value, block=False):
    FakeParams.values[key] = value
    FakeParams.writes.append((key, value))


def parked(**extra):
  FakeParams.values = {'IsOffroad': True, 'IsEngaged': False, 'TorqueInterceptorEnabled': True, 'AccordSteeringBoard': 'auto',
                       'OpenpilotEnabledToggle': True, **extra}
  FakeParams.writes = []
  FakeParams.unreadable = set()


class HudWritesServerTest(unittest.TestCase):
  def setUp(self):
    parked(AccordSteeringBoardSeen={'ti': NOW - DAY, 'ssv3': NOW - DAY, 'ssv3Firmware': 3})
    self.gap = mock.patch.object(hud_writes, 'WRITE_GAP_S', 0.0)
    self.gap.start()
    self.wall = mock.patch.object(hud_writes, '_wall', return_value=NOW)
    self.wall.start()
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
    self.patch.stop(); self.gap.stop(); self.wall.stop()
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

  def board(self, board):
    status, body, _ = self.req('POST', '/api/hud/steeringBoard', {'board': board}, self.cookie)
    return status, json.loads(body)

  def enabled(self, value):
    status, body, _ = self.req('POST', '/api/hud/openpilotEnabled', {'enabled': value}, self.cookie)
    return status, json.loads(body)

  # ---- steeringBoard
  def test_auth_required(self):
    self.assertEqual(self.req('POST', '/api/hud/steeringBoard', {'board': 'ssv3'})[0], 401)
    self.assertEqual(self.req('POST', '/api/hud/openpilotEnabled', {'enabled': False})[0], 401)
    self.assertEqual(FakeParams.writes, [])

  def test_writes_params_for_next_start(self):
    self.assertEqual(self.board('ssv3'), (200, {'applied': 'next_start', 'board': 'ssv3'}))
    self.assertEqual(self.board('ti'), (200, {'applied': 'next_start', 'board': 'ti'}))
    self.assertEqual(FakeParams.writes, [
      ('AccordSteeringBoardPrevious', 'ti'), ('TorqueInterceptorEnabled', False), ('AccordSteeringBoard', 'auto'),
      ('AccordSteeringBoardPrevious', 'ssv3'), ('TorqueInterceptorEnabled', True), ('AccordSteeringBoard', 'auto')])

  def test_400_unknown_board(self):
    for bad in ({'board': 'TI'}, {'board': 'eps'}, {'board': 1}, {}, {'key': 'TorqueInterceptorEnabled', 'value': 1}):
      self.assertEqual(self.req('POST', '/api/hud/steeringBoard', bad, self.cookie)[0], 400, bad)
    self.assertEqual(FakeParams.writes, [])

  def test_409_onroad(self):
    for offroad in (False, None):   # onroad, or IsOffroad missing (manager not up / unknown)
      FakeParams.values['IsOffroad'] = offroad
      status, body = self.board('ssv3')
      self.assertEqual(status, 409, offroad); self.assertIn('offroad', body['error'])
    self.assertEqual(FakeParams.writes, [])

  def test_409_engaged(self):
    FakeParams.values['IsEngaged'] = True
    self.assertEqual(self.board('ssv3')[0], 409)
    self.assertEqual(FakeParams.writes, [])

  def test_409_unreadable(self):
    for key in ('IsOffroad', 'IsEngaged'):
      FakeParams.unreadable = {key}
      self.assertEqual(self.board('ssv3')[0], 409, key)
      self.assertEqual(self.enabled(False)[0], 409, key)
    self.assertEqual(FakeParams.writes, [])

  def test_409_absent_board(self):
    FakeParams.values['AccordSteeringBoardSeen'] = {'ti': NOW - DAY, 'ssv3': None, 'ssv3Firmware': None}
    status, body = self.board('ssv3')
    self.assertEqual(status, 409); self.assertIn('SSV3', body['error'])
    FakeParams.values['AccordSteeringBoardSeen'] = {'ti': NOW - DAY, 'ssv3': NOW - 31 * DAY, 'ssv3Firmware': 2}   # too old
    self.assertEqual(self.board('ssv3')[0], 409)
    FakeParams.values.pop('AccordSteeringBoardSeen')   # no record at all: refuse
    self.assertEqual(self.board('ssv3')[0], 409)
    self.assertEqual(FakeParams.writes, [])
    FakeParams.values['AccordSteeringBoardSeen'] = {'ti': None, 'ssv3': NOW - 29 * DAY, 'ssv3Firmware': 2}
    self.assertEqual(self.board('ssv3')[0], 200)

  def test_429_one_write_per_5_s(self):
    self.patch.stop()   # make_server's own settings owner must see the real Params module
    with mock.patch.object(hud_writes, 'WRITE_GAP_S', 5.0):
      owner = GalaxyAccessOwner(Path(self.directory.name) / 'access2')
      server = make_server(port=0, owner=owner)
      thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
      thread.start()
    self.patch.start()
    try:
      self.server, saved = server, self.server
      status, _, headers = self.req('GET', '/api/auth/session')
      self.cookie = headers['Set-Cookie'].split(';', 1)[0]
      FakeParams.values['IsOffroad'] = False
      self.assertEqual(self.board('ssv3')[0], 409)               # refusals don't use up the window
      FakeParams.values['IsOffroad'] = True
      self.assertEqual(self.board('ssv3')[0], 200)
      self.assertEqual(self.board('ti')[0], 429)
      self.assertEqual(self.enabled(False)[0], 200)              # separate window per setting
      self.assertEqual(self.enabled(True)[0], 429)
      self.assertEqual(len([w for w in FakeParams.writes if w[0] == 'TorqueInterceptorEnabled']), 1)
    finally:
      self.server = saved
      server.shutdown(); thread.join(2); server.server_close()

  def test_switch_back_to_ti_after_ssv3_only_drives(self):
    # TI drives recorded the TI 40 days ago; then the car was switched to SSV3 and only SSV3 drives followed (the TI
    # never talks there, so the record never moves). Switching back to the TI must still work.
    FakeParams.values['AccordSteeringBoardSeen'] = {'ti': NOW - 40 * DAY, 'ssv3': NOW - DAY, 'ssv3Firmware': 3}
    self.assertEqual(self.board('ssv3')[0], 200)
    self.assertEqual(FakeParams.values['AccordSteeringBoardPrevious'], 'ti')
    self.assertEqual(self.board('ti'), (200, {'applied': 'next_start', 'board': 'ti'}))
    # also with no Previous record (switched on the comma's own UI): the last drive's board counts
    parked(AccordSteeringBoardSeen={'ti': None, 'ssv3': NOW, 'ssv3Firmware': 3}, TorqueInterceptorEnabled=False)
    with mock.patch.object(hud_writes, 'last_drive_board', return_value='ti'):
      self.assertEqual(self.board('ti')[0], 200)
    parked(AccordSteeringBoardSeen={'ti': None, 'ssv3': NOW, 'ssv3Firmware': 3}, TorqueInterceptorEnabled=False)
    self.assertEqual(self.board('ti')[0], 409)   # never fitted, never configured: refused
    self.assertEqual(self.board('ssv3')[0], 200)  # the configured board is always fine

  def test_ti_recorded_within_30_days(self):
    parked(AccordSteeringBoardSeen={'ti': NOW - 29 * DAY, 'ssv3': NOW, 'ssv3Firmware': 3}, TorqueInterceptorEnabled=False)
    self.assertEqual(self.board('ti')[0], 200)

  # ---- openpilotEnabled
  def test_datalogger_disable_then_enable(self):
    self.assertEqual(self.enabled(False), (200, {'applied': 'next_start', 'enabled': False}))
    self.assertIs(FakeParams.values['OpenpilotEnabledToggle'], False)
    self.assertEqual(self.enabled(True), (200, {'applied': 'next_start', 'enabled': True}))
    self.assertIs(FakeParams.values['OpenpilotEnabledToggle'], True)
    self.assertEqual(FakeParams.writes, [('OpenpilotEnabledToggle', False), ('OpenpilotEnabledToggle', True)])

  def test_disable_refusals(self):
    for bad in ({'enabled': 'false'}, {'enabled': 0}, {}, {'enabled': None}):
      self.assertEqual(self.req('POST', '/api/hud/openpilotEnabled', bad, self.cookie)[0], 400, bad)
    FakeParams.values['IsOffroad'] = False
    self.assertEqual(self.enabled(False)[0], 409)
    FakeParams.values['IsOffroad'] = True
    FakeParams.values['IsEngaged'] = True
    self.assertEqual(self.enabled(False)[0], 409)
    self.assertEqual(FakeParams.writes, [])

  def test_reenable_never_locked_out_offroad(self):
    # stale IsEngaged, no board record, no CarParams: turning openpilot back on only needs offroad
    parked(OpenpilotEnabledToggle=False, IsEngaged=True)
    FakeParams.unreadable = {'IsEngaged', 'AccordSteeringBoardSeen', 'CarParamsPersistent'}
    self.assertEqual(self.enabled(True), (200, {'applied': 'next_start', 'enabled': True}))
    FakeParams.values['IsOffroad'] = False
    self.assertEqual(self.enabled(True)[0], 409)   # still never while driving

  def test_commalink_allowlist(self):
    from openpilot.starpilot.commalink.daemon import Allow
    import inspect
    src = inspect.getsource(Allow)
    self.assertIn('"/api/hud/steeringBoard"', src)
    self.assertIn('"/api/hud/openpilotEnabled"', src)


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
    def cp(param, passive=False):
      return types.SimpleNamespace(brand='honda', passive=passive,
                                   safetyConfigs=[types.SimpleNamespace(safetyModel='hondaNidec', safetyParam=param)])
    on_ti = steering_board(cp(548 | TI_SAFETY_PARAM), False, 'auto', {'ti': True, 'ssv3': True, 'version': 3}, None, NOW)
    self.assertEqual(on_ti, {'configured': 'ssv3', 'active': 'ti', 'tiPresent': True, 'ssv3Present': True, 'ssv3Firmware': 3,
                             'tiLastSeen': None, 'ssv3LastSeen': None, 'pendingRestart': True})
    same = steering_board(cp(548), False, '', {'ssv3': True}, None, NOW)
    self.assertEqual((same['active'], same['pendingRestart'], same['tiPresent'], same['ssv3Firmware']), ('ssv3', False, False, None))
    self.assertEqual(steering_board(cp(548), True, 'ssv3', {}, None, NOW)['configured'], 'ssv3')
    unknown = steering_board(None, None, None, None)
    self.assertEqual((unknown['configured'], unknown['active'], unknown['pendingRestart']), (None, None, False))
    self.assertTrue(empty()['steeringBoardWrite'])
    self.assertIsNone(empty()['steeringBoard'])

  def test_persisted_presence(self):
    from openpilot.starpilot.galaxy.hud import steering_board
    cp = types.SimpleNamespace(brand='honda', passive=False, safetyConfigs=[types.SimpleNamespace(safetyModel='hondaNidec', safetyParam=548)])
    # SSV3-only drive: the TI is silent, but card heard it 3 days ago -> present, with its timestamp
    record = {'ti': int(NOW - 3 * DAY), 'ssv3': int(NOW - 60), 'ssv3Firmware': 3}
    b = steering_board(cp, False, 'auto', {'ssv3': True}, record, NOW)
    self.assertEqual((b['tiPresent'], b['ssv3Present'], b['tiLastSeen'], b['ssv3LastSeen'], b['ssv3Firmware']),
                     (True, True, int(NOW - 3 * DAY), int(NOW - 60), 3))
    old = steering_board(cp, False, 'auto', {}, {'ti': int(NOW - 40 * DAY), 'ssv3': None}, NOW)
    self.assertEqual((old['tiPresent'], old['ssv3Present'], old['tiLastSeen'], old['ssv3LastSeen']), (False, False, int(NOW - 40 * DAY), None))
    json.dumps(b)   # plain JSON types

  def test_openpilot_disabled_drive(self):
    from openpilot.starpilot.galaxy.hud import empty, openpilot_enabled, steering_board
    passive = types.SimpleNamespace(brand='honda', passive=True, safetyConfigs=[types.SimpleNamespace(safetyModel='noOutput', safetyParam=0)])
    self.assertEqual(openpilot_enabled(passive, False), {'configured': False, 'active': False, 'pendingRestart': False})
    self.assertEqual(openpilot_enabled(passive, True), {'configured': True, 'active': False, 'pendingRestart': True})
    self.assertEqual(openpilot_enabled(None, None), {'configured': None, 'active': None, 'pendingRestart': False})
    self.assertIsNone(steering_board(passive, True, 'auto', {}, None, NOW)['active'])   # no board steers in datalogger mode
    self.assertTrue(empty()['openpilotEnabledWrite'])
    self.assertIsNone(empty()['openpilotEnabled'])


if __name__ == '__main__':
  unittest.main()
