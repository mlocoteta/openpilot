"""Accord: cell status shown under the active network when Wi-Fi/Ethernet carries the data.

Source is the modem daemon's state (/dev/shm/modem via HARDWARE.get_modem_state()); hardwared only reports the
default-route network, so on Wi-Fi the cell side was invisible.
"""
from dataclasses import dataclass

from openpilot.cereal import log

NetworkType = log.DeviceState.NetworkType

CELL_TECH = {"lte": "LTE", "nr": "5G", "utran": "3G", "umts": "3G", "gsm": "2G"}
REGISTERED = ("home", "roaming")


@dataclass(frozen=True, slots=True)
class CellStatus:
  kind: str   # "cell" (registered/connected), "no_cell", "no_sim"
  label: str  # "LTE" / "5G" / "No LTE" / "No SIM"
  bars: int   # 0..5, same scale as the sidebar's main dots


def cell_bars(signal_quality) -> int:
  # matches hardware.parse_strength() + the sidebar's raw + 1 mapping (poor=2 .. great=5)
  try:
    q = int(signal_quality)
  except (TypeError, ValueError):
    return 0
  if q <= 0:
    return 0
  return 2 if q < 25 else 3 if q < 50 else 4 if q < 75 else 5


def cell_status(network_type, modem: dict | None) -> CellStatus | None:
  """None = no second line (cell is the active network, or nothing is connected): keep the stock indicator."""
  if network_type not in (NetworkType.wifi, NetworkType.ethernet):
    return None
  ms = modem or {}
  if ms.get("sim") == "absent":
    return CellStatus("no_sim", "No SIM", 0)
  if ms.get("connected") or ms.get("registration") in REGISTERED:
    return CellStatus("cell", CELL_TECH.get(str(ms.get("network_type", "")).lower(), "LTE"), cell_bars(ms.get("signal_quality", 0)))
  return CellStatus("no_cell", "No LTE", 0)
