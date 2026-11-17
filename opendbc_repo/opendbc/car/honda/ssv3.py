"""SSV3 serial-steering board, firmware 3 additions (2016-17 Accord, HONDA_ACCORD_9G).

The board sits on the camera <-> EPS serial link, takes 0xE4 STEERING_CONTROL from openpilot on the
powertrain bus and reports STEER_STATUS (400), STEER_MOTOR_TORQUE (427) and SS_STATUS (520) there.
Firmware 3 adds signals in bits firmware 2 sends differently, so everything here is gated on
SS_STATUS.VERSION_NUM >= 3:

  * 400 bit 39 is EPS_LKAS_ACK on firmware 3 but firmware 2's steer-blended flag; bit 38 CAMERA_FAULT.
  * 427 MOTOR_TORQUE is two's-complement on firmware 3 (sign-magnitude-ish on firmware 2). The shared
    _honda_common.dbc declares it unsigned for every Honda and is left alone; it is re-signed here.
  * 0xE4 byte 2 bits 0-3 are board options. On firmware 2, bit 0 disables torque limiting and bit 1
    turns on an old debug frame, so they must never be non-zero unless firmware 3 has been seen.

Firmware 3 needs FW3_CONFIRM_FRAMES valid 520 frames with VERSION_NUM >= 3 and is dropped again when 520
stops for FW3_LOST_FRAMES (or reports < 3). Firmware-2 boards (and boards with no 520 at all) see exactly
what upstream sends: the 0xE4 bytes are
untouched unless firmware 3 was seen AND an option was requested, and the extra frames are read by a
separate advisory parser whose validity never reaches carState.canValid / canTimeout.
"""
import math

from opendbc.can import CANParser
from opendbc.car import Bus, structs
from opendbc.car.honda.hondacan import CanBus, honda_checksum
from opendbc.car.honda.values import CAR

ButtonType = structs.CarState.ButtonEvent.Type

STEERING_CONTROL_ADDR = 0xE4
SS_STATUS_ADDR = 520
FW3 = 3
# Consecutive checksum/counter-valid SS_STATUS frames with VERSION_NUM >= 3 before firmware 3 is
# believed (0.3 s at 10 Hz).
FW3_CONFIRM_FRAMES = 3
# carState frames (100 Hz) without a valid SS_STATUS after which firmware-2 treatment returns (0.5 s =
# 5 missed 10 Hz frames). Nothing is kept across ignition cycles: every drive starts as firmware 2.
FW3_LOST_FRAMES = 50

# Initial lateral tune for the SSV3 path (stock-LKAS dashcam drive 000000f3--740a520643, report
# 2026-11-15-ssv3-initial-tune.md). The shared HONDA_ACCORD_9G entry in params.toml is the TI tune
# (TI_STEER_MAX 599 on a different actuator): its LAF 1.19 is at the top of the SSV3's plausible band and its
# FRICTION 0.31 is ~3x the SSV3's measured friction step. FRICTION is in normalized torque units (x240 counts).
# torqued learns from these (its +-30 % / +-50 % windows).
# 2026-11-16, after the first SSV3 openpilot-steered drive (report 2026-11-16-ssv3-first-drive.md): LAF 0.90 -> 1.6
# (open-loop refit 1.4-1.8, torqued raw 2.4-2.8 pinned at the old window edge; windows now LAF 1.12-2.08) and
# FRICTION 0.12 -> 0.15 (torqued raw 0.18-0.19; window 0.075-0.225).
# 2026-11-17 (reports 2026-11-16-ssv3-blend-on-vs-off.md, 2026-11-16-drive-ff-acedd8b.md): LAF 1.6 -> 1.9 (torqued
# filtered 1.80-1.93, raw 2.07-2.13; window now 1.33-2.47) and delay 0.20 -> 0.30 (lagd 0.45, blend probe ~0.50 s).
# FRICTION 0.15 kept (torqued 0.147-0.156).
SSV3_LAT_ACCEL_FACTOR = 1.9
SSV3_FRICTION = 0.15
# Gives lagd an initial total of 0.50 s (+0.2 s), the lag measured on the SSV3 drives.
SSV3_STEER_ACTUATOR_DELAY = 0.30


