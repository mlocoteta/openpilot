"""TI always-on lateral (F05): the 9G Torque Interceptor car on 7.0's Nidec pedal AOL policy.

The TI word 548|4096 (NIDEC_ALT|GAS_INTERCEPTOR|NIDEC_PEDAL_AOL|TORQUE_INTERCEPTOR) with
alternativeExperience 32 attaches honda_stock_aol.h, and honda_ti.h gates non-zero 0x249 on
lateral_controls_allowed(), i.e. on that policy's lateral permission. TestTiStockAolPolicy runs the
whole stock pedal AOL suite (inherited tests) on the 9G message set with the TI word, then checks
0x249 itself and that no other word or experience attaches AOL to the TI car.
"""
import unittest

from opendbc.car import structs
from opendbc.safety.tests import test_honda_stock_aol as stock
from opendbc.safety.tests.libsafety import libsafety_py
from opendbc.safety.tests.test_honda_ti import HONDA_TI_MAX_STEER, TI, ti_frame

NIDEC = structs.CarParams.SafetyModel.hondaNidec
TI_AOL_WORD = 548 | TI
# 9G message set: SCM_BUTTONS 0x1A6 (MAIN_ON), STEER_STATUS 0x190 (5 bytes), GEARBOX_CVT 0x191 (4 = D).
# These are the ids, lengths and values recorded on the TI car (drive 313, 2026-09-30).
TI_CASE = ("ti-9g-pedal", 1, TI_AOL_WORD, 0, "honda_accord_2017_can_ext_generated", True, "GEARBOX_CVT", 4)
STEERS = (-2048, -600, -599, -1, 1, 599, 600, 2047)


