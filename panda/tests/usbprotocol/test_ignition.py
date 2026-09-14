#!/usr/bin/env python3
import unittest

from panda.tests.libpanda import libpanda_py


lpp = libpanda_py.libpanda


def volkswagen_meb_ignition_msg(counter, ignition, bus=0, length=4):
  dat = bytearray(length)
  if length >= 2:
    dat[1] = counter & 0xF
  if length >= 3:
    dat[2] = int(ignition) << 1
  return libpanda_py.make_CANPacket(0x3C0, bus, dat)


class TestIgnitionCanHook(unittest.TestCase):
  def test_volkswagen_meb_ignition(self):
    lpp.set_ignition_can_for_test(False)
    lpp.set_ignition_can_cnt_for_test(123)

    # A single frame is insufficient: the rolling counter must first be established.
    lpp.ignition_can_hook(volkswagen_meb_ignition_msg(7, True))
    self.assertFalse(lpp.get_ignition_can_for_test())
    self.assertEqual(lpp.get_ignition_can_cnt_for_test(), 123)

    lpp.ignition_can_hook(volkswagen_meb_ignition_msg(8, True))
    self.assertTrue(lpp.get_ignition_can_for_test())
    self.assertEqual(lpp.get_ignition_can_cnt_for_test(), 0)

    # A duplicate counter must not change ignition state.
    lpp.set_ignition_can_cnt_for_test(123)
    lpp.ignition_can_hook(volkswagen_meb_ignition_msg(8, False))
    self.assertTrue(lpp.get_ignition_can_for_test())
    self.assertEqual(lpp.get_ignition_can_cnt_for_test(), 123)

    lpp.ignition_can_hook(volkswagen_meb_ignition_msg(9, False))
    self.assertFalse(lpp.get_ignition_can_for_test())
    self.assertEqual(lpp.get_ignition_can_cnt_for_test(), 0)


if __name__ == "__main__":
  unittest.main()
