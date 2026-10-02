from types import SimpleNamespace
from time import monotonic

from cereal import log

from openpilot.selfdrive.controls.lib.desire_helper import DesireHelper, LaneChangeDirection, LaneChangeState


def make_car_state(**overrides):
  defaults = {
    "vEgo": 20.0,
    "leftBlinker": False,
    "rightBlinker": False,
    "leftBlindspot": False,
    "rightBlindspot": False,
    "steeringPressed": False,
    "steeringTorque": 0.0,
    "standstill": False,
    "cruiseState": SimpleNamespace(enabled=True),
  }
  defaults.update(overrides)
  return SimpleNamespace(**defaults)


def make_toggles(**overrides):
  defaults = {
    "lane_changes": True,
    "lane_change_delay": 0.0,
    "lane_detection_width": 3.0,
    "minimum_lane_change_speed": 10.0,
    "nudgeless": True,
    "nudgeless_lane_change_only_when_engaged": False,
    "one_lane_change": False,
    "use_turn_desires": False,
    "lane_changes_require_cruise": False,
    "nav_desires_allowed": True,
    "nav_lane_positioning_allowed": True,
  }
  defaults.update(overrides)
  return SimpleNamespace(**defaults)


def make_plan(**overrides):
  defaults = {
    "laneWidthLeft": 4.0,
    "laneWidthRight": 4.0,
  }
  defaults.update(overrides)
  return SimpleNamespace(**defaults)

def test_nav_desires_keep_left_when_route_requests_it():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {"valid": True, "maneuverModifier": "slightLeft", "updatedAtMonotonic": monotonic()}

  helper.update(
    make_car_state(vEgo=20.0, steeringPressed=True, steeringTorque=1.0),
    True,
    0.0,
    make_plan(laneWidthLeft=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.keepLeft


def test_nav_desires_turn_right_below_lane_change_speed():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True, "maneuverType": "turn", "maneuverModifier": "right",
    "maneuverDistance": 10.0, "updatedAtMonotonic": monotonic(),
  }

  helper.update(
    make_car_state(vEgo=5.0, rightBlinker=True),
    True,
    0.0,
    make_plan(),
    make_toggles(minimum_lane_change_speed=10.0, nav_lane_positioning_allowed=False),
  )

  assert helper.desire == log.Desire.turnRight


def test_nav_desires_turn_preview_starts_before_last_second():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True, "maneuverType": "turn", "maneuverModifier": "right",
    "maneuverDistance": 50.0, "updatedAtMonotonic": monotonic(),
  }

  helper.update(
    make_car_state(vEgo=10.5, rightBlinker=True),
    True,
    0.0,
    make_plan(),
    make_toggles(minimum_lane_change_speed=11.1),
  )

  assert helper.desire == log.Desire.turnRight
  assert helper.lane_change_state == LaneChangeState.off


def test_routed_turn_replays_signaled_approach_independently_of_lane_change_setting():
  samples = (
    (82.6, 13.64, True, log.Desire.none),
    (69.1, 13.15, True, log.Desire.turnRight),
    (56.3, 13.18, True, log.Desire.turnRight),
    (43.1, 13.00, False, log.Desire.none),
  )
  for lane_change_speed in (2.777777, 11.1):
    helper = DesireHelper()
    helper._update_nav_params = lambda: None
    toggles = make_toggles(minimum_lane_change_speed=lane_change_speed)
    for distance, speed, right_blinker, expected in samples:
      helper._nav_instruction_state = {
        "valid": True,
        "maneuverType": "turn",
        "maneuverModifier": "right",
        "maneuverDistance": distance,
        "updatedAtMonotonic": monotonic(),
      }
      helper.update(
        make_car_state(vEgo=speed, rightBlinker=right_blinker),
        True,
        0.0,
        make_plan(),
        toggles,
      )
      assert helper.desire == expected
      assert helper.lane_change_state == LaneChangeState.off
      assert helper.turn_direction == expected


