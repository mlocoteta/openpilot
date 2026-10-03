"""Runtime recovery from the small fallback model to the external-GPU (Chestnut) model.

modeld decides big vs small once at start. When the Chestnut has no 12 V at that
moment (route 00000319: 0 V for 242 s after boot) the whole drive runs on the
small fallback, even after power returns. Re-selecting the model in the UI, which
sets OnroadCycleRequested, reloaded the big model fine mid-drive (route 0000031a).

This module decides *when* to ask for that same onroad cycle automatically:
  - only while the small fallback is running although a big model is configured,
  - only after the Chestnut's own 12 V input (chestnutState.supplyVoltage) has been
    >= 10 V for >= 10 s and the custom-firmware USB product is present,
  - only at a safe moment: stopped with the driver holding the brake (openpilot is
    then not controlling longitudinal), or fully disengaged for a while,
  - at most MAX_ATTEMPTS times per drive, with backoff between attempts.

The reload itself is the existing startup path: modeld loads the big model and, if
that fails, the small one, exactly as at ignition. A failed attempt therefore ends on
the small model again, and the next attempt waits for the backoff.

State lives in a small JSON file on tmpfs so that it survives the modeld restart that
the onroad cycle causes. selfdrived reads the same file to show a minor alert.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

STATE_PATH = Path(os.getenv("EGPU_RECOVERY_STATE", "/dev/shm/egpu_recovery.json"))
DISABLE_PATH = Path(os.getenv("EGPU_RECOVERY_DISABLE", "/data/egpu_auto_recover_disabled"))

POWER_READY_MV = 10000
POWER_STABLE_SECONDS = 10.0
CHECK_INTERVAL_SECONDS = 1.0
MAX_ATTEMPTS = 3
# Wait after the n-th failed attempt before the next one.
BACKOFF_SECONDS = (120.0, 300.0)
# Without an observed power loss the failure is probably not power related; one retry only.
MAX_ATTEMPTS_WITHOUT_POWER_LOSS = 1
FIRST_ATTEMPT_DELAY_WITHOUT_POWER_LOSS = 60.0
# A requested onroad cycle normally kills modeld within ~1 s. If it has not after this, count it as failed.
CYCLE_TIMEOUT_SECONDS = 20.0
# Safe-moment gates.
STANDSTILL_BRAKE_HOLD_SECONDS = 1.0
DISENGAGED_HOLD_SECONDS = 10.0
# selfdrived ignores the file if modeld stopped updating it.
STALE_SECONDS = 5.0

# Stages written to the state file.
IDLE = "idle"                  # big model active, or recovery not applicable
WAIT_POWER = "wait_power"      # on backup; Chestnut 12 V missing or not yet stable
WAIT_SAFE = "wait_safe"        # power stable; waiting for a stop with the brake held / disengaged
BACKOFF = "backoff"            # previous attempt failed; waiting before the next one
SWITCHING = "switching"        # onroad cycle requested
GAVE_UP = "gave_up"            # attempts exhausted; restart the car to retry
RECOVERED = "recovered"        # the big model loaded after an automatic attempt
DISABLED = "disabled"          # on backup, auto-recover switched off by DISABLE_PATH


@dataclass
class RecoveryState:
  stage: str = IDLE
  attempts: int = 0
  pending: bool = False          # an onroad cycle was requested and the next modeld start must report back
  last_attempt_t: float = 0.0    # time.monotonic() (system-wide, survives process restarts)
  last_fail_t: float = 0.0
  power_loss_seen: bool = False
  updated_t: float = 0.0
  detail: str = ""
  history: list = field(default_factory=list)


def load_state(path: Path = STATE_PATH) -> RecoveryState:
  try:
    raw = json.loads(path.read_text())
    known = RecoveryState.__dataclass_fields__.keys()
    return RecoveryState(**{k: v for k, v in raw.items() if k in known})
  except (OSError, ValueError, TypeError):
    return RecoveryState()


def save_state(state: RecoveryState, path: Path = STATE_PATH) -> None:
  try:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(state)))
    os.replace(tmp, path)
  except OSError:
    pass


def read_status(path: Path = STATE_PATH, now: float | None = None) -> RecoveryState | None:
  """For selfdrived: the current state, or None when modeld is not updating it."""
  state = load_state(path)
  now = time.monotonic() if now is None else now
  if state.updated_t <= 0 or now - state.updated_t > STALE_SECONDS:
    return None
  return state


def recovery_enabled() -> bool:
  return not DISABLE_PATH.exists()


@dataclass
class CarInputs:
  v_ego: float = 0.0
  standstill: bool = False
  brake_pressed: bool = False
  in_park: bool = False
  enabled: bool = False       # carControl.enabled
  lat_active: bool = False    # carControl.latActive (includes always-on lateral)
  long_active: bool = False   # carControl.longActive
  valid: bool = False         # carState/carControl seen and alive


class EgpuRecovery:
  """Decides when to request an onroad cycle to reload the big model. Pure logic; no I/O except the state file."""

  def __init__(self, big_model_active: bool, now: float, state_path: Path = STATE_PATH, enabled: bool = True):
    self.state_path = state_path
    self.enabled = enabled
    self.power_stable_since: float | None = None
    self.safe_since: float | None = None
    self.last_check = -1e9
    self.started_t = now
    self.recovered_until = now + 60.0
    prev = load_state(state_path)

    if prev.pending:
      # This modeld start was caused by our own onroad cycle: report the outcome.
      if big_model_active:
        self.state = RecoveryState(stage=RECOVERED, attempts=prev.attempts, last_attempt_t=prev.last_attempt_t,
                                   power_loss_seen=prev.power_loss_seen, detail=f"after attempt {prev.attempts}",
                                   history=(prev.history + [["ok", round(now, 1)]])[-10:])
      else:
        self.state = RecoveryState(stage=BACKOFF, attempts=prev.attempts, last_attempt_t=prev.last_attempt_t,
                                   last_fail_t=now, power_loss_seen=prev.power_loss_seen,
                                   history=(prev.history + [["fail", round(now, 1)]])[-10:])
        if self.state.attempts >= self._max_attempts():
          self.state.stage = GAVE_UP
    else:
      # Ignition start, a manual UI cycle, or a crash restart: start a fresh budget.
      self.state = RecoveryState(stage=IDLE if big_model_active else WAIT_POWER)
    if big_model_active and self.state.stage != RECOVERED:
      self.state.stage = IDLE
    self.state.pending = False
    self._save(now)

  def _max_attempts(self) -> int:
    return MAX_ATTEMPTS if self.state.power_loss_seen else MAX_ATTEMPTS_WITHOUT_POWER_LOSS

  def _save(self, now: float) -> None:
    self.state.updated_t = now
    save_state(self.state, self.state_path)

  def _next_attempt_t(self) -> float:
    s = self.state
    if s.attempts == 0:
      return self.started_t + (0.0 if s.power_loss_seen else FIRST_ATTEMPT_DELAY_WITHOUT_POWER_LOSS)
    idx = min(s.attempts - 1, len(BACKOFF_SECONDS) - 1)
    return max(s.last_fail_t, s.last_attempt_t) + BACKOFF_SECONDS[idx]

  @staticmethod
  def safe_moment(car: CarInputs) -> str | None:
    """Return why this is a safe moment to drop onroad, or None."""
    if not car.valid or car.long_active:
      return None
    if car.standstill and (car.brake_pressed or car.in_park):
      # Stopped and the driver holds the car; at most always-on lateral is active, which does nothing at a stop.
      return "standstill"
    if not car.enabled and not car.lat_active:
      return "disengaged"
    return None

  def update(self, now: float, big_model_active: bool, supply_mv: int | None, usb_ready: bool,
             car: CarInputs) -> bool:
    """Call every frame (cheap). Returns True exactly when an onroad cycle should be requested now."""
    if now - self.last_check < CHECK_INTERVAL_SECONDS:
      return False
    self.last_check = now
    s = self.state

    if big_model_active:
      if s.stage not in (IDLE, RECOVERED) or (s.stage == RECOVERED and now > self.recovered_until):
        s.stage = IDLE
      self._save(now)
      return False

    power_ok = usb_ready and supply_mv is not None and supply_mv >= POWER_READY_MV
    if not power_ok:
      s.power_loss_seen = True
      self.power_stable_since = None
    elif self.power_stable_since is None:
      self.power_stable_since = now
    power_stable = power_ok and now - self.power_stable_since >= POWER_STABLE_SECONDS

    reason = self.safe_moment(car)
    if reason is None:
      self.safe_since = None
    elif self.safe_since is None:
      self.safe_since = now
    hold = STANDSTILL_BRAKE_HOLD_SECONDS if reason == "standstill" else DISENGAGED_HOLD_SECONDS
    safe = reason is not None and now - self.safe_since >= hold

    request = False
    if not self.enabled:
      s.stage = DISABLED
    elif s.stage == SWITCHING:
      if now - s.last_attempt_t > CYCLE_TIMEOUT_SECONDS:
        s.pending = False
        s.last_fail_t = now
        s.history = (s.history + [["no_cycle", round(now, 1)]])[-10:]
        s.stage = GAVE_UP if s.attempts >= self._max_attempts() else BACKOFF
    elif s.stage == GAVE_UP:
      pass
    elif s.attempts >= self._max_attempts():
      s.stage = GAVE_UP
    elif not power_stable:
      s.stage = WAIT_POWER
      s.detail = "no 12 V" if supply_mv is not None and supply_mv < 1000 else ""
    elif now < self._next_attempt_t():
      s.stage = BACKOFF if s.attempts else WAIT_SAFE
      s.detail = f"{int(self._next_attempt_t() - now)} s"
    elif not safe:
      s.stage = WAIT_SAFE
    else:
      s.attempts += 1
      s.pending = True
      s.last_attempt_t = now
      s.stage = SWITCHING
      s.detail = reason
      s.history = (s.history + [["request", round(now, 1), reason, supply_mv]])[-10:]
      request = True

    self._save(now)
    return request
