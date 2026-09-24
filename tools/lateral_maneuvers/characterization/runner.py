"""Plan-driven characterization loop used by lateral_maneuversd when a plan file exists.

CharacterizationRunner is a pure per-frame state machine (Frame in, Output out) so it can be
unit tested without messaging. main() wires it to SubMaster/PubMaster/Params.

Per block:  apply_wait (straight, not touched, lateral engaged for 1 s) -> write settings
            -> verify (controller picked them up) -> maneuvers -> next block.
Per maneuver: stock readiness (speed, latActive, straight, flat for 2 s) -> active ->
            1 s "Complete" holdoff. Steering touch, lateral inactive, speed out of range or
            a settings drift aborts the run and it is repeated (max_attempts_per_maneuver).
Disengage (selfdriveState.enabled false for 0.5 s): the snapshot values are written back
            (run paused); on re-engage the block's settings are re-applied and re-verified.
Completion / process exit: snapshot restored and snapshot file deleted.
"""
import json
from dataclasses import dataclass, field

import numpy as np

from openpilot.tools.lateral_maneuvers.characterization.plan import (
  DT, LAT_ACCEL_ABS_MAX, MPH_TO_MS, lat_accel_limit, maneuver_meta, maneuver_profile,
)
from openpilot.tools.lateral_maneuvers.characterization.settings import SettingsVerifier, TI_KP_DEFAULT

# stock lateral_maneuversd readiness thresholds (kept identical; see lateral_maneuversd.py)
MAX_CURV = 0.002
MAX_ROLL = 0.08
TIMER = 2.0

APPLY_STABLE_S = 1.0  # straight + engaged + hands off before settings are written
VERIFY_TIMEOUT_S = 20.0  # lat-active seconds allowed for the controller to show the new settings
MAX_APPLY_ATTEMPTS = 2
DISENGAGE_RESTORE_S = 0.5
DRIFT_ABORT_S = 1.0
COMPLETE_HOLDOFF_S = 1.0
RESTORE_CHECK_S = 15.0
SETTINGS_FRAMES = 3  # alertDebug frames carrying the block JSON (rlog-recoverable settings)
MIN_SPEED = 1.0  # drive_helpers.MIN_SPEED


@dataclass
class Frame:
  t: float  # s, log clock
  mono_ns: int
  v_ego: float = 0.0
  steering_pressed: bool = False
  lat_active: bool = False
  enabled: bool = False
  curvature: float = 0.0  # controlsState.desiredCurvature
  roll: float = 0.0
  pitch: float = 0.0
  live_delay: float | None = None
  live_delay_fresh: bool = False
  toggles: dict | None = None  # set only on frames where a new toggle broadcast was parsed
  friction_threshold: float = 0.0
  pid_p: float = 0.0
  pid_error: float = 0.0
  pid_fresh: bool = False

  def obs(self):
    return {"t": self.t, "lat_active": self.lat_active, "v_ego": self.v_ego, "live_delay": self.live_delay,
            "live_delay_fresh": self.live_delay_fresh, "toggles": self.toggles,
            "friction_threshold": self.friction_threshold, "pid_p": self.pid_p, "pid_error": self.pid_error,
            "pid_fresh": self.pid_fresh}


@dataclass
class Output:
  accel: float = 0.0
  plan_valid: bool = False
  desired_curvature: float = 0.0
  text1: str = ""
  text2: str = ""
  state: str = ""
  phase: str = ""
  events: list = field(default_factory=list)