def test_stale_route_instruction_cannot_request_turn_or_suppress_lane_change():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "maneuverType": "turn",
    "maneuverModifier": "right",
    "maneuverDistance": 55.0,
    "updatedAtMonotonic": monotonic() - 10.0,
  }
  helper.update(
    make_car_state(vEgo=13.0, rightBlinker=True),
    True,
    0.0,
    make_plan(),
    make_toggles(minimum_lane_change_speed=2.777777),
  )

  assert helper.desire == log.Desire.none
  assert helper.lane_change_state == LaneChangeState.preLaneChange


def test_nav_desires_turn_preview_is_bounded_and_requires_matching_signal():
  for distance, blinker, speed, maneuver_type in (
    (65.0, True, 10.5, "turn"),
    (-1.0, True, 10.5, "turn"),
    (50.0, False, 10.5, "turn"),
    (50.0, True, 14.2, "turn"),
    (50.0, True, 10.5, "arrive"),
  ):
    helper = DesireHelper()
    helper._update_nav_params = lambda: None
    helper._nav_instruction_state = {
      "valid": True, "maneuverType": maneuver_type, "maneuverModifier": "right",
      "maneuverDistance": distance, "updatedAtMonotonic": monotonic(),
    }

    helper.update(
      make_car_state(vEgo=speed, rightBlinker=blinker),
      True,
      0.0,
      make_plan(),
      make_toggles(minimum_lane_change_speed=11.1),
    )

    assert helper.desire == log.Desire.none


def test_nav_desires_turn_preview_respects_stop_hold():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True, "maneuverType": "turn", "maneuverModifier": "right",
    "maneuverDistance": 20.0, "updatedAtMonotonic": monotonic(),
  }

  helper.update(
    make_car_state(vEgo=5.0, rightBlinker=True),
    True,
    0.0,
    make_plan(redLight=True),
    make_toggles(minimum_lane_change_speed=11.1),
  )

  assert helper.turn_stop_hold
  assert helper.desire == log.Desire.none


def test_nav_desires_turn_requires_matching_blinker():
  for modifier, opposite_blinker in (("left", "rightBlinker"), ("right", "leftBlinker")):
    helper = DesireHelper()
    helper.nav_desires_allowed = True
    helper._update_nav_params = lambda: None
    helper._nav_instruction_state = {
      "valid": True, "maneuverType": "turn", "maneuverModifier": modifier,
      "maneuverDistance": 10.0, "updatedAtMonotonic": monotonic(),
    }

    helper.update(
      make_car_state(vEgo=5.0, **{opposite_blinker: True}),
      True,
      0.0,
      make_plan(),
      make_toggles(minimum_lane_change_speed=10.0, nav_lane_positioning_allowed=False),
    )

    assert helper.desire == log.Desire.none


def test_nav_desires_turn_right_waits_until_turn_is_close():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True, "maneuverType": "turn", "maneuverModifier": "right",
    "maneuverDistance": 300.0, "updatedAtMonotonic": monotonic(),
  }

  helper.update(
    make_car_state(vEgo=5.0),
    True,
    0.0,
    make_plan(),
    make_toggles(minimum_lane_change_speed=10.0),
  )

  assert helper.desire == log.Desire.none


def test_matching_routed_turn_does_not_start_lane_change_above_threshold():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "turn",
    "maneuverModifier": "right",
    "maneuverDistance": 111.0,
  }

  helper.update(
    make_car_state(vEgo=16.0, rightBlinker=True),
    True,
    0.0,
    make_plan(),
    make_toggles(minimum_lane_change_speed=11.1),
  )

  assert helper.lane_change_state == LaneChangeState.off
  assert helper.lane_change_direction == LaneChangeDirection.none
  assert helper.desire == log.Desire.none


def test_distant_routed_turn_does_not_block_lane_change():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "turn",
    "maneuverModifier": "right",
    "maneuverDistance": 794.0,
  }

  helper.update(
    make_car_state(vEgo=16.0, rightBlinker=True),
    True,
    0.0,
    make_plan(),
    make_toggles(minimum_lane_change_speed=11.1),
  )

  assert helper.lane_change_state == LaneChangeState.preLaneChange
  assert helper.lane_change_direction == LaneChangeDirection.right


