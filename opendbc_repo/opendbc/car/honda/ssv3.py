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

Firmware-2 boards (and boards with no 520 at all) see exactly what upstream sends: the 0xE4 bytes are
untouched unless firmware 3 was seen AND an option was requested, and the extra frames are read by a
separate advisory parser whose validity never reaches carState.canValid / canTimeout.
"""
import math

from opendbc.can import CANParser
from opendbc.car import Bus, structs
from opendbc.car.honda.hondacan import CanBus, honda_checksum
from opendbc.car.honda.values import CAR

STEERING_CONTROL_ADDR = 0xE4
SS_STATUS_ADDR = 520
FW3 = 3
# Consecutive checksum/counter-valid SS_STATUS frames with VERSION_NUM >= 3 before firmware 3 is
# believed (0.3 s at 10 Hz). Latched for the drive: the board can only be reflashed offroad.
FW3_CONFIRM_FRAMES = 3


class Ssv3Option:
  # 0xE4 byte 2 bit masks (DBC bits 16-19, _steering_control_d_ssv3.dbc)
  TORQUE_BLEND_DISABLE = 0x01
  TX_ALL_LKAS_DATA = 0x02
  LSB_TOGGLE_DISABLE = 0x04
  ZERO_TORQUE_KEEPS_LKAS_ON = 0x08
  ALL = 0x0F


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
  return Ssv3Parser(dbc_name, [("SS_STATUS", math.nan), ("STEER_MOTOR_TORQUE", math.nan)], CanBus(CP).pt)


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

  def update(self, cp_ssv3, cp_pt, ret: structs.CarState) -> None:
    # vl_all only holds this update's checksum/counter-valid frames; vl keeps stale/default values.
    versions = cp_ssv3.vl_all["SS_STATUS"]["VERSION_NUM"]
    for v in versions:
      self.version = int(v)
      self.fw3_count = self.fw3_count + 1 if self.version >= FW3 else 0
      if self.fw3_count >= FW3_CONFIRM_FRAMES:
        self.fw3 = True
    if versions:
      self.hardware_rev = int(cp_ssv3.vl["SS_STATUS"]["HARDWARE_REV"])
      self.lkas_blocked = bool(cp_ssv3.vl["SS_STATUS"]["LKAS_ALLOWED"])

    if not self.fw3:
      return
    self.eps_lkas_ack = bool(cp_pt.vl["STEER_STATUS"]["EPS_LKAS_ACK"])
    self.camera_fault = bool(cp_pt.vl["STEER_STATUS"]["CAMERA_FAULT"])
    self.motor_torque = signed_motor_torque(cp_ssv3.vl["STEER_MOTOR_TORQUE"]["MOTOR_TORQUE"])
    ret.steeringTorqueEps = float(self.motor_torque)


class Ssv3Controller:
  """0xE4 option bits. requested_options is set by the openpilot side (developer params); it only
  reaches the wire once firmware 3 has been confirmed for this drive."""

  def __init__(self):
    self.requested_options = 0

  def options(self, CS) -> int:
    ssv3 = getattr(CS, "ssv3", None)
    if ssv3 is None or not ssv3.fw3:
      return 0
    return int(self.requested_options) & Ssv3Option.ALL

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
