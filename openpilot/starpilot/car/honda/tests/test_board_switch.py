"""9G Accord live steering-board switch (starpilot/car/honda/board_switch.py): gate, commit order, staging, and the
CarParams / panda safety param / learner basis the restarted card builds from the switched params."""
import os
import tempfile
import types
import unittest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import SSV3_LAT_ACCEL_FACTOR
from opendbc.car.honda.torque_interceptor import TI_SAFETY_PARAM, ti_qualified
from opendbc.car.honda.values import CAR
from openpilot.starpilot.car.honda import board_switch as bs
from openpilot.starpilot.galaxy import hud_writes
from openpilot.starpilot.vehicle_preferences import VehicleStartupPreferences


class FakeParams:
  def __init__(self, **values):
    self.values = dict(values)
    self.writes = []

  def get(self, key):
    return self.values.get(key)

  def get_bool(self, key):
    return bool(self.values.get(key))

  def put(self, key, value, block=False):
    self.values[key] = value
    self.writes.append(key)

  def put_bool(self, key, value, block=False):
    self.values[key] = value
    self.writes.append(key)

  def remove(self, key):
    self.values.pop(key, None)
    self.writes.append(('remove', key))


class FileParams(FakeParams):
  """FakeParams mirrored to files the way Params stores them, for VehicleStartupPreferences.read (read_saved)."""
  def __init__(self, directory):
    super().__init__()
    self.directory = directory

  def get_param_path(self, key=''):
    return os.path.join(self.directory, key)

  def get_default_value(self, key):
    return None

  def _file(self, key, value):
    path = self.get_param_path(key)
    if value is None:
      if os.path.exists(path):
        os.unlink(path)
      return
    raw = (b'1' if value else b'0') if isinstance(value, bool) else value.encode() if isinstance(value, str) else None
    if raw is not None:
      with open(path, 'wb') as f:
        f.write(raw)

  def put(self, key, value, block=False):
    super().put(key, value, block)
    self._file(key, value)

  def put_bool(self, key, value, block=False):
    super().put_bool(key, bool(value), block)
    self._file(key, bool(value))

  def remove(self, key):
    super().remove(key)
    self._file(key, None)


class Clock:
  def __init__(self):
    self.t = 100.0

  def __call__(self):
    return self.t


def honda(identity=CAR.HONDA_ACCORD_9G):
  fp = gen_empty_fingerprint()
  fp[0][0x201] = 6
  return CarInterface.get_params(identity, fp, [], False, False, False)


def cp(board='ti', passive=False, identity=CAR.HONDA_ACCORD_9G):
  out = VehicleStartupPreferences(honda_torque_interceptor=board == 'ti').prepare(honda(identity))
  out.passive = passive
  return out


def cs(v=0.0):
  return types.SimpleNamespace(vEgo=v, vEgoRaw=v, cruiseState=types.SimpleNamespace(available=True), steerFaultTemporary=False)


def cc(enabled=False, lat=False):
  return types.SimpleNamespace(enabled=enabled, latActive=lat)


def live_params(board='ti'):
  return FakeParams(TorqueInterceptorEnabled=board == 'ti', AccordSteeringBoard='auto')