def apply_ssv3_lateral_tune(cp) -> None:
  """Startup only (torque_interceptor.apply_torque_interceptor, non-TI branch): the SSV3 path's lateral tune.
  Never called on the TI path, which keeps the shared params.toml tune."""
  if cp.carFingerprint != CAR.HONDA_ACCORD_9G or cp.lateralTuning.which() != 'torque':
    return
  cp.lateralTuning.torque.latAccelFactor = SSV3_LAT_ACCEL_FACTOR
  cp.lateralTuning.torque.friction = SSV3_FRICTION
  cp.steerActuatorDelay = SSV3_STEER_ACTUATOR_DELAY


def restore_shared_lateral_tune(cp) -> None:
  """TI branch: put back the shared params.toml LAF/FRICTION in case this CarParams went through the SSV3
  branch first (a no-op on a fresh CarParams, so the TI tune is unchanged)."""
  if cp.carFingerprint != CAR.HONDA_ACCORD_9G or cp.lateralTuning.which() != 'torque':
    return
  from opendbc.car.interfaces import get_torque_params
  shared = get_torque_params()[cp.carFingerprint]
  cp.lateralTuning.torque.latAccelFactor = shared['LAT_ACCEL_FACTOR']
  cp.lateralTuning.torque.friction = shared['FRICTION']


def ssv3_steer_command(raw: float, lat_active: bool, last_nonzero: int) -> int:
  """0xE4 STEER_TORQUE for the SSV3 path from the unrounded lookup output `raw` (counts).

  Rounded to the nearest count (the shared Honda path truncates toward zero, which sends 0 for every
  |raw| < 1). While openpilot steers, an exact 0 is replaced by +-1: the board's steer-request decision is
  `request && (torque != 0 || ZERO_TORQUE_KEEPS_LKAS_ON)` (bridge.cpp, ZERO_TORQUE_SENDS_OFF = 1 on firmware
  2 and 3), so a 0 makes it send LKAS-off and restart the 50 ms lead-in plus the ~120 ms EPS ack. Sign: the
  unrounded command, else the last non-zero command sent, else +1. The board dithers a held v
  between v and v - sign(v) (toward zero; it clamps at 240): +1 -> 1/0, -1 -> -1/0, 240 -> 240/239, so it
  never crosses zero. Not lat_active: unchanged
  (rounded; the controller sends 0 there anyway)."""
  cmd = int(round(raw))
  if lat_active and cmd == 0:
    if raw > 0:
      cmd = 1
    elif raw < 0:
      cmd = -1
    else:
      cmd = -1 if last_nonzero < 0 else 1
  return cmd


class Ssv3Option:
  # 0xE4 byte 2 bit masks (DBC bits 16-19, _steering_control_d_ssv3.dbc)
  TORQUE_BLEND_DISABLE = 0x01
  TX_ALL_LKAS_DATA = 0x02
  LSB_TOGGLE_DISABLE = 0x04
  ZERO_TORQUE_KEEPS_LKAS_ON = 0x08
  ALL = 0x0F
  # TX_ALL_LKAS_DATA is never sent (firmware agent, 2026-11-14): firmware 3 transmits 523/524 regardless,
  # and on firmware 2 bit 17 silently drops frame 520. The param stays, but the bit never reaches the wire.
  SENDABLE = ALL & ~TX_ALL_LKAS_DATA


def ssv3_qualified(CP) -> bool:
  """A controllable 9G Accord on the Nidec safety model, i.e. the upstream SSV3 steering path."""
  configs = list(CP.safetyConfigs)
  return bool(CP.carFingerprint == CAR.HONDA_ACCORD_9G and not CP.passive and not CP.dashcamOnly and
              not CP.notCar and len(configs) == 1 and
              configs[0].safetyModel == structs.CarParams.SafetyModel.hondaNidec)


