import os
import pyray as rl
from cereal import log
from openpilot.common.constants import CV
from openpilot.selfdrive.ui.mici.onroad import SIDE_PANEL_WIDTH
from openpilot.selfdrive.ui.mici.onroad.confidence_ball import ConfidenceBall
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.starpilot.common.experimental_state import CCStatus, CEStatus
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget

PERSONALITY_TO_INT = log.LongitudinalPersonality.schema.enumerants
DEMO_HOLD_SECONDS = 1.5
DEMO_REASONS = ("chill", "lead", "stop", "curve", "speed")
DEMO_PERSONALITIES = (
  (False, 0),  # aggressive
  (False, 1),  # standard
  (False, 2),  # relaxed
  (True, 0),   # traffic
)

WHITE = rl.Color(255, 255, 255, 255)
WHITE_DIM = rl.Color(255, 255, 255, 170)
BLACK = rl.Color(0, 0, 0, 255)
PERSONALITY_BLUE = rl.Color(112, 192, 216, 255)
CEM_BLUE = PERSONALITY_BLUE
TRAFFIC_RED = rl.Color(200, 32, 48, 255)


def _with_alpha(color: rl.Color, alpha: int) -> rl.Color:
  return rl.Color(color.r, color.g, color.b, max(0, min(255, alpha)))


def _env_truthy(name: str) -> bool:
  return os.getenv(name, "").lower() in {"1", "true", "yes", "on"}


def _v(x: float, y: float) -> rl.Vector2:
  return rl.Vector2(float(x), float(y))


def _draw_line(x1: float, y1: float, x2: float, y2: float, thickness: float, color: rl.Color) -> None:
  rl.draw_line_ex(_v(x1, y1), _v(x2, y2), thickness, color)


def _draw_tri(p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float], color: rl.Color) -> None:
  rl.draw_triangle(_v(*p1), _v(*p2), _v(*p3), color)


def _draw_quad(points: tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]], color: rl.Color) -> None:
  p1, p2, p3, p4 = points
  rl.draw_triangle(_v(*p1), _v(*p2), _v(*p3), color)
  rl.draw_triangle(_v(*p1), _v(*p3), _v(*p4), color)


def _draw_quad_outline(points: tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]], thickness: float, color: rl.Color) -> None:
  for idx, start in enumerate(points):
    end = points[(idx + 1) % len(points)]
    _draw_line(start[0], start[1], end[0], end[1], thickness, color)


def _draw_bezier(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float], thickness: float, color: rl.Color) -> None:
  rl.draw_spline_segment_bezier_cubic(_v(*p0), _v(*p1), _v(*p2), _v(*p3), thickness, color)


def _bezier_point(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float], t: float) -> tuple[float, float]:
  inv_t = 1.0 - t
  x = inv_t ** 3 * p0[0] + 3 * inv_t ** 2 * t * p1[0] + 3 * inv_t * t ** 2 * p2[0] + t ** 3 * p3[0]
  y = inv_t ** 3 * p0[1] + 3 * inv_t ** 2 * t * p1[1] + 3 * inv_t * t ** 2 * p2[1] + t ** 3 * p3[1]
  return x, y


def _draw_dashed_bezier(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float], thickness: float, color: rl.Color) -> None:
  for start_t, end_t in ((0.18, 0.28), (0.39, 0.50), (0.61, 0.72)):
    start = _bezier_point(p0, p1, p2, p3, start_t)
    end = _bezier_point(p0, p1, p2, p3, end_t)
    _draw_line(start[0], start[1], end[0], end[1], thickness, color)