def test_matching_routed_turn_cancels_pending_lane_change_before_it_starts():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "turn",
    "maneuverModifier": "left",
    "maneuverDistance": 125.0,
  }
  helper.lane_change_state = LaneChangeState.preLaneChange
  helper.lane_change_direction = LaneChangeDirection.left
  helper.prev_one_blinker = True

  helper.update(
    make_car_state(vEgo=11.0, leftBlinker=True),
    True,
    0.0,
    make_plan(),
    make_toggles(minimum_lane_change_speed=10.0),
  )

  assert helper.lane_change_state == LaneChangeState.off
  assert helper.lane_change_direction == LaneChangeDirection.none


def test_nav_desires_off_ramp_lane_guidance_becomes_keep_right():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "off ramp",
    "maneuverModifier": "right",
    "activeLaneDirection": "slightRight",
    "maneuverDistance": 120.0,
  }

  helper.update(
    make_car_state(vEgo=22.5, steeringPressed=True, steeringTorque=-1.0),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.keepRight


def test_nav_desires_off_ramp_lane_guidance_waits_until_split_is_close():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "off ramp",
    "maneuverModifier": "right",
    "activeLaneDirection": "slightRight",
    "maneuverDistance": 300.0,
  }

  helper.update(
    make_car_state(vEgo=22.5),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.none


def test_nav_desires_ambiguous_off_ramp_waits_longer_before_keep_right():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "off ramp",
    "maneuverModifier": "right",
    "activeLaneDirection": "slightRight",
    "sameSideLaneCount": 3,
    "maneuverDistance": 120.0,
  }

  helper.update(
    make_car_state(vEgo=22.5),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.none


def test_nav_desires_edge_exit_lane_with_shared_transition_lane_does_not_keep_right():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "off ramp",
    "maneuverModifier": "right",
    "activeLaneDirection": "slightRight",
    "laneCount": 3,
    "sameSideLaneCount": 2,
    "activeLaneAtRoadEdge": True,
    "hasSharedSameSideLane": True,
    "maneuverDistance": 10.0,
  }

  helper.update(
    make_car_state(vEgo=22.5),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.none


def test_nav_desires_wide_highway_edge_exit_lane_keeps_right():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "off ramp",
    "maneuverModifier": "right",
    "activeLaneDirection": "slightRight",
    "laneCount": 7,
    "sameSideLaneCount": 2,
    "activeLaneAtRoadEdge": True,
    "hasSharedSameSideLane": True,
    "maneuverDistance": 105.0,
  }

  helper.update(
    make_car_state(vEgo=19.0, steeringPressed=True, steeringTorque=-1.0),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.keepRight


def test_nav_desires_shared_transition_lane_keeps_when_active_lane_is_not_outermost():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "off ramp",
    "maneuverModifier": "right",
    "activeLaneDirection": "slightRight",
    "sameSideLaneCount": 2,
    "activeLaneAtRoadEdge": False,
    "hasSharedSameSideLane": True,
    "maneuverDistance": 10.0,
  }

  helper.update(
    make_car_state(vEgo=22.5, steeringPressed=True, steeringTorque=-1.0),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.keepRight


def test_nav_desires_ambiguous_fork_slight_right_only_keeps_close_to_split():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "fork",
    "maneuverModifier": "slightRight",
    "activeLaneDirection": "slightRight",
    "sameSideLaneCount": 3,
    "maneuverDistance": 60.0,
  }

  helper.update(
    make_car_state(vEgo=22.5, steeringPressed=True, steeringTorque=-1.0),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.keepRight


def test_nav_desires_ambiguous_fork_slight_right_does_not_nudge_too_early():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "fork",
    "maneuverModifier": "slightRight",
    "activeLaneDirection": "slightRight",
    "sameSideLaneCount": 3,
    "maneuverDistance": 120.0,
  }

  helper.update(
    make_car_state(vEgo=22.5),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nudgeless=True),
  )

  assert helper.desire == log.Desire.none


def test_nav_desires_fork_with_active_straight_lane_does_not_turn_left():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "fork",
    "maneuverModifier": "left",
    "activeLaneDirection": "straight",
    "maneuverDistance": 15.0,
  }

  helper.update(
    make_car_state(vEgo=5.0),
    True,
    0.0,
    make_plan(laneWidthLeft=4.2),
    make_toggles(nudgeless=True, minimum_lane_change_speed=10.0),
  )

  assert helper.desire == log.Desire.none


