from __future__ import annotations

import json
from types import SimpleNamespace

from openpilot.tools.replay import onroad_config


TEST_ROUTE = "344c5c15b34f2d8a/2024-01-03--09-37-12"


class FakeParams:
  def __init__(self, values=None):
    self.values = dict(values or {})

  def get(self, key, encoding=None, default=None):
    value = self.values.get(key, default)
    if encoding == "utf-8" and isinstance(value, bytes):
      return value.decode("utf-8")
    return value

  def cpp2python(self, key, value):
    if key == "ShowSLCOffset":
      return value == b"1"
    if key == "UnknownOldParam":
      raise onroad_config.UnknownKeyName(key)
    return value.decode("utf-8")

  def put(self, key, value):
    self.values[key] = value

  def put_bool(self, key, value):
    self.values[key] = bool(value)


def _init_data(device_type="tici", params=None):
  params = params or {}
  entries = [SimpleNamespace(key=key, value=value) for key, value in params.items()]
  return SimpleNamespace(deviceType=device_type, params=SimpleNamespace(entries=entries))


def test_parse_replay_args_handles_demo_data_dir_and_flags():
  replay_args = onroad_config.parse_replay_args([
    "--start", "30",
    "--data_dir=/tmp/routes",
    "--demo",
    "--no-loop",
  ])

  assert replay_args.route == onroad_config.DEMO_ROUTE
  assert replay_args.data_dir == "/tmp/routes"
  assert not replay_args.auto_source


def test_first_segment_identifier_limits_full_route_to_segment_zero():
  assert onroad_config.first_segment_identifier(TEST_ROUTE) == f"{TEST_ROUTE}/0/a"
  assert onroad_config.first_segment_identifier(f"{TEST_ROUTE}/5:6/r") == f"{TEST_ROUTE}/5/r"


def test_replay_log_identifiers_prefers_local_data_dir(tmp_path):
  segment_dir = tmp_path / f"{TEST_ROUTE.replace('/', '|')}--5"
  segment_dir.mkdir()
  qlog = segment_dir / "qlog.zst"
  qlog.touch()

  identifiers = onroad_config.replay_log_identifiers(
    onroad_config.ReplayArgs(route=f"{TEST_ROUTE}/5", data_dir=str(tmp_path))
  )

  assert identifiers == [str(qlog)]


def test_select_ui_uses_c4_for_mici_routes():
  assert onroad_config.select_ui_target(_init_data("mici")) == "c4"


def test_select_ui_uses_old_qt_only_when_big_route_logged_use_old_ui():
  assert onroad_config.select_ui_target(_init_data("tici", {"UseOldUI": b"1"})) == "c3"
  assert onroad_config.select_ui_target(_init_data("tici", {"TryRaylibUI": b"0"})) == "raybig"
  assert onroad_config.select_ui_target(_init_data("tizi")) == "raybig"


def test_seed_onroad_params_uses_logged_disabled_bool_and_desktop_overrides(monkeypatch):
  monkeypatch.setenv("SP_ONROAD_NAV_DEMO", "1")
  params = FakeParams()
  init_data = _init_data("tici", {
    "ShowSLCOffset": b"0",
    "LanguageSetting": b"main_en",
    "AccessToken": b"",
    "UnknownOldParam": b"1",
  })

  seeded = onroad_config.seed_onroad_params(init_data, params)

  assert seeded == 2
  assert params.values["ShowSLCOffset"] is False
  assert params.values["LanguageSetting"] == "main_en"
  assert "AccessToken" not in params.values
  assert params.values["OpenpilotEnabledToggle"] is True
  assert params.values["NavigationUI"] is True
  assert params.values["ForceOffroad"] is False
  assert "MapboxSecretKey" not in params.values
  assert "FavoriteDestinations" not in params.values


def test_seed_nav_offroad_preview_provides_quick_start_requirements(monkeypatch):
  monkeypatch.setenv("SP_ONROAD_NAV_DEMO", "1")
  monkeypatch.setenv("SP_ONROAD_OFFROAD_DEMO", "1")
  params = FakeParams()

  onroad_config.seed_onroad_params(None, params)

  assert params.values["ForceOffroad"] is True
  assert params.values["ForceOnroad"] is False
  assert params.values["MapboxSecretKey"] == onroad_config.NAV_DEMO_MAPBOX_SECRET
  assert params.values["FavoriteDestinations"] == onroad_config.NAV_DEMO_FAVORITES


def test_seed_nav_offroad_preview_preserves_existing_navigation_data(monkeypatch):
  monkeypatch.setenv("SP_ONROAD_NAV_DEMO", "1")
  monkeypatch.setenv("SP_ONROAD_OFFROAD_DEMO", "1")
  favorites = [{"name": "Existing", "latitude": 1.0, "longitude": 2.0}]
  params = FakeParams({
    "MapboxSecretKey": "existing-secret",
    "FavoriteDestinations": json.dumps(favorites),
  })

  onroad_config.seed_onroad_params(None, params)

  assert params.values["MapboxSecretKey"] == "existing-secret"
  assert json.loads(params.values["FavoriteDestinations"]) == favorites