class ManeuverPlayer:
  def __init__(self, spec, speed_mps, speed_tol):
    self.spec = spec
    self.t, self.accel = maneuver_profile(spec)
    self.meta = maneuver_meta(spec)
    self.target = speed_mps
    self.tol = speed_tol
    self.ready_cnt = 0
    self.active = False
    self.finished = False
    self.frame = 0
    self.baseline_curvature = 0.0
    self.just_started = False

  def conditions(self, f):
    return {"speed": abs(f.v_ego - self.target) < self.tol, "lateral": f.lat_active,
            "straight": abs(f.curvature) < MAX_CURV, "flat": abs(f.roll) < MAX_ROLL}

  def update(self, f):
    self.just_started = False
    ready = all(self.conditions(f).values()) and not f.steering_pressed
    self.ready_cnt = self.ready_cnt + 1 if ready else max(self.ready_cnt - 1, 0)
    if not self.active and not self.finished and self.ready_cnt > TIMER / DT:
      self.active = True
      self.just_started = True
      self.frame = 0
      self.baseline_curvature = f.curvature
    if not self.active:
      return 0.0
    accel = float(self.accel[self.frame])
    self.frame += 1
    if self.frame >= len(self.accel):
      self.active = False
      self.finished = True
    return accel

  def abort(self):
    self.active = False
    self.frame = 0
    self.ready_cnt = 0

  @property
  def remaining_s(self):
    return max(len(self.accel) - self.frame, 0) * DT


def _compact(obj):
  return json.dumps(obj, separators=(",", ":"), sort_keys=True)


def settings_from_snapshot(snapshot, initial_toggles):
  """What the controller should show after restore (only settings we can check)."""
  expected = {}
  if initial_toggles and initial_toggles.get("use_custom_steerActuatorDelay") is not None:
    if initial_toggles["use_custom_steerActuatorDelay"]:
      expected["steer_delay"] = float(initial_toggles.get("steerActuatorDelay") or 0.01)
    else:
      expected["steer_delay"] = "auto"
  raw_kp = (snapshot or {}).get("TISteerKp")
  try:
    kp = float(raw_kp) if raw_kp is not None else 0.0
  except ValueError:
    kp = 0.0
  expected["ti_steer_kp"] = kp if kp > 0 else TI_KP_DEFAULT
  return expected


