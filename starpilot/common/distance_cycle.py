"""4-step distance cycle: Traffic (1 bar) -> Aggressive (2) -> Standard (3) -> Relaxed (4) -> Traffic.

Enabled by setting a distance button control to BUTTON_FUNCTIONS["PERSONALITY_TRAFFIC_CYCLE"].
Traffic Mode rides on top of the Aggressive personality. The personality itself persists in
LongitudinalPersonality; the Traffic Mode bit persists in a small file so it survives restarts
without adding a new params key (which would need a C++ params rebuild).
"""
import os
import threading
from pathlib import Path

# cereal LongitudinalPersonality raw values
AGGRESSIVE = 0
STANDARD = 1
RELAXED = 2

TRAFFIC_STATE_PATH = Path(os.getenv("DISTANCE_CYCLE_TRAFFIC_PATH", "/data/distance_cycle_traffic"))

PERSONALITY_TRAFFIC_CYCLE = 15  # BUTTON_FUNCTIONS["PERSONALITY_TRAFFIC_CYCLE"]
DISTANCE_BUTTON_PARAMS = {
  "distance": "DistanceButtonControl",
  "distance_long": "LongDistanceButtonControl",
  "distance_very_long": "VeryLongDistanceButtonControl",
}
_fallback_cycle_keys: frozenset | None = None


def _read_fallback_cycle_keys() -> frozenset:
  from openpilot.common.params import Params
  params = Params()
  keys = set()
  for key, param in DISTANCE_BUTTON_PARAMS.items():
    try:
      if int(float(params.get(param) or 0)) == PERSONALITY_TRAFFIC_CYCLE:
        keys.add(key)
    except (TypeError, ValueError):
      pass
  return frozenset(keys)


def _fallback_cycle_via(toggles, key: str) -> bool:
  # starpilot_process is always running, so after a code-only update it can still publish toggles
  # without the cycle flags. Read the button setting once per (onroad) process instead.
  global _fallback_cycle_keys
  if not getattr(toggles, "openpilot_longitudinal", False):
    return False
  if _fallback_cycle_keys is None:
    try:
      _fallback_cycle_keys = _read_fallback_cycle_keys()
    except Exception:
      _fallback_cycle_keys = frozenset()
  return key in _fallback_cycle_keys if key else bool(_fallback_cycle_keys)


def distance_cycle_via(toggles, key: str) -> bool:
  if hasattr(toggles, "distance_traffic_cycle"):
    return bool(getattr(toggles, f"distance_cycle_via_{key}", False))
  return key in DISTANCE_BUTTON_PARAMS and _fallback_cycle_via(toggles, key)


def distance_cycle_enabled(toggles) -> bool:
  if hasattr(toggles, "distance_traffic_cycle"):
    return bool(toggles.distance_traffic_cycle)
  return _fallback_cycle_via(toggles, "")


def next_cycle_state(personality: int, traffic_enabled: bool) -> tuple[int, bool]:
  """Return (personality, traffic_enabled) after one short press."""
  if traffic_enabled:
    return AGGRESSIVE, False
  if personality == AGGRESSIVE:
    return STANDARD, False
  if personality == STANDARD:
    return RELAXED, False
  return AGGRESSIVE, True


def cycle_lead_distance_bars(personality: int, traffic_enabled: bool) -> int:
  """Dash bars for the 4-step cycle. Honda's 2-bit HUD_DISTANCE encodes 4 bars as 0 (the packer masks 4 -> 0)."""
  if traffic_enabled:
    return 1
  return min(max(int(personality), AGGRESSIVE), RELAXED) + 2


def load_traffic_state(path: Path | None = None) -> bool:
  path = path or TRAFFIC_STATE_PATH
  try:
    return path.read_text().strip() == "1"
  except (OSError, ValueError):
    return False


def _write_traffic_state(path: Path, enabled: bool) -> None:
  try:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("1\n" if enabled else "0\n")
    os.replace(tmp, path)
  except OSError:
    pass


def save_traffic_state_nonblocking(enabled: bool, path: Path | None = None) -> threading.Thread:
  # File IO stays off the 100 Hz card loop.
  thread = threading.Thread(target=_write_traffic_state, args=(path or TRAFFIC_STATE_PATH, enabled), daemon=True)
  thread.start()
  return thread
