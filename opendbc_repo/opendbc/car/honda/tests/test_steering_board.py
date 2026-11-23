"""9G TI -> SSV3 fallback (opendbc/car/honda/steering_board.py)."""
import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import SSV3_PARSER_BUS
from opendbc.car.honda.steering_board import TI_MISSING_FRAMES, TiPresence, select_ti, ssv3_present
from opendbc.car.honda.tests.test_ssv3 import car_frames, fw2_400, fw2_427, ss_status
from opendbc.car.honda.torque_interceptor import apply_torque_interceptor, ti_qualified
from opendbc.car.honda.values import CAR, DBC


@pytest.mark.parametrize("enabled,override,missing,ssv3,expected", [
  (True, "", False, True, True),          # Mat's car today: TI, identical
  (True, "auto", False, False, True),
  (True, "", True, False, True),          # record but no SSV3 on the bus: as today
  (True, "", True, True, False),          # TI gone, SSV3 there: fallback
  (False, "", False, True, False),        # TI switched off: the 9G SSV3 path, as today
  (False, "", True, True, False),
  (True, "ssv3", False, True, False),
  (False, "ti", True, True, False),       # TI switch off = SSV3 only, override can't bring the TI back
  (False, "ti", False, True, False),
  (True, b"TI\n", True, True, True),
  (True, None, False, True, True),
])
def test_select_ti(enabled, override, missing, ssv3, expected):
  assert select_ti(enabled, override, missing, ssv3)[0] is expected


def test_ssv3_present():
  fp = gen_empty_fingerprint()
  assert not ssv3_present(fp) and not ssv3_present(None)
  fp[0][0x190] = 4          # SSV2-style 4-byte status is not the SSV3
  assert not ssv3_present(fp)
  fp[2][0x208] = 3          # wrong bus
  assert not ssv3_present(fp)
  fp[0][0x190] = 5
  assert ssv3_present(fp)
  fp = gen_empty_fingerprint()
  fp[0][0x208] = 3
  assert ssv3_present(fp)


def test_ti_presence():
  p = TiPresence()
  for _ in range(TI_MISSING_FRAMES - 1):
    assert not p.update(False, True)
  assert p.update(False, True)
  assert p.update(False, False)           # latched ...
  assert not p.update(True, True)         # ... until the TI answers
  q = TiPresence()
  for _ in range(5 * TI_MISSING_FRAMES):
    assert not q.update(False, False)     # no SSV3 either: never "missing" (behave as today)
  r = TiPresence()
  r.update(True, True)
  for _ in range(5 * TI_MISSING_FRAMES):
    assert not r.update(True, True)


def accord(ti: bool):
  cp = CarInterface.get_params(CAR.HONDA_ACCORD_9G, gen_empty_fingerprint(), [], False, False, False)
  apply_torque_interceptor(cp, ti)
  return cp


def test_ti_drive_has_no_ssv3_objects_and_ssv3_drive_no_ti():
  ti = CarInterface(accord(True))
  assert ti_qualified(ti.CP) and ti.CC.ti is not None and ti.CS.ti_presence is not None
  assert ti.CS.ssv3 is None and ti.CC.ssv3 is None and SSV3_PARSER_BUS not in ti.can_parsers
  ssv3 = CarInterface(accord(False))
  assert not ti_qualified(ssv3.CP) and ssv3.CC.ti is None and ssv3.CS.ti_presence is None
  assert ssv3.CS.ssv3 is not None and ssv3.CC.ssv3 is not None and SSV3_PARSER_BUS in ssv3.can_parsers
  # the fallback safety word is the standard upstream 9G Nidec word (TI bit cleared)
  stock = CarInterface.get_params(CAR.HONDA_ACCORD_9G, gen_empty_fingerprint(), [], False, False, False)
  assert ssv3.CP.safetyConfigs[0].safetyParam == stock.safetyConfigs[0].safetyParam
  assert ssv3.CP.safetyConfigs[0].safetyModel == structs.CarParams.SafetyModel.hondaNidec


