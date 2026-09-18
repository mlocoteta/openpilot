import abc
import math
import pyray as rl
from typing import Union, cast
from collections.abc import Callable
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.nav_widget import NavWidget
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.widgets.mici_keyboard import MiciKeyboard
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.lib.application import gui_app, FontWeight, MousePos, MouseEvent
from openpilot.system.ui.widgets.scroller import Scroller
from openpilot.system.ui.widgets.slider import RedBigSlider, BigSlider
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui.mici.widgets.button import BigCircleButton, BigButton, GreyBigButton
from openpilot.selfdrive.ui.mici.widgets.side_button import SideButton

DEBUG = False

PADDING = 20


class BigDialogBase(NavWidget, abc.ABC):
  def __init__(self):
    super().__init__()
    self.set_rect(rl.Rectangle(0, 0, gui_app.width, gui_app.height))


class BigDialog(BigDialogBase):
  def __init__(self, title: str, description: str, icon: Union[rl.Texture, None] = None):
    super().__init__()
    self._card = GreyBigButton(title, description, icon)

  def _render(self, _):
    self._card.render(rl.Rectangle(
      self._rect.x + self._rect.width / 2 - self._card.rect.width / 2,
      self._rect.y + self._rect.height / 2 - self._card.rect.height / 2,
      self._card.rect.width,
      self._card.rect.height,
    ))


class BigConfirmationDialog(BigDialogBase):
  def __init__(self, title: str, icon: rl.Texture, confirm_callback: Callable[[], None],
               exit_on_confirm: bool = True, red: bool = False):
    super().__init__()
    self._confirm_callback = confirm_callback
    self._exit_on_confirm = exit_on_confirm

    self._slider: BigSlider | RedBigSlider
    if red:
      self._slider = self._child(RedBigSlider(title, icon, confirm_callback=self._on_confirm))
    else:
      self._slider = self._child(BigSlider(title, icon, confirm_callback=self._on_confirm))
    self._slider.set_enabled(lambda: self.enabled and not self.is_dismissing)  # for nav stack + NavWidget

  def _on_confirm(self):
    if self._exit_on_confirm:
      self.dismiss(self._confirm_callback)
    elif self._confirm_callback:
      self._confirm_callback()

  def _update_state(self):
    super()._update_state()
    if self.is_dismissing and not self._slider.confirmed:
      self._slider.reset()

  def _render(self, _):
    self._slider.render(self._rect)


