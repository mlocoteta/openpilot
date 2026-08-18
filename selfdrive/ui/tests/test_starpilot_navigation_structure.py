from types import SimpleNamespace

from openpilot.selfdrive.ui.layouts.settings.starpilot.main_panel import StarPilotLayout
from openpilot.selfdrive.ui.layouts.settings.starpilot.navigation import StarPilotNavigationLayout
from openpilot.selfdrive.ui.layouts.settings.starpilot.panel import StarPilotPanelType
from openpilot.selfdrive.ui.layouts.settings.starpilot.aethergrid import BreadcrumbController, gui_app


def test_root_hub_contains_the_six_categories_in_order():
  assert [item["title"] for item in StarPilotLayout.CATEGORIES] == [
    "Sounds & Alerts",
    "Driving Model",
    "Driving Controls",
    "System",
    "Appearance",
    "Vehicle Settings",
  ]
  assert len(StarPilotLayout.CATEGORIES) == 6
  assert all(item["title"] != "Navigation & Maps" for item in StarPilotLayout.CATEGORIES)


def test_driving_controls_contains_nested_navigation_folder_and_leaf_routes():
  controls = next(item for item in StarPilotLayout.CATEGORIES if item["title"] == "Driving Controls")

  assert "panel" not in controls
  assert [item["title"] for item in controls["children"]] == [
    "Navigation & Maps",
    "Gas / Brake",
    "Steering",
  ]

  navigation_maps = controls["children"][0]
  assert "panel" not in navigation_maps
  assert navigation_maps["children"] == [
    {"title": "Map Data", "panel": "MAPS", "icon": "navigate"},
    {"title": "Navigation", "panel": "NAVIGATION", "icon": "road"},
  ]

  assert controls["children"][1]["panel"] == "LONGITUDINAL"
  assert controls["children"][2]["panel"] == "LATERAL"


def test_driving_model_is_a_root_leaf_and_existing_panel_routes_are_preserved():
  driving_model = next(item for item in StarPilotLayout.CATEGORIES if item["title"] == "Driving Model")

  assert driving_model["panel"] == "DRIVING_MODEL"
  assert driving_model["icon"] == "aicar"
  assert "children" not in driving_model
  assert StarPilotLayout.PANEL_TYPE_MAP["DRIVING_MODEL"] == StarPilotPanelType.DRIVING_MODEL
  assert StarPilotLayout.PANEL_TYPE_MAP["MAPS"] == StarPilotPanelType.MAPS
  assert StarPilotLayout.PANEL_TYPE_MAP["NAVIGATION"] == StarPilotPanelType.NAVIGATION
  assert StarPilotPanelType.NAVIGATION.value == 13


class _FakeHubTile:
  def __init__(self, title, desc, icon_key, on_click, bg_color=None):
    self.title = title
    self.desc = desc
    self.icon_key = icon_key
    self.on_click = on_click
    self.bg_color = bg_color


class _FakeGrid:
  def __init__(self):
    self.tiles = []

  def clear(self):
    self.tiles.clear()

  def add_tile(self, tile):
    self.tiles.append(tile)


class _PanelSpy:
  def __init__(self, name):
    self.name = name
    self.show_count = 0
    self.hide_count = 0
    self.current_sub_panel = ""

  def show_event(self):
    self.show_count += 1

  def hide_event(self):
    self.hide_count += 1

  def set_current_sub_panel(self, sub_panel):
    self.current_sub_panel = sub_panel


def _make_layout(monkeypatch):
  import openpilot.selfdrive.ui.layouts.settings.starpilot.main_panel as main_panel

  monkeypatch.setattr(main_panel, "HubTile", _FakeHubTile)

  layout = object.__new__(StarPilotLayout)
  layout._current_panel = StarPilotPanelType.MAIN
  layout._hub_path = []
  layout._selected_leaf = None
  layout._current_category_idx = None
  layout._panel_stack = []
  layout._depth_callback = None
  layout._main_grid = _FakeGrid()
  layout._panels = {}
  for panel_type in StarPilotPanelType:
    layout._panels[panel_type] = SimpleNamespace(
      name=panel_type.name,
      instance=None if panel_type == StarPilotPanelType.MAIN else _PanelSpy(panel_type.name),
    )

  depths = []
  layout.set_depth_callback(depths.append)
  StarPilotLayout.active_instance = layout
  layout._rebuild_grid()
  return layout, depths


def _click_title(layout, title):
  tile = next(tile for tile in layout._main_grid.tiles if tile.title == title)
  tile.on_click()


