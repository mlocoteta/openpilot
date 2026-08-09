from dataclasses import dataclass
from enum import Enum
import math
import os
import pyray as rl
from openpilot.common.constants import CV
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.starpilot.common.experimental_state import CEStatus
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.selfdrive.ui.onroad.starpilot.starpilot_border import _csc_state, _intensity, _glow_color
from openpilot.selfdrive.ui.lib.starpilot_status import get_border_color


# --- Scale factor (single knob for all pixel-space dimensions) ---

SCALE = 1.5


# --- Named constants ---

X_MIN = 3.0
X_MAX = 60.0
PATH_Y_FAR_SCALE = 1800.0
PERSPECTIVE_GAIN = 0.35
PERSPECTIVE_MAX_OFFSET = 26.0 * SCALE
PERSPECTIVE_EXPONENT = 1.8

ROAD_HEIGHT = 80.0 * SCALE
ROAD_SEGMENTS = 24
ROAD_W_BOTTOM = 32.0 * SCALE
ROAD_W_TOP = 18.0 * SCALE
ROAD_THICKNESS = 4.0 * SCALE
ROAD_HALF_SIZE = 40.0 * SCALE
ROAD_EDGE_INSET = 2.0 * SCALE
FILL_ALPHA = 90

STOP_SNAP_THRESHOLD = 0.5
STOP_LERP_RATE = 0.25
STOP_DISTANCE_MAX = 60.0

CHEVRON_COUNT = 6
CHEVRON_SPACING = 0.3
CHEVRON_STEP = 0.05

CEM_STATUS_CURVE = 3
CEM_STATUS_LEAD = 4
CEM_STATUS_STOP_LIGHT = 8

LEAD_STOPPED_SPEED_THRESHOLD = 1.0

COLOR_FORCE_STOP = rl.Color(255, 30, 60, 255)
COLOR_LEAD_STOPPED = rl.Color(255, 60, 60, 255)
COLOR_LEAD_SLOWER = rl.Color(255, 191, 0, 255)
COLOR_SHADOW = rl.Color(0, 0, 0, 100)
COLOR_STOP_SIGN_OUTLINE = rl.Color(255, 255, 255, 255)
COLOR_STOP_LINE_GLOW = rl.Color(255, 30, 60, 255)
COLOR_STOP_LINE_CORE = rl.Color(255, 200, 200, 255)
COLOR_CEM_SPEED = rl.Color(112, 192, 216, 255)
COLOR_REDUCTION = rl.Color(255, 191, 0, 220)

# Set to True to force test-cycle mode (flip back to False before pushing)
TEST_CYCLE = False


# --- Conversion helpers ---

def _speed_conversion() -> float:
  return CV.MS_TO_KPH if ui_state.is_metric else CV.MS_TO_MPH

def _speed_unit() -> str:
  return "km/h" if ui_state.is_metric else "mph"

def _distance_conversion() -> float:
  return 1.0 if ui_state.is_metric else CV.METER_TO_FOOT

def _distance_unit() -> str:
  return "m" if ui_state.is_metric else "ft"

def _to_display_distance(val_m: float) -> tuple[int, str]:
  return int(round(val_m * _distance_conversion())), _distance_unit()

def _env_truthy(name: str) -> bool:
  return os.getenv(name, "").lower() in {"1", "true", "yes", "on"}

def _to_display_speed(val: float) -> tuple[int, str]:
  return int(round(val * _speed_conversion())), _speed_unit()

def _get_val(msg: str, attr: str, default=None):
  return getattr(ui_state.sm[msg], attr, default) if _sm_valid(msg) else default


# --- Shared helpers ---

def _sm_valid(key: str) -> bool:
  return key in ui_state.sm.valid and ui_state.sm.valid[key]

def _calc_reduction(v_cruise: float, target: float) -> int:
  if v_cruise > 0.1 and target > 0.1 and target < v_cruise:
    return int(round((v_cruise - target) * _speed_conversion()))
  return 0

def _channels(color):
  """Extract (r, g, b, a) from either an rl.Color struct or a 4-tuple."""
  if hasattr(color, "r"):
    return color.r, color.g, color.b, color.a
  return color[0], color[1], color[2], color[3]

def _with_alpha(color, a: int) -> rl.Color:
  r, g, b, _ = _channels(color)
  return rl.Color(r, g, b, max(0, min(255, a)))

def _fade(color, alpha: float) -> rl.Color:
  r, g, b, a = _channels(color)
  return rl.Color(r, g, b, max(0, min(255, int(a * alpha))))

def _lerp_color(a, b, t: float) -> rl.Color:
  t = max(0.0, min(1.0, t))
  ar, ag, ab, _ = _channels(a)
  br, bg, bb, _ = _channels(b)
  return rl.Color(
    ar + int((br - ar) * t),
    ag + int((bg - ag) * t),
    ab + int((bb - ab) * t),
    255,
  )

