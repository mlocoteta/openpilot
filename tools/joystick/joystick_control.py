#!/usr/bin/env python3
import os
import time
import argparse
import fcntl
import select
import struct
import threading
import numpy as np
import inputs
from inputs import UnpluggedError, get_gamepad

from cereal import messaging
from openpilot.common.params import Params
from openpilot.common.realtime import Ratekeeper
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware import HARDWARE
from openpilot.starpilot.system.wheel_controls import connected_input_sources, selected_joystick_device
from openpilot.tools.lib.kbhit import KBHit

EXPO = 0.4

# Per-controller config keyed on a substring of the `inputs` gamepad name.
# accel = right stick vertical (up = gas). Axis codes and raw ranges (signed vs
# unsigned) differ per pad — use tools/joystick/joystick_probe.py to add one.
CONTROLLER_PROFILES = {
  'Stadia':    {'name': 'Stadia',    'steer': 'ABS_X', 'accel': 'ABS_RZ', 'lo': 0.,      'hi': 255.},
  'X-Box':     {'name': 'Xbox',      'steer': 'ABS_X', 'accel': 'ABS_RY', 'lo': -32768., 'hi': 32767.},
  'DualSense': {'name': 'DualSense', 'steer': 'ABS_X', 'accel': 'ABS_RY', 'lo': 0.,      'hi': 255.},
}
DEFAULT_PROFILE = 'X-Box'
ABS_CODES = {'ABS_X': 0, 'ABS_Y': 1, 'ABS_Z': 2, 'ABS_RX': 3, 'ABS_RY': 4, 'ABS_RZ': 5}
INPUT_EVENT = struct.Struct('@llHHi')
EV_KEY = 1
EV_ABS = 3
BTN_NORTH = 307


class Keyboard:
  def __init__(self):
    self.kb = KBHit()
    self.axis_increment = 0.05  # 5% of full actuation each key press
    self.axes_map = {'w': 'gb', 's': 'gb',
                     'a': 'steer', 'd': 'steer'}
    self.axes_values = {'gb': 0., 'steer': 0.}
    self.axes_order = ['gb', 'steer']
    self.cancel = False

  def update(self):
    key = self.kb.getch().lower()
    self.cancel = False
    if key == 'r':
      self.axes_values = dict.fromkeys(self.axes_values, 0.)
    elif key == 'c':
      self.cancel = True
    elif key in self.axes_map:
      axis = self.axes_map[key]
      incr = self.axis_increment if key in ['w', 'a'] else -self.axis_increment
      self.axes_values[axis] = float(np.clip(self.axes_values[axis] + incr, -1, 1))
    else:
      return False
    return True


