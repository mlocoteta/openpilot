import json
import os

import pytest

from openpilot.tools.lateral_maneuvers.characterization import settings as S
from openpilot.tools.lateral_maneuvers.characterization.plan import FRICTION_TABLES


class FileParams:
  """File-backed stand-in for openpilot Params (same on-disk layout and put() serialization)."""

  def __init__(self, root):
    self.root = root
    os.makedirs(root, exist_ok=True)
    self.fail_keys = set()

  def get_param_path(self, key=""):
    return os.path.join(self.root, key)

  def _write(self, key, text):
    if key in self.fail_keys:
      raise OSError(f"disk error writing {key}")
    with open(self.get_param_path(key), "w") as f:
      f.write(text)

  def put(self, key, value):
    self._write(key, json.dumps(value) if isinstance(value, (dict, list)) else str(value))

  def put_bool(self, key, value):
    self._write(key, "1" if value else "0")

  def remove(self, key):
    try:
      os.unlink(self.get_param_path(key))
    except FileNotFoundError:
      pass

  def raw(self, key):
    try:
      with open(self.get_param_path(key)) as f:
        return f.read()
    except FileNotFoundError:
      return None


class MemParams:
  def __init__(self):
    self.values = {}

  def put_bool(self, key, value):
    self.values[key] = value


ORIGINAL = {
  "SteerDelay": "0.01",
  "UseAutoSteerDelay": "0",
  "FLMActiveOverrides": '{"schemaVersion": 1, "vehicleKnobs": {"torque_universal.ff_gain_left": 0.1}}',
  "FLMActiveProfileId": "mat-profile",
  "FLMTrialApplied": "1",
  # TISteerKp deliberately unset: restore must remove it again
}


@pytest.fixture
def env(tmp_path):
  params = FileParams(str(tmp_path / "params"))
  for key, raw in ORIGINAL.items():
    params._write(key, raw)
  mem = MemParams()
  store = S.ParamStore(params, mem)
  snap = str(tmp_path / "snapshot.json")
  return params, mem, store, snap


def _state(params):
  return {k: params.raw(k) for k in S.BASE_KEYS}


def test_snapshot_apply_restore_round_trip(env):
  params, mem, store, snap = env
  before = _state(params)
  mgr = S.SettingsManager(store, snap)
  mgr.take_snapshot()
  assert os.path.exists(snap)

  changes = mgr.apply({"steer_delay": 0.5, "friction_table": FRICTION_TABLES["lowspeed"], "ti_steer_kp": 0.8})
  assert set(changes) == {"SteerDelay", "FLMActiveOverrides", "TISteerKp"}
  assert params.raw("SteerDelay") == "0.5"
  assert params.raw("TISteerKp") == "0.8"
  flm = json.loads(params.raw("FLMActiveOverrides"))
  assert flm["baseFrictionThresholds"]["standard"]["values"] == FRICTION_TABLES["lowspeed"]
  assert flm["vehicleKnobs"] == {"torque_universal.ff_gain_left": 0.1}  # Mat's FLM knobs kept
  assert params.raw("FLMActiveProfileId") == "mat-profile"
  assert mem.values["StarPilotTogglesUpdated"] is True

  mgr.restore()
  assert _state(params) == before
  assert params.raw("TISteerKp") is None
  assert not os.path.exists(snap)
  assert mgr.restore() == {}  # idempotent


def test_unspecified_settings_revert_to_snapshot_between_blocks(env):
  params, _, store, snap = env
  mgr = S.SettingsManager(store, snap)
  mgr.take_snapshot()
  mgr.apply({"steer_delay": "auto", "ti_steer_kp": 0.8})
  assert params.raw("UseAutoSteerDelay") == "1"
  assert params.raw("SteerDelay") == "0.01"  # auto keeps the snapshot manual value
  mgr.apply({"steer_delay": 0.5})
  assert params.raw("UseAutoSteerDelay") == "0"
  assert params.raw("TISteerKp") is None  # back to the snapshot (unset)
  mgr.restore()


