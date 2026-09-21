import pyray as rl
import pytest

from openpilot.system.ui import widgets
from openpilot.system.ui.lib import scroll_panel2
from openpilot.system.ui.lib.application import MouseEvent, MousePos, gui_app
from openpilot.system.ui.widgets.scroller import _Scroller, _MiciScrollPanel


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

  def make(items=None, **kwargs):
    scroller = _Scroller(items if items is not None else [Item() for _ in range(8)],
                         scroll_indicator=False, edge_shadows=False, **kwargs)
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
@pytest.mark.parametrize("single_batch", [True, False])
def test_inertial_scroll_click_threshold_is_unchanged(make_scroller, speed, expected_clicks, single_batch):
  scroller = make_scroller()
  scroller.scroll_panel._state = scroll_panel2.ScrollState.AUTO_SCROLL
  scroller.scroll_panel._velocity = -speed

  if single_batch:
    batch(scroller, event(pressed=True), event(released=True, t=1.05))
  else:
    frame(scroller, pressed=True)
    frame(scroller, released=True, t=1.05)

  assert sum(item.clicks for item in scroller.items) == expected_clicks


def event(x=200, y=100, *, pressed=False, released=False, slot=0, t=1.0):
  return MouseEvent(MousePos(x, y), slot, pressed, released, not released, t)


def batch(scroller, *events):
  gui_app._mouse_events = list(events)
  scroller.render()


@pytest.mark.parametrize("horizontal", [True, False])
@pytest.mark.parametrize("single_batch", [True, False])
def test_drag_release_never_clicks(make_scroller, horizontal, single_batch):
  scroller = make_scroller(horizontal=horizontal)
  move = (lambda value, **kw: event(x=value, **kw)) if horizontal else (lambda value, **kw: event(y=value, **kw))
  start = 200 if horizontal else 100
  events = [move(start, pressed=True), move(start - 20, t=1.01), move(start - 40, t=1.21),
            move(start - 40, released=True, t=1.22)]
  if single_batch:
    batch(scroller, *events)
  else:
    batch(scroller, events[0])
    batch(scroller, *events[1:])

  assert sum(item.clicks for item in scroller.items) == 0
  assert not any(item.is_pressed for item in scroller.items)


@pytest.mark.parametrize("same_batch", [True, False])
@pytest.mark.parametrize("pc", [True, False])
def test_drag_then_tap_activates_only_the_tap(make_scroller, monkeypatch, same_batch, pc):
  scroller = make_scroller()
  monkeypatch.setattr(widgets, "PC", pc)
  batch(scroller, event(pressed=True))
  drag = [event(180, t=1.01), event(160, t=1.21), event(160, released=True, t=1.22)]
  tap = [event(160, pressed=True, t=1.30), event(160, released=True, t=1.35)]
  if same_batch:
    batch(scroller, *drag, *tap)
  else:
    batch(scroller, *drag)
    batch(scroller, *tap)

  assert sum(item.clicks for item in scroller.items) == 1


def test_tap_before_drag_in_same_batch_is_preserved(make_scroller):
  scroller = make_scroller()
  batch(scroller, event(pressed=True), event(released=True, t=1.05),
        event(pressed=True, t=1.10), event(180, t=1.12))

  assert sum(item.clicks for item in scroller.items) == 1
  assert scroller.scroll_panel.state == scroll_panel2.ScrollState.MANUAL_SCROLL


def test_batched_tap_cancels_programmatic_scroll(make_scroller):
  scroller = make_scroller()
  scroller.scroll_to(3, smooth=True)
  batch(scroller, event(pressed=True), event(released=True, t=1.05))

  assert not scroller.is_auto_scrolling
  assert sum(item.clicks for item in scroller.items) == 1


def test_secondary_touch_does_not_change_drag_or_velocity(make_scroller):
  scroller = make_scroller()
  batch(scroller, event(pressed=True), event(180, t=1.02))
  offset = scroller.scroll_panel.get_offset()
  batch(scroller, event(400, slot=1, pressed=True, t=1.025), event(160, t=1.04),
        event(420, slot=1, t=1.045), event(420, slot=1, released=True, t=1.05))

  assert scroller.scroll_panel.state == scroll_panel2.ScrollState.MANUAL_SCROLL
  assert scroller.scroll_panel.get_offset() == pytest.approx(offset - 20)
  assert scroller.scroll_panel._velocity == pytest.approx(-1000)