class Ssv3Parser(CANParser):
  """Advisory parser for SSV3 frames that firmware 2 / board-less cars may not send (or send oddly).
  Its messages never make carState invalid or timed out: the frames are information, not inputs."""

  @property
  def can_valid(self) -> bool:
    return True

  @property
  def bus_timeout(self) -> bool:
    return False


# Bus key for the advisory parser in CarState.get_can_parsers; Honda uses no other Bus.alt parser.
SSV3_PARSER_BUS = Bus.alt


def ssv3_can_parser(CP, dbc_name):
  return Ssv3Parser(dbc_name, [("SS_STATUS", math.nan), ("STEER_MOTOR_TORQUE", math.nan), ("EPS_RAW", math.nan)],
                    CanBus(CP).pt)


def signed_motor_torque(raw: float) -> int:
  # 427 MOTOR_TORQUE: 10-bit field, unsigned in _honda_common.dbc, two's complement on firmware 3
  v = int(raw) & 0x3FF
  return v - 0x400 if v & 0x200 else v


class Ssv3CarState:
  def __init__(self):
    self.version = 0            # last VERSION_NUM seen, 0 = no 520 yet (treated as firmware 2)
    self.hardware_rev = 0
    self.fw3 = False            # latched once FW3_CONFIRM_FRAMES consecutive frames say >= 3
    self.fw3_count = 0
    self.eps_lkas_ack = False
    self.camera_fault = False
    self.motor_torque = 0
    self.lkas_blocked = False   # SS_STATUS.LKAS_ALLOWED (inverted sense: 1 = board cannot steer)
    self.frames_since_520 = 0
    self.steer_status = 0       # raw 400 STEER_STATUS (EPS status bits), every firmware; blend probe abort input
    # Wind-up guard inputs (firmware 3 only; Ssv3WindupGuard). Defaults = "steering applied".
    self.board_mode = BOARD_MODE_STEER   # 524 MODE, last valid frame
    self.board_request = False           # 524 STEER_REQUEST: the board sees our request bit
    self.frames_since_524 = 0
    self.lin_fatal = False               # 400 LIN_INTERFACE_FATAL_ERROR: set on the frame after an EPS serial gap
    self.frames_without_400 = 0          # carState updates in a row with no new 400 (EPS serial frame) at all

  def _drop_to_fw2(self):
    # SS_STATUS stopped (or reported < 3): firmware-2 treatment, no options, no fw3 fields
    self.fw3 = False
    self.fw3_count = 0
    self.eps_lkas_ack = False
    self.camera_fault = False
    self.motor_torque = 0
    self.board_mode = BOARD_MODE_STEER
    self.board_request = False
    self.lin_fatal = False

  def update(self, cp_ssv3, cp_pt, ret: structs.CarState) -> None:
    # vl_all only holds this update's checksum/counter-valid frames; vl keeps stale/default values.
    versions = cp_ssv3.vl_all["SS_STATUS"]["VERSION_NUM"]
    if versions:
      self.frames_since_520 = 0
    else:
      self.frames_since_520 += 1
      if self.frames_since_520 > FW3_LOST_FRAMES and self.fw3:
        self._drop_to_fw2()
    for v in versions:
      self.version = int(v)
      self.fw3_count = self.fw3_count + 1 if self.version >= FW3 else 0
      if self.fw3_count >= FW3_CONFIRM_FRAMES:
        self.fw3 = True
      elif self.version < FW3 and self.fw3:
        self._drop_to_fw2()
    if versions:
      self.hardware_rev = int(cp_ssv3.vl["SS_STATUS"]["HARDWARE_REV"])
      self.lkas_blocked = bool(cp_ssv3.vl["SS_STATUS"]["LKAS_ALLOWED"])
    self.steer_status = int(cp_pt.vl["STEER_STATUS"]["STEER_STATUS"])
    # 400/427/524 are all emitted per EPS serial frame (100 Hz): none in this update = the EPS is not talking
    self.frames_without_400 = 0 if cp_pt.vl_all["STEER_STATUS"]["STEER_STATUS"] else self.frames_without_400 + 1
    if cp_ssv3.vl_all["EPS_RAW"]["MODE"]:
      self.frames_since_524 = 0
    else:
      self.frames_since_524 += 1

    if not self.fw3:
      return
    if self.frames_since_524 == 0:
      self.board_mode = int(cp_ssv3.vl["EPS_RAW"]["MODE"])
      self.board_request = bool(cp_ssv3.vl["EPS_RAW"]["STEER_REQUEST"])
    elif self.frames_since_524 > EPS_RAW_STALE_FRAMES:
      # 524 stopped (not sent by this board build): mode unknown, never treated as a cut
      self.board_mode, self.board_request = BOARD_MODE_STEER, False
    self.lin_fatal = bool(cp_pt.vl["STEER_STATUS"]["LIN_INTERFACE_FATAL_ERROR"])
    self.eps_lkas_ack = bool(cp_pt.vl["STEER_STATUS"]["EPS_LKAS_ACK"])
    self.camera_fault = bool(cp_pt.vl["STEER_STATUS"]["CAMERA_FAULT"])
    self.motor_torque = signed_motor_torque(cp_ssv3.vl["STEER_MOTOR_TORQUE"]["MOTOR_TORQUE"])
    ret.steeringTorqueEps = float(self.motor_torque)


