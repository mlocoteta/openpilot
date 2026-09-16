"""Choose a recognized CarParams snapshot for capability-gated settings.

The current persistent snapshot may temporarily be MOCK while the car process
starts. A matching previous route is safe for displaying an *available* toggle;
it never enables control or changes the panda safety configuration by itself.
"""

from cereal import car


def _fingerprint(raw: bytes | None) -> str:
  if not raw:
    return ""
  try:
    with car.CarParams.from_bytes(raw) as cp:
      return str(cp.carFingerprint)
  except Exception:
    return ""


def capability_car_params_bytes(params) -> bytes | None:
  """Prefer live/recognized params; fallback only to the exact forced model."""
  model = params.get("CarModel", encoding="utf-8") or ""
  forced = params.get_bool("ForceFingerprint")
  current_keys = ("CarParams", "CarParamsPersistent") if params.get_bool("IsOnroad") else ("CarParamsPersistent",)

  for key in current_keys:
    raw = params.get(key)
    fingerprint = _fingerprint(raw)
    if fingerprint and fingerprint != "MOCK":
      if forced and model and fingerprint != model:
        return None
      return raw

  if forced and model:
    previous = params.get("CarParamsPrevRoute")
    if _fingerprint(previous) == model:
      return previous
  return None