def test_secondary_touch_does_not_cancel_primary_tap(make_scroller):
  scroller = make_scroller()
  batch(scroller, event(pressed=True), event(400, slot=1, pressed=True, t=1.01),
        event(400, slot=1, released=True, t=1.02), event(released=True, t=1.05))

  assert sum(item.clicks for item in scroller.items) == 1


def test_outside_press_does_not_capture_coasting_panel(make_scroller):
  scroller = make_scroller()
  panel = scroller.scroll_panel
  panel._state = scroll_panel2.ScrollState.AUTO_SCROLL
  panel._velocity = -500
  offset = panel.get_offset()
  batch(scroller, event(600, pressed=True), event(200, t=1.01), event(200, released=True, t=1.02))

  assert panel.state == scroll_panel2.ScrollState.AUTO_SCROLL
  assert panel.get_offset() == pytest.approx(offset - 500 / 60)
  assert sum(item.clicks for item in scroller.items) == 0


def test_outside_press_does_not_clear_snap_target(make_scroller):
  scroller = make_scroller()
  panel = scroller.scroll_panel
  panel._state = scroll_panel2.ScrollState.AUTO_SCROLL
  panel.snap_interval = 100
  panel._snap_target = -600
  batch(scroller, event(600, pressed=True))

  assert panel._snap_target == -600
  assert panel.state == scroll_panel2.ScrollState.AUTO_SCROLL


def test_release_crossing_drag_threshold_does_not_leave_drag_active(make_scroller):
  scroller = make_scroller()
  batch(scroller, event(pressed=True), event(160, released=True, t=1.05))

  assert sum(item.clicks for item in scroller.items) == 0
  assert scroller.scroll_panel.state == scroll_panel2.ScrollState.STEADY
  batch(scroller, event(pressed=True, t=1.10), event(released=True, t=1.15))
  assert sum(item.clicks for item in scroller.items) == 1


def test_disabling_scrolling_preserves_control_taps(make_scroller):
  scroller = make_scroller()
  scroller.set_scrolling_enabled(False)
  offset = scroller.scroll_panel.get_offset()
  batch(scroller, event(pressed=True), event(released=True, t=1.05))

  assert sum(item.clicks for item in scroller.items) == 1
  assert scroller.scroll_panel.get_offset() == offset


@pytest.mark.parametrize("restart", ["show", "enable"])
def test_interrupted_drag_does_not_poison_next_tap(make_scroller, restart):
  scroller = make_scroller()
  batch(scroller, event(pressed=True), event(180, t=1.02))
  if restart == "show":
    scroller.set_reset_scroll_at_show(False)
    scroller.hide_event()
    scroller.show_event()
  else:
    scroller.set_enabled(False)
    batch(scroller)
    scroller.set_enabled(True)
  batch(scroller, event(pressed=True, t=1.10), event(released=True, t=1.15))

  assert sum(item.clicks for item in scroller.items) == 1


def test_mici_panel_is_not_used_by_shared_panel_callers(make_scroller):
  assert isinstance(make_scroller().scroll_panel, _MiciScrollPanel)
  # Shared callers retain the original event handling, not Mici's slot filter.
  panel = scroll_panel2.GuiScrollPanel2()
  gui_app._mouse_events = [event(slot=1, pressed=True)]
  panel.update(rl.Rectangle(0, 0, 536, 240), 1000)
  assert panel.state == scroll_panel2.ScrollState.PRESSED