class CharacterizationRunner:
  def __init__(self, plan, settings_mgr, sidecar=None, log=None, ti_enabled=True):
    self.plan = plan
    self.mgr = settings_mgr
    self.sidecar = sidecar
    self.log = log or (lambda *a, **k: None)
    self.ti_enabled = ti_enabled
    self.blocks = plan["blocks"]
    self.block_idx = 0
    self.man_idx = 0
    self.state = "init"
    self.player = None
    self.verifier = None
    self.restore_verifier = None
    self.restore_check_s = 0.0
    self.stable_s = 0.0
    self.verify_active_s = 0.0
    self.apply_attempts = 0
    self.attempts = 0
    self.disengaged_s = 0.0
    self.drift_s = 0.0
    self.holdoff_s = 0.0
    self.settings_frames = 0
    self.settings_label = ""
    self.settings_payload = ""
    self._holdoff_text2 = ""
    self.initial_toggles = None
    self.finish_reason = None
    self._started_block = None
    self.history = []
    self._pending_events = []

  # -- helpers ---------------------------------------------------------------
  @property
  def block(self):
    return self.blocks[self.block_idx] if self.block_idx < len(self.blocks) else None

  def _event(self, kind, mono_ns, **fields):
    block = self.block
    if block is not None and "block" not in fields:
      fields["block"] = block["id"]
    entry = {"type": kind, "mono_ns": int(mono_ns), **fields}
    if self.sidecar is not None:
      entry = self.sidecar.event(kind, mono_ns, **fields)
    self._pending_events.append(entry)
    self.log(f"lateral characterization: {kind} {_compact(fields)}")
    line = self._history_line(kind, fields)
    if line:
      self.history.append(line)
      self.history = self.history[-120:]
    return entry

  @staticmethod
  def _history_line(kind, f):
    labels = {
      "run_start": "Characterization started", "settings_verified": "Settings verified",
      "block_skipped": "Block skipped", "maneuver_start": "Started", "maneuver_end": "Completed",
      "maneuver_aborted": "Aborted", "maneuver_skipped": "Skipped", "paused": "Paused (settings restored)",
      "resumed": "Resumed", "run_end": "Characterization ended",
    }
    if kind not in labels:
      return ""
    detail = f.get("maneuver_desc") or f.get("tag") or f.get("reason") or ""
    who = f.get("maneuver") or f.get("block") or ""
    return f"{labels[kind]} {who} {detail}".strip()

  def _maneuver(self):
    block = self.block
    return block["maneuvers"][self.man_idx] if block is not None and self.man_idx < len(block["maneuvers"]) else None

  def _new_player(self):
    spec = self._maneuver()
    self.player = ManeuverPlayer(spec, self.block["speed_mps"], self.plan["speed_tolerance_mps"]) if spec else None

  def _text2(self):
    block, spec = self.block, self._maneuver()
    if block is None:
      return ""
    where = f"Block {self.block_idx + 1}/{len(self.blocks)}"
    if spec is None or self.state in ("apply_wait", "verify"):
      return f"{where}, settings, set {block['speed_mph']:g} mph · {block['tag']}"
    n = len(block['maneuvers'])
    return f"{where} m{self.man_idx + 1}/{n}, {spec['desc']}, set {block['speed_mph']:g} mph · {block['tag']}"

  @staticmethod
  def _road(f):
    return {"roll": round(f.roll, 5), "pitch": round(f.pitch, 5), "v_ego": round(f.v_ego, 3)}

  # -- lifecycle -------------------------------------------------------------
  def start(self, mono_ns, extra=None):
    restored = self.mgr.restore_stale()
    snapshot = self.mgr.take_snapshot()
    self.state = "apply_wait"
    self._new_player()
    self._event("run_start", mono_ns, plan_name=self.plan["name"], blocks=len(self.blocks), snapshot=snapshot,
                stale_restored=restored, estimated_minutes=self.plan["estimated_minutes"], **(extra or {}))
    self.settings_label = "LC plan"
    self.settings_payload = _compact({"plan": self.plan["name"], "snapshot": snapshot})
    self.settings_frames = SETTINGS_FRAMES

  def finish(self, reason, mono_ns):
    """Final restore. Safe to call more than once and from exit handlers."""
    if self.finish_reason is not None:
      return
    self.finish_reason = reason
    if self.player is not None and self.player.active:
      self._event("maneuver_aborted", mono_ns, maneuver=self.player.spec["id"], reason=reason)
    try:
      changes = self.mgr.restore()
      self._event("run_end", mono_ns, reason=reason, restored={k: v[1] for k, v in changes.items()})
    finally:
      self.state = "done"
      self.player = None
      expected = settings_from_snapshot(self.mgr.current, self.initial_toggles)
      if not self.ti_enabled:  # controlsd only reads TISteerKp with the TI enabled
        expected.pop("ti_steer_kp", None)
      self.restore_verifier = SettingsVerifier(expected, t_apply=mono_ns * 1e-9)
      self.restore_check_s = 0.0

  def pop_events(self):
    events, self._pending_events = self._pending_events, []
    return events

  # -- per frame ---------------------------------------------------------------
  def step(self, f):
    out = Output()
    if f.toggles is not None and self.initial_toggles is None and self.state in ("init", "apply_wait") \
       and self.block_idx == 0 and self.apply_attempts == 0:
      self.initial_toggles = f.toggles
      self._event("baseline_toggles", f.mono_ns, toggles=f.toggles)

    if self.state == "done":
      self._step_done(f, out)
      out.events = self.pop_events()
      return out

    self.disengaged_s = 0.0 if f.enabled else self.disengaged_s + DT
    if self.state != "paused" and self.disengaged_s >= DISENGAGE_RESTORE_S:
      self._pause(f)
    if self.state == "paused":
      if f.enabled:
        self.state = "apply_wait"
        self.stable_s = 0.0
        self.apply_attempts = 0
        self._event("resumed", f.mono_ns)
      else:
        out.text1, out.state, out.phase = "Paused: engage to continue", "paused", "disengaged"

    if self.state == "apply_wait":
      self._step_apply(f, out)
    if self.state == "verify":
      self._step_verify(f, out)
    if self.state == "maneuver":
      self._step_maneuver(f, out)

    if self.state == "done":
      self._step_done(f, out)
    if not out.text2:
      out.text2 = self._text2()
    if self.settings_frames > 0 and not out.plan_valid:
      self.settings_frames -= 1
      out.text1 = self.settings_label
      out.text2 = self.settings_payload
    out.events = self.pop_events()
    return out

  def _pause(self, f):
    if self.player is not None and self.player.active:
      self.player.abort()
      self._event("maneuver_aborted", f.mono_ns, maneuver=self.player.spec["id"], reason="disengaged",
                  attempt=self.attempts, **self._road(f))
    changes = self.mgr.revert()
    self.verifier = None
    self.state = "paused"
    self._event("paused", f.mono_ns, reason="disengaged", restored={k: v[1] for k, v in changes.items()})

  def _step_apply(self, f, out):
    block = self.block
    stable = f.lat_active and not f.steering_pressed and abs(f.curvature) < MAX_CURV and abs(f.roll) < MAX_ROLL
    self.stable_s = self.stable_s + DT if stable else 0.0
    out.state, out.phase = "setup", "apply_settings"
    out.text1 = "Hold straight: applying settings" if f.lat_active else "Engage lateral to apply settings"
    if self.stable_s < APPLY_STABLE_S:
      return
    if self._started_block != self.block_idx:
      self._started_block = self.block_idx
      self._event("block_start", f.mono_ns, index=self.block_idx + 1, of=len(self.blocks), speed_mph=block["speed_mph"],
                  variant=block["variant"], tag=block["tag"], settings=block["settings"], **self._road(f))
    changes = self.mgr.apply(block["settings"], self.plan["enable_advanced_lateral_tune"])
    self.apply_attempts += 1
    self.verifier = SettingsVerifier(block["settings"], t_apply=f.t)
    self.verify_active_s = 0.0
    self.state = "verify"
    self._event("settings_applied", f.mono_ns, settings=block["settings"], tag=block["tag"],
                speed_mph=block["speed_mph"], attempt=self.apply_attempts,
                changes={k: v[1] for k, v in changes.items()}, **self._road(f))

  def _step_verify(self, f, out):
    block = self.block
    self.verifier.update(f.obs())
    if f.lat_active:
      self.verify_active_s += DT
    out.state, out.phase = "setup", "verify_settings"
    out.text1 = "Verifying: " + ", ".join(self.verifier.pending())
    if self.verifier.ok:
      results = self.verifier.results()
      self._event("settings_verified", f.mono_ns, settings=block["settings"], tag=block["tag"],
                  speed_mph=block["speed_mph"], observed={k: r["observed"] for k, r in results.items()})
      self.settings_payload = _compact({
        "block": block["id"], "speed_mph": block["speed_mph"], "variant": block["variant"], "settings": block["settings"],
        "observed": {k: r["observed"] for k, r in results.items()},
        "maneuvers": [{k: m[k] for k in ("id", "type", "amplitude", "hold_s", "freq_hz", "cycles", "duration_s") if k in m}
                      for m in block["maneuvers"]],
      })
      self.settings_label = f"LC settings {block['id']}"
      self.settings_frames = SETTINGS_FRAMES
      self.drift_s = 0.0
      self.state = "maneuver"
      if self.player is None or self.player.finished:
        self._new_player()
      return
    if self.verify_active_s < VERIFY_TIMEOUT_S:
      return
    results = self.verifier.results()
    if self.apply_attempts < MAX_APPLY_ATTEMPTS:
      self._event("settings_retry", f.mono_ns, pending=self.verifier.pending(), results=results)
      self.state = "apply_wait"
      self.stable_s = 0.0
      return
    self._event("block_skipped", f.mono_ns, reason="settings not confirmed by the controller: " +
                ", ".join(self.verifier.pending()), results=results)
    self._next_block(f)

  def _abort_reason(self, f):
    if f.steering_pressed:
      return "steering touched"
    if not f.lat_active:
      return "lateral inactive"
    if abs(f.v_ego - self.player.target) > self.player.tol:
      return "speed out of range"
    if self.drift_s >= DRIFT_ABORT_S:
      return "settings drift"
    return None

  def _step_maneuver(self, f, out):
    block, player = self.block, self.player
    self.verifier.update(f.obs())
    self.drift_s = self.drift_s + DT if not self.verifier.ok else 0.0

    if self.holdoff_s > 0.0:
      self.holdoff_s -= DT
      out.text1, out.state, out.phase = "Complete", "completed", "holdoff"
      out.text2 = self._holdoff_text2
      if self.holdoff_s <= 1e-9:
        self._next_maneuver(f)
      return

    if player.active:
      reason = self._abort_reason(f)
      if reason is not None:
        player.abort()
        self.attempts += 1
        self._event("maneuver_aborted", f.mono_ns, maneuver=player.spec["id"], maneuver_desc=player.spec["desc"],
                    reason=reason, attempt=self.attempts, **self._road(f))
        if reason == "settings drift":
          self.verifier = SettingsVerifier(block["settings"], t_apply=f.t)
          self.verify_active_s = 0.0
          self.state = "verify"
        if self.attempts >= self.plan["max_attempts_per_maneuver"]:
          self._event("maneuver_skipped", f.mono_ns, maneuver=player.spec["id"], maneuver_desc=player.spec["desc"],
                      reason=f"{self.attempts} aborted attempts")
          self._next_maneuver(f)
        out.text1, out.state, out.phase = f"Aborted: {reason}", "setup", "aborted"
        return
    elif f.steering_pressed:
      player.ready_cnt = 0

    accel = player.update(f)
    speed_mph_now = f.v_ego / MPH_TO_MS
    limit = min(lat_accel_limit(block["speed_mph"]), lat_accel_limit(speed_mph_now), LAT_ACCEL_ABS_MAX)
    accel = float(np.clip(accel, -limit, limit))

    if player.just_started:
      self._event("maneuver_start", f.mono_ns, maneuver=player.spec["id"], maneuver_desc=player.spec["desc"],
                  spec={k: v for k, v in player.spec.items() if k != "notes"}, meta=player.meta,
                  settings=block["settings"], tag=block["tag"], speed_mph=block["speed_mph"],
                  active_settings={k: r["observed"] for k, r in self.verifier.results().items()},
                  block_index=self.block_idx + 1, maneuver_index=self.man_idx + 1,
                  baseline_curvature=player.baseline_curvature, attempt=self.attempts + 1, **self._road(f))

    if player.active or player.finished:
      out.accel = accel
      out.plan_valid = True
      out.desired_curvature = player.baseline_curvature + accel / max(f.v_ego, MIN_SPEED) ** 2
      kind = player.spec["type"]
      if kind == "sine":
        out.text1 = f"Active sine {player.spec['freq_hz']:.1f}Hz {player.remaining_s:.1f}s"
      elif kind == "hold":
        out.text1 = f"Active hold {player.remaining_s:.1f}s"
      else:
        out.text1 = f"Active {accel:+.1f}m/s² {player.remaining_s:.1f}s"
      out.state, out.phase = "running", "active"
      if player.finished:
        self._event("maneuver_end", f.mono_ns, maneuver=player.spec["id"], maneuver_desc=player.spec["desc"],
                    settings=block["settings"], tag=block["tag"], attempt=self.attempts + 1,
                    observed={k: r["observed"] for k, r in self.verifier.results().items()}, **self._road(f))
        self._holdoff_text2 = self._text2()
        self.holdoff_s = COMPLETE_HOLDOFF_S
        out.text1, out.phase = "Complete", "run_complete"
      return

    cond = player.conditions(f)
    out.state = "setup"
    if not (cond["speed"] and cond["lateral"]):
      out.text1, out.phase = f"Set speed to {block['speed_mph']:.0f} mph", "set_speed"
    elif player.ready_cnt > 0:
      out.text1, out.phase = f"Starting: {int(max(TIMER - player.ready_cnt * DT, 0)) + 1}", "stabilizing"
    else:
      reason = "road not straight" if not cond["straight"] else "road not flat" if not cond["flat"] else "hands off"
      out.text1, out.phase = f"Waiting: {reason}", "road_check"

  def _next_maneuver(self, f):
    self.man_idx += 1
    self.attempts = 0
    self.holdoff_s = 0.0
    if self.man_idx >= len(self.block["maneuvers"]):
      self._event("block_end", f.mono_ns, **self._road(f))
      self._next_block(f)
    else:
      self._new_player()

  def _next_block(self, f):
    self.block_idx += 1
    self.man_idx = 0
    self.attempts = 0
    self.apply_attempts = 0
    self.stable_s = 0.0
    self.verifier = None
    if self.block_idx >= len(self.blocks):
      self.finish("completed", f.mono_ns)
      return
    self.state = "apply_wait"
    self._new_player()

  def _step_done(self, f, out):
    out.state, out.phase = "finished", "done"
    out.text1 = "Characterization finished" if self.finish_reason == "completed" else f"Stopped: {self.finish_reason}"
    out.text2 = "settings restored"
    if self.restore_verifier is None:
      return
    self.restore_verifier.update(f.obs())
    self.restore_check_s += DT
    if self.restore_verifier.ok or self.restore_check_s >= RESTORE_CHECK_S:
      results = self.restore_verifier.results()
      self._event("restore_verified", f.mono_ns, ok=self.restore_verifier.ok,
                  observed={k: r["observed"] for k, r in results.items()},
                  expected={k: r["expected"] for k, r in results.items()})
      self.restore_verifier = None


