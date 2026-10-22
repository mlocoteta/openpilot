"""Honda 9G Accord (2016-17) Serial Steering V2 (SSV2) board.

The 2016-17 Accord camera steers the EPS over a serial (LIN-like) link, not CAN. The SSV2 board
sits on that link on the camera side of the harness (panda bus 2). It reads openpilot's
STEERING_CONTROL (0xE4) on bus 2, replaces the camera's LKAS frame to the EPS, and reports the
EPS state back as a 4-byte STEER_STATUS (0x190) on bus 2. Mat's 9G logs (TI era) also show a 5-byte
0x190 in the SSV3 layout on the car side (bus 0); openpilot does not read that one in SSV2 mode.
"""
import numpy as np


def apply_ssv2_steer_torque_limits(apply_torque: float, apply_torque_last: int, driver_torque: float, LIMITS) -> int:
  """Driver-torque limit with a symmetric window, then the standard torque rate limit.

  Same behaviour as the 2023 SSV2 `ss=True` path: the driver allowance window is computed the
  usual way, then the smaller of its two sides is used in both directions. Driver torque in
  either direction therefore shrinks the allowed torque equally, and the result does not depend
  on the sign convention of the board's driver torque sensor.
  """
  driver_offset = driver_torque * LIMITS.STEER_DRIVER_FACTOR
  driver_max_torque = LIMITS.STEER_MAX + (LIMITS.STEER_DRIVER_ALLOWANCE + driver_offset) * LIMITS.STEER_DRIVER_MULTIPLIER
  driver_min_torque = -LIMITS.STEER_MAX + (-LIMITS.STEER_DRIVER_ALLOWANCE + driver_offset) * LIMITS.STEER_DRIVER_MULTIPLIER
  max_steer_allowed = max(min(LIMITS.STEER_MAX, driver_max_torque), 0)
  min_steer_allowed = min(max(-LIMITS.STEER_MAX, driver_min_torque), 0)
  steer_allowed = min(max_steer_allowed, -min_steer_allowed)
  apply_torque = np.clip(apply_torque, -steer_allowed, steer_allowed)

  # slow rate if steer torque increases in magnitude
  if apply_torque_last > 0:
    apply_torque = np.clip(apply_torque, max(apply_torque_last - LIMITS.STEER_DELTA_DOWN, -LIMITS.STEER_DELTA_UP),
                           apply_torque_last + LIMITS.STEER_DELTA_UP)
  else:
    apply_torque = np.clip(apply_torque, apply_torque_last - LIMITS.STEER_DELTA_UP,
                           min(apply_torque_last + LIMITS.STEER_DELTA_DOWN, LIMITS.STEER_DELTA_UP))

  return int(round(float(apply_torque)))
