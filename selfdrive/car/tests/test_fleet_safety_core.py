import json
import unittest  # noqa: TID251 - Deliberately stdlib-only offline tests.
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

from selfdrive.car.tests.fleet_safety_core import EffectiveSafetyConfig, TxAudit, effective_safety_configs  # noqa: TID251


def params(configs=(), alternative=0):
  return SimpleNamespace(safetyConfigs=list(configs), alternativeExperience=alternative)


def config(model, param):
  return SimpleNamespace(safetyModel=model, safetyParam=param)


class FakeSafety:
  def __init__(self, controls=False, aol=False, longitudinal=False, accepted=True, hook=None):
    self.controls, self.aol, self.longitudinal = controls, aol, longitudinal
    self.accepted, self.hook = accepted, hook
    self.packets = []

  def get_controls_allowed(self):
    return self.controls

  def get_aol_allowed(self):
    return self.aol

  def get_longitudinal_allowed(self):
    return self.longitudinal

  def safety_tx_hook(self, packet):
    self.packets.append(packet)
    if self.hook:
      self.hook(self)
    return self.accepted


def audit(safety=None, panda_index=0):
  return TxAudit(safety or FakeSafety(), lambda addr, bus, data: SimpleNamespace(addr=addr, bus=bus, data=data),
                 config=EffectiveSafetyConfig(panda_index, 2, 0, 0))


def check(tx, **kwargs):
  values = dict(addr=0x123, bus=0, data=b"\x01\x02", timestamp_ns=123456, scenario="recorded engagement",
                requested_lat_active=True, requested_long_active=False)
  values.update(kwargs)
  return tx.check(**values)


class TestEffectiveSafetyConfigs(unittest.TestCase):
  def test_panda_models_params_and_alternative_bits(self):
    cp = params([config(SimpleNamespace(raw=5), 0x01), config(17, 0x08)], 0x01)
    fpcp = params([config(99, 0x10), config(98, 0x20), config(97, 0x40)], 0x04)
    result = effective_safety_configs(cp, fpcp, panda_count=4)
    self.assertEqual(result, (EffectiveSafetyConfig(0, 5, 0x11, 5), EffectiveSafetyConfig(1, 17, 0x28, 5),
                              EffectiveSafetyConfig(2, 0, 0x40, 5), EffectiveSafetyConfig(3, 0, 0, 5)))
    with self.assertRaises(FrozenInstanceError):
      result[0].safety_model = 99

  def test_signed_capnp_alt_matches_uint16_assignment(self):
    self.assertEqual(effective_safety_configs(params(alternative=-32768), params(alternative=1))[0].alternative_experience, 32769)

  def test_default_count_and_actual_count(self):
    self.assertEqual(len(effective_safety_configs(params(), params())), 1)
    self.assertEqual(len(effective_safety_configs(params([config(5, 0)]), params([config(0, 0)] * 3))), 3)
    self.assertEqual(effective_safety_configs(params(), params(), panda_count=0), ())
    self.assertEqual(len(effective_safety_configs(params([config(5, 0)] * 2), params(), panda_count=1)), 1)

  def test_global_bus_never_aliases_another_panda(self):
    second = EffectiveSafetyConfig(1, 5, 0, 0)
    self.assertEqual(second.local_bus(4), 0)
    self.assertEqual(second.local_bus(7), 3)
    for bus in (0, 3, 8, 128, -1, 256, True):
      with self.subTest(bus=bus), self.assertRaises(ValueError):
        second.local_bus(bus)

  def test_invalid_config_not_silently_truncated(self):
    for cp, fp, kwargs in ((params([config(1, 65536)]), params(), {}),
                           (params(), params([config(1, -1)]), {}),
                           (params(alternative=65535), params(), {}),
                           (params(), params(), {"panda_count": -1})):
      with self.subTest(case=repr((cp, fp, kwargs))), self.assertRaises(ValueError):
        effective_safety_configs(cp, fp, **kwargs)