class BigInputDialog(BigDialogBase):
  BACK_TOUCH_AREA_PERCENTAGE = 0.2
  BACKSPACE_RATE = 25  # hz
  TEXT_INPUT_SIZE = 35

  def __init__(self,
               hint: str,
               default_text: str = "",
               minimum_length: int = 1,
               confirm_callback: Callable[[str], None] | None = None,
               auto_return_to_letters: str = ""):
    super().__init__()
    self._hint_label = UnifiedLabel(hint, font_size=35, text_color=rl.Color(255, 255, 255, int(255 * 0.35)),
                                    font_weight=FontWeight.MEDIUM)
    self._keyboard = MiciKeyboard(auto_return_to_letters=auto_return_to_letters)
    self._keyboard.set_text(default_text)
    self._keyboard.set_enabled(lambda: self.enabled and not self.is_dismissing)  # for nav stack + NavWidget
    self._minimum_length = minimum_length

    self._backspace_held_time: float | None = None

    self._backspace_img = gui_app.texture("icons_mici/settings/keyboard/backspace.png", 42, 36)
    self._backspace_img_alpha = FirstOrderFilter(0, 0.05, 1 / gui_app.target_fps)

    self._enter_img = gui_app.texture("icons_mici/settings/keyboard/enter.png", 76, 62)
    self._enter_disabled_img = gui_app.texture("icons_mici/settings/keyboard/enter_disabled.png", 76, 62)
    self._enter_img_alpha = FirstOrderFilter(0, 0.05, 1 / gui_app.target_fps)

    # rects for top buttons
    self._top_left_button_rect = rl.Rectangle(0, 0, 0, 0)
    self._top_right_button_rect = rl.Rectangle(0, 0, 0, 0)

    def confirm_callback_wrapper():
      text = self._keyboard.text()
      self.dismiss((lambda: confirm_callback(text)) if confirm_callback else None)
    self._confirm_callback = confirm_callback_wrapper

  def _update_state(self):
    super()._update_state()

    if self.is_dismissing:
      self._backspace_held_time = None
      return

    last_mouse_event = gui_app.last_mouse_event
    if last_mouse_event.left_down and rl.check_collision_point_rec(last_mouse_event.pos, self._top_right_button_rect) and self._backspace_img_alpha.x > 1:
      if self._backspace_held_time is None:
        self._backspace_held_time = rl.get_time()

      if rl.get_time() - self._backspace_held_time > 0.5:
        if gui_app.frame % round(gui_app.target_fps / self.BACKSPACE_RATE) == 0:
          self._keyboard.backspace()

    else:
      self._backspace_held_time = None

  def _render(self, _):
    # draw current text so far below everything. text floats left but always stays in view
    text = self._keyboard.text()
    candidate_char = self._keyboard.get_candidate_character()
    text_size = measure_text_cached(gui_app.font(FontWeight.ROMAN), text + candidate_char or self._hint_label.text, self.TEXT_INPUT_SIZE)

    bg_block_margin = 5
    text_x = PADDING / 2 + self._enter_img.width + PADDING
    text_field_rect = rl.Rectangle(text_x, self._rect.y + PADDING - bg_block_margin,
                                   self._rect.width - text_x * 2,
                                   text_size.y)

    # draw text input
    # push text left with a gradient on left side if too long
    if text_size.x > text_field_rect.width:
      text_x -= text_size.x - text_field_rect.width

    rl.begin_scissor_mode(int(text_field_rect.x), int(text_field_rect.y), int(text_field_rect.width), int(text_field_rect.height))
    rl.draw_text_ex(gui_app.font(FontWeight.ROMAN), text, rl.Vector2(text_x, text_field_rect.y), self.TEXT_INPUT_SIZE, 0, rl.WHITE)

    # draw grayed out character user is hovering over
    if candidate_char:
      candidate_char_size = measure_text_cached(gui_app.font(FontWeight.ROMAN), candidate_char, self.TEXT_INPUT_SIZE)
      rl.draw_text_ex(gui_app.font(FontWeight.ROMAN), candidate_char,
                      rl.Vector2(min(text_x + text_size.x, text_field_rect.x + text_field_rect.width) - candidate_char_size.x, text_field_rect.y),
                      self.TEXT_INPUT_SIZE, 0, rl.Color(255, 255, 255, 128))

    rl.end_scissor_mode()

    # draw gradient on left side to indicate more text
    if text_size.x > text_field_rect.width:
      rl.draw_rectangle_gradient_ex(rl.Rectangle(text_field_rect.x, text_field_rect.y, 80, text_field_rect.height),
                                    rl.BLACK, rl.BLANK, rl.BLANK, rl.BLACK)

    # draw cursor
    blink_alpha = (math.sin(rl.get_time() * 6) + 1) / 2
    if text:
      cursor_x = min(text_x + text_size.x + 3, text_field_rect.x + text_field_rect.width)
    else:
      cursor_x = text_field_rect.x - 6
    rl.draw_rectangle_rounded(rl.Rectangle(cursor_x, text_field_rect.y, 4, text_size.y),
                              1, 4, rl.Color(255, 255, 255, int(255 * blink_alpha)))

    # draw backspace icon with nice fade
    self._backspace_img_alpha.update(255 * bool(text))
    if self._backspace_img_alpha.x > 1:
      color = rl.Color(255, 255, 255, int(self._backspace_img_alpha.x))
      rl.draw_texture_ex(self._backspace_img, rl.Vector2(self._rect.width - self._backspace_img.width - 27, self._rect.y + 14), 0.0, 1.0, color)

    if not text and self._hint_label.text and not candidate_char:
      # draw description if no text entered yet and not drawing candidate char
      hint_rect = rl.Rectangle(text_field_rect.x, text_field_rect.y,
                               self._rect.width - text_field_rect.x - PADDING,
                               text_field_rect.height)
      self._hint_label.render(hint_rect)

    # TODO: move to update state
    # make rect take up entire area so it's easier to click
    self._top_left_button_rect = rl.Rectangle(self._rect.x, self._rect.y, text_field_rect.x, self._rect.height - self._keyboard.get_keyboard_height())
    self._top_right_button_rect = rl.Rectangle(text_field_rect.x + text_field_rect.width, self._rect.y,
                                               self._rect.width - (text_field_rect.x + text_field_rect.width), self._top_left_button_rect.height)

    # draw enter button
    self._enter_img_alpha.update(255 if len(text) >= self._minimum_length else 0)
    color = rl.Color(255, 255, 255, int(self._enter_img_alpha.x))
    rl.draw_texture_ex(self._enter_img, rl.Vector2(self._rect.x + PADDING / 2, self._rect.y), 0.0, 1.0, color)
    color = rl.Color(255, 255, 255, 255 - int(self._enter_img_alpha.x))
    rl.draw_texture_ex(self._enter_disabled_img, rl.Vector2(self._rect.x + PADDING / 2, self._rect.y), 0.0, 1.0, color)

    # keyboard goes over everything
    self._keyboard.render(self._rect)

    # draw debugging rect bounds
    if DEBUG:
      rl.draw_rectangle_lines_ex(text_field_rect, 1, rl.Color(100, 100, 100, 255))
      rl.draw_rectangle_lines_ex(self._top_right_button_rect, 1, rl.Color(0, 255, 0, 255))
      rl.draw_rectangle_lines_ex(self._top_left_button_rect, 1, rl.Color(0, 255, 0, 255))

  def _handle_mouse_press(self, mouse_pos: MousePos):
    super()._handle_mouse_press(mouse_pos)
    # TODO: need to track where press was so enter and back can activate on release rather than press
    #  or turn into icon widgets :eyes_open:

    if self.is_dismissing:
      return

    # handle backspace icon click
    if rl.check_collision_point_rec(mouse_pos, self._top_right_button_rect) and self._backspace_img_alpha.x > 254:
      self._keyboard.backspace()
    elif rl.check_collision_point_rec(mouse_pos, self._top_left_button_rect) and self._enter_img_alpha.x > 254:
      # handle enter icon click
      self._confirm_callback()


