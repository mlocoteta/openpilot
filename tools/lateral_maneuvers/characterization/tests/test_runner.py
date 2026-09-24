import json
import os

import numpy as np
import pytest

from openpilot.tools.lateral_maneuvers.characterization import plan as P
from openpilot.tools.lateral_maneuvers.characterization import runner as R
from openpilot.tools.lateral_maneuvers.characterization import settings as S
from openpilot.tools.lateral_maneuvers.characterization.sidecar import Sidecar

ORIGINAL = {"SteerDelay": "0.01", "UseAutoSteerDelay": "0", "FLMActiveOverrides": None, "FLMActiveProfileId": None,
            "FLMTrialApplied": "0", "TISteerKp": "0.3"}
LAGD_DELAY = 0.35


class DictStore:
  def __init__(self, values):
    self.values = dict(values)
    self.refresh_requests = 0

  def read_raw(self, key):
    return self.values.get(key)

  def write_raw(self, key, raw):
    self.values[key] = raw

  def request_toggle_refresh(self):
    self.refresh_requests += 1


class SimCar:
  """Driver holds the block speed; StarPilot/lagd/controlsd react to params with realistic lags."""

  def __init__(self, store, ti_enabled=True, seed=0):
    self.store = store
    self.ti_enabled = ti_enabled
    self.frame = 0
    self.enabled = True
    self.pressed = False
    self.speed_offset = 0.0
    self.toggles = self._toggles()
    self.refresh_at = None
    self.seen_refresh = 0
    self.kp = float(store.values["TISteerKp"])
    self.rng = np.random.default_rng(seed)
    self.curvature = 0.0

  def _toggles(self):
    v = self.store.values
    flm = json.loads(v["FLMActiveOverrides"]) if v.get("FLMActiveOverrides") else {}
    return {"use_custom_steerActuatorDelay": v.get("UseAutoSteerDelay") == "0",
            "steerActuatorDelay": float(v.get("SteerDelay") or 0.01),
            "flm_trial_applied": v.get("FLMTrialApplied") == "1",
            "flm_active_profile_id": v.get("FLMActiveProfileId") or "",
            "flm_active_overrides": flm, "lane_centering": False}

  def friction_threshold(self, v_ego):
    t = self.toggles
    table = ((t["flm_active_overrides"].get("baseFrictionThresholds") or {}).get("standard") or {}).get("values")
    if t["flm_trial_applied"] and t["flm_active_profile_id"] and table:
      return float(np.interp(v_ego, P.FRICTION_SPEED_KNOTS, table))
    return 0.30

  def frame_for(self, runner, out_prev):
    self.frame += 1
    toggles = None
    if self.store.refresh_requests > self.seen_refresh and self.refresh_at is None:
      self.refresh_at = self.frame + 8  # background toggle update thread
    if self.refresh_at is not None and self.frame >= self.refresh_at:
      self.seen_refresh = self.store.refresh_requests
      self.refresh_at = None
      self.toggles = self._toggles()
      toggles = dict(self.toggles)
    elif self.frame % 20 == 0:
      toggles = dict(self.toggles)  # periodic 1 s rebroadcast
    if self.ti_enabled and self.frame % 20 == 0:  # controlsd re-reads TISteerKp every 100 frames
      self.kp = float(self.store.values.get("TISteerKp") or S.TI_KP_DEFAULT)
    live_fresh = self.frame % 5 == 0
    live = self.toggles["steerActuatorDelay"] if self.toggles["use_custom_steerActuatorDelay"] else LAGD_DELAY
    block = runner.block or runner.blocks[-1]
    v = block["speed_mps"] + self.speed_offset
    self.curvature = out_prev.desired_curvature if out_prev is not None and out_prev.plan_valid else 0.0
    err = float(self.rng.normal(0, 0.05))
    mono_ns = int(1e12 + self.frame * P.DT * 1e9)
    return R.Frame(t=mono_ns * 1e-9, mono_ns=mono_ns, v_ego=v, steering_pressed=self.pressed,
                   lat_active=self.enabled, enabled=self.enabled, curvature=self.curvature, roll=0.0,
                   live_delay=live, live_delay_fresh=live_fresh, toggles=toggles,
                   friction_threshold=self.friction_threshold(v) if self.enabled else 0.0,
                   pid_p=self.kp * err, pid_error=err, pid_fresh=True)