# ---- Wind-up guard (report 2026-11-17-ssv3-windup-fix.md) ----
#
# openpilot cannot see when the SSV3/EPS stops applying our torque, so the controller kept winding 0xE4 up to +-240
# into a board that had cut LKAS (524 MODE IDLE at |driver| ~90) or an EPS that had stopped acking (below ~3 mph),
# and the board then stepped that stale command back in on release. While a cut is seen, the command (the car
# controller's rate-limited torque, CarControl.actuatorsOutput.torque) is capped:
#   BOARD_IDLE  524 MODE != STEER while 524 STEER_REQUEST = 1, and for BOARD_LEAD_IN_FRAMES after the board is back in
#               STEER: the board has sent LKAS-off and then sends its 5-frame zero lead-in, so nothing of ours is
#               applied -> cap 0. At the 84-90 count hysteresis edge the board flips IDLE/STEER every few frames
#               with the ack still up; the latch keeps the command down through that chatter.
#   EPS_NO_ACK  400 EPS_LKAS_ACK = 0 for ACK_DEBOUNCE_FRAMES: the EPS says it is not applying LKAS -> cap 0.
#               Both cap-0 cuts drop the command to the +-1 keep-alive at once (invisible: nothing is applied), and
#               the ramp-in on release starts from 0, where the EPS actually is.
#   LIN_FATAL / SERIAL_GAP  400 LIN_INTERFACE_FATAL_ERROR, or no EPS frame for SERIAL_GAP_FRAMES: the EPS serial
#               link dropped; whether the EPS is still applying is unknown (2/11 gaps came back acked, and a
#               gap ride-through firmware keeps steering) -> hold: no growth, no step. If the board then goes IDLE or
#               the ack drops, the cap-0 rules take over.
# The smallest cap wins. Release: the cap goes away on the first clean frame and the normal STEER_DELTA_UP rate
# limit (7.2 counts per frame, 0.33 s to full) ramps back from the capped value. Because actuatorsOutput.torque
# then differs from actuators.torque, controlsd's existing steer_limited_by_safety freezes the torque controller's
# integrator and skips the saturation timer, so no controlsd change and no alert. Firmware 3 only, latActive only,
# never during a blend-probe window, never on the TI path (Ssv3Controller does not exist there). A newer board
# firmware that ramps its own release only meets a command that is already ramping from 0.
BOARD_MODE_STEER = 2
EPS_RAW_STALE_FRAMES = 50       # 524 missing this long -> mode unknown (not a cut)
ACK_DEBOUNCE_FRAMES = 2
BOARD_LEAD_IN_FRAMES = 5        # firmware 2/3 send zero for 5 frames after IDLE -> STEER (bridge.cpp lead-in)
SERIAL_GAP_FRAMES = 4           # >= 40 ms with no EPS frame (gaps are 60-70 ms; normal batching gives 0-1)