def test_nav_desires_do_not_override_lane_change_state_machine():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {"valid": True, "maneuverModifier": "slightRight", "updatedAtMonotonic": monotonic()}
  helper.lane_change_state = LaneChangeState.laneChangeStarting
  helper.lane_change_direction = LaneChangeDirection.left
  helper.lane_change_ll_prob = 0.5

  helper.update(
    make_car_state(vEgo=25.0, leftBlinker=True),
    True,
    0.5,
    make_plan(),
    make_toggles(),
  )

  assert helper.desire == log.Desire.laneChangeLeft


def test_lane_changes_require_cruise_blocks_blinker_lane_change_without_cruise():
  helper = DesireHelper()

  helper.update(
    make_car_state(leftBlinker=True, cruiseState=SimpleNamespace(enabled=False)),
    True,
    0.0,
    make_plan(),
    make_toggles(lane_changes_require_cruise=True),
  )

  assert helper.lane_change_state == LaneChangeState.off
  assert helper.lane_change_direction == LaneChangeDirection.none
  assert helper.desire == log.Desire.none


def test_lane_changes_require_cruise_allows_blinker_lane_change_with_cruise():
  helper = DesireHelper()

  helper.update(
    make_car_state(leftBlinker=True, cruiseState=SimpleNamespace(enabled=True)),
    True,
    0.0,
    make_plan(),
    make_toggles(lane_changes_require_cruise=True),
  )

  assert helper.lane_change_state == LaneChangeState.preLaneChange
  assert helper.lane_change_direction == LaneChangeDirection.left


def test_lane_changes_without_cruise_requirement_keep_existing_behavior():
  helper = DesireHelper()

  helper.update(
    make_car_state(leftBlinker=True, cruiseState=SimpleNamespace(enabled=False)),
    True,
    0.0,
    make_plan(),
    make_toggles(lane_changes_require_cruise=False),
  )

  assert helper.lane_change_state == LaneChangeState.preLaneChange
  assert helper.lane_change_direction == LaneChangeDirection.left


def test_nudgeless_only_when_engaged_allows_automatic_lane_change_when_engaged():
  helper = DesireHelper()

  for _ in range(2):
    helper.update(
      make_car_state(leftBlinker=True),
      True,
      0.0,
      make_plan(),
      make_toggles(nudgeless_lane_change_only_when_engaged=True),
      controls_enabled=True,
    )

  assert helper.lane_change_state == LaneChangeState.laneChangeStarting
  assert helper.lane_change_direction == LaneChangeDirection.left


def test_nudgeless_only_when_engaged_requires_nudge_when_aol_only():
  helper = DesireHelper()
  toggles = make_toggles(nudgeless_lane_change_only_when_engaged=True)

  for _ in range(2):
    helper.update(
      make_car_state(leftBlinker=True),
      True,
      0.0,
      make_plan(),
      toggles,
      controls_enabled=False,
    )

  assert helper.lane_change_state == LaneChangeState.preLaneChange
  assert helper.lane_change_direction == LaneChangeDirection.left

  helper.update(
    make_car_state(leftBlinker=True, steeringPressed=True, steeringTorque=1.0),
    True,
    0.0,
    make_plan(),
    toggles,
    controls_enabled=False,
  )

  assert helper.lane_change_state == LaneChangeState.laneChangeStarting
  assert helper.lane_change_direction == LaneChangeDirection.left


def test_nav_desires_nudgeless_only_when_engaged_blocks_keep_when_aol_only():
  helper = DesireHelper()
  helper.nav_desires_allowed = True
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {"valid": True, "maneuverModifier": "slightLeft", "updatedAtMonotonic": monotonic()}

  helper.update(
    make_car_state(vEgo=20.0),
    True,
    0.0,
    make_plan(laneWidthLeft=4.2),
    make_toggles(nudgeless=True, nudgeless_lane_change_only_when_engaged=True),
    controls_enabled=False,
  )

  assert helper.desire == log.Desire.none

  helper.update(
    make_car_state(vEgo=20.0, steeringPressed=True, steeringTorque=-1.0),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nav_desires_allowed=True, nav_lane_positioning_allowed=False, nudgeless=True),
  )

  assert helper.desire == log.Desire.none


