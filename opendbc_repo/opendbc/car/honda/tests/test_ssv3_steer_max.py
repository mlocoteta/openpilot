"""9G SSV3 path: STEER_MAX 239 (the SSV3 board clamp), decided at startup from CarParams; the TI path keeps 2560.

The SSV3 (LKAS_EPS_V3 firmware 2 and 3) takes 0xE4 STEER_TORQUE as raw wire counts and clamps at 239, so the
old generic Honda 2560 scale saturated the board at ~9% of the command.
"""
import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.tests.test_ssv3 import car_frames, fw2_400, fw2_427, fw3_400, fw3_427, ss_status
from opendbc.car.honda.torque_interceptor import apply_torque_interceptor, ti_qualified
from opendbc.car.honda.values import CAR, DBC, SSV3_STEER_MAX, CarControllerParams


def accord(ti: bool):
  cp = CarInterface.get_params(CAR.HONDA_ACCORD_9G, gen_empty_fingerprint(), [], False, False, False)
  apply_torque_interceptor(cp, ti)
  return cp


def e4_torques(ci, torque, firmware, ticks=150, ti_feedback=False):
  packer = CANPacker(DBC[CAR.HONDA_ACCORD_9G][Bus.pt])
  cc = structs.CarControl(latActive=True, enabled=True)
  cc.actuators.torque = torque
  out = []
  for tick in range(ticks):
    if firmware == 3:
      board = [(400, fw3_400(tick, lkas_ack=True), 0), (427, fw3_427(tick), 0)]
    else:
      board = [(400, fw2_400(tick), 0), (427, fw2_427(tick), 0)]
    if tick % 10 == 0:
      board.append((520, ss_status(tick // 10, firmware), 0))
    if ti_feedback:
      board.append(packer.make_can_msg("TI_FEEDBACK", 0, {"TI_TORQUE_SENSOR": 3, "CHKSUM": 3, "VERSION_NUMBER": 6,
                                                          "STATE": 3, "VIOL": 0, "ERROR": 0, "RAMP_DOWN": 0}))
    t = 1_000_000_000 + tick * 10_000_000
    ci.update([(t, car_frames(packer, tick, board))])
    _, sends = ci.apply(cc.as_reader(), t)
    out += [int.from_bytes(f[1][0:2], "big", signed=True) for f in sends if f[0] == 0xE4]
  return out


def test_params_by_path():
  ssv3 = CarControllerParams(accord(False))
  assert ssv3.STEER_MAX == SSV3_STEER_MAX == 239
  assert ssv3.STEER_LOOKUP == ssv3.STEER_LOOKUP_V == [-239, 0, 239]
  ti_cp = accord(True)
  assert ti_qualified(ti_cp)
  ti = CarControllerParams(ti_cp)
  assert ti.STEER_MAX == 2560 and ti.STEER_LOOKUP == ti.STEER_LOOKUP_V == [-2560, 0, 2560]
  # normalized rate limits unchanged on both paths
  assert (ssv3.STEER_DELTA_UP, ssv3.STEER_DELTA_DOWN) == (ti.STEER_DELTA_UP, ti.STEER_DELTA_DOWN) == (3, 3)


def test_other_hondas_unchanged():
  for car, steer_max in ((CAR.HONDA_ACCORD, 4096), (CAR.ACURA_MDX_3G, 2560), (CAR.HONDA_CIVIC, 2560)):
    cp = CarInterface.get_params(car, gen_empty_fingerprint(), [], False, False, False)
    assert CarControllerParams(cp).STEER_MAX == steer_max


@pytest.mark.parametrize("firmware", (2, 3))
@pytest.mark.parametrize("torque,expected", ((1.0, 239), (-1.0, -239), (0.5, 119), (-0.5, -119), (0.1, 23)))
def test_ssv3_sends_board_scaled_torque(firmware, torque, expected):
  # 0xE4 is positive when steering right, actuators.torque positive = left: sign flips
  torques = e4_torques(CarInterface(accord(False)), torque, firmware)
  assert torques[-1] == -expected
  assert max(abs(x) for x in torques) == abs(expected) <= 239


def test_ssv3_full_command_never_exceeds_239():
  torques = e4_torques(CarInterface(accord(False)), 1.0, 2, ticks=300)
  assert min(torques) == -239 and max(torques) <= 0


def test_ti_path_0xe4_still_zero_and_lookup_untouched():
  ci = CarInterface(accord(True))
  assert ci.CC.params.STEER_MAX == 2560
  assert set(e4_torques(ci, 1.0, 2, ti_feedback=True)) == {0}
