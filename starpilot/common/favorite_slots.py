#!/usr/bin/env python3
from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from openpilot.common.params import ParamKeyType, Params


FAVORITE_SLOTS_PARAM = "StarPilotFavoriteSlots"
FAVORITE_SLOT_COUNT = 3
FAVORITE_ACTION_PREFIX = "__starpilot_favorite_action__:"
FAVORITE_ACTION_DISTANCE_DECREASE = f"{FAVORITE_ACTION_PREFIX}distance_decrease"
FAVORITE_ACTION_DISTANCE_INCREASE = f"{FAVORITE_ACTION_PREFIX}distance_increase"
FAVORITE_ACTION_TOGGLE_TRAFFIC_MODE = f"{FAVORITE_ACTION_PREFIX}toggle_traffic_mode"
FAVORITE_ACTION_DECEL_COUNTER = "FavoriteVirtualDecelCruiseCounter"
FAVORITE_ACTION_ACCEL_COUNTER = "FavoriteVirtualAccelCruiseCounter"
FAVORITE_ACTION_TRAFFIC_MODE_COUNTER = "FavoriteTrafficModeCounter"
FAVORITE_ACTION_OPTIONS = (
  {
    "key": FAVORITE_ACTION_DISTANCE_DECREASE,
    "label": "Distance - / SET",
    "description": "Acts like a short press of the car's SET/- cruise button.",
    "section": "Actions",
    "action": "decelCruise",
  },
  {
    "key": FAVORITE_ACTION_DISTANCE_INCREASE,
    "label": "Distance + / RES",
    "description": "Acts like a short press of the car's RES/+ cruise button.",
    "section": "Actions",
    "action": "accelCruise",
  },
  {
    "key": FAVORITE_ACTION_TOGGLE_TRAFFIC_MODE,
    "label": "Toggle Traffic Mode",
    "description": "Engages or disengages Traffic Mode while openpilot is actively controlling.",
    "section": "Actions",
    "action": "trafficMode",
  },
)
FAVORITE_ACTION_KEYS = {option["key"] for option in FAVORITE_ACTION_OPTIONS}
FAVORITE_ACTION_LABELS = {option["key"]: option["label"] for option in FAVORITE_ACTION_OPTIONS}


def default_favorite_slots() -> list[dict[str, Any]]:
  return [
    {"enabled": False, "show_onroad": False, "key": None, "label": ""}
    for _ in range(FAVORITE_SLOT_COUNT)
  ]


def _load_raw_slots(raw_slots: Any) -> list[Any]:
  if raw_slots in (None, "", b""):
    return default_favorite_slots()

  if isinstance(raw_slots, bytes):
    raw_slots = raw_slots.decode("utf-8", errors="replace")

  if isinstance(raw_slots, str):
    try:
      raw_slots = json.loads(raw_slots)
    except json.JSONDecodeError:
      return default_favorite_slots()

  if isinstance(raw_slots, dict):
    raw_slots = raw_slots.get("slots", [])

  return raw_slots if isinstance(raw_slots, list) else default_favorite_slots()


def _get_key_type(params: Params, key: str):
  for getter_name in ("get_type", "get_key_type"):
    getter = getattr(params, getter_name, None)
    if getter is None:
      continue
    try:
      return getter(key)
    except Exception:
      return None
  return None


def is_favorite_action_key(key: str | None) -> bool:
  return bool(key) and key in FAVORITE_ACTION_KEYS


def favorite_key_is_valid(params: Params, key: str | None, eligible_keys: Iterable[str] | None = None) -> bool:
  if not key:
    return False

  if is_favorite_action_key(key):
    return True

  if eligible_keys is not None and key not in set(eligible_keys):
    return False

  return _get_key_type(params, key) == ParamKeyType.BOOL


