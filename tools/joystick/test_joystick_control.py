from openpilot.tools.joystick import joystick_control


def test_evdev_axes_are_normalized_for_joystick_mode():
  joystick = joystick_control.Joystick.__new__(joystick_control.Joystick)
  joystick.axes_values = {"ABS_RY": 0.0, "ABS_X": 0.0}
  joystick.min_axis_value = {"ABS_RY": 0.0, "ABS_X": 0.0}
  joystick.max_axis_value = {"ABS_RY": 255.0, "ABS_X": 255.0}
  joystick.deadzone = 0.1
  joystick.cancel = False

  assert joystick._handle_event(joystick_control.EV_ABS, joystick_control.ABS_CODES["ABS_X"], 0)
  assert joystick.axes_values["ABS_X"] == 1.0
  assert joystick._handle_event(joystick_control.EV_ABS, joystick_control.ABS_CODES["ABS_RY"], 255)
  assert joystick.axes_values["ABS_RY"] == -1.0
  assert joystick._handle_event(joystick_control.EV_ABS, joystick_control.ABS_CODES["ABS_X"], 128)
  assert joystick.axes_values["ABS_X"] == 0.0


def test_evdev_ignores_unconfigured_axes_and_tracks_cancel_button():
  joystick = joystick_control.Joystick.__new__(joystick_control.Joystick)
  joystick.axes_values = {"ABS_RY": 0.0, "ABS_X": 0.0}
  joystick.min_axis_value = {"ABS_RY": 0.0, "ABS_X": 0.0}
  joystick.max_axis_value = {"ABS_RY": 255.0, "ABS_X": 255.0}
  joystick.deadzone = 0.1
  joystick.cancel = False

  assert not joystick._handle_event(joystick_control.EV_ABS, joystick_control.ABS_CODES["ABS_Z"], 255)
  assert joystick._handle_event(joystick_control.EV_KEY, joystick_control.BTN_NORTH, 1)
  assert joystick.cancel
  assert joystick._handle_event(joystick_control.EV_KEY, joystick_control.BTN_NORTH, 0)
  assert not joystick.cancel
