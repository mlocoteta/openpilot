import pyray as rl
from cereal import log
from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.layouts.settings.starpilot.asset_loader import starpilot_texture
from openpilot.system.ui.widgets import Widget

BTN_SIZE = 192
ICON_SIZE = 144
PERSONALITY_TO_INT = log.LongitudinalPersonality.schema.enumerants


class PersonalityButton(Widget):
  def __init__(self):
    super().__init__()
    self._params_memory = Params(memory=True)

    self._personality: int = 1  # default: standard
    self._traffic_mode: bool = False

    # Texture I/O must not occur while MainLayout is being assembled.  The
    # startup watchdog has a short budget and this widget is often hidden
    # until controls engage, so load these on first render instead.
    self._icons: list[rl.Texture] = []

    self._rect = rl.Rectangle(0, 0, BTN_SIZE, BTN_SIZE)

    self._black_bg = rl.Color(0, 0, 0, 0)
    self._white = rl.Color(255, 255, 255, 255)

    self.set_visible(lambda: ui_state.started and ui_state.has_longitudinal_control)

  @property
  def center_x(self) -> float:
    return self._rect.x + self._rect.width / 2

  @property
  def is_interacting(self) -> bool:
    return self.is_pressed

  def _update_state(self):
    sm = ui_state.sm
    if sm.valid.get("selfdriveState", False):
      self._personality = PERSONALITY_TO_INT[sm["selfdriveState"].personality]
    self._traffic_mode = ui_state.traffic_mode_enabled

  def _load_icons(self):
    if self._icons:
      return
    # 0=traffic, 1=aggressive, 2=standard, 3=relaxed
    self._icons = [
      starpilot_texture("stock_theme/distance_icons/traffic.png", ICON_SIZE, ICON_SIZE),
      starpilot_texture("stock_theme/distance_icons/aggressive.png", ICON_SIZE, ICON_SIZE),
      starpilot_texture("stock_theme/distance_icons/standard.png", ICON_SIZE, ICON_SIZE),
      starpilot_texture("stock_theme/distance_icons/relaxed.png", ICON_SIZE, ICON_SIZE),
    ]

  def _handle_mouse_press(self, _):
    self._params_memory.put_bool("OnroadDistanceButtonPressed", True)

  def _handle_mouse_release(self, _):
    self._params_memory.put_bool("OnroadDistanceButtonPressed", False)

  def _render(self, rect: rl.Rectangle):
    self._load_icons()
    center_x = int(self._rect.x + self._rect.width / 2)
    center_y = int(self._rect.y + self._rect.height / 2)

    opacity = 180 if self.is_pressed else 255
    self._white.a = opacity

    icon_idx = 0 if self._traffic_mode else min(self._personality + 1, len(self._icons) - 1)
    icon = self._icons[icon_idx]

    rl.draw_circle(center_x, center_y, self._rect.width / 2, self._black_bg)
    rl.draw_texture(icon, center_x - icon.width // 2, center_y - icon.height // 2, self._white)
