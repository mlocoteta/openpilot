import types

import pytest


class MockSubMaster:
  def __init__(self):
    self.valid = {}
    self.updated = {}
    self.data = {}

  def __getitem__(self, key):
    return self.data.get(key)

  def __setitem__(self, key, value):
    self.data[key] = value

  def reset(self):
    self.valid.clear()
    self.updated.clear()
    self.data.clear()


mock_ui_state = types.SimpleNamespace(
  is_metric=False,
  sm=MockSubMaster(),
  conditional_status=0,
  starpilot_toggles={
    "conditional_experimental_mode": True,
    "conditional_curves": True,
  },
)
from openpilot.selfdrive.ui.onroad.starpilot import aethergauge
from openpilot.selfdrive.ui.onroad.starpilot.aethergauge import (
  AetherGauge,
  AetherGaugeData,
  IndicatorType,
  _cem_curvature_data,
  _is_cem_curvature,
  _is_curve_speed,
  _is_lead,
  _is_stop_light,
  _lead_data,
)
from openpilot.starpilot.common.experimental_state import CEStatus

aethergauge.ui_state = mock_ui_state


@pytest.fixture(autouse=True)
def reset_ui_state():
  mock_ui_state.sm.reset()
  mock_ui_state.conditional_status = CEStatus["OFF"]
  mock_ui_state.starpilot_toggles.update({
    "conditional_experimental_mode": True,
    "conditional_curves": True,
  })
  mock_ui_state.sm.valid["selfdriveState"] = True
  mock_ui_state.sm["selfdriveState"] = types.SimpleNamespace(enabled=True)


def _set_plan(**overrides):
  plan = types.SimpleNamespace(
    experimentalMode=True,
    roadCurvature=0.002,
    cscSpeed=0.0,
    vCruise=20.0,
    redLight=False,
    forcingStop=False,
    trackingLead=False,
  )
  for key, value in overrides.items():
    setattr(plan, key, value)
  mock_ui_state.sm.valid["starpilotPlan"] = True
  mock_ui_state.sm["starpilotPlan"] = plan
  return plan


def test_is_lead_inactive_if_not_experimental():
  _set_plan(experimentalMode=False, trackingLead=True)
  mock_ui_state.sm.valid["radarState"] = True
  mock_ui_state.sm["radarState"] = types.SimpleNamespace(
    leadOne=types.SimpleNamespace(status=True, vLead=5.0, dRel=20.0)
  )
  assert not _is_lead()


def test_is_lead_inactive_if_not_tracking_lead():
  _set_plan(trackingLead=False)
  mock_ui_state.sm.valid["radarState"] = True
  mock_ui_state.sm["radarState"] = types.SimpleNamespace(
    leadOne=types.SimpleNamespace(status=True, vLead=5.0, dRel=20.0)
  )
  assert not _is_lead()


def test_is_lead_active_when_experimental_and_tracking():
  _set_plan(trackingLead=True)
  mock_ui_state.sm.valid["radarState"] = True
  mock_ui_state.sm["radarState"] = types.SimpleNamespace(
    leadOne=types.SimpleNamespace(status=True, vLead=5.0, dRel=20.0)
  )
  assert _is_lead()


def test_lead_data_slow():
  mock_ui_state.sm.valid["radarState"] = True
  mock_ui_state.sm["radarState"] = types.SimpleNamespace(
    leadOne=types.SimpleNamespace(status=True, vLead=5.0, dRel=25.0)
  )
  data = _lead_data()
  assert data.text == "SLOW"
  assert data.indicator_extra == "slower"
  assert data.indicator_value == 25.0
  assert data.indicator_type is IndicatorType.LEAD


def test_lead_data_stopped():
  mock_ui_state.sm.valid["radarState"] = True
  mock_ui_state.sm["radarState"] = types.SimpleNamespace(
    leadOne=types.SimpleNamespace(status=True, vLead=0.5, dRel=12.0)
  )
  data = _lead_data()
  assert data.text == "STOPPED"
  assert data.indicator_extra == "stopped"
  assert data.indicator_value == 12.0
  assert data.indicator_type is IndicatorType.LEAD


def test_is_stop_light():
  _set_plan(redLight=True)
  assert _is_stop_light()

  mock_ui_state.sm["starpilotPlan"].redLight = False
  assert not _is_stop_light()


