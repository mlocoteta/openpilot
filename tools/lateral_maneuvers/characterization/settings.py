"""Controller-setting overrides for characterization: snapshot, apply, verify, restore.

Only settings that apply AND restore live are handled (plan.LIVE_SETTINGS):

  steer_delay     SteerDelay + UseAutoSteerDelay -> StarPilot toggles -> lagd -> liveDelay.lateralDelay
                  -> controlsd lat_delay (+ LAT_SMOOTH_SECONDS). Needs AdvancedLateralTune=1.
  friction_table  FLMActiveOverrides.baseFrictionThresholds.standard (+ FLMTrialApplied, FLMActiveProfileId)
                  -> toggles -> set_flm_runtime_overrides() in LatControlTorque.update() every frame.
  ti_steer_kp     TISteerKp, read by controlsd._update_ti_live_params() every 100 frames (~1 s)
                  and used as the whole Kp schedule while TorqueInterceptorEnabled.

Every touched key is snapshotted to SNAPSHOT_PATH (raw file contents, or null when unset)
before the first write. restore() writes the snapshot back and deletes the file; a snapshot
file that survives a crash/power loss is restored by the next daemon or manager start.
"""
import json
import os
import statistics
import tempfile
import time

import numpy as np

from openpilot.tools.lateral_maneuvers.characterization.plan import FRICTION_SPEED_KNOTS

SNAPSHOT_PATH = "/data/lateral_characterization_snapshot.json"
SNAPSHOT_VERSION = 1
FLM_PROFILE_ID = "lateral_characterization"
TI_KP_DEFAULT = 0.3  # controlsd._read_ti_kp: get_float("TISteerKp") or 0.3

KEY_TYPES = {
  "SteerDelay": "float",
  "UseAutoSteerDelay": "bool",
  "FLMActiveOverrides": "json",
  "FLMActiveProfileId": "string",
  "FLMTrialApplied": "bool",
  "TISteerKp": "float",
  "AdvancedLateralTune": "bool",
}
BASE_KEYS = ["SteerDelay", "UseAutoSteerDelay", "FLMActiveOverrides", "FLMActiveProfileId", "FLMTrialApplied", "TISteerKp"]


def touched_keys(enable_advanced_lateral_tune=False):
  return BASE_KEYS + (["AdvancedLateralTune"] if enable_advanced_lateral_tune else [])


# ---------------------------------------------------------------------------
# param access

def _decode(raw, kind):
  if kind == "float":
    return float(raw)
  if kind == "bool":
    return raw.strip() == "1"
  if kind == "json":
    return json.loads(raw) if raw.strip() else {}
  return raw


class ParamStore:
  """Raw read / typed write access to openpilot Params (read_raw returns None when unset)."""

  def __init__(self, params, params_memory=None):
    self.params = params
    self.params_memory = params_memory

  def read_raw(self, key):
    path = self.params.get_param_path(key)
    try:
      with open(path, "rb") as f:
        return f.read().decode("utf-8")
    except FileNotFoundError:
      return None

  def write_raw(self, key, raw):
    if raw is None:
      self.params.remove(key)
      return
    kind = KEY_TYPES[key]
    try:
      value = _decode(raw, kind)
    except ValueError:
      # e.g. corrupt JSON in the original file: StarPilot already read it as {} / default
      self.params.remove(key)
      return
    if kind == "bool":
      self.params.put_bool(key, value)
    else:
      self.params.put(key, value)

  def request_toggle_refresh(self):
    if self.params_memory is not None:
      self.params_memory.put_bool("StarPilotTogglesUpdated", True)


def same_raw(key, a, b):
  """Raw values equal once decoded (Params.put(dict) re-serializes JSON with its own spacing)."""
  if a is None or b is None:
    return a is b
  try:
    return _decode(a, KEY_TYPES.get(key, "string")) == _decode(b, KEY_TYPES.get(key, "string"))
  except ValueError:
    return a == b


def _fmt_float(value):
  return str(float(value))  # what Params.put(float) stores, so read-back compares equal


