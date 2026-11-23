"""Saved SLC lifecycle and model-frame integration shared by both planners."""

import json
import secrets
import time
from dataclasses import replace

from opendbc.car.tesla.speed_sync import selected as tesla_set_speed_selected
from openpilot.starpilot.car.tesla import set_speed as tesla_set_speed
from openpilot.cereal import messaging
from openpilot.cereal.services import SERVICE_LIST
from openpilot.starpilot.feature_runtime import enabled as feature_enabled, slc_runtime_settings, vision_control_enabled
from openpilot.starpilot.saved_source import read_saved
from openpilot.starpilot.speed_limits import history
from openpilot.starpilot.speed_limits.runtime import Action, CruiseEvent, Runtime as SlcRuntime
from openpilot.starpilot.speed_limits.runtime_settings import read_params as read_slc_settings

ACTION_MAX_AGE_NS = int(2e9 / SERVICE_LIST['modelV2'].frequency)
SLC_ACTIONS = ('accept', 'reject', 'adopt')
# commandApplied/commandRejected: card's answers to the Tesla set-speed rule's commands; no other car sends them.
SLC_CRUISE_EVENTS = ('driverChange', 'confirmationAccept', 'confirmationReject', 'engagementAdopt',
                     'commandApplied', 'commandRejected')


def map_data_available() -> bool:
  """F29: can this drive read Maps at all (packaged provider + a selected offline snapshot)?

  Cheap disk check only (no binary hash): the manager's full preflight still decides whether
  the provider runs; this only answers whether a remembered Maps limit has any data behind it.
  """
  try:
    from openpilot.starpilot.maps import shadow_lifecycle as shadow
    return bool(shadow.PROVIDER_BINARY.is_file() and shadow._owned_root(shadow.OFFLINE_ROOT, shadow.STORAGE_ANCHOR) and
                shadow._selected_snapshot(shadow.OFFLINE_ROOT))
  except Exception:
    return False


def restorable_previous_limit(previous, cp):
  """F29 (Accord 9G): no map data means no map limit.

  Upstream restores the last accepted limit on every drive, from any source, even when that
  source cannot produce data (no offline maps downloaded -> mapd never starts). On the 9G that
  re-applied a held Maps 45 mph (+offset = 53) on every engagement on 55 mph highways. Drop a
  remembered Maps limit when no map data can exist this drive; SET stays the target until a
  live source is accepted. The saved record is left untouched.
  """
  if (previous is not None and str(cp.carFingerprint) == 'HONDA_ACCORD_9G' and
      previous.candidate.source == 'map' and not map_data_available()):
    return None
  return previous