class BigDialogButton(BigButton):
  def __init__(self, text: str, value: str = "", icon: Union[str, rl.Texture] = "", description: str = ""):
    super().__init__(text, value, icon)
    self._description = description

  def _handle_mouse_release(self, mouse_pos: MousePos):
    super()._handle_mouse_release(mouse_pos)

    dlg = BigDialog(self.text, self._description)
    gui_app.push_widget(dlg)


class BigConfirmationCircleButton(BigCircleButton):
  def __init__(self, title: str, icon: rl.Texture, confirm_callback: Callable[[], None], exit_on_confirm: bool = True,
               red: bool = False, icon_offset: tuple[int, int] = (0, 0)):
    super().__init__(icon, red, icon_offset)

    def show_confirm_dialog():
      gui_app.push_widget(BigConfirmationDialog(title, icon, confirm_callback,
                                                exit_on_confirm=exit_on_confirm, red=red))

    self.set_click_callback(show_confirm_dialog)


class BigDialogOptionButton(Widget):
  HEIGHT = 64
  SELECTED_HEIGHT = 74

  def __init__(self, option: str):
    super().__init__()
    self.option = option
    self.set_rect(rl.Rectangle(0, 0, int(gui_app.width / 2 + 220), self.HEIGHT))
    self._selected = False
    self._label = UnifiedLabel(
      option,
      font_size=70,
      text_color=rl.Color(255, 255, 255, int(255 * 0.58)),
      font_weight=FontWeight.DISPLAY_REGULAR,
      alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE,
      scroll=True,
    )

  def show_event(self):
    super().show_event()
    self._label.reset_scroll()

  def set_selected(self, selected: bool):
    self._selected = selected
    self._rect.height = self.SELECTED_HEIGHT if selected else self.HEIGHT

  def _render(self, _):
    if self._selected:
      self._label.set_font_size(self.SELECTED_HEIGHT)
      self._label.set_color(rl.Color(255, 255, 255, int(255 * 0.9)))
      self._label.set_font_weight(FontWeight.DISPLAY)
    else:
      self._label.set_font_size(self.HEIGHT)
      self._label.set_color(rl.Color(255, 255, 255, int(255 * 0.58)))
      self._label.set_font_weight(FontWeight.DISPLAY_REGULAR)

    self._label.render(self._rect)


