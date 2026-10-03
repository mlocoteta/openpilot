from types import SimpleNamespace

import pytest

from openpilot.common.constants import CV
from openpilot.selfdrive.ui.onroad.starpilot.widgets import desired_speed as ds


class FakeParams:
  def __init__(self, lead_info=True):
    self.lead_info = lead_info

  def get_bool(self, key, default=False):
    return self.lead_info if key == "LeadInfo" else default


class FakeSM:
  def __init__(self, speeds, valid=True):
    self.valid = {"longitudinalPlan": valid}
    self.recv_frame = {"longitudinalPlan": 10}
    self._plan = SimpleNamespace(speeds=speeds)

  def __getitem__(self, k):
    assert k == "longitudinalPlan"
    return self._plan


@pytest.fixture
def widget(monkeypatch):
  monkeypatch.setattr(ds.gui_app, "font", lambda *a, **k: object())
  us = ds.ui_state
  monkeypatch.setattr(us, "status", ds.UIStatus.ENGAGED, raising=False)
  monkeypatch.setattr(us, "is_metric", False, raising=False)
  monkeypatch.setattr(us, "starpilot_toggles", {}, raising=False)
  monkeypatch.setattr(us, "started_frame", 0, raising=False)
  monkeypatch.setattr(us, "has_longitudinal_control", True, raising=False)
  monkeypatch.setattr(us, "ui_params", FakeParams(), raising=False)
  hud = SimpleNamespace(is_cruise_set=True, set_speed=70.0)
  return ds.DesiredSpeedWidget(hud)


def plan(end_mph, start_mph=60.0):
  return FakeSM([start_mph * CV.MPH_TO_MS] * 16 + [end_mph * CV.MPH_TO_MS])


def test_shows_planner_end_of_horizon_below_set_speed(widget, monkeypatch):
  monkeypatch.setattr(ds.ui_state, "sm", plan(52.0))
  assert widget.is_visible
  assert widget._lines == ["Desired", "52 mph"]


def test_quiet_at_set_speed(widget, monkeypatch):
  monkeypatch.setattr(ds.ui_state, "sm", plan(69.4))
  assert not widget.is_visible


def test_metric_and_si_units(widget, monkeypatch):
  monkeypatch.setattr(ds.ui_state, "sm", plan(52.0))
  monkeypatch.setattr(ds.ui_state, "is_metric", True)
  widget.hud_renderer.set_speed = 113.0
  assert widget.is_visible and widget._lines[1] == "84 km/h"
  monkeypatch.setattr(ds.ui_state, "starpilot_toggles", {"UseSiMetrics": True})
  assert widget.is_visible and widget._lines[1] == "23 m/s"


@pytest.mark.parametrize("attr,value", [
  ("status", 0),                        # disengaged: plan just tracks v_ego
  ("has_longitudinal_control", False),  # stock ACC: no planner target
  ("ui_params", FakeParams(lead_info=False)),
])
def test_hidden_without_engaged_op_long_or_lead_info(widget, monkeypatch, attr, value):
  monkeypatch.setattr(ds.ui_state, "sm", plan(40.0))
  monkeypatch.setattr(ds.ui_state, attr, value)
  assert not widget.is_visible


def test_hidden_without_plan_or_cruise(widget, monkeypatch):
  monkeypatch.setattr(ds.ui_state, "sm", FakeSM([], valid=True))
  assert not widget.is_visible
  monkeypatch.setattr(ds.ui_state, "sm", plan(40.0))
  widget.hud_renderer.is_cruise_set = False
  assert not widget.is_visible


def test_does_not_block_background_taps(widget):
  assert widget.blocks_pointer is False
