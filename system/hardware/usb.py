from pathlib import Path

CHESTNUT_VENDOR_ID = 0xADD1
CHESTNUT_VENDOR_IDS = (CHESTNUT_VENDOR_ID, 0x3801)
CHESTNUT_PRODUCT_ID = 0x0001
CHESTNUT_FW_VERSION = "ed4e39b7"
CHESTNUT_ROM_USB_IDS = ((0x174C, 0x2464), (0x174C, 0x2463))
USB_DEVICES_PATH = Path("/sys/bus/usb/devices")


def read_int(path: Path, base: int = 10) -> int:
  try:
    return int(path.read_text(), base)
  except (OSError, ValueError):
    return 0


def read_text(path: Path) -> str:
  try:
    return path.read_text().strip()
  except OSError:
    return ""


def usb_devices() -> list[Path]:
  try:
    devices = (path for path in USB_DEVICES_PATH.glob("*") if (path / "idVendor").exists())
    return sorted(devices, key=lambda path: path.name)
  except OSError:
    return []


def chestnut_present() -> bool:
  return any(
    read_int(device / "idVendor", 16) in CHESTNUT_VENDOR_IDS and
    read_int(device / "idProduct", 16) == CHESTNUT_PRODUCT_ID
    for device in usb_devices()
  )


def chestnut_firmware_ready() -> bool:
  expected = f"custom {CHESTNUT_FW_VERSION}-CLEAN"
  return any(
    read_int(device / "idVendor", 16) in CHESTNUT_VENDOR_IDS and
    read_int(device / "idProduct", 16) == CHESTNUT_PRODUCT_ID and
    read_text(device / "product") == expected
    for device in usb_devices()
  )


def controller(device: Path) -> Path | None:
  try:
    return next((parent for parent in device.resolve().parents if parent.name.endswith(".ssusb")), None)
  except OSError:
    return None
