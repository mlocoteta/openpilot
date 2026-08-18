#!/usr/bin/env python3
import unittest

from opendbc.car import make_tester_present_msg
from opendbc.car.nissan import nissancan
from opendbc.car.nissan.values import NissanSafetyFlags
from opendbc.car.structs import CarParams
from opendbc.safety import ALTERNATIVE_EXPERIENCE
from opendbc.safety.tests.libsafety import libsafety_py
import opendbc.safety.tests.common as common
from opendbc.safety.tests.common import CANPackerSafety


class TestNissanSafety(common.CarSafetyTest, common.AngleSteeringSafetyTest):

  TX_MSGS = [[0x169, 0], [0x2b1, 0], [0x4cc, 0], [0x20b, 2], [0x280, 2]]
  GAS_PRESSED_THRESHOLD = 3
  RELAY_MALFUNCTION_ADDRS = {0: (0x169, 0x2b1, 0x4cc), 2: (0x280,)}
  FWD_BLACKLISTED_ADDRS = {0: [0x280], 2: [0x169, 0x2b1, 0x4cc]}

  EPS_BUS = 0
  CRUISE_BUS = 2
  PRO_PILOT_BUS = 1

  # Angle control limits
  STEER_ANGLE_MAX = 600  # deg, reasonable limit
  DEG_TO_CAN = 100

  ANGLE_RATE_BP = [0., 5., 15.]
  ANGLE_RATE_UP = [5., .8, .15]  # windup limit
  ANGLE_RATE_DOWN = [5., 3.5, .4]  # unwind limit

  def setUp(self):
    self.packer = CANPackerSafety("nissan_x_trail_2017_generated")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.nissan, 0)
    self.safety.init_tests()

  def _angle_cmd_msg(self, angle: float, enabled: bool):
    values = {"DESIRED_ANGLE": angle, "LKA_ACTIVE": 1 if enabled else 0}
    return self.packer.make_can_msg_safety("LKAS", 0, values)

  def _angle_meas_msg(self, angle: float):
    values = {"STEER_ANGLE": angle}
    return self.packer.make_can_msg_safety("STEER_ANGLE_SENSOR", self.EPS_BUS, values)

  def _pcm_status_msg(self, enable):
    values = {"CRUISE_ENABLED": enable}
    return self.packer.make_can_msg_safety("CRUISE_STATE", self.CRUISE_BUS, values)

  def _speed_msg(self, speed):
    values = {"WHEEL_SPEED_%s" % s: speed * 3.6 for s in ["RR", "RL"]}
    return self.packer.make_can_msg_safety("WHEEL_SPEEDS_REAR", self.EPS_BUS, values)

  def _user_brake_msg(self, brake):
    values = {"USER_BRAKE_PRESSED": brake}
    return self.packer.make_can_msg_safety("DOORS_LIGHTS", self.EPS_BUS, values)

  def _user_gas_msg(self, gas):
    values = {"GAS_PEDAL": gas}
    return self.packer.make_can_msg_safety("GAS_PEDAL", self.EPS_BUS, values)

  def _acc_button_cmd(self, cancel=0, propilot=0, flw_dist=0, _set=0, res=0):
    no_button = not any([cancel, propilot, flw_dist, _set, res])
    values = {"CANCEL_BUTTON": cancel, "PROPILOT_BUTTON": propilot,
              "FOLLOW_DISTANCE_BUTTON": flw_dist, "SET_BUTTON": _set,
              "RES_BUTTON": res, "NO_BUTTON_PRESSED": no_button}
    return self.packer.make_can_msg_safety("CRUISE_THROTTLE", 2, values)

  def test_acc_buttons(self):
    btns = [
      ("cancel", True),
      ("propilot", False),
      ("flw_dist", False),
      ("_set", False),
      ("res", False),
      (None, False),
    ]
    for controls_allowed in (True, False):
      for btn, should_tx in btns:
        self.safety.set_controls_allowed(controls_allowed)
        args = {} if btn is None else {btn: 1}
        tx = self._tx(self._acc_button_cmd(**args))
        self.assertEqual(tx, should_tx)

  def _toggle_aol(self, toggle_on):
    # PRO_PILOT, CRUISE_ON is the main on button for X-Trail/Rogue/Altima
    values = {"CRUISE_ON": 1 if toggle_on else 0}
    return self.packer.make_can_msg_panda("PRO_PILOT", self.PRO_PILOT_BUS, values)

  def test_aol_remains_allowed_after_cruise_cancel(self):
    self.safety.set_alternative_experience(ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL)
    self._rx(self._toggle_aol(True))
    self._rx(self._pcm_status_msg(True))
    self.assertTrue(self.safety.get_controls_allowed())

    self._rx(self._pcm_status_msg(False))
    self.assertFalse(self.safety.get_controls_allowed())

    self._reset_angle_measurement(0)
    self._reset_speed_measurement(1)
    self._set_prev_desired_angle(0)
    self.assertTrue(self._tx(self._angle_cmd_msg(angle=self.ANGLE_RATE_UP[0] / 2.0, enabled=True)))