def test_turn_desire_fires_below_lane_change_speed_when_no_stop():
  helper = DesireHelper()

  helper.update(
    make_car_state(vEgo=5.0, rightBlinker=True),
    True,
    0.0,
    make_plan(),
    make_toggles(use_turn_desires=True, minimum_lane_change_speed=10.0),
  )

  assert helper.desire == log.Desire.turnRight


def test_turn_desire_held_while_stopping_for_red_light():
  helper = DesireHelper()

  helper.update(
    make_car_state(vEgo=5.0, rightBlinker=True),
    True,
    0.0,
    make_plan(redLight=True),
    make_toggles(use_turn_desires=True, minimum_lane_change_speed=10.0),
  )

  assert helper.turn_stop_hold
  assert helper.desire == log.Desire.none


def test_turn_desire_released_after_stop_completes():
  helper = DesireHelper()
  toggles = make_toggles(use_turn_desires=True, minimum_lane_change_speed=10.0)

  helper.update(make_car_state(vEgo=5.0, rightBlinker=True), True, 0.0, make_plan(redLight=True), toggles)
  assert helper.desire == log.Desire.none

  helper.update(make_car_state(vEgo=0.0, rightBlinker=True, standstill=True), True, 0.0, make_plan(redLight=True), toggles)
  assert not helper.turn_stop_hold

  helper.update(make_car_state(vEgo=2.0, rightBlinker=True), True, 0.0, make_plan(), toggles)
  assert helper.desire == log.Desire.turnRight


def test_nav_desires_disabled_leave_desire_unchanged():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {"valid": True, "maneuverModifier": "left", "updatedAtMonotonic": monotonic()}

  helper.update(
    make_car_state(vEgo=5.0),
    True,
    0.0,
    make_plan(),
    make_toggles(minimum_lane_change_speed=10.0, nav_desires_allowed=False),
  )

  assert helper.desire == log.Desire.none


def test_disabling_nav_desires_clears_active_route_desire_immediately():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {"valid": True, "maneuverModifier": "slightRight", "updatedAtMonotonic": monotonic()}
  car_state = make_car_state(vEgo=20.0, steeringPressed=True, steeringTorque=-1.0)
  plan = make_plan(laneWidthRight=4.2)

  helper.update(car_state, True, 0.0, plan, make_toggles(nav_desires_allowed=True, nav_lane_positioning_allowed=True))
  assert helper.desire == log.Desire.keepRight

  helper.update(car_state, True, 0.0, plan, make_toggles(nav_desires_allowed=False, nav_lane_positioning_allowed=True))
  assert helper.desire == log.Desire.none


def test_nav_lane_positioning_requires_driver_confirmation():
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = {"valid": True, "maneuverModifier": "slightRight", "updatedAtMonotonic": monotonic()}

  helper.update(
    make_car_state(vEgo=20.0),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nav_desires_allowed=True, nav_lane_positioning_allowed=True, nudgeless=True),
  )

  assert helper.desire == log.Desire.none

  helper.update(
    make_car_state(vEgo=20.0, steeringPressed=True, steeringTorque=-1.0),
    True,
    0.0,
    make_plan(laneWidthRight=4.2),
    make_toggles(nav_desires_allowed=True, nav_lane_positioning_allowed=False, nudgeless=True),
  )

  assert helper.desire == log.Desire.none


def make_exit_state(**overrides):
  state = {
    "valid": True,
    "updatedAtMonotonic": monotonic(),
    "maneuverType": "off ramp",
    "maneuverModifier": "right",
    "maneuverPrimaryText": "CR 46 South",
    "maneuverDistance": 180.0,
  }
  state.update(overrides)
  return state


def make_exit_helper(**state_overrides):
  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = make_exit_state(**state_overrides)
  return helper


def step_exit(helper, car_state, toggles, lane_change_prob=0.0, plan=None, distance_step=0.0):
  if distance_step:
    distance = helper._nav_instruction_state["maneuverDistance"] - distance_step
    helper._nav_instruction_state = dict(helper._nav_instruction_state, maneuverDistance=distance, updatedAtMonotonic=monotonic())
  helper.update(car_state, True, lane_change_prob, plan or make_plan(), toggles)