class BoardSwitchGateTest(unittest.TestCase):
  def setUp(self):
    self.clock = Clock()
    self.params = live_params('ti')
    self.sw = bs.BoardSwitch(cp('ti'), self.params, clock=self.clock)

  def run_for(self, seconds, CS=None, CC=None, alive=True):
    blocked = False
    for _ in range(int(round(seconds * 100))):
      self.clock.t += 0.01
      blocked = self.sw.update(CS or cs(), CC or cc(), alive)
    return blocked

  def request(self, board='ssv3', rid='r1'):
    self.params.put(bs.SWITCH_PARAM, {'board': board, 'id': rid})

  def result(self):
    return self.params.values.get(bs.RESULT_PARAM)

  def assert_untouched(self):
    self.assertIs(self.params.values['TorqueInterceptorEnabled'], True)
    self.assertNotIn(bs.CYCLE_PARAM, self.params.values)

  def test_running_board(self):
    self.assertEqual(bs.running_board(cp('ti')), 'ti')
    self.assertEqual(bs.running_board(cp('ssv3')), 'ssv3')
    self.assertIsNone(bs.running_board(cp('ti', passive=True)))
    self.assertIsNone(bs.running_board(cp('ti', identity=CAR.HONDA_CIVIC)))

  def test_refused_while_engaged(self):
    self.run_for(2.0, CC=cc(enabled=True, lat=True))
    self.request()
    self.assertFalse(self.run_for(0.2, CC=cc(enabled=True, lat=True)))
    self.assertEqual(self.result()['applied'], 'refused')
    self.assertEqual(self.result()['reason'], bs.REFUSE_ENGAGED)
    self.assertEqual(self.result()['id'], 'r1')
    self.assertNotIn(bs.SWITCH_PARAM, self.params.values)       # never queued behind an engagement
    self.assert_untouched()
    self.run_for(5.0)                                          # disengaging later does not switch
    self.assert_untouched()

  def test_refused_while_lat_active_only(self):
    # always-on lateral: not "enabled" but steering
    self.request()
    self.run_for(0.2, CC=cc(lat=True))
    self.assertEqual((self.result()['applied'], self.result()['reason']), ('refused', bs.REFUSE_LAT))
    self.assert_untouched()

  def test_refused_while_moving(self):
    self.request()
    self.run_for(0.2, CS=cs(0.5))
    self.assertEqual((self.result()['applied'], self.result()['reason']), ('refused', bs.REFUSE_MOVING))
    self.assert_untouched()
    sw = bs.BoardSwitch(cp('ti'), self.params, clock=self.clock)   # vEgoRaw alone also counts
    self.sw = sw
    self.request(rid='r2')
    moving = cs(0.0); moving.vEgoRaw = 0.3
    self.run_for(0.2, CS=moving)
    self.assertEqual(self.result()['reason'], bs.REFUSE_MOVING)

  def test_applies_when_disengaged_and_stopped(self):
    self.run_for(1.5)                                           # dwell already met
    self.request()
    self.assertTrue(self.run_for(0.2))
    self.assertEqual(self.result(), {'id': 'r1', 'board': 'ssv3', 'applied': 'now',
                                     'reason': 'Switching, about 10 s'})
    self.assertIs(self.params.values['TorqueInterceptorEnabled'], False)
    self.assertEqual(self.params.values['AccordSteeringBoard'], 'auto')
    self.assertEqual(self.params.values['AccordSteeringBoardPrevious'], 'ti')
    self.assertIs(self.params.values[bs.CYCLE_PARAM], True)
    self.assertNotIn(bs.SWITCH_PARAM, self.params.values)
    # order: board params durable before the answer, the answer before the restart request
    w = self.params.writes
    self.assertLess(w.index('TorqueInterceptorEnabled'), w.index(bs.RESULT_PARAM))
    self.assertLess(w.index(bs.RESULT_PARAM), w.index(bs.CYCLE_PARAM))
    self.assertEqual(w.count(bs.CYCLE_PARAM), 1)

  def test_blocks_engagement_until_restart(self):
    self.run_for(1.5)
    self.request()
    self.run_for(0.2)
    CS = cs()
    self.assertTrue(self.sw.update(CS, cc(), True))
    bs.block_engagement(CS)
    self.assertFalse(CS.cruiseState.available)                  # selfdrived: wrongCarMode NO_ENTRY
    self.assertTrue(CS.steerFaultTemporary)                     # selfdrived NO_ENTRY, controlsd: no latActive
    self.request('ti', 'r2')                                    # a second request while committed is not handled here
    self.run_for(1.0)
    self.assertEqual(self.params.values[bs.SWITCH_PARAM]['id'], 'r2')
    self.assertEqual(self.params.writes.count(bs.CYCLE_PARAM), 1)
    self.assertFalse(self.run_for(bs.UNBLOCK_S))                # hardwared never cycled: stop blocking

  def test_dwell_required(self):
    self.run_for(0.5, CC=cc(enabled=True))
    self.request()
    self.run_for(0.5)                                           # disengaged 0.5 s: waits
    self.assertIsNone(self.result())
    self.assert_untouched()
    self.run_for(0.7)                                           # 1.2 s: switches
    self.assertEqual(self.result()['applied'], 'now')
    self.assertIs(self.params.values['TorqueInterceptorEnabled'], False)

  def test_engage_during_dwell_refuses(self):
    self.request()
    self.run_for(0.5)
    self.run_for(0.2, CC=cc(enabled=True))
    self.assertEqual(self.result()['reason'], bs.REFUSE_ENGAGED)
    self.assert_untouched()

  def test_unknown_openpilot_state_times_out(self):
    self.request()
    self.run_for(bs.REQUEST_TIMEOUT_S - 0.5, alive=False)
    self.assertIsNone(self.result())
    self.run_for(1.0, alive=False)
    self.assertEqual((self.result()['applied'], self.result()['reason']), ('refused', bs.REFUSE_UNKNOWN))
    self.assert_untouched()

  def test_same_board_no_restart(self):
    self.request('ti')
    self.run_for(0.2, CC=cc(enabled=True))                      # even engaged: nothing changes
    self.assertEqual((self.result()['applied'], self.result()['reason']), ('now', 'already active'))
    self.assertNotIn(bs.CYCLE_PARAM, self.params.values)

  def test_same_board_rewrites_drifted_params(self):
    self.params.values['TorqueInterceptorEnabled'] = False      # e.g. a direct param write for the next start
    self.request('ti')
    self.run_for(0.2)
    self.assertIs(self.params.values['TorqueInterceptorEnabled'], True)
    self.assertNotIn(bs.CYCLE_PARAM, self.params.values)

  def test_passive_writes_params_without_restart(self):
    self.sw = bs.BoardSwitch(cp('ti', passive=True), self.params, clock=self.clock)
    self.request('ssv3')
    self.run_for(0.2, alive=False)
    self.assertEqual(self.result()['applied'], 'now')
    self.assertIs(self.params.values['TorqueInterceptorEnabled'], False)
    self.assertNotIn(bs.CYCLE_PARAM, self.params.values)

  def test_garbage_request_cleared(self):
    self.params.values[bs.SWITCH_PARAM] = {'board': 'eps'}
    self.run_for(0.2)
    self.assertNotIn(bs.SWITCH_PARAM, self.params.values)
    self.assert_untouched()

  # ---- staging fix: a staged value no longer waits for IsOffroad (never true in accessory)
  def test_staged_applies_when_disengaged_onroad(self):
    self.params.put(hud_writes.BOARD_PENDING, 'ssv3')
    self.run_for(30.0, CC=cc(enabled=True, lat=True))           # engaged: stays staged, no time-out
    self.assertEqual(self.params.values[hud_writes.BOARD_PENDING], 'ssv3')
    self.run_for(30.0, CS=cs(20.0))                             # disengaged but driving: stays staged
    self.assert_untouched()
    self.assertTrue(self.run_for(1.2))                          # stopped, disengaged 1 s: switch
    self.assertIs(self.params.values['TorqueInterceptorEnabled'], False)
    self.assertNotIn(hud_writes.BOARD_PENDING, self.params.values)
    self.assertIs(self.params.values[bs.CYCLE_PARAM], True)

  def test_staged_same_board_cleared_without_restart(self):
    self.params.put(hud_writes.BOARD_PENDING, 'ti')
    self.run_for(0.2, CC=cc(enabled=True))
    self.assertNotIn(hud_writes.BOARD_PENDING, self.params.values)
    self.assertNotIn(bs.CYCLE_PARAM, self.params.values)

  def test_staged_applies_at_start(self):
    self.params.put(hud_writes.BOARD_PENDING, 'ssv3')
    self.assertEqual(bs.consume_at_start(self.params), 'ssv3')
    self.assertIs(self.params.values['TorqueInterceptorEnabled'], False)
    self.assertNotIn(hud_writes.BOARD_PENDING, self.params.values)
    self.assertNotIn(bs.CYCLE_PARAM, self.params.values)        # nothing running yet: no restart needed
    self.assertIsNone(bs.consume_at_start(self.params))

  def test_request_answered_at_start(self):
    self.request('ssv3', 'r9')
    self.assertEqual(bs.consume_at_start(self.params), 'ssv3')
    self.assertEqual(self.result()['id'], 'r9')
    self.assertEqual(self.result()['applied'], 'now')
    self.assertNotIn(bs.SWITCH_PARAM, self.params.values)

  def test_install_only_9g(self):
    self.assertIsNotNone(bs.install(cp('ti'), self.params))
    self.assertIsNotNone(bs.install(cp('ti', passive=True), self.params))
    self.assertIsNone(bs.install(cp('ti', identity=CAR.HONDA_CIVIC), self.params))


