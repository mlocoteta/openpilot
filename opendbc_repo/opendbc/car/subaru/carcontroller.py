import numpy as np
from opendbc.can import CANPacker
from opendbc.car import Bus, DT_CTRL, make_tester_present_msg, structs
from opendbc.car.lateral import apply_driver_steer_torque_limits, apply_std_steer_angle_limits, apply_steer_angle_limits_vm, common_fault_avoidance
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.values import CAR, DBC, GLOBAL_ES_ADDR, CanBus, CarControllerParams, SubaruFlags
from opendbc.car.vehicle_model import VehicleModel

# FIXME: These limits aren't exact. The real limit is more than likely over a larger time period and
# involves the total steering angle change rather than rate, but these limits work well for now
MAX_STEER_RATE = 25  # deg/s
MAX_STEER_RATE_FRAMES = 7  # tx control frames needed before torque can be cut

_SNG_ACC_MIN_DIST = 3
_SNG_ACC_MAX_DIST = 4.5
_LEGACY_2025_MADS_MIN_SPEED = 0.44704
_LEGACY_2025_MADS_MAX_STEER_ANGLE = 120.0
_LEGACY_2025_OVERRIDE_HOLD_FRAMES = 10
_LEGACY_2025_REENGAGE_SETTLE_FRAMES = 8
_LEGACY_2025_REENGAGE_MAX_STEER_RATE = 2.0
_LEGACY_2025_REENGAGE_MAX_ANGLE_DELTA = 1.0
_LEGACY_2025_RECLAIM_FRAMES = 36
_LEGACY_2025_RECLAIM_EXPONENT = 2.5
_ASCENT_OVERRIDE_HOLD_FRAMES = 10
_ASCENT_REENGAGE_SETTLE_FRAMES = 8
_ASCENT_REENGAGE_MAX_STEER_RATE = 2.0
_ASCENT_REENGAGE_MAX_ANGLE_DELTA = 1.0
_ASCENT_RECLAIM_FRAMES = 36
_ASCENT_RECLAIM_EXPONENT = 2.5


def get_safety_CP():
  from opendbc.car.subaru.interface import CarInterface
  return CarInterface.get_non_essential_params("SUBARU_ASCENT")


