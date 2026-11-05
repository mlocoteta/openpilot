from openpilot.cereal import log
from openpilot.selfdrive.ui.lib.cell_status import CellStatus, cell_bars, cell_status

NT = log.DeviceState.NetworkType

LTE_UP = {"state": "CONNECTED", "connected": True, "registration": "home", "network_type": "lte", "signal_quality": 61, "sim": "ready"}


def test_wifi_plus_lte():
  assert cell_status(NT.wifi, LTE_UP) == CellStatus("cell", "LTE", 4)


def test_wifi_plus_registered_not_dialed():
  ms = {"state": "SEARCHING", "connected": False, "registration": "roaming", "network_type": "nr", "signal_quality": 90}
  assert cell_status(NT.wifi, ms) == CellStatus("cell", "5G", 5)


def test_wifi_no_lte():
  ms = {"state": "SEARCHING", "connected": False, "registration": "searching", "sim": "ready"}
  assert cell_status(NT.wifi, ms) == CellStatus("no_cell", "No LTE", 0)
  assert cell_status(NT.wifi, {}) == CellStatus("no_cell", "No LTE", 0)  # modem daemon not up / PC
  assert cell_status(NT.wifi, None) == CellStatus("no_cell", "No LTE", 0)


def test_wifi_no_sim_wins_over_stale_registration():
  ms = {"state": "INITIALIZING", "connected": False, "registration": "home", "sim": "absent", "imei": "123456789012345"}
  assert cell_status(NT.wifi, ms) == CellStatus("no_sim", "No SIM", 0)


def test_ethernet_also_shows_cell():
  assert cell_status(NT.ethernet, LTE_UP) == CellStatus("cell", "LTE", 4)


def test_cell_only_and_offline_keep_stock_indicator():
  for nt in (NT.cell2G, NT.cell3G, NT.cell4G, NT.cell5G, NT.none):
    assert cell_status(nt, LTE_UP) is None
    assert cell_status(nt, {"sim": "absent"}) is None


def test_bars_scale():
  assert [cell_bars(q) for q in (0, 1, 24, 25, 49, 50, 74, 75, 100)] == [0, 2, 2, 3, 3, 4, 4, 5, 5]
  assert cell_bars(None) == 0 and cell_bars("x") == 0
