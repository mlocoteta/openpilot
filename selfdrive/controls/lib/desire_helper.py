import json
from time import monotonic

import numpy as np

from cereal import log
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL

LaneChangeState = log.LaneChangeState
LaneChangeDirection = log.LaneChangeDirection

LANE_CHANGE_SPEED_MIN = 20 * CV.MPH_TO_MS
LANE_CHANGE_TIME_MAX = 10.
NAV_TURN_MAX_SPEED = 14.0
NAV_TURN_PREVIEW_SECONDS = 6.0
NAV_TURN_MIN_DISTANCE = 35.0
NAV_TURN_MAX_DISTANCE = 90.0
NAV_INSTRUCTION_MAX_AGE = 2.5
# A driver normally signals an intersection before slowing below the lane-change
# speed threshold. Use the route to classify that early signal so it does not
# start a lane change while approaching the matching turn.
NAV_TURN_SIGNAL_LEAD_TIME = 12.0
NAV_TURN_SIGNAL_BASE_DISTANCE = 15.0
NAV_TURN_SIGNAL_MIN_DISTANCE = 30.0
NAV_TURN_SIGNAL_MAX_DISTANCE = 250.0
NAV_KEEP_DISTANCE_SPEED_BREAKPOINTS = [0.0, 15.0, 30.0]
NAV_KEEP_DISTANCE_BREAKPOINTS = [25.0, 90.0, 160.0]
NAV_KEEP_AMBIGUOUS_SPLIT_DISTANCE_SCALE = 0.6
NAV_KEEP_SMALL_SPLIT_MAX_OTHER_LANES = 2
# Highway exit/fork assist: with the driver's matching blinker and a routed
# off ramp/fork close ahead, start the lane change without the nudgeless wait,
# then keep pulsing keepLeft/keepRight so the model commits to the ramp.
NAV_EXIT_MANEUVER_TYPES = ("off ramp", "fork")
NAV_EXIT_LEFT_MODIFIERS = ("slightLeft", "left", "sharpLeft")
NAV_EXIT_RIGHT_MODIFIERS = ("slightRight", "right", "sharpRight")
NAV_EXIT_PREVIEW_SECONDS = 10.0
NAV_EXIT_MIN_DISTANCE = 150.0
NAV_EXIT_MAX_DISTANCE = 400.0
# Once an exit episode is underway, keep holding while the car slows on the ramp approach.
NAV_EXIT_HOLD_MIN_SPEED = 11.0
NAV_EXIT_DISTANCE_RESET_JUMP = 50.0
# modeld only feeds desire rising edges to the model, so re-pulse the keep desire.
NAV_EXIT_KEEP_PULSE_PERIOD = 1.0

DESIRES = {
  LaneChangeDirection.none: {
    LaneChangeState.off: log.Desire.none,
    LaneChangeState.preLaneChange: log.Desire.none,
    LaneChangeState.laneChangeStarting: log.Desire.none,
    LaneChangeState.laneChangeFinishing: log.Desire.none,
  },
  LaneChangeDirection.left: {
    LaneChangeState.off: log.Desire.none,
    LaneChangeState.preLaneChange: log.Desire.none,
    LaneChangeState.laneChangeStarting: log.Desire.laneChangeLeft,
    LaneChangeState.laneChangeFinishing: log.Desire.laneChangeLeft,
  },
  LaneChangeDirection.right: {
    LaneChangeState.off: log.Desire.none,
    LaneChangeState.preLaneChange: log.Desire.none,
    LaneChangeState.laneChangeStarting: log.Desire.laneChangeRight,
    LaneChangeState.laneChangeFinishing: log.Desire.laneChangeRight,
  },
}

TurnDirection = log.Desire

TURN_DESIRES = {
  TurnDirection.none: log.Desire.none,
  TurnDirection.turnLeft: log.Desire.turnLeft,
  TurnDirection.turnRight: log.Desire.turnRight,
}


