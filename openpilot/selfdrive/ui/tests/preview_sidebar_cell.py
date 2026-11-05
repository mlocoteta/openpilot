"""Accord: render the sidebar network indicator for each cell state to PNGs (desktop, xvfb ok).

  ./dev python openpilot/selfdrive/ui/tests/preview_sidebar_cell.py OUT_DIR
"""
import sys
from pathlib import Path

import pyray as rl

from openpilot.cereal import log
from openpilot.selfdrive.ui.lib.cell_status import cell_status
from openpilot.system.ui.lib.application import gui_app

NT = log.DeviceState.NetworkType
STATES = {
  "wifi_lte": (NT.wifi, 4, {"connected": True, "registration": "home", "network_type": "lte", "signal_quality": 61, "sim": "ready"}),
  "wifi_no_lte": (NT.wifi, 5, {"state": "SEARCHING", "registration": "searching", "sim": "ready"}),
  "wifi_no_sim": (NT.wifi, 5, {"state": "INITIALIZING", "sim": "absent"}),
  "lte_only": (NT.cell4G, 3, {"connected": True, "registration": "home", "network_type": "lte", "signal_quality": 45}),
  "offline": (NT.none, 0, {}),
}


def main(out: Path) -> None:
  from openpilot.selfdrive.ui.layouts.sidebar import NETWORK_TYPES, SIDEBAR_WIDTH, Sidebar
  out.mkdir(parents=True, exist_ok=True)
  gui_app.init_window("sidebar cell preview")
  h = 1080
  target = rl.load_render_texture(SIDEBAR_WIDTH, h)
  sb = Sidebar()
  for name, (nt, bars, modem) in STATES.items():
    sb._net_type = NETWORK_TYPES[nt]
    sb._net_strength = bars
    sb._cell = cell_status(nt, modem)
    rl.begin_texture_mode(target)
    rl.clear_background(rl.BLACK)
    sb._render(rl.Rectangle(0, 0, SIDEBAR_WIDTH, h))
    rl.end_texture_mode()
    img = rl.load_image_from_texture(target.texture)
    rl.image_flip_vertical(img)
    rl.image_crop(img, rl.Rectangle(0, 160, SIDEBAR_WIDTH, 180))
    rl.export_image(img, str(out / f"{name}.png"))
    rl.unload_image(img)
    print(name, sb._cell)
  gui_app.close()


if __name__ == "__main__":
  main(Path(sys.argv[1]))
