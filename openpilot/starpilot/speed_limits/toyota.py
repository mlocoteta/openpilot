"""Native Toyota cruise prerequisites, owned beside Card's software SET."""

import math
from typing import cast

from openpilot.selfdrive.car.cruise import ButtonType, SlcPendingConfirmation, V_CRUISE_UNSET, slc_target_kph
from openpilot.starpilot.speed_limits.physical_actions import adoption_speed


def eligible(cp) -> bool:
  if cp.brand != 'toyota' or not cp.pcmCruise or not cp.openpilotLongitudinalControl:
    return False
  from opendbc.car.toyota.values import ToyotaFlags
  return not (cp.flags & ToyotaFlags.GAS_INTERCEPTOR or cp.notCar or cp.passive or cp.dashcamOnly)


def _speed(value: float) -> bool:
  return math.isfinite(value) and 0 < value < V_CRUISE_UNSET


def projection(sm, now_ns: int):
  stamp = int(sm.logMonoTime.get('starpilotCarState', 0))
  car_stamp = int(sm.logMonoTime.get('carState', 0))
  if not (sm.valid.get('starpilotCarState', False) and sm.alive.get('starpilotCarState', False) and
          0 < stamp <= now_ns and now_ns - stamp <= 100_000_000):
    return None
  parent = sm['starpilotCarState']
  if not (parent.toyotaCruise.version == 1 and int(parent.sourceCarStateMonoTime) == stamp and
          stamp <= car_stamp <= now_ns and car_stamp - stamp <= 20_000_000):
    return None
  row = parent.toyotaCruise
  if not (_speed(float(row.nativeKph)) and _speed(float(row.nativeClusterKph))):
    return None
  if row.status in ('ready', 'raise_dash', 'release_plus', 'cancelled') and not (
      row.sessionId and row.acceptedMonoTime > 0 and _speed(float(row.targetKph)) and _speed(float(row.approvedTargetMps))):
    return None
  return row