def test_nested_hub_navigation_back_and_depth_values(monkeypatch):
  layout, depths = _make_layout(monkeypatch)
  assert len(layout._main_grid.tiles) == 6
  assert depths == []

  _click_title(layout, "Driving Controls")
  assert [folder["title"] for folder in layout._hub_path] == ["Driving Controls"]
  assert layout._current_panel == StarPilotPanelType.MAIN
  layout._update_depth()
  assert depths[-1] == 1

  _click_title(layout, "Navigation & Maps")
  assert [folder["title"] for folder in layout._hub_path] == ["Driving Controls", "Navigation & Maps"]
  layout._update_depth()
  assert depths[-1] == 2

  _click_title(layout, "Map Data")
  assert layout._current_panel == StarPilotPanelType.MAPS
  assert layout._selected_leaf["title"] == "Map Data"
  assert depths[-1] == 3
  maps_panel = layout._panels[StarPilotPanelType.MAPS].instance
  assert (maps_panel.show_count, maps_panel.hide_count) == (1, 0)

  layout.navigate_back()
  assert layout._current_panel == StarPilotPanelType.MAIN
  assert [folder["title"] for folder in layout._hub_path] == ["Driving Controls", "Navigation & Maps"]
  assert depths[-1] == 2
  assert (maps_panel.show_count, maps_panel.hide_count) == (1, 1)

  layout.navigate_back()
  assert [folder["title"] for folder in layout._hub_path] == ["Driving Controls"]
  assert depths[-1] == 1

  layout.navigate_back()
  assert layout._hub_path == []
  assert depths[-1] == 0


def test_root_driving_model_opens_directly_and_sub_panel_depth_is_additive(monkeypatch):
  layout, depths = _make_layout(monkeypatch)

  _click_title(layout, "Driving Model")
  assert layout._hub_path == []
  assert layout._current_panel == StarPilotPanelType.DRIVING_MODEL
  assert depths[-1] == 1

  layout._panel_stack.append((StarPilotPanelType.DRIVING_MODEL, "details"))
  layout._commit_navigation()
  assert depths[-1] == 2

  layout.navigate_back()
  assert layout._current_panel == StarPilotPanelType.DRIVING_MODEL
  assert layout._panel_stack == []
  assert depths[-1] == 1

  layout.navigate_back()
  assert layout._current_panel == StarPilotPanelType.MAIN
  assert depths[-1] == 0


def test_breadcrumb_paths_and_folder_jump_back(monkeypatch):
  layout, _ = _make_layout(monkeypatch)
  monkeypatch.setattr(gui_app, "_nav_stack", [layout], raising=False)

  assert BreadcrumbController.build_path() == [("StarPilot", "action:home")]

  _click_title(layout, "Driving Controls")
  assert BreadcrumbController.build_path() == [
    ("StarPilot", "action:home"),
    ("Driving Controls", "action:hub:1"),
  ]

  _click_title(layout, "Navigation & Maps")
  assert BreadcrumbController.build_path() == [
    ("StarPilot", "action:home"),
    ("Driving Controls", "action:hub:1"),
    ("Navigation & Maps", "action:hub:2"),
  ]

  _click_title(layout, "Map Data")
  assert BreadcrumbController.build_path()[-1] == ("Map Data", "action:panel")

  nav_stack = [layout, object()]
  monkeypatch.setattr(gui_app, "_nav_stack", nav_stack, raising=False)
  monkeypatch.setattr(gui_app, "pop_widget", lambda: nav_stack.pop(), raising=False)
  BreadcrumbController().handle_click("action:hub:1")

  assert nav_stack == [layout]
  assert layout._current_panel == StarPilotPanelType.MAIN
  assert [folder["title"] for folder in layout._hub_path] == ["Driving Controls"]
  assert BreadcrumbController.build_path()[-1] == ("Driving Controls", "action:hub:1")


def test_home_breadcrumb_clears_hub_path_panel_stack_and_active_panel(monkeypatch):
  layout, _ = _make_layout(monkeypatch)
  _click_title(layout, "Driving Controls")
  _click_title(layout, "Navigation & Maps")
  _click_title(layout, "Map Data")
  layout._panel_stack.append((StarPilotPanelType.MAPS, "details"))

  nav_stack = [layout, object(), object()]
  monkeypatch.setattr(gui_app, "_nav_stack", nav_stack, raising=False)
  monkeypatch.setattr(gui_app, "pop_widget", lambda: nav_stack.pop(), raising=False)
  BreadcrumbController().handle_click("action:home")

  maps_panel = layout._panels[StarPilotPanelType.MAPS].instance
  assert nav_stack == [layout]
  assert layout._hub_path == []
  assert layout._selected_leaf is None
  assert layout._panel_stack == []
  assert layout._current_panel == StarPilotPanelType.MAIN
  assert maps_panel.hide_count == 1
  assert BreadcrumbController.build_path() == [("StarPilot", "action:home")]


def test_navigation_start_is_the_summary_action_not_a_duplicate_rail_target():
  layout = object.__new__(StarPilotNavigationLayout)
  layout._draft_destination = {
    "name": "Home",
    "place_name": "Home",
    "latitude": 1.0,
    "longitude": 2.0,
  }
  layout._selected_favorite = None
  layout._favorites = []

  action_ids = [action[0] for action in layout._action_definitions()]

  assert action_ids == ["action:favorite", "action:home", "action:work"]


def test_rejected_search_invalidates_an_in_flight_request_generation():
  layout = object.__new__(StarPilotNavigationLayout)
  layout._search_generation = 3
  layout._query = "previous"
  layout._search_results = []
  layout._search_error = ""
  layout._draft_destination = None
  layout._selected_favorite = None

  layout._start_search("ab")

  assert layout._search_generation == 4
  assert layout._search_error
