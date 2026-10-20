import pyray as rl
from openpilot.common.constants import CV
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.selfdrive.ui.onroad.starpilot.widgets.base import LayoutWidget
from openpilot.selfdrive.ui.onroad.model_renderer import get_planner_desired_speed

# Same look as the lead metrics under the chevron (model_renderer._draw_lead_metrics).
FONT_SIZE = 36
LINE_HEIGHT = FONT_SIZE + 2
# Hide when within this many display units of the set speed, so steady cruising stays quiet.
QUIET_BAND = 1.0


def speed_units() -> tuple[float, str]:
  if ui_state.starpilot_toggles.get("UseSiMetrics", False):
    return 1.0, "m/s"
  if ui_state.is_metric:
    return CV.MS_TO_KPH, "km/h"
  return CV.MS_TO_MPH, "mph"


class DesiredSpeedWidget(LayoutWidget):
  """No-lead planner target speed under the MAX / speed-limit cards. Hidden when it matches the set speed."""

  def __init__(self, hud_renderer):
    super().__init__("desired_speed", priority=2)
    self.hud_renderer = hud_renderer
    self._font = gui_app.font(FontWeight.SEMI_BOLD)
    self._lines: list[str] = []

  def _compute_lines(self) -> list[str]:
    if not ui_state.ui_params.get_bool("LeadInfo"):
      return []
    if not ui_state.has_longitudinal_control or ui_state.status == UIStatus.DISENGAGED:
      return []
    if not self.hud_renderer.is_cruise_set:
      return []

    # With a lead the value is inline in the lead metrics ("53 mph (Desired: 52)").
    sm = ui_state.sm
    if sm.valid.get("radarState", False) and sm["radarState"].leadOne.status:
      return []

    v_desired = get_planner_desired_speed(sm)
    if v_desired is None:
      return []

    # hud_renderer.set_speed is in km/h or mph (offset included), whatever unit we display in.
    set_speed_conversion = CV.MS_TO_KPH if ui_state.is_metric else CV.MS_TO_MPH
    if v_desired * set_speed_conversion >= self.hud_renderer.set_speed - QUIET_BAND:
      return []

    conversion, unit = speed_units()
    return ["Desired", f"{round(v_desired * conversion)} {unit}"]

  @property
  def is_visible(self) -> bool:
    self._lines = self._compute_lines()
    return bool(self._lines)

  @property
  def blocks_pointer(self) -> bool:
    return False

  def get_size(self) -> tuple[float, float]:
    width = max((measure_text_cached(self._font, line, FONT_SIZE).x for line in self._lines), default=0.0)
    return float(width), float(len(self._lines) * LINE_HEIGHT)

  def _render(self, rect: rl.Rectangle) -> None:
    from openpilot.selfdrive.ui.onroad.starpilot.path import _draw_text_with_outline
    center_x = rect.x + rect.width / 2
    for i, line in enumerate(self._lines):
      sz = measure_text_cached(self._font, line, FONT_SIZE)
      _draw_text_with_outline(line, center_x - sz.x / 2, rect.y + i * LINE_HEIGHT, self._font, FONT_SIZE)
