"""9G Accord SSV3 path: initial lateral tune and the zero-torque LKAS dropout (opendbc/car/honda/ssv3.py).

The board model below follows LKAS_EPS_V3 firmware 3 src/bridge.cpp (onCanFrame / torqueLimit / buildFrame);
firmware 2 has the same zero-torque rule (ZERO_TORQUE_SENDS_OFF behaviour, no option bits).
"""
import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import (SSV3_FRICTION, SSV3_LAT_ACCEL_FACTOR, SSV3_STEER_ACTUATOR_DELAY, apply_ssv3_lateral_tune,
                                    ssv3_steer_command)
from opendbc.car.honda.tests.test_ssv3 import car_frames, fw2_400, fw2_427, fw3_400, fw3_427, ss_status, ACCORD_DBC
from opendbc.car.honda.values import CAR
from opendbc.can import CANPacker

# config.h
STEER_MAX = 239
STEER_DELTA = 100
STEER_DRIVER_ALLOWANCE = 30
STEER_DRIVER_MULTIPLIER = 18
STEER_DRIVER_FACTOR = 1
ZERO_TORQUE_KEEPS_LKAS_ON = 0x08


def board_torque_limit(request, last, driver_torque):
  # bridge.cpp torqueLimit()
  driver = driver_torque >> 1
  if last > 0:
    torque = min(max(request, max(last - STEER_DELTA, -STEER_DELTA)), last + STEER_DELTA)
  else:
    torque = min(max(request, last - STEER_DELTA), min(last + STEER_DELTA, STEER_DELTA))
  driver_max = STEER_MAX + (STEER_DRIVER_ALLOWANCE + driver * STEER_DRIVER_FACTOR) * STEER_DRIVER_MULTIPLIER
  driver_min = -STEER_MAX + (-STEER_DRIVER_ALLOWANCE + driver * STEER_DRIVER_FACTOR) * STEER_DRIVER_MULTIPLIER
  limit = min(max(min(STEER_MAX, driver_max), 0), -min(max(-STEER_MAX, driver_min), 0))
  return min(max(torque, -limit), limit)


class Board:
  """onCanFrame(): steerRequest = requestBit && (torque != 0 || !ZERO_TORQUE_SENDS_OFF || zeroKeepsOn)."""
  def __init__(self):
    self.steer_command = 0
    self.last_lsb = 0

  def on_0xe4(self, dat, driver_torque=0):
    request = bool(dat[2] & 0x80)
    zero_keeps = bool(dat[2] & ZERO_TORQUE_KEEPS_LKAS_ON)
    torque = int.from_bytes(dat[0:2], "big", signed=True)
    self.steer_command = board_torque_limit(torque, self.steer_command, driver_torque)
    return request and (self.steer_command != 0 or zero_keeps)

  def wire(self):
    # buildFrame() with STEER_LSB_TOGGLE = 1, outside the lead-in
    steer = self.steer_command
    if steer != 0:
      steer = (steer & ~1) | (self.last_lsb ^ 1)
    self.last_lsb = steer & 1
    return steer


def params(identity=CAR.HONDA_ACCORD_9G, *, pedal=True):
  fp = gen_empty_fingerprint()
  if pedal:
    fp[0][0x201] = 6
  return CarInterface.get_params(identity, fp, [], False, False, False)


# ---- tune ----

@pytest.mark.parametrize("pedal", (True, False))
def test_9g_gets_the_ssv3_tune(pedal):
  cp = params(pedal=pedal)
  assert cp.lateralTuning.which() == "torque"
  assert (SSV3_LAT_ACCEL_FACTOR, SSV3_FRICTION, SSV3_STEER_ACTUATOR_DELAY) == (0.90, 0.12, 0.20)
  assert (cp.lateralTuning.torque.latAccelFactor, cp.lateralTuning.torque.friction, cp.steerActuatorDelay) == \
         pytest.approx((0.90, 0.12, 0.20), abs=1e-6)
  assert cp.lateralTuning.torque.latAccelOffset == 0.0


@pytest.mark.parametrize("identity", (CAR.HONDA_CIVIC, CAR.HONDA_ACCORD, CAR.HONDA_ACCORD_11G, CAR.ACURA_MDX_3G, CAR.HONDA_CRV_5G))
def test_other_hondas_untouched(identity):
  fp = gen_empty_fingerprint()
  before = CarInterface.get_params(identity, fp, [], False, False, False)
  after = CarInterface.get_params(identity, fp, [], False, False, False)
  apply_ssv3_lateral_tune(after)
  assert after.to_dict() == before.to_dict()


# ---- command shaping ----

