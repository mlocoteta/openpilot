import pyray as rl
import pytest

from openpilot.system.ui import widgets
from openpilot.system.ui.lib import scroll_panel2
from openpilot.system.ui.lib.application import MouseEvent, MousePos, gui_app
from openpilot.system.ui.widgets.scroller import _Scroller


class Item(widgets.Widget):
  def __init__(self):
    super().__init__()
    self.set_rect(rl.Rectangle(0, 0, 402, 180))
    self.clicks = 0
    self.set_click_callback(self._clicked)

  def _clicked(self):
    self.clicks += 1

  def _render(self, _):
    pass


@pytest.fixture
def make_scroller(monkeypatch):
  monkeypatch.setattr(rl, "begin_scissor_mode", lambda *args: None)
  monkeypatch.setattr(rl, "end_scissor_mode", lambda: None)
  monkeypatch.setattr(rl, "get_frame_time", lambda: 1 / 60)
  monkeypatch.setattr(rl, "get_time", lambda: 1.0)
  monkeypatch.setattr(rl, "get_mouse_wheel_move", lambda: 0)
  monkeypatch.setattr(gui_app, "texture", lambda *args: rl.Texture())
  monkeypatch.setattr(gui_app, "_show_touches", False)
  monkeypatch.setattr(gui_app, "_mouse_events", [])
  monkeypatch.setattr(widgets, "PC", False)
  monkeypatch.setattr(widgets.device, "awake", True)
  monkeypatch.setattr(scroll_panel2, "TICI", True)

  def make(**kwargs):
    scroller = _Scroller([Item() for _ in range(8)], scroll_indicator=False, edge_shadows=False, **kwargs)
    scroller.set_rect(rl.Rectangle(0, 0, 536, 240))
    scroller.scroll_panel.set_offset(-500)
    scroller.render()
    return scroller

  return make


def frame(scroller, *, pressed=False, released=False, pos=(200, 100), t=1.0):
  gui_app._mouse_events = [MouseEvent(MousePos(*pos), 0, pressed, released, not released, t)]
  scroller.render()


def test_tap_interrupts_programmatic_scroll_tail(make_scroller):
  scroller = make_scroller()
  scroller.scroll_to(3, smooth=True)
  frame(scroller, pressed=True)
  frame(scroller, released=True, t=1.05)

  assert not scroller.is_auto_scrolling
  assert sum(item.clicks for item in scroller.items) == 1


def test_blocking_programmatic_scroll_still_rejects_taps(make_scroller):
  scroller = make_scroller()
  scroller.scroll_to(30, smooth=True, block_interaction=True)
  frame(scroller, pressed=True)
  frame(scroller, released=True, t=1.05)

  assert scroller.is_auto_scrolling
  assert sum(item.clicks for item in scroller.items) == 0


@pytest.mark.parametrize("horizontal", [True, False])
def test_touch_down_immediately_stops_snapping(make_scroller, horizontal):
  scroller = make_scroller(snap_items=True, horizontal=horizontal)
  offset = scroller.scroll_panel.get_offset()

  frame(scroller, pressed=True)

  assert scroller.scroll_panel.state == scroll_panel2.ScrollState.PRESSED
  assert scroller.scroll_panel.get_offset() == offset


def test_drag_outside_viewport_does_not_resume_snapping(make_scroller):
  scroller = make_scroller(snap_items=True)
  frame(scroller, pressed=True)
  frame(scroller, pos=(180, 100), t=1.02)
  frame(scroller, pos=(160, 250), t=1.04)
  offset = scroller.scroll_panel.get_offset()

  frame(scroller, pos=(140, 250), t=1.06)

  assert scroller.scroll_panel.state == scroll_panel2.ScrollState.MANUAL_SCROLL
  assert scroller.scroll_panel.get_offset() == pytest.approx(offset - 20)


@pytest.mark.parametrize("speed, expected_clicks", [(25, 1), (119, 1), (121, 0)])
def test_inertial_scroll_click_threshold_is_unchanged(make_scroller, speed, expected_clicks):
  scroller = make_scroller()
  scroller.scroll_panel._state = scroll_panel2.ScrollState.AUTO_SCROLL
  scroller.scroll_panel._velocity = -speed

  frame(scroller, pressed=True)
  frame(scroller, released=True, t=1.05)

  assert sum(item.clicks for item in scroller.items) == expected_clicks
