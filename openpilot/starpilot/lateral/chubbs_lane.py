"""Optional model-frame lane correction; final steering limits remain in Controls."""

import math

import numpy as np

from openpilot.starpilot.lateral.blendful import Blendful, X_IDXS, LOOKAHEAD_TIME, MIN_LOOKAHEAD, MIN_SPEED
from openpilot.starpilot.saved_source import read_saved

KEY = "TryChubbsLaneCentering"
DESCRIPTION = ("Experimental lane-line guidance instead of StarPilot lane centering. Uses compatible local model outputs; " +
               "does not change steering limits. Applies next drive.")


def selected(params):
  raw, readable = read_saved(params, KEY, 8)
  return readable and raw == b"1"


class ChubbsLaneCentering:
  def __init__(self, enabled):
    self.enabled = enabled
    self.policy = Blendful() if enabled else None

  def apply(self, outputs, action, speed, *, active, desire, lane_change):
    if not self.enabled:
      return action
    if not active or desire != 0 or lane_change != 0 or not math.isfinite(speed) or speed < MIN_SPEED:
      self.policy = Blendful()
      return action
    arrays = {name: outputs.get(name) for name in ("lane_lines", "lane_lines_stds", "lane_lines_prob", "plan")}
    shapes = {"lane_lines": (1, 4, 33, 2), "lane_lines_stds": (1, 4, 33, 2), "lane_lines_prob": (1, 8)}
    valid = all(isinstance(value, np.ndarray) and value.dtype.kind in "fiu" and np.isfinite(value).all()
                for value in arrays.values())
    if valid:
      plan, stds, probs = arrays["plan"], arrays["lane_lines_stds"], arrays["lane_lines_prob"]
      lookahead = max(speed * LOOKAHEAD_TIME, MIN_LOOKAHEAD)
      valid = (all(arrays[name].shape == shape for name, shape in shapes.items()) and
               plan.ndim == 3 and plan.shape[:2] == (1, 33) and plan.shape[2] >= 3 and
               np.all(np.diff(plan[0, :, 0]) > 0) and np.all(stds[:, 1:3] > 0) and
               np.all((probs >= 0) & (probs <= 1)) and
               np.count_nonzero((X_IDXS >= 0.5 * lookahead) & (X_IDXS <= 1.5 * lookahead)) >= 3 and
               math.isfinite(action.desiredCurvature))
    if not valid:
      self.policy = Blendful()
      return action
    correction = self.policy.update(outputs, speed, True, action.desiredCurvature)
    if math.isfinite(correction):
      action.desiredCurvature += correction
    else:
      self.policy = Blendful()
    return action