# ---------------------------------------------------------------------------
# daemon wiring (device only)

SUBSCRIBED = ['carState', 'carControl', 'controlsState', 'selfdriveState', 'modelV2', 'liveDelay', 'starpilotPlan',
              'starpilotLateralState']
ROUTE_FALLBACK_S = 30.0  # name the sidecar without a route if loggerd never publishes one


def build_frame(sm, mono_ns, toggles):
  cs = sm['controlsState']
  lat = cs.lateralControlState
  torque = lat.torqueState if lat.which() == 'torqueState' else None
  sp_lat = sm['starpilotLateralState']
  cc = sm['carControl']
  return Frame(
    t=mono_ns * 1e-9,
    mono_ns=mono_ns,
    v_ego=max(sm['carState'].vEgo, 0.0),
    steering_pressed=bool(sm['carState'].steeringPressed),
    lat_active=bool(cc.latActive),
    enabled=bool(sm['selfdriveState'].enabled),
    curvature=float(cs.desiredCurvature),
    roll=float(cc.orientationNED[0]) if len(cc.orientationNED) == 3 else 0.0,
    pitch=float(cc.orientationNED[1]) if len(cc.orientationNED) == 3 else 0.0,
    live_delay=float(sm['liveDelay'].lateralDelay) if sm.recv_frame['liveDelay'] > 0 else None,
    live_delay_fresh=bool(sm.updated['liveDelay']),
    toggles=toggles,
    friction_threshold=float(sp_lat.frictionThreshold) if sp_lat.active else 0.0,
    pid_p=float(torque.p) if torque is not None else 0.0,
    pid_error=float(torque.error) if torque is not None else 0.0,
    pid_fresh=bool(sm.updated['controlsState'] and torque is not None and torque.active),
  )