class DesireHelper:
  def __init__(self):
    self.params_memory = Params(memory=True)
    self.lane_change_state = LaneChangeState.off
    self.lane_change_direction = LaneChangeDirection.none
    self.lane_change_timer = 0.0
    self.lane_change_ll_prob = 1.0
    self.keep_pulse_timer = 0.0
    self.prev_one_blinker = False
    self.desire = log.Desire.none

    self.turn_stop_hold = False

    self.lane_change_completed = False

    self.lane_change_wait_timer = 0.0
    self.nav_desires_allowed = False
    self.nav_lane_positioning_allowed = False
    self._nav_instruction_state_raw: object = None
    self._nav_instruction_state: dict[str, object] = {}

    self.nav_exit_direction = LaneChangeDirection.none
    self._reset_nav_exit_episode()

  def _reset_nav_exit_episode(self):
    self.nav_exit_key: tuple | None = None
    self.nav_exit_last_distance: float | None = None
    self.nav_exit_started = False
    self.nav_exit_lane_change_done = False
    self.nav_exit_cancelled = False
    self.nav_exit_keep_timer = 0.0

  def _update_nav_params(self):
    raw = self.params_memory.get("NavInstructionState") or {}
    if raw == self._nav_instruction_state_raw:
      return

    self._nav_instruction_state_raw = raw
    if not raw:
      self._nav_instruction_state = {}
      return

    if isinstance(raw, dict):
      self._nav_instruction_state = raw
      return

    if isinstance(raw, str):
      try:
        parsed = json.loads(raw)
        self._nav_instruction_state = parsed if isinstance(parsed, dict) else {}
        return
      except Exception:
        pass

    self._nav_instruction_state = {}

  @staticmethod
  def _nav_keep_direction_is_clear(carstate, lane_change_direction):
    return not (
      (lane_change_direction == LaneChangeDirection.left and carstate.leftBlindspot) or
      (lane_change_direction == LaneChangeDirection.right and carstate.rightBlindspot)
    )

  @staticmethod
  def _nav_torque_applied(carstate, lane_change_direction):
    return carstate.steeringPressed and (
      (lane_change_direction == LaneChangeDirection.left and carstate.steeringTorque > 0) or
      (lane_change_direction == LaneChangeDirection.right and carstate.steeringTorque < 0)
    )

  @staticmethod
  def _nav_turn_is_imminent(carstate, maneuver_distance):
    try:
      distance = float(maneuver_distance)
    except (TypeError, ValueError):
      return False

    preview_distance = float(np.clip(
      max(float(carstate.vEgo), 0.0) * NAV_TURN_PREVIEW_SECONDS,
      NAV_TURN_MIN_DISTANCE,
      NAV_TURN_MAX_DISTANCE,
    ))
    return 0.0 <= distance <= preview_distance

  def _nav_instruction_is_fresh(self):
    try:
      updated_at = float(self._nav_instruction_state["updatedAtMonotonic"])
    except (KeyError, TypeError, ValueError):
      return False
    age = monotonic() - updated_at
    return 0.0 <= age <= NAV_INSTRUCTION_MAX_AGE

  @staticmethod
  def _nav_turn_signal_matches(carstate, nav_instruction_state):
    if not bool(nav_instruction_state.get("valid", False)):
      return False
    if str(nav_instruction_state.get("maneuverType", "")).strip().lower() != "turn":
      return False

    modifier = str(nav_instruction_state.get("maneuverModifier", "")).strip()
    matching_signal = (
      modifier in ("left", "sharpLeft") and carstate.leftBlinker and not carstate.rightBlinker
    ) or (
      modifier in ("right", "sharpRight") and carstate.rightBlinker and not carstate.leftBlinker
    )
    if not matching_signal:
      return False

    try:
      maneuver_distance = float(nav_instruction_state.get("maneuverDistance", 0.0))
    except (TypeError, ValueError):
      return False

    signal_distance = float(np.clip(
      NAV_TURN_SIGNAL_BASE_DISTANCE + max(float(carstate.vEgo), 0.0) * NAV_TURN_SIGNAL_LEAD_TIME,
      NAV_TURN_SIGNAL_MIN_DISTANCE,
      NAV_TURN_SIGNAL_MAX_DISTANCE,
    ))
    return 0.0 <= maneuver_distance <= signal_distance

  @staticmethod
  def _nudgeless_enabled(starpilot_toggles, controls_enabled):
    nudgeless = bool(getattr(starpilot_toggles, "nudgeless", False))
    if getattr(starpilot_toggles, "nudgeless_lane_change_only_when_engaged", False):
      nudgeless &= bool(controls_enabled)
    return nudgeless

  @staticmethod
  def _nav_should_delay_ambiguous_split(maneuver_type="", same_side_lane_count=0, lane_count=0):
    if maneuver_type not in ("off ramp", "fork") or int(same_side_lane_count or 0) <= 1:
      return False

    total_lanes = int(lane_count or 0)
    if total_lanes <= 0:
      return True

    other_lanes = max(total_lanes - int(same_side_lane_count or 0), 0)
    return other_lanes <= NAV_KEEP_SMALL_SPLIT_MAX_OTHER_LANES

  @staticmethod
  def _nav_keep_is_imminent(carstate, maneuver_distance, maneuver_type="", same_side_lane_count=0, lane_count=0):
    try:
      distance = float(maneuver_distance)
    except (TypeError, ValueError):
      return False

    threshold = float(np.interp(carstate.vEgo, NAV_KEEP_DISTANCE_SPEED_BREAKPOINTS, NAV_KEEP_DISTANCE_BREAKPOINTS))
    if DesireHelper._nav_should_delay_ambiguous_split(maneuver_type, same_side_lane_count, lane_count):
      threshold *= NAV_KEEP_AMBIGUOUS_SPLIT_DISTANCE_SCALE
    return distance <= threshold

  @staticmethod
  def _nav_should_suppress_edge_lane_keep(nav_instruction_state):
    maneuver_type = str(nav_instruction_state.get("maneuverType", ""))
    if maneuver_type not in ("off ramp", "fork"):
      return False

    active_lane_direction = str(nav_instruction_state.get("activeLaneDirection", ""))
    if active_lane_direction not in ("slightLeft", "left", "sharpLeft", "slightRight", "right", "sharpRight"):
      return False

    same_side_lane_count = int(nav_instruction_state.get("sameSideLaneCount", 0) or 0)
    lane_count = int(nav_instruction_state.get("laneCount", 0) or 0)

    return (
      DesireHelper._nav_should_delay_ambiguous_split(maneuver_type, same_side_lane_count, lane_count) and
      bool(nav_instruction_state.get("activeLaneAtRoadEdge", False)) and
      bool(nav_instruction_state.get("hasSharedSameSideLane", False))
    )

  @staticmethod
  def _nav_effective_modifier(nav_instruction_state, carstate, maneuver_distance):
    modifier = str(nav_instruction_state.get("maneuverModifier", ""))
    maneuver_type = str(nav_instruction_state.get("maneuverType", ""))
    active_lane_direction = str(nav_instruction_state.get("activeLaneDirection", ""))
    same_side_lane_count = int(nav_instruction_state.get("sameSideLaneCount", 0) or 0)
    lane_count = int(nav_instruction_state.get("laneCount", 0) or 0)

    if maneuver_type in ("off ramp", "fork") and modifier in ("slightLeft", "left", "sharpLeft", "slightRight", "right", "sharpRight"):
      if not DesireHelper._nav_keep_is_imminent(carstate, maneuver_distance, maneuver_type, same_side_lane_count, lane_count):
        return ""

      if DesireHelper._nav_should_suppress_edge_lane_keep(nav_instruction_state):
        return ""

      if active_lane_direction in ("slightLeft", "left"):
        return "slightLeft"
      if active_lane_direction in ("slightRight", "right"):
        return "slightRight"

      # If lane guidance says the active lane stays straight, don't reinterpret the
      # broader fork/off-ramp maneuver as a late turn into another branch.
      return ""

    return modifier

  def _navigation_desire(self, carstate, lateral_active, starpilotPlan, starpilot_toggles):
    self._update_nav_params()
    self.nav_desires_allowed = bool(getattr(starpilot_toggles, "nav_desires_allowed", self.nav_desires_allowed))
    self.nav_lane_positioning_allowed = bool(
      getattr(starpilot_toggles, "nav_lane_positioning_allowed", self.nav_lane_positioning_allowed)
    )
    if not self.nav_desires_allowed or not lateral_active or not bool(self._nav_instruction_state.get("valid", False)) or not self._nav_instruction_is_fresh():
      return log.Desire.none

    maneuver_distance = self._nav_instruction_state.get("maneuverDistance", 0.0)
    modifier = self._nav_effective_modifier(self._nav_instruction_state, carstate, maneuver_distance)
    if modifier == "":
      return log.Desire.none

    if modifier in ("left", "sharpLeft", "right", "sharpRight") and str(self._nav_instruction_state.get("maneuverType", "")).strip().lower() != "turn":
      return log.Desire.none

    if modifier == "slightLeft":
      if not self.nav_lane_positioning_allowed:
        return log.Desire.none
      lane_change_direction = LaneChangeDirection.left
      desired_lane_width = starpilotPlan.laneWidthLeft
      if not carstate.rightBlinker and self._nav_keep_direction_is_clear(carstate, lane_change_direction):
        if desired_lane_width >= starpilot_toggles.lane_detection_width and self._nav_torque_applied(carstate, lane_change_direction):
          return log.Desire.keepLeft
    elif modifier == "slightRight":
      if not self.nav_lane_positioning_allowed:
        return log.Desire.none
      lane_change_direction = LaneChangeDirection.right
      desired_lane_width = starpilotPlan.laneWidthRight
      if not carstate.leftBlinker and self._nav_keep_direction_is_clear(carstate, lane_change_direction):
        if desired_lane_width >= starpilot_toggles.lane_detection_width and self._nav_torque_applied(carstate, lane_change_direction):
          return log.Desire.keepRight
    elif modifier in ("left", "sharpLeft"):
      if self.turn_stop_hold:
        return log.Desire.none
      turn_allowed = carstate.leftBlinker and not carstate.rightBlinker and not carstate.leftBlindspot
      turn_allowed &= 0.0 <= carstate.vEgo < NAV_TURN_MAX_SPEED and not carstate.standstill
      if turn_allowed and self._nav_turn_is_imminent(carstate, maneuver_distance):
        return log.Desire.turnLeft
    elif modifier in ("right", "sharpRight"):
      if self.turn_stop_hold:
        return log.Desire.none
      turn_allowed = carstate.rightBlinker and not carstate.leftBlinker and not carstate.rightBlindspot
      turn_allowed &= 0.0 <= carstate.vEgo < NAV_TURN_MAX_SPEED and not carstate.standstill
      if turn_allowed and self._nav_turn_is_imminent(carstate, maneuver_distance):
        return log.Desire.turnRight

    return log.Desire.none

  def _update_nav_exit_assist(self, carstate, lateral_active):
    """Return the routed exit side the driver is signaling for, or none."""
    state = self._nav_instruction_state
    direction = LaneChangeDirection.none
    maneuver_type = str(state.get("maneuverType", "")).strip().lower()
    modifier = str(state.get("maneuverModifier", "")).strip()
    try:
      distance = float(state.get("maneuverDistance", -1.0))
    except (TypeError, ValueError):
      distance = -1.0

    if self.nav_desires_allowed and lateral_active and bool(state.get("valid", False)) and self._nav_instruction_is_fresh() \
        and maneuver_type in NAV_EXIT_MANEUVER_TYPES:
      if modifier in NAV_EXIT_RIGHT_MODIFIERS:
        direction = LaneChangeDirection.right
      elif modifier in NAV_EXIT_LEFT_MODIFIERS:
        direction = LaneChangeDirection.left

    blinker_matches = (
      (direction == LaneChangeDirection.right and carstate.rightBlinker and not carstate.leftBlinker) or
      (direction == LaneChangeDirection.left and carstate.leftBlinker and not carstate.rightBlinker)
    )

    key = (maneuver_type, modifier, str(state.get("maneuverPrimaryText", "")))
    distance_jumped = self.nav_exit_last_distance is not None and distance > self.nav_exit_last_distance + NAV_EXIT_DISTANCE_RESET_JUMP
    if not blinker_matches or key != self.nav_exit_key or distance_jumped:
      self._reset_nav_exit_episode()
    self.nav_exit_key = key
    self.nav_exit_last_distance = distance

    if not blinker_matches:
      return LaneChangeDirection.none

    episode_underway = self.nav_exit_started or self.nav_exit_lane_change_done
    min_speed = NAV_EXIT_HOLD_MIN_SPEED if episode_underway else NAV_TURN_MAX_SPEED
    preview_distance = float(np.clip(max(float(carstate.vEgo), 0.0) * NAV_EXIT_PREVIEW_SECONDS,
                                     NAV_EXIT_MIN_DISTANCE, NAV_EXIT_MAX_DISTANCE))
    if carstate.vEgo < min_speed or not 0.0 <= distance <= preview_distance:
      return LaneChangeDirection.none

    # Driver steering away from the exit cancels the assist until the blinker or instruction resets.
    if carstate.steeringPressed and (
      (direction == LaneChangeDirection.right and carstate.steeringTorque > 0) or
      (direction == LaneChangeDirection.left and carstate.steeringTorque < 0)
    ):
      self.nav_exit_cancelled = True
    if self.nav_exit_cancelled:
      return LaneChangeDirection.none

    return direction

  @staticmethod
  def get_lane_change_direction(CS):
    return LaneChangeDirection.left if CS.leftBlinker else LaneChangeDirection.right

  def update(self, carstate, lateral_active, lane_change_prob, starpilotPlan, starpilot_toggles, controls_enabled=None):
    v_ego = carstate.vEgo
    one_blinker = carstate.leftBlinker != carstate.rightBlinker
    below_lane_change_speed = v_ego < starpilot_toggles.minimum_lane_change_speed

    self._update_nav_params()
    self.nav_desires_allowed = bool(getattr(starpilot_toggles, "nav_desires_allowed", self.nav_desires_allowed))
    nav_turn_signal = self.nav_desires_allowed and self._nav_instruction_is_fresh() and self._nav_turn_signal_matches(carstate, self._nav_instruction_state)
    self.nav_exit_direction = self._update_nav_exit_assist(carstate, lateral_active)

    stop_imminent = (bool(getattr(starpilotPlan, "redLight", False))
                     or bool(getattr(starpilotPlan, "forcingStop", False))
                     or bool(getattr(starpilotPlan, "stopSignConfirmed", False)))
    if carstate.standstill or not one_blinker:
      self.turn_stop_hold = False
    elif stop_imminent:
      self.turn_stop_hold = True

    cruise_state = getattr(carstate, "cruiseState", None)
    controls_enabled = bool(getattr(cruise_state, "enabled", False)) if controls_enabled is None else bool(controls_enabled)
    nudgeless_enabled = self._nudgeless_enabled(starpilot_toggles, controls_enabled)
    lane_changes_allowed = starpilot_toggles.lane_changes
    lane_changes_allowed &= not getattr(starpilot_toggles, "lane_changes_require_cruise", False) or bool(getattr(cruise_state, "enabled", False))

    lane_change_time_max = getattr(starpilot_toggles, 'lane_change_time_max', LANE_CHANGE_TIME_MAX)
    if not lateral_active or self.lane_change_timer > lane_change_time_max or not lane_changes_allowed:
      self.lane_change_state = LaneChangeState.off
      self.lane_change_direction = LaneChangeDirection.none
    else:
      if nav_turn_signal and self.lane_change_state == LaneChangeState.preLaneChange:
        self.lane_change_state = LaneChangeState.off
        self.lane_change_direction = LaneChangeDirection.none

      # LaneChangeState.off
      if (self.lane_change_state == LaneChangeState.off and one_blinker and not self.prev_one_blinker
          and not below_lane_change_speed and not nav_turn_signal):
        self.lane_change_state = LaneChangeState.preLaneChange
        self.lane_change_ll_prob = 1.0
        # Initialize lane change direction to prevent UI alert flicker
        self.lane_change_direction = self.get_lane_change_direction(carstate)

      # LaneChangeState.preLaneChange
      elif self.lane_change_state == LaneChangeState.preLaneChange:
        # Update lane change direction
        self.lane_change_direction = self.get_lane_change_direction(carstate)

        torque_applied = carstate.steeringPressed and \
                         ((carstate.steeringTorque > 0 and self.lane_change_direction == LaneChangeDirection.left) or
                          (carstate.steeringTorque < 0 and self.lane_change_direction == LaneChangeDirection.right))

        blindspot_detected = ((carstate.leftBlindspot and self.lane_change_direction == LaneChangeDirection.left) or
                              (carstate.rightBlindspot and self.lane_change_direction == LaneChangeDirection.right))

        # The first lane change toward a signaled, routed exit skips the nudgeless wait.
        nav_exit_skip_wait = self.nav_exit_direction == self.lane_change_direction and not self.nav_exit_started
        # While holding toward the ramp, a still-on blinker must not trigger another automatic lane change
        # (it would steer into the gore); the driver can still nudge for one.
        nav_exit_holding = self.nav_exit_direction == self.lane_change_direction and self.nav_exit_lane_change_done

        if torque_applied:
          self.lane_change_wait_timer = starpilot_toggles.lane_change_delay
        else:
          torque_applied |= nudgeless_enabled and not nav_exit_holding
          if nav_exit_holding:
            # Restart the full nudgeless wait once the hold ends (e.g. instruction advances past the exit).
            self.lane_change_wait_timer = 0.0
          torque_applied &= self.lane_change_wait_timer >= starpilot_toggles.lane_change_delay or nav_exit_skip_wait

          desired_lane_width = starpilotPlan.laneWidthLeft if self.lane_change_direction == LaneChangeDirection.left else starpilotPlan.laneWidthRight
          torque_applied &= desired_lane_width >= starpilot_toggles.lane_detection_width

        if not one_blinker or below_lane_change_speed or self.lane_change_completed:
          self.lane_change_state = LaneChangeState.off
          self.lane_change_direction = LaneChangeDirection.none
        elif torque_applied and not blindspot_detected:
          self.lane_change_state = LaneChangeState.laneChangeStarting
          if self.nav_exit_direction == self.lane_change_direction:
            self.nav_exit_started = True

          self.lane_change_completed = starpilot_toggles.one_lane_change

          self.lane_change_wait_timer = 0.0

        self.lane_change_wait_timer += DT_MDL

      # LaneChangeState.laneChangeStarting
      elif self.lane_change_state == LaneChangeState.laneChangeStarting:
        # fade out over .5s
        self.lane_change_ll_prob = max(self.lane_change_ll_prob - 2 * DT_MDL, 0.0)

        # 98% certainty
        if lane_change_prob < 0.02 and self.lane_change_ll_prob < 0.01:
          self.lane_change_state = LaneChangeState.laneChangeFinishing

      # LaneChangeState.laneChangeFinishing
      elif self.lane_change_state == LaneChangeState.laneChangeFinishing:
        # fade in laneline over 1s
        self.lane_change_ll_prob = min(self.lane_change_ll_prob + DT_MDL, 1.0)

        if self.lane_change_ll_prob > 0.99:
          if self.nav_exit_direction == self.lane_change_direction:
            self.nav_exit_lane_change_done = True
          self.lane_change_direction = LaneChangeDirection.none
          if one_blinker:
            self.lane_change_state = LaneChangeState.preLaneChange
          else:
            self.lane_change_state = LaneChangeState.off

    if self.lane_change_state in (LaneChangeState.off, LaneChangeState.preLaneChange):
      self.lane_change_timer = 0.0
    else:
      self.lane_change_timer += DT_MDL

    self.prev_one_blinker = one_blinker

    if lateral_active and one_blinker and below_lane_change_speed and not carstate.standstill \
        and starpilot_toggles.use_turn_desires and not self.turn_stop_hold:
      self.turn_direction = TurnDirection.turnLeft if carstate.leftBlinker else TurnDirection.turnRight
      self.desire = TURN_DESIRES[self.turn_direction]
    else:
      self.turn_direction = TurnDirection.none
      self.desire = DESIRES[self.lane_change_direction][self.lane_change_state]

    # Send keep pulse once per second during LaneChangeStart.preLaneChange
    if self.lane_change_state in (LaneChangeState.off, LaneChangeState.laneChangeStarting):
      self.keep_pulse_timer = 0.0
    elif self.lane_change_state == LaneChangeState.preLaneChange:
      self.keep_pulse_timer += DT_MDL
      if self.keep_pulse_timer > 1.0:
        self.keep_pulse_timer = 0.0
      elif self.desire in (log.Desire.keepLeft, log.Desire.keepRight):
        self.desire = log.Desire.none

    if not one_blinker:
      self.lane_change_completed = False

      self.lane_change_wait_timer = 0.0

    nav_desire = self._navigation_desire(carstate, lateral_active, starpilotPlan, starpilot_toggles)
    if nav_desire != log.Desire.none and self.lane_change_state == LaneChangeState.off:
      self.desire = nav_desire
      if nav_desire in (log.Desire.turnLeft, log.Desire.turnRight):
        self.turn_direction = nav_desire

    # After the lane change toward the exit, keep pulsing keepLeft/keepRight so the model takes the ramp.
    nav_exit_hold = (self.nav_exit_lane_change_done and self.nav_exit_direction != LaneChangeDirection.none and
                     self.lane_change_state in (LaneChangeState.off, LaneChangeState.preLaneChange) and
                     self.desire == log.Desire.none and
                     self._nav_keep_direction_is_clear(carstate, self.nav_exit_direction))
    if nav_exit_hold:
      self.nav_exit_keep_timer += DT_MDL
      if self.nav_exit_keep_timer >= NAV_EXIT_KEEP_PULSE_PERIOD:
        # Drop one frame so the next keep request is a fresh rising edge for the model.
        self.nav_exit_keep_timer = 0.0
      else:
        self.desire = log.Desire.keepLeft if self.nav_exit_direction == LaneChangeDirection.left else log.Desire.keepRight
    else:
      self.nav_exit_keep_timer = 0.0