def small_plan(**extra):
  raw = {"version": 1, "name": "test", "blocks": [
    {"id": "b1", "speed_mph": 8, "settings": {"steer_delay": 0.5, "friction_table": "lowspeed", "ti_steer_kp": 0.8},
     "maneuvers": [{"type": "hold", "duration_s": 2.0}, {"type": "step", "amplitude": 0.6, "hold_s": 0.5}]},
    {"id": "b2", "speed_mph": 20, "settings": {"steer_delay": "auto", "friction_table": "flat", "ti_steer_kp": 0.5},
     "maneuvers": [{"type": "sine", "freq_hz": 0.8, "amplitude": 0.3, "cycles": 2}]},
  ]}
  raw.update(extra)
  return P.normalize_plan(raw)


@pytest.fixture
def rig(tmp_path):
  def make(plan=None, ti_enabled=True):
    store = DictStore(ORIGINAL)
    mgr = S.SettingsManager(store, str(tmp_path / "snap.json"))
    sidecar = Sidecar(str(tmp_path / "sidecar"))
    sidecar.set_route("00000abc--deadbeef")
    runner = R.CharacterizationRunner(plan or small_plan(), mgr, sidecar, ti_enabled=ti_enabled)
    car = SimCar(store, ti_enabled=ti_enabled)
    runner.start(int(1e12))
    return runner, car, store
  return make


def drive(runner, car, frames, hook=None):
  outs, out = [], None
  for i in range(frames):
    if hook:
      hook(i, runner, car)
    out = runner.step(car.frame_for(runner, out))
    outs.append(out)
    if runner.state == "done" and runner.restore_verifier is None:
      break
  return outs


def kinds(runner):
  return [e["type"] for e in runner.sidecar.doc["events"]]


def test_full_plan_completes_and_restores(rig, tmp_path):
  runner, car, store = rig()
  outs = drive(runner, car, 6000)
  k = kinds(runner)
  assert k[0] == "run_start"
  assert k.count("settings_verified") == 2
  assert k.count("maneuver_start") == k.count("maneuver_end") == 3
  assert "block_skipped" not in k and "maneuver_aborted" not in k
  assert k[-2:] == ["run_end", "restore_verified"]
  assert runner.sidecar.doc["events"][-1]["ok"] is True
  assert store.values == ORIGINAL
  assert not os.path.exists(str(tmp_path / "snap.json"))

  verified = [e for e in runner.sidecar.doc["events"] if e["type"] == "settings_verified"]
  assert verified[0]["observed"]["steer_delay"] == 0.5
  assert verified[0]["observed"]["ti_steer_kp"] == pytest.approx(0.8)
  assert verified[1]["observed"]["steer_delay"] == LAGD_DELAY

  # sidecar on disk is the same document, with monotonically increasing log-clock times
  with open(runner.sidecar.path) as f:
    doc = json.load(f)
  assert doc["route"] == "00000abc--deadbeef"
  monos = [e["mono_ns"] for e in doc["events"]]
  assert monos == sorted(monos)

  # every maneuver is bracketed by stock-report-compatible alerts with a stable text2
  active = [o for o in outs if o.text1.startswith("Active")]
  assert active and all(o.plan_valid for o in active)
  assert {o.text2 for o in active} == {"LC b1/1 8mph hold 2s · d0.50 flowspeed kp0.80",
                                       "LC b1/2 8mph step ±0.6 0.5s · d0.50 flowspeed kp0.80",
                                       "LC b2/1 20mph sine 0.8Hz ±0.3 · dauto fflat kp0.50"}
  assert sum(o.text1 == "Complete" for o in outs) >= 3
  settings_frames = [o for o in outs if o.text1.startswith("LC settings")]
  assert len(settings_frames) == 2 * R.SETTINGS_FRAMES
  assert json.loads(settings_frames[0].text2)["settings"]["ti_steer_kp"] == 0.8


