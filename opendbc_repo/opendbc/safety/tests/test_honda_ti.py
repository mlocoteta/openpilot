"""Panda rule for the Honda 9G Accord Torque Interceptor (0x249), honda_ti.h.

0x249 may only be sent on Nidec when the TI bit (32768) is in the safety param. Neutral is 0x800 on
the wire (12-bit field, +2048 offset). With lateral permission the magnitude cap is 599; without
it only neutral passes. The TI bit must not change any other Nidec decision.
"""
import re
import unittest
from pathlib import Path

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
    for word in (0, 1, 2 | 512, 2 | 4096, TI, 1 | TI, 2 | TI, 4096 | TI):
      self.assertEqual(self.safety.set_safety_hooks(structs.CarParams.SafetyModel.hondaBosch, word), 0)
      self.safety.init_tests()
      self.safety.set_controls_allowed(True)
      self.assertFalse(self.tx(ti_frame(0)))

  def test_ti_bit_is_no_other_honda_param(self):
    # A panda flag that reuses the TI bit merges without a git conflict; it has to fail here.
    params = {}
    for path in sorted((Path(__file__).parents[1] / "modes").glob("honda*.h")):
      for name, value in re.findall(r"\bHONDA_PARAM_(\w+)\s*=?\s*(0x[0-9a-fA-F]+|\d+)U?\b", path.read_text(encoding="utf-8")):
        params.setdefault(name, set()).add(int(value, 0))
    self.assertEqual(params.pop("TORQUE_INTERCEPTOR"), {TI})
    self.assertGreater(len(params), 3)  # the pattern still finds the other flags
    for name, values in params.items():
      for value in values:
        self.assertFalse(value & TI, name)

  def test_the_former_bit_4096_enables_nothing(self):
    # 4096 was the TI bit until upstream took it for ACCORD_ANGLE (Bosch only). On Nidec it is not TI, and it
    # still breaks the exact pedal words, so a stale word has no 0x249 and no gas command.
    for word in (4 | 4096, 36 | 4096, 548 | 4096):
      for experience in (0, 32):
        self.init(word, experience=experience)
        for tick in range(20):
          self.feed(tick, pedal=False)
        self.safety.set_controls_allowed(True)
        self.assertFalse(self.tx(ti_frame(0)), (word, experience))
        self.assertFalse(self.tx(create_command(self.packer, 0.5, 0)), (word, experience))
    self.safety.set_alternative_experience(0)

  def test_angle_setpoint_frames_stay_blocked_on_the_ti_car(self):
    # Upstream's rule: an 0xE4 frame with STEER_CONTROL_ARM 2 is only for the Bosch Accord angle-loop EPS. The TI
    # car sends 0xE4 with zero torque and no option bits, and the TI bit never makes a Bosch car angle capable.
    nidec, bosch = structs.CarParams.SafetyModel.hondaNidec, structs.CarParams.SafetyModel.hondaBosch
    for model, word in ((nidec, 4 | TI), (nidec, 36 | TI), (nidec, 548 | TI), (bosch, TI), (bosch, 1 | TI)):
      self.assertEqual(self.safety.set_safety_hooks(model, word), 0)
      self.safety.init_tests()
      for allowed in (True, False):
        self.safety.set_controls_allowed(allowed)
        for request in (0x00, 0x80):
          for arm in range(4):
            packet = libsafety_py.make_CANPacket(0xE4, 0, bytes((0, 0, request | (arm << 2), 0, 0)))
            self.assertEqual(arm != 2, bool(self.safety.safety_tx_hook(packet)), (model, word, allowed, request, arm))

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
    # experience 32, plain word 4 and the 7.0 Nidec pedal AOL word 548 (36|512) attach it (those
    # checks go invalid on this stream); 4|TI, 36|TI and 548|TI must stay on the baseline Nidec checks.
    def rx_invalid(word):
      self.init(word, experience=32)
      for tick in range(30):
        self.feed(tick, pedal=bool(word & 32))
      return self.safety.safety_test_toyota_rx_summary_invalid()
    try:
      self.assertTrue(rx_invalid(4))
      self.assertFalse(rx_invalid(4 | TI))
      self.assertFalse(rx_invalid(36 | TI))
      self.assertTrue(rx_invalid(548))
      # F05: 548|TI is the TI AOL word and attaches the same policy (test_honda_ti_aol.py)
      self.assertTrue(rx_invalid(548 | TI))
      self.assertFalse(self.tx(ti_frame(1)))
    finally:
      self.safety.set_alternative_experience(0)

HONDA_TI_MAX_STEER = 599


if __name__ == "__main__":
  unittest.main()