def test_flm_enabled_with_fresh_profile_when_none_active(env):
  params, _, store, snap = env
  params.remove("FLMActiveProfileId")
  params.remove("FLMActiveOverrides")
  params.put_bool("FLMTrialApplied", False)
  mgr = S.SettingsManager(store, snap)
  mgr.take_snapshot()
  mgr.apply({"friction_table": FRICTION_TABLES["flat"]})
  assert params.raw("FLMTrialApplied") == "1"
  assert params.raw("FLMActiveProfileId") == S.FLM_PROFILE_ID
  mgr.restore()
  assert params.raw("FLMActiveProfileId") is None
  assert params.raw("FLMTrialApplied") == "0"


def test_crash_leaves_snapshot_that_next_start_restores(env):
  params, mem, store, snap = env
  before = _state(params)
  crashed = S.SettingsManager(store, snap)
  crashed.take_snapshot()
  crashed.apply({"steer_delay": 0.5, "ti_steer_kp": 1.2})
  # process dies here: no restore()
  assert params.raw("SteerDelay") == "0.5"

  mem.values.clear()
  restored = S.SettingsManager(store, snap).restore_stale()
  assert restored is not None
  assert _state(params) == before
  assert not os.path.exists(snap)
  assert mem.values["StarPilotTogglesUpdated"] is True
  assert S.SettingsManager(store, snap).restore_stale() is None


def test_corrupt_stale_snapshot_is_discarded_without_touching_params(env):
  params, _, store, snap = env
  before = _state(params)
  with open(snap, "w") as f:
    f.write("{truncated")
  assert S.SettingsManager(store, snap).restore_stale() is None
  assert not os.path.exists(snap)
  assert _state(params) == before


def test_restore_continues_past_a_failing_key(env):
  params, _, store, snap = env
  logs = []
  mgr = S.SettingsManager(store, snap, log=logs.append)
  mgr.take_snapshot()
  mgr.apply({"steer_delay": 0.5, "ti_steer_kp": 0.8})
  params.fail_keys.add("SteerDelay")
  mgr.restore()
  assert params.raw("TISteerKp") is None
  assert any("SteerDelay" in line for line in logs)
  assert os.path.exists(snap)  # kept so the next start retries the failed key
  params.fail_keys.clear()
  S.SettingsManager(store, snap).restore_stale()
  assert params.raw("SteerDelay") == "0.01"
  assert not os.path.exists(snap)


def test_revert_keeps_snapshot_for_resume(env):
  params, _, store, snap = env
  mgr = S.SettingsManager(store, snap)
  mgr.take_snapshot()
  mgr.apply({"ti_steer_kp": 0.8})
  assert set(mgr.revert()) == {"TISteerKp"}
  assert params.raw("TISteerKp") is None
  assert os.path.exists(snap) and mgr.active
  mgr.apply({"ti_steer_kp": 0.8})
  assert params.raw("TISteerKp") == "0.8"
  mgr.restore()
  assert params.raw("TISteerKp") is None


def test_snapshot_taken_once(env):
  params, _, store, snap = env
  mgr = S.SettingsManager(store, snap)
  first = mgr.take_snapshot()
  mgr.apply({"ti_steer_kp": 0.8})
  assert mgr.take_snapshot() == first  # a second call must not capture the modified values
  mgr.restore()


def test_advanced_lateral_tune_only_touched_when_enabled(env):
  params, _, store, snap = env
  params.put_bool("AdvancedLateralTune", False)
  mgr = S.SettingsManager(store, snap, keys=S.touched_keys(True))
  mgr.take_snapshot()
  mgr.apply({"steer_delay": 0.3}, enable_advanced_lateral_tune=True)
  assert params.raw("AdvancedLateralTune") == "1"
  mgr.restore()
  assert params.raw("AdvancedLateralTune") == "0"
  assert "AdvancedLateralTune" not in S.touched_keys(False)


