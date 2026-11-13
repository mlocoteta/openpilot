"""card.py side of the Accord 9G SSV3 firmware-3 support (opendbc/car/honda/ssv3.py).

* Reads the four developer params (all default off) about once a second and hands them to the car
  controller as requested 0xE4 option bits. The car controller only puts them on the wire once the
  board has reported firmware >= 3 for this drive; a firmware-2 board never sees them.
* Once firmware >= 3 is seen, adds starpilotCarState.ssv3 (version, EPS_LKAS_ACK, CAMERA_FAULT, signed
  motor torque, options sent) to the carState companion. Nothing is published for firmware 2.
"""
import openpilot.cereal.messaging as messaging
from opendbc.car.honda.ssv3 import Ssv3Option

OPTION_PARAMS = (
  ("SSV3TorqueBlendDisable", Ssv3Option.TORQUE_BLEND_DISABLE),
  ("SSV3TxAllLkasData", Ssv3Option.TX_ALL_LKAS_DATA),
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
    return message


def install(CI, params):
  """Returns a feed for a 9G Accord on the SSV3 path, else None."""
  controller = getattr(CI.CC, 'ssv3', None)
  if controller is None or getattr(CI.CS, 'ssv3', None) is None:
    return None
  return Ssv3Feed(controller, CI.CS, params)
