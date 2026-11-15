"""card.py side of the Accord 9G SSV3 firmware-3 support (opendbc/car/honda/ssv3.py).

* Reads the four developer params (all default off) about once a second and hands them to the car
  controller as requested 0xE4 option bits. The car controller only puts them on the wire once the
  board has reported firmware >= 3 for this drive; a firmware-2 board never sees them.
* Once firmware >= 3 is seen, adds starpilotCarState.ssv3 (version, EPS_LKAS_ACK, CAMERA_FAULT, signed
  motor torque, options sent) to the carState companion. Nothing is published for firmware 2.
* SSV3BlendProbe (developer EPS torque-blend probe, default 0 = off, cleared at every manager start and onroad /
  offroad transition): read with the option params and handed to the car controller's probe
  (opendbc/car/honda/ssv3.py Ssv3BlendProbe). When the probe ends (completed or aborted) the param is cleared here,
  and no non-zero value is handed over again until the param has read back 0.
"""
import openpilot.cereal.messaging as messaging
from opendbc.car.honda.ssv3 import PROBE_END_NAMES, ProbeState, Ssv3Option
from opendbc.car.honda.values import CAR

OPTION_PARAMS = (
  ("SSV3TorqueBlendDisable", Ssv3Option.TORQUE_BLEND_DISABLE),
  ("SSV3TxAllLkasData", Ssv3Option.TX_ALL_LKAS_DATA),
  ("SSV3LsbToggleDisable", Ssv3Option.LSB_TOGGLE_DISABLE),
  ("SSV3ZeroTorqueKeepsLkasOn", Ssv3Option.ZERO_TORQUE_KEEPS_LKAS_ON),
)
PARAM_INTERVAL = 100  # carState frames (~1 s)
PROBE_PARAM = "SSV3BlendProbe"


def read_options(params) -> int:
  options = 0
  for key, bit in OPTION_PARAMS:
    try:
      if params.get_bool(key):
        options |= bit
    except Exception:
      pass  # unreadable = off
  return options


def read_probe(params) -> int:
  try:
    value = params.get(PROBE_PARAM)
    return max(0, int(value)) if value is not None else 0
  except Exception:
    return 0  # unreadable = off


def blend_probe_alert_active(CP, sm) -> bool:
  """selfdrived: show the "Blend test" alert while the probe is armed, holding or resting."""
  if CP.carFingerprint != CAR.HONDA_ACCORD_9G:
    return False
  try:
    if not (sm.seen['starpilotCarState'] and sm.alive['starpilotCarState']):
      return False
    return int(sm['starpilotCarState'].ssv3.blendProbeState) in (ProbeState.ARMED, ProbeState.HOLD, ProbeState.REST)
  except (KeyError, AttributeError):
    return False


class Ssv3Feed:
  def __init__(self, controller, car_state_owner, params):
    self.controller = controller
    self.owner = car_state_owner   # the opendbc CarState; .ssv3 is its Ssv3CarState
    self.params = params
    self.frame = 0
    self.probe_awaiting_clear = False

  def update(self, CS, message, *, car_state_stamp):
    if self.frame % PARAM_INTERVAL == 0:
      self.controller.requested_options = read_options(self.params)
      probe = read_probe(self.params)
      if self.probe_awaiting_clear:
        self.controller.requested_probe = 0
        self.probe_awaiting_clear = probe != 0
      else:
        self.controller.requested_probe = probe
    self.frame += 1
    self._clear_finished_probe()
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
    probe = self.controller.probe
    out.blendProbeProgram = probe.program
    out.blendProbeState = probe.state
    out.blendProbeWindow = probe.window if probe.active else -1
    out.blendProbeCommand = probe.command
    out.blendProbeEnd = probe.end
    out.blendProbeTime = probe.total * 0.01
    out.steerStatus = max(0, min(255, int(ssv3.steer_status)))
    return message

  def _clear_finished_probe(self):
    probe = self.controller.probe
    if not probe.finished or self.probe_awaiting_clear:
      return
    self.probe_awaiting_clear = True
    self.controller.requested_probe = 0
    try:
      from openpilot.common.swaglog import cloudlog
      cloudlog.warning(f"ssv3 blend probe ended: program {probe.program} {PROBE_END_NAMES.get(probe.end, probe.end)}")
    except Exception:
      pass
    try:
      self.params.put(PROBE_PARAM, 0)
    except Exception:
      pass  # the latch above still keeps it off for the rest of the drive


def install(CI, params):
  """Returns a feed for a 9G Accord on the SSV3 path, else None."""
  controller = getattr(CI.CC, 'ssv3', None)
  if controller is None or getattr(CI.CS, 'ssv3', None) is None:
    return None
  return Ssv3Feed(controller, CI.CS, params)