class Ssv3Cut:
  NONE = 0
  BOARD_IDLE = 1
  EPS_NO_ACK = 2
  LIN_FATAL = 4
  SERIAL_GAP = 8


class Ssv3WindupGuard:
  def __init__(self):
    self.reason = Ssv3Cut.NONE     # this frame's cut reasons (bit mask), logged in starpilotCarState.ssv3
    self.no_ack_frames = 0
    self.steer_frames = BOARD_LEAD_IN_FRAMES   # board frames in STEER since its last IDLE-with-request
    self.cut_frames = 0             # consecutive frames with any cut

  def update(self, ssv3, lat_active: bool) -> int:
    if ssv3 is None or not ssv3.fw3 or not lat_active:
      self.__init__()
      return self.reason
    self.no_ack_frames = 0 if ssv3.eps_lkas_ack else self.no_ack_frames + 1
    idle = ssv3.board_request and ssv3.board_mode != BOARD_MODE_STEER
    self.steer_frames = 0 if idle else min(self.steer_frames + 1, BOARD_LEAD_IN_FRAMES)
    reason = Ssv3Cut.NONE
    if self.steer_frames < BOARD_LEAD_IN_FRAMES:
      reason |= Ssv3Cut.BOARD_IDLE
    if self.no_ack_frames >= ACK_DEBOUNCE_FRAMES:
      reason |= Ssv3Cut.EPS_NO_ACK
    if ssv3.lin_fatal:
      reason |= Ssv3Cut.LIN_FATAL
    if ssv3.frames_without_400 >= SERIAL_GAP_FRAMES:
      reason |= Ssv3Cut.SERIAL_GAP
    self.reason = reason
    self.cut_frames = self.cut_frames + 1 if reason else 0
    return reason

  def limit(self, torque: float, last_torque: float) -> float:
    """Caps this frame's rate-limited normalized torque given last frame's output (both openpilot sign)."""
    if not self.reason:
      return torque
    cap = abs(last_torque)          # any cut: no growth (LIN_FATAL / SERIAL_GAP: hold)
    if self.reason & (Ssv3Cut.BOARD_IDLE | Ssv3Cut.EPS_NO_ACK):
      cap = 0.0
    return max(-cap, min(cap, torque))


# ---- EPS deadband compensation (developer A/B, SSV3DeadbandComp, default off) ----
# The EPS gives ~0 motor torque for |0xE4| <= ~20 counts (report 2026-11-17-ssv3-raw-vs-can.md). When on, a
# sign-following offset of DEADBAND_COMP_COUNTS is added to the wire command, faded in over the first
# DEADBAND_FADE_COUNTS so the command stays continuous through zero. Applied to the wire value only (the
# controller's actuatorsOutput.torque is unchanged), only while steering is applied (no cut).
DEADBAND_COMP_COUNTS = 20.0
DEADBAND_FADE_COUNTS = 20.0


def deadband_compensate(raw: float, steer_max: float) -> float:
  if raw == 0.0:
    return raw
  out = raw + math.copysign(DEADBAND_COMP_COUNTS * min(1.0, abs(raw) / DEADBAND_FADE_COUNTS), raw)
  return max(-steer_max, min(steer_max, out))