def test_restore_stale_snapshot_without_file_is_noop(tmp_path):
  assert S.restore_stale_snapshot(str(tmp_path / "none.json")) is None


# --- verification -----------------------------------------------------------

def _obs(t, **kw):
  base = {"t": t, "lat_active": True, "v_ego": 5.0, "live_delay": None, "live_delay_fresh": False,
          "toggles": None, "friction_threshold": 0.0, "pid_p": 0.0, "pid_error": 0.0, "pid_fresh": False}
  base.update(kw)
  return base


def test_manual_delay_needs_two_fresh_matching_live_delay():
  v = S.SettingsVerifier({"steer_delay": 0.5}, t_apply=10.0)
  assert not v.update(_obs(9.0, live_delay=0.5, live_delay_fresh=True))  # before apply: ignored
  assert not v.update(_obs(10.1, live_delay=0.01, live_delay_fresh=True))
  assert not v.update(_obs(10.3, live_delay=0.5, live_delay_fresh=True))
  assert v.update(_obs(10.5, live_delay=0.5, live_delay_fresh=True))
  assert v.results()["steer_delay"]["observed"] == 0.5


def test_auto_delay_needs_toggles_then_live_delay():
  v = S.SettingsVerifier({"steer_delay": "auto"}, t_apply=0.0)
  assert not v.update(_obs(0.1, live_delay=0.01, live_delay_fresh=True,
                           toggles={"use_custom_steerActuatorDelay": True}))
  assert not v.update(_obs(0.5, toggles={"use_custom_steerActuatorDelay": False}))
  assert not v.update(_obs(0.7, live_delay=0.35, live_delay_fresh=True))
  assert v.update(_obs(0.9, live_delay=0.35, live_delay_fresh=True))
  assert v.results()["steer_delay"]["observed"] == 0.35


def test_friction_check_uses_controller_threshold_at_speed():
  table = FRICTION_TABLES["lowspeed"]
  toggles = {"flm_trial_applied": True, "flm_active_profile_id": "x",
             "flm_active_overrides": {"baseFrictionThresholds": {"standard": {"values": table}}}}
  v = S.SettingsVerifier({"friction_table": table}, t_apply=0.0)
  v.update(_obs(0.1, toggles=toggles))
  for i in range(9):
    assert not v.update(_obs(0.2 + i * 0.05, v_ego=5.0, friction_threshold=1.2))
  assert v.update(_obs(1.0, v_ego=5.0, friction_threshold=1.2))
  # controller still on the old flat table -> not ok
  w = S.SettingsVerifier({"friction_table": table}, t_apply=0.0)
  w.update(_obs(0.1, toggles=toggles))
  for i in range(15):
    w.update(_obs(0.2 + i * 0.05, v_ego=5.0, friction_threshold=0.30))
  assert not w.ok
  assert w.results()["friction_table"]["observed"]["medianRelErr"] > 0.5


def test_friction_check_rejects_stale_toggles():
  v = S.SettingsVerifier({"friction_table": FRICTION_TABLES["lowspeed"]}, t_apply=0.0)
  stale = {"flm_trial_applied": True, "flm_active_profile_id": "x",
           "flm_active_overrides": {"baseFrictionThresholds": {"standard": {"values": FRICTION_TABLES["flat"]}}}}
  v.update(_obs(0.1, toggles=stale))
  for i in range(20):
    v.update(_obs(0.2 + i * 0.05, friction_threshold=1.2))
  assert not v.ok
  assert "toggles" in v.results()["friction_table"]["detail"]


