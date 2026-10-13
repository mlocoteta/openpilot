"""Standstill engage hold through the real SelfdriveD event + state machine path (2017 Accord 9G with a gas interceptor)."""
from types import SimpleNamespace

import cereal.messaging as messaging
import pytest

from cereal import car, custom, log
from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.common.params import Params
from openpilot.selfdrive.controls.lib.standstill_hold import MODE_HOLD_ONLY, MODE_OFF, MODE_RESUME
from openpilot.selfdrive.selfdrived.events import ET
from openpilot.selfdrive.selfdrived.selfdrived import SelfdriveD

State = log.SelfdriveState.OpenpilotState
EventName = log.OnroadEvent.EventName
StarPilotEventName = custom.StarPilotOnroadEvent.EventName
ButtonType = car.CarState.ButtonEvent.Type
GearShifter = car.CarState.GearShifter


def make_cp():
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x201] = 6  # gas interceptor, like Mat's car (pcmCruise False, button enable)
  CP = CarInterface.get_params(CAR.HONDA_ACCORD_9G, fingerprint, [], False, False, False, SimpleNamespace())
  assert not CP.pcmCruise and CP.openpilotLongitudinalControl and CP.enableGasInterceptorDEPRECATED
  return CP


def make_selfdrived(mode):
  Params().put("StarPilotCarParams", custom.StarPilotCarParams.new_message().to_bytes())
  sd = SelfdriveD(make_cp().as_reader())
  sd.initialized = True
  sd.startup_event = None
  sd.sm.frame = 1000
  sd.standstill_engage_mode = mode
  for service in sd.sm.data:
    sd.sm.valid[service] = sd.sm.alive[service] = sd.sm.freq_ok[service] = sd.sm.seen[service] = True
    sd.sm.updated[service] = False
    sd.sm.recv_frame[service] = sd.sm.frame
  device_state = log.DeviceState.new_message()
  device_state.started = True
  device_state.freeSpacePercent = 100.0
  sd.sm.data["deviceState"] = device_state.as_reader()
  live_calibration = log.LiveCalibrationData.new_message()
  live_calibration.calStatus = log.LiveCalibrationData.Status.calibrated
  sd.sm.data["liveCalibration"] = live_calibration.as_reader()
  live_parameters = log.LiveParametersData.new_message()
  live_parameters.valid = True
  sd.sm.data["liveParameters"] = live_parameters.as_reader()
  live_pose = log.LivePose.new_message()
  live_pose.posenetOK = True
  live_pose.inputsOK = True
  sd.sm.data["livePose"] = live_pose.as_reader()
  sd.sm.data["pandaStates"] = messaging.new_message("pandaStates", 0).pandaStates
  sd.CS_prev = make_cs(brake=True).as_reader()
  return sd


def make_cs(brake=False, gas=False, door=False, belt=False, gear=GearShifter.drive, set_release=False):
  cs = car.CarState.new_message()
  cs.canValid = True
  cs.standstill = True
  cs.vEgo = 0.0
  cs.gearShifter = gear
  cs.cruiseState.available = True
  cs.brakePressed = brake
  cs.gasPressed = gas
  cs.doorOpen = door
  cs.seatbeltUnlatched = belt
  if set_release:
    be = car.CarState.ButtonEvent.new_message()
    be.type = ButtonType.decelCruise  # Honda SET
    be.pressed = False
    cs.buttonEvents = [be]
    cs.buttonEnable = True
  return cs


def step(sd, cs):
  cs = cs.as_reader()
  sd.update_events(cs)
  sd.enabled, sd.active = sd.state_machine.update(sd.events, sd.starpilot_events, False)
  sd.CS_prev = cs
  sp_names = set(sd.starpilot_events.names)
  return sd.state_machine.state, set(sd.events.names), sp_names


def engage_and_release(sd):
  state, events, _ = step(sd, make_cs(brake=True, set_release=True))
  assert EventName.buttonEnable in events and EventName.preEnableStandstill in events
  assert state == State.preEnabled  # "Release Brake to Engage"
  step(sd, make_cs(brake=True))  # the latch arms from last frame's preEnabled
  state, _, sp = step(sd, make_cs())  # brake released
  assert state == State.enabled
  return sp


@pytest.mark.parametrize("mode, banner", [(MODE_RESUME, StarPilotEventName.standstillHold),
                                          (MODE_HOLD_ONLY, StarPilotEventName.standstillHoldOnly)])
