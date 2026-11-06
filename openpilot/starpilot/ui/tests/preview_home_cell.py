"""Accord: render the StarPilot Home sidebar (home.py, what the comma 3X shows) for each cell state to PNGs.

  OFFSCREEN=1 xvfb-run -a ./dev python openpilot/starpilot/ui/tests/preview_home_cell.py OUT_DIR
"""
import sys
from dataclasses import replace
from pathlib import Path

import pyray as rl

from openpilot.selfdrive.ui.lib.cell_status import CellStatus
from openpilot.starpilot.ui.home import HomeView
from openpilot.starpilot.ui.preview_home import reference_state
from openpilot.starpilot.ui.presentation import BitmapFonts, Profile, default_font_directory

ASSETS = Path(__file__).resolve().parents[3] / "selfdrive/assets"
STATES = {
  "home_wifi_lte": ("wifi", 4, CellStatus("cell", "LTE", 4)),
  "home_wifi_no_lte": ("wifi", 5, CellStatus("no_cell", "No LTE", 0)),
  "home_wifi_no_sim": ("wifi", 5, CellStatus("no_sim", "No SIM", 0)),
  "home_lte_only": ("cell4G", 3, None),
}


def main(out: Path) -> None:
  out.mkdir(parents=True, exist_ok=True)
  profile = Profile.LARGE
  width, height = profile.size
  rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)
  rl.init_window(960, 540, "Home cell preview")
  target = rl.load_render_texture(width, height)
  try:
    with BitmapFonts(profile, default_font_directory()) as fonts:
      view = HomeView(fonts, ASSETS)
      try:
        for name, (network, strength, cell) in STATES.items():
          state = replace(reference_state(), network=network, network_strength=strength, cell=cell, connection="ONLINE")
          rl.begin_texture_mode(target)
          rl.clear_background(rl.BLACK)
          view.render(state)
          rl.end_texture_mode()
          for suffix, crop in (("", rl.Rectangle(0, 0, 330, 820)), ("_full", None)):
            img = rl.load_image_from_texture(target.texture)
            rl.image_flip_vertical(img)
            if crop is not None:
              rl.image_crop(img, crop)
            rl.export_image(img, str(out / f"{name}{suffix}.png"))
            rl.unload_image(img)
          print(name, cell)
      finally:
        view.close()
  finally:
    rl.unload_render_texture(target)
    rl.close_window()


if __name__ == "__main__":
  main(Path(sys.argv[1]))