def run_exit_lane_change(helper, car_state, toggles):
  # Blinker rising edge, then the assisted start on the next frame.
  step_exit(helper, car_state, toggles, distance_step=1.0)
  step_exit(helper, car_state, toggles, distance_step=1.0)
  assert helper.lane_change_state == LaneChangeState.laneChangeStarting
  assert helper.lane_change_direction == LaneChangeDirection.right
  for _ in range(200):
    if helper.lane_change_state not in (LaneChangeState.laneChangeStarting, LaneChangeState.laneChangeFinishing):
      break
    step_exit(helper, car_state, toggles, distance_step=1.0)
  assert helper.lane_change_state == LaneChangeState.preLaneChange


def test_nav_exit_right_starts_lane_change_immediately_and_holds_keep_right():
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=20.0, rightBlinker=True)

  run_exit_lane_change(helper, car_state, toggles)
  assert helper.nav_exit_lane_change_done

  desires = []
  for _ in range(40):
    step_exit(helper, car_state, toggles, distance_step=1.0)
    desires.append(helper.desire)
  assert desires.count(log.Desire.keepRight) >= 36
  assert set(desires) <= {log.Desire.keepRight, log.Desire.none}
  # Periodic one-frame gaps re-arm the rising edge modeld feeds to the model.
  assert any(a == log.Desire.none and b == log.Desire.keepRight for a, b in zip(desires, desires[1:], strict=False))

  # A new instruction (maneuver passed) ends the hold.
  helper._nav_instruction_state = make_exit_state(maneuverType="turn", maneuverPrimaryText="Main St", maneuverDistance=900.0)
  step_exit(helper, car_state, toggles)
  assert helper.desire == log.Desire.none
  assert not helper.nav_exit_lane_change_done
  # With the blinker still on, the normal nudgeless wait restarts instead of firing at once.
  assert helper.lane_change_state == LaneChangeState.preLaneChange
  for _ in range(30):
    step_exit(helper, car_state, toggles)
  assert helper.lane_change_state == LaneChangeState.preLaneChange


def test_nav_exit_left_fork_uses_keep_left():
  helper = make_exit_helper(maneuverType="fork", maneuverModifier="slightLeft")
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=25.0, leftBlinker=True)

  step_exit(helper, car_state, toggles)
  step_exit(helper, car_state, toggles)
  assert helper.lane_change_state == LaneChangeState.laneChangeStarting
  assert helper.lane_change_direction == LaneChangeDirection.left


def test_nav_exit_without_blinker_does_nothing():
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0)
  for _ in range(20):
    step_exit(helper, make_car_state(vEgo=20.0), toggles, distance_step=1.0)
    assert helper.lane_change_state == LaneChangeState.off
    assert helper.desire == log.Desire.none


def test_nav_exit_wrong_blinker_keeps_normal_lane_change_wait():
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=20.0, leftBlinker=True)
  for _ in range(5):
    step_exit(helper, car_state, toggles, distance_step=1.0)
  assert helper.lane_change_state == LaneChangeState.preLaneChange
  assert helper.lane_change_direction == LaneChangeDirection.left
  assert helper.nav_exit_direction == LaneChangeDirection.none
  assert helper.desire == log.Desire.none


def test_nav_exit_stale_instruction_does_nothing():
  helper = make_exit_helper(updatedAtMonotonic=monotonic() - 10.0)
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=20.0, rightBlinker=True)
  for _ in range(5):
    step_exit(helper, car_state, toggles)
  assert helper.lane_change_state == LaneChangeState.preLaneChange
  assert helper.nav_exit_direction == LaneChangeDirection.none


def test_nav_exit_disabled_nav_desires_does_nothing():
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0, nav_desires_allowed=False)
  car_state = make_car_state(vEgo=20.0, rightBlinker=True)
  for _ in range(5):
    step_exit(helper, car_state, toggles)
  assert helper.lane_change_state == LaneChangeState.preLaneChange