def _pulse(freq: float) -> float:
  return 0.5 + 0.5 * math.sin(rl.get_time() * freq)

def _get_road_height(data: 'AetherGaugeData | None') -> float:
  is_curve = data.indicator_type == IndicatorType.ROAD_CURVE if data else False
  return ROAD_HEIGHT if is_curve else (45.0 * SCALE)

def _road_xy(distance: float, icx: float, bottom: float, data: 'AetherGaugeData', road_h: float | None = None) -> tuple[float, float, float]:
  t = max(0.0, min(1.0, _get_t_from_x(distance)))
  offset = _get_perspective_offset(t, data)
  h = road_h if road_h is not None else _get_road_height(data)
  return t, icx + offset, bottom - t * h

def _get_t_from_x(x: float) -> float:
  x_clamped = max(X_MIN, min(X_MAX, x))
  return (1.0 - X_MIN / x_clamped) / (1.0 - X_MIN / X_MAX)

def _get_perspective_offset(t: float, data: 'AetherGaugeData | None') -> float:
  curvature = 0.0
  if data and data.indicator_type == IndicatorType.ROAD_CURVE:
    curvature = data.indicator_value

  path_y_far = PATH_Y_FAR_SCALE * curvature
  max_offset_top = math.tanh(path_y_far * PERSPECTIVE_GAIN) * PERSPECTIVE_MAX_OFFSET
  return max_offset_top * (t ** PERSPECTIVE_EXPONENT)

def _draw_text_with_shadow(font: rl.Font, text: str, pos: rl.Vector2, size: int, color: rl.Color, alpha: float = 1.0):
  for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
    rl.draw_text_ex(font, text, rl.Vector2(pos.x + dx, pos.y + dy), size, 0, _fade(rl.BLACK, alpha))
  rl.draw_text_ex(font, text, pos, size, 0, _fade(color, alpha))


# --- Data model ---

class IndicatorType(Enum):
  NONE = "none"
  ROAD_CURVE = "road_curve"
  FORCE_STOP = "force_stop"
  STOP_LIGHT = "stop_light"
  LEAD = "lead"


@dataclass
class AetherGaugeData:
  text: str
  unit: str = ""
  color: rl.Color = rl.WHITE
  indicator_type: IndicatorType = IndicatorType.NONE
  indicator_value: float = 0.0
  indicator_extra: str = ""
  reduction_text: str = ""
  is_numeric: bool = False


# --- Source functions (replaces class-based sources) ---

def _build_curve_gauge_data(curvature: float, target_speed: float, v_cruise: float) -> AetherGaugeData:
  v_ego = _get_val("carState", "vEgo", 0.0)
  display_speed, unit = _to_display_speed(min(v_ego, target_speed) if target_speed > 0.1 else v_ego)
  reduction = _calc_reduction(v_cruise, target_speed)
  intensity = _intensity(curvature)
  severity_color = _glow_color(intensity)
  engagement_color = get_border_color(ui_state)
  curve_color = _lerp_color(severity_color, engagement_color, 0.35)

  return AetherGaugeData(
    text=str(display_speed),
    unit=unit,
    color=curve_color,
    indicator_type=IndicatorType.ROAD_CURVE,
    indicator_value=curvature,
    reduction_text=f"-{reduction}" if reduction > 0 else "",
    is_numeric=True,
  )


# --- Force stop ---

def _is_force_stop() -> bool:
  return _get_val("starpilotPlan", "forcingStop", False) and not _get_val("starpilotPlan", "redLight", False)

def _force_stop_data() -> AetherGaugeData:
  dist_m = _get_val("starpilotPlan", "forcingStopLength", 0.0)
  display_dist, unit = _to_display_distance(dist_m)
  return AetherGaugeData(
    text=str(display_dist), unit=unit, color=COLOR_FORCE_STOP,
    indicator_type=IndicatorType.FORCE_STOP, indicator_value=dist_m, is_numeric=True,
  )


# --- CEM: Stop light / stop sign ---

def _is_stop_light() -> bool:
  return _get_val("starpilotPlan", "experimentalMode", False) and _get_val("starpilotPlan", "redLight", False)

def _stop_light_data() -> AetherGaugeData:
  dist_m = _get_val("starpilotPlan", "forcingStopLength", 0.0)
  if dist_m == 0.0 and _sm_valid("modelV2"):
    model = ui_state.sm["modelV2"]
    if len(model.position.x) > 0:
      dist_m = model.position.x[min(32, len(model.position.x) - 1)]
  display_dist, unit = _to_display_distance(dist_m)
  return AetherGaugeData(
    text=str(display_dist), unit=unit, color=COLOR_FORCE_STOP,
    indicator_type=IndicatorType.STOP_LIGHT, indicator_value=dist_m,
    indicator_extra="red", is_numeric=True,
  )