class TestTxAudit(unittest.TestCase):
  def test_aol_rejection_fails_without_controls(self):
    tx = audit(FakeSafety(aol=True, accepted=False))
    record = check(tx)
    self.assertFalse(record.permissions.controls_allowed)
    self.assertTrue(record.permissions.aol_allowed)
    self.assertEqual(tx.summary()["status"], "failed")
    self.assertEqual(tx.summary()["unexpected_rejections"], 1)
    self.assertEqual(tx.summary()["requested_aol_only_tx"], 1)

  def test_permissions_are_captured_before_mutating_hook(self):
    def clear(safety):
      safety.controls = safety.aol = safety.longitudinal = False
    safety = FakeSafety(controls=True, aol=True, longitudinal=True, accepted=False, hook=clear)
    tx = audit(safety)
    record = check(tx)
    self.assertEqual((record.permissions.controls_allowed, record.permissions.aol_allowed, record.permissions.longitudinal_allowed),
                     (True, True, True))
    self.assertFalse(safety.controls)
    self.assertEqual(tx.summary()["active_tx"], 1)
    self.assertEqual(tx.summary()["status"], "failed")

  def test_inactive_rejection_also_fails(self):
    tx = audit(FakeSafety(accepted=False))
    check(tx, requested_lat_active=False)
    self.assertEqual(tx.summary()["status"], "failed")
    self.assertEqual(tx.summary()["inactive_tx"], 1)

  def test_expected_blocks_are_per_packet_and_keep_reason(self):
    safety = FakeSafety(aol=True, accepted=False)
    tx = audit(safety)
    first = check(tx, expected_block_reason="negative case: excessive torque")
    self.assertEqual(first.expected_block_reason, "negative case: excessive torque")
    self.assertIsNone(first.failure)
    self.assertEqual(tx.summary()["expected_blocks"], 1)
    self.assertEqual(tx.summary()["status"], "uncovered")
    check(tx)  # Previous expectation must not leak onto another packet.
    self.assertEqual(tx.summary()["unexpected_rejections"], 1)
    self.assertEqual(tx.summary()["status"], "failed")

  def test_expected_block_acceptance_fails(self):
    tx = audit(FakeSafety(controls=True))
    check(tx, expected_block_reason="negative case: wrong command bit")
    self.assertEqual(tx.summary()["status"], "failed")
    self.assertEqual(tx.summary()["unexpected_acceptances"], 1)

  def test_failure_summary_is_bounded_without_hiding_verdict(self):
    tx = audit(FakeSafety(aol=True, accepted=False))
    for _ in range(3):
      check(tx)
    summary = tx.summary(failure_limit=1)
    self.assertEqual(summary["failure_count"], 3)
    self.assertEqual(summary["failures_truncated"], 2)
    self.assertEqual(len(summary["failures"]), 1)
    self.assertEqual(len(tx.records), 3)
    self.assertEqual(tx.summary(failure_limit=0)["status"], "failed")

  def test_missing_coverage_is_not_a_pass(self):
    tx = audit(FakeSafety())
    self.assertEqual(tx.summary()["status"], "uncovered")
    self.assertIn("no emitted TX", tx.summary()["uncovered_reasons"])
    check(tx)
    self.assertEqual(tx.summary()["status"], "uncovered")
    tx = audit(FakeSafety(controls=True))
    check(tx, requested_lat_active=None, requested_long_active=None)
    self.assertEqual(tx.summary()["status"], "uncovered")
    self.assertEqual(tx.summary()["requested_unknown_tx"], 1)
    check(tx, requested_lat_active=False)
    self.assertEqual(tx.summary()["status"], "uncovered")
    check(tx)
    self.assertEqual(tx.summary()["status"], "pass")

  def test_states_requests_and_transitions_are_independent(self):
    safety = FakeSafety()
    tx = audit(safety)
    check(tx, requested_lat_active=False)
    safety.aol = True
    check(tx)
    check(tx)
    safety.controls = safety.longitudinal = True
    check(tx, requested_long_active=True)
    safety.aol = safety.controls = safety.longitudinal = False
    check(tx, requested_lat_active=False)
    summary = tx.summary()
    self.assertEqual(summary["tx_total"], 5)
    self.assertEqual(summary["active_tx"], 3)
    self.assertEqual(summary["inactive_tx"], 2)
    self.assertEqual(summary["requested_active_tx"], 3)
    self.assertEqual(summary["requested_inactive_tx"], 2)
    self.assertEqual(summary["requested_aol_only_tx"], 2)
    self.assertEqual(summary["permission_transitions"], {"inactive -> aol": 1, "aol -> controls+aol+long": 1,
                                                         "controls+aol+long -> inactive": 1})
    self.assertEqual(sum(summary["requested_transitions"].values()), 3)
    json.dumps(summary)  # Reports can be serialized without compiled dependencies.

  def test_every_packet_keeps_immutable_original_metadata(self):
    safety = FakeSafety(longitudinal=True)
    tx = audit(safety, panda_index=1)
    data = bytearray(b"\x00\xfe")
    record = check(tx, bus=6, data=data, requested_lat_active=False, requested_long_active=True)
    data[0] = 5
    self.assertEqual((record.addr, record.bus, record.local_bus, record.data, record.timestamp_ns, record.scenario),
                     (0x123, 6, 2, b"\x00\xfe", 123456, "recorded engagement"))
    self.assertEqual(safety.packets[0].bus, 2)
    self.assertIsInstance(tx.records, tuple)
    with self.assertRaises(FrozenInstanceError):
      record.accepted = False
    self.assertEqual(tx.summary()["status"], "pass")

  def test_invalid_per_packet_inputs_rejected(self):
    for kwargs in ({"expected_block_reason": " "}, {"expected_block_reason": True}, {"requested_lat_active": 1},
                   {"scenario": ""}, {"timestamp_ns": -1}, {"data": 8}, {"addr": -1}, {"bus": 4}):
      tx = audit()
      with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
        check(tx, **kwargs)
      self.assertEqual(tx.records, ())

  def test_hook_exception_is_recorded_and_reraised(self):
    def broken(_safety):
      raise RuntimeError("hook crashed")
    tx = audit(FakeSafety(aol=True, hook=broken))
    with self.assertRaisesRegex(RuntimeError, "hook crashed"):
      check(tx)
    self.assertEqual(tx.summary()["status"], "failed")
    self.assertEqual(tx.summary()["hook_errors"], 1)
    self.assertEqual(tx.records[0].data, b"\x01\x02")
    self.assertTrue(tx.records[0].permissions.aol_allowed)


if __name__ == "__main__":
  unittest.main()