class Ssv3Controller:
  """0xE4 option bits. requested_options is set by the openpilot side (developer params); it only
  reaches the wire once firmware 3 has been confirmed for this drive."""

  def __init__(self):
    self.requested_options = 0
    # Developer-only EPS torque-blend probe (SSV3BlendProbe, default 0 = off), set by the openpilot side.
    self.requested_probe = 0
    self.probe = Ssv3BlendProbe()
    self.guard = Ssv3WindupGuard()
    # SSV3DeadbandComp (default off), set by the openpilot side; firmware 3 only.
    self.requested_deadband_comp = False

  def deadband_comp(self, CS) -> bool:
    ssv3 = getattr(CS, "ssv3", None)
    return bool(self.requested_deadband_comp and ssv3 is not None and ssv3.fw3)

  def options(self, CS) -> int:
    ssv3 = getattr(CS, "ssv3", None)
    if ssv3 is None or not ssv3.fw3:
      return 0
    return int(self.requested_options) & Ssv3Option.SENDABLE

  def apply(self, can_sends, CS, lkas_bus: int) -> None:
    """Sets the option bits in this frame's 0xE4 (byte 2 low nibble) and redoes the Honda checksum.
    With no options (always on firmware 2) the frame is left exactly as the packer built it."""
    options = self.options(CS)
    if not options:
      return
    for i, (addr, dat, bus) in enumerate(can_sends):
      if addr == STEERING_CONTROL_ADDR and bus == lkas_bus and len(dat) == 5:
        can_sends[i] = (addr, set_steering_options(dat, options), bus)


# ---- EPS torque-blend probe (developer only; report 2026-11-15-ssv3-blend-test.md) ----
#
# While SSV3BlendProbe != 0 and every start condition has held for PROBE_ARM_SETTLE_S, openpilot's steer torque
# is replaced by a FIXED 0xE4 command for PROBE_HOLD_S per window, with >= PROBE_REST_S of normal control between
# windows. The driver holds the wheel and slowly ramps their own torque against / with it; the logs then show how
# the EPS blends the two. The override is applied before the normal STEER_DELTA rate limit and the SSV3 command
# shaping, so it changes the torque value only. Any abort condition ends the probe at once (normal control, rate
# limited) and the openpilot side clears the param. Never on the TI path (Ssv3Controller exists only on the SSV3
# path). TORQUE_BLEND_DISABLE is not touched here: it stays SSV3TorqueBlendDisable's (firmware 3 only).

# Programs: 0xE4 STEER_TORQUE wire counts per window (positive = torque to the RIGHT, as the stock camera sends).
PROBE_PROGRAMS = {
  1: (60, -60, 120),
  2: (-60, 60, -120),
  3: (60,),
  4: (-60,),
  5: (120,),
  6: (-120,),
  7: (120, -120, 180, -180, 240),   # highway-band program: up to the full SSV3 range, 70 s
}
PROBE_MAX_COUNTS = 240          # |command| never above this (the full SSV3 range), whatever the table says
PROBE_HOLD_S = 10.0             # one fixed-command window
PROBE_REST_S = 5.0              # normal openpilot control between windows
PROBE_TOTAL_S = 90.0            # hard limit from the first window's start
PROBE_ARM_SETTLE_S = 2.0        # start conditions must hold this long before the first window
PROBE_ARM_TIMEOUT_S = 120.0     # armed but never started -> give up and clear the param
MPH = 0.44704
PROBE_V_MIN = 10.0 * MPH        # abort outside [V_MIN, V_MAX]
PROBE_V_MAX = 52.0 * MPH
PROBE_START_V_MIN = 11.0 * MPH  # start only inside a narrower band, so a start never sits on an abort edge
PROBE_START_V_MAX = 50.0 * MPH
PROBE_START_ANGLE_DEG = 30.0    # |steering angle| to start
PROBE_ABORT_ANGLE_DEG = 45.0
PROBE_START_YAW = 0.05          # rad/s (calibrated yaw rate, CarControl.angularVelocity[2])
PROBE_ABORT_YAW = 0.25          # absolute yaw-rate ceiling (~14 deg/s; ~1.1 m/s^2 at 10 mph)
PROBE_ABORT_LAT_ACCEL = 1.5     # m/s^2, |yaw rate * vEgo|: the speed-aware limit (0.075 rad/s at 45 mph)
PROBE_DT = 0.01                 # CarController.update runs at 100 Hz


