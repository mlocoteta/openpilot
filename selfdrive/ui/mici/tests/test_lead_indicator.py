from types import SimpleNamespace

import pytest

import openpilot.selfdrive.ui.mici.onroad.model_renderer as model_renderer


class _FakeParams:
  def __init__(self, enabled: bool, lead_info: bool = False, lead_info_mode: int = model_renderer.LeadInfoMode.SPEED):
    self.enabled = enabled
    self.lead_info = lead_info
    self.lead_info_mode = lead_info_mode

  def get(self, key):
    assert key == "HideLeadMarker"
    return b"0" if self.enabled else b"1"

  def get_bool(self, key):
    if key == "HideLeadMarker":
      return not self.enabled
    if key == "LeadInfo":
      return self.lead_info
    raise AssertionError(key)

  def get_int(self, key, **_kwargs):
    assert key == "LeadInfoMode"
    return self.lead_info_mode


def test_lead_indicator_renders_in_aol_without_longitudinal_control(monkeypatch):
  monkeypatch.setattr(model_renderer, "ui_state", SimpleNamespace(always_on_lateral_active=True))
  renderer = object.__new__(model_renderer.ModelRenderer)
  renderer._params = _FakeParams(enabled=True)
  renderer._longitudinal_control = False

  assert renderer._should_render_lead_indicator(SimpleNamespace())


def test_lead_indicator_still_honors_disabled_setting():
  renderer = object.__new__(model_renderer.ModelRenderer)
  renderer._params = _FakeParams(enabled=False)

  assert not renderer._should_render_lead_indicator(SimpleNamespace())
  assert not renderer._should_render_lead_indicator(None)


@pytest.mark.parametrize(
  ("is_metric", "use_si_metrics", "expected"),
  [
    (False, False, "22 mph"),
    (True, False, "36 km/h"),
    (False, True, "10 m/s"),
  ],
)
def test_lead_speed_uses_selected_units(is_metric, use_si_metrics, expected):
  assert model_renderer.ModelRenderer._format_lead_speed(10.0, is_metric, use_si_metrics) == expected


@pytest.mark.parametrize(
  ("is_metric", "use_si_metrics", "expected"),
  [
    (False, False, "33 ft"),
    (True, False, "10 m"),
    (False, True, "10 m"),
  ],
)
def test_lead_distance_uses_selected_units(is_metric, use_si_metrics, expected):
  assert model_renderer.ModelRenderer._format_lead_distance(10.0, is_metric, use_si_metrics) == expected


@pytest.mark.parametrize(
  ("lead_info", "configured_mode", "expected"),
  [
    (False, model_renderer.LeadInfoMode.SPEED, model_renderer.LeadInfoMode.OFF),
    (True, model_renderer.LeadInfoMode.DISTANCE, model_renderer.LeadInfoMode.DISTANCE),
    (True, model_renderer.LeadInfoMode.SPEED, model_renderer.LeadInfoMode.SPEED),
    (True, model_renderer.LeadInfoMode.OFF, model_renderer.LeadInfoMode.SPEED),
    (True, 99, model_renderer.LeadInfoMode.SPEED),
  ],
)
def test_lead_info_mode_preserves_legacy_speed_behavior(lead_info, configured_mode, expected):
  params = _FakeParams(enabled=True, lead_info=lead_info, lead_info_mode=configured_mode)
  assert model_renderer.lead_info_mode(params) == expected


@pytest.mark.parametrize(
  ("mode", "expected"),
  [
    (model_renderer.LeadInfoMode.DISTANCE, "82 ft"),
    (model_renderer.LeadInfoMode.SPEED, "27 mph"),
  ],
)
def test_lead_info_formats_selected_metric(mode, expected):
  renderer = object.__new__(model_renderer.ModelRenderer)
  renderer._lead_info_mode = mode
  lead = SimpleNamespace(dRel=25.0, vLead=12.0)

  assert renderer._format_lead_info(lead, is_metric=False, use_si_metrics=False) == expected


def test_lead_metrics_draw_selected_value_when_enabled(monkeypatch):
  drawn_metrics = []
  monkeypatch.setattr(model_renderer, "get_theme_color", lambda *_args: model_renderer.rl.RED)
  monkeypatch.setattr(model_renderer.rl, "draw_triangle_fan", lambda *_args: None)

  renderer = object.__new__(model_renderer.ModelRenderer)
  renderer._lead_info_mode = model_renderer.LeadInfoMode.DISTANCE
  renderer._lead_vehicles = [
    model_renderer.LeadVehicle(
      glow=[(1.0, 2.0)] * 3,
      chevron=[(1.0, 2.0)] * 3,
      fill_alpha=255,
    ),
    model_renderer.LeadVehicle(),
  ]
  renderer._draw_lead_info = drawn_metrics.append
  lead_one = SimpleNamespace(status=True, dRel=25.0, vLead=10.0)

  renderer._draw_lead_indicator(SimpleNamespace(leadOne=lead_one, leadTwo=SimpleNamespace(status=False)))

  assert drawn_metrics == [lead_one]
