"""The production lateral-controller selection, shared with independent replay."""

from opendbc.car import structs
from openpilot.selfdrive.controls.lib.latcontrol_angle import LatControlAngle
from openpilot.selfdrive.controls.lib.latcontrol_curvature import LatControlCurvature
from openpilot.selfdrive.controls.lib.latcontrol_pid import LatControlPID
from openpilot.selfdrive.controls.lib.latcontrol_torque import LatControlTorque
from openpilot.selfdrive.controls.lib.latcontrol_torque_ti import LatControlTorqueTI, ti_lateral_qualified


def create_lateral_controller(cp, ci, dt, *, mode, turn_assist=False):
  if cp.steerControlType == structs.CarParams.SteerControlType.angle:
    return LatControlAngle(cp, ci, dt)
  if cp.steerControlType == structs.CarParams.SteerControlType.curvature:
    return LatControlCurvature(cp, ci, dt)
  if cp.lateralTuning.which() == 'pid':
    return LatControlPID(cp, ci, dt)
  if ti_lateral_qualified(cp):  # Honda 9G Accord Torque Interceptor (F03)
    return LatControlTorqueTI(cp, ci, dt)
  if cp.lateralTuning.which() == 'torque':
    return LatControlTorque(cp, ci, dt, controller_mode=mode, turn_assist=turn_assist)
  raise ValueError('No lateral controller for CarParams')
