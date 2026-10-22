"""Panda rule for the Honda 9G Accord Torque Interceptor (0x249), honda_ti.h.

0x249 may only be sent on Nidec when the TI bit (512) is in the safety param. Neutral is 0x800 on
the wire (12-bit field, +2048 offset). With lateral permission the magnitude cap is 599; without
it only neutral passes. The TI bit must not change any other Nidec decision.
"""
import unittest

from opendbc.can import CANPacker
from opendbc.car import structs
from opendbc.car.honda.nidec_interceptor import create_command
from opendbc.car.honda.torque_interceptor import TI_LIMITS, TI_SAFETY_PARAM, create_ti_steering_control
from opendbc.safety.tests.libsafety import libsafety_py

DBC = "honda_accord_2017_can_ext_generated"
TI = TI_SAFETY_PARAM
STEERS = (-2048, -600, -599, -15, -1, 0, 1, 15, 599, 600, 2047)


def ti_frame(steer, bus=0, length=8):
  # LKAS_REQUEST/CHKSUM: 12-bit with a +2048 offset; KEY bytes as sent by the car.
  raw = steer + 2048
  data = bytes(((raw >> 8) & 0x0F, raw & 0xFF, (raw >> 8) & 0x0F, raw & 0xFF, 0xC4, 0x61, 0xCE, 0x60))
  return 0x249, data[:length], bus


class TestHondaTorqueInterceptor(unittest.TestCase):
  def setUp(self):
    self.safety = libsafety_py.libsafety

  def init(self, word, experience=0):
    self.safety.set_alternative_experience(experience)
    self.assertEqual(self.safety.set_safety_hooks(structs.CarParams.SafetyModel.hondaNidec, word), 0)
    self.safety.init_tests()
    self.safety.set_timer(0)
    self.packer = CANPacker(DBC)

  @staticmethod
  def packet(message):
    return libsafety_py.make_CANPacket(message[0], message[2], message[1])

  def tx(self, message):
    return self.safety.safety_tx_hook(self.packet(message))

  def rx(self, name, bus, values):
    return self.safety.safety_rx_hook(self.packet(self.packer.make_can_msg(name, bus, values)))

  def feed(self, tick, *, button=0, pedal=True):
    self.safety.set_timer(tick * 10_000)
    self.assertTrue(self.rx("ENGINE_DATA", 0, {"XMISSION_SPEED": 30}))
    self.assertTrue(self.rx("POWERTRAIN_DATA", 0, {"ACC_STATUS": 0, "BRAKE_PRESSED": 0, "PEDAL_GAS": 0}))
    self.assertTrue(self.rx("SCM_BUTTONS", 0, {"CRUISE_BUTTONS": button, "MAIN_ON": 1}))
    self.assertTrue(self.rx("BRAKE_COMMAND", 2, {"COMPUTER_BRAKE": 0}))
    if pedal:
      self.assertTrue(self.rx("GAS_SENSOR", 0, {"INTERCEPTOR_GAS": 0, "INTERCEPTOR_GAS2": 0, "STATE": 0}))
    self.safety.safety_tick()

  def engage(self, word):
    self.init(word)
    pedal = bool(word & 32)
    for tick in range(20):
      self.feed(tick, pedal=pedal)
    self.feed(20, button=3, pedal=pedal)
    self.feed(21, button=0, pedal=pedal)
    self.assertTrue(self.safety.get_controls_allowed())

  def test_packer_matches_the_hand_encoding(self):
    packer = CANPacker(DBC)
    for steer in (-599, -15, 0, 15, 599):
      self.assertEqual(create_ti_steering_control(packer, steer), ti_frame(steer))
    self.assertEqual(HONDA_TI_MAX_STEER, TI_LIMITS.TI_STEER_MAX)

  def test_cap_and_neutral_with_and_without_permission(self):
    for word in (36 | TI, 4 | TI):
      for allowed in (True, False):
        self.init(word)
        self.safety.set_controls_allowed(allowed)
        for steer in STEERS:
          expected = steer == 0 or (allowed and abs(steer) <= HONDA_TI_MAX_STEER)
          self.assertEqual(expected, self.tx(ti_frame(steer)), (word, allowed, steer))

  def test_blocked_without_the_ti_bit(self):
    for word in (36, 4, 32, 0):
      for allowed in (True, False):
        self.init(word)
        self.safety.set_controls_allowed(allowed)
        for steer in (0, 15):
          self.assertFalse(self.tx(ti_frame(steer)), (word, allowed, steer))

  def test_wrong_bus_or_length_blocked(self):
    self.init(36 | TI)
    self.safety.set_controls_allowed(True)
    for bus in (1, 2):
      self.assertFalse(self.tx(ti_frame(0, bus=bus)))
    for length in (5, 6, 7):
      self.assertFalse(self.tx(ti_frame(0, length=length)))

  def test_bosch_never_allows_0x249(self):
    for word in (0, 1, 2 | 512):
      self.assertEqual(self.safety.set_safety_hooks(structs.CarParams.SafetyModel.hondaBosch, word), 0)
      self.safety.init_tests()
      self.safety.set_controls_allowed(True)
      self.assertFalse(self.tx(ti_frame(0)))

  def test_ti_bit_keeps_the_pedal_interceptor(self):
    # honda_interceptor_reset compares the exact word; the TI bit must be masked before it.
    self.engage(36 | TI)
    packer = CANPacker(DBC)
    self.assertTrue(self.tx(create_command(packer, 0.5, 0)))
    self.assertTrue(self.tx(ti_frame(HONDA_TI_MAX_STEER)))
    # a button-enabled, pedal-sensing Nidec: MAIN/CANCEL exits, then only neutral passes
    self.feed(22, button=2)
    self.assertFalse(self.safety.get_controls_allowed())
    self.assertFalse(self.tx(ti_frame(1)))
    self.assertTrue(self.tx(ti_frame(0)))

  def test_ti_word_never_attaches_stock_aol(self):
    # The 9G has no factory EPS; stock AOL would add EPS (0x18F/0x190) and gear RX checks. With
    # experience 32, plain word 4 attaches it (those checks go invalid on this stream); 4|512 and
    # 36|512 must stay on the baseline Nidec checks.
    def rx_invalid(word):
      self.init(word, experience=32)
      for tick in range(30):
        self.feed(tick, pedal=bool(word & 32))
      return self.safety.safety_test_toyota_rx_summary_invalid()
    try:
      self.assertTrue(rx_invalid(4))
      self.assertFalse(rx_invalid(4 | TI))
      self.assertFalse(rx_invalid(36 | TI))
      self.assertFalse(self.tx(ti_frame(1)))
    finally:
      self.safety.set_alternative_experience(0)

HONDA_TI_MAX_STEER = 599


if __name__ == "__main__":
  unittest.main()
