"""Minor onroad alert while modeld runs the small fallback instead of the configured external-GPU model."""
from __future__ import annotations

from openpilot.selfdrive.modeld import egpu_recovery as R

SHOW_SECONDS = 12.0       # how long the alert stays up after each stage change
REMINDER_SECONDS = 300.0  # re-show while still on the backup model
RECOVERED_SECONDS = 6.0

BACKUP = "Backup driving model"


def alert_text(state: R.RecoveryState) -> tuple[str, str]:
  stage = state.stage
  if stage == R.WAIT_POWER:
    return BACKUP, "GPU reconnecting: no 12 V power" if state.detail == "no 12 V" else "GPU reconnecting"
  if stage == R.WAIT_SAFE:
    return BACKUP, "GPU ready: switches at next stop with brake held"
  if stage == R.BACKOFF:
    return BACKUP, f"GPU switch failed, retrying ({state.attempts}/{R.MAX_ATTEMPTS})"
  if stage == R.SWITCHING:
    return "Switching to GPU model", "openpilot restarts, about 30 s"
  if stage == R.GAVE_UP:
    return BACKUP, "GPU retries failed: restart car to retry"
  if stage == R.DISABLED:
    return BACKUP, "GPU auto-recover is off"
  if stage == R.RECOVERED:
    return "GPU model restored", ""
  return "", ""


class GpuBackupAlert:
  def __init__(self):
    self.stage_prev: str | None = None
    self.show_until = 0.0
    self.next_reminder = 0.0

  def update(self, now: float, state: R.RecoveryState | None) -> tuple[str, str] | None:
    """Return (text1, text2) when the alert should be shown this frame, else None."""
    if state is None or state.stage == R.IDLE:
      self.stage_prev = None
      return None

    if state.stage != self.stage_prev:
      self.show_until = now + (RECOVERED_SECONDS if state.stage == R.RECOVERED else SHOW_SECONDS)
      self.next_reminder = now + REMINDER_SECONDS
    elif state.stage not in (R.RECOVERED, R.SWITCHING) and now >= self.next_reminder:
      self.show_until = now + SHOW_SECONDS
      self.next_reminder = now + REMINDER_SECONDS
    self.stage_prev = state.stage

    if state.stage == R.SWITCHING or now < self.show_until:
      text1, text2 = alert_text(state)
      return (text1, text2) if text1 else None
    return None