def is_bool_param(params: Params, key: str | None, eligible_keys: Iterable[str] | None = None) -> bool:
  if not key:
    return False

  if eligible_keys is not None and key not in set(eligible_keys):
    return False

  return _get_key_type(params, key) == ParamKeyType.BOOL


def normalize_favorite_slots(raw_slots: Any, params: Params | None = None,
                             eligible_keys: Iterable[str] | None = None) -> list[dict[str, Any]]:
  slots = default_favorite_slots()
  eligible = set(eligible_keys) if eligible_keys is not None else None

  for idx, raw_slot in enumerate(_load_raw_slots(raw_slots)[:FAVORITE_SLOT_COUNT]):
    if not isinstance(raw_slot, dict):
      continue

    key = raw_slot.get("key")
    if key is not None:
      key = str(key).strip() or None

    if key and is_favorite_action_key(key):
      pass
    elif key and (
      (eligible is not None and key not in eligible) or
      (params is not None and not is_bool_param(params, key))
    ):
      key = None

    label = str(raw_slot.get("label") or FAVORITE_ACTION_LABELS.get(key, "")).strip()
    if len(label) > 32:
      label = label[:32].rstrip()

    slots[idx] = {
      "enabled": bool(raw_slot.get("enabled", False)),
      "show_onroad": bool(raw_slot.get("show_onroad", False)),
      "key": key,
      "label": label if key else "",
    }

  return slots


def load_favorite_slots(params: Params | None = None, eligible_keys: Iterable[str] | None = None) -> list[dict[str, Any]]:
  params = params or Params(return_defaults=True)
  try:
    raw_slots = params.get(FAVORITE_SLOTS_PARAM)
  except Exception:
    raw_slots = None
  return normalize_favorite_slots(raw_slots, params=params, eligible_keys=eligible_keys)


def save_favorite_slots(slots: list[dict[str, Any]], params: Params | None = None) -> list[dict[str, Any]]:
  params = params or Params(return_defaults=True)
  normalized = normalize_favorite_slots(slots, params=params)
  params.put(FAVORITE_SLOTS_PARAM, normalized)
  return normalized


def request_starpilot_toggle_refresh(params_memory: Params | None = None) -> None:
  params_memory = params_memory or Params(memory=True)
  params_memory.put_bool("StarPilotTogglesUpdated", True)


def trigger_favorite_action(key: str | None, params_memory: Params | None = None) -> bool:
  if not is_favorite_action_key(key):
    return False

  params_memory = params_memory or Params(memory=True)
  counter_key = {
    FAVORITE_ACTION_DISTANCE_DECREASE: FAVORITE_ACTION_DECEL_COUNTER,
    FAVORITE_ACTION_DISTANCE_INCREASE: FAVORITE_ACTION_ACCEL_COUNTER,
    FAVORITE_ACTION_TOGGLE_TRAFFIC_MODE: FAVORITE_ACTION_TRAFFIC_MODE_COUNTER,
  }[key]
  params_memory.put_int(counter_key, params_memory.get_int(counter_key) + 1)
  return True


def toggle_favorite_slot(slot_index: int, params: Params | None = None, params_memory: Params | None = None) -> bool:
  if slot_index < 0 or slot_index >= FAVORITE_SLOT_COUNT:
    return False

  params = params or Params(return_defaults=True)
  slots = load_favorite_slots(params)
  slot = slots[slot_index]
  key = slot.get("key")
  if not slot.get("enabled"):
    return False

  if is_favorite_action_key(key):
    return trigger_favorite_action(key, params_memory)

  if not is_bool_param(params, key):
    return False

  if key == "AlphaLongitudinalEnabled" and params.get_bool("IsOnroad"):
    return False

  next_value = not params.get_bool(key)
  put_bool = getattr(params, "put_bool_nonblocking", None) or getattr(params, "put_bool", None)
  if put_bool is None:
    return False

  put_bool(key, next_value)
  request_starpilot_toggle_refresh(params_memory)
  return True
