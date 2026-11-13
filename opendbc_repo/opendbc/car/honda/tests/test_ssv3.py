"""SSV3 firmware 3 support (opendbc/car/honda/ssv3.py) and the firmware-2 compatibility rule.

Frames are built byte-for-byte like the board firmware builds them (LKAS_EPS_V3: firmware 2 =
src/canMessages.cpp @ ac40e47, firmware 3 = src/can_messages.cpp), not with the DBC packer, so the
tests also check the DBC against the board.
"""
import os
import re

import pytest

from opendbc.can import CANPacker, CANParser
from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.honda.hondacan import honda_checksum
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import (SSV3_PARSER_BUS, Ssv3Option, Ssv3Parser, set_steering_options, signed_motor_torque,
                                    ssv3_qualified)
from opendbc.car.honda.values import CAR, DBC

GEN = os.path.join(os.path.dirname(__file__), "..", "..", "..", "dbc", "generator", "honda")
ACCORD_DBC = DBC[CAR.HONDA_ACCORD_9G][Bus.pt]
MDX_DBC = DBC[CAR.ACURA_MDX_3G][Bus.pt]   # still imports the unchanged _steering_control_d_ext.dbc


def _finish(addr: int, data: bytearray, counter: int) -> bytes:
  # firmware 3 finishFrame(): counter from bit 4 of the last byte, Honda checksum in the low nibble
  data[-1] |= (counter << 4) & 0xF0
  data[-1] |= honda_checksum(addr, None, data)
  return bytes(data)


def fw2_400(counter, driver=0, steer=0, eps_status=0, lkas_allowed=True, steer_blended=False):
  d = bytearray(5)
  d[0] = driver & 0xFF
  d[1] = (driver >> 8) & 0x01
  d[1] |= (not lkas_allowed) << 1
  d[1] |= (eps_status << 4) & 0x70
  d[1] |= ((not lkas_allowed) << 5) & 0x10
  d[2] = (steer >> 8) & 0xFF
  d[3] = steer & 0xFF
  d[4] = (counter & 3) << 4
  d[4] |= honda_checksum(400, None, d)
  d[4] |= steer_blended << 7       # firmware 2 ORs this in AFTER the checksum
  return bytes(d)


def fw2_427(counter, torque=0):
  d = bytearray([0x80 | ((torque >> 8) & 0x03), torque & 0xFF, (counter & 3) << 4])
  d[2] |= honda_checksum(427, None, d)
  return bytes(d)


def ss_status(counter, version, hw=4, lkas_blocked=False):
  d = bytearray([version | (hw << 4), lkas_blocked << 4, 0])
  return _finish(520, d, counter & 3)


def fw3_400(counter, driver=0, steer=0, eps_status=0, lkas_ack=False, camera_fault=False):
  d = bytearray(5)
  d[0] = driver & 0xFF
  d[1] = (driver >> 8) & 0x01
  d[1] |= (eps_status << 4) & 0x70
  d[2] = (steer >> 8) & 0xFF
  d[3] = steer & 0xFF
  d[4] = (lkas_ack << 7) | (camera_fault << 6)
  return _finish(400, d, counter & 3)


def fw3_427(counter, torque=0):
  t = torque & 0x3FF
  return _finish(427, bytearray([0x80 | (t >> 8), t & 0xFF, 0]), counter & 3)


def fw3_raw(addr, counter, payload):
  return _finish(addr, bytearray(payload[:7]) + bytearray(1), counter & 15)


# ---- DBC (work item 1) ----

def _lines(path, prefix):
  with open(path) as f:
    return [line.rstrip("\n") for line in f if line.startswith(prefix)]


def test_ssv3_fragment_is_strictly_additive_over_d_ext():
  base = os.path.join(GEN, "_steering_control_d_ext.dbc")
  ssv3 = os.path.join(GEN, "_steering_control_d_ssv3.dbc")
  new_lines = set(_lines(ssv3, (" SG_", "BO_", "VAL_")))
  for line in _lines(base, (" SG_", "BO_", "VAL_")):
    assert line in new_lines, f"changed or missing vs _steering_control_d_ext.dbc: {line}"
  # 427 MOTOR_TORQUE in the shared _honda_common.dbc keeps its unsigned definition
  assert " SG_ MOTOR_TORQUE : 1|10@0+ (1,0) [0|256] \"\" EON" in _lines(os.path.join(GEN, "_honda_common.dbc"), " SG_")


