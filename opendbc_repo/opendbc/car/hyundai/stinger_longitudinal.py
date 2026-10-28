"""Stinger forecast stopping intent from Dom; acceleration stays planner-owned."""
import numpy as np

from opendbc.car.hyundai.values import CAR


def forecast_should_stop(cp, speeds, time_indices, action_t):
  if cp.carFingerprint != CAR.KIA_STINGER_2022 or not cp.openpilotLongitudinalControl:
    return None
  if len(speeds) != len(time_indices) or len(speeds) < 2:
    return None
  threshold = float(np.float32(0.3))
  return bool(np.interp(action_t, time_indices, speeds) < threshold and
              np.interp(action_t + 1.0, time_indices, speeds) < threshold)
