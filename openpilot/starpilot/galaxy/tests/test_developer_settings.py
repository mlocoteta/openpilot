"""Galaxy developer preference admission, exact saves and drive-start selection."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast
import tempfile
import unittest
from unittest.mock import patch

from openpilot.starpilot.galaxy.developer_settings import CALIBRATION_RESET, DRIVER_MONITORING_RESET, STARPORT_WIFI_KEY, DeveloperSettingsOwner
from openpilot.starpilot.galaxy.settings import AuthorityContext, ContextSource, SettingsChanged, SettingsGateway
from openpilot.starpilot.longitudinal.voacc import KEY, selected
from openpilot.starpilot.ui.feature_settings_state import FeatureSettingsRequest


class FileParams:
  def __init__(self, root):
    self.root = Path(root) / "d"
    self.root.mkdir()

  def get_param_path(self, key):
    return str(self.root / key)

  def get_bool(self, key):
    try:
      return Path(self.get_param_path(key)).read_bytes() == b"1"
    except FileNotFoundError:
      return False

  def remove(self, key):
    try:
      Path(self.get_param_path(key)).unlink()
    except FileNotFoundError:
      pass

  def put_bool(self, key, value, block=False):
    Path(self.get_param_path(key)).write_bytes(b"1" if value else b"0")


class FakeStarPort:
  def __init__(self, enabled=False, running=True):
    self.enabled, self.running = enabled, running

  def call(self, command, **payload):
    if not self.running:
      raise RuntimeError("Android Auto service is not running (turn on Bluetooth)")
    if command == "set_dedicated_wifi":
      self.enabled = payload["enabled"]
      return {"ok": True}
    return {"ok": True, "status": {"dedicated_wifi_interface": self.enabled}}


class DeveloperSettingsTest(unittest.TestCase):
  def setUp(self):
    directory = tempfile.TemporaryDirectory()
    self.addCleanup(directory.cleanup)
    self.params = FileParams(directory.name)
    self.path = Path(self.params.get_param_path(KEY))
    self.cp = SimpleNamespace(openpilotLongitudinalControl=True, notCar=False, dashcamOnly=False, passive=False)
    self.parked = True
    self.owner = DeveloperSettingsOwner(self.params, lambda: self.parked)

  def test_default_off_strict_selection_and_vehicle_admission(self):
    self.assertEqual(self.owner.snapshot().rows[0].value, "Off")
    self.assertFalse(selected(self.params, self.cp))
    for raw in (b"0", b"", b"true", b"1\n", b"1" * 9):
      with self.subTest(raw=raw):
        self.path.write_bytes(raw)
        self.assertFalse(selected(self.params, self.cp))
    self.path.write_bytes(b"1")
    self.assertTrue(selected(self.params, self.cp))
    self.assertFalse(selected(self.params, None))
    self.assertFalse(selected(self.params, SimpleNamespace()))
    for field, value in (("openpilotLongitudinalControl", False), ("notCar", True),
                         ("dashcamOnly", True), ("passive", True)):
      with self.subTest(field=field):
        cp = SimpleNamespace(**{**vars(self.cp), field: value})
        self.assertFalse(selected(self.params, cp))

  def test_built_native_registry_and_actual_params_save(self):
    from openpilot.common.params import Params, ParamKeyType
    params = Params(str(self.params.root.parent / "native-params"))
    self.assertTrue(params.check_key(KEY))
    self.assertEqual(params.get_type(KEY), ParamKeyType.BOOL)
    self.assertIs(params.get_default_value(KEY), False)
    owner = DeveloperSettingsOwner(params, lambda: True)
    row = owner.snapshot().rows[0]
    self.assertEqual(row.value, "Off")
    self.assertTrue(owner.apply(FeatureSettingsRequest(KEY, row.source, "On")))
    self.assertTrue(params.get_bool(KEY))
    self.assertTrue(selected(params, self.cp))

  def test_exact_save_rejects_races_invalid_values_and_onroad(self):
    self.assertTrue(self.owner.apply(FeatureSettingsRequest(KEY, None, "On")))
    self.assertEqual(self.path.read_bytes(), b"1")
    self.assertFalse(self.owner.apply(FeatureSettingsRequest(KEY, None, "Off")))
    self.parked = False
    self.assertFalse(self.owner.snapshot().rows[0].available)
    self.assertFalse(self.owner.apply(FeatureSettingsRequest(KEY, b"1", "Off")))
    self.parked = True
    self.assertFalse(self.owner.apply(FeatureSettingsRequest(KEY, b"1", "yes")))
    self.assertFalse(self.owner.apply(FeatureSettingsRequest("AlwaysOnLateral", None, "On")))
    self.assertTrue(self.owner.apply(FeatureSettingsRequest(KEY, b"1", "Off")))
    self.assertEqual(self.path.read_bytes(), b"0")
    self.path.write_bytes(b"garbage")
    self.assertFalse(self.owner.snapshot().rows[0].available)
    self.assertFalse(self.owner.apply(FeatureSettingsRequest(KEY, b"garbage", "On")))

  def test_real_gateway_preview_save_default_and_authority_recheck(self):
    context = SimpleNamespace(value=AuthorityContext(True, None, None))
    context.sample = lambda: context.value
    gateway = SettingsGateway(self.params, cast(ContextSource, context), clock=lambda: 10.)
    token, generation = "session", b"generation"

    def preview(value):
      page = gateway.page("developer", token, generation)
      self.assertEqual(page["rows"][0]["label"], "Use VOACC")
      self.assertEqual(page["rows"][0]["defaultValue"], "Off")
      self.assertIn("next drive", page["rows"][0]["reason"])
      return gateway.preview(page["view"], 0, 0, token, generation, value=value)["intent"]

    intent = preview("On")
    self.assertTrue(gateway.confirm(intent, token, generation))
    self.assertEqual(self.path.read_bytes(), b"1")
    intent = preview("Off")
    context.value = replace(context.value, parked=False)
    with self.assertRaises(SettingsChanged):
      gateway.confirm(intent, token, generation)
    self.assertEqual(self.path.read_bytes(), b"1")
    context.value = replace(context.value, parked=True)
    page = gateway.page("developer", token, generation)
    intent = gateway.preview(page["view"], 0, 0, token, generation, reset_default=True)
    self.assertTrue(gateway.confirm(intent["intent"], token, generation))
    self.assertEqual(self.path.read_bytes(), b"0")
    intent = preview("On")
    with self.assertRaises(SettingsChanged):
      gateway.confirm(intent, token, generation, session_valid=lambda: False)

  def test_starport_stay_on_wifi_toggle(self):
    self.assertNotIn(STARPORT_WIFI_KEY, [row.key for row in self.owner.snapshot().rows])
    service = FakeStarPort()
    owner = DeveloperSettingsOwner(self.params, lambda: self.parked, starport=lambda: service)
    row = next(row for row in owner.snapshot().rows if row.key == STARPORT_WIFI_KEY)
    self.assertEqual((row.value, row.choices, row.available), ("Off", ("Off", "On"), True))
    self.assertTrue(owner.apply(FeatureSettingsRequest(STARPORT_WIFI_KEY, row.source, "On")))
    self.assertTrue(service.enabled)
    self.assertFalse(owner.apply(FeatureSettingsRequest(STARPORT_WIFI_KEY, row.source, "Off")))  # stale view
    self.assertFalse(owner.apply(FeatureSettingsRequest(STARPORT_WIFI_KEY, b"1", "maybe")))
    self.parked = False
    self.assertFalse(next(row for row in owner.snapshot().rows if row.key == STARPORT_WIFI_KEY).available)
    self.assertFalse(owner.apply(FeatureSettingsRequest(STARPORT_WIFI_KEY, b"1", "Off")))
    self.parked = True
    self.assertTrue(owner.apply(FeatureSettingsRequest(STARPORT_WIFI_KEY, b"1", "Off")))
    self.assertFalse(service.enabled)
    service.running = False
    self.assertNotIn(STARPORT_WIFI_KEY, [row.key for row in owner.snapshot().rows])
    self.assertFalse(owner.apply(FeatureSettingsRequest(STARPORT_WIFI_KEY, b"0", "On")))

  def test_driver_monitoring_reset_matches_native_semantics_and_guards_preview(self):
    self.params.put_bool("IsRhdDetected", True, block=True)
    row = next(row for row in self.owner.snapshot().rows if row.key == DRIVER_MONITORING_RESET)
    self.assertTrue(row.available)
    self.assertTrue(self.owner.apply(FeatureSettingsRequest(DRIVER_MONITORING_RESET, b"1", "confirm", confirmation=True)))
    self.assertFalse(Path(self.params.get_param_path("IsRhdDetected")).exists())
    self.assertEqual(Path(self.params.get_param_path("OnroadCycleRequested")).read_bytes(), b"1")

    self.params.put_bool("IsRhdDetected", True, block=True)
    self.params.put_bool("IsDriverViewEnabled", True, block=True)
    row = next(row for row in self.owner.snapshot().rows if row.key == DRIVER_MONITORING_RESET)
    self.assertFalse(row.available)
    self.assertFalse(self.owner.apply(FeatureSettingsRequest(DRIVER_MONITORING_RESET, b"1", "confirm", confirmation=True)))
    self.assertTrue(Path(self.params.get_param_path("IsRhdDetected")).exists())


class CalibrationResetSettingsTest(unittest.TestCase):
  setUp = DeveloperSettingsTest.setUp
  def test_calibration_reset_adjacent_and_uses_existing_reset_service(self):
    with patch("openpilot.starpilot.galaxy.developer_settings.calibration_reset") as reset:
      reset.pending = False
      rows = self.owner.snapshot().rows
      keys = [row.key for row in rows]
      self.assertEqual(keys[keys.index(DRIVER_MONITORING_RESET) + 1], CALIBRATION_RESET)
      self.assertTrue(rows[keys.index(CALIBRATION_RESET)].available)
      reset.request.return_value = True
      self.assertTrue(self.owner.apply(FeatureSettingsRequest(CALIBRATION_RESET, None, "confirm", confirmation=True)))
      reset.request.assert_called_once_with(self.params)

  def test_calibration_reset_refuses_onroad_pending_stale_and_wrong_value(self):
    with patch("openpilot.starpilot.galaxy.developer_settings.calibration_reset") as reset:
      reset.pending = False
      request = FeatureSettingsRequest(CALIBRATION_RESET, None, "confirm", confirmation=True)
      self.assertFalse(self.owner.apply(replace(request, value="On")))
      self.parked = False
      self.assertFalse(self.owner.apply(request))
      self.assertFalse(next(row for row in self.owner.snapshot().rows if row.key == CALIBRATION_RESET).available)
      self.parked = True
      reset.pending = True
      self.assertFalse(self.owner.apply(request))
      reset.pending = False
      self.params.put_bool("OnroadCycleRequested", True)
      self.assertFalse(self.owner.apply(request))
      self.params.remove("OnroadCycleRequested")
      Path(self.params.get_param_path("CalibrationParams")).write_bytes(b"changed")
      self.assertFalse(self.owner.apply(request))
      reset.request.assert_not_called()

  def test_calibration_reset_gateway_requires_confirmation_and_fresh_parked_state(self):
    with patch("openpilot.starpilot.galaxy.developer_settings.calibration_reset") as reset:
      reset.pending = False
      reset.request.return_value = True
      context = SimpleNamespace(value=AuthorityContext(True, None, None))
      context.sample = lambda: context.value
      gateway = SettingsGateway(self.params, cast(ContextSource, context), clock=lambda: 10.)
      def preview():
        page = gateway.page("developer", "session", b"generation")
        i = next(i for i,row in enumerate(page["rows"]) if row["label"] == "Reset Calibration")
        self.assertTrue(page["rows"][i]["confirm"])
        return gateway.preview(page["view"], i, 0, "session", b"generation")
      pending = preview()
      self.assertIn("recalibrate", pending["question"])
      reset.request.assert_not_called()
      context.value = replace(context.value, parked=False)
      with self.assertRaises(SettingsChanged):
        gateway.confirm(pending["intent"], "session", b"generation")
      reset.request.assert_not_called()
      context.value = replace(context.value, parked=True)
      pending = preview()
      self.assertTrue(gateway.confirm(pending["intent"], "session", b"generation"))
      reset.request.assert_called_once()