# --- Curve speed source (CSC active) ---

def _is_curve_speed() -> bool:
  state = _csc_state()
  return state is not None and state['active']

def _curve_speed_data() -> AetherGaugeData:
  state = _csc_state()
  if state is None:
    return AetherGaugeData(text="")
  csc_speed = _get_val("starpilotPlan", "cscSpeed", 0.0)
  v_cruise = _get_val("starpilotPlan", "vCruise", 0.0)
  return _build_curve_gauge_data(state['curvature'], csc_speed, v_cruise)


# --- CEM: Curvature (non-CSC) ---

def _is_curvature() -> bool:
  return _get_val("starpilotPlan", "experimentalMode", False) and abs(_get_val("starpilotPlan", "roadCurvature", 0.0)) > 0.0012

def _curvature_data() -> AetherGaugeData:
  csc_speed = _get_val("starpilotPlan", "cscSpeed", 0.0)
  v_ego = _get_val("carState", "vEgo", 0.0)
  v_cruise = _get_val("starpilotPlan", "vCruise", v_ego)
  target_speed = csc_speed if csc_speed > 0.1 else v_cruise
  road_curvature = _get_val("starpilotPlan", "roadCurvature", 0.0)
  return _build_curve_gauge_data(road_curvature, target_speed, v_cruise)


# --- CEM: Lead vehicle (graphic only, no numeric) ---

def _is_lead() -> bool:
  return (_get_val("starpilotPlan", "experimentalMode", False)
          and _get_val("starpilotPlan", "trackingLead", False)
          and _sm_valid("radarState")
          and ui_state.sm["radarState"].leadOne.status)

def _lead_data() -> AetherGaugeData:
  lead = ui_state.sm["radarState"].leadOne
  is_stopped = lead.vLead < LEAD_STOPPED_SPEED_THRESHOLD
  return AetherGaugeData(
    text="STOPPED" if is_stopped else "SLOW",
    color=COLOR_LEAD_STOPPED if is_stopped else COLOR_LEAD_SLOWER,
    indicator_type=IndicatorType.LEAD, indicator_value=lead.dRel,
    indicator_extra="stopped" if is_stopped else "slower",
  )








# --- Test cycle source (debug only, module-level state) ---

_TEST_STATES = [
  (IndicatorType.ROAD_CURVE, "45", rl.Color(0, 255, 100, 255), 0.005, "", "-20"),
  (IndicatorType.STOP_LIGHT, "", COLOR_FORCE_STOP, 35.0, "red", ""),
  (IndicatorType.LEAD, "", COLOR_LEAD_SLOWER, 25.0, "slower", ""),
  (IndicatorType.LEAD, "", COLOR_LEAD_SLOWER, 15.0, "stopped", ""),
  (IndicatorType.FORCE_STOP, "", COLOR_FORCE_STOP, 12.0, "", ""),
]
_TEST_CYCLE_SEC = 6.0
CEM_DEMO = _env_truthy("SP_CEM_DEMO") or _env_truthy("SP_MICI_WIDGET_DEMO")

def _test_cycle_active() -> bool:
  return rl.get_time() > 3.0

def _test_cycle_data() -> AetherGaugeData:
  now = rl.get_time()
  elapsed = (now - 3.0) % _TEST_CYCLE_SEC
  idx = int((now - 3.0) / _TEST_CYCLE_SEC) % len(_TEST_STATES)
  ind_type, text, color, base_val, extra, reduction = _TEST_STATES[idx]
  anim_t = elapsed / max(0.001, _TEST_CYCLE_SEC - 0.5)

  if ind_type in (IndicatorType.STOP_LIGHT, IndicatorType.FORCE_STOP):
    ind_val = max(5.0, 60.0 - anim_t * 55.0)
    display_dist, unit = _to_display_distance(ind_val)
    return AetherGaugeData(text=str(display_dist), unit=unit, color=color,
      indicator_type=ind_type, indicator_value=ind_val,
      indicator_extra=extra, reduction_text=reduction, is_numeric=True)

  if ind_type == IndicatorType.LEAD:
    ind_val = max(3.0, 60.0 - anim_t * 57.0)
    is_stopped = extra == "stopped"
    text = "STOPPED" if is_stopped else "SLOW"
    color = COLOR_LEAD_STOPPED if is_stopped else COLOR_LEAD_SLOWER
    return AetherGaugeData(text=text, color=color,
      indicator_type=ind_type, indicator_value=ind_val,
      indicator_extra=extra, reduction_text=reduction)

  return AetherGaugeData(text=text, unit=_speed_unit(), color=color,
    indicator_type=ind_type, indicator_value=base_val,
    indicator_extra=extra, reduction_text=reduction, is_numeric=True)