class CarController(CarControllerBase):
  def __init__(self, dbc_names, CP):
    super().__init__(dbc_names, CP)
    self.apply_torque_last = 0
    self.apply_steer_last = 0
    self.driver_override = False
    self.legacy_2025_lkas_active = False
    self.legacy_2025_handoff_active = False
    self.legacy_2025_override_hold_frames = 0
    self.legacy_2025_reengage_settle_frames = 0
    self.legacy_2025_reengage_reference_angle = 0.0
    self.legacy_2025_reclaim_frames = 0
    self.legacy_2025_reclaim_start_angle = 0.0
    self.ascent_lkas_active = False
    self.ascent_handoff_active = False
    self.ascent_override_hold_frames = 0
    self.ascent_reengage_settle_frames = 0
    self.ascent_reengage_reference_angle = 0.0
    self.ascent_reclaim_frames = 0
    self.ascent_reclaim_start_angle = 0.0

    self.cruise_button_prev = 0
    self.steer_rate_counter = 0

    self.p = CarControllerParams(CP)
    self.packer = CANPacker(DBC[CP.carFingerprint][Bus.pt])
    self.main_bus = CanBus.main_for_cp(CP)
    self.angle_bus = CanBus.angle_for_cp(CP)
    self.status_bus = CanBus.camera if CP.flags & SubaruFlags.D_PLATFORM_CAMERA else CanBus.main

    if CP.flags & SubaruFlags.LKAS_ANGLE:
      self.VM = VehicleModel(get_safety_CP())

    self.prev_close_distance = 0
    self.epb_resume_frames_remaining = -1
    self.last_standstill_frame = 0

  def _reset_legacy_2025_handoff(self):
    self.legacy_2025_handoff_active = False
    self.legacy_2025_override_hold_frames = 0
    self.legacy_2025_reengage_settle_frames = 0
    self.legacy_2025_reengage_reference_angle = 0.0
    self.legacy_2025_reclaim_frames = 0
    self.legacy_2025_reclaim_start_angle = 0.0

  def _legacy_2025_manual_handoff(self, CS, lkas_available):
    if not lkas_available:
      self._reset_legacy_2025_handoff()
      return False

    if CS.out.steeringPressed:
      self.legacy_2025_handoff_active = True
      self.legacy_2025_override_hold_frames = _LEGACY_2025_OVERRIDE_HOLD_FRAMES
      self.legacy_2025_reengage_settle_frames = 0
      self.legacy_2025_reengage_reference_angle = CS.out.steeringAngleDeg
      self.legacy_2025_reclaim_frames = 0
      return True

    if not self.legacy_2025_handoff_active and not self.legacy_2025_lkas_active and \
       abs(CS.out.steeringRateDeg) > _LEGACY_2025_REENGAGE_MAX_STEER_RATE:
      self.legacy_2025_handoff_active = True
      self.legacy_2025_reengage_reference_angle = CS.out.steeringAngleDeg

    if not self.legacy_2025_handoff_active:
      return False

    if self.legacy_2025_override_hold_frames > 0:
      self.legacy_2025_override_hold_frames -= 1
      if self.legacy_2025_override_hold_frames == 0:
        self.legacy_2025_reengage_reference_angle = CS.out.steeringAngleDeg
      return True

    wheel_stable = abs(CS.out.steeringRateDeg) <= _LEGACY_2025_REENGAGE_MAX_STEER_RATE and \
      abs(CS.out.steeringAngleDeg - self.legacy_2025_reengage_reference_angle) <= _LEGACY_2025_REENGAGE_MAX_ANGLE_DELTA
    if wheel_stable:
      self.legacy_2025_reengage_settle_frames += 1
    else:
      self.legacy_2025_reengage_settle_frames = 0
      self.legacy_2025_reengage_reference_angle = CS.out.steeringAngleDeg

    if self.legacy_2025_reengage_settle_frames < _LEGACY_2025_REENGAGE_SETTLE_FRAMES:
      return True

    self.legacy_2025_handoff_active = False
    self.legacy_2025_reengage_settle_frames = 0
    self.legacy_2025_reclaim_frames = _LEGACY_2025_RECLAIM_FRAMES
    self.legacy_2025_reclaim_start_angle = CS.out.steeringAngleDeg
    return True

  def _legacy_2025_reclaim_target(self, target_angle):
    if self.legacy_2025_reclaim_frames <= 0:
      return target_angle

    progress = (_LEGACY_2025_RECLAIM_FRAMES - self.legacy_2025_reclaim_frames + 1) / _LEGACY_2025_RECLAIM_FRAMES
    eased_progress = progress ** _LEGACY_2025_RECLAIM_EXPONENT
    target_angle = self.legacy_2025_reclaim_start_angle + eased_progress * \
      (target_angle - self.legacy_2025_reclaim_start_angle)
    self.legacy_2025_reclaim_frames -= 1
    return target_angle

  def _reset_ascent_handoff(self):
    self.ascent_handoff_active = False
    self.ascent_override_hold_frames = 0
    self.ascent_reengage_settle_frames = 0
    self.ascent_reengage_reference_angle = 0.0
    self.ascent_reclaim_frames = 0
    self.ascent_reclaim_start_angle = 0.0

  def _ascent_manual_handoff(self, CS, lat_active):
    if not lat_active:
      self._reset_ascent_handoff()
      return False

    if CS.out.steeringPressed:
      self.ascent_handoff_active = True
      self.ascent_override_hold_frames = _ASCENT_OVERRIDE_HOLD_FRAMES
      self.ascent_reengage_settle_frames = 0
      self.ascent_reengage_reference_angle = CS.out.steeringAngleDeg
      self.ascent_reclaim_frames = 0
      return True

    if not self.ascent_handoff_active and not self.ascent_lkas_active and \
       abs(CS.out.steeringRateDeg) > _ASCENT_REENGAGE_MAX_STEER_RATE:
      self.ascent_handoff_active = True
      self.ascent_reengage_reference_angle = CS.out.steeringAngleDeg

    if not self.ascent_handoff_active:
      return False

    if self.ascent_override_hold_frames > 0:
      self.ascent_override_hold_frames -= 1
      if self.ascent_override_hold_frames == 0:
        self.ascent_reengage_reference_angle = CS.out.steeringAngleDeg
      return True

    wheel_stable = abs(CS.out.steeringRateDeg) <= _ASCENT_REENGAGE_MAX_STEER_RATE and \
      abs(CS.out.steeringAngleDeg - self.ascent_reengage_reference_angle) <= _ASCENT_REENGAGE_MAX_ANGLE_DELTA
    if wheel_stable:
      self.ascent_reengage_settle_frames += 1
    else:
      self.ascent_reengage_settle_frames = 0
      self.ascent_reengage_reference_angle = CS.out.steeringAngleDeg

    if self.ascent_reengage_settle_frames < _ASCENT_REENGAGE_SETTLE_FRAMES:
      return True

    self.ascent_handoff_active = False
    self.ascent_reengage_settle_frames = 0
    self.ascent_reclaim_frames = _ASCENT_RECLAIM_FRAMES
    self.ascent_reclaim_start_angle = CS.out.steeringAngleDeg
    return True

  def _ascent_reclaim_target(self, target_angle):
    if self.ascent_reclaim_frames <= 0:
      return target_angle

    progress = (_ASCENT_RECLAIM_FRAMES - self.ascent_reclaim_frames + 1) / _ASCENT_RECLAIM_FRAMES
    eased_progress = progress ** _ASCENT_RECLAIM_EXPONENT
    target_angle = self.ascent_reclaim_start_angle + eased_progress * \
      (target_angle - self.ascent_reclaim_start_angle)
    self.ascent_reclaim_frames -= 1
    return target_angle

  def lateral_angle(self, CC, CS):
    if self.CP.carFingerprint == CAR.SUBARU_LEGACY_2025:
      mads_only = CC.latActive and not CC.enabled
      mads_only_ok = CS.out.vEgoRaw > _LEGACY_2025_MADS_MIN_SPEED and \
        abs(CS.out.steeringAngleDeg) < _LEGACY_2025_MADS_MAX_STEER_ANGLE
      lkas_available = CC.latActive and (not mads_only or mads_only_ok) and \
        CS.out.gearShifter == structs.CarState.GearShifter.drive and not CS.out.standstill

      manual_handoff = self._legacy_2025_manual_handoff(CS, lkas_available)
      lkas_active = lkas_available and not manual_handoff

      steer_target = self._legacy_2025_reclaim_target(CC.actuators.steeringAngleDeg) if lkas_active else CC.actuators.steeringAngleDeg
      apply_steer = apply_std_steer_angle_limits(
        steer_target,
        self.apply_steer_last,
        CS.out.vEgoRaw,
        CS.out.steeringAngleDeg,
        lkas_active,
        self.p.LEGACY_2025_ANGLE_LIMITS,
      )
      self.apply_steer_last = apply_steer
      self.legacy_2025_lkas_active = lkas_active
      return subarucan.create_steering_control_angle(self.packer, apply_steer, lkas_active, self.angle_bus)

    if self.CP.carFingerprint == CAR.SUBARU_ASCENT_2023:
      manual_handoff = self._ascent_manual_handoff(CS, CC.latActive)
      lkas_active = CC.latActive and not manual_handoff

      if lkas_active and not self.ascent_lkas_active:
        self.apply_steer_last = CS.out.steeringAngleDeg

      steer_target = self._ascent_reclaim_target(CC.actuators.steeringAngleDeg) if lkas_active else CC.actuators.steeringAngleDeg
      apply_steer = apply_std_steer_angle_limits(
        steer_target,
        self.apply_steer_last,
        CS.out.vEgoRaw,
        CS.out.steeringAngleDeg,
        lkas_active,
        self.p.FIXED_ANGLE_LIMITS,
      )
      self.apply_steer_last = apply_steer
      self.ascent_lkas_active = lkas_active
      return subarucan.create_steering_control_angle(self.packer, apply_steer, lkas_active, self.angle_bus)

    abs_torque = abs(CS.out.steeringTorque)
    if abs_torque > self.p.STEER_OVERRIDE_TORQUE_HIGH:
      self.driver_override = True
    elif abs_torque < self.p.STEER_OVERRIDE_TORQUE_LOW:
      self.driver_override = False

    lat_active = CC.latActive and not self.driver_override
    apply_steer = apply_steer_angle_limits_vm(
      CC.actuators.steeringAngleDeg,
      self.apply_steer_last,
      CS.out.vEgoRaw,
      CS.out.steeringAngleDeg,
      lat_active,
      self.p,
      self.VM,
    )

    if not lat_active:
      apply_steer = CS.out.steeringAngleDeg

    self.apply_steer_last = apply_steer
    return subarucan.create_steering_control_angle(self.packer, apply_steer, lat_active, self.angle_bus)

  def lateral_torque(self, CC, CS):
    apply_torque = int(round(CC.actuators.torque * self.p.STEER_MAX))
    apply_torque = apply_driver_steer_torque_limits(apply_torque, self.apply_torque_last, CS.out.steeringTorque, self.p)

    if not CC.latActive:
      apply_torque = 0

    self.apply_torque_last = apply_torque

    if self.CP.flags & SubaruFlags.PREGLOBAL:
      return subarucan.create_preglobal_steering_control(
        self.packer, self.frame // self.p.STEER_STEP, apply_torque, CC.latActive,
      )

    apply_steer_req = CC.latActive
    if self.CP.flags & SubaruFlags.STEER_RATE_LIMITED:
      self.steer_rate_counter, apply_steer_req = common_fault_avoidance(
        abs(CS.out.steeringRateDeg) > MAX_STEER_RATE,
        apply_steer_req,
        self.steer_rate_counter,
        MAX_STEER_RATE_FRAMES,
      )

    return subarucan.create_steering_control(self.packer, apply_torque, apply_steer_req)

  def update(self, CC, CS, now_nanos, starpilot_toggles):
    actuators = CC.actuators
    hud_control = CC.hudControl
    pcm_cancel_cmd = CC.cruiseControl.cancel

    can_sends = []

    # *** steering ***
    if (self.frame % self.p.STEER_STEP) == 0:
      if self.CP.flags & SubaruFlags.LKAS_ANGLE:
        can_sends.append(self.lateral_angle(CC, CS))
      else:
        can_sends.append(self.lateral_torque(CC, CS))

    # *** stop and go ***
    subaru_sng_manual_parking_brake = getattr(starpilot_toggles, "subaru_sng_manual_parking_brake", False)
    if starpilot_toggles.subaru_sng:
      throttle_cmd, speed_cmd = self.stop_and_go(CC, CS, subaru_sng_manual_parking_brake)

    # *** longitudinal ***

    if CC.longActive:
      apply_throttle = int(round(np.interp(actuators.accel, CarControllerParams.THROTTLE_LOOKUP_BP, CarControllerParams.THROTTLE_LOOKUP_V)))
      apply_rpm = int(round(np.interp(actuators.accel, CarControllerParams.RPM_LOOKUP_BP, CarControllerParams.RPM_LOOKUP_V)))
      apply_brake = int(round(np.interp(actuators.accel, CarControllerParams.BRAKE_LOOKUP_BP, CarControllerParams.BRAKE_LOOKUP_V)))

      # limit min and max values
      cruise_throttle = np.clip(apply_throttle, CarControllerParams.THROTTLE_MIN, CarControllerParams.THROTTLE_MAX)
      cruise_rpm = np.clip(apply_rpm, CarControllerParams.RPM_MIN, CarControllerParams.RPM_MAX)
      cruise_brake = np.clip(apply_brake, CarControllerParams.BRAKE_MIN, CarControllerParams.BRAKE_MAX)
    else:
      cruise_throttle = CarControllerParams.THROTTLE_INACTIVE
      cruise_rpm = CarControllerParams.RPM_MIN
      cruise_brake = CarControllerParams.BRAKE_MIN

    # *** alerts and pcm cancel ***
    if self.CP.flags & SubaruFlags.PREGLOBAL:
      if self.frame % 5 == 0:
        # 1 = main, 2 = set shallow, 3 = set deep, 4 = resume shallow, 5 = resume deep
        # disengage ACC when OP is disengaged
        if pcm_cancel_cmd:
          cruise_button = 1
        # turn main on if off and past start-up state
        elif not CS.out.cruiseState.available and CS.ready:
          cruise_button = 1
        else:
          cruise_button = CS.cruise_button

        # unstick previous mocked button press
        if cruise_button == 1 and self.cruise_button_prev == 1:
          cruise_button = 0
        self.cruise_button_prev = cruise_button

        can_sends.append(subarucan.create_preglobal_es_distance(self.packer, cruise_button, CS.es_distance_msg))

      if starpilot_toggles.subaru_sng:
        can_sends.append(subarucan.create_preglobal_throttle(self.packer, CS.throttle_msg["COUNTER"] + 1, CS.throttle_msg,
                                                             throttle_cmd))
        if self.frame % 2 == 0:
          can_sends.append(subarucan.create_preglobal_brake_pedal(self.packer, CS.brake_pedal_msg,
                                                                  speed_cmd))
    else:
      if self.frame % 10 == 0:
        can_sends.append(subarucan.create_es_dashstatus(self.packer, self.frame // 10, CS.es_dashstatus_msg, CC.enabled,
                                                        self.CP.openpilotLongitudinalControl, CC.longActive, hud_control.leadVisible,
                                                        self.status_bus))

        can_sends.append(subarucan.create_es_lkas_state(self.packer, self.frame // 10, CS.es_lkas_state_msg, CC.latActive, hud_control.visualAlert,
                                                        hud_control.leftLaneVisible, hud_control.rightLaneVisible,
                                                        hud_control.leftLaneDepart, hud_control.rightLaneDepart, self.status_bus))

        if self.CP.flags & SubaruFlags.SEND_INFOTAINMENT:
          can_sends.append(subarucan.create_es_infotainment(self.packer, self.frame // 10, CS.es_infotainment_msg,
                                                           hud_control.visualAlert, self.status_bus))

      if starpilot_toggles.subaru_sng:
        can_sends.append(subarucan.create_throttle(self.packer, CS.throttle_msg["COUNTER"] + 1, CS.throttle_msg,
                                                   throttle_cmd))
        if self.frame % 2 == 0:
          can_sends.append(subarucan.create_brake_pedal(self.packer, self.frame // 2, CS.brake_pedal_msg,
                                                        speed_cmd, pcm_cancel_cmd))

      if self.CP.openpilotLongitudinalControl:
        if self.frame % 5 == 0:
          can_sends.append(subarucan.create_es_status(self.packer, self.frame // 5, CS.es_status_msg,
                                                      self.CP.openpilotLongitudinalControl, CC.longActive, cruise_rpm))

          can_sends.append(subarucan.create_es_brake(self.packer, self.frame // 5, CS.es_brake_msg,
                                                     self.CP.openpilotLongitudinalControl, CC.longActive, cruise_brake))

          can_sends.append(subarucan.create_es_distance(self.packer, self.frame // 5, CS.es_distance_msg, 0, pcm_cancel_cmd,
                                                        self.CP.openpilotLongitudinalControl, cruise_brake > 0, cruise_throttle))
      else:
        if pcm_cancel_cmd:
          if not (self.CP.flags & SubaruFlags.HYBRID):
            bus = CanBus.alt_for_cp(self.CP) if self.CP.flags & SubaruFlags.GLOBAL_GEN2 else self.main_bus
            can_sends.append(subarucan.create_es_distance(self.packer, CS.es_distance_msg["COUNTER"] + 1, CS.es_distance_msg, bus, pcm_cancel_cmd))

      if self.CP.flags & SubaruFlags.DISABLE_EYESIGHT:
        # Tester present (keeps eyesight disabled)
        if self.frame % 100 == 0:
          can_sends.append(make_tester_present_msg(GLOBAL_ES_ADDR, CanBus.camera, suppress_response=True))

        # Create all of the other eyesight messages to keep the rest of the car happy when eyesight is disabled
        if self.frame % 5 == 0:
          can_sends.append(subarucan.create_es_highbeamassist(self.packer))

        if self.frame % 10 == 0:
          can_sends.append(subarucan.create_es_static_1(self.packer))

        if self.frame % 2 == 0:
          can_sends.append(subarucan.create_es_static_2(self.packer))

    new_actuators = actuators.as_builder()
    if self.CP.flags & SubaruFlags.LKAS_ANGLE:
      new_actuators.steeringAngleDeg = self.apply_steer_last
    else:
      new_actuators.torque = self.apply_torque_last / self.p.STEER_MAX
      new_actuators.torqueOutputCan = self.apply_torque_last

    self.frame += 1
    return new_actuators, can_sends

  def stop_and_go(self, CC, CS, manual_parking_brake=False):
    throttle_cmd = False
    speed_cmd = False

    if not CC.enabled or not CC.hudControl.leadVisible:
      return throttle_cmd, speed_cmd

    close_distance = CS.close_distance
    if not CS.out.standstill:
      self.last_standstill_frame = self.frame

    standstill_timers = (0.75, 0.8) if self.CP.flags & SubaruFlags.PREGLOBAL else (0.5, 0.55)
    standstill_duration = (self.frame - self.last_standstill_frame) * DT_CTRL
    in_standstill_hold = standstill_duration > standstill_timers[0]
    if standstill_duration >= standstill_timers[1]:
      self.last_standstill_frame = self.frame

    if manual_parking_brake or not (self.CP.flags & SubaruFlags.PREGLOBAL):
      speed_cmd = in_standstill_hold

    should_resume = (
      CS.out.standstill and
      _SNG_ACC_MIN_DIST < close_distance < _SNG_ACC_MAX_DIST and
      close_distance > self.prev_close_distance
    )
    if should_resume:
      self.epb_resume_frames_remaining = 15

    throttle_cmd = self.epb_resume_frames_remaining > 0
    if self.epb_resume_frames_remaining > 0:
      self.epb_resume_frames_remaining -= 1

    self.prev_close_distance = close_distance
    return throttle_cmd, speed_cmd
