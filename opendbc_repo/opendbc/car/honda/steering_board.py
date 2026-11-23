"""9G Accord steering board selection: Torque Interceptor (TI) or the SSV3 serial-steering board.

Mat's car carries both boards: the SSV3 (firmware 2 today) sits in the camera <-> EPS serial link and
reports STEER_STATUS 0x190 / SS_STATUS 0x208 on bus 0 from power-on, the TI is the steering board.
When the TI is removed the car should steer through the SSV3 instead of failing.

The TI can not be seen at startup: it is silent until openpilot sends it 0x249 (the TI_FEEDBACK 0x24A
in the 2026-10-26 rlog starts in the same 10 ms as our first 0x249). So the choice is made once per
drive, before CarParams exist (vehicle_preferences.prepare -> apply_torque_interceptor), from:

  TorqueInterceptorEnabled  the existing TI switch; off = SSV3 only, always (TI never commanded,
                            no TI safety bit), even when the TI is fitted and answering
  AccordSteeringBoard  "ti" / "ssv3" override (only with the TI switch on), anything else = auto
  TorqueInterceptorMissing  written by an earlier TI drive in which the TI never answered for
                            TI_MISSING_FRAMES while the SSV3 was reporting (TiPresence below)
  SSV3 frames in this start's CAN fingerprint (0x190 5 bytes or 0x208 3 bytes on bus 0)

TI switch on, auto: TI, unless TorqueInterceptorMissing is set AND the SSV3 is on the
bus; then the drive uses the standard 9G SSV3 path (TI safety bit cleared = upstream safety param).
A TI drive that never hears the TI raises steerFaultTemporary for the rest of that drive (nothing is
steering) and records TorqueInterceptorMissing, so the next start falls back. The car never switches
boards mid-drive. A TI drive that hears the TI clears the record (only possible with override "ti"
once a record exists, since auto then starts on the SSV3).

TI and SSV3 coexist on the bus: on the TI path 0xE4 goes out with zero torque, so the SSV3 holds the EPS
in LKAS-off and the TI is the only actuator.
"""
from opendbc.car.honda.torque_interceptor import TI_DISCOVERY_FRAMES

OVERRIDE_TI = "ti"
OVERRIDE_SSV3 = "ssv3"

# No TI_FEEDBACK at all for 10 s of TI handshake (TI_DISCOVERY_FRAMES is 5 s; the board answers the
# first zero-torque frame) while STEER_STATUS from the SSV3 kept arriving.
TI_MISSING_FRAMES = 2 * TI_DISCOVERY_FRAMES
SSV3_MIN_STATUS_FRAMES = TI_MISSING_FRAMES // 2

SSV3_FINGERPRINT = ((0x190, 5), (0x208, 3))   # STEER_STATUS, SS_STATUS on bus 0


def ssv3_present(fingerprints) -> bool:
  """SSV3 frames in the startup CAN fingerprint ({bus: {address: length}})."""
  if not isinstance(fingerprints, dict):
    return False
  bus0 = fingerprints.get(0) or {}
  return any(bus0.get(addr) == length for addr, length in SSV3_FINGERPRINT)


def select_ti(ti_enabled: bool, override, ti_missing: bool, ssv3_seen: bool) -> tuple[bool, str]:
  """(use TI this drive, reason). Pure; called once at startup."""
  override = override.decode() if isinstance(override, bytes) else (override or "")
  override = override.strip().lower()
  # TI switched off = SSV3 only, even with a working TI fitted and talking (Mat, 2026-11-13)
  if not ti_enabled:
    return False, "TorqueInterceptorEnabled off: SSV3 only"
  if override == OVERRIDE_TI:
    return True, "override ti"
  if override == OVERRIDE_SSV3:
    return False, "override ssv3"
  if ti_missing and ssv3_seen:
    return False, "TI missing on an earlier drive, SSV3 on the bus: SSV3 fallback"
  return True, "TorqueInterceptorEnabled"


class TiPresence:
  """TI drive: latches `missing` when TI_FEEDBACK never arrived for TI_MISSING_FRAMES carState frames
  while the SSV3's STEER_STATUS did (at least SSV3_MIN_STATUS_FRAMES of them). A late TI_FEEDBACK clears it."""

  def __init__(self):
    self.frames = 0
    self.status_frames = 0
    self.missing = False

  def update(self, feedback_seen: bool, steer_status_seen: bool) -> bool:
    if feedback_seen:
      self.missing = False
      return False
    if self.missing:
      return True
    self.frames += 1
    self.status_frames += int(bool(steer_status_seen))
    if self.frames >= TI_MISSING_FRAMES and self.status_frames >= SSV3_MIN_STATUS_FRAMES:
      self.missing = True
    return self.missing