def _cem_demo_active() -> bool:
  return CEM_DEMO and ui_state.conditional_status in {
    CEStatus["CURVATURE"],
    CEStatus["LEAD"],
    CEStatus["STOP_LIGHT"],
    CEStatus["SPEED"],
    CEStatus["SPEED_LIMIT"],
  }


def _cem_demo_data() -> AetherGaugeData:
  status = ui_state.conditional_status

  if status == CEStatus["CURVATURE"]:
    v_ego = _get_val("carState", "vEgo", 18.0)
    target_speed = max(8.0, v_ego * 0.72)
    v_cruise = max(target_speed + 4.0, _get_val("starpilotPlan", "vCruise", target_speed + 4.0))
    return _build_curve_gauge_data(0.005, target_speed, v_cruise)

  if status == CEStatus["LEAD"]:
    if _sm_valid("radarState") and ui_state.sm["radarState"].leadOne.status:
      return _lead_data()
    is_stopped = int(rl.get_time() / 1.0) % 2 == 0
    return AetherGaugeData(
      text="STOPPED" if is_stopped else "SLOW",
      color=COLOR_LEAD_STOPPED if is_stopped else COLOR_LEAD_SLOWER,
      indicator_type=IndicatorType.LEAD,
      indicator_value=12.0 if is_stopped else 24.0,
      indicator_extra="stopped" if is_stopped else "slower",
    )

  if status == CEStatus["STOP_LIGHT"]:
    phase = rl.get_time() % 2.0
    distance = max(6.0, 35.0 - phase * 12.0)
    display_dist, unit = _to_display_distance(distance)
    return AetherGaugeData(
      text=str(display_dist),
      unit=unit,
      color=COLOR_FORCE_STOP,
      indicator_type=IndicatorType.STOP_LIGHT,
      indicator_value=distance,
      indicator_extra="red",
      is_numeric=True,
    )

  v_ego = _get_val("carState", "vEgo", 20.0)
  display_speed, unit = _to_display_speed(max(8.0, v_ego * 0.85))
  return AetherGaugeData(
    text=str(display_speed),
    unit=unit,
    color=COLOR_CEM_SPEED,
    indicator_type=IndicatorType.ROAD_CURVE,
    indicator_value=0.0,
    is_numeric=True,
  )


# --- Main widget ---