@pytest.mark.parametrize("kind", ["wifi", "bluetooth"])
def test_nested_forget_button_rejects_swipe_and_accepts_next_tap(make_scroller, monkeypatch, kind):
  from openpilot.selfdrive.ui.mici.layouts.settings.network.wifi_ui import WifiButton
  from openpilot.selfdrive.ui.mici.layouts.settings.bluetooth import BluetoothDeviceButton

  cls = WifiButton if kind == "wifi" else BluetoothDeviceButton
  button = object.__new__(cls)
  widgets.Widget.__init__(button)
  button.set_rect(rl.Rectangle(0, 0, 402, 180))
  button._grow_animation_until = None
  button._shake_start = None
  button._forget_btn = Item()
  # Exercise the real callback forwarding and touch dispatch without network
  # services or drawing; use the full card as the nested button's hit area.
  monkeypatch.setattr(button, "_update_state", lambda: None)
  monkeypatch.setattr(button, "_render", lambda rect: button._forget_btn.render(rect))
  monkeypatch.setattr(button, "_handle_mouse_release", lambda pos: None)
  scroller = make_scroller(items=[Item(), button] + [Item() for _ in range(6)])
  batch(scroller, event(pressed=True))
  batch(scroller, event(180, t=1.01), event(160, t=1.21), event(160, released=True, t=1.22))
  assert button._forget_btn.clicks == 0

  batch(scroller, event(160, pressed=True, t=1.30), event(160, released=True, t=1.35))
  assert button._forget_btn.clicks == 1


@pytest.mark.parametrize("tap_after_drag", [False, True])
def test_option_picker_uses_event_cancellation(make_scroller, monkeypatch, tap_after_drag):
  from openpilot.selfdrive.ui.mici.widgets.dialog import BigMultiOptionDialog
  from openpilot.system.ui.widgets.nav_widget import NavWidget

  scroller = make_scroller()
  dialog = object.__new__(BigMultiOptionDialog)
  widgets.Widget.__init__(dialog)
  dialog.set_rect(scroller.rect)
  dialog._scroll_inner = scroller
  dialog._selected_option = "option"
  scroller.items[0].option = "option"
  selections = []
  monkeypatch.setattr(dialog, "_on_option_selected", selections.append)
  monkeypatch.setattr(NavWidget, "_handle_mouse_event", lambda *args: None)
  gui_app._mouse_events = [event(pressed=True)]
  scroller.render()
  dialog._process_mouse_events()
  gui_app._mouse_events = [event(180, t=1.01), event(160, t=1.21), event(160, released=True, t=1.22)]
  if tap_after_drag:
    gui_app._mouse_events += [event(160, pressed=True, t=1.30), event(160, released=True, t=1.35)]
  scroller.render()
  dialog._process_mouse_events()

  assert selections == (["option"] if tap_after_drag else [])


@pytest.mark.parametrize("guard", ["disabled", "moving", "original_callback", "original_event_callback"])
def test_existing_item_guards_still_reject_taps(make_scroller, monkeypatch, guard):
  items = [Item() for _ in range(8)]
  if guard == "original_callback":
    items[1].set_touch_valid_callback(lambda: False)
  elif guard == "original_event_callback":
    items[1].set_touch_event_valid_callback(lambda ev: False)
  scroller = make_scroller(items=items)
  if guard == "disabled":
    items[1].set_enabled(False)
  elif guard == "moving":
    monkeypatch.setattr(rl, "draw_rectangle_rec", lambda *args: None)
    scroller.move_item(1, 2)
  batch(scroller, event(pressed=True), event(released=True, t=1.05))

  assert sum(item.clicks for item in items) == 0


@pytest.mark.parametrize("horizontal", [True, False])
def test_nav_scroller_swipe_to_dismiss_still_works(make_scroller, horizontal):
  from openpilot.system.ui.widgets.scroller import NavScroller, NavRawScrollPanel

  class RawPanel(NavRawScrollPanel):
    def _render(self, _):
      pass

  nav = NavScroller() if horizontal else RawPanel()
  nav.set_rect(rl.Rectangle(0, 0, 536, 240))
  if horizontal:
    nav._scroller._show_scroll_indicator = False
    nav._scroller._edge_shadows = False
    nav._scroller.add_widgets([Item() for _ in range(8)])
  for ev in (event(y=50, pressed=True), event(y=150, t=1.1), event(y=150, released=True, t=1.15)):
    gui_app._mouse_events = [ev]
    # Same child-before-parent dispatch order as rendering, without drawing.
    if horizontal:
      nav._scroller.render(nav.rect)
    else:
      nav._scroll_panel.update(nav.rect, 1000)
    nav._process_mouse_events()

  assert nav._playing_dismiss_animation
  if horizontal:
    assert sum(item.clicks for item in nav._scroller.items) == 0