def test_only_the_9g_imports_the_ssv3_fragment():
  for name in os.listdir(GEN):
    if name.endswith(".dbc") and not name.startswith("_"):
      text = open(os.path.join(GEN, name)).read()
      assert ("_steering_control_d_ssv3.dbc" in text) == (name == "honda_accord_2017_can_ext.dbc"), name


@pytest.mark.parametrize("torque", (-3840, -255, -1, 0, 1, 77, 255, 3840))
@pytest.mark.parametrize("request_", (0, 1))
def test_0xe4_bytes_unchanged_by_the_dbc_change(torque, request_):
  old, new = CANPacker(MDX_DBC), CANPacker(ACCORD_DBC)
  for _ in range(6):   # walk the counter
    values = {"STEER_TORQUE": torque, "STEER_TORQUE_REQUEST": request_}
    assert new.make_can_msg("STEERING_CONTROL", 0, values) == old.make_can_msg("STEERING_CONTROL", 0, values)


@pytest.mark.parametrize("options", range(16))
def test_option_bits_match_the_dbc(options):
  packer = CANPacker(ACCORD_DBC)
  base = packer.make_can_msg("STEERING_CONTROL", 0, {"STEER_TORQUE": -120, "STEER_TORQUE_REQUEST": 1})
  packer2 = CANPacker(ACCORD_DBC)
  names = ("TORQUE_BLEND_DISABLE", "TX_ALL_LKAS_DATA", "LSB_TOGGLE_DISABLE", "ZERO_TORQUE_KEEPS_LKAS_ON")
  values = {"STEER_TORQUE": -120, "STEER_TORQUE_REQUEST": 1} | {n: (options >> i) & 1 for i, n in enumerate(names)}
  expected = packer2.make_can_msg("STEERING_CONTROL", 0, values)
  assert set_steering_options(base[1], options) == expected[1]
  parser = CANParser(ACCORD_DBC, [("STEERING_CONTROL", 0)], 0)
  parser.update([(1, [(0xE4, set_steering_options(base[1], options), 0)])])
  assert parser.vl["STEERING_CONTROL"]["STEER_TORQUE"] == -120
  for i, n in enumerate(names):
    assert parser.vl["STEERING_CONTROL"][n] == (options >> i) & 1