def test_nav_exit_blindspot_blocks_lane_change_and_hold():
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=20.0, rightBlinker=True, rightBlindspot=True)
  for _ in range(60):
    step_exit(helper, car_state, toggles)
    assert helper.lane_change_state == LaneChangeState.preLaneChange
    assert helper.desire == log.Desire.none

  # Blindspot appearing after the exit lane change suppresses the keep hold.
  helper = make_exit_helper()
  run_exit_lane_change(helper, make_car_state(vEgo=20.0, rightBlinker=True), toggles)
  step_exit(helper, car_state, toggles)
  assert helper.desire == log.Desire.none


def test_nav_exit_too_far_keeps_normal_behaviour():
  helper = make_exit_helper(maneuverDistance=450.0)
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=20.0, rightBlinker=True)
  for _ in range(5):
    step_exit(helper, car_state, toggles)
  assert helper.lane_change_state == LaneChangeState.preLaneChange
  for _ in range(40):
    step_exit(helper, car_state, toggles)
  assert helper.lane_change_state == LaneChangeState.laneChangeStarting


def test_nav_exit_lane_width_check_still_blocks_start():
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=20.0, rightBlinker=True)
  for _ in range(5):
    step_exit(helper, car_state, toggles, plan=make_plan(laneWidthRight=2.0))
  assert helper.lane_change_state == LaneChangeState.preLaneChange
  assert helper.desire == log.Desire.none


def test_nav_exit_low_speed_leaves_turn_logic_unchanged():
  # Below NAV_TURN_MAX_SPEED the exit assist stays out; routed turns behave as before.
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=12.0, rightBlinker=True)
  for _ in range(5):
    step_exit(helper, car_state, toggles)
  assert helper.lane_change_state == LaneChangeState.preLaneChange
  assert helper.nav_exit_direction == LaneChangeDirection.none

  helper = DesireHelper()
  helper._update_nav_params = lambda: None
  helper._nav_instruction_state = make_exit_state(maneuverType="turn", maneuverDistance=50.0)
  helper.update(make_car_state(vEgo=10.5, rightBlinker=True), True, 0.0, make_plan(), make_toggles(minimum_lane_change_speed=11.1))
  assert helper.desire == log.Desire.turnRight
  assert helper.nav_exit_direction == LaneChangeDirection.none


def test_nav_exit_driver_counter_torque_cancels_assist():
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0)
  step_exit(helper, make_car_state(vEgo=20.0, rightBlinker=True), toggles)
  step_exit(helper, make_car_state(vEgo=20.0, rightBlinker=True, steeringPressed=True, steeringTorque=1.0), toggles)
  assert helper.nav_exit_cancelled
  assert helper.lane_change_state == LaneChangeState.preLaneChange

  # Cancel stays latched: no shortcut start once the driver lets go.
  step_exit(helper, make_car_state(vEgo=20.0, rightBlinker=True), toggles)
  assert helper.lane_change_state == LaneChangeState.preLaneChange

  # Counter-torque after the lane change drops the keep hold too.
  helper = make_exit_helper()
  run_exit_lane_change(helper, make_car_state(vEgo=20.0, rightBlinker=True), toggles)
  step_exit(helper, make_car_state(vEgo=20.0, rightBlinker=True), toggles)
  assert helper.desire == log.Desire.keepRight
  step_exit(helper, make_car_state(vEgo=20.0, rightBlinker=True, steeringPressed=True, steeringTorque=1.0), toggles)
  assert helper.desire == log.Desire.none

  # Blinker off/on re-arms it.
  step_exit(helper, make_car_state(vEgo=20.0), toggles)
  assert not helper.nav_exit_cancelled


def test_nav_exit_only_first_lane_change_skips_wait():
  helper = make_exit_helper()
  toggles = make_toggles(lane_change_delay=2.0)
  car_state = make_car_state(vEgo=20.0, rightBlinker=True)
  run_exit_lane_change(helper, car_state, toggles)
  # The held blinker does not trigger a second automatic lane change toward the gore...
  for _ in range(80):
    step_exit(helper, car_state, toggles)
    assert helper.lane_change_state == LaneChangeState.preLaneChange
  # ...but a driver nudge still does.
  step_exit(helper, make_car_state(vEgo=20.0, rightBlinker=True, steeringPressed=True, steeringTorque=-1.0), toggles)
  assert helper.lane_change_state == LaneChangeState.laneChangeStarting