class Joystick:
  def __init__(self):
    self.cancel_button = 'BTN_NORTH'
    self.is_pc = HARDWARE.get_device_type() == 'pc'
    self.params = Params(return_defaults=True)
    self._last_scan = 0.
    self._source_id = ''
    self._event_path = ''
    self._event_fd = None
    self._load_profile()
    self._rescan(force=True)

  def _load_profile(self, name=''):
    if self.is_pc:
      # DualSense over a laptop for development
      accel_axis, steer_axis = 'ABS_Z', 'ABS_RX'
      self.flip_map = {'ABS_RZ': accel_axis}
      raw_min, raw_max, self.deadzone = 0., 255., 0.03
      name, prof_name = 'pc', 'pc'
    else:
      prof = next((p for key, p in CONTROLLER_PROFILES.items() if key in name), CONTROLLER_PROFILES[DEFAULT_PROFILE])
      accel_axis, steer_axis = prof['accel'], prof['steer']
      self.flip_map = {}
      raw_min, raw_max, self.deadzone = prof['lo'], prof['hi'], 0.10
      prof_name = prof['name']

    cloudlog.info(f"joystick_control: gamepad='{name}' using profile '{prof_name}'")
    self.min_axis_value = {accel_axis: raw_min, steer_axis: raw_min}
    self.max_axis_value = {accel_axis: raw_max, steer_axis: raw_max}
    self.axes_values = {accel_axis: 0., steer_axis: 0.}
    self.axes_order = [accel_axis, steer_axis]
    self.cancel = False

  def _close_event(self):
    if self._event_fd is not None:
      try:
        os.close(self._event_fd)
      except OSError:
        pass
    self._event_fd = None
    self._event_path = ''
    self._source_id = ''

  def _axis_range(self, axis_name, fallback_min, fallback_max):
    if self._event_fd is None:
      return fallback_min, fallback_max
    axis = ABS_CODES[axis_name]
    data = bytearray(24)
    try:
      fcntl.ioctl(self._event_fd, 0x80184540 + axis, data, True)
      _value, minimum, maximum, _fuzz, _flat, _resolution = struct.unpack('iiiiii', data)
      if maximum > minimum:
        return float(minimum), float(maximum)
    except OSError:
      pass
    return fallback_min, fallback_max

  def _rescan(self, force=False):
    now = time.monotonic()
    if not force and now - self._last_scan < 1.0:
      return
    self._last_scan = now
    if self.is_pc:
      inputs.devices = inputs.DeviceManager()
      if inputs.devices.gamepads:
        self._load_profile(inputs.devices.gamepads[0].name)
      return

    selected = selected_joystick_device(self.params)
    source = next((item for item in connected_input_sources()
                   if item.device_id == selected and item.joystick_capable), None)
    if source is None:
      if self._event_fd is not None:
        cloudlog.info('joystick_control: selected controller disconnected')
      self._close_event()
      self.axes_values = dict.fromkeys(self.axes_values, 0.)
      return
    if self._source_id == source.device_id and self._event_path == source.path and self._event_fd is not None:
      return

    self._close_event()
    try:
      self._event_fd = os.open(source.path, os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
      return
    self._source_id = source.device_id
    self._event_path = source.path
    self._load_profile(source.name)
    for axis in self.axes_order:
      self.min_axis_value[axis], self.max_axis_value[axis] = self._axis_range(
        axis, self.min_axis_value[axis], self.max_axis_value[axis])
    cloudlog.info(f"joystick_control: selected '{source.name}' at {source.path}")

  def _handle_event(self, event_type, code, value):
    if event_type == EV_KEY and code == BTN_NORTH:
      self.cancel = value != 0
      return True
    if event_type != EV_ABS:
      return False
    event_name = next((name for name, number in ABS_CODES.items() if number == code), '')
    if event_name not in self.axes_values:
      return False
    norm = -float(np.interp(value, [self.min_axis_value[event_name], self.max_axis_value[event_name]], [-1., 1.]))
    norm = norm if abs(norm) > self.deadzone else 0.
    self.axes_values[event_name] = EXPO * norm ** 3 + (1 - EXPO) * norm
    return True

  def update(self):
    if not self.is_pc:
      self._rescan()
      if self._event_fd is None:
        time.sleep(0.1)
        return False
      try:
        readable, _, _ = select.select([self._event_fd], [], [], 0.1)
        if not readable:
          return False
        data = os.read(self._event_fd, INPUT_EVENT.size * 64)
      except OSError:
        self._close_event()
        return False
      if not data:
        self._close_event()
        return False
      handled = False
      for offset in range(0, len(data) - INPUT_EVENT.size + 1, INPUT_EVENT.size):
        _seconds, _microseconds, event_type, code, value = INPUT_EVENT.unpack_from(data, offset)
        handled = self._handle_event(event_type, code, value) or handled
      return handled

    try:
      joystick_event = get_gamepad()[0]
    except (OSError, UnpluggedError):
      self.axes_values = dict.fromkeys(self.axes_values, 0.)
      self._rescan()
      time.sleep(0.1)  # no controller; avoid busy-spin
      return False

    event = (joystick_event.code, joystick_event.state)

    if event[0] in self.flip_map:
      event = (self.flip_map[event[0]], -event[1])

    if event[0] == self.cancel_button:
      if event[1] == 1:
        self.cancel = True
      elif event[1] == 0:   # state 0 is falling edge
        self.cancel = False
    elif event[0] in self.axes_values:
      norm = -float(np.interp(event[1], [self.min_axis_value[event[0]], self.max_axis_value[event[0]]], [-1., 1.]))
      norm = norm if abs(norm) > self.deadzone else 0.  # center can be noisy
      self.axes_values[event[0]] = EXPO * norm ** 3 + (1 - EXPO) * norm  # less action near center for fine control
    else:
      return False
    return True


def send_thread(joystick):
  pm = messaging.PubMaster(['testJoystick'])

  rk = Ratekeeper(100, print_delay_threshold=None)

  while True:
    if rk.frame % 20 == 0:
      print('\n' + ', '.join(f'{name}: {round(v, 3)}' for name, v in joystick.axes_values.items()))

    # _rescan() may swap the axis map from another thread
    values, order = joystick.axes_values, joystick.axes_order
    joystick_msg = messaging.new_message('testJoystick')
    joystick_msg.valid = True
    joystick_msg.testJoystick.axes = [values.get(ax, 0.) for ax in order]

    pm.send('testJoystick', joystick_msg)

    rk.keep_time()


def joystick_control_thread(joystick):
  Params().put_bool('JoystickDebugMode', True)
  threading.Thread(target=send_thread, args=(joystick,), daemon=True).start()
  while True:
    joystick.update()


def main():
  joystick_control_thread(Joystick())


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Publishes events from your joystick to control your car.\n' +
                                               'openpilot must be offroad before starting joystick_control. This tool supports ' +
                                               'a PlayStation 5 DualSense controller on the comma 3X.',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--keyboard', action='store_true', help='Use your keyboard instead of a joystick')
  args = parser.parse_args()

  if not Params().get_bool("IsOffroad") and "ZMQ" not in os.environ:
    print("The car must be off before running joystick_control.")
    exit()

  print()
  if args.keyboard:
    print('Gas/brake control: `W` and `S` keys')
    print('Steering control: `A` and `D` keys')
    print('Buttons')
    print('- `R`: Resets axes')
    print('- `C`: Cancel cruise control')
  else:
    print('Using joystick, make sure to run cereal/messaging/bridge on your device if running over the network!')
    print('If not running on a comma device, the mapping may need to be adjusted.')

  joystick = Keyboard() if args.keyboard else Joystick()
  joystick_control_thread(joystick)