def test_settings_applied_only_while_straight_and_hands_off(rig):
  runner, car, store = rig()

  def hook(i, runner, car):
    car.pressed = i < 100
  drive(runner, car, 150, hook)
  applied = [e for e in runner.sidecar.doc["events"] if e["type"] == "settings_applied"]
  assert applied and applied[0]["mono_ns"] > int(1e12 + 100 * P.DT * 1e9)


def test_output_clamped_at_low_speed(rig):
  runner, car, _ = rig()
  outs = drive(runner, car, 6000)
  low = [o for o in outs if o.plan_valid and "8mph" in o.text2]
  assert low and max(abs(o.accel) for o in low) <= P.LOW_SPEED_LAT_ACCEL_MAX + 1e-9
  v = runner.blocks[0]["speed_mps"]  # SimCar holds the block speed exactly
  o = next(o for o in low if abs(o.accel) > 0.5)
  assert o.desired_curvature == pytest.approx(o.accel / v ** 2, rel=1e-6, abs=1e-6)


def test_steering_touch_aborts_and_repeats(rig):
  runner, car, store = rig()
  state = {"done": False}

  def hook(i, runner, car):
    car.pressed = False
    if not state["done"] and runner.player is not None and runner.player.active and runner.player.frame > 10:
      car.pressed = True
      state["done"] = True
  drive(runner, car, 8000, hook)
  aborted = [e for e in runner.sidecar.doc["events"] if e["type"] == "maneuver_aborted"]
  assert len(aborted) == 1 and aborted[0]["reason"] == "steering touched"
  assert kinds(runner).count("maneuver_end") == 3  # the aborted run was repeated
  assert store.values == ORIGINAL


def test_repeated_aborts_skip_maneuver(rig):
  runner, car, store = rig(small_plan(max_attempts_per_maneuver=2))

  def hook(i, runner, car):
    car.speed_offset = 0.0
    if runner.player is not None and runner.player.active and runner.player.spec["type"] == "step" \
       and runner.player.frame > 5:
      car.speed_offset = 2.0  # driver cannot hold the speed during the step
  drive(runner, car, 8000, hook)
  events = runner.sidecar.doc["events"]
  skipped = [e for e in events if e["type"] == "maneuver_skipped"]
  assert len(skipped) == 1 and skipped[0]["maneuver"] == "b1m2"
  assert [e["reason"] for e in events if e["type"] == "maneuver_aborted"] == ["speed out of range"] * 2
  assert store.values == ORIGINAL


def test_disengage_restores_then_resume_reapplies(rig, tmp_path):
  runner, car, store = rig()
  seen = {}

  def hook(i, runner, car):
    if runner.player is not None and runner.player.active and runner.player.spec["type"] == "step" and "t" not in seen:
      seen["t"] = i
    if "t" in seen and seen["t"] <= i < seen["t"] + 60:
      car.enabled = False
      if i == seen["t"] + 40:
        seen["paused_values"] = dict(store.values)
        seen["snap_exists"] = os.path.exists(str(tmp_path / "snap.json"))
    else:
      car.enabled = True
  drive(runner, car, 8000, hook)
  k = kinds(runner)
  assert "paused" in k and "resumed" in k
  assert seen["paused_values"] == ORIGINAL  # driver's settings while disengaged
  assert seen["snap_exists"]  # run can resume
  assert k.count("settings_verified") == 3  # b1 re-verified after resume
  # latActive drops with the disengage, so the run aborts on the first frame; the pause follows 0.5 s later
  assert [e["reason"] for e in runner.sidecar.doc["events"] if e["type"] == "maneuver_aborted"] == ["lateral inactive"]
  assert k.index("maneuver_aborted") < k.index("paused") < k.index("resumed")
  assert k.count("maneuver_end") == 3
  assert store.values == ORIGINAL