def merged_flm_overrides(base_raw, values):
  """FLMActiveOverrides JSON with only baseFrictionThresholds.standard replaced (vehicle knobs kept)."""
  try:
    base = json.loads(base_raw) if base_raw else {}
  except (TypeError, ValueError):
    base = {}
  if not isinstance(base, dict):
    base = {}
  merged = dict(base)
  merged["schemaVersion"] = merged.get("schemaVersion", 1)
  thresholds = dict(merged.get("baseFrictionThresholds") or {})
  thresholds["standard"] = {"speedKnots": list(FRICTION_SPEED_KNOTS), "values": [float(v) for v in values]}
  merged["baseFrictionThresholds"] = thresholds
  merged["vehicleKnobs"] = dict(merged.get("vehicleKnobs") or {})
  return json.dumps(merged, sort_keys=True, separators=(",", ":"))


def desired_raw_state(settings, snapshot_keys, enable_advanced_lateral_tune=False):
  """Full raw state for all touched keys: snapshot values overlaid with the block settings."""
  state = dict(snapshot_keys)
  if "steer_delay" in settings:
    if settings["steer_delay"] == "auto":
      state["UseAutoSteerDelay"] = "1"
    else:
      state["UseAutoSteerDelay"] = "0"
      state["SteerDelay"] = _fmt_float(settings["steer_delay"])
    if enable_advanced_lateral_tune:
      state["AdvancedLateralTune"] = "1"
  if "friction_table" in settings:
    state["FLMActiveOverrides"] = merged_flm_overrides(snapshot_keys.get("FLMActiveOverrides"), settings["friction_table"])
    state["FLMTrialApplied"] = "1"
    state["FLMActiveProfileId"] = snapshot_keys.get("FLMActiveProfileId") or FLM_PROFILE_ID
  if "ti_steer_kp" in settings:
    state["TISteerKp"] = _fmt_float(settings["ti_steer_kp"])
  return state


def _atomic_write_json(path, payload):
  directory = os.path.dirname(path) or "."
  os.makedirs(directory, exist_ok=True)
  fd, tmp = tempfile.mkstemp(dir=directory, prefix=".lc_", suffix=".tmp")
  try:
    with os.fdopen(fd, "w") as f:
      json.dump(payload, f, indent=1, sort_keys=True)
      f.flush()
      os.fsync(f.fileno())
    os.replace(tmp, path)
  except BaseException:
    try:
      os.unlink(tmp)
    except FileNotFoundError:
      pass
    raise


class SettingsManager:
  """Owns the snapshot file. All writes go through here so restore() can undo them."""

  def __init__(self, store, snapshot_path=SNAPSHOT_PATH, keys=None, log=None):
    self.store = store
    self.snapshot_path = snapshot_path
    self.keys = list(keys or BASE_KEYS)
    self.log = log or (lambda *a, **k: None)
    self.snapshot = None  # {key: raw or None}
    self.current = {}  # last raw values written/known

  def restore_stale(self):
    """Restore a snapshot left behind by a crashed run. Returns {key: raw} restored, or None."""
    try:
      with open(self.snapshot_path) as f:
        payload = json.load(f)
    except FileNotFoundError:
      return None
    except (OSError, ValueError) as e:
      self.log(f"lateral characterization: unreadable stale snapshot {self.snapshot_path}: {e}")
      self._remove_snapshot_file()
      return None
    keys = payload.get("keys") if isinstance(payload, dict) else None
    if not isinstance(keys, dict):
      self._remove_snapshot_file()
      return None
    restored = {}
    for key, raw in keys.items():
      if key not in KEY_TYPES:
        continue
      if not same_raw(key, self.store.read_raw(key), raw):
        self.store.write_raw(key, raw)
      restored[key] = raw
    self.store.request_toggle_refresh()
    self._remove_snapshot_file()
    self.log(f"lateral characterization: restored stale snapshot from {payload.get('createdWall', '?')}: {restored}")
    return restored

  def take_snapshot(self, extra=None):
    if self.snapshot is not None:
      return self.snapshot
    keys = {key: self.store.read_raw(key) for key in self.keys}
    payload = {"version": SNAPSHOT_VERSION, "createdWall": time.time(), "createdMono": time.monotonic(),  # noqa: TID251 (human-readable wall time)
               "pid": os.getpid(), "keys": keys}
    if extra:
      payload.update(extra)
    _atomic_write_json(self.snapshot_path, payload)
    self.snapshot = keys
    self.current = dict(keys)
    return keys

  def apply(self, settings, enable_advanced_lateral_tune=False):
    """Write the block settings. Returns {key: (old_raw, new_raw)} for keys that changed."""
    if self.snapshot is None:
      raise RuntimeError("take_snapshot() before apply()")
    desired = desired_raw_state(settings, self.snapshot, enable_advanced_lateral_tune)
    changes = {}
    for key in self.keys:
      new = desired.get(key)
      old = self.store.read_raw(key)
      if not same_raw(key, old, new):
        self.store.write_raw(key, new)
        changes[key] = (old, new)
      self.current[key] = new
    self.store.request_toggle_refresh()
    return changes

  def revert(self):
    """Write the snapshot values back but keep the snapshot (run paused, e.g. on disengage)."""
    if self.snapshot is None:
      return {}
    changes, _ = self._write_snapshot_values()
    self.store.request_toggle_refresh()
    return changes

  def restore(self):
    """Write the snapshot back and delete the snapshot file. Idempotent; never raises on one bad key.

    If any key fails to restore, the snapshot file is kept so the next daemon/manager start retries.
    """
    if self.snapshot is None:
      return {}
    failed = list(self.snapshot)
    try:
      changes, failed = self._write_snapshot_values()
      self.store.request_toggle_refresh()
    finally:
      if failed:
        self.log(f"lateral characterization: kept {self.snapshot_path} for retry, failed keys: {failed}")
      else:
        self._remove_snapshot_file()
      self.snapshot = None
    return changes

  def _write_snapshot_values(self):
    changes, failed = {}, []
    for key, raw in self.snapshot.items():
      try:
        old = self.store.read_raw(key)
        if not same_raw(key, old, raw):
          self.store.write_raw(key, raw)
          changes[key] = (old, raw)
        self.current[key] = raw
      except Exception as e:  # keep restoring the other keys
        failed.append(key)
        self.log(f"lateral characterization: failed to restore {key}: {e}")
    return changes, failed

  @property
  def active(self):
    return self.snapshot is not None

  def _remove_snapshot_file(self):
    try:
      os.unlink(self.snapshot_path)
    except FileNotFoundError:
      pass


