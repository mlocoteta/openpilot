import importlib
from types import SimpleNamespace

import pytest

from openpilot.selfdrive.ui.mici.layouts.settings import settings


PANELS = {
  "toggles": ("settings", "TogglesLayoutMici"),
  "network": ("settings", "NetworkLayoutMici"),
  "bluetooth": ("bluetooth", "BluetoothLayoutMici"),
  "vehicle": ("vehicle", "VehicleLayoutMici"),
  "visuals": ("visuals", "VisualsLayoutMici"),
  "device": ("settings", "DeviceLayoutMici"),
  "software": ("software", "SoftwareLayoutMici"),
  "developer": ("settings", "DeveloperLayoutMici"),
}
EAGER_PANELS = ("toggles", "network", "developer")


@pytest.fixture
def settings_menu(monkeypatch):
  created, pushed, buttons = [], [], []

  class Button:
    def __init__(self, label="", *_args):
      self.label = label
      self.callback = None
      self.refreshes = 0

    def set_click_callback(self, callback):
      self.callback = callback

    def refresh(self):
      self.refreshes += 1

  def initialize_scroller(layout):
    layout._scroller = SimpleNamespace(add_widgets=buttons.extend)

  for name, (module_name, class_name) in PANELS.items():
    module = importlib.import_module(f"openpilot.selfdrive.ui.mici.layouts.settings.{module_name}")

    def create_panel(*args, name=name):
      panel = SimpleNamespace(name=name, args=args)
      created.append(panel)
      return panel

    monkeypatch.setattr(module, class_name, create_panel)

  monkeypatch.setattr(settings.NavScroller, "__init__", initialize_scroller)
  monkeypatch.setattr(settings.NavScroller, "show_event", lambda _layout: None)
  monkeypatch.setattr(settings, "Params", lambda: None)
  monkeypatch.setattr(settings, "SettingsBigButton", Button)
  for class_name in ("ForceDriveStateBigButton", "DrivingModelBigButton", "GalaxyBigButton", "PairBigButton"):
    monkeypatch.setattr(settings, class_name, Button)
  monkeypatch.setattr(settings.gui_app, "texture", lambda *_args: None)
  monkeypatch.setattr(settings.gui_app, "font", lambda *_args: None)
  monkeypatch.setattr(settings.gui_app, "push_widget", pushed.append)

  wifi_manager = object()
  layout = settings.SettingsLayout(wifi_manager)
  return SimpleNamespace(layout=layout, created=created, pushed=pushed, wifi_manager=wifi_manager,
                         buttons={button.label: button for button in buttons if button.label})


def test_opening_settings_preserves_runtime_initializers(settings_menu):
  settings_menu.layout.show_event()
  assert [panel.name for panel in settings_menu.created] == list(EAGER_PANELS)
  assert settings_menu.created[1].args == (settings_menu.wifi_manager,)
  assert not settings_menu.pushed
  assert settings_menu.layout._force_drive_state_btn.refreshes == 1
  assert settings_menu.layout._driving_model_btn.refreshes == 1


@pytest.mark.parametrize("name", PANELS)
def test_only_selected_subpanel_is_constructed_and_reused(settings_menu, name):
  button = settings_menu.buttons[name]
  button.callback()
  expected_names = [*EAGER_PANELS, *([] if name in EAGER_PANELS else [name])]
  assert [panel.name for panel in settings_menu.created] == expected_names
  panel = settings_menu.pushed[-1]
  assert panel.name == name
  assert panel.args == ((settings_menu.wifi_manager,) if name == "network" else ())
  assert settings_menu.pushed == [panel]

  settings_menu.layout.show_event()
  button.callback()
  assert [panel.name for panel in settings_menu.created] == expected_names
  assert settings_menu.pushed == [panel, panel]


def test_visiting_one_subpanel_does_not_construct_another(settings_menu):
  settings_menu.buttons["vehicle"].callback()
  settings_menu.buttons["visuals"].callback()
  settings_menu.buttons["vehicle"].callback()
  assert [panel.name for panel in settings_menu.created] == [*EAGER_PANELS, "vehicle", "visuals"]
  assert settings_menu.pushed[0] is settings_menu.pushed[2]


def test_failed_subpanel_construction_can_be_retried(settings_menu, monkeypatch):
  module = importlib.import_module("openpilot.selfdrive.ui.mici.layouts.settings.vehicle")
  original_constructor = module.VehicleLayoutMici

  def fail():
    raise RuntimeError("constructor failed")

  monkeypatch.setattr(module, "VehicleLayoutMici", fail)
  with pytest.raises(RuntimeError, match="constructor failed"):
    settings_menu.buttons["vehicle"].callback()
  assert not settings_menu.pushed

  monkeypatch.setattr(module, "VehicleLayoutMici", original_constructor)
  settings_menu.buttons["vehicle"].callback()
  assert [panel.name for panel in settings_menu.created] == [*EAGER_PANELS, "vehicle"]
  assert settings_menu.pushed == [settings_menu.created[-1]]
