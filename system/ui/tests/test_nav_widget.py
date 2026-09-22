import pyray as rl
import pytest

from openpilot.system.ui.lib.application import MouseEvent, MousePos, gui_app
from openpilot.common.filter_simple import BounceFilter
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.nav_widget import NavBar, NavWidget, NAV_BAR_MARGIN, NAV_BAR_HEIGHT


class NavScreen(NavWidget):
  def _render(self, _):
    pass


class TransparentScreen(Widget):
  def _render(self, _):
    pass


@pytest.fixture
def viewport():
  return rl.Rectangle(0, 0, gui_app.width, gui_app.height)


@pytest.fixture
def screen(monkeypatch, viewport):
  monkeypatch.setattr(rl, "draw_rectangle_rec", lambda *_: None)
  monkeypatch.setattr(rl, "get_time", lambda: 10.0)
  monkeypatch.setattr(rl, "get_frame_time", lambda: 1 / 60)
  monkeypatch.setattr(gui_app, "_target_fps", 60)
  monkeypatch.setattr(gui_app, "_show_touches", False)
  monkeypatch.setattr(gui_app, "_mouse_events", [])
  screen = NavScreen()
  screen.set_rect(viewport)
  monkeypatch.setattr(screen._nav_bar, "render", lambda: None)
  return screen


def touch(monkeypatch, y, *, pressed=False, released=False):
  event = MouseEvent(MousePos(20, y), 0, pressed, released, not released, 10.0)
  monkeypatch.setattr(gui_app, "_mouse_events", [event])
  monkeypatch.setattr(gui_app, "_last_mouse_event", event)


def test_only_settled_opaque_navigation_covers_background(screen, viewport):
  assert screen.covers_background(viewport)
  assert not TransparentScreen().covers_background(viewport)

  class TransparentNav(NavScreen):
    def _layout(self):
      pass

  transparent = TransparentNav()
  transparent.set_rect(viewport)
  assert not transparent.covers_background(viewport)
  screen.set_visible(False)
  assert not screen.covers_background(viewport)


@pytest.mark.parametrize("x,y,width,height", [(1, 0, 1, 1), (0, 1, 1, 1), (0, 0, 0.5, 1), (0, 0, 1, 0.5)])
def test_partial_navigation_does_not_cover_background(screen, viewport, x, y, width, height):
  screen.set_rect(rl.Rectangle(x, y, viewport.width * width, viewport.height * height))
  assert not screen.covers_background(viewport)


@pytest.mark.parametrize("position,velocity", [(0.1, 0), (-0.1, 0), (0, 0.1), (0, -0.1)])
def test_bounce_keeps_background_visible(screen, viewport, position, velocity):
  screen._y_pos_filter.x = position
  screen._y_pos_filter.velocity.x = velocity
  assert not screen.covers_background(viewport)


def test_show_animation_keeps_background_until_settled(screen, viewport):
  shown = []
  screen.set_shown_callback(lambda: shown.append(True))
  screen.show_event()
  assert not screen.covers_background(viewport)
  for _ in range(300):
    screen.render(viewport)
    if screen.covers_background(viewport):
      break
  assert screen.covers_background(viewport)
  assert shown == [True]


def test_swipe_uncovers_background_before_first_moving_frame(monkeypatch, screen, viewport):
  touch(monkeypatch, 20, pressed=True)
  assert screen.covers_background(viewport)
  screen.render(viewport)
  assert screen.rect.y == 0

  touch(monkeypatch, 120)
  assert not screen.covers_background(viewport)
  screen.render(viewport)
  assert screen.rect.y > 0

  popped = []
  monkeypatch.setattr(gui_app, "pop_widget", lambda: popped.append(True))
  touch(monkeypatch, 120, released=True)
  screen.render(viewport)
  monkeypatch.setattr(gui_app, "_mouse_events", [])
  for _ in range(300):
    assert not screen.covers_background(viewport)
    screen.render(viewport)
    if popped:
      break
  assert popped == [True]


def test_cancelled_swipe_restores_culling_only_after_settling(monkeypatch, screen, viewport):
  touch(monkeypatch, 20, pressed=True)
  screen.render(viewport)
  touch(monkeypatch, 50)
  screen.render(viewport)
  touch(monkeypatch, 50, released=True)
  screen.render(viewport)
  assert not screen.covers_background(viewport)
  monkeypatch.setattr(gui_app, "_mouse_events", [])
  for _ in range(300):
    screen.render(viewport)
    if screen.covers_background(viewport):
      break
  assert screen.covers_background(viewport)
  assert screen.rect.y == 0


