"""Offroad /api/hud steeringBoard + openpilotEnabled from CarParamsPersistent as card really writes it (put_cache envelope).

hud.py used to log_from_bytes() the raw param; card saves it with schema_cache.put_cache (SPCACHE magic + header), so the
decode failed and both blocks were null offroad on the car (416df2ea18c, AGNOS 20.5.2)."""
import tempfile

import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.torque_interceptor import apply_torque_interceptor
from opendbc.car.honda.values import CAR
from openpilot.cereal import messaging
from openpilot.common.params import Params
from openpilot.common.prefix import OpenpilotPrefix
from openpilot.starpilot.galaxy import hud_writes
from openpilot.starpilot.galaxy.hud import SERVICES, FuelTrip, MessagingHudReader, RouteAhead
from openpilot.starpilot.schema_cache import MAGIC, put_cache


class Nothing:
  """SubMaster with no messages: car off / ACC, card not running."""
  def __init__(self):
    self.seen = dict.fromkeys(SERVICES, False)
    self.valid = dict.fromkeys(SERVICES, False)
    self.recv_time = dict.fromkeys(SERVICES, 0.)
    self.logMonoTime = dict.fromkeys(SERVICES, 0)

  def update(self, timeout):
    pass

  def __getitem__(self, key):
    return None


def reader(params):
  r = object.__new__(MessagingHudReader)
  r.messaging = messaging
  r.sm = Nothing()
  r.seen_moving, r.fuel, r.can_sock = {}, FuelTrip(), None
  r.doors = r.doors_at = None
  r.route = RouteAhead(path=None)
  r.params = params
  r.is_metric = True
  r.car_params = r.car_params_at = None
  r.board_seen = {}
  r.board_params = (None, None, None, None)
  r.board_params_at = None
  r.last_drive_cp = r.last_drive_cp_at = None
  r.started_ns = 0
  r.boot_offset_ns = None
  return r


@pytest.mark.parametrize("ti", (True, False))
def test_offroad_blocks_from_put_cache_car_params(ti):
  with OpenpilotPrefix(), tempfile.TemporaryDirectory() as directory:
    params = Params(directory)
    cp = CarInterface.get_params(CAR.HONDA_ACCORD_9G, gen_empty_fingerprint(), [], False, False, False)
    apply_torque_interceptor(cp, ti)
    put_cache(params, 'CarParamsPersistent', cp.as_reader(), block=True)   # what card.py does
    params.put_bool('TorqueInterceptorEnabled', ti, block=True)
    params.put_bool('OpenpilotEnabledToggle', True, block=True)
    params.put('AccordSteeringBoard', 'auto', block=True)
    assert params.get('CarParamsPersistent').startswith(MAGIC)   # the envelope, not raw capnp

    values = reader(params).sample(0).values
    board, op = values['steeringBoard'], values['openpilotEnabled']
    assert board is not None and op is not None
    assert board['active'] == ('ti' if ti else 'ssv3') and board['configured'] == ('ti' if ti else 'ssv3')
    assert op == {'configured': True, 'active': True, 'pendingRestart': False}
    assert hud_writes.last_drive_board(params) == ('ti' if ti else 'ssv3')


def test_raw_or_missing_param_is_a_miss_not_a_crash():
  with OpenpilotPrefix(), tempfile.TemporaryDirectory() as directory:
    params = Params(directory)
    values = reader(params).sample(0).values
    assert values['steeringBoard'] is None
    assert hud_writes.last_drive_board(params) is None