class MiciSidebarWidgets(Widget):
  def __init__(self, confidence_ball: ConfidenceBall):
    super().__init__()
    self._confidence_ball = confidence_ball
    self._font_bold = gui_app.font(FontWeight.BOLD)
    self._font_semi_bold = gui_app.font(FontWeight.SEMI_BOLD)
    self._demo = _env_truthy("SP_CEM_DEMO") or _env_truthy("SP_MICI_WIDGET_DEMO")

  @property
  def demo_active(self) -> bool:
    return self._demo

  def _render(self, rect: rl.Rectangle) -> None:
    sidebar = rl.Rectangle(
      rect.x + rect.width - SIDE_PANEL_WIDTH,
      rect.y,
      SIDE_PANEL_WIDTH,
      rect.height,
    )
    rl.draw_rectangle(int(sidebar.x), int(sidebar.y), int(sidebar.width), int(sidebar.height), BLACK)

    slot_height = sidebar.height / 3
    confidence_slot = rl.Rectangle(sidebar.x, sidebar.y, sidebar.width, slot_height)
    cem_slot = rl.Rectangle(sidebar.x, sidebar.y + slot_height, sidebar.width, slot_height)
    personality_slot = rl.Rectangle(sidebar.x, sidebar.y + slot_height * 2, sidebar.width, sidebar.height - slot_height * 2)

    self._confidence_ball.render_static(confidence_slot, max(16, min(20, int(slot_height * 0.28))))
    self._draw_cem_widget(cem_slot)
    self._draw_personality_widget(personality_slot)

  def _draw_personality_widget(self, rect: rl.Rectangle) -> None:
    center_x = rect.x + rect.width / 2
    center_y = rect.y + rect.height / 2
    icon_height = min(rect.height - 6, 64)
    bottom_y = center_y + icon_height * 0.42
    lane_top_y = center_y - icon_height * 0.38

    traffic_mode, personality = self._personality_state()

    active_color = TRAFFIC_RED if traffic_mode else PERSONALITY_BLUE
    stack_count = 1 if traffic_mode else max(1, min(3, personality + 1))

    _draw_line(center_x - 23, bottom_y, center_x - 14, lane_top_y, 3, WHITE)
    _draw_line(center_x + 23, bottom_y, center_x + 14, lane_top_y, 3, WHITE)

    car_top_y = bottom_y - 4
    car_bottom_y = bottom_y + 8
    car_outline = (
      (center_x - 8, car_top_y),
      (center_x + 8, car_top_y),
      (center_x + 13, car_bottom_y),
      (center_x - 13, car_bottom_y),
    )
    _draw_quad_outline(car_outline, 3, WHITE)

    bar_h = max(6, min(9, int(icon_height * 0.14)))
    gap = max(3, min(5, int(icon_height * 0.08)))
    y = bottom_y - bar_h - 4
    widths = ((36, 30), (28, 23), (20, 16))
    for idx in range(stack_count):
      bottom_w, top_w = widths[idx]
      top_y = y
      bottom = y + bar_h
      points = (
        (center_x - top_w / 2, top_y),
        (center_x + top_w / 2, top_y),
        (center_x + bottom_w / 2, bottom),
        (center_x - bottom_w / 2, bottom),
      )
      _draw_quad(points, _with_alpha(active_color, 60))
      _draw_quad_outline(points, 3, active_color)
      y -= bar_h + gap

  def _personality_state(self) -> tuple[bool, int]:
    if self._demo:
      return DEMO_PERSONALITIES[int(rl.get_time() / DEMO_HOLD_SECONDS) % len(DEMO_PERSONALITIES)]

    personality = 1
    try:
      if ui_state.sm.valid.get("selfdriveState", False):
        personality = PERSONALITY_TO_INT[ui_state.sm["selfdriveState"].personality]
      elif isinstance(ui_state.personality, int):
        personality = ui_state.personality
      else:
        personality = PERSONALITY_TO_INT[ui_state.personality]
    except Exception:
      personality = 1
    return ui_state.traffic_mode_enabled, personality

  def _draw_cem_widget(self, rect: rl.Rectangle) -> None:
    reason, color = self._cem_reason()
    if reason == "chill":
      self._draw_chill_icon(rect)
    elif reason == "lead":
      self._draw_lead_icon(rect, color)
    elif reason == "stop":
      self._draw_stop_light_icon(rect)
    elif reason == "curve":
      self._draw_curve_icon(rect, color)
    elif reason == "turn":
      self._draw_turn_icon(rect, color)
    elif reason == "speed":
      self._draw_speed_icon(rect, color)
    else:
      self._draw_chill_icon(rect)

  def _model_stop_active(self) -> bool:
    try:
      if ui_state.sm.recv_frame["starpilotPlan"] >= ui_state.started_frame:
        starpilot_plan = ui_state.sm["starpilotPlan"]
        return bool(starpilot_plan.redLight or starpilot_plan.forcingStop)
    except Exception:
      pass
    return False

  def _curve_speed_controller_active(self) -> bool:
    try:
      if ui_state.sm.recv_frame["starpilotPlan"] >= ui_state.started_frame:
        return bool(ui_state.sm["starpilotPlan"].cscControllingSpeed)
    except Exception:
      pass
    return False

  def _cem_reason(self) -> tuple[str, rl.Color]:
    if self._demo:
      status = ui_state.params_memory.get_int("CEStatus", default=CEStatus["OFF"])
      status_reason = self._ce_status_reason(status)
      if status_reason is not None:
        return status_reason
      return self._fallback_demo_reason()

    if self._model_stop_active():
      return "stop", TRAFFIC_RED
    if self._curve_speed_controller_active():
      return "curve", CEM_BLUE

    conditional_experimental = ui_state.ui_params.get_bool("ConditionalExperimental")
    conditional_chill = ui_state.ui_params.get_bool("ConditionalChill") and not conditional_experimental
    if conditional_chill:
      status = ui_state.params_memory.get_int("CCStatus", default=CCStatus["OFF"])
      if status == CCStatus["LEAD"]:
        return "lead", CEM_BLUE
      if status == CCStatus["SPEED"]:
        return "speed", CEM_BLUE
      if status == CCStatus["USER_EXPERIMENTAL"]:
        return "chill", WHITE
      if status == CCStatus["USER_CHILL"]:
        return "chill", WHITE
      return "chill", WHITE

    status = ui_state.params_memory.get_int("CEStatus", default=CEStatus["OFF"]) if conditional_experimental else CEStatus["OFF"]
    status_reason = self._ce_status_reason(status)
    if status_reason is not None:
      return status_reason
    return "chill", WHITE

  def _fallback_demo_reason(self) -> tuple[str, rl.Color]:
    reason = DEMO_REASONS[int(rl.get_time() / DEMO_HOLD_SECONDS) % len(DEMO_REASONS)]
    if reason == "chill":
      return reason, WHITE
    if reason == "stop":
      return reason, TRAFFIC_RED
    return reason, CEM_BLUE

  def _ce_status_reason(self, status: int) -> tuple[str, rl.Color] | None:
    if status == CEStatus["CURVATURE"]:
      return "curve", CEM_BLUE
    if status == CEStatus["LEAD"]:
      return "lead", CEM_BLUE
    if status == CEStatus["SIGNAL"]:
      return "turn", CEM_BLUE
    if status in (CEStatus["SPEED"], CEStatus["SPEED_LIMIT"]):
      return "speed", CEM_BLUE
    if status == CEStatus["STOP_LIGHT"]:
      return "stop", TRAFFIC_RED
    if status == CEStatus["USER_DISABLED"]:
      return "chill", WHITE
    if status == CEStatus["USER_OVERRIDDEN"]:
      return "chill", WHITE
    return None

  def _draw_chill_icon(self, rect: rl.Rectangle) -> None:
    cx = rect.x + rect.width / 2
    cy = rect.y + rect.height / 2
    stroke = 3

    _draw_line(cx - 14, cy - 15, cx + 14, cy - 15, stroke, WHITE)
    _draw_line(cx - 16, cy - 13, cx - 16, cy + 1, stroke, WHITE)
    _draw_line(cx + 16, cy - 13, cx + 16, cy + 1, stroke, WHITE)
    _draw_line(cx - 19, cy + 3, cx + 19, cy + 3, stroke, WHITE)
    _draw_line(cx - 21, cy - 3, cx - 21, cy + 10, stroke, WHITE)
    _draw_line(cx + 21, cy - 3, cx + 21, cy + 10, stroke, WHITE)
    _draw_line(cx - 21, cy + 10, cx + 21, cy + 10, stroke, WHITE)
    _draw_line(cx - 14, cy + 6, cx + 14, cy + 6, 2, CEM_BLUE)
    _draw_line(cx - 14, cy + 12, cx - 17, cy + 19, stroke, WHITE)
    _draw_line(cx + 14, cy + 12, cx + 17, cy + 19, stroke, WHITE)

  def _draw_lead_icon(self, rect: rl.Rectangle, color: rl.Color) -> None:
    cx = rect.x + rect.width / 2
    cy = rect.y + rect.height / 2
    self._draw_car(cx, cy - 13, 31, 18, WHITE, TRAFFIC_RED)
    self._draw_car(cx, cy + 12, 43, 22, WHITE, TRAFFIC_RED)
    _draw_line(cx - 11, cy - 1, cx - 11, cy + 3, 2, _with_alpha(WHITE, 130))
    _draw_line(cx + 11, cy - 1, cx + 11, cy + 3, 2, _with_alpha(WHITE, 130))

  def _draw_car(self, cx: float, cy: float, width: float, height: float, color: rl.Color, accent: rl.Color) -> None:
    top = cy - height / 2
    bottom = cy + height / 2
    body = (
      (cx - width * 0.34, top + height * 0.10),
      (cx + width * 0.34, top + height * 0.10),
      (cx + width * 0.50, bottom - height * 0.04),
      (cx - width * 0.50, bottom - height * 0.04),
    )
    windshield = (
      (cx - width * 0.22, top + height * 0.24),
      (cx + width * 0.22, top + height * 0.24),
      (cx + width * 0.32, top + height * 0.50),
      (cx - width * 0.32, top + height * 0.50),
    )
    _draw_quad_outline(body, 3, color)
    _draw_quad_outline(windshield, 2, color)
    _draw_line(cx - width * 0.56, top + height * 0.46, cx - width * 0.50, top + height * 0.46, 2, color)
    _draw_line(cx + width * 0.50, top + height * 0.46, cx + width * 0.56, top + height * 0.46, 2, color)
    _draw_line(cx - width * 0.32, bottom - height * 0.22, cx - width * 0.16, bottom - height * 0.22, 2, accent)
    _draw_line(cx + width * 0.16, bottom - height * 0.22, cx + width * 0.32, bottom - height * 0.22, 2, accent)

  def _draw_stop_light_icon(self, rect: rl.Rectangle) -> None:
    cx = rect.x + rect.width / 2
    cy = rect.y + rect.height / 2
    housing = rl.Rectangle(cx - 12, cy - 27, 24, 54)
    rl.draw_rectangle_rounded_lines_ex(housing, 0.35, 8, 3, WHITE)
    for bulb_y in (cy - 16, cy, cy + 16):
      rl.draw_circle_lines(int(cx), int(bulb_y), 6, WHITE)
    rl.draw_circle_lines(int(cx), int(cy - 16), 7, TRAFFIC_RED)
    rl.draw_circle(int(cx), int(cy - 16), 4, TRAFFIC_RED)

  def _draw_curve_icon(self, rect: rl.Rectangle, color: rl.Color) -> None:
    cx = rect.x + rect.width / 2
    cy = rect.y + rect.height / 2
    def road_curve_points(x_offset: float) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]:
      return (
        (cx + x_offset, cy + 24),
        (cx + x_offset - 1, cy + 9),
        (cx + x_offset + 1, cy - 9),
        (cx + x_offset + 6, cy - 24),
      )

    for points in (road_curve_points(-18), road_curve_points(14)):
      _draw_bezier(*points, 3, WHITE)
    _draw_dashed_bezier(*road_curve_points(-2), 4, color)

  def _draw_turn_icon(self, rect: rl.Rectangle, color: rl.Color) -> None:
    cx = rect.x + rect.width / 2
    cy = rect.y + rect.height / 2
    left = False
    right = True
    try:
      left = ui_state.sm["carState"].leftBlinker
      right = ui_state.sm["carState"].rightBlinker
    except Exception:
      pass
    direction = -1 if left or not right else 1
    shaft = (
      (cx - direction * 10, cy + 25),
      (cx - direction * 13, cy + 6),
      (cx - direction * 4, cy - 8),
      (cx + direction * 18, cy - 20),
    )
    _draw_bezier(*shaft, 4, color)
    tip = (cx + direction * 24, cy - 26)
    _draw_tri(
      tip,
      (cx + direction * 4, cy - 24),
      (cx + direction * 19, cy - 7),
      color,
    )

  def _draw_speed_icon(self, rect: rl.Rectangle, color: rl.Color) -> None:
    cx = rect.x + rect.width / 2
    cy = rect.y + rect.height / 2
    radius = min(rect.width, rect.height) * 0.34
    text = self._speed_text()

    rl.draw_circle(int(cx), int(cy), radius - 2.5, WHITE)
    rl.draw_ring(_v(cx, cy), radius - 5, radius, 0, 360, 48, color)

    font_size = 19 if len(text) <= 2 else 16
    text_size = measure_text_cached(self._font_bold, text, font_size)
    rl.draw_text_ex(self._font_bold, text, rl.Vector2(cx - text_size.x / 2, cy - text_size.y / 2 + 1), font_size, 0, BLACK)

  def _speed_text(self) -> str:
    if ui_state.sm.recv_frame["starpilotPlan"] < ui_state.started_frame:
      return "S"

    speed_limit = ui_state.sm["starpilotPlan"].slcSpeedLimit
    if speed_limit <= 0:
      return "S"

    conversion = CV.MS_TO_KPH if ui_state.is_metric else CV.MS_TO_MPH
    speed_text = str(round(speed_limit * conversion))
    return speed_text[:3]
