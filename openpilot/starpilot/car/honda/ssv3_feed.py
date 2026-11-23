"""card.py side of the Accord 9G SSV3 firmware-3 support (opendbc/car/honda/ssv3.py).

* Reads the three developer option params (all default off) about once a second and hands them to the car
  controller as requested 0xE4 option bits. The car controller only puts them on the wire once the
  board has reported firmware >= 3 for this drive; a firmware-2 board never sees them.
* Once firmware >= 3 is seen, adds starpilotCarState.ssv3 (version, EPS_LKAS_ACK, CAMERA_FAULT, signed
  427 torque, options sent) to the carState companion. Nothing is published for firmware 2.
* The wind-up guard state (lkasCut, cutReason, boardMode, ...) is published in starpilotCarState.ssv3 so it is in
  every log.
* Retired 2026-11-23: the blend probe (SSV3BlendProbe), SSV3DeadbandComp and the SSV3TxAllLkasData param. Their
  Ssv3Status fields stay in the schema for old logs and are written with their old idle values.
"""
import openpilot.cereal.messaging as messaging
from opendbc.car.honda.ssv3 import Ssv3Option

OPTION_PARAMS = (
  ("SSV3TorqueBlendDisable", Ssv3Option.TORQUE_BLEND_DISABLE),
  ("SSV3LsbToggleDisable", Ssv3Option.LSB_TOGGLE_DISABLE),
  ("SSV3ZeroTorqueKeepsLkasOn", Ssv3Option.ZERO_TORQUE_KEEPS_LKAS_ON),
)
PARAM_INTERVAL = 100  # carState frames (~1 s)


def read_options(params) -> int:
  options = 0
  for key, bit in OPTION_PARAMS:
    try:
      if params.get_bool(key):
        options |= bit
    except Exception:
      pass  # unreadable = off
  return options


class Ssv3Feed:
  def __init__(self, controller, car_state_owner, params):
    self.controller = controller
    self.owner = car_state_owner   # the opendbc CarState; .ssv3 is its Ssv3CarState
    self.params = params
    self.frame = 0

  def update(self, CS, message, *, car_state_stamp):
    if self.frame % PARAM_INTERVAL == 0:
      self.controller.requested_options = read_options(self.params)
    self.frame += 1
    ssv3 = self.owner.ssv3
    if not ssv3.fw3:
      return message
    if message is None:
      message = messaging.new_message('starpilotCarState', valid=bool(CS.canValid), logMonoTime=car_state_stamp)
      message.starpilotCarState.sourceCarStateMonoTime = car_state_stamp
    out = message.starpilotCarState.ssv3
    out.firmwareVersion = ssv3.version
    out.hardwareRev = ssv3.hardware_rev
    out.epsLkasAck = ssv3.eps_lkas_ack
    out.cameraFault = ssv3.camera_fault
    out.motorTorque = ssv3.motor_torque
    out.lkasBlocked = ssv3.lkas_blocked
    out.options = self.controller.options(self.owner)
    out.blendProbeWindow = -1  # retired blend-probe fields: idle values (the others default to 0)
    out.steerStatus = max(0, min(255, int(ssv3.steer_status)))
    guard = self.controller.guard
    out.lkasCut = bool(guard.reason)
    out.cutReason = int(guard.reason)
    out.boardMode = max(0, min(255, int(ssv3.board_mode)))
    out.boardSteerRequest = bool(ssv3.board_request)
    out.linFatalError = bool(ssv3.lin_fatal)
    return message


def install(CI, params):
  """Returns a feed for a 9G Accord on the SSV3 path, else None."""
  controller = getattr(CI.CC, 'ssv3', None)
  if controller is None or getattr(CI.CS, 'ssv3', None) is None:
    return None
  return Ssv3Feed(controller, CI.CS, params)
