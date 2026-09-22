import math
from types import SimpleNamespace

import pyray as rl
import pytest

from openpilot.common.constants import CV
from openpilot.selfdrive.ui.lib.speed_limit_pulse import SpeedLimitPulse


@pytest.mark.parametrize("conversion", [CV.MS_TO_MPH, CV.MS_TO_KPH])
def test_pulse_tracks_visible_number_without_delaying_real_changes(conversion):
  pulse = SpeedLimitPulse()
  pulse.update("Vision", 35 / conversion, conversion, 0.0, 1)

  for frame in range(1, 100):
    limit = (35.3 if frame % 2 else 35.0) / conversion
    pulse.update("Vision", limit, conversion, frame / 20, 1)
    assert pulse.start_time == 0.0

  pulse.update("Vision", 30 / conversion, conversion, 5.0, 1)
  assert pulse.start_time == 5.0


def test_source_reacquisition_does_not_repeat_an_already_visible_limit():
  pulse = SpeedLimitPulse()
  for index, source in enumerate(["Map Data", "Vision", "Dashboard", "Vision"] * 10):
    pulse.update(source, 15.6464, CV.MS_TO_MPH, float(index), 1)
    assert pulse.start_time == -math.inf


def test_new_drive_resets_pulse_and_unit_change_does_not():
  pulse = SpeedLimitPulse()
  pulse.update("Vision", 15.6464, CV.MS_TO_MPH, 1.0, 10)
  pulse.update("Vision", 15.6464, CV.MS_TO_KPH, 2.0, 10)
  assert pulse.start_time == 1.0

  pulse.update("Vision", 15.6464, CV.MS_TO_KPH, 3.0, 20)
  assert pulse.start_time == 3.0


@pytest.mark.parametrize("missing", [0.0, float("nan"), float("inf")])
def test_missing_reading_cancels_pulse_without_forgetting_limit(missing):
  pulse = SpeedLimitPulse()
  pulse.update("Vision", 15.6464, CV.MS_TO_MPH, 0.0, 1)
  pulse.update("Vision", missing, CV.MS_TO_MPH, 0.2, 1)
  pulse.update("Vision", 15.6464, CV.MS_TO_MPH, 0.3, 1)
  assert pulse.start_time == -math.inf


class FakeParams(dict):
  def get(self, key, encoding=None):
    return super().get(key)

  def get_bool(self, key):
    return bool(self.get(key))


class FakeSubMaster(dict):
  recv_frame = {"carState": 20, "starpilotPlan": 20}
  valid = {"starpilotCarState": True}


@pytest.fixture(params=["big", "small"])
def renderer(request, monkeypatch):
  from openpilot.selfdrive.ui.mici.onroad import hud_renderer
  from openpilot.selfdrive.ui.onroad.starpilot import slc_speed_limit

  plan = SimpleNamespace(
    slcSpeedLimit=15.6464, slcSpeedLimitSource="Vision", slcOverriddenSpeed=0.0, slcSpeedLimitOffset=0.0,
    slcMapSpeedLimit=15.6464, slcMapboxSpeedLimit=0.0, slcNextSpeedLimit=0.0,
    unconfirmedSlcSpeedLimit=0.0, speedLimitChanged=False,
  )
  sm = FakeSubMaster({
    "starpilotPlan": plan,
    "starpilotCarState": SimpleNamespace(dashboardSpeedLimit=15.6464),
    "carState": SimpleNamespace(vCruiseCluster=100.0, vEgoCluster=0.0, vEgo=0.0, standstill=True),
    "controlsState": SimpleNamespace(),
    "selfdriveState": SimpleNamespace(enabled=False),
  })
  sm.recv_frame = sm.recv_frame.copy()
  params = FakeParams({"ShowSpeedLimits": True, "ShowSLCOffset": True, "VisionSpeedLimitDetection": True,
                       "SLCPriority1": "Vision", "SLCPriority2": "Map Data"})
  ui = SimpleNamespace(sm=sm, started_frame=10, is_metric=False, ui_params=params,
                       params_memory=SimpleNamespace(get_float=lambda _: plan.slcSpeedLimit))
  pulse = SpeedLimitPulse()
  clock = [0.0]
  monkeypatch.setattr(rl, "get_time", lambda: clock[0])

  if request.param == "big":
    monkeypatch.setattr(slc_speed_limit, "ui_state", ui)
    monkeypatch.setattr(slc_speed_limit, "_pulse", pulse)
    update = slc_speed_limit._get_slc_state
  else:
    monkeypatch.setattr(hud_renderer, "ui_state", ui)
    monkeypatch.setattr(hud_renderer, "rivian_lateral_mode", SimpleNamespace(update=lambda: None, wheel_tint=None))
    hud = object.__new__(hud_renderer.HudRenderer)
    hud._engaged = False
    hud.set_speed = 100.0
    hud.v_ego_cluster_seen = False
    hud._speed_limit_pulse = pulse
    update = hud._update_state

  return SimpleNamespace(update=update, pulse=pulse, clock=clock, plan=plan, sm=sm, params=params)


@pytest.mark.parametrize("gap", ["hidden", "stale", "source"])
def test_both_renderers_preserve_pulse_history_at_standstill(renderer, gap):
  renderer.update()
  assert renderer.pulse.start_time == 0.0
  renderer.clock[0] = 0.5

  if gap == "hidden":
    renderer.params["ShowSpeedLimits"] = False
  elif gap == "stale":
    renderer.sm.recv_frame["starpilotPlan"] = 9
  else:
    renderer.plan.slcSpeedLimitSource = "Map Data"
  renderer.update()

  renderer.params["ShowSpeedLimits"] = True
  renderer.sm.recv_frame["starpilotPlan"] = 20
  renderer.plan.slcSpeedLimitSource = "Vision"
  renderer.clock[0] = 0.6
  renderer.update()
  assert renderer.pulse.start_time == -math.inf

  renderer.plan.slcSpeedLimit = 30 * CV.MPH_TO_MS
  renderer.clock[0] = 0.7
  renderer.update()
  assert renderer.pulse.start_time == 0.7


def test_both_renderers_do_not_pulse_for_jitter_with_same_sign_number(renderer):
  renderer.update()
  renderer.plan.slcSpeedLimit = 35.3 * CV.MPH_TO_MS
  renderer.clock[0] = 2.0
  renderer.update()
  assert renderer.pulse.start_time == 0.0
