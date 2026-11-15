"""9G Accord SSV3 initial lateral tune at runtime: CarParams, saved legacy torque keys, torqued start values."""
from pathlib import Path
import tempfile
import unittest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import SSV3_FRICTION, SSV3_LAT_ACCEL_FACTOR, SSV3_STEER_ACTUATOR_DELAY
from opendbc.car.honda.values import CAR
from openpilot.common.params import Params
from openpilot.starpilot.lateral.torque_settings import LEGACY_KEYS, LegacyMode, interpret_legacy

# Mat's saved values (device params 2026-11-15): a TI-era custom friction against the TI stock markers
SAVED = {"SteerLatAccel": b"1.1878130435943604", "SteerLatAccelStock": b"1.1878130435943604",
         "SteerFriction": b"0.19", "SteerFrictionStock": b"0.3100000023841858"}
TI_BASIS = (1.187813, 0.0, 0.31)
SSV3_BASIS = (SSV3_LAT_ACCEL_FACTOR, 0.0, SSV3_FRICTION)


def accord():
  fp = gen_empty_fingerprint()
  fp[0][0x201] = 6
  return CarInterface.get_params(CAR.HONDA_ACCORD_9G, fp, [], False, False, False)


def tune(cp):
  t = cp.lateralTuning.torque
  return float(t.latAccelFactor), float(t.friction), float(cp.steerActuatorDelay)


class TestSsv3TuneRuntime(unittest.TestCase):
  def setUp(self):
    temporary = tempfile.TemporaryDirectory()
    self.addCleanup(temporary.cleanup)
    self.params = Params(temporary.name)

  def write(self, values):
    for key, value in values.items():
      Path(self.params.get_param_path(key)).write_bytes(value)

  def test_9g_carparams_carry_the_ssv3_tune(self):
    for got, want in zip(tune(accord()), (0.90, 0.12, SSV3_STEER_ACTUATOR_DELAY), strict=True):
      self.assertAlmostEqual(got, want, places=6)

  def test_ti_era_custom_values_do_not_reach_the_ssv3_basis(self):
    raw = {k: SAVED[k] for k in LEGACY_KEYS}
    ssv3 = interpret_legacy(raw, SSV3_BASIS, fingerprint="HONDA_ACCORD_9G")
    self.assertEqual((ssv3.factor, ssv3.friction), (None, None))
    self.assertEqual((ssv3.factor_mode, ssv3.friction_mode), (LegacyMode.STOCK, LegacyMode.STOCK))
    # TI basis: exactly as before (friction 0.19 custom, factor stock)
    ti = interpret_legacy(raw, TI_BASIS, fingerprint="HONDA_ACCORD_9G")
    self.assertEqual((ti.factor, ti.friction), (None, 0.19))
    # other cars keep the old semantics even with a foreign marker
    other = interpret_legacy(raw, (2.0, 0.0, 0.25), fingerprint="HONDA_CIVIC")
    self.assertEqual(other.friction, 0.19)

  def test_ssv3_custom_values_still_apply_on_the_ssv3_basis(self):
    raw = {"SteerLatAccel": b"1.0", "SteerLatAccelStock": b"0.9", "SteerFriction": b"0.08", "SteerFrictionStock": b"0.12"}
    got = interpret_legacy(raw, SSV3_BASIS, fingerprint="HONDA_ACCORD_9G")
    self.assertEqual((got.factor, got.friction), (1.0, 0.08))

  def test_torque_runtime_and_torqued_start_from_the_ssv3_tune(self):
    from openpilot.starpilot.lateral.torque_runtime import manual_overrides_present, read_settings, TorqueHost
    from openpilot.selfdrive.locationd.torqued import TorqueEstimator
    self.write(SAVED)
    cp = accord()
    settings = read_settings(self.params, TorqueHost(self.params, cp).vehicle, CP=cp)
    self.assertTrue(settings.valid)
    self.assertIsNone(settings.user_factor)
    self.assertIsNone(settings.user_friction)
    self.assertFalse(manual_overrides_present(cp, self.params))
    est = TorqueEstimator(cp.as_reader())
    self.assertAlmostEqual(est.offline_latAccelFactor, 0.90, places=6)
    self.assertAlmostEqual(est.offline_friction, 0.12, places=6)
    self.assertAlmostEqual(est.min_lataccel_factor, 0.63, places=5)
    self.assertAlmostEqual(est.max_lataccel_factor, 1.17, places=5)


if __name__ == "__main__":
  unittest.main()