def restore_stale_snapshot(snapshot_path=SNAPSHOT_PATH, log=None):
  """Backstop for manager start: restore params if a characterization run died without cleanup."""
  if not os.path.exists(snapshot_path):
    return None
  from openpilot.common.params import Params
  store = ParamStore(Params(), Params(memory=True))
  return SettingsManager(store, snapshot_path, log=log).restore_stale()


# ---------------------------------------------------------------------------
# verification: did the controller actually pick the settings up?

def parse_toggles(text):
  """Subset of the StarPilot toggle broadcast that the verification needs."""
  try:
    toggles = json.loads(text)
  except (TypeError, ValueError):
    return None
  if not isinstance(toggles, dict):
    return None
  keys = ("use_custom_steerActuatorDelay", "steerActuatorDelay", "use_auto_steer_delay",
          "flm_trial_applied", "flm_active_profile_id", "flm_active_overrides", "lane_centering", "nnff", "nnff_lite")
  return {k: toggles.get(k) for k in keys}


def _toggle_friction_values(toggles):
  overrides = (toggles or {}).get("flm_active_overrides") or {}
  if not isinstance(overrides, dict):
    return None
  payload = (overrides.get("baseFrictionThresholds") or {}).get("standard") or {}
  values = payload.get("values", payload if isinstance(payload, list) else None)
  return list(values) if isinstance(values, list) else None


class _Check:
  name = ""

  def __init__(self, expected, t_apply):
    self.expected = expected
    self.t_apply = t_apply
    self.ok = False
    self.observed = None
    self.detail = "waiting"

  def result(self):
    return {"ok": self.ok, "expected": self.expected, "observed": self.observed, "detail": self.detail}


class SteerDelayCheck(_Check):
  """Manual: liveDelay.lateralDelay == value on 2 fresh messages. Auto: toggles report auto, then 2 fresh liveDelay."""
  name = "steer_delay"

  def __init__(self, expected, t_apply):
    super().__init__(expected, t_apply)
    self.fresh = []
    self.toggles_ok_t = None

  def update(self, obs):
    toggles = obs.get("toggles")
    if self.expected == "auto":
      if toggles and toggles.get("use_custom_steerActuatorDelay") is False and self.toggles_ok_t is None:
        self.toggles_ok_t = obs["t"]
      if toggles and toggles.get("use_custom_steerActuatorDelay") is True:
        self.toggles_ok_t = None
        self.fresh = []
      if obs.get("live_delay_fresh") and self.toggles_ok_t is not None and obs["t"] > self.toggles_ok_t:
        self.fresh.append(obs["live_delay"])
      self.fresh = self.fresh[-4:]
      self.ok = len(self.fresh) >= 2
      self.observed = self.fresh[-1] if self.fresh else obs.get("live_delay")
      self.detail = "lagd auto delay in use" if self.ok else "waiting for toggles use_custom_steerActuatorDelay=False"
      return
    if obs.get("live_delay_fresh") and obs["t"] > self.t_apply:
      self.fresh.append(obs["live_delay"])
      self.fresh = self.fresh[-4:]
    last = self.fresh[-2:]
    self.observed = last[-1] if last else obs.get("live_delay")
    self.ok = len(last) == 2 and all(abs(v - self.expected) < 2e-3 for v in last)
    self.detail = "liveDelay.lateralDelay matches" if self.ok else "waiting for liveDelay.lateralDelay"