def test_process_exit_mid_run_restores(rig, tmp_path):
  runner, car, store = rig()

  class Boom(Exception):
    pass

  def hook(i, runner, car):
    if runner.player is not None and runner.player.active:
      raise Boom()
  with pytest.raises(Boom):
    try:
      drive(runner, car, 8000, hook)
    finally:
      runner.finish("process_exit", int(2e12))
  assert store.values == ORIGINAL
  assert not os.path.exists(str(tmp_path / "snap.json"))
  k = kinds(runner)
  assert k[-2:] == ["maneuver_aborted", "run_end"]
  runner.finish("process_exit", int(2e12))  # atexit calls it again: no-op
  assert kinds(runner).count("run_end") == 1


def test_unconfirmed_settings_skip_block(rig):
  runner, car, store = rig(ti_enabled=False)  # controlsd never reads TISteerKp
  drive(runner, car, 12000)
  events = runner.sidecar.doc["events"]
  skipped = [e for e in events if e["type"] == "block_skipped"]
  assert [e["block"] for e in skipped] == ["b1", "b2"]
  assert "ti_steer_kp" in skipped[0]["reason"]
  assert kinds(runner).count("settings_retry") == 2
  assert "maneuver_start" not in kinds(runner)
  assert store.values == ORIGINAL


def test_external_setting_change_aborts_and_reverifies(rig):
  runner, car, store = rig()
  state = {"done": False}

  def hook(i, runner, car):
    if not state["done"] and runner.player is not None and runner.player.active and runner.player.frame > 5:
      store.values["TISteerKp"] = "1.5"  # someone moves the TI Kp slider mid-maneuver
      state["done"] = True
  drive(runner, car, 12000, hook)
  events = runner.sidecar.doc["events"]
  aborted = [e for e in events if e["type"] == "maneuver_aborted"]
  assert aborted and aborted[0]["reason"] == "settings drift"
  assert kinds(runner).count("settings_applied") >= 3  # re-applied after the drift
  assert kinds(runner).count("maneuver_end") == 3
  assert store.values == ORIGINAL


def test_stale_snapshot_restored_on_start(tmp_path):
  store = DictStore(ORIGINAL)
  snap = str(tmp_path / "snap.json")
  crashed = S.SettingsManager(store, snap)
  crashed.take_snapshot()
  crashed.apply({"ti_steer_kp": 1.1})
  runner = R.CharacterizationRunner(small_plan(), S.SettingsManager(store, snap), None)
  runner.start(1)
  start = runner.pop_events()[0]
  assert start["stale_restored"]["TISteerKp"] == "0.3"
  assert start["snapshot"]["TISteerKp"] == "0.3"  # new snapshot taken after the restore
  runner.finish("process_exit", 2)
  assert store.values == ORIGINAL


def test_lateral_maneuversd_plan_switch(tmp_path, monkeypatch):
  from openpilot.tools.lateral_maneuvers import lateral_maneuversd
  from openpilot.tools.lateral_maneuvers.characterization import plan as plan_mod
  monkeypatch.setattr(S, "SNAPSHOT_PATH", str(tmp_path / "snap.json"))
  path = tmp_path / "plan.json"
  monkeypatch.setattr(plan_mod, "PLAN_PATH", str(path))
  assert lateral_maneuversd._characterization_plan() is None  # absent -> stock maneuvers
  path.write_text(json.dumps(P.build_plan("quick")))
  assert lateral_maneuversd._characterization_plan()["name"] == "quick"
  path.write_text(json.dumps({"version": 1, "blocks": [{"speed_mph": 20, "settings": {"steer_friction": 0.1}}]}))
  assert isinstance(lateral_maneuversd._characterization_plan(), P.PlanError)