class TestNissanSafetyAltEpsBus(TestNissanSafety):
  """Altima uses different buses"""

  EPS_BUS = 1
  CRUISE_BUS = 1
  PRO_PILOT_BUS = 2

  def setUp(self):
    self.packer = CANPackerSafety("nissan_x_trail_2017_generated")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.nissan, NissanSafetyFlags.ALT_EPS_BUS)
    self.safety.init_tests()


class TestNissanLeafSafety(TestNissanSafety):

  def setUp(self):
    self.packer = CANPackerSafety("nissan_leaf_2018_generated")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.nissan, 0)
    self.safety.init_tests()

  def _user_brake_msg(self, brake):
    values = {"USER_BRAKE_PRESSED": brake}
    return self.packer.make_can_msg_safety("CRUISE_THROTTLE", 0, values)

  def _user_gas_msg(self, gas):
    values = {"GAS_PEDAL": gas}
    return self.packer.make_can_msg_safety("CRUISE_THROTTLE", 0, values)

  # TODO: leaf should use its own safety param
  def test_acc_buttons(self):
    pass

  def _toggle_aol(self, toggle_on):
    # CRUISE_THROTTLE, CRUISE_AVAILABLE is the main on button for Leaf
    values = {"CRUISE_AVAILABLE": 1 if toggle_on else 0}
    return self.packer.make_can_msg_panda("CRUISE_THROTTLE", 0, values)


