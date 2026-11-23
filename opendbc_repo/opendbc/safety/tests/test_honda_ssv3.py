"""Panda rule for the 9G Accord SSV3 board's 0xE4 option bits (honda_ssv3.h).

On the 9G, 0xE4 byte 2 bits 0-3 are SSV3 options. The Bosch Accord's angle-loop EPS uses bits 2-3 as STEER_CONTROL_ARM,
and honda.h blocks ARM 2 on every car without that EPS. ZERO_TORQUE_KEEPS_LKAS_ON alone reads as ARM 2, so the rule
would take all steering from an SSV3 car with that option. Only the words an SSV3 9G can run are exempt, and the
torque rule still applies to them.
"""
import unittest
from types import SimpleNamespace

from opendbc.can import CANPacker
from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda.hondacan import create_steering_control
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import Ssv3Option, set_steering_options, ssv3_qualified
from opendbc.car.honda.tests.test_ssv3 import accord, run
from opendbc.car.honda.torque_interceptor import TI_BASE_SAFETY_PARAMS, TI_SAFETY_PARAM as TI, apply_torque_interceptor
from opendbc.car.honda.values import CAR, HondaSafetyFlags
from opendbc.safety.tests.libsafety import libsafety_py

NIDEC = structs.CarParams.SafetyModel.hondaNidec
BOSCH = structs.CarParams.SafetyModel.hondaBosch
DBC = "honda_accord_2017_can_ext_generated"
SSV3_WORDS = (4, 36, 548)  # NIDEC_ALT, + GAS_INTERCEPTOR, + NIDEC_PEDAL_AOL
TORQUES = (-240, -1, 0, 1, 240)
ARM_2 = 0x08  # byte 2 bits 3:2 = 0b10 = ZERO_TORQUE_KEEPS_LKAS_ON without LSB_TOGGLE_DISABLE


def arm(options):
  return (options >> 2) & 0x3


class TestHondaSsv3Options(unittest.TestCase):
  def setUp(self):
    self.safety = libsafety_py.libsafety
    self.packer = CANPacker(DBC)

  def tearDown(self):
    self.safety.set_alternative_experience(0)

  def init(self, model, word, experience=0):
    self.safety.set_alternative_experience(experience)
    self.assertEqual(self.safety.set_safety_hooks(model, word), 0)
    self.safety.init_tests()

  def tx(self, torque, options, request=True, bus=0):
    address, data, _ = create_steering_control(self.packer, SimpleNamespace(lkas=0), torque, request, False)
    return bool(self.safety.safety_tx_hook(libsafety_py.make_CANPacket(address, bus, set_steering_options(data, options))))

  def test_the_exempt_words_are_the_9g_words(self):
    words = set()
    for pedal in (True, False):
      fingerprint = gen_empty_fingerprint()
      if pedal:
        fingerprint[0][0x201] = 6
      cp = CarInterface.get_params(CAR.HONDA_ACCORD_9G, fingerprint, [], False, False, False)
      apply_torque_interceptor(cp, False)
      self.assertTrue(ssv3_qualified(cp))
      words.add(int(cp.safetyConfigs[0].safetyParam))
    words.add(36 | int(HondaSafetyFlags.NIDEC_PEDAL_AOL))  # 7.0's pedal AOL addition
    self.assertEqual(words, set(SSV3_WORDS))
    self.assertEqual(set(TI_BASE_SAFETY_PARAMS), set(SSV3_WORDS))
    self.assertEqual(arm(Ssv3Option.ZERO_TORQUE_KEEPS_LKAS_ON), 2)
    self.assertEqual(Ssv3Option.ZERO_TORQUE_KEEPS_LKAS_ON, ARM_2)

  def test_every_option_passes_and_torque_still_needs_permission(self):
    for word in SSV3_WORDS:
      for options in range(Ssv3Option.ALL + 1):
        for allowed in (True, False):
          self.init(NIDEC, word)
          self.safety.set_controls_allowed(allowed)
          for torque in TORQUES:
            self.assertEqual(allowed or torque == 0, self.tx(torque, options), (word, options, allowed, torque))

  def test_options_pass_on_the_aol_word_without_engagement(self):
    # experience 32 attaches stock pedal AOL: no session here, so only zero torque passes, with any option
    self.init(NIDEC, 548, experience=32)
    self.safety.set_controls_allowed(False)
    for options in range(Ssv3Option.ALL + 1):
      for torque in TORQUES:
        self.assertEqual(torque == 0, self.tx(torque, options), (options, torque))

  def test_every_other_honda_word_keeps_the_angle_rule(self):
    nidec = (0, 32, 260, 544, 804, 4 | 4096, 36 | 4096, 548 | 4096, 4 | TI, 36 | TI, 548 | TI, TI)
    bosch = (0, 1, 2, 3, 4, 8, 9, 16, 36, 80, 512, 548, 4 | TI, 36 | TI, 548 | TI)
    for model, words in ((NIDEC, nidec), (BOSCH, bosch)):
      for word in words:
        self.init(NIDEC, 36)  # an SSV3 word first: the next init must not inherit it
        self.init(model, word)
        self.safety.set_controls_allowed(True)
        for bus in (0, 1):
          for options in range(Ssv3Option.ALL + 1):
            if arm(options) == 2:
              self.assertFalse(self.tx(0, options, bus=bus), (model, word, bus, options))
            elif model == NIDEC and bus == 0:
              self.assertTrue(self.tx(0, options, bus=bus), (model, word, options))

  def test_the_car_controllers_own_frames_pass(self):
    # firmware 3 confirmed at tick 20; from there every 0xE4 carries the option that reads as ARM 2
    options = Ssv3Option.TORQUE_BLEND_DISABLE | Ssv3Option.ZERO_TORQUE_KEEPS_LKAS_ON
    _, frames = run(CarInterface(accord()), "fw3", 60, options=options)
    self.assertTrue(all(arm(data[2]) == 2 for _, data, _ in frames[20:]))
    self.assertTrue(any(data[0] or data[1] for _, data, _ in frames[20:]))
    self.init(NIDEC, int(accord().safetyConfigs[0].safetyParam))
    self.safety.set_controls_allowed(True)
    for address, data, bus in frames:
      self.assertTrue(self.safety.safety_tx_hook(libsafety_py.make_CANPacket(address, bus, data)))


if __name__ == "__main__":
  unittest.main()
