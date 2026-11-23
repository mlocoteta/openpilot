"""9G Accord Torque Interceptor: the saved toggle reaches CarParams only through startup prepare()."""
from pathlib import Path
import tempfile
import unittest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.torque_interceptor import TI_SAFETY_PARAM, ti_qualified
from opendbc.car.honda.values import CAR
from openpilot.common.params import Params
from openpilot.starpilot.vehicle_preferences import VehicleStartupPreferences


def honda(identity=CAR.HONDA_ACCORD_9G):
  fp = gen_empty_fingerprint()
  fp[0][0x201] = 6
  return CarInterface.get_params(identity, fp, [], False, False, False)


class TestTorqueInterceptorPreference(unittest.TestCase):
  def setUp(self):
    temporary = tempfile.TemporaryDirectory()
    self.addCleanup(temporary.cleanup)
    self.params = Params(temporary.name)

  def raw(self, key, value):
    path = Path(self.params.get_param_path(key))
    if value is None:
      path.unlink(missing_ok=True)
    else:
      path.write_bytes(value)

  def test_saved_values(self):
    # opt-in: absent = the registry default "0"; anything but "1" is off
    for raw, expected in ((None, False), (b"1", True), (b"0", False), (b"true", False), (b"1\n", False)):
      self.raw("TorqueInterceptorEnabled", raw)
      self.assertEqual(VehicleStartupPreferences.read(self.params, enabled=True).honda_torque_interceptor, expected, raw)

  def test_prepare_sets_the_safety_bit_on_the_9g_only(self):
    on, off = VehicleStartupPreferences(honda_torque_interceptor=True), VehicleStartupPreferences()
    cp = on.prepare(honda())
    self.assertTrue(ti_qualified(cp))
    self.assertEqual(cp.safetyConfigs[0].safetyParam, 36 | TI_SAFETY_PARAM)
    self.assertFalse(ti_qualified(off.prepare(honda())))
    for identity in (CAR.HONDA_CIVIC, CAR.ACURA_MDX_3G, CAR.HONDA_ACCORD):
      cp = on.prepare(honda(identity))
      self.assertFalse(cp.safetyConfigs[0].safetyParam & TI_SAFETY_PARAM, identity)

  def test_default_dataclass_is_off(self):
    # positional construction of the older fields is unchanged; TI is keyword-only in practice
    self.assertFalse(VehicleStartupPreferences().honda_torque_interceptor)


if __name__ == "__main__":
  unittest.main()