def test_kp_check_from_p_over_error():
  v = S.SettingsVerifier({"ti_steer_kp": 0.8}, t_apply=0.0)
  t = 0.0
  for i in range(30):  # old Kp still active during the first second
    t = 0.05 * i
    v.update(_obs(t, pid_p=0.5 * 0.1, pid_error=0.1, pid_fresh=True))
  assert not v.ok
  for i in range(25):
    t += 0.05
    err = 0.05 if i % 2 else -0.08
    v.update(_obs(t, pid_p=0.8 * err, pid_error=err, pid_fresh=True))
  assert v.ok
  assert v.results()["ti_steer_kp"]["observed"] == pytest.approx(0.8)


def test_parse_toggles_subset():
  text = json.dumps({"use_custom_steerActuatorDelay": True, "steerActuatorDelay": 0.01, "unrelated": 1})
  parsed = S.parse_toggles(text)
  assert parsed["use_custom_steerActuatorDelay"] is True
  assert "unrelated" not in parsed
  assert S.parse_toggles("not json") is None


def test_real_params_round_trip(tmp_path):
  from openpilot.common.params import Params
  params, mem = Params(), Params(memory=True)
  params.put("SteerDelay", 0.01)
  params.put_bool("UseAutoSteerDelay", False)
  params.put("FLMActiveOverrides", {"vehicleKnobs": {"k": 1.0}})
  params.remove("TISteerKp")
  params.remove("FLMActiveProfileId")
  store = S.ParamStore(params, mem)
  before = {k: store.read_raw(k) for k in S.BASE_KEYS}
  assert before["TISteerKp"] is None

  mgr = S.SettingsManager(store, str(tmp_path / "snap.json"))
  mgr.take_snapshot()
  mgr.apply({"steer_delay": 0.5, "friction_table": FRICTION_TABLES["lowspeed"], "ti_steer_kp": 0.8})
  assert params.get_float("SteerDelay") == 0.5
  assert params.get_float("TISteerKp") == 0.8
  assert params.get_bool("FLMTrialApplied")
  assert params.get("FLMActiveOverrides")["baseFrictionThresholds"]["standard"]["values"] == FRICTION_TABLES["lowspeed"]
  assert mem.get_bool("StarPilotTogglesUpdated")
  assert mgr.apply({"steer_delay": 0.5, "friction_table": FRICTION_TABLES["lowspeed"], "ti_steer_kp": 0.8}) == {}

  mgr.restore()
  after = {k: store.read_raw(k) for k in S.BASE_KEYS}
  assert all(S.same_raw(k, before[k], after[k]) for k in S.BASE_KEYS), (before, after)
  assert params.get_float("SteerDelay") == 0.01


def test_applied_friction_table_reaches_toggles_and_verifies(env):
  """End to end: tool writes FLM params -> StarPilotVariables reads the JSON-typed key (Params.get returns
  a dict) -> toggle broadcast -> parse_toggles -> FrictionTableCheck. Before the load_json_param fix the
  broadcast carried flm_active_overrides={} and this check could never pass."""
  from openpilot.starpilot.common.json_param import load_json_param
  params, _, store, snap = env
  mgr = S.SettingsManager(store, snap)
  mgr.take_snapshot()
  table = FRICTION_TABLES["lowspeed"]
  mgr.apply({"friction_table": table})

  decoded = json.loads(params.raw("FLMActiveOverrides"))  # what Params.get("FLMActiveOverrides") returns
  broadcast = json.dumps({"flm_trial_applied": params.raw("FLMTrialApplied") == "1",
                          "flm_active_profile_id": params.raw("FLMActiveProfileId"),
                          "flm_active_overrides": load_json_param(decoded, {})})
  toggles = S.parse_toggles(broadcast)
  assert toggles["flm_active_overrides"]["vehicleKnobs"] == {"torque_universal.ff_gain_left": 0.1}
  v = S.SettingsVerifier({"friction_table": table}, t_apply=0.0)
  v.update(_obs(0.1, toggles=toggles))
  for i in range(10):
    v.update(_obs(0.2 + i * 0.05, v_ego=5.0, friction_threshold=1.2))
  assert v.ok