def test_is_curve_speed_follows_csc_activation_without_mode_gate(monkeypatch):
  monkeypatch.setattr(aethergauge, "_csc_state", lambda: {"active": True, "curvature": 0.002})
  assert _is_curve_speed()

  monkeypatch.setattr(aethergauge, "_csc_state", lambda: {"active": False, "curvature": 0.002})
  assert not _is_curve_speed()


def test_is_cem_curvature_requires_selected_cem_reason():
  _set_plan()
  mock_ui_state.conditional_status = CEStatus["SPEED"]
  assert not _is_cem_curvature()

  mock_ui_state.conditional_status = CEStatus["CURVATURE"]
  assert _is_cem_curvature()


def test_is_cem_curvature_uses_status_not_curvature_threshold():
  _set_plan(roadCurvature=0.00001)
  mock_ui_state.conditional_status = CEStatus["CURVATURE"]
  assert _is_cem_curvature()


def test_is_cem_curvature_requires_experimental_mode():
  _set_plan(experimentalMode=False)
  mock_ui_state.conditional_status = CEStatus["CURVATURE"]
  assert not _is_cem_curvature()


def test_is_cem_curvature_requires_cem_mode_enabled():
  _set_plan()
  mock_ui_state.conditional_status = CEStatus["CURVATURE"]
  mock_ui_state.starpilot_toggles["conditional_experimental_mode"] = False
  assert not _is_cem_curvature()


def test_is_cem_curvature_requires_curve_toggle():
  _set_plan()
  mock_ui_state.conditional_status = CEStatus["CURVATURE"]
  mock_ui_state.starpilot_toggles["conditional_curves"] = False
  assert not _is_cem_curvature()


def test_is_cem_curvature_rejects_stale_status_when_tracking_stops():
  _set_plan()
  mock_ui_state.conditional_status = CEStatus["CURVATURE"]
  mock_ui_state.sm["selfdriveState"].enabled = False
  assert not _is_cem_curvature()


def test_cem_curvature_data_preserves_curve_metrics(monkeypatch):
  _set_plan(roadCurvature=0.003, cscSpeed=8.0, vCruise=10.0)
  mock_ui_state.sm.valid["carState"] = True
  mock_ui_state.sm["carState"] = types.SimpleNamespace(vEgo=12.0)
  monkeypatch.setattr(aethergauge, "get_border_color", lambda _: aethergauge.COLOR_CEM_SPEED)

  data = _cem_curvature_data()

  assert isinstance(data, AetherGaugeData)
  assert data.indicator_type is IndicatorType.ROAD_CURVE
  assert data.indicator_value == pytest.approx(0.003)
  assert data.reduction_text


def test_widget_wires_cem_source_to_road_curve_data(monkeypatch):
  _set_plan(roadCurvature=0.003, cscSpeed=8.0, vCruise=10.0)
  mock_ui_state.sm.valid["carState"] = True
  mock_ui_state.sm["carState"] = types.SimpleNamespace(vEgo=12.0)
  mock_ui_state.conditional_status = CEStatus["CURVATURE"]
  monkeypatch.setattr(aethergauge, "_is_curve_speed", lambda: False)
  monkeypatch.setattr(aethergauge, "get_border_color", lambda _: aethergauge.COLOR_CEM_SPEED)
  monkeypatch.setattr(aethergauge.rl, "get_time", lambda: 1.0)

  gauge = AetherGauge()
  data = gauge.get_active_data()

  assert data is not None
  assert data.indicator_type is IndicatorType.ROAD_CURVE
  assert data.indicator_value == pytest.approx(0.003)


def test_csc_source_precedes_cem_source(monkeypatch):
  _set_plan(roadCurvature=0.003, cscSpeed=8.0, vCruise=10.0)
  mock_ui_state.sm.valid["carState"] = True
  mock_ui_state.sm["carState"] = types.SimpleNamespace(vEgo=12.0)
  mock_ui_state.conditional_status = CEStatus["CURVATURE"]
  monkeypatch.setattr(aethergauge, "_csc_state", lambda: {"active": True, "curvature": 0.01})
  monkeypatch.setattr(aethergauge, "get_border_color", lambda _: aethergauge.COLOR_CEM_SPEED)
  monkeypatch.setattr(aethergauge.rl, "get_time", lambda: 1.0)

  gauge = AetherGauge()
  data = gauge.get_active_data()

  assert data is not None
  assert data.indicator_type is IndicatorType.ROAD_CURVE
  assert data.indicator_value == pytest.approx(0.01)