def test_board_frames_decode_and_4bit_counters_pass_the_parser():
  parser = CANParser(ACCORD_DBC, [("STEER_STATUS", 0), ("SS_STATUS", 0), ("LKAS_RAW", 0), ("EPS_RAW", 0)], 0)
  for i in range(40):   # 4-bit counters on 523/524 wrap 15 -> 0 twice
    t = 1_000_000_000 + i * 10_000_000
    frames = [(400, fw3_400(i, driver=-37, steer=-200, eps_status=0, lkas_ack=True, camera_fault=True), 0),
              (523, fw3_raw(523, i, [0x20, 0x81, 0x04, 0x7F, 0x20, 0x81, 0x04]), 0),
              (524, fw3_raw(524, i, [1, 2, 3, 4, 5, 0xAB, (2 << 6) | (1 << 5) | 7]), 0)]
    if i % 10 == 0:
      frames.append((520, ss_status(i // 10, 3), 0))
    parser.update([(t, frames)])
  assert parser.can_valid
  for state in parser.message_states.values():
    assert state.counter_fail == 0, state.name
  assert parser.vl["STEER_STATUS"]["STEER_TORQUE_SENSOR"] == -37
  assert parser.vl["STEER_STATUS"]["STEER_APPLIED"] == -200
  assert parser.vl["STEER_STATUS"]["EPS_LKAS_ACK"] == 1 and parser.vl["STEER_STATUS"]["CAMERA_FAULT"] == 1
  assert parser.vl["SS_STATUS"]["VERSION_NUM"] == 3 and parser.vl["SS_STATUS"]["HARDWARE_REV"] == 4
  assert parser.vl["EPS_RAW"]["MODE"] == 2 and parser.vl["EPS_RAW"]["STEER_REQUEST"] == 1
  assert parser.vl["EPS_RAW"]["CAMERA_FRAME_AGE"] == 7 and parser.vl["EPS_RAW"]["BOARD_TIME"] == 0xAB
  assert parser.vl["LKAS_RAW"]["CAMERA_B1"] == 0x81


@pytest.mark.parametrize("value", (-128, -1, 0, 1, 127))
def test_signed_motor_torque(value):
  parser = CANParser(ACCORD_DBC, [("STEER_MOTOR_TORQUE", 0)], 0)
  parser.update([(1, [(427, fw3_427(0, value), 0)])])
  assert signed_motor_torque(parser.vl["STEER_MOTOR_TORQUE"]["MOTOR_TORQUE"]) == value


# ---- carState / carController through the real CarInterface (work items 2, 3) ----

def accord():
  return CarInterface.get_params(CAR.HONDA_ACCORD_9G, gen_empty_fingerprint(), [], False, False, False)


def car_frames(packer, tick, ssv3_frames):
  from opendbc.car.honda.tests.test_nidec_interceptor import source_frames
  cp = accord()
  frames = [f for f in source_frames(cp, packer, tick, sensor=False) if f[0] not in (0x190,)]
  return frames + ssv3_frames


def run(ci, kind, ticks, options=0, request=True, torque=0.3):
  """Feeds `ticks` frames of a board of `kind` ('fw2', 'fw2_no520', 'fw3', 'none') and returns
  (carStates, 0xE4 frames)."""
  packer = CANPacker(ACCORD_DBC)
  if ci.CC.ssv3 is not None:
    ci.CC.ssv3.requested_options = options
  states, e4 = [], []
  cc = structs.CarControl(latActive=request, enabled=request)
  cc.actuators.torque = torque
  for tick in range(ticks):
    board = []
    if kind == "fw2" or kind == "fw2_no520":
      board = [(400, fw2_400(tick, driver=5, steer=100, steer_blended=tick % 7 == 0), 0), (427, fw2_427(tick, 300), 0)]
      if kind == "fw2" and tick % 10 == 0:
        board.append((520, ss_status(tick // 10, 2), 0))
    elif kind == "fw3":
      board = [(400, fw3_400(tick, driver=5, steer=100, lkas_ack=True), 0), (427, fw3_427(tick, -60), 0)]
      if tick % 10 == 0:
        board.append((520, ss_status(tick // 10, 3), 0))
    else:
      board = [(400, fw2_400(tick, driver=5), 0)]
    t = 1_000_000_000 + tick * 10_000_000
    states.append(ci.update([(t, car_frames(packer, tick, board))]))
    _, sends = ci.apply(cc.as_reader(), t)
    e4 += [f for f in sends if f[0] == 0xE4]
  return states, e4


def upstream_ci():
  """The same car with the SSV3 additions switched off = Dom before this change."""
  ci = CarInterface(accord())
  ci.CC.ssv3 = None
  ci.CS.ssv3 = None
  ci.can_parsers.pop(SSV3_PARSER_BUS, None)
  return ci


def test_9g_is_qualified_and_has_the_advisory_parser():
  cp = accord()
  assert ssv3_qualified(cp)
  ci = CarInterface(cp)
  assert isinstance(ci.can_parsers[SSV3_PARSER_BUS], Ssv3Parser)
  for other in (CAR.ACURA_MDX_3G, CAR.HONDA_CIVIC):
    assert not ssv3_qualified(CarInterface.get_params(other, gen_empty_fingerprint(), [], False, False, False))


@pytest.mark.parametrize("kind", ("fw2", "fw2_no520", "none"))
def test_firmware2_output_is_identical_with_every_option_requested(kind):
  ci_new = CarInterface(accord())
  states_new, e4_new = run(ci_new, kind, 300, options=Ssv3Option.ALL)
  states_old, e4_old = run(upstream_ci(), kind, 300)
  assert e4_new == e4_old and len(e4_new) == 300
  assert all((f[1][2] & 0x0F) == 0 for f in e4_new)
  assert not ci_new.CS.ssv3.fw3
  for a, b in zip(states_new, states_old, strict=True):
    assert a.canValid == b.canValid and a.canTimeout == b.canTimeout
    assert a.steeringTorque == b.steeringTorque and a.steeringTorqueEps == b.steeringTorqueEps == 0
    assert a.steerFaultTemporary == b.steerFaultTemporary and a.steerFaultPermanent == b.steerFaultPermanent


def test_firmware3_without_options_sends_upstream_bytes():
  _, e4_new = run(CarInterface(accord()), "fw3", 200)
  _, e4_old = run(upstream_ci(), "fw3", 200)
  assert e4_new == e4_old


def test_firmware3_options_only_after_confirmation():
  ci = CarInterface(accord())
  states, e4 = run(ci, "fw3", 60, options=Ssv3Option.TORQUE_BLEND_DISABLE | Ssv3Option.ZERO_TORQUE_KEEPS_LKAS_ON)
  assert ci.CS.ssv3.fw3 and ci.CS.ssv3.version == 3
  # 520 at ticks 0, 10, 20 -> confirmed in tick 20; nothing before it carries an option
  assert all((f[1][2] & 0x0F) == 0 for f in e4[:20])
  assert all((f[1][2] & 0x0F) == 0x09 for f in e4[20:])
  parser = CANParser(ACCORD_DBC, [("STEERING_CONTROL", 0)], 0)
  for i, f in enumerate(e4):
    parser.update([(1_000_000_000 + i * 10_000_000, [f])])
  assert parser.can_valid and parser.message_states[0xE4].counter_fail == 0
  assert states[-1].steeringTorqueEps == -60
  assert ci.CS.ssv3.eps_lkas_ack and not ci.CS.ssv3.camera_fault
  assert all(s.canValid for s in states[5:])


def test_bad_or_garbled_520_never_reaches_canvalid_or_unlocks_options():
  ci = CarInterface(accord())
  packer = CANPacker(ACCORD_DBC)
  ci.CC.ssv3.requested_options = Ssv3Option.ALL
  cc = structs.CarControl(latActive=True, enabled=True)
  for tick in range(200):
    bad = bytearray(ss_status(0, 3))
    bad[2] ^= 0x01   # wrong checksum every time
    board = [(400, fw2_400(tick), 0), (427, fw2_427(tick), 0), (520, bytes(bad), 0)]
    t = 1_000_000_000 + tick * 10_000_000
    cs = ci.update([(t, car_frames(packer, tick, board))])
    _, sends = ci.apply(cc.as_reader(), t)
    assert all((f[1][2] & 0x0F) == 0 for f in sends if f[0] == 0xE4)
  assert cs.canValid and not ci.CS.ssv3.fw3


def test_no_option_bits_can_come_from_anywhere_but_the_controller():
  # every Python caller of create_steering_control keeps byte 2 low nibble zero
  src = open(os.path.join(os.path.dirname(__file__), "..", "hondacan.py")).read()
  body = re.search(r"def create_steering_control\(.*?\n\n\n", src, re.S).group(0)
  for name in ("TORQUE_BLEND_DISABLE", "TX_ALL_LKAS_DATA", "LSB_TOGGLE_DISABLE", "ZERO_TORQUE_KEEPS_LKAS_ON"):
    assert name not in body


def test_firmware3_drops_back_to_firmware2_when_520_stops():
  ci = CarInterface(accord())
  packer = CANPacker(ACCORD_DBC)
  ci.CC.ssv3.requested_options = Ssv3Option.LSB_TOGGLE_DISABLE
  cc = structs.CarControl(latActive=True, enabled=True)
  opts = []
  for tick in range(200):
    board = [(400, fw3_400(tick, lkas_ack=True), 0), (427, fw3_427(tick, -60), 0)]
    if tick < 60 and tick % 10 == 0:
      board.append((520, ss_status(tick // 10, 3), 0))
    t = 1_000_000_000 + tick * 10_000_000
    cs = ci.update([(t, car_frames(packer, tick, board))])
    _, sends = ci.apply(cc.as_reader(), t)
    opts.append(next(f for f in sends if f[0] == 0xE4)[1][2] & 0x0F)
  assert opts[30] == Ssv3Option.LSB_TOGGLE_DISABLE
  # last 520 at tick 50; firmware 3 must be gone 0.5 s later and stay gone
  assert all(o == 0 for o in opts[102:])
  assert not ci.CS.ssv3.fw3 and cs.steeringTorqueEps == 0 and not ci.CS.ssv3.eps_lkas_ack
