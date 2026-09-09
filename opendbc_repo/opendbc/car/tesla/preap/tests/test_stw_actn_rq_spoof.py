"""Byte-level invariants for Pre-AP stalk spoof frames."""

from opendbc.can import CANPacker
from opendbc.car.tesla.preap.teslacan import TeslaCANPreAP, _STW_DEFAULTS
from opendbc.car.tesla.values import CANBUS, CruiseButtons


def _spoof(button):
  tc = TeslaCANPreAP(CANPacker("tesla_can"))
  msg_stw = {"MC_STW_ACTN_RQ": 5, "CRC_STW_ACTN_RQ": 0, "DTR_Dist_Rq": 255}
  msg_stw.update(_STW_DEFAULTS)
  msg_stw["VSL_Enbl_Rq"] = 0
  _, dat, _ = tc.create_action_request(button, CANBUS.party, 6, msg_stw)
  return dat


def test_vsl_enable_bit_is_set_on_cancel():
  dat = _spoof(CruiseButtons.CANCEL)
  assert (dat[0] >> 6) & 1 == 1


def test_vsl_enable_bit_is_set_on_set_accel():
  dat = _spoof(CruiseButtons.SET_ACCEL)
  assert (dat[0] >> 6) & 1 == 1


def test_stalk_button_and_vsl_bits_match_real_set_accel_frame():
  dat = _spoof(CruiseButtons.SET_ACCEL)
  assert dat[0] == 0x50