def test_engage_shows_holding(mode, banner):
  sd = make_selfdrived(mode)
  sp = engage_and_release(sd)
  assert banner in sp
  assert sd.standstill_hold.active
  for _ in range(100):
    state, _, sp = step(sd, make_cs())
  assert state == State.enabled and banner in sp


@pytest.mark.parametrize("mode", [MODE_RESUME, MODE_HOLD_ONLY])
@pytest.mark.parametrize("kw, held_back", [
  ({"door": True}, EventName.doorOpen),
  ({"belt": True}, EventName.seatbeltNotLatched),
  ({"gear": GearShifter.park}, EventName.wrongGear),
  ({"gear": GearShifter.reverse}, EventName.reverseGear),
])
def test_door_belt_gear_ask_for_brake_and_keep_holding(mode, kw, held_back):
  sd = make_selfdrived(mode)
  engage_and_release(sd)
  for _ in range(500):  # 5 s: well past the 2 s soft-disable these would normally run
    state, events, sp = step(sd, make_cs(**kw))
    assert held_back not in events
    assert StarPilotEventName.standstillHoldBrake in sp
  assert state == State.enabled and sd.standstill_hold.active
  alerts = sd.starpilot_events.create_alerts([ET.WARNING], [sd.CP, make_cs(**kw).as_reader(), sd.sm, False, 0, None, None])
  hold_alerts = [a for a in alerts if a.alert_type.startswith("standstillHoldBrake/")]
  assert len(hold_alerts) == 1, [a.alert_type for a in alerts]
  assert hold_alerts[0].audible_alert == log.SelfdriveState.AudibleAlert.promptRepeat
  assert hold_alerts[0].alert_text_1.startswith("Press Brake")
  # it outranks everything else the starpilot alert manager could show alongside
  assert all(hold_alerts[0].priority >= a.priority for a in alerts), [(a.alert_type, a.priority) for a in alerts]
  # the driver brakes: normal disengage, the foot now holds the car
  state, events, _ = step(sd, make_cs(brake=True, **kw))
  assert EventName.pedalPressed in events
  assert state == State.disabled


def test_off_mode_is_stock():
  sd = make_selfdrived(MODE_OFF)
  sp = engage_and_release(sd)
  assert not ({StarPilotEventName.standstillHold, StarPilotEventName.standstillHoldOnly} & sp)
  state, events, _ = step(sd, make_cs(door=True))
  assert EventName.doorOpen in events
  assert state == State.softDisabling


def test_resume_mode_gas_keeps_engaged():
  sd = make_selfdrived(MODE_RESUME)
  engage_and_release(sd)
  state, events, sp = step(sd, make_cs(gas=True))
  assert EventName.pedalPressed not in events
  assert state == State.overriding
  assert not sd.standstill_hold.active
  state, _, sp = step(sd, make_cs())
  assert state == State.enabled and StarPilotEventName.standstillHold not in sp


def test_hold_only_gas_disengages():
  sd = make_selfdrived(MODE_HOLD_ONLY)
  engage_and_release(sd)
  state, events, _ = step(sd, make_cs(gas=True))
  assert EventName.pedalPressed in events
  assert state == State.disabled


def test_resume_mode_gas_with_door_open_disengages():
  # door open while holding: the gas ends the hold, and the held-back door event mustn't leave it engaged
  sd = make_selfdrived(MODE_RESUME)
  engage_and_release(sd)
  step(sd, make_cs(door=True))
  state, events, _ = step(sd, make_cs(door=True, gas=True))
  assert EventName.pedalPressed in events
  assert state == State.disabled


def test_timeout_asks_for_brake(monkeypatch):
  import openpilot.selfdrive.selfdrived.selfdrived as selfdrived_mod
  now = [1000.0]
  monkeypatch.setattr(selfdrived_mod.time, "monotonic", lambda: now[0])
  sd = make_selfdrived(MODE_RESUME)
  engage_and_release(sd)
  now[0] += 179.0
  _, _, sp = step(sd, make_cs())
  assert StarPilotEventName.standstillHoldBrake not in sp
  now[0] += 2.0
  state, _, sp = step(sd, make_cs())
  assert StarPilotEventName.standstillHoldBrake in sp and state == State.enabled
