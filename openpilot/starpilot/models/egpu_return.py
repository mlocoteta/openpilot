"""Accord F16: give modeld the Chestnut again after it re-enumerates mid-drive.

modeld picks Chestnut vs Small once per process. After a USB-C flap the Chestnut
comes back as a new USB device a few seconds later, but the drive keeps running
Small (the startup-exit or stall path latches small_only for that drive_id), and
on the TI Accord Small lags enough that openpilot can't engage.

This owner only decides; ModeldProcess does the restart. It never touches GPU
state and only acts when openpilot is neither engaged nor steering.
"""
from dataclasses import dataclass
from pathlib import Path

from openpilot.common.hardware.usb import CHESTNUT_USB_PRODUCT, USB_DEVICES_PATH, is_chestnut_usb_id

STABLE_NS = 10_000_000_000        # Chestnut on USB with the same enumeration this long
SAFE_NS = 3_000_000_000           # not engaged / not steering this long
MIN_INTERVAL_NS = 180_000_000_000  # at most one restart per 3 min
MAX_ATTEMPTS = 3                  # per drive
STOP_GRACE_NS = 2_000_000_000     # SIGINT, then SIGKILL, then give up for this drive
DISABLE_FILE = Path('/data/egpu_auto_recover_disabled')


def chestnut_usb_identity(root: Path = USB_DEVICES_PATH) -> tuple[str, int, int] | None:
  """(sysfs name, busnum, devnum) of the enumerated Chestnut; devnum changes on every re-enumeration."""
  for d in sorted(root.glob('*')):
    try:
      if (is_chestnut_usb_id(int((d / 'idVendor').read_text(), 16), int((d / 'idProduct').read_text(), 16)) and
          (d / 'product').read_text().strip() == CHESTNUT_USB_PRODUCT):
        return d.name, int((d / 'busnum').read_text()), int((d / 'devnum').read_text())
    except (OSError, ValueError):
      pass
  return None


@dataclass
class EgpuReturn:
  drive_id: int = 0
  attempts: int = 0
  last_attempt_ns: int = 0
  used: tuple | None = None      # enumeration the last Chestnut-capable modeld launch saw (may have touched)
  seen: tuple | None = None
  seen_since_ns: int = 0
  safe_since_ns: int = 0

  def launched(self, chestnut, small_only: bool) -> None:
    if not small_only:
      self.used = chestnut

  def step(self, now_ns: int, drive_id: int, running_small: bool, chestnut, safe: bool, big_selected) -> bool:
    """True = restart modeld now, without the small_only latch. big_selected is a callable, read last."""
    if drive_id <= 0:
      self.drive_id = self.attempts = self.last_attempt_ns = 0
      return False
    if drive_id != self.drive_id:
      self.drive_id, self.attempts, self.last_attempt_ns = drive_id, 0, 0
    if chestnut != self.seen:
      self.seen, self.seen_since_ns = chestnut, now_ns
    if not safe:
      self.safe_since_ns = 0
    elif not self.safe_since_ns:
      self.safe_since_ns = now_ns
    if (not running_small or chestnut is None or chestnut == self.used or
        now_ns - self.seen_since_ns < STABLE_NS or self.attempts >= MAX_ATTEMPTS or
        (self.last_attempt_ns and now_ns - self.last_attempt_ns < MIN_INTERVAL_NS) or
        not self.safe_since_ns or now_ns - self.safe_since_ns < SAFE_NS or
        DISABLE_FILE.exists() or not big_selected()):
      return False
    self.attempts += 1
    self.last_attempt_ns = now_ns
    self.used = chestnut  # one try per enumeration; a failed try waits for the next re-enumeration
    return True