class FrictionTableCheck(_Check):
  """Toggles carry the table AND the controller's published frictionThreshold matches it at the current speed."""
  name = "friction_table"
  WINDOW = 20
  MIN_SAMPLES = 10
  REL_TOL = 0.20  # universal-FLM threshold scale is bounded to [0.82, 1.18] by vehicle knobs

  def __init__(self, expected, t_apply):
    super().__init__(expected, t_apply)
    self.toggles_ok = False
    self.samples = []

  def update(self, obs):
    toggles = obs.get("toggles")
    if toggles is not None:
      values = _toggle_friction_values(toggles)
      self.toggles_ok = bool(toggles.get("flm_trial_applied")) and bool(toggles.get("flm_active_profile_id")) and \
        values is not None and len(values) == len(self.expected) and np.allclose(values, self.expected, atol=1e-4)
      if not self.toggles_ok:
        self.samples = []
    if self.toggles_ok and obs.get("lat_active") and obs.get("friction_threshold"):
      expected_now = float(np.interp(obs["v_ego"], FRICTION_SPEED_KNOTS, self.expected))
      self.samples.append((obs["friction_threshold"], expected_now))
      self.samples = self.samples[-self.WINDOW:]
    if self.samples:
      rel = [abs(o - e) / max(e, 1e-3) for o, e in self.samples]
      self.observed = {"frictionThreshold": round(self.samples[-1][0], 4), "expectedAtSpeed": round(self.samples[-1][1], 4),
                       "medianRelErr": round(statistics.median(rel), 4)}
      self.ok = len(self.samples) >= self.MIN_SAMPLES and statistics.median(rel) <= self.REL_TOL
    else:
      self.ok = False
    self.detail = ("frictionThreshold matches table" if self.ok else
                   "waiting for toggles" if not self.toggles_ok else "waiting for lat-active frictionThreshold samples")


class TiKpCheck(_Check):
  """torqueState.p / torqueState.error == Kp (PIDController: p = k_p * error, schedule [[0],[TISteerKp]])."""
  name = "ti_steer_kp"
  WINDOW = 40
  MIN_SAMPLES = 20
  REL_TOL = 0.03
  SETTLE_S = 1.2  # controlsd re-reads TISteerKp every 100 frames

  def __init__(self, expected, t_apply):
    super().__init__(expected, t_apply)
    self.ratios = []

  def update(self, obs):
    if obs["t"] < self.t_apply + self.SETTLE_S or not obs.get("lat_active") or not obs.get("pid_fresh"):
      return
    error = obs.get("pid_error") or 0.0
    if abs(error) > 1e-3:
      self.ratios.append(obs["pid_p"] / error)
      self.ratios = self.ratios[-self.WINDOW:]
    if self.ratios:
      kp = statistics.median(self.ratios)
      self.observed = round(kp, 4)
      self.ok = len(self.ratios) >= self.MIN_SAMPLES and abs(kp - self.expected) <= self.REL_TOL * self.expected
    self.detail = "torqueState p/error matches" if self.ok else "waiting for p/error samples"


CHECKS = {"steer_delay": SteerDelayCheck, "friction_table": FrictionTableCheck, "ti_steer_kp": TiKpCheck}


class SettingsVerifier:
  """Feeds per-frame observations to one check per specified setting."""

  def __init__(self, settings, t_apply):
    self.checks = [CHECKS[k](settings[k], t_apply) for k in CHECKS if k in settings]

  def update(self, obs):
    for check in self.checks:
      check.update(obs)
    return self.ok

  @property
  def ok(self):
    return all(c.ok for c in self.checks)

  def pending(self):
    return [c.name for c in self.checks if not c.ok]

  def results(self):
    return {c.name: c.result() for c in self.checks}