class TestTiStockAolPolicy(stock.TestHondaStockAol):
  """Every stock pedal AOL rule, on the TI car's word and messages."""

  @classmethod
  def setUpClass(cls):
    cls._cases = stock.CASES
    stock.CASES = (TI_CASE,)

  @classmethod
  def tearDownClass(cls):
    stock.CASES = cls._cases

  def configure(self, case, experience=32):
    super().configure(case, experience)
    self.pedal = case[2] == TI_AOL_WORD or self.pedal

  def tx(self, steer):
    address, data, bus = ti_frame(steer)
    return self.safety.safety_tx_hook(libsafety_py.make_CANPacket(address, bus, data))

  def assert_steer(self, allowed):
    self.assertTrue(self.tx(0))  # neutral (0x800 on the wire) always passes
    for steer in STEERS:
      self.assertEqual(self.tx(steer), allowed and abs(steer) <= HONDA_TI_MAX_STEER, steer)

  def test_main_gesture_allows_capped_torque(self):
    self.configure(TI_CASE)
    self.stream()
    self.assertFalse(self.safety.get_controls_allowed())
    self.assert_steer(False)  # MAIN already on at start: no physical grant yet
    self.arm()
    self.assertFalse(self.safety.get_controls_allowed())
    self.assert_steer(True)

  def test_main_off_is_neutral_only_until_main_returns(self):
    self.configure(TI_CASE)
    self.arm()
    self.stream(main=False)
    self.assert_steer(False)
    self.stream(main=False)
    self.assert_steer(False)
    self.stream(main=True)  # MAIN off -> on is a new grant
    self.assert_steer(True)

  def test_stale_main_drops_to_neutral(self):
    self.configure(TI_CASE)
    self.arm()
    self.safety.set_timer(1_000_000 + 300_001)
    self.safety.aol_set_host_request(1)  # host still asks; only the MAIN/EPS/gear sources are stale
    self.assert_steer(False)
    self.stream()
    self.assert_steer(False)  # fresh sources alone do not restore the session
    self.stream(lkas=1)
    self.assert_steer(True)

  def test_stale_main_only_drops_to_neutral_after_300ms(self):
    # Every other source stays fresh; only SCM_BUTTONS (MAIN_ON) stops. The MAIN timestamp limit
    # (300 ms) is tighter than the generic 0x1A6 RX age (400 ms at 25 Hz), so this isolates it.
    self.configure(TI_CASE)
    self.arm()
    for ms in range(10, 360, 10):
      self.safety.set_timer(1_000_000 + ms * 1000)
      self.stream(omit="SCM_BUTTONS")
      if ms <= 290:
        self.assert_steer(True)
      elif ms > 300:
        self.assert_steer(False)

  def test_host_request_required(self):
    self.configure(TI_CASE)
    self.arm()
    self.safety.aol_set_host_request(0)
    self.assert_steer(False)
    self.safety.aol_set_host_request(1)
    self.assert_steer(True)
    self.safety.set_timer(1_000_000 + 300_001)
    self.stream(request=False)  # sources fresh, host request expired
    self.assert_steer(False)

  def test_heartbeat_loss_drops_to_neutral(self):
    self.configure(TI_CASE)
    self.arm()
    self.safety.set_aol_test_heartbeat(False)
    self.assert_steer(False)

  def test_engaged_then_brake_keeps_lateral_with_main(self):
    # 7.0 AOL rule: a brake press ends longitudinal (controls_allowed) but keeps AOL lateral.
    for button in (3, 4):
      with self.subTest(button=button):
        self.configure(TI_CASE)
        self.stream()
        self.normal_engage(button=button)
        self.assertTrue(self.safety.get_controls_allowed())
        self.safety.aol_set_host_request(3)
        self.assert_steer(True)
        self.press_brake()
        self.assertFalse(self.safety.get_controls_allowed())
        self.assert_steer(True)
        self.stream(main=False, cruise=0)
        self.assert_steer(False)

  def test_gas_press_keeps_lateral(self):
    self.configure(TI_CASE)
    self.arm()
    self.stream(gas=1)
    self.assert_steer(True)

  def test_eps_temporary_fault_and_permanent_fault(self):
    self.configure(TI_CASE)
    self.arm()
    for eps in (2, 6):
      self.stream(eps=eps)
      self.assert_steer(False)
      self.stream()
      self.assert_steer(True)
    self.stream(eps=7)
    self.assert_steer(False)
    self.stream()
    self.assert_steer(False)  # a permanent fault needs a new gesture
    self.stream(lkas=1)
    self.assert_steer(True)

  def test_reverse_is_neutral_only(self):
    self.configure(TI_CASE)
    self.arm()
    self.stream(gear=2)
    self.assert_steer(False)

  def test_missing_eps_or_gear_source(self):
    for source in ("STEER_STATUS", "GEARBOX_CVT"):
      with self.subTest(source=source):
        self.configure(TI_CASE)
        self.arm()
        self.safety.set_timer(1_000_000 + 300_001)
        self.stream(omit=source)
        self.assert_steer(False)

  # --- opt-in: only 548|TI with experience 32 attaches AOL to the TI car ---

  def permission_after_gesture(self, word, experience):
    case = ("opt-in", 1, word, 0, TI_CASE[4], True, "GEARBOX_CVT", 4)
    self.configure(case, experience)
    self.pedal = bool(word & 32)
    for main, lkas in ((False, 0), (True, 0), (True, 1)):
      self.stream(main=main, lkas=lkas)
    return self.safety.aol_get_permission_mask()

  def test_policy_attachment(self):
    for word, experience, expected in (
      (TI_AOL_WORD, 32, 1),
      (TI_AOL_WORD, 0, 0),   # AOL toggle off: the TI car steers only while engaged
      (548, 32, 1),          # stock 9G pedal AOL, unchanged
      (36 | TI, 32, 0),
      (36 | TI, 0, 0),
      (4 | TI, 32, 0),       # no-pedal TI car: never AOL
      (4 | TI, 0, 0),
      (TI, 32, 0),
    ):
      with self.subTest(word=word, experience=experience):
        self.assertEqual(self.permission_after_gesture(word, experience), expected)
        if word & TI:
          self.assertTrue(self.tx(0))
          self.assertEqual(self.tx(1), expected == 1)
          self.safety.set_controls_allowed(True)
          if expected == 0:
            # without the policy the 0x249 rule falls back to controls_allowed
            self.assertTrue(self.tx(1))
            self.assertFalse(self.tx(600))
        else:
          self.assertFalse(self.tx(0))  # no TI bit: 0x249 is not in the TX table


if __name__ == "__main__":
  unittest.main()