class RestartedCardTest(unittest.TestCase):
  """What the card started by the onroad cycle builds from the switched params (startup prepare, real Params)."""

  def setUp(self):
    temporary = tempfile.TemporaryDirectory()
    self.addCleanup(temporary.cleanup)
    self.params = FileParams(temporary.name)
    self.clock = Clock()

  def start_card(self):
    bs.consume_at_start(self.params)
    return VehicleStartupPreferences.read(self.params, enabled=True).prepare(honda())

  def switch(self, running_cp, board):
    sw = bs.BoardSwitch(running_cp, self.params, clock=self.clock)
    self.params.put(bs.SWITCH_PARAM, {'board': board, 'id': 'x'})
    for _ in range(200):
      self.clock.t += 0.01
      sw.update(cs(), cc(), True)
    self.assertTrue(self.params.get_bool(bs.CYCLE_PARAM))
    self.params.put_bool(bs.CYCLE_PARAM, False)

  def test_panda_safety_param_matches_board_after_switch(self):
    self.params.put_bool('TorqueInterceptorEnabled', True)
    ti_cp = self.start_card()
    self.assertTrue(ti_qualified(ti_cp))
    self.assertEqual(bs.running_board(ti_cp), 'ti')
    self.switch(ti_cp, 'ssv3')
    ssv3_cp = self.start_card()
    self.assertFalse(ssv3_cp.safetyConfigs[0].safetyParam & TI_SAFETY_PARAM)   # panda: upstream 9G safety param
    self.assertAlmostEqual(ssv3_cp.lateralTuning.torque.latAccelFactor, SSV3_LAT_ACCEL_FACTOR, places=5)   # SSV3 tune
    self.assertEqual(bs.running_board(ssv3_cp), hud_writes.configured_board(self.params))
    self.switch(ssv3_cp, 'ti')
    back = self.start_card()
    self.assertEqual(back.safetyConfigs[0].safetyParam, ti_cp.safetyConfigs[0].safetyParam)
    self.assertEqual(bs.running_board(back), 'ti')

  def test_ti_carparams_byte_identical(self):
    # TI CarParams after TI -> SSV3 -> TI live switches == a plain TI start (TorqueInterceptorEnabled=1, as before)
    self.params.put_bool('TorqueInterceptorEnabled', True)
    plain = self.start_card()
    self.switch(plain, 'ssv3')
    ssv3_cp = self.start_card()
    self.switch(ssv3_cp, 'ti')
    again = self.start_card()
    self.assertEqual(_cp_bytes(again), _cp_bytes(plain))

  def test_learner_basis_differs_between_boards(self):
    from openpilot.selfdrive.locationd.lagd import _tune_basis_changed
    from openpilot.selfdrive.locationd.torqued import TorqueEstimator, VERSION
    self.params.put_bool('TorqueInterceptorEnabled', True)
    ti_cp = _capnp(self.start_card())
    self.params.put_bool('TorqueInterceptorEnabled', False)
    ssv3_cp = _capnp(self.start_card())
    # CarParamsPrevRoute after a live switch is the other board's CarParams: neither learner restores across boards
    self.assertTrue(_tune_basis_changed(ti_cp, ssv3_cp))
    self.assertTrue(_tune_basis_changed(ssv3_cp, ti_cp))
    self.assertNotEqual(TorqueEstimator.get_restore_key(ti_cp, VERSION), TorqueEstimator.get_restore_key(ssv3_cp, VERSION))
    self.assertFalse(_tune_basis_changed(ti_cp, _capnp(self._ti_again())))

  def _ti_again(self):
    self.params.put_bool('TorqueInterceptorEnabled', True)
    return self.start_card()


def _capnp(cp):
  return cp   # opendbc CarParams are capnp builders


def _cp_bytes(cp):
  return cp.to_bytes()


class CardWiringTest(unittest.TestCase):
  def test_card_hooks(self):
    import inspect
    from openpilot.selfdrive.car import card
    init, step = inspect.getsource(card.Car.__init__), inspect.getsource(card.Car.step)
    # staged board applied before the startup preferences (and so CarParams) are read
    self.assertLess(init.index('consume_honda_board_at_start(self.params)'), init.index('VehicleStartupPreferences.read('))
    self.assertIn('install_honda_board_switch(self.CP, self.params)', init)
    # the gate sees this frame's carState + carControl, and blocks engagement before carState is published
    self.assertLess(step.index("board_switch.update(CS, self.sm['carControl'], self.sm.alive['carControl'])"),
                    step.index('self.state_publish(CS, RD)'))
    self.assertLess(step.index('block_engagement(CS)'), step.index('self.state_publish(CS, RD)'))


if __name__ == '__main__':
  unittest.main()
