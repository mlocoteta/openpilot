import subprocess
import time

from pathlib import Path


RADIO_HELPER = "/usr/comma/bluetooth-radio"


class BluetoothRadio:
  def __init__(self, helper: str = RADIO_HELPER):
    self.helper = helper

  @property
  def available(self) -> bool:
    return Path(self.helper).is_file()

  @property
  def ready(self) -> bool:
    return Path("/sys/class/bluetooth/hci0").exists()

  def start(self, timeout: float = 50.0) -> None:
    if not self.available:
      raise RuntimeError("Bluetooth radio support is not installed")
    subprocess.run(["sudo", "-n", "systemctl", "start", "starpilot-bluetooth-radio.service"], check=True, timeout=timeout)
    deadline = time.monotonic() + timeout
    while not self.ready:
      if time.monotonic() >= deadline:
        raise RuntimeError("Bluetooth radio did not become ready")
      time.sleep(0.1)

  def stop(self, timeout: float = 10.0) -> None:
    if self.available:
      subprocess.run(["sudo", "-n", "systemctl", "stop", "starpilot-bluetooth-radio.service"], check=True, timeout=timeout)
