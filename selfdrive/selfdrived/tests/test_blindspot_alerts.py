from types import SimpleNamespace

from cereal import custom, log
from openpilot.selfdrive.selfdrived.alertmanager import AlertManager
from openpilot.selfdrive.selfdrived.events import ET, Events
from openpilot.selfdrive.selfdrived.selfdrived import get_starpilot_alert_filters, should_loud_blindspot_alert_without_lateral


LaneChangeState = log.LaneChangeState
LaneChangeDirection = log.LaneChangeDirection
StarPilotEventName = custom.StarPilotOnroadEvent.EventName


def _car_state(left_blinker=False, right_blinker=False, left_blindspot=False, right_blindspot=False):
  return SimpleNamespace(
    leftBlinker=left_blinker,
    rightBlinker=right_blinker,
    leftBlindspot=left_blindspot,
    rightBlindspot=right_blindspot,
  )


def _sm(lane_change_state=LaneChangeState.off, lane_change_direction=LaneChangeDirection.none,
        lat_active=False, lateral_check=False, pause_lateral=False):
  return {
    "modelV2": SimpleNamespace(meta=SimpleNamespace(laneChangeState=lane_change_state, laneChangeDirection=lane_change_direction)),
    "carControl": SimpleNamespace(latActive=lat_active),
    "starpilotPlan": SimpleNamespace(lateralCheck=lateral_check),
    "starpilotCarState": SimpleNamespace(pauseLateral=pause_lateral),
  }


def _toggles(enabled=True, loud_enabled=True):
  return SimpleNamespace(
    loud_blindspot_alert=loud_enabled,
    loud_blindspot_alert_when_disengaged=enabled,
  )


def test_loud_blindspot_alert_without_lateral_for_matching_signal():
  CS = _car_state(left_blinker=True, left_blindspot=True)

  assert should_loud_blindspot_alert_without_lateral(CS, _sm(lat_active=False), _toggles())
  assert should_loud_blindspot_alert_without_lateral(CS, _sm(lat_active=True, lateral_check=False), _toggles())
  assert should_loud_blindspot_alert_without_lateral(CS, _sm(lat_active=True, lateral_check=True, pause_lateral=True), _toggles())


def test_loud_blindspot_alert_accepts_combined_vision_state():
  CS = _car_state(left_blinker=True)

  assert should_loud_blindspot_alert_without_lateral(
    CS, _sm(lat_active=False), _toggles(), combined_left_bsm=True,
  )


def test_loud_blindspot_alert_without_lateral_is_independent_of_active_loud_alert():
  CS = _car_state(left_blinker=True, left_blindspot=True)

  assert should_loud_blindspot_alert_without_lateral(CS, _sm(), _toggles(loud_enabled=False))


def test_loud_blindspot_alert_without_lateral_ignores_active_lateral():
  CS = _car_state(right_blinker=True, right_blindspot=True)

  assert not should_loud_blindspot_alert_without_lateral(CS, _sm(lat_active=True, lateral_check=True), _toggles())


def test_loud_blindspot_alert_without_lateral_requires_matching_side_and_toggle():
  assert not should_loud_blindspot_alert_without_lateral(_car_state(left_blinker=True, right_blindspot=True), _sm(), _toggles())
  assert not should_loud_blindspot_alert_without_lateral(_car_state(left_blinker=True, right_blinker=True, left_blindspot=True), _sm(), _toggles())
  assert not should_loud_blindspot_alert_without_lateral(_car_state(left_blinker=True, left_blindspot=True), _sm(), _toggles(enabled=False))


def test_loud_blindspot_alert_without_lateral_skips_normal_lane_change_alert_path():
  CS = _car_state(left_blinker=True, left_blindspot=True)

  assert not should_loud_blindspot_alert_without_lateral(CS, _sm(lane_change_state=LaneChangeState.preLaneChange,
                                                                 lane_change_direction=LaneChangeDirection.left), _toggles())


def test_loud_blindspot_alert_without_lateral_handles_paused_pre_lane_change_without_direction():
  CS = _car_state(left_blinker=True, left_blindspot=True)
  sm = _sm(lane_change_state=LaneChangeState.preLaneChange, lat_active=True, lateral_check=True, pause_lateral=True)

  assert should_loud_blindspot_alert_without_lateral(CS, sm, _toggles())


def test_loud_blindspot_alert_survives_disabled_warning_filter():
  events = Events(starpilot=True)
  events.add(StarPilotEventName.laneChangeBlockedLoud)

  alert_types, clear_event_types = get_starpilot_alert_filters([ET.PERMANENT], {ET.WARNING}, events)

  alerts = events.create_alerts(alert_types)
  alert_manager = AlertManager()
  alert_manager.add_many(0, alerts)
  alert_manager.process_alerts(0, clear_event_types)

  assert alert_manager.current_alert.alert_type == "laneChangeBlockedLoud/warning"


def test_lkas_enable_sound_survives_disabled_warning_filter():
  events = Events(starpilot=True)
  events.add(StarPilotEventName.lkasEnable)

  alert_types, clear_event_types = get_starpilot_alert_filters([ET.PERMANENT], {ET.WARNING}, events)

  alerts = events.create_alerts(alert_types)
  alert_manager = AlertManager()
  alert_manager.add_many(0, alerts)
  alert_manager.process_alerts(0, clear_event_types)

  assert alert_manager.current_alert.alert_type == "lkasEnable/warning"
  assert alert_manager.current_alert.audible_alert == log.SelfdriveState.AudibleAlert.engage


def test_disabled_starpilot_warnings_stay_filtered_without_blindspot_event():
  events = Events(starpilot=True)
  events.add(StarPilotEventName.noLaneAvailable)

  alert_types, clear_event_types = get_starpilot_alert_filters([ET.PERMANENT], {ET.WARNING}, events)

  assert ET.WARNING not in alert_types
  assert ET.WARNING in clear_event_types
  assert events.create_alerts(alert_types) == []