def test_programmatic_dismiss_uncovers_background_before_first_moving_frame(screen, viewport):
  screen.dismiss()
  assert not screen.covers_background(viewport)
  screen.render(viewport)
  assert screen.rect.y > 0


@pytest.mark.parametrize("fps", [20, 30, 60])
def test_show_animation_duration_tracks_elapsed_time(monkeypatch, screen, viewport, fps):
  monkeypatch.setattr(rl, "get_frame_time", lambda: 1 / fps)
  shown = []
  screen.set_shown_callback(lambda: shown.append(True))
  screen.show_event()
  for _frames in range(1, fps * 3):
    screen.render(viewport)
    if screen.covers_background(viewport):
      break

  assert screen.covers_background(viewport)
  assert screen._y_pos_filter.x == screen._y_pos_filter.velocity.x == 0
  assert _frames / fps == pytest.approx(35 / 60, abs=1 / fps)
  assert shown == [True]


@pytest.mark.parametrize("fps", [20, 30, 60])
def test_dismiss_animation_duration_tracks_elapsed_time(monkeypatch, screen, viewport, fps):
  monkeypatch.setattr(rl, "get_frame_time", lambda: 1 / fps)
  popped, dismissed, backed = [], [], []
  monkeypatch.setattr(gui_app, "pop_widget", lambda: popped.append(True))
  screen.set_back_callback(lambda: backed.append(True))
  screen.dismiss(lambda: dismissed.append(True))
  for _frames in range(1, fps * 3):
    screen.render(viewport)
    if popped:
      break

  assert _frames / fps == pytest.approx(13 / 60, abs=1 / fps)
  assert popped == dismissed == [True]
  assert not backed


def test_show_animation_retains_original_sixty_fps_motion(screen):
  reference = BounceFilter(gui_app.height, 0.1, 1 / 60, bounce=1)
  screen.show_event()
  for _ in range(20):
    reference.update(0.0)
    screen._update_state()
    assert screen._y_pos_filter.x == pytest.approx(reference.x)
    assert screen._y_pos_filter.velocity.x == pytest.approx(reference.velocity.x)


@pytest.mark.parametrize("fps", [20, 30, 60])
def test_navigation_bar_fade_tracks_elapsed_time(monkeypatch, screen, fps):
  monkeypatch.setattr(rl, "get_frame_time", lambda: 1 / fps)
  monkeypatch.setattr(rl, "draw_rectangle_rounded", lambda *_: None)
  monkeypatch.setattr(rl, "draw_rectangle_rounded_lines_ex", lambda *_: None)
  bar = NavBar()
  bar.set_alpha(0.0)
  for _ in range(fps // 2):
    bar._render(bar.rect)
  assert bar._alpha_filter.x == pytest.approx((1 - bar._alpha_filter.alpha) ** 30)


@pytest.mark.parametrize("fps", [20, 30, 60])
def test_navigation_bar_slide_tracks_elapsed_time(monkeypatch, screen, viewport, fps):
  monkeypatch.setattr(rl, "get_frame_time", lambda: 1 / fps)
  screen._nav_bar_y_filter.x = -NAV_BAR_MARGIN - NAV_BAR_HEIGHT
  for _ in range(fps // 2):
    screen.render(viewport)
  remaining = (1 - screen._nav_bar_y_filter.alpha) ** 30
  assert screen._nav_bar_y_filter.x == pytest.approx(NAV_BAR_MARGIN - (2 * NAV_BAR_MARGIN + NAV_BAR_HEIGHT) * remaining)


def test_long_frame_uses_bounded_spring_steps(monkeypatch, screen):
  screen.show_event()
  monkeypatch.setattr(rl, "get_frame_time", lambda: 0.1)
  screen._update_state()
  expected = screen._y_pos_filter.x, screen._y_pos_filter.velocity.x

  screen.show_event()
  monkeypatch.setattr(rl, "get_frame_time", lambda: 5.0)
  screen._update_state()
  assert (screen._y_pos_filter.x, screen._y_pos_filter.velocity.x) == pytest.approx(expected)


@pytest.mark.parametrize("elapsed", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_frame_duration_uses_default_step(monkeypatch, screen, elapsed):
  screen.show_event()
  screen._update_state()
  expected = screen._y_pos_filter.x, screen._y_pos_filter.velocity.x

  screen.show_event()
  monkeypatch.setattr(rl, "get_frame_time", lambda: elapsed)
  screen._update_state()
  assert (screen._y_pos_filter.x, screen._y_pos_filter.velocity.x) == pytest.approx(expected)