class ProbeState:
  IDLE = 0
  ARMED = 1
  HOLD = 2
  REST = 3
  DONE = 4


class ProbeEnd:
  NONE = 0
  COMPLETED = 1
  LAT_INACTIVE = 2
  BRAKE = 3
  GAS = 4
  CANCEL = 5
  SPEED = 6
  ANGLE = 7
  YAW = 8
  EPS_FAULT = 9
  TIME_LIMIT = 10
  BOARD_LOST = 11
  ARM_TIMEOUT = 12
  BAD_PROGRAM = 13
  STOPPED = 14     # param set back to 0 while running


PROBE_END_NAMES = {v: k.lower() for k, v in vars(ProbeEnd).items() if not k.startswith('_')}


class ProbeInputs:
  __slots__ = ('lat_active', 'cancel', 'v_ego', 'angle_deg', 'yaw', 'brake', 'gas', 'steer_fault', 'steer_status', 'fw3')

  def __init__(self, *, lat_active=False, cancel=False, v_ego=0.0, angle_deg=0.0, yaw=math.nan, brake=False, gas=False,
               steer_fault=False, steer_status=0, fw3=False):
    self.lat_active, self.cancel, self.v_ego, self.angle_deg, self.yaw = lat_active, cancel, v_ego, angle_deg, yaw
    self.brake, self.gas, self.steer_fault, self.steer_status, self.fw3 = brake, gas, steer_fault, steer_status, fw3

  @classmethod
  def from_car(cls, CC, CS):
    out = CS.out
    av = list(CC.angularVelocity)
    ssv3 = getattr(CS, 'ssv3', None)
    # CC.cruiseControl.cancel is openpilot's own PCM command (controlsd: cruiseState.enabled and not CC.enabled), asserted
    # continuously in always-on-lateral. A driver cancel is a CANCEL/MAIN press seen in CarState.buttonEvents.
    cancel = any(b.pressed and b.type in (ButtonType.cancel, ButtonType.mainCruise) for b in (out.buttonEvents or []))
    return cls(lat_active=bool(CC.latActive), cancel=cancel, v_ego=float(out.vEgo),
               angle_deg=float(out.steeringAngleDeg), yaw=float(av[2]) if len(av) >= 3 else math.nan,
               brake=bool(out.brakePressed), gas=bool(out.gasPressed),
               steer_fault=bool(out.steerFaultTemporary or out.steerFaultPermanent),
               steer_status=int(ssv3.steer_status) if ssv3 is not None else -1,
               fw3=bool(ssv3 is not None and ssv3.fw3))


def probe_abort_reason(i: ProbeInputs) -> int:
  """Running-state abort check (every frame, in priority order). Missing/NaN inputs abort."""
  if not i.lat_active:
    return ProbeEnd.LAT_INACTIVE
  if i.brake:
    return ProbeEnd.BRAKE
  if i.gas:
    return ProbeEnd.GAS
  if i.cancel:
    return ProbeEnd.CANCEL
  if not (PROBE_V_MIN <= i.v_ego <= PROBE_V_MAX):        # NaN fails too
    return ProbeEnd.SPEED
  if not abs(i.angle_deg) <= PROBE_ABORT_ANGLE_DEG:
    return ProbeEnd.ANGLE
  if not (abs(i.yaw) <= PROBE_ABORT_YAW and abs(i.yaw) * i.v_ego <= PROBE_ABORT_LAT_ACCEL):   # NaN fails
    return ProbeEnd.YAW
  if i.steer_fault or i.steer_status != 0:
    return ProbeEnd.EPS_FAULT
  if not i.fw3:
    return ProbeEnd.BOARD_LOST
  return ProbeEnd.NONE