class SavedSlcLifecycle:
  """Refresh saved admission; offsets and display units preserve driver choices."""

  def __init__(self, params, cp, environment):
    self.params, self.cp, self.environment = params, cp, dict(environment)
    self.runtime = None
    self.configuration = None
    self.source_stability = False
    self.last_refresh_ns = None
    # Tesla set-speed rule: SLC's set-speed commands for card, from whichever planner hosts this lifecycle.
    self.command_sock = messaging.pub_sock('slcCruiseCommand') if tesla_set_speed_selected(cp) else None

  def source_services(self):
    services = ['slcDashboardObservation', 'slcVisionObservation', 'mapdOut']
    if feature_enabled(self.params, self.cp, 'aol', self.environment):
      services.append('aolAxisState')
    return services

  def refresh(self, now_ns: int, *, pending_actions=None, pending_cruise=None):
    if self.last_refresh_ns is not None and 0 <= now_ns - self.last_refresh_ns < 1_000_000_000:
      return self.runtime, False
    self.last_refresh_ns = now_ns
    # One immutable parsed snapshot owns this refresh. Repeated qualification
    # used to reopen the same saved keys five times in a due model iteration.
    saved_slc = read_slc_settings(self.params)
    admitted = feature_enabled(self.params, self.cp, 'slc', self.environment, saved_slc=saved_slc)
    settings = slc_runtime_settings(self.params, self.cp, self.environment, saved_slc=saved_slc)
    if self.command_sock is not None and tesla_set_speed.active(self.params, self.cp):
      # Tesla set-speed rule: SLC writes SET through card. Early adoption writes SET early (runtime._command), and the
      # accelerator-override choice is applied by card, which owns SET (tesla_set_speed_card.pedal_hold).
      settings = replace(settings, set_speed_rule=True)
    vision = admitted and feature_enabled(self.params, self.cp, 'vision', self.environment, saved_slc=saved_slc)
    configuration = (admitted and not settings.errors, settings, vision,
                     vision_control_enabled(self.params, self.cp, saved_slc=saved_slc),
                     feature_enabled(self.params, self.cp, 'vision', {}, saved_slc=saved_slc),
                     self.params.get_bool('IsMetric'))
    # F28 map/vision debounce: Accord 9G only, and only while SLCSourceStability is on (default off).
    stability = str(self.cp.carFingerprint) == 'HONDA_ACCORD_9G' and self.params.get_bool('SLCSourceStability')
    if configuration == self.configuration and stability == self.source_stability:
      return self.runtime, False
    previous_runtime = self.runtime
    # Who owns SET changed (the Tesla switch): start a new session rather than carry cap or command state across.
    continuing_control = bool(self.runtime is not None and self.runtime.settings.enabled and settings.enabled and configuration[0] and
                              self.runtime.settings.set_speed_rule == settings.set_speed_rule)
    timing_only = False
    preserve_runtime = continuing_control
    if self.runtime is not None and self.configuration is not None:
      old_admitted, old_settings, *old_display = self.configuration
      retimed = replace(old_settings, advance_higher_seconds=settings.advance_higher_seconds,
                        advance_lower_seconds=settings.advance_lower_seconds)
      timing_only = configuration == (old_admitted, retimed, *old_display)
      preserve_runtime |= configuration[:-1] == (old_admitted, replace(retimed, offsets=settings.offsets), *old_display[:-1])
    if stability != self.source_stability:
      preserve_runtime = timing_only = False  # F28: flipping the debounce builds a fresh runtime
    if preserve_runtime:
      assert self.runtime is not None and self.configuration is not None
      # Policy/source edits renew choices without releasing the engaged speed cap.
      choices_changed = (settings.selection != self.runtime.settings.selection or
                         settings.acceptance != self.runtime.settings.acceptance or configuration[2:5] != self.configuration[2:5])
      if choices_changed or settings.offsets != self.runtime.settings.offsets or configuration[5] != self.configuration[5]:
        self.runtime.update_offsets(settings.offsets, is_metric=configuration[5])
      if self.runtime.source_stability and (settings.selection != self.runtime.settings.selection or
                                            configuration[2:5] != self.configuration[2:5]):
        self.runtime.reset_source_stability()  # F28: a new source set starts a fresh debounce
      if (settings.advance_higher_seconds != self.runtime.settings.advance_higher_seconds or
          settings.advance_lower_seconds != self.runtime.settings.advance_lower_seconds):
        self.runtime.update_advance(settings.advance_higher_seconds, settings.advance_lower_seconds)
      if settings.wheel_override != self.runtime.settings.wheel_override:
        self.runtime.state = replace(self.runtime.state, wheel_override_metric=None, wheel_override_since_ns=0)
      self.runtime.settings = settings
      self.runtime.vision_enabled = vision
      self.runtime.vision_control_qualified = vision and configuration[3]
      self.runtime.vision_display_qualified = bool(vision and configuration[4] and settings.display and not settings.enabled)
    else:
      if self.runtime is not None:
        self.runtime.reset()
      session_id = secrets.token_hex(16)
      saved_history, _ = read_saved(self.params, 'SLCQualifiedHistory', history.MAX_BYTES)
      self.runtime = (SlcRuntime(settings, vision_enabled=vision,
                                 vision_control_qualified=configuration[3],
                                 vision_display_qualified=configuration[4], is_metric=configuration[5],
                                 session_id=session_id,
                                 previous_limit=restorable_previous_limit(history.decode(saved_history, session_id=session_id), self.cp),
                                 source_stability=stability)
                      if configuration[0] else None)
    self.configuration = configuration
    self.source_stability = stability
    if pending_actions is not None and not timing_only:
      pending_actions.clear()
    if pending_cruise is not None and (self.runtime is None or self.runtime is not previous_runtime):
      pending_cruise.clear()
    return self.runtime, True

  def step(self, sm, now_ns, pending_actions, pending_cruise, *, drive_changed, wheel_override_blocked=False):
    runtime = self.runtime
    if runtime is None:
      return None
    if drive_changed or runtime.state.reset_required or runtime.ledger.reset_required:
      runtime.reset()
      pending_actions.clear()
      pending_cruise.clear()
    while pending_actions and now_ns - pending_actions[0][0] > ACTION_MAX_AGE_NS:
      pending_actions.popleft()
    cruise_event = current_cruise_event(pending_cruise, now_ns, car_state_ns=sm.logMonoTime['carState'])
    request = (pending_actions.popleft()[1] if cruise_event is None and pending_actions and
               pending_actions[0][0] <= now_ns else None)
    previous_accepted = runtime.history_limit
    output = runtime.step(sm, self.cp, now_ns=now_ns, request=request, cruise_event=cruise_event,
                          confirmation_grace_ns=ACTION_MAX_AGE_NS, wheel_override_blocked=wheel_override_blocked)
    accepted = runtime.history_limit
    if accepted != previous_accepted:
      self.params.put("SLCQualifiedHistory", json.loads(history.encode(accepted, time.time_ns())) if accepted is not None else {})
    if output.command is not None and self.command_sock is not None:
      self.command_sock.send(output.command.to_bytes())
    return output


def receive_slc_events(sock):
  for _ in range(8):
    event = messaging.recv_one_or_none(sock)
    if event is None:
      break
    yield event


def cruise_event_from_message(event):
  cruise = event.slcCruiseEvent
  return CruiseEvent(int(cruise.eventId), int(cruise.observedMonoTime), float(cruise.previousMps),
                     float(cruise.selectedMps), str(cruise.button), str(cruise.producerSessionId),
                     int(event.logMonoTime), str(cruise.kind), str(cruise.sessionId), int(cruise.decisionId),
                     int(cruise.presentationId), int(cruise.commandId), int(cruise.wheelOverrideSince), bool(cruise.longPress))


def action_from_message(event):
  request = event.slcAction
  observed_ns = int(event.logMonoTime)
  return observed_ns, Action(str(request.sessionId), int(request.sequenceId), int(request.decisionId),
                             int(request.presentationId), str(request.kind), observed_ns, int(request.wheelAdoptMonoTime))


def current_cruise_event(events, now_ns: int, *, car_state_ns: int | None = None):
  while events and now_ns - events[0].observed_ns > ACTION_MAX_AGE_NS:
    events.popleft()
  if events and events[0].observed_ns <= now_ns and (car_state_ns is None or events[0].car_state_log_ns <= car_state_ns):
    return events.popleft()
  return None
