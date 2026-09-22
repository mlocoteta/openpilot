import json
from collections import Counter
from types import SimpleNamespace

import pyray as rl
import pytest

from openpilot.common.params import UnknownKeyName
from openpilot.selfdrive.ui.onroad.starpilot import navigation_card


class FakeParams:
  def __init__(self, values):
    self.values = values
    self.reads = Counter()

  def get(self, key):
    self.reads[key] += 1
    return self.values.get(key)

  def get_bool(self, key):
    return bool(self.get(key))

  def put_bool(self, key, value):
    self.values[key] = value

  def remove(self, key):
    self.values.pop(key, None)


@pytest.fixture
def card_state(monkeypatch):
  params = FakeParams({"NavigationUI": True, "NavDestination": {"name": "Home"}})
  nav_state = {"valid": True, "maneuverPrimaryText": "Main Street", "maneuverDistance": 1500}
  memory = FakeParams({"NavInstructionState": json.dumps(nav_state), "NavInstructionCollapsed": False})
  ui = SimpleNamespace(ui_params=params, params_memory=memory, is_metric=True)
  clock = [0.0]
  monkeypatch.setattr(navigation_card, "ui_state", ui)
  monkeypatch.setattr(navigation_card.time, "monotonic", lambda: clock[0])
  monkeypatch.setattr(navigation_card.gui_app, "font", lambda _: None)
  card = navigation_card.NavigationCardRenderer()
  return card, ui, clock


def test_navigation_state_reads_are_bounded_at_sixty_fps(card_state):
  card, ui, clock = card_state
  for frame in range(60):
    clock[0] = frame / 60
    card._update_state()
    assert card._valid

  assert 8 <= ui.params_memory.reads["NavInstructionState"] <= 10
  assert ui.params_memory.reads["NavInstructionCollapsed"] == ui.params_memory.reads["NavInstructionState"]


def test_render_does_not_repeat_state_update(card_state, monkeypatch):
  card, ui, _ = card_state
  card._update_state()
  reads = ui.ui_params.reads.copy()
  monkeypatch.setattr(card, "_render_default", lambda _: None)

  card._render(rl.Rectangle(0, 0, 100, 100))

  assert ui.ui_params.reads == reads


def test_metric_and_destination_changes_bypass_refresh_interval(card_state):
  card, ui, clock = card_state
  card._update_state()
  assert card._distance == "1.5 km"

  clock[0] = 0.01
  ui.is_metric = False
  card._update_state()
  assert card._distance == "0.9 mi"

  ui.ui_params.values["NavDestination"] = {"name": "Work"}
  ui.params_memory.values["NavInstructionState"] = {"valid": True, "maneuverPrimaryText": "Second Street"}
  card._update_state()
  assert card._primary_text == "Second Street"
  assert ui.params_memory.reads["NavInstructionState"] == 3


@pytest.mark.parametrize("key, value", [("NavigationUI", False), ("NavDestination", None)])
def test_disabled_navigation_clears_card_and_reenables_immediately(card_state, key, value):
  card, ui, clock = card_state
  card._update_state()
  card._interactive_rect = rl.Rectangle(0, 0, 100, 100)
  previous = ui.ui_params.values[key]
  ui.ui_params.values[key] = value
  clock[0] = 0.01
  card._update_state()
  assert not card._valid
  assert card._hit_rect.width == 0
  assert ui.params_memory.reads["NavInstructionState"] == 1

  ui.ui_params.values[key] = previous
  card._update_state()
  assert card._valid
  assert ui.params_memory.reads["NavInstructionState"] == 2


@pytest.mark.parametrize("state", [None, "{invalid json", {"valid": False}, {"valid": True, "maneuverPrimaryText": ""}])
def test_invalid_state_clears_card_at_next_refresh(card_state, state):
  card, ui, clock = card_state
  card._update_state()
  card._interactive_rect = rl.Rectangle(0, 0, 100, 100)
  ui.params_memory.values["NavInstructionState"] = state
  clock[0] = 0.1
  card._update_state()

  assert not card._valid
  assert card._hit_rect.width == 0


@pytest.mark.parametrize("supported", [False, True])
def test_collapse_changes_immediately_and_forces_refresh(card_state, monkeypatch, supported):
  card, ui, _ = card_state
  card._update_state()
  if not supported:
    def unsupported(*_):
      raise UnknownKeyName("NavInstructionCollapsed")
    monkeypatch.setattr(ui.params_memory, "put_bool", unsupported)

  card._toggle_collapsed()
  assert card._collapsed
  card._update_state()
  assert card._collapsed
  assert ui.params_memory.reads["NavInstructionState"] == 2

  card._toggle_collapsed()
  assert not card._collapsed


def test_cancel_navigation_clears_card_immediately(card_state):
  card, ui, _ = card_state
  card._update_state()
  card._interactive_rect = rl.Rectangle(0, 0, 100, 100)
  card._cancel_navigation()

  assert not card._valid
  assert card._hit_rect.width == 0
  assert "NavDestination" not in ui.ui_params.values
  assert "NavInstructionState" not in ui.params_memory.values
  assert "NavInstructionCollapsed" not in ui.params_memory.values
  card._update_state()
  assert not card._valid


@pytest.mark.parametrize("maneuver, modifier, expected", [
  ("turn", "left", "direction_turn_left.png"),
  ("turn", "uturn", "direction_uturn.png"),
  ("missing", "right", navigation_card.FALLBACK_ICON),
])
def test_icon_resolution_and_texture_load_are_cached(card_state, monkeypatch, maneuver, modifier, expected):
  card, _, _ = card_state
  checks = []
  loads = []
  texture = object()

  def exists(path):
    checks.append(path.name)
    return not path.name.startswith("direction_missing")

  monkeypatch.setattr(navigation_card.Path, "exists", exists)
  monkeypatch.setattr(rl, "load_image", lambda path: loads.append(path))
  monkeypatch.setattr(rl, "load_texture_from_image", lambda _: texture)
  monkeypatch.setattr(rl, "set_texture_filter", lambda *_: None)
  monkeypatch.setattr(rl, "set_texture_wrap", lambda *_: None)
  monkeypatch.setattr(rl, "unload_image", lambda _: None)

  for _ in range(60):
    assert card._get_icon(maneuver, modifier) is texture

  assert len(checks) == 1
  assert loads == [str(navigation_card.ASSETS_PATH / expected)]