def probe_start_ok(i: ProbeInputs) -> bool:
  return (probe_abort_reason(i) == ProbeEnd.NONE and PROBE_START_V_MIN <= i.v_ego <= PROBE_START_V_MAX and
          abs(i.angle_deg) < PROBE_START_ANGLE_DEG and abs(i.yaw) < PROBE_START_YAW)


class Ssv3BlendProbe:
  """State machine; update() returns the normalized torque override (openpilot sign) or None for normal control."""

  def __init__(self):
    self.state = ProbeState.IDLE
    self.end = ProbeEnd.NONE
    self.program = 0
    self.window = -1           # index into the program while HOLD/REST
    self.command = 0           # wire counts of the current HOLD window, else 0
    self.timer = 0             # frames in the current state
    self.total = 0             # frames since the first window started
    self.settle = 0            # consecutive frames with start conditions met (ARMED)

  @property
  def active(self) -> bool:
    return self.state in (ProbeState.HOLD, ProbeState.REST)

  @property
  def finished(self) -> bool:
    """Ended (completed or aborted): the openpilot side should clear SSV3BlendProbe."""
    return self.state == ProbeState.DONE

  def _finish(self, reason: int) -> None:
    self.state, self.end, self.command, self.timer = ProbeState.DONE, reason, 0, 0

  def update(self, program: int, inputs: ProbeInputs, steer_max: float):
    program = int(program or 0)
    if self.state == ProbeState.DONE:
      if program == 0:          # latched until the param reads 0 again: a stale value can never re-arm it
        self.__init__()
      return None
    if program == 0:
      if self.active:
        self._finish(ProbeEnd.STOPPED)
        return None
      self.__init__()
      return None

    if self.state == ProbeState.IDLE:
      if program not in PROBE_PROGRAMS:
        self.program = program
        self._finish(ProbeEnd.BAD_PROGRAM)
        return None
      self.state, self.program, self.timer, self.settle = ProbeState.ARMED, program, 0, 0

    if self.state == ProbeState.ARMED:
      self.timer += 1
      self.settle = self.settle + 1 if probe_start_ok(inputs) else 0
      if self.settle >= round(PROBE_ARM_SETTLE_S / PROBE_DT):
        self.state, self.window, self.timer, self.total = ProbeState.HOLD, 0, 0, 0
      elif self.timer >= round(PROBE_ARM_TIMEOUT_S / PROBE_DT):
        self._finish(ProbeEnd.ARM_TIMEOUT)
        return None
      else:
        return None

    # HOLD / REST
    reason = probe_abort_reason(inputs)
    if reason == ProbeEnd.NONE and self.total >= round(PROBE_TOTAL_S / PROBE_DT):
      reason = ProbeEnd.TIME_LIMIT
    if reason != ProbeEnd.NONE:
      self._finish(reason)
      return None
    self.total += 1
    self.timer += 1
    windows = PROBE_PROGRAMS[self.program]
    if self.state == ProbeState.HOLD and self.timer > round(PROBE_HOLD_S / PROBE_DT):
      if self.window + 1 >= len(windows):
        self._finish(ProbeEnd.COMPLETED)
        return None
      self.state, self.timer, self.command = ProbeState.REST, 1, 0
    elif self.state == ProbeState.REST and self.timer > round(PROBE_REST_S / PROBE_DT):
      self.state, self.timer, self.window = ProbeState.HOLD, 1, self.window + 1
    if self.state == ProbeState.REST:
      return None
    counts = max(-PROBE_MAX_COUNTS, min(PROBE_MAX_COUNTS, int(windows[self.window])))
    self.command = counts
    # 0xE4 wire = -torque * STEER_MAX (CarController: interp(-limited_torque * STEER_MAX, ...))
    return -counts / float(steer_max)


def set_steering_options(dat: bytes, options: int) -> bytes:
  d = bytearray(dat)
  d[2] = (d[2] & 0xF0) | (options & Ssv3Option.ALL)
  d[4] = (d[4] & 0xF0) | honda_checksum(STEERING_CONTROL_ADDR, None, d)
  return bytes(d)
