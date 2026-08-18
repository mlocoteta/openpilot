from openpilot.selfdrive.ui.onroad.starpilot.source_bubble_layout import (
  enabled_source_titles,
  fit_source_label,
  source_abbreviated_value_text,
  source_content_metrics,
  source_value_text,
  visible_source_rows,
)


def test_source_content_metrics_scale_with_visible_row_count():
  assert source_content_metrics(3) == (30, 34, 7)
  assert source_content_metrics(4) == (30, 32, 7)
  assert source_content_metrics(5) == (28, 30, 6)


def test_fit_source_label_preserves_a_safe_value_column_gap():
  def width(text: str) -> int:
    return len(text) * 10

  assert fit_source_label("Dashboard", "Dash", 80, width) == "Dash"
  assert fit_source_label("Vision", "Vision", 70, width) == "Vision"
  assert fit_source_label("Dashboard", "Dash", 20, width) == "D…"


def test_source_value_text_keeps_missing_values_as_a_dash():
  assert source_value_text(0) == "–"
  assert source_value_text(0.1) == "–"
  assert source_value_text(55) == "55"
  assert source_value_text(float("nan")) == "–"
  assert source_value_text(float("inf")) == "–"
  assert source_abbreviated_value_text(0) == "X"
  assert source_abbreviated_value_text(55) == "55"


def test_enabled_source_titles_follow_priority_and_fallback_settings():
  assert enabled_source_titles(
    "Map Data", "Vision", vision_enabled=True, mapbox_enabled=False,
  ) == ("Map Data", "Vision", "Upcoming")
  assert enabled_source_titles(
    "Dashboard", "None", vision_enabled=False, mapbox_enabled=True,
  ) == ("Dashboard", "Mapbox")
  assert enabled_source_titles(
    "Highest", "None", vision_enabled=True, mapbox_enabled=True,
  ) == ("Dashboard", "Map Data", "Mapbox", "Upcoming")
  assert enabled_source_titles(
    "Dashboard", "Map Data", vision_enabled=False, mapbox_enabled=False,
    dashboard_available=False,
  ) == ("Map Data", "Upcoming")


def test_visible_source_rows_honor_active_only_and_source_order():
  source_defs = [
    ("Dashboard", "Dash", "dashboard", "Dashboard", "dashboard"),
    ("Map Data", "MapD", "map", "Map Data", "map"),
    ("Vision", "Vision", "vision", "Vision", "camera"),
    ("Mapbox", "MapB", "mapbox", "Mapbox", "map"),
    ("Upcoming", "Next", "next", "Next", "next"),
  ]
  values = {"dashboard": 45.0, "map": 0.0, "vision": 50.0, "mapbox": 30.0, "next": 20.0}

  assert visible_source_rows(
    source_defs, values, "Dashboard", ("Dashboard", "Map Data"), False,
  ) == [
    ("Dashboard", "dashboard", 45.0, True),
    ("Map Data", "map", 0.0, False),
  ]
  assert visible_source_rows(
    source_defs, values, "Dashboard", ("Dashboard", "Map Data"), True,
  ) == [
    ("Dashboard", "dashboard", 45.0, True),
  ]
  assert visible_source_rows(
    source_defs, values, "Map Data", ("Dashboard", "Map Data"), True,
  ) == [
    ("Dashboard", "dashboard", 45.0, False),
  ]
  assert visible_source_rows(
    source_defs, {key: 0.0 for key in values}, "Map Data", ("Map Data",), True,
  ) == []
