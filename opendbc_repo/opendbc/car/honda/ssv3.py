"""SSV3 serial-steering board, firmware 3 additions (2016-17 Accord, HONDA_ACCORD_9G).

The board sits on the camera <-> EPS serial link, takes 0xE4 STEERING_CONTROL from openpilot on the
powertrain bus and reports STEER_STATUS (400), STEER_MOTOR_TORQUE (427) and SS_STATUS (520) there.
Firmware 3 adds signals in bits firmware 2 sends differently, so everything here is gated on
SS_STATUS.VERSION_NUM >= 3:

  * 400 bit 39 is EPS_LKAS_ACK on firmware 3 but firmware 2's steer-blended flag; bit 38 CAMERA_FAULT.
  * 427 MOTOR_TORQUE is two's-complement on firmware 3 (sign-magnitude-ish on firmware 2). The shared
    _honda_common.dbc declares it unsigned for every Honda and is left alone; it is re-signed here.
    Despite the DBC name, 427 is NOT the EPS motor output (report 2026-11-22-eps-0x421-0x18e.md: r=0.29
    against 0x18E MOTOR_OUTPUT_MAG, and at standstill it follows driver torque). It is reported as-is in
    carState.steeringTorqueEps / ssv3.motorTorque for continuity; the real motor readout is 0x18E. No
    control path (wind-up guard included) reads it.
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
  # TX_ALL_LKAS_DATA is never sent: firmware 3 transmits 523/524 regardless, and on firmware 2 bit 17
  # silently drops frame 520. There is no param for it; the mask only keeps the bit off the wire.
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
  return Ssv3Parser(dbc_name, [("SS_STATUS", math.nan), ("STEER_MOTOR_TORQUE", math.nan), ("EPS_RAW", math.nan),
                               ("BLEND_STATE", math.nan)], CanBus(CP).pt)


def signed_motor_torque(raw: float) -> int:
  # 427 MOTOR_TORQUE (DBC name; not the EPS motor output, see the module docstring): 10-bit field,
  # unsigned in _honda_common.dbc, two's complement on firmware 3
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
    self.steer_status = 0       # raw 400 STEER_STATUS (EPS status bits), every firmware
    # Wind-up guard inputs (firmware 3 only; Ssv3WindupGuard). Defaults = "steering applied".
    self.board_mode = BOARD_MODE_STEER   # 524 MODE, last valid frame
    self.board_request = False           # 524 STEER_REQUEST: the board sees our request bit
    self.frames_since_524 = 0
    self.lin_fatal = False               # 400 LIN_INTERFACE_FATAL_ERROR: set on the frame after an EPS serial gap
    self.frames_without_400 = 0          # carState updates in a row with no new 400 (EPS serial frame) at all
    # Board firmware build >= 4 (526 BLEND_STATE; Ssv3WindupGuard 526 rules). Defaults = "no 526" = build-3 rules.
    self.frames_since_526 = BLEND_STALE_FRAMES + 1
    self._blend_defaults()

  def _blend_defaults(self):
    self.blend_gain = BLEND_GAIN_FULL    # 526 BLEND_GAIN, last frame (255 = full LKAS)
    self.blend_rise_frames = 0           # consecutive 526 frames with a rising gain (the board's release ramp)
    self.eps_gap_active = False          # 526 EPS_GAP_ACTIVE: the board is riding through an EPS serial gap
    self.frames_since_eps_gap = BLEND_GAP_RECOVERY_FRAMES   # carState updates since EPS_GAP_ACTIVE was last seen
    self.steer_applied = 0               # 400 STEER_APPLIED (build >= 4: post-blend torque sent to the EPS)
    self.new_400 = False                 # a 400 frame arrived in this update

  @property
  def blend_state(self) -> bool:
    """526 BLEND_STATE is being received (board firmware build >= 4)."""
    return self.fw3 and self.frames_since_526 <= BLEND_STALE_FRAMES

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
    self._blend_defaults()

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
    gains = cp_ssv3.vl_all["BLEND_STATE"]["BLEND_GAIN"]
    self.frames_since_526 = 0 if gains else min(self.frames_since_526 + 1, BLEND_STALE_FRAMES + 1)

    if not self.fw3:
      return
    self._update_blend(cp_ssv3, cp_pt, gains)
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

  def _update_blend(self, cp_ssv3, cp_pt, gains) -> None:
    if not self.blend_state:
      # no 526 (build 3) or it stopped: none of the 526 rules apply
      self._blend_defaults()
      return
    gap_flags = cp_ssv3.vl_all["BLEND_STATE"]["EPS_GAP_ACTIVE"]
    for g in gains:
      g = int(g)
      self.blend_rise_frames = self.blend_rise_frames + 1 if g > self.blend_gain else 0
      self.blend_gain = g
    if gains:
      self.eps_gap_active = bool(gap_flags[-1])
    if any(gap_flags):
      self.frames_since_eps_gap = 0
    else:
      self.frames_since_eps_gap = min(self.frames_since_eps_gap + 1, BLEND_GAP_RECOVERY_FRAMES)
    self.new_400 = bool(cp_pt.vl_all["STEER_STATUS"]["STEER_APPLIED"])
    self.steer_applied = int(cp_pt.vl["STEER_STATUS"]["STEER_APPLIED"])


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
# never on the TI path (Ssv3Controller does not exist there). A newer board
# firmware that ramps its own release only meets a command that is already ramping from 0.
#
# Board firmware build 4 (report 2026-11-19-ssv3-guard-526.md; firmware report 2026-11-17-ssv3-fw-blend-v4.md) no
# longer drops to IDLE on a driver override: it stays in STEER and scales our command by its blend gain (cut from
# ~30 driver counts, total at ~45, released linearly over 0.5 s), and rides through EPS serial gaps up to 100 ms. So
# BOARD_IDLE no longer fires on an override. Build 4 sends 526 BLEND_STATE (100 Hz) and makes 400 STEER_APPLIED the
# torque actually sent; only while 526 is being received (Ssv3CarState.blend_state):
#   BOARD_BLEND    BLEND_GAIN <= BLEND_CUT_GAIN (cut >= 50 %) and the board is not releasing -> cap 0, as BOARD_IDLE.
#   BLEND_PARTIAL  BLEND_GAIN < BLEND_HOLD_GAIN (cut > 10 %) and not releasing -> hold (no growth): a light push keeps
#                  part of our torque applied, so no drop, but no wind-up either. Road bumps (<= ~7 % cuts) are below it.
#   APPLIED_LOW    a fresh 400 STEER_APPLIED below APPLIED_FRACTION of every one of our last APPLIED_WINDOW wire
#                  commands (all one sign, >= APPLIED_MIN_COUNTS), for APPLIED_DEBOUNCE frames -> cap 0. Catches a cut
#                  526 does not explain; the window covers the 1-2 frame board/EPS lag of a rising command. Once
#                  capped there is nothing to compare (+-1), so it is latched APPLIED_LATCH_FRAMES; then the ramp-in
#                  re-checks (while it stays unapplied the wire saws between +-1 and ~65 counts, none of it applied).
#   EPS_GAP_ACTIVE -> SERIAL_GAP (hold). During a ridden-through gap and for BLEND_GAP_RECOVERY_FRAMES after it, the
#                  board's own gap fade is not a driver cut: low gain only holds, and APPLIED_LOW is off.
# Releasing = the gain rose for BLEND_RELEASE_STREAK frames in a row (the board's 0.5 s release ramp): no blend cap,
# so our STEER_DELTA_UP ramp-in runs alongside the board's (applied = gain x command, both ramping from 0). Build 3
# (no 526, or 526 stale for BLEND_STALE_FRAMES) keeps exactly the rules above; BOARD_IDLE/EPS_NO_ACK/LIN_FATAL/
# SERIAL_GAP still apply on build 4 (faults > 100 ms, engage, low-speed refusal).
BOARD_MODE_STEER = 2
EPS_RAW_STALE_FRAMES = 50       # 524 missing this long -> mode unknown (not a cut)
ACK_DEBOUNCE_FRAMES = 2
BOARD_LEAD_IN_FRAMES = 5        # firmware 2/3 send zero for 5 frames after IDLE -> STEER (bridge.cpp lead-in)
SERIAL_GAP_FRAMES = 4           # >= 40 ms with no EPS frame (gaps are 60-70 ms; normal batching gives 0-1)
# build 4 (526 BLEND_STATE)
BLEND_GAIN_FULL = 255
BLEND_STALE_FRAMES = 10         # no 526 for 100 ms -> build-3 rules only
BLEND_CUT_GAIN = 127            # gain <= this (cut >= 50 %) -> not applied: cap 0
BLEND_HOLD_GAIN = 230           # gain below this (cut > 10 %) -> hold
BLEND_RELEASE_STREAK = 3        # gain rising this many 526 frames in a row = the board is releasing
BLEND_GAP_RECOVERY_FRAMES = 60  # after EPS_GAP_ACTIVE: the gap fade (to 100 ms) + 0.5 s release is not a driver cut
APPLIED_MIN_COUNTS = 30         # APPLIED_LOW only checks commands at least this big (wire counts)
APPLIED_FRACTION = 0.5
APPLIED_WINDOW = 4              # our last N wire commands (board + EPS lag 1-2 frames)
APPLIED_DEBOUNCE = 2
APPLIED_LATCH_FRAMES = 25      # APPLIED_LOW keeps the cap this long, then the ramp-in re-checks (nothing to compare at +-1)


class Ssv3Cut:
  NONE = 0
  BOARD_IDLE = 1
  EPS_NO_ACK = 2
  LIN_FATAL = 4
  SERIAL_GAP = 8
  BOARD_BLEND = 16      # build 4: 526 BLEND_GAIN cut >= 50 % -> cap 0
  BLEND_PARTIAL = 32    # build 4: 526 BLEND_GAIN cut > 10 % -> hold
  APPLIED_LOW = 64      # build 4: 400 STEER_APPLIED far below our command -> cap 0
  CAP_ZERO = BOARD_IDLE | EPS_NO_ACK | BOARD_BLEND | APPLIED_LOW


class Ssv3WindupGuard:
  def __init__(self):
    self.reason = Ssv3Cut.NONE     # this frame's cut reasons (bit mask), logged in starpilotCarState.ssv3
    self.no_ack_frames = 0
    self.steer_frames = BOARD_LEAD_IN_FRAMES   # board frames in STEER since its last IDLE-with-request
    self.cut_frames = 0             # consecutive frames with any cut
    self.sent = []                  # our last APPLIED_WINDOW wire commands (build-4 APPLIED_LOW)
    self.applied_low_frames = 0
    self.applied_low_latch = 0

  def note_sent(self, wire: int) -> None:
    """The 0xE4 STEER_TORQUE just built (car controller, SSV3 path, after this frame's update/limit)."""
    self.sent = (self.sent + [int(wire)])[-APPLIED_WINDOW:]

  def _blend_reason(self, ssv3) -> int:
    # build 4 only (526 being received); see the block comment above
    if not getattr(ssv3, "blend_state", False):
      self.applied_low_frames = self.applied_low_latch = 0
      return Ssv3Cut.NONE
    reason = Ssv3Cut.NONE
    gap_recent = ssv3.eps_gap_active or ssv3.frames_since_eps_gap < BLEND_GAP_RECOVERY_FRAMES
    releasing = ssv3.blend_rise_frames >= BLEND_RELEASE_STREAK
    if ssv3.eps_gap_active:
      reason |= Ssv3Cut.SERIAL_GAP
    if not releasing:
      if ssv3.blend_gain <= BLEND_CUT_GAIN and not gap_recent:
        reason |= Ssv3Cut.BOARD_BLEND
      elif ssv3.blend_gain < BLEND_HOLD_GAIN:
        reason |= Ssv3Cut.BLEND_PARTIAL
    if ssv3.new_400:
      low = False
      if len(self.sent) == APPLIED_WINDOW and not releasing and not gap_recent:
        sign = 1 if self.sent[-1] > 0 else -1
        if all(w * sign >= APPLIED_MIN_COUNTS for w in self.sent):
          ref = min(w * sign for w in self.sent)
          low = ssv3.steer_applied * sign < APPLIED_FRACTION * ref
      self.applied_low_frames = self.applied_low_frames + 1 if low else 0
    if self.applied_low_frames >= APPLIED_DEBOUNCE:
      self.applied_low_latch = APPLIED_LATCH_FRAMES
    if self.applied_low_latch > 0:
      self.applied_low_latch -= 1
      reason |= Ssv3Cut.APPLIED_LOW
    return reason

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
    reason |= self._blend_reason(ssv3)
    self.reason = reason
    self.cut_frames = self.cut_frames + 1 if reason else 0
    return reason

  def limit(self, torque: float, last_torque: float) -> float:
    """Caps this frame's rate-limited normalized torque given last frame's output (both openpilot sign)."""
    if not self.reason:
      return torque
    cap = abs(last_torque)          # any cut: no growth (LIN_FATAL / SERIAL_GAP: hold)
    if self.reason & Ssv3Cut.CAP_ZERO:
      cap = 0.0
    return max(-cap, min(cap, torque))


class Ssv3Controller:
  """0xE4 option bits. requested_options is set by the openpilot side (developer params); it only
  reaches the wire once firmware 3 has been confirmed for this drive."""

  def __init__(self):
    self.requested_options = 0
    self.guard = Ssv3WindupGuard()

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


def set_steering_options(dat: bytes, options: int) -> bytes:
  d = bytearray(dat)
  d[2] = (d[2] & 0xF0) | (options & Ssv3Option.ALL)
  d[4] = (d[4] & 0xF0) | honda_checksum(STEERING_CONTROL_ADDR, None, d)
  return bytes(d)
