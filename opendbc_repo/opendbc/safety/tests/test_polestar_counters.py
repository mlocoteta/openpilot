"""Polestar modulo-15 receiver counters retain physical-source watchdogs."""
import unittest

from opendbc.safety.tests import test_volvo_cma as cma


class TestPolestarCounters(unittest.TestCase):
  PARAM = 5
  setUp = cma.TestVolvoCMASafety.setUp
  reset = cma.TestVolvoCMASafety.reset
  rx = cma.TestVolvoCMASafety.rx
  tx = cma.TestVolvoCMASafety.tx
  base_sources = cma.TestVolvoCMASafety.sources
  feed = cma.TestVolvoCMASafety.feed
  relay = cma.TestVolvoCMASafety.relay
  lca_command = cma.TestVolvoCMASafety.lca_command

  def sources(self, sample=0, one=None, two=None, **kwargs):
    messages = self.base_sources(sample=sample, **kwargs)
    result = []
    for address, payload, bus in messages:
      if address == 0x69:
        data = bytearray(payload)
        data[1] = (data[1] & 0xF0) | (sample * 2 % 15 if one is None else one)
        data[5] = (data[5] & 0xF0) | (sample * 4 % 15 if two is None else two)
        payload = cma.checksummed((address, data, bus))[1]
      result.append((address, payload, bus))
    return result

  def test_nominal_and_jittered_counters_wrap_without_losing_permission(self):
    self.feed()
    one = two = 0
    for sample in range(1, 46):
      self.safety.set_timer(10000 + sample * 20000)
      one = (one + (1, 2, 3)[sample % 3]) % 15
      two = (two + (3, 4, 5)[sample % 3]) % 15
      self.feed(sample=sample, one=one, two=two)
      self.assertTrue(self.tx(self.lca_command()))

  def test_each_frozen_or_jumped_clock_withdraws_permission(self):
    for clock, delta in (('one', 0), ('one', 7), ('two', 0), ('two', 8)):
      with self.subTest(clock=clock, delta=delta):
        self.reset()
        self.feed()
        rejected = False
        for sample in range(1, 12):
          self.safety.set_timer(10000 + sample * 20000)
          for message in self.sources(sample=sample, **{clock: sample * delta % 15}):
            accepted = self.rx(message)
            if message[0] == 0x69:
              rejected |= not accepted
            else:
              self.assertTrue(accepted)
          self.safety.safety_tick()
        self.assertTrue(rejected)
        self.assertFalse(self.safety.safety_config_valid())
        self.assertFalse(self.safety.get_controls_allowed())
        self.assertFalse(self.tx(self.lca_command()))

  def test_invalid_nibbles_and_checksum_fail_closed(self):
    for one, two, corrupt in ((15, 0, False), (0, 15, False), (0, 0, True)):
      with self.subTest(one=one, two=two, corrupt=corrupt):
        self.reset()
        self.feed()
        message = next(m for m in self.sources(one=one, two=two) if m[0] == 0x69)
        if corrupt:
          data = bytearray(message[1])
          data[2] ^= 1
          message = message[0], bytes(data), message[2]
        self.assertFalse(self.rx(message))
        self.safety.safety_tick()
        self.assertFalse(self.safety.safety_config_valid())
        self.assertFalse(self.safety.get_controls_allowed())
        self.assertFalse(self.tx(self.lca_command()))

  def test_healthy_steps_clear_secondary_counter_error_tolerance(self):
    self.feed()
    # A single duplicate is within the shared tolerance, then healthy frames
    # must recover it rather than accumulate isolated errors indefinitely.
    for sample in range(1, 30):
      self.safety.set_timer(10000 + sample * 20000)
      self.feed(sample=sample)
      if sample % 3 == 0:
        message = next(m for m in self.sources(sample=sample) if m[0] == 0x69)
        self.assertTrue(self.rx(message))
    self.assertTrue(self.safety.safety_config_valid())
    self.assertTrue(self.safety.get_controls_allowed())
    self.assertTrue(self.tx(self.lca_command()))