def test_ti_drive_without_ti_feedback_raises_steer_fault_after_10s():
  ci = CarInterface(accord(True))
  packer = CANPacker(DBC[CAR.HONDA_ACCORD_9G][Bus.pt])
  cc = structs.CarControl(latActive=True, enabled=True)
  faults = []
  for tick in range(TI_MISSING_FRAMES + 50):
    board = [(400, fw2_400(tick), 0), (427, fw2_427(tick), 0)]
    if tick % 10 == 0:
      board.append((520, ss_status(tick // 10, 2), 0))
    t = 1_000_000_000 + tick * 10_000_000
    cs = ci.update([(t, car_frames(packer, tick, board))])
    ci.apply(cc.as_reader(), t)
    faults.append(cs.steerFaultTemporary)
  assert not any(faults[:TI_MISSING_FRAMES - 1])
  assert all(faults[TI_MISSING_FRAMES:])
  assert ci.CS.ti_presence.missing


def ti_feedback(packer, tick):
  return packer.make_can_msg("TI_FEEDBACK", 0, {"TI_TORQUE_SENSOR": 3, "CHKSUM": 3, "VERSION_NUMBER": 6, "STATE": 3,
                                                "VIOL": 0, "ERROR": 0, "RAMP_DOWN": 0})


@pytest.mark.parametrize("override", ("", "auto", "ti"))
def test_ti_switch_off_means_ssv3_only_with_a_live_ti(override):
  from opendbc.car.honda.steering_board import select_ti, ssv3_present
  fp = gen_empty_fingerprint()
  fp[0].update({0x190: 5, 0x208: 3, 0x24A: 8})   # SSV3 and a talking TI on bus 0
  use_ti, _ = select_ti(False, override, False, ssv3_present(fp))
  assert not use_ti
  ci = CarInterface(accord(use_ti))
  stock = CarInterface.get_params(CAR.HONDA_ACCORD_9G, gen_empty_fingerprint(), [], False, False, False)
  assert ci.CP.safetyConfigs[0].safetyParam == stock.safetyConfigs[0].safetyParam
  assert not ci.CP.safetyConfigs[0].safetyParam & 4096 and ci.CS.ti is None and ci.CC.ti is None
  packer = CANPacker(DBC[CAR.HONDA_ACCORD_9G][Bus.pt])
  cc = structs.CarControl(latActive=True, enabled=True)
  cc.actuators.torque = 0.5
  e4 = []
  for tick in range(200):
    board = [(400, fw2_400(tick), 0), (427, fw2_427(tick), 0), ti_feedback(packer, tick)]
    t = 1_000_000_000 + tick * 10_000_000
    cs = ci.update([(t, car_frames(packer, tick, board))])
    _, sends = ci.apply(cc.as_reader(), t)
    assert not any(f[0] == 0x249 for f in sends)
    e4 += [f for f in sends if f[0] == 0xE4]
  assert cs.canValid and not cs.steerFaultTemporary
  torques = [int.from_bytes(f[1][0:2], "big", signed=True) for f in e4]
  assert min(torques) < 0 and all(f[1][2] & 0x80 for f in e4)   # real 0xE4 torque, request set


def test_ti_path_never_sets_ssv3_option_bits():
  ci = CarInterface(accord(True))
  packer = CANPacker(DBC[CAR.HONDA_ACCORD_9G][Bus.pt])
  cc = structs.CarControl(latActive=True, enabled=True)
  cc.actuators.torque = 0.5
  for tick in range(200):
    board = [(400, fw2_400(tick), 0), ti_feedback(packer, tick)]
    if tick % 10 == 0:
      board.append((520, ss_status(tick // 10, 3), 0))   # even a firmware 3 SSV3
    t = 1_000_000_000 + tick * 10_000_000
    ci.update([(t, car_frames(packer, tick, board))])
    _, sends = ci.apply(cc.as_reader(), t)
    e4 = next(f for f in sends if f[0] == 0xE4)
    assert e4[1][2] & 0x0F == 0 and e4[1][0:2] == b"\x00\x00"