def run_daemon(plan, snapshot_path=None, sidecar_dir=None):
  import atexit
  import signal

  from cereal import car, messaging
  from openpilot.common.params import Params
  from openpilot.common.swaglog import cloudlog
  from openpilot.tools.lateral_maneuvers.characterization.settings import (
    SNAPSHOT_PATH, ParamStore, SettingsManager, parse_toggles, touched_keys,
  )
  from openpilot.tools.lateral_maneuvers.characterization.sidecar import SIDECAR_DIR, Sidecar, boot_ns
  from openpilot.tools.lateral_maneuvers.lateral_maneuversd import _load_status, _save_status, _status_signature

  params = Params()
  params_memory = Params(memory=True)
  CP = messaging.log_from_bytes(params.get("CarParams", block=True), car.CarParams)
  ti_enabled = CP.carFingerprint == "HONDA_ACCORD_9G" and params.get_bool("TorqueInterceptorEnabled")

  mgr = SettingsManager(ParamStore(params, params_memory), snapshot_path or SNAPSHOT_PATH,
                        keys=touched_keys(plan["enable_advanced_lateral_tune"]), log=cloudlog.warning)
  header = {
    "plan": plan, "carFingerprint": CP.carFingerprint, "tiEnabled": bool(ti_enabled),
    "gitCommit": params.get("GitCommit") or "", "gitBranch": params.get("GitBranch") or "",
    "advancedLateralTune": params.get_bool("AdvancedLateralTune"),
  }
  sidecar = Sidecar(sidecar_dir or SIDECAR_DIR, header=header, log=cloudlog.warning)
  runner = CharacterizationRunner(plan, mgr, sidecar, log=cloudlog.info, ti_enabled=ti_enabled)
  last_mono = [boot_ns()]

  def _exit_restore():
    runner.finish("process_exit", last_mono[0])

  def _sigterm(signum, frame):
    raise SystemExit(0)

  atexit.register(_exit_restore)
  signal.signal(signal.SIGTERM, _sigterm)

  sm = messaging.SubMaster(SUBSCRIBED, poll='modelV2')
  pm = messaging.PubMaster(['lateralManeuverPlan', 'alertDebug'])
  status = _load_status(params)
  last_signature, last_status_write = "", 0.0
  last_toggles_text = ""
  route_wait_s = 0.0

  try:
    runner.start(last_mono[0], extra={"tiEnabled": bool(ti_enabled),
                                      "advancedLateralTune": header["advancedLateralTune"]})
    if not header["advancedLateralTune"] and not plan["enable_advanced_lateral_tune"] and \
       any("steer_delay" in b["settings"] for b in plan["blocks"]):
      cloudlog.warning("lateral characterization: AdvancedLateralTune is off, steer_delay blocks will not verify")
    while True:
      sm.update()
      mono_ns = sm.logMonoTime['modelV2'] or boot_ns()
      last_mono[0] = mono_ns

      if sidecar.path is None:
        route_wait_s += DT
        route = params.get("CurrentRoute") or ""
        if not route and route_wait_s >= ROUTE_FALLBACK_S:
          route = f"noroute-{int(sidecar.doc['startedWall'])}"
        sidecar.set_route(route)

      toggles = None
      text = sm['starpilotPlan'].starpilotToggles
      if sm.updated['starpilotPlan'] and text and text != last_toggles_text:
        last_toggles_text = text
        toggles = parse_toggles(text)

      out = runner.step(build_frame(sm, mono_ns, toggles))

      alert = messaging.new_message('alertDebug')
      alert.valid = True
      alert.alertDebug.alertText1 = out.text1
      alert.alertDebug.alertText2 = out.text2
      pm.send('alertDebug', alert)

      plan_msg = messaging.new_message('lateralManeuverPlan')
      plan_msg.valid = bool(out.plan_valid)
      if out.plan_valid:
        plan_msg.lateralManeuverPlan.desiredCurvature = float(out.desired_curvature)
      pm.send('lateralManeuverPlan', plan_msg)

      block = runner.block
      status.update({
        "state": out.state, "phase": out.phase,
        "maneuver": out.text2 if not out.text2.startswith("{") else "",
        "runIndex": min(runner.block_idx + 1, len(runner.blocks)), "runTotal": len(runner.blocks),
        "stepIndex": runner.man_idx + 1 if block is not None else 0,
        "stepTotal": len(block["maneuvers"]) if block is not None else 0,
        "phaseStepIndex": runner.man_idx + 1 if block is not None else 0,
        "phaseStepTotal": len(block["maneuvers"]) if block is not None else 0,
        "uiShow": True, "uiSize": "mid", "uiText1": out.text1,
        "uiText2": out.text2 if not out.text2.startswith("{") else "",
        "history": list(runner.history),
      })
      signature = _status_signature(status)
      now = mono_ns * 1e-9
      if signature != last_signature or now - last_status_write >= 1.0:
        status["updatedAtSec"] = now
        _save_status(params, status)
        last_signature, last_status_write = signature, now
  finally:
    _exit_restore()