class BigMultiOptionDialog(NavWidget):
  BACK_TOUCH_AREA_PERCENTAGE = 0.25

  def __init__(self, options: list[str], default: str | None,
               right_btn: str | None = "check", right_btn_callback: Callable[[], None] | None = None):
    super().__init__()
    self._options = options
    if default not in options:
      default = options[0] if options else None

    self._right_btn_callback = right_btn_callback
    self._default_option: str | None = default
    self._selected_option: str = self._default_option or (options[0] if options else "")
    self._last_selected_option: str = self._selected_option
    self._can_click = True

    self._scroller = self._child(Scroller(horizontal=False, pad=100, spacing=0, snap_items=True,
                                          scroll_indicator=False, edge_shadows=False))
    self._scroll_inner = self._scroller._scroller

    self._right_btn = self._child(SideButton(right_btn or "check")) if right_btn is not None else None
    if self._right_btn is not None:
      self._right_btn.set_click_callback(self._confirm_selection)
      self._scroller.set_enabled(lambda: self.enabled and not self.is_dismissing and not self._right_btn.is_pressed)
    else:
      self._scroller.set_enabled(lambda: self.enabled and not self.is_dismissing)

    for option in options:
      self._scroll_inner.add_widget(BigDialogOptionButton(option))

  def show_event(self):
    super().show_event()
    if self._default_option is not None:
      self._on_option_selected(self._default_option)

  def get_selected_option(self) -> str:
    return self._selected_option

  def _confirm_selection(self):
    self.dismiss(self._right_btn_callback)

  def _on_option_selected(self, option: str):
    y_pos = 0.0
    for btn in self._scroll_inner.items:
      btn = cast(BigDialogOptionButton, btn)
      if btn.option == option:
        rect_center_y = self._rect.y + self._rect.height / 2
        if btn._selected:
          height = btn.rect.height
        else:
          btn_center_y = btn.rect.y + btn.rect.height / 2
          height_offset = BigDialogOptionButton.SELECTED_HEIGHT - BigDialogOptionButton.HEIGHT
          height = (BigDialogOptionButton.HEIGHT - height_offset) if rect_center_y < btn_center_y else BigDialogOptionButton.SELECTED_HEIGHT
        y_pos = rect_center_y - (btn.rect.y + height / 2)
        break

    self._scroll_inner.scroll_to(-y_pos)

  def _selected_option_changed(self):
    pass

  def _handle_mouse_press(self, mouse_pos: MousePos):
    super()._handle_mouse_press(mouse_pos)
    self._can_click = True

  def _handle_mouse_event(self, mouse_event: MouseEvent) -> None:
    super()._handle_mouse_event(mouse_event)
    if not self._scroll_inner.scroll_panel.is_event_touch_valid(mouse_event):
      self._can_click = False

  def _handle_mouse_release(self, mouse_pos: MousePos):
    super()._handle_mouse_release(mouse_pos)

    if not self._can_click:
      return

    for btn in self._scroll_inner.items:
      btn = cast(BigDialogOptionButton, btn)
      if btn.option == self._selected_option:
        self._on_option_selected(btn.option)
        break

  def _update_state(self):
    super()._update_state()
    if not self.is_dismissing:
      self._nav_bar.set_alpha(1.0)

    center_y = self._rect.y + self._rect.height / 2
    closest_btn = (None, float("inf"))
    for btn in self._scroll_inner.items:
      dist_y = abs((btn.rect.y + btn.rect.height / 2) - center_y)
      if dist_y < closest_btn[1]:
        closest_btn = (btn, dist_y)

    if closest_btn[0] is not None:
      for btn in self._scroll_inner.items:
        btn.set_selected(btn.option == closest_btn[0].option)
      self._selected_option = closest_btn[0].option

    if self._selected_option != self._last_selected_option:
      self._selected_option_changed()
      self._last_selected_option = self._selected_option

  def _render(self, _):
    if self._right_btn is not None:
      self._right_btn.set_position(self._rect.x + self._rect.width - self._right_btn.rect.width, self._rect.y)
      self._right_btn.render()
    self._scroller.render(self._rect)
