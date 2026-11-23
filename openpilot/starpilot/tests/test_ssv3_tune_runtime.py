"""9G Accord SSV3 initial lateral tune at runtime: prepare(), saved legacy torque keys, torqued start values."""
from pathlib import Path
import tempfile
import unittest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import SSV3_FRICTION, SSV3_LAT_ACCEL_FACTOR, SSV3_STEER_ACTUATOR_DELAY
from opendbc.car.honda.torque_interceptor import TI_STEER_ACTUATOR_DELAY, ti_qualified
from opendbc.car.honda.values import CAR
from openpilot.common.params import Params
from openpilot.starpilot.lateral.torque_settings import LEGACY_KEYS, LegacyMode, interpret_legacy
from openpilot.starpilot.vehicle_preferences import VehicleStartupPreferences

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

  def test_prepare_picks_the_tune_with_the_board(self):
    ssv3 = VehicleStartupPreferences().prepare(accord())          # TI switch off = SSV3 only
    self.assertFalse(ti_qualified(ssv3))
    for got, want in zip(tune(ssv3), (1.9, 0.15, 0.30), strict=True):
      self.assertAlmostEqual(got, want, places=6)
    ti = VehicleStartupPreferences(honda_torque_interceptor=True).prepare(accord())
    self.assertTrue(ti_qualified(ti))
    for got, want in zip(tune(ti), (1.187813, 0.31, TI_STEER_ACTUATOR_DELAY), strict=True):
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
    raw = {"SteerLatAccel": b"1.8", "SteerLatAccelStock": b"1.9", "SteerFriction": b"0.08", "SteerFrictionStock": b"0.15"}
    got = interpret_legacy(raw, SSV3_BASIS, fingerprint="HONDA_ACCORD_9G")
    self.assertEqual((got.factor, got.friction), (1.8, 0.08))

  def test_values_saved_against_the_previous_ssv3_tune_do_not_reach_the_new_basis(self):
    # 2026-11-17 retune LAF 1.6 -> 1.9: a custom factor saved against the LAF 1.6 marker is not this basis's setting
    raw = {"SteerLatAccel": b"1.8", "SteerLatAccelStock": b"1.6", "SteerFriction": b"0.15", "SteerFrictionStock": b"0.15"}
    got = interpret_legacy(raw, SSV3_BASIS, fingerprint="HONDA_ACCORD_9G")
    self.assertEqual((got.factor, got.friction), (None, None))
    self.assertEqual((got.factor_mode, got.friction_mode), (LegacyMode.STOCK, LegacyMode.STOCK))
    # a value equal to the old stock 1.6 with its own marker is stock too
    old_stock = {"SteerLatAccel": b"1.6", "SteerLatAccelStock": b"1.6"}
    self.assertIsNone(interpret_legacy(old_stock, SSV3_BASIS, fingerprint="HONDA_ACCORD_9G").factor)

  def test_torque_runtime_and_torqued_start_from_the_ssv3_tune(self):
    from openpilot.starpilot.lateral.torque_runtime import manual_overrides_present, read_settings, TorqueHost
    from openpilot.selfdrive.locationd.torqued import TorqueEstimator
    self.write(SAVED)
    cp = VehicleStartupPreferences().prepare(accord())
    settings = read_settings(self.params, TorqueHost(self.params, cp).vehicle, CP=cp)
    self.assertTrue(settings.valid)
    self.assertIsNone(settings.user_factor)
    self.assertIsNone(settings.user_friction)
    self.assertFalse(manual_overrides_present(cp, self.params))
    est = TorqueEstimator(cp.as_reader())
    self.assertAlmostEqual(est.offline_latAccelFactor, 1.9, places=6)
    self.assertAlmostEqual(est.offline_friction, 0.15, places=6)
    self.assertAlmostEqual(est.min_lataccel_factor, 1.33, places=5)
    self.assertAlmostEqual(est.max_lataccel_factor, 2.47, places=5)


if __name__ == "__main__":
  unittest.main()
