"""GM startup must replace the camera stream even before host initialization ends."""
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock, patch

import pytest

from opendbc.car import structs
from opendbc.car.gm.carcontroller import CarController
from opendbc.car.gm.carstate import CarState
from opendbc.car.gm.values import DBC
from openpilot.selfdrive.car.card import Car
from openpilot.starpilot.aol.tests.test_gm import _configurations


CONFIGURATIONS = list(_configurations())


@pytest.mark.parametrize('cp', CONFIGURATIONS, ids=lambda cp: f'{cp.carFingerprint}-{cp.safetyConfigs[0].safetyParam:x}')
def test_all_gm_initializing_steps_keep_servicing_handoff(cp):
  # Exercise the actual step dispatch, including after CI initialization. That
  # second iteration was excluded for Bolt while selfdriveInitializing remained.
  cs = structs.CarState.new_message().as_reader()
  card = SimpleNamespace(CP=cp, ci_initialized=True, aol_replay=True,
                         vehicle_startup=SimpleNamespace(owner=None),
                         sm=SimpleNamespace(seen={'onroadEvents': True}),
                         state_update=Mock(return_value=(cs, None)), state_publish=Mock(),
                         controls_update=Mock(), _deferred_radar_can=None,
                         radar_update=Mock(), radar_publish=Mock())
  events = [SimpleNamespace(name=1)]
  card.sm = type('SM', (), {'seen': {'onroadEvents': True}, '__getitem__': lambda _, key: events if key == 'onroadEvents' else None})()
  for method in ('gm_startup_keepalive', 'volt_startup_keepalive', 'volt_sdgm_startup_keepalive'):
    setattr(card, method, getattr(Car, method).__get__(card))
  for method in ('ev6_startup_keepalive', 'classic_startup_keepalive', 'torque_ev_startup_keepalive', 'mixed_startup_keepalive'):
    setattr(card, method, lambda: False)
  with patch('openpilot.selfdrive.car.card.EventName', SimpleNamespace(selfdriveInitializing=1)):
    for _ in range(600):
      Car.step(cast(Car, card))
  assert card.controls_update.call_count == 600
  assert all(call.kwargs == {'initialize_only': True} for call in card.controls_update.call_args_list)


@pytest.mark.parametrize('cp', CONFIGURATIONS, ids=lambda cp: f'{cp.carFingerprint}-{cp.safetyConfigs[0].safetyParam:x}')
def test_initializing_gm_output_is_inactive_and_profile_complete(cp):
  controller = CarController(DBC[cp.carFingerprint], cp)
  cs = CarState(cp)
  state = structs.CarState.new_message()
  state.canValid = True
  state.gearShifter = structs.CarState.GearShifter.reverse
  cs.out = state.as_reader()
  cs.pscm_status = dict.fromkeys(('HandsOffSWDetectionMode', 'HandsOffSWlDetectionStatus',
                                'LKATorqueDeliveredStatus', 'LKADriverAppldTrq', 'LKATorqueDelivered',
                                'LKATotalTorqueDelivered', 'RollingCounter', 'PSCMStatusChecksum'), 0)
  # Even an incorrectly active caller cannot turn a keepalive into actuation.
  control = structs.CarControl.new_message()
  control.enabled = control.latActive = control.longActive = True
  control.actuators.torque = 1.0
  control.actuators.accel = 1.0
  sent = []
  last_ns = 0
  last_counter = 0
  for tick in range(600):
    now = 12_380_000_000 + tick * 10_000_000
    cs.loopback_lka_steering_cmd_updated = bool(last_ns)
    cs.loopback_lka_steering_cmd_ts_nanos = last_ns
    cs.loopback_lka_steering_cmd_counter = last_counter
    cs.cam_lka_steering_cmd_counter = last_counter
    output, frames = controller.update(control.as_reader(), cs, now, startup_keepalive=True)
    assert not output.torque and not output.torqueOutputCan and not output.accel
    assert not output.brake
    for address, data, bus in frames:
      if address == 0x180:
        assert bus == 0 and not data[0] & 8 and not ((data[0] & 7) or data[1])
        last_ns = now
        last_counter = (data[0] >> 4) & 3
        sent.append(now)
      else:
        assert controller.ordinary_camera_long and controller.camera_pedal_profile is None
        assert (address, bus) in ((0x2CB, 0), (0x315, 0), (0x370, 0), (0x2CD, 0),
                                  (0x184, 2), (0x409, 0), (0x40A, 0))
        if address == 0x2CB:
          assert not data[0] & 1 and not data[1] & 0x20
        elif address == 0x315:
          assert data[0] >> 4 == 1 and not (int.from_bytes(data[:2], 'big') & 0xFFF)
        elif address == 0x370:
          assert not data[2] & 0x80 and data[1] & 7 == 2
  assert sent and sent[0] <= 12_480_000_000
  assert max(b - a for a, b in zip(sent, sent[1:], strict=False)) <= 110_000_000


def test_non_gm_does_not_enter_gm_keepalive():
  assert not Car.gm_startup_keepalive(cast(Car, SimpleNamespace(CP=SimpleNamespace(brand='hyundai', passive=False))))


def test_card_replaces_bolt_camera_stream_during_initialization():
  from opendbc.car.gm.tests.test_bolt_cc import params
  from opendbc.car.gm.interface import CarInterface
  from opendbc.car.gm.values import CAR
  cp = params(CAR.CHEVROLET_BOLT_CC_2017)
  ci = CarInterface(cp)
  state = structs.CarState.new_message()
  state.canValid = True
  state.gearShifter = structs.CarState.GearShifter.reverse
  ci.CS.out = state.as_reader()
  control = structs.CarControl.new_message().as_reader()

  class SM:
    seen = valid = alive = {'carControl': True}
    logMonoTime = {'carControl': 0}
    recv_time = {'carControl': 0.0}

  card = SimpleNamespace(CP=cp, CI=ci, sm=SM(), ci_initialized=True,
                         volt_cc_selected=False, is_metric=False,
                         vehicle_startup=SimpleNamespace(owner=None),
                         startup_panda_configured=Mock(return_value=True),
                         publish_sendcan=Mock(), _invalidate_feedback_output=Mock())
  card.gm_startup_keepalive = Car.gm_startup_keepalive.__get__(card)
  for method in ('ev6_startup_keepalive', 'classic_startup_keepalive', 'torque_ev_startup_keepalive', 'mixed_startup_keepalive'):
    setattr(card, method, lambda: False)
  for tick in range(600):
    now = 12_380_000_000 + tick * 10_000_000
    card.sm.logMonoTime['carControl'] = now
    card.sm.recv_time['carControl'] = now / 1e9
    with patch('openpilot.selfdrive.car.card.time.monotonic_ns', return_value=now), \
         patch('openpilot.selfdrive.car.card.time.clock_gettime_ns', return_value=now):
      Car.controls_update(cast(Car, card), ci.CS.out, control, initialize_only=True)
  assert card.publish_sendcan.call_count == 600
  assert any(call.args[0] for call in card.publish_sendcan.call_args_list)
  for call in card.publish_sendcan.call_args_list:
    assert call.kwargs['valid']
    assert all(address == 0x180 and bus == 0 and not data[0] & 8
               for address, data, bus in call.args[0])
  # Stale or active host commands cannot enter the startup stream.
  card.publish_sendcan.reset_mock()
  with patch('openpilot.selfdrive.car.card.time.monotonic_ns', return_value=now + 200_000_000):
    Car.controls_update(cast(Car, card), ci.CS.out, control, initialize_only=True)
  card.publish_sendcan.assert_not_called()
