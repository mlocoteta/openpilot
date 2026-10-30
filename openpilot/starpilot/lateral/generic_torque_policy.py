"""Shared StarPilot torque shaping using the vehicle's own calibration and conversion."""

from openpilot.common.scalar_clip import clip_scalar
from openpilot.starpilot.lateral.controller_selection import generic_torque_supported
from openpilot.starpilot.lateral.hkg_torque_policy import HKGShapedTorquePolicy
from openpilot.starpilot.lateral.torque_shaping import get_standard_friction_threshold


class GenericTorquePolicy(HKGShapedTorquePolicy):
  supported_cp = staticmethod(generic_torque_supported)

  def feedforward(self, value, setpoint, jerk, speed):
    return value

  def friction(self, setpoint, jerk, speed):
    return get_standard_friction_threshold(speed), 1.0

  def output(self, value, setpoint, speed):
    return clip_scalar(value, -self.parent.steer_max, self.parent.steer_max)