@pytest.mark.parametrize("raw,lat,last,expected", (
  (0.0, True, 0, 1), (0.0, True, 5, 1), (0.0, True, -5, -1),
  (0.2, True, -5, 1), (-0.2, True, 5, -1), (0.49, True, 0, 1), (-0.49, True, 0, -1),
  (0.6, True, 0, 1), (-0.6, True, 0, -1), (1.4, True, 0, 1), (-1.6, True, 0, -2), (238.7, True, 0, 239), (-239.0, True, 0, -239),
  (0.0, False, 5, 0), (0.4, False, 5, 0), (-0.6, False, 0, -1), (71.7, False, 0, 72),
))
def test_ssv3_steer_command(raw, lat, last, expected):
  assert ssv3_steer_command(raw, lat, last) == expected


def test_rounding_is_symmetric():
  for i in range(-2400, 2401):
    raw = i / 10
    assert ssv3_steer_command(raw, False, 0) == -ssv3_steer_command(-raw, False, 0)
    assert abs(ssv3_steer_command(raw, False, 0) - raw) <= 0.5


def test_board_lsb_toggle_never_crosses_zero():
  for v in list(range(-239, 0)) + list(range(1, 240)):
    b = Board()
    b.steer_command = v
    for _ in range(4):
      w = b.wire()
      assert w * v >= 0, (v, w)          # same sign, or 0 for v = +1
      assert abs(w - v) <= 1
  b = Board()
  b.steer_command = -1
  assert {b.wire() for _ in range(4)} == {-2, -1}


# ---- through the real CarInterface ----

def board_frames(kind, tick):
  if kind == "fw3":
    board = [(400, fw3_400(tick, lkas_ack=True), 0), (427, fw3_427(tick, 0), 0)]
    if tick % 10 == 0:
      board.append((520, ss_status(tick // 10, 3), 0))
  else:
    board = [(400, fw2_400(tick), 0), (427, fw2_427(tick, 0), 0)]
    if tick % 10 == 0:
      board.append((520, ss_status(tick // 10, 2), 0))
  return board


def drive(ci, kind, torques, lat_active=True):
  packer = CANPacker(ACCORD_DBC)
  board = Board()
  out = []
  for tick, torque in enumerate(torques):
    t = 1_000_000_000 + tick * 10_000_000
    ci.update([(t, car_frames(packer, tick, board_frames(kind, tick)))])
    cc = structs.CarControl(latActive=lat_active, enabled=lat_active)
    cc.actuators.torque = torque
    actuators, sends = ci.apply(cc.as_reader(), t)
    e4 = [f for f in sends if f[0] == 0xE4]
    assert len(e4) == 1
    dat = e4[0][1]
    out.append((int.from_bytes(dat[0:2], "big", signed=True), dat[2], board.on_0xe4(dat), actuators.torqueOutputCan))
  return out


NEAR_ZERO = ([0.0] * 50 + [1e-5, -1e-5, 1e-6, 0.0, -0.001, 0.001, 0.002, -0.003] * 20 +
             [0.05 * (1 if i % 40 < 20 else -1) for i in range(200)] + [0.0] * 100)


@pytest.mark.parametrize("kind", ("fw2", "fw3"))
def test_steering_near_zero_never_drops_lkas(kind):
  out = drive(CarInterface(params()), kind, NEAR_ZERO)
  for i, (torque, byte2, board_steers, reported) in enumerate(out):
    assert byte2 & 0x80, i                   # request on every frame
    assert torque != 0 and board_steers, i   # never a 0 that sends LKAS-off
    assert byte2 & 0x0F == 0, i              # no option bits (ZERO_TORQUE_KEEPS_LKAS_ON not used)
    assert reported == torque
  # sign follows the command through the zero crossings: no flip without the command changing sign
  torques = [o[0] for o in out]
  assert max(abs(t) for t in torques[:50]) == 1


@pytest.mark.parametrize("kind", ("fw2", "fw3"))
def test_not_lat_active_sends_zero_and_request_off(kind):
  out = drive(CarInterface(params()), kind, [0.0, 0.3, -0.3, 1e-5] * 25, lat_active=False)
  for torque, byte2, board_steers, _ in out:
    assert torque == 0 and not byte2 & 0x80 and byte2 & 0x0F == 0 and not board_steers


@pytest.mark.parametrize("kind", ("fw2", "fw3"))
def test_disengage_after_steering_drops_to_zero(kind):
  ci = CarInterface(params())
  steering = drive(ci, kind, [0.2] * 50)
  assert all(o[2] for o in steering)
  off = drive(ci, kind, [0.0] * 20, lat_active=False)
  assert all(o[0] == 0 and not o[1] & 0x80 for o in off)