class TestNissanLeafLongSafety(TestNissanLeafSafety):

  TX_MSGS = [*TestNissanLeafSafety.TX_MSGS, [0x2B0, 1], [0x1C3, 1], [0x707, 0]]
  RELAY_MALFUNCTION_ADDRS = {0: (0x169, 0x2B1, 0x4CC), 1: (0x2B0, 0x1C3), 2: (0x280,)}
  FWD_BLACKLISTED_ADDRS = {0: [0x280], 2: [0x169, 0x2B1, 0x4CC]}

  def setUp(self):
    self.packer = CANPackerSafety("nissan_leaf_2018_generated")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.nissan, NissanSafetyFlags.LONG_CONTROL)
    self.safety.init_tests()

  @staticmethod
  def _make_msg(can_data):
    return common.make_msg(can_data.src, can_data.address, len(can_data.dat), can_data.dat)

  def _accel_msg(self, raw_command, active=True):
    return self._make_msg(nissancan.create_accel_command(raw_command, 0, active))

  def _brake_msg(self, pressure, active=None, brake_mode=True):
    if active is None:
      active = pressure > 0
    return self._make_msg(nissancan.create_brake_command(pressure, 0, active, brake_mode))

  def _button_msg(self, main=True, set_button=False, res_button=False, cancel_button=False):
    values = {
      "CRUISE_AVAILABLE": main,
      "SET_BUTTON": set_button,
      "RES_BUTTON": res_button,
      "CANCEL_BUTTON": cancel_button,
      "NO_BUTTON_PRESSED": not any((set_button, res_button, cancel_button)),
    }
    return self.packer.make_can_msg_safety("CRUISE_THROTTLE", 0, values)

  def _user_brake_msg(self, brake):
    values = {"USER_BRAKE_PRESSED": brake, "CRUISE_AVAILABLE": 1, "NO_BUTTON_PRESSED": 1}
    return self.packer.make_can_msg_safety("CRUISE_THROTTLE", 0, values)

  def _user_gas_msg(self, gas):
    values = {"GAS_PEDAL": gas, "CRUISE_AVAILABLE": 1, "NO_BUTTON_PRESSED": 1}
    return self.packer.make_can_msg_safety("CRUISE_THROTTLE", 0, values)

  # Longitudinal mode uses SET/RES button edges, not CRUISE_STATE.
  def test_enable_control_allowed_from_cruise(self):
    pass

  def test_disable_control_allowed_from_cruise(self):
    pass

  def test_cruise_engaged_prev(self):
    pass

  def test_aol_remains_allowed_after_cruise_cancel(self):
    pass

  def test_set_and_resume_enable_on_release(self):
    for button in ("set_button", "res_button"):
      with self.subTest(button=button):
        self._reset_safety_hooks()
        self.safety.init_tests()
        self._rx(self._button_msg(main=True, **{button: True}))
        self.assertFalse(self.safety.get_controls_allowed())
        self._rx(self._button_msg(main=True))
        self.assertTrue(self.safety.get_controls_allowed())

  def test_cancel_and_main_off_disable(self):
    for msg in (self._button_msg(cancel_button=True), self._button_msg(main=False)):
      self.safety.set_controls_allowed(True)
      self._rx(msg)
      self.assertFalse(self.safety.get_controls_allowed())

  def test_accel_command_limits_and_inactive(self):
    self.safety.set_controls_allowed(False)
    self.assertTrue(self._tx(self._accel_msg(5320, active=False)))
    for raw_command in (4096, 6144, 8191, 2518):
      self.assertFalse(self._tx(self._accel_msg(raw_command)))

    self.safety.set_controls_allowed(True)
    for raw_command in (4096, 6144, 8191, 2518):
      self.assertTrue(self._tx(self._accel_msg(raw_command)))
    for raw_command in (0, 2517, 2519, 4095, 8192, 0x3FFF):
      self.assertFalse(self._tx(self._accel_msg(raw_command)))

  def test_accel_redundancy_and_constants(self):
    self.safety.set_controls_allowed(True)
    valid = self._accel_msg(6144)
    for index in range(8):
      dat = bytearray(valid.data)
      dat[index] ^= 0x1
      self.assertFalse(self._tx(common.make_msg(1, 0x2B0, 8, dat)), index)

  def test_brake_command_limits_and_format(self):
    self.safety.set_controls_allowed(False)
    self.assertTrue(self._tx(self._brake_msg(0, active=False, brake_mode=False)))
    self.assertFalse(self._tx(self._brake_msg(1)))

    self.safety.set_controls_allowed(True)
    for pressure in (1, 200, 659):
      self.assertTrue(self._tx(self._brake_msg(pressure)))
    self.assertFalse(self._tx(self._brake_msg(660)))
    self.assertFalse(self._tx(self._brake_msg(0, active=True)))
    self.assertFalse(self._tx(self._brake_msg(1, active=False)))
    self.assertFalse(self._tx(self._brake_msg(0, active=False, brake_mode=True)))

    bad_checksum = self._brake_msg(200)
    dat = bytearray(bad_checksum.data)
    dat[7] ^= 0x1
    self.assertFalse(self._tx(common.make_msg(1, 0x1C3, 8, dat)))

  def test_gas_override_blocks_longitudinal_commands(self):
    self.safety.set_controls_allowed(True)
    self._rx(self._user_gas_msg(self.GAS_PRESSED_THRESHOLD + 1))
    self.assertFalse(self._tx(self._accel_msg(6144)))
    self.assertFalse(self._tx(self._brake_msg(1)))
    self.assertTrue(self._tx(self._accel_msg(5320, active=False)))
    self.assertTrue(self._tx(self._brake_msg(0, active=False, brake_mode=False)))

  def test_tester_present(self):
    tester_present = make_tester_present_msg(0x707, 0, suppress_response=True)
    self.assertTrue(self._tx(self._make_msg(tester_present)))

    for index in range(8):
      dat = bytearray(tester_present.dat)
      dat[index] ^= 0x1
      self.assertFalse(self._tx(common.make_msg(0, 0x707, 8, dat)), index)


if __name__ == "__main__":
  unittest.main()
