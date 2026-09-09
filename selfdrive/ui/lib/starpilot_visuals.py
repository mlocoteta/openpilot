from __future__ import annotations

import math

import pyray as rl

from openpilot.common.params import Params


_BORDER_ROUNDNESS = 0.12
_BORDER_RADIUS_MULTIPLE = 3.0


def get_border_roundness(rect: rl.Rectangle, border_width: float) -> float:
  """Keep a rectangular camera inset inside the rounded frame at thin widths."""
  min_dimension = max(1.0, min(rect.width, rect.height))
  return min(_BORDER_ROUNDNESS, 2.0 * _BORDER_RADIUS_MULTIPLE * border_width / min_dimension)


def blend_colors(a: rl.Color, b: rl.Color, f: float) -> rl.Color:
  h0, s0, v0 = (hsv0 := rl.color_to_hsv(a)).x, hsv0.y, hsv0.z
  h1, s1, v1 = (hsv1 := rl.color_to_hsv(b)).x, hsv1.y, hsv1.z
  dh = ((h1 - h0 + 180) % 360) - 180  # shortest hue delta
  return rl.color_from_hsv((h0 + f * dh) % 360,
                           s0 + f * (s1 - s0),
                           v0 + f * (v1 - v0))


def get_border_width(base_width: int, params: Params | None = None) -> int:
  active_params = params if params is not None else Params()

  scale = active_params.get_float("BorderWidth", return_default=True, default=100.0)
  if not math.isfinite(scale):
    scale = 100.0
  scale = min(250.0, max(25.0, scale))

  return max(1, int(round(base_width * scale / 100.0)))


def lead_indicator_enabled(params: Params | None = None, *, hide_by_default: bool = False) -> bool:
  active_params = params if params is not None else Params()

  if active_params.get("HideLeadMarker") is None:
    return not hide_by_default
  return not active_params.get_bool("HideLeadMarker")