class AetherGauge:
  def __init__(self):
    self._sources = [
      (_is_force_stop, _force_stop_data),
      (_is_stop_light, _stop_light_data),
      (_is_curve_speed, _curve_speed_data),
      (_is_curvature, _curvature_data),
      (_is_lead, _lead_data),
    ]
    if TEST_CYCLE:
      self._sources.insert(0, (_test_cycle_active, _test_cycle_data))
    if CEM_DEMO:
      self._sources.insert(0, (_cem_demo_active, _cem_demo_data))
    self._chevron_accum = 0.0
    self._lead_chevron_accum = 0.0
    self._active_priority = 999
    self._cached_data = None
    self._last_active_time = 0.0
    self._cooldown = 0.5
    self._road_h_filter = FirstOrderFilter(ROAD_HEIGHT, 0.06, 1 / gui_app.target_fps)
    self._current_road_h = ROAD_HEIGHT

  def has_active_source(self) -> bool:
    """Lightweight visibility check — no side effects, no data construction."""
    for is_active, _ in self._sources:
      if is_active():
        return True
    return False

  def get_active_data(self) -> AetherGaugeData | None:
    now = rl.get_time()
    best_priority = 999
    new_data = None
    
    for i, (is_active, get_data) in enumerate(self._sources):
      if is_active():
        best_priority = i
        new_data = get_data()
        break
        
    # Treat None as a priority 999 state: switch immediately if higher/equal priority,
    # or wait for cooldown to downgrade/hide.
    if best_priority <= self._active_priority or (now - self._last_active_time > self._cooldown):
      self._cached_data = new_data
      self._active_priority = best_priority
      self._last_active_time = now if new_data is not None else 0.0

    return self._cached_data

  def render(self, rect: rl.Rectangle, font_bold: rl.Font, font_medium: rl.Font, current_speed: float, cx: float | None = None, bottom: float | None = None, alpha: float = 1.0):
    data = self.get_active_data()
    if not data:
      return

    if cx is None or bottom is None:
      base_cx = rect.x + rect.width / 2
      cy_speed = rect.y + 180 * SCALE
      speed_text = str(round(current_speed))
      speed_text_size = measure_text_cached(font_bold, speed_text, int(176 * SCALE))
      icx = base_cx - speed_text_size.x / 2 - 70.0 * SCALE
      icy = cy_speed - 39.5 * SCALE
    else:
      icx = cx
      icy = bottom - ROAD_HALF_SIZE

    if data.indicator_type in (IndicatorType.ROAD_CURVE, IndicatorType.FORCE_STOP, IndicatorType.LEAD, IndicatorType.STOP_LIGHT):
      self._render_unified_road(rect, icx, icy, data, font_bold, font_medium, alpha)

  def _render_unified_road(self, rect, icx, icy, data, font_bold, font_medium, alpha=1.0):
    bottom = icy + ROAD_HALF_SIZE

    if data.indicator_type in (IndicatorType.FORCE_STOP, IndicatorType.STOP_LIGHT):
      distance = 15.0
    else:
      distance = data.indicator_value

    points_left = []
    points_right = []
    self._current_road_h = self._road_h_filter.update(_get_road_height(data))
    road_h = self._current_road_h

    for i in range(ROAD_SEGMENTS + 1):
      t = i / ROAD_SEGMENTS
      offset = _get_perspective_offset(t, data)
      cx_t = icx + offset
      y_t = bottom - t * road_h
      w_t = ROAD_W_BOTTOM - t * (ROAD_W_BOTTOM - ROAD_W_TOP)

      points_left.append(rl.Vector2(cx_t - w_t, y_t))
      points_right.append(rl.Vector2(cx_t + w_t, y_t))

    fill_color = _fade(_with_alpha(data.color, FILL_ALPHA), alpha)
    for i in range(ROAD_SEGMENTS):
      t = i / ROAD_SEGMENTS
      stroke = ROAD_THICKNESS * (1.0 - 0.6 * t)
      rl.draw_triangle(points_left[i], points_right[i], points_left[i+1], fill_color)
      rl.draw_triangle(points_right[i], points_right[i+1], points_left[i+1], fill_color)
      rl.draw_line_ex(points_left[i], points_left[i+1], stroke, _fade(COLOR_SHADOW, alpha))
      rl.draw_line_ex(points_right[i], points_right[i+1], stroke, _fade(COLOR_SHADOW, alpha))
      rl.draw_line_ex(points_left[i], points_left[i+1], stroke, _fade(data.color, alpha))
      rl.draw_line_ex(points_right[i], points_right[i+1], stroke, _fade(data.color, alpha))

    it = data.indicator_type

    if it in (IndicatorType.STOP_LIGHT, IndicatorType.FORCE_STOP):
      self._draw_stop_line(icx, bottom, distance, data, alpha)

    if it == IndicatorType.LEAD:
      self._draw_lead_car(icx, bottom, data, alpha)

    if it in (IndicatorType.ROAD_CURVE, IndicatorType.FORCE_STOP, IndicatorType.STOP_LIGHT):
      self._draw_standard_chevrons(icx, bottom, distance, data, alpha)

    if it == IndicatorType.STOP_LIGHT:
      self._draw_traffic_light(icx, icy, distance, data, alpha)

    if it == IndicatorType.FORCE_STOP:
      self._draw_approaching_stop_sign(icx, icy, bottom, distance, data, font_bold, alpha)

    self._draw_mini_cradle(icx, bottom, data, font_bold, font_medium, alpha)

  def _draw_stop_line(self, icx, bottom, distance, data, alpha=1.0):
    t, cx_line, cy_line = _road_xy(distance, icx, bottom, data, self._current_road_h)
    w_line = ROAD_W_BOTTOM - t * (ROAD_W_BOTTOM - ROAD_W_TOP)

    p_left = rl.Vector2(cx_line - w_line + ROAD_EDGE_INSET, cy_line)
    p_right = rl.Vector2(cx_line + w_line - ROAD_EDGE_INSET, cy_line)

    fade = 1.0 - t * 0.5
    glow_a = int(150 * fade)

    rl.draw_line_ex(p_left, p_right, max(3.0 * SCALE, 7.0 * SCALE * fade), _fade(_with_alpha(COLOR_STOP_LINE_GLOW, glow_a), alpha))
    rl.draw_line_ex(p_left, p_right, max(1.5 * SCALE, 3.5 * SCALE * fade), _fade(COLOR_STOP_LINE_CORE, alpha))

  def _draw_lead_car(self, icx, bottom, data, alpha=1.0):
    t_lead, cx_lead, cy_lead = _road_xy(6.5, icx, bottom, data, self._current_road_h)
    t_lead = max(0.15, min(0.85, t_lead))

    car_scale = 0.45 + (1.0 - t_lead) * 0.55
    W = 38.0 * SCALE * car_scale
    H = 22.0 * SCALE * car_scale

    is_stopped = data.indicator_extra == "stopped"
    is_slower = data.indicator_extra == "slower"

    if is_stopped:
      border_color = _fade(COLOR_LEAD_STOPPED, alpha)
    elif is_slower:
      border_color = _fade(_with_alpha(data.color, int(160 + 95 * _pulse(1.2))), alpha)
    else:
      border_color = _fade(data.color, alpha)

    # Car body: cabin and main body with high-contrast outlines
    for rect_args, corner_r, fill in [
      ((cx_lead - W * 0.3, cy_lead - H, W * 0.6, H * 0.45), 0.5, _fade(rl.Color(15, 15, 15, 240), alpha)),
      ((cx_lead - W / 2, cy_lead - H * 0.65, W, H * 0.55), 0.3, _fade(rl.Color(20, 20, 20, 240), alpha)),
    ]:
      r = rl.Rectangle(*rect_args)
      rl.draw_rectangle_rounded(r, corner_r, 4, fill)
      rl.draw_rectangle_rounded_lines_ex(r, corner_r, 4, 2.0, border_color)

    # Tail lights with radial bloom
    tl_w = max(4.0, W * 0.16)
    tl_h = max(2.5, H * 0.14)
    tl_y = int(cy_lead - H * 0.55)
    glow_y = int(cy_lead - H * 0.5)
    for tl_x, glow_x in [(int(cx_lead - W * 0.45), int(cx_lead - W * 0.38)),
                          (int(cx_lead + W * 0.3), int(cx_lead + W * 0.38))]:
      if is_stopped:
        pulse = _pulse(2.5)
        r_glow = int(W * 0.10 * (1.0 + 0.4 * pulse))
        rl.draw_circle(glow_x, glow_y, r_glow + 4, _fade(rl.Color(255, 30, 60, int(60 + 40 * pulse)), alpha))
        rl.draw_circle(glow_x, glow_y, r_glow, _fade(rl.Color(255, 30, 60, int(150 + 105 * pulse)), alpha))
        c_tl = _fade(rl.Color(255, 220, 220, 255), alpha)
      elif is_slower:
        pulse = _pulse(1.2)
        r_glow = int(W * 0.08 * (1.0 + 0.2 * pulse))
        rl.draw_circle(glow_x, glow_y, r_glow, _fade(rl.Color(255, 140, 30, int(100 + 80 * pulse)), alpha))
        c_tl = _fade(rl.Color(255, 160, 60, int(180 + 75 * pulse)), alpha)
      else:
        c_tl = _fade(COLOR_FORCE_STOP, alpha)
      rl.draw_rectangle(tl_x, tl_y, int(tl_w), int(tl_h), c_tl)

    # Wheels
    wheel_y = int(cy_lead - H * 0.1)
    wheel_w = int(W * 0.12)
    wheel_h = int(H * 0.1)
    wheel_c = _fade(rl.Color(10, 10, 10, 255), alpha)
    rl.draw_rectangle(int(cx_lead - W * 0.4), wheel_y, wheel_w, wheel_h, wheel_c)
    rl.draw_rectangle(int(cx_lead + W * 0.28), wheel_y, wheel_w, wheel_h, wheel_c)

    # Following chevrons (from lead car back toward viewer)
    dt = rl.get_frame_time()
    v_ego = _get_val("carState", "vEgo", 0.0)
    flow_speed_factor = min(1.8, v_ego * 0.08)
    self._lead_chevron_accum = (self._lead_chevron_accum + dt * flow_speed_factor * 1.8) % 1.0
    progress = self._lead_chevron_accum
    for i in range(2):
      t = t_lead * (1.0 - ((i + progress) / 2) % 1.0)

      cx_t = icx + _get_perspective_offset(t, data)
      road_h = self._current_road_h
      cy_t = bottom - t * road_h

      chevron_w = 14.0 * SCALE - t * 5.0 * SCALE
      chevron_thick = max(2.0 * SCALE, 4.0 * SCALE - t * 1.5 * SCALE)
      lx = cx_t - chevron_w
      rx = cx_t + chevron_w

      chev_a = max(0, min(255, int(data.color.a * (1.0 - t / t_lead) * math.sin(t / t_lead * math.pi))))
      c_color = _fade(_with_alpha(data.color, chev_a), alpha)

      rl.draw_line_ex(rl.Vector2(lx, cy_t - chevron_w * 0.5), rl.Vector2(cx_t, cy_t), chevron_thick, c_color)
      rl.draw_line_ex(rl.Vector2(rx, cy_t - chevron_w * 0.5), rl.Vector2(cx_t, cy_t), chevron_thick, c_color)

  def _draw_standard_chevrons(self, icx, bottom, distance, data, alpha=1.0):
    is_stop = data.indicator_type in (IndicatorType.FORCE_STOP, IndicatorType.STOP_LIGHT)
    dt = rl.get_frame_time()
    v_ego = _get_val("carState", "vEgo", 0.0)
    flow_speed_factor = min(1.5, v_ego * 0.08)
    self._chevron_accum = (self._chevron_accum + dt * flow_speed_factor * 1.5) % 1.0
    progress = self._chevron_accum
    t_stop = max(0.05, min(1.0, distance / STOP_DISTANCE_MAX)) if is_stop else 1.0
    max_t = t_stop if is_stop else 1.0

    for i in range(CHEVRON_COUNT):
      t = max_t - (i + progress) * CHEVRON_SPACING
      if t < 0.0 or t > max_t:
        continue

      t_next = min(max_t, t + CHEVRON_STEP)
      cx_t = icx + _get_perspective_offset(t, data)
      cx_next = icx + _get_perspective_offset(t_next, data)

      road_h = self._current_road_h
      cy_t = bottom - t * road_h
      cy_next = bottom - t_next * road_h

      dx = cx_next - cx_t
      dy = cy_next - cy_t
      len_v = math.hypot(dx, dy)
      dir_up_x, dir_up_y = (dx / len_v, dy / len_v) if len_v > 0.001 else (0.0, -1.0)

      dir_right_x = -dir_up_y
      dir_right_y = dir_up_x

      chevron_w = max(3.0 * SCALE, 18.0 * SCALE - t * 7.0 * SCALE)
      chevron_h = chevron_w * 0.6
      chevron_thick = max(2.5 * SCALE, 4.5 * SCALE - t * 2.0 * SCALE)

      lx = cx_t - dir_right_x * chevron_w + dir_up_x * chevron_h
      ly = cy_t - dir_right_y * chevron_w + dir_up_y * chevron_h
      rx = cx_t + dir_right_x * chevron_w + dir_up_x * chevron_h
      ry = cy_t + dir_right_y * chevron_w + dir_up_y * chevron_h

      alpha_factor = math.sin((t / max_t) * math.pi) if max_t > 0.01 else 0.0
      chev_a = max(0, min(255, int(data.color.a * alpha_factor)))
      chev_color = _fade(_with_alpha(data.color, chev_a), alpha)
      chev_shadow = _fade(rl.Color(0, 0, 0, int(chev_a * 0.5)), alpha)

      rl.draw_line_ex(rl.Vector2(lx, ly + 1.5), rl.Vector2(cx_t, cy_t + 1.5), chevron_thick, chev_shadow)
      rl.draw_line_ex(rl.Vector2(rx, ry + 1.5), rl.Vector2(cx_t, cy_t + 1.5), chevron_thick, chev_shadow)
      rl.draw_line_ex(rl.Vector2(lx, ly), rl.Vector2(cx_t, cy_t), chevron_thick, chev_color)
      rl.draw_line_ex(rl.Vector2(rx, ry), rl.Vector2(cx_t, cy_t), chevron_thick, chev_color)

  def _draw_traffic_light(self, icx, icy, distance, data, alpha=1.0):
    t_light, cx_light, cy_road = _road_xy(distance, icx, icy + ROAD_HALF_SIZE, data, self._current_road_h)
    s_light = 1.0 - t_light

    scale_light = 0.65 + (s_light ** 2.0) * 1.35
    cy_light = cy_road - 38.0 * SCALE * s_light
    width = 15.0 * SCALE * scale_light
    height = 36.0 * SCALE * scale_light

    rl.draw_rectangle_rounded(rl.Rectangle(cx_light - width/2, cy_light - height/2 + 1.5, width, height), 0.25, 4, _fade(rl.Color(0, 0, 0, 120), alpha))
    rect_housing = rl.Rectangle(cx_light - width/2, cy_light - height/2, width, height)
    rl.draw_rectangle_rounded(rect_housing, 0.25, 4, _fade(rl.Color(22, 22, 22, 255), alpha))
    rl.draw_rectangle_rounded_lines_ex(rect_housing, 0.25, 4, 1.5, _fade(rl.Color(100, 100, 100, 255), alpha))

    r_bulb = 3.2 * SCALE * scale_light
    active_light = data.indicator_extra if data.indicator_extra in ("red", "yellow", "green") else "red"

    bulbs = [
      (cy_light - 10.0 * SCALE * scale_light, "red", rl.Color(255, 30, 60, 255), rl.Color(50, 10, 15, 255)),
      (cy_light, "yellow", rl.Color(255, 200, 0, 255), rl.Color(50, 40, 0, 255)),
      (cy_light + 10.0 * SCALE * scale_light, "green", rl.Color(0, 255, 100, 255), rl.Color(0, 40, 15, 255)),
    ]
    for y, name, active_c, inactive_c in bulbs:
      if name == "red" and active_light == "red":
        glow_pulse = _pulse(1.5)
        rl.draw_circle_v(rl.Vector2(cx_light, y), r_bulb + 8.0 * SCALE * glow_pulse, _fade(rl.Color(255, 30, 60, 25), alpha))
        rl.draw_circle_v(rl.Vector2(cx_light, y), r_bulb + 4.0 * SCALE * glow_pulse, _fade(rl.Color(255, 30, 60, 60), alpha))
      c = _fade(active_c if active_light == name else inactive_c, alpha)
      rl.draw_circle_v(rl.Vector2(cx_light, y), r_bulb, c)

  def _draw_approaching_stop_sign(self, cx, icy, bottom, smoothed_distance, data, font_bold, alpha=1.0):
    t_stop_gauge = _get_t_from_x(smoothed_distance)
    smoothed_s = max(0.0, min(1.0, 1.0 - (smoothed_distance / STOP_DISTANCE_MAX)))

    offset_stop = _get_perspective_offset(t_stop_gauge, data) if data else 0.0
    cx_stop = cx + offset_stop

    road_h = self._current_road_h
    cy_road = bottom - t_stop_gauge * road_h
    y_sign = cy_road - 25.0 * SCALE * smoothed_s

    r_min = 12.0 * SCALE
    r_max = 28.0 * SCALE
    r_sign = r_min + (smoothed_s ** 2.0) * (r_max - r_min)

    shadow_alpha = int(min(140, r_sign * 10))
    rl.draw_poly(rl.Vector2(cx_stop, y_sign + 2.0), 8, r_sign, 22.5, _fade(rl.Color(0, 0, 0, shadow_alpha), alpha))
    rl.draw_poly(rl.Vector2(cx_stop, y_sign), 8, r_sign, 22.5, _fade(COLOR_FORCE_STOP, alpha))

    outline_t = max(1.5, min(2.5, r_sign * 0.08))
    outline_a = int(max(0, min(220, (r_sign - 5.0) * 20)))
    if outline_a > 20:
      for i in range(8):
        a1 = math.radians(22.5 + i * 45.0)
        a2 = math.radians(22.5 + ((i + 1) % 8) * 45.0)
        p1 = rl.Vector2(cx_stop + r_sign * math.cos(a1), y_sign + r_sign * math.sin(a1))
        p2 = rl.Vector2(cx_stop + r_sign * math.cos(a2), y_sign + r_sign * math.sin(a2))
        rl.draw_line_ex(p1, p2, outline_t, _fade(_with_alpha(COLOR_STOP_SIGN_OUTLINE, outline_a), alpha))

    if r_sign < 10.0 * SCALE:
      return
    stop_font_size = max(14, int(r_sign * 0.7))
    stop_txt_size = measure_text_cached(font_bold, "STOP", stop_font_size)
    rl.draw_text_ex(font_bold, "STOP", rl.Vector2(cx_stop - stop_txt_size.x / 2, y_sign - stop_txt_size.y / 2), stop_font_size, 0, _fade(rl.WHITE, alpha))

  def _draw_mini_cradle(self, cx, bottom, data, font_bold, font_medium, alpha=1.0):
    if not data.text:
      return

    if data.is_numeric:
      val_size = measure_text_cached(font_bold, data.text, int(50 * SCALE))
      val_pos = rl.Vector2(int(cx - val_size.x / 2), int(bottom + 6 * SCALE))
      _draw_text_with_shadow(font_bold, data.text, val_pos, int(50 * SCALE), data.color, alpha)

      accent_y = int(val_pos.y + val_size.y + 2 * SCALE)
      accent_w = int(val_size.x + 16 * SCALE)
      accent_x = int(cx - accent_w / 2)
      rl.draw_line_ex(
        rl.Vector2(accent_x, accent_y),
        rl.Vector2(accent_x + accent_w, accent_y),
        2.0 * SCALE,
        _fade(_with_alpha(data.color, 160), alpha),
      )

      if data.reduction_text:
        red_size = measure_text_cached(font_medium, data.reduction_text, int(22 * SCALE))
        red_pos = rl.Vector2(int(cx + val_size.x / 2 + 6 * SCALE), int(val_pos.y + val_size.y / 2 - red_size.y / 2))
        _draw_text_with_shadow(font_medium, data.reduction_text, red_pos, int(22 * SCALE), COLOR_REDUCTION, alpha)

      if data.unit:
        unit_size = measure_text_cached(font_medium, data.unit, int(20 * SCALE))
        unit_pos = rl.Vector2(int(cx - unit_size.x / 2), int(accent_y + 3 * SCALE))
        _draw_text_with_shadow(font_medium, data.unit, unit_pos, int(20 * SCALE), rl.Color(255, 255, 255, 180), alpha)
    else:
      val_size = measure_text_cached(font_bold, data.text, int(32 * SCALE))
      val_pos = rl.Vector2(int(cx - val_size.x / 2), int(bottom + 10 * SCALE))
      _draw_text_with_shadow(font_bold, data.text, val_pos, int(32 * SCALE), data.color, alpha)