class ToyotaCruise:
  def __init__(self):
    self.owns_target = False
    self.engaged = False
    self.valid = False
    self.native_kph = self.native_cluster_kph = 0.0
    self.status = ''
    self.target_kph = 0.0
    self.approved_target_mps = 0.0
    self.approval = None
    self.last_approval = None
    self.last_adoption = None
    self.cancelled = None
    self.plus_held = False
    self.requested = None
    self.manual_step = None
    self.resume_kph = None
    self.metric = True

  def capacity(self, target_kph: float) -> bool:
    # Compare the two independent integer CAN readings in their display units;
    # never learn a calibration from their transient difference.
    units = 1.0 if self.metric else 0.6213711922
    target = round(target_kph * units)
    return self.valid and min(round(self.native_kph * units), round(self.native_cluster_kph * units)) >= target

  def constrain(self, helper) -> None:
    if self.valid:
      step = self.manual_step
      if step is not None:
        previous_kph, previous_cluster_kph, button, long_press = step
        requested = cast(tuple[float, float], self.requested)
        ready = self.capacity(requested[1])
        helper.v_cruise_kph, helper.v_cruise_cluster_kph = requested if ready or button == 'decel' else (previous_kph, previous_cluster_kph)
      helper.v_cruise_kph = min(helper.v_cruise_kph, self.native_kph)
      helper.v_cruise_cluster_kph = min(helper.v_cruise_cluster_kph, self.native_cluster_kph)
      if step is not None:
        current = (float(helper.v_cruise_kph), float(helper.v_cruise_cluster_kph))
        if (current[0] > previous_kph if button == 'accel' else current[0] < previous_kph):
          helper.slc_cruise_change = (previous_kph / 3.6, current[0] / 3.6, button, long_press)
        if ready or button == 'decel':
          self.manual_step = None
          self.requested = current
        else:
          self.manual_step = (*current, button, long_press)

  def update(self, helper, cs, enabled: bool, slc_enabled: bool, approved, metric: bool) -> bool:
    self.metric = metric
    # An unrelated CAN fault must not lose a physical release and leave guidance stuck.
    for edge in cs.buttonEvents:
      if edge.type == ButtonType.accelCruise:
        self.plus_held = bool(edge.pressed)
    healthy = bool(cs.canValid and not cs.canTimeout)
    active = bool(cs.cruiseState.enabled and cs.cruiseState.available)
    rising = healthy and active and not self.engaged
    if healthy:
      if self.owns_target and helper.v_cruise_initialized:
        self.resume_kph = helper.v_cruise_cluster_kph
      if not active:
        self.owns_target = False
      self.engaged = active
    self.valid = bool(healthy and cs.cruiseState.available and
                      _speed(cs.cruiseState.speed * 3.6) and _speed(cs.cruiseState.speedCluster * 3.6))
    self.status = ''
    if not (self.valid and active and enabled):
      self.requested = self.manual_step = None
    if not self.valid:
      return slc_enabled or self.owns_target
    self.native_kph = float(cs.cruiseState.speed * 3.6)
    self.native_cluster_kph = float(cs.cruiseState.speedCluster * 3.6)
    if active and slc_enabled and enabled:
      self.owns_target = True
    off_notice = not rising and self.resume_kph is not None and abs(self.resume_kph - self.native_cluster_kph) > 0.1
    mode = slc_enabled or self.owns_target
    self.target_kph = 0.0
    self.approved_target_mps = 0.0
    self.approval = None
    if (slc_enabled and approved is not None and approved.hasAccepted and not approved.hasPending and
        approved.hasAcceptedAdjustedLimit and approved.acceptedMonoTime > 0 and
        adoption_speed(approved) is not None and
        abs(float(approved.acceptedSpeedLimit) - adoption_speed(approved)) <= 0.02):
      self.target_kph = slc_target_kph(float(approved.acceptedAdjustedLimit), metric)
      self.approved_target_mps = float(approved.acceptedAdjustedLimit)
      self.approval = (str(approved.sessionId), int(approved.acceptedMonoTime), self.target_kph)
      adoption = (str(approved.sessionId), int(approved.actionSequenceId))
      readopted = (not approved.driverOverrideActive and approved.actionStatus == 'adopt' and
                   adoption[1] > 0 and adoption != self.last_adoption)
      if self.approval != self.last_approval or readopted:
        self.requested = self.manual_step = None
      if readopted:
        self.last_adoption = adoption
        self.cancelled = None
      self.last_approval = self.approval
    can_prepare = self.approval is not None and not approved.driverOverrideActive
    for edge in cs.buttonEvents:
      if edge.type == ButtonType.accelCruise:
        if mode and edge.pressed and (rising or not active or cs.standstill or cs.cruiseState.standstill):
          # Native RES must not also become a software speed step on release.
          helper.slc_suppressed_buttons.add(ButtonType.accelCruise)
      elif edge.type == ButtonType.decelCruise:
        if edge.pressed:
          self.manual_step = None
          self.cancelled = self.approval or self.last_approval
    if mode and (rising or not helper.v_cruise_initialized):
      seed = self.resume_kph if self.resume_kph is not None else self.native_cluster_kph
      if can_prepare and self.cancelled != self.approval:
        seed = min(seed, self.target_kph)
      helper.v_cruise_kph = helper.v_cruise_cluster_kph = seed
    if mode and active and enabled and helper.v_cruise_initialized:
      if (self.requested is None or rising or self.manual_step is None and not cs.buttonEvents and
          not any(helper.button_timers.values()) and self.capacity(self.requested[1])):
        self.requested = (float(helper.v_cruise_kph), float(helper.v_cruise_cluster_kph))
    else:
      self.requested = self.manual_step = None
    if slc_enabled:
      if not active or not enabled:
        self.status = 'inactive'
      elif self.approval is not None:
        if self.cancelled == self.approval:
          self.status = 'cancelled'
        elif can_prepare:
          if not self.capacity(self.target_kph):
            self.status = 'raise_dash'
          elif self.plus_held and (self.target_kph > helper.v_cruise_cluster_kph + 0.1 or
                                  ButtonType.accelCruise in helper.slc_suppressed_buttons):
            self.status = 'release_plus'
          else:
            self.status = 'ready'
      if (can_prepare and self.cancelled != self.approval and self.plus_held and
          self.target_kph > helper.v_cruise_cluster_kph + 0.1 and
          not (rising or cs.standstill or cs.cruiseState.standstill)):
        button = ButtonType.accelCruise
        if button not in helper.slc_suppressed_buttons:
          helper.slc_suppressed_buttons.add(button)
          helper.slc_suppression_owner[button] = SlcPendingConfirmation(
            str(approved.sessionId), int(approved.decisionId), int(approved.presentationId))
    elif off_notice:
      self.status = 'off_hold' if mode else 'off_resume' if not active else ''
      self.target_kph = self.native_cluster_kph
    return mode

  def can_apply(self, target_mps: float) -> bool:
    target_kph = slc_target_kph(target_mps, self.metric)
    return self.status == 'ready' and self.owns_target and self.capacity(target_kph) and abs(target_kph - self.target_kph) < 0.05

  def publish(self, row) -> None:
    row.version = 1 if self.valid else 0
    row.status = self.status
    row.targetKph = self.target_kph
    row.nativeKph = self.native_kph
    row.nativeClusterKph = self.native_cluster_kph
    row.approvedTargetMps = self.approved_target_mps
    if self.approval is not None:
      row.sessionId, row.acceptedMonoTime = self.approval[:2]
