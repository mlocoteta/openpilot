import pyray as rl

from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.text_measure import draw_text_with_shadow, measure_text_cached


PULSE_COLOR = rl.Color(52, 190, 112, 255)
GLIDE_COLOR = rl.Color(65, 155, 235, 255)
DEEP_GLIDE_BORDER_COLOR = rl.Color(24, 72, 150, 255)


def get_pulse_glide_border_color(sm, default_color: rl.Color) -> rl.Color:
  """Use a deep-blue outer border only while developer P&G is gliding."""
  if (
    not sm.valid.get("starpilotCarState", False) or
    not sm.valid.get("starpilotPlan", False) or
    not sm.valid.get("carControl", False) or
    not bool(getattr(sm["carControl"], "longActive", False))
  ):
    return default_color

  car_state = sm["starpilotCarState"]
  plan = sm["starpilotPlan"]
  if bool(getattr(car_state, "pulseAndGlide", False)) and bool(getattr(plan, "pulseGlideCoasting", False)):
    return DEEP_GLIDE_BORDER_COLOR
  return default_color


def render_pulse_glide(rect: rl.Rectangle, coasting: bool) -> None:
  """Render the developer-only P&G phase badge beside the standard HUD badges."""
  border = GLIDE_COLOR if coasting else PULSE_COLOR
  label = "GLIDE" if coasting else "PULSE"
  font = gui_app.font(FontWeight.BOLD)
  font_size = 27
  text_size = measure_text_cached(font, label, font_size)

  rl.draw_rectangle_rounded(rect, 0.3, 10, rl.Color(0, 0, 0, 166))
  rl.draw_rectangle_rounded_lines_ex(rect, 0.3, 10, 4, border)
  draw_text_with_shadow(
    font,
    label,
    rl.Vector2(rect.x + (rect.width - text_size.x) / 2, rect.y + (rect.height - text_size.y) / 2),
    font_size,
    rl.WHITE,
  )
