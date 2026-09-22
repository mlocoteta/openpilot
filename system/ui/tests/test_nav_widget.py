import pyray as rl
import pytest

from openpilot.system.ui.lib.application import MouseEvent, MousePos, gui_app
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.nav_widget import NavWidget


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
