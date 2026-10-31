"""A qualified current limit is ready before fresh SET, with RESUME preserved."""
from collections import deque
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch
import math

import pytest

from opendbc.car.dashboard_speed_limit import Status
from opendbc.car.structs import car
from openpilot.cereal import messaging
from openpilot.common.constants import CV
from openpilot.selfdrive.car import card, cruise
from openpilot.selfdrive.controls.plannerd import queue_cruise_event
from openpilot.starpilot.speed_limits import physical_actions
from openpilot.starpilot.speed_limits.runtime import Action, CruiseEvent, Runtime
from openpilot.starpilot.speed_limits.runtime_settings import parse
from openpilot.starpilot.speed_limits.speed_domain import OffsetBand, OffsetSchedule
from openpilot.starpilot.speed_limits.tests import test_runtime_replay as replay_fixture
from openpilot.starpilot.speed_limits.tests.test_maps_runtime import packet
from openpilot.starpilot.speed_limits.vision.observation import MODEL_ID


START = 2_000_000_000


def drive(*, metric=False, limit=45., offset=5., confirmation=True):
  fixture = replay_fixture.RuntimeReplayTests()
  fixture.setUp()
  sm, cp = fixture.sm, fixture.cp
  cp.pcmCruise = False
  sm['carState'].canValid = sm['carState'].cruiseState.available = True
  sm['carState'].vCruise = sm['carState'].vCruiseCluster = cruise.V_CRUISE_UNSET
  sm['carControl'].enabled = sm['carControl'].longActive = False
  units = CV.KPH_TO_MS if metric else CV.MPH_TO_MS
  sm['slcDashboardObservation'].speedMps = limit * units
  settings = replace(parse({'SpeedLimitController': True, 'SLCPriority1': 'Dashboard', 'SLCConfirmation': confirmation}),
                     offsets=OffsetSchedule((OffsetBand(0., None, offset * units),)))
  runtime = Runtime(settings, is_metric=metric)
  state = runtime.step(sm, cp, now_ns=START).message.slcState
  sm.data['slcState'] = state
  for flags in (sm.valid, sm.alive, sm.updated):
    flags['slcState'] = True
  sm.logMonoTime['slcState'] = START
  return runtime, sm, cp


def owner(sm, cp, *, metric=False, resume=None):
  instance = card.Car.__new__(card.Car)
  instance.CP, instance.sm = cp, sm
  instance.CC_prev = car.CarControl(enabled=False)
  instance.CS_prev = car.CarState(vEgo=sm['carState'].vEgo)
  instance.is_metric, instance.experimental_mode, instance.initial_cruise_speed = metric, False, 40
  instance.slc_control_enabled = instance.slc_replay = True
  instance.slc_source_floor_ns = 0
  instance.slc_producer_session, instance.slc_cruise_event_id = 'card-producer', 0
  instance.slc_receipts = []
  instance.v_cruise_helper = cruise.VCruiseHelper(cp)
  instance.vehicle_startup = Mock(consume_cruise_resume=lambda: resume)
  evidence = sm['slcDashboardObservation']
  observation = SimpleNamespace(status=Status.VALID, speed_mps=float(evidence.speedMps), episode=int(evidence.episode),
    observed_ns=int(evidence.observedMonoTime), valid_until_ns=int(evidence.validUntilMonoTime))
  instance.CI = Mock(CS=SimpleNamespace(dashboard_limit=SimpleNamespace(observation=observation)))
  return instance


def engage(instance, *, now=START + 10_000_000):
  sm = instance.sm
  sm.advance(now)
  sm['carControl'].enabled = sm['carControl'].longActive = True
  cs = car.CarState(canValid=sm['carState'].canValid, canTimeout=sm['carState'].canTimeout,
    vEgo=sm['carState'].vEgo, cruiseState={'available': True, 'enabled': True, 'speed': 60 / 3.6, 'speedCluster': 60 / 3.6})
  with patch.object(card.time, 'monotonic_ns', return_value=now), patch.object(cruise, 'monotonic_ns', return_value=now):
    instance.update_cruise_speed(cs)
  sm['carState'].vCruise = instance.v_cruise_helper.v_cruise_kph
  sm['carState'].vCruiseCluster = instance.v_cruise_helper.v_cruise_cluster_kph
  return cs


def receipt(instance, *, now=START + 10_000_000, event_id=1):
  kind, state, previous, selected, observed = instance.slc_receipts[-1]
  return CruiseEvent(event_id, observed, previous, selected, 'decel', instance.slc_producer_session, now,
                     kind, str(state.sessionId), int(state.decisionId), int(state.presentationId))


@pytest.mark.parametrize('confirmation', [False, True])
@pytest.mark.parametrize('metric,limit,offset', [(False, 45., 5.), (False, 20., -2.), (False, 55., -.4),
                                              (True, 72., 5.), (True, 30., -2.), (True, 72., -.4)])
def test_prepared_limit_initializes_set_once_and_adopts_it(metric, limit, offset, confirmation):
  runtime, sm, cp = drive(metric=metric, limit=limit, offset=offset, confirmation=confirmation)
  prepared = sm['slcState']
  assert prepared.observationKind == 'valid' and prepared.hasPresentationAdjustedLimit
  assert not sm['carControl'].enabled and prepared.presentationId > 0
  instance = owner(sm, cp, metric=metric)
  engage(instance)
  expected = cruise.slc_target_kph(float(prepared.presentationAdjustedLimit), metric)
  assert instance.v_cruise_helper.v_cruise_kph == expected
  assert instance.v_cruise_helper.v_cruise_cluster_kph == expected
  adopted = runtime.step(sm, cp, now_ns=START + 10_000_000, cruise_event=receipt(instance))
  assert not adopted.result.errors and adopted.message.slcState.hasAccepted
  assert not adopted.message.slcState.hasPending and not adopted.message.slcState.driverOverrideActive
  assert adopted.message.slcState.actionStatus == 'adopt' and adopted.command is None
  assert runtime.ledger.transactions == ()
  instance.CC_prev.enabled = True
  instance.slc_receipts.clear()
  engage(instance, now=START + 20_000_000)
  assert instance.v_cruise_helper.v_cruise_kph == expected and instance.slc_receipts == []


@pytest.mark.parametrize('invalid', ['disabled', 'stale', 'unknown', 'stock-long', 'can-fault', 'wrong-episode', 'configuration'])
def test_unavailable_limit_keeps_normal_initialization(invalid):
  _, sm, cp = drive()
  instance = owner(sm, cp)
  if invalid == 'disabled':
    instance.slc_control_enabled = False
  elif invalid == 'stale':
    sm['slcState'].frameMonoTime = START - physical_actions.STATE_MAX_AGE_NS
  elif invalid == 'unknown':
    sm['slcState'].observationKind = 'unknown'
  elif invalid == 'stock-long':
    cp.openpilotLongitudinalControl = False
  elif invalid == 'can-fault':
    sm['carState'].canTimeout = True
  elif invalid == 'wrong-episode':
    instance.CI.CS.dashboard_limit.observation.episode += 1
  else:
    instance.slc_source_floor_ns = START
  engage(instance)
  assert instance.v_cruise_helper.v_cruise_kph == 72.  # Existing vEgo-based initialization.
  assert instance.slc_receipts == []


def test_first_engagement_without_limit_keeps_default_floor():
  _, sm, cp = drive()
  sm['slcState'].observationKind = 'unknown'
  sm['carState'].vEgo = sm['carState'].vEgoCluster = 0.
  instance = owner(sm, cp)
  engage(instance)
  assert instance.v_cruise_helper.v_cruise_kph == cruise.V_CRUISE_INITIAL
  assert instance.slc_receipts == []


@pytest.mark.parametrize('resume', [True, None])
def test_resume_restores_previous_set_instead_of_available_limit(resume):
  _, sm, cp = drive()
  instance = owner(sm, cp, resume=resume)
  instance.v_cruise_helper.v_cruise_kph = instance.v_cruise_helper.v_cruise_cluster_kph = 105.
  if resume is None:
    instance.CS_prev.buttonEvents = [car.CarState.ButtonEvent(type='accelCruise', pressed=False)]
  engage(instance)
  assert instance.v_cruise_helper.v_cruise_kph == 105.
  assert instance.slc_receipts == []


def test_card_publication_routes_engagement_to_runtime_and_preserves_later_confirmation():
  runtime, sm, cp = drive()
  instance = owner(sm, cp)
  cs = engage(instance)
  instance.can_log_mono_time = START + 10_000_000
  instance.car_params_published, instance.aol_replay, instance.curve_replay = True, False, False
  instance.last_actuators_output = car.CarControl.Actuators()
  instance.can_rcv_cum_timeout_counter = 0
  instance.rk = SimpleNamespace(remaining=0.)
  instance.pm, instance.car_gps_publisher = Mock(), Mock()
  sm.frame, sm.all_checks = 1, lambda _: True
  cs.vCruise, cs.vCruiseCluster = instance.v_cruise_helper.v_cruise_kph, instance.v_cruise_helper.v_cruise_cluster_kph
  with patch.object(card, 'REPLAY', True):
    instance.state_publish(cs, None)
  published = next(call.args[1] for call in instance.pm.send.call_args_list if call.args[0] == 'slcCruiseEvent')
  events = deque()
  queue_cruise_event(published.as_reader(), events, deque())
  assert len(events) == 1 and events[0].kind == 'engagementAdopt'
  first = runtime.step(sm, cp, now_ns=START + 10_000_000, cruise_event=events.popleft())
  assert first.message.slcState.hasAccepted and first.command is None
  sm.advance(START + 50_000_000)
  sm['slcDashboardObservation'].speedMps = 55 * CV.MPH_TO_MS
  later = runtime.step(sm, cp, now_ns=START + 50_000_000)
  assert later.message.slcState.hasPending and later.command is None


@pytest.mark.parametrize('change', ['session', 'presentation', 'producer', 'replaced-source', 'changed-set', 'stale', 'replay'])
def test_engagement_receipt_cannot_adopt_unrelated_or_stale_work(change):
  runtime, sm, cp = drive()
  instance = owner(sm, cp)
  engage(instance)
  event = receipt(instance)
  if change == 'session':
    event = replace(event, session_id='old-drive')
  elif change == 'presentation':
    event = replace(event, presentation_id=event.presentation_id + 1)
  elif change == 'producer':
    event = replace(event, producer_session='old-card')
  elif change == 'replaced-source':
    sm['slcDashboardObservation'].episode += 1
    sm['slcDashboardObservation'].observedMonoTime = START + 5_000_000
  elif change == 'changed-set':
    sm['carState'].vCruise += 5.
  elif change == 'stale':
    event = replace(event, observed_ns=START - 100_000_000)
  else:
    runtime.step(sm, cp, now_ns=START + 10_000_000, cruise_event=event)
  output = runtime.step(sm, cp, now_ns=START + 10_000_000, cruise_event=event)
  assert output.message.slcState.actionStatus != 'adopt' and output.command is None
  assert runtime.ledger.transactions == ()


@pytest.mark.parametrize('target', [None, True, 0., -1., math.nan, math.inf, 146 / 3.6])
def test_initializer_rejects_invalid_targets(target):
  helper = cruise.VCruiseHelper(car.CarParams(pcmCruise=False, openpilotLongitudinalControl=True))
  assert not helper.initialize_v_cruise(car.CarState(), False, resume=False, slc_target_mps=target)
  assert helper.v_cruise_kph == cruise.V_CRUISE_INITIAL


def test_set_reengagement_clears_previous_decline():
  runtime, sm, cp = drive()
  sm['carControl'].enabled = sm['carControl'].longActive = True
  sm.advance(START + 1_000_000)
  pending = runtime.step(sm, cp, now_ns=START + 1_000_000).message.slcState
  sm.advance(START + 2_000_000)
  rejected = runtime.step(sm, cp, now_ns=START + 2_000_000,
    request=Action(runtime.session_id, 1, pending.decisionId, pending.presentationId, 'reject'))
  assert not rejected.message.slcState.hasPending and not rejected.message.slcState.hasAccepted
  sm.data['slcState'] = rejected.message.slcState
  instance = owner(sm, cp)
  engage(instance)
  adopted = runtime.step(sm, cp, now_ns=START + 10_000_000, cruise_event=receipt(instance))
  assert adopted.message.slcState.actionStatus == 'adopt' and adopted.message.slcState.hasAccepted
  assert not adopted.message.slcState.hasPending and adopted.command is None


def test_set_reengagement_clears_override_even_after_previous_application():
  runtime, sm, cp = drive()
  instance = owner(sm, cp)
  engage(instance)
  runtime.step(sm, cp, now_ns=START + 10_000_000, cruise_event=receipt(instance))
  previous = float(sm['carState'].vCruise) / 3.6
  sm.advance(START + 20_000_000)
  sm['carState'].vCruise = sm['carState'].vCruiseCluster = 105.
  overridden = runtime.step(sm, cp, now_ns=START + 20_000_000,
    cruise_event=CruiseEvent(2, START + 20_000_000, previous, 105 / 3.6, 'accel', 'card-producer', START + 20_000_000))
  assert overridden.message.slcState.driverOverrideActive
  sm.data['slcState'] = overridden.message.slcState
  instance.CC_prev.enabled = False
  instance.slc_receipts.clear()
  engage(instance, now=START + 30_000_000)
  adopted = runtime.step(sm, cp, now_ns=START + 30_000_000,
    cruise_event=receipt(instance, now=START + 30_000_000, event_id=3))
  assert adopted.message.slcState.actionStatus == 'adopt' and not adopted.message.slcState.driverOverrideActive
  assert adopted.message.slcState.commandStatus == 'applied' and adopted.command is None


@pytest.mark.parametrize('source', ['Maps', 'Vision'])
@pytest.mark.parametrize('dashboard_available', [True, False])
def test_engagement_uses_existing_priority_and_qualified_secondary_source(source, dashboard_available):
  runtime, sm, cp = drive()
  boot = START + 4_000_000_000
  settings = replace(runtime.settings, selection=parse({'SLCPriority1': 'Dashboard', 'SLCPriority2': source}).selection)
  runtime = Runtime(settings, vision_enabled=True, vision_control_qualified=True)
  sm['slcDashboardObservation'].status = 'valid' if dashboard_available else 'unknown'
  if source == 'Maps':
    road = packet(speedLimit=30., gpsMonoTime=boot - 50_000_000, computedMonoTime=boot)
    sm.data['mapdOut'] = road.mapdOut
    service = 'mapdOut'
  else:
    vision = messaging.new_message('slcVisionObservation').slcVisionObservation
    vision.vision = {'status': 'valid', 'modelId': MODEL_ID, 'stream': 'road', 'speedMps': 30., 'confidence': .9,
      'supportCount': 2, 'episode': 1, 'producerSessionId': 'vision', 'frameId': 1,
      'observedMonoTime': START - 50_000_000, 'validUntilMonoTime': START + 200_000_000, 'cameraFrameEofBootTime': boot - 50_000_000}
    sm.data['slcVisionObservation'] = vision
    service = 'slcVisionObservation'
  for flags in (sm.valid, sm.alive, sm.updated):
    flags[service] = True
  sm.logMonoTime[service] = boot if source == 'Maps' else START
  prepared = runtime.step(sm, cp, now_ns=START, now_boot_ns=boot).message.slcState
  expected_source = 'dashboard' if dashboard_available else ('map' if source == 'Maps' else 'vision')
  assert prepared.source == expected_source and prepared.hasPresentationAdjustedLimit
  sm.data['slcState'] = prepared
  instance = owner(sm, cp)
  engage(instance)
  expected = cruise.slc_target_kph(float(prepared.presentationAdjustedLimit), False)
  assert instance.v_cruise_helper.v_cruise_kph == expected
  # ReplaySM.advance uses monotonic stamps for every service; mapd uses boottime.
  if source == 'Maps':
    sm.logMonoTime['mapdOut'] = boot
  adopted = runtime.step(sm, cp, now_ns=START + 10_000_000, now_boot_ns=boot + 10_000_000, cruise_event=receipt(instance))
  assert adopted.message.slcState.acceptedSource == expected_source and not adopted.message.slcState.hasPending


@pytest.mark.parametrize('confirmation', [False, True])
def test_set_engagement_uses_current_limit_over_previous_early_proposal(confirmation):
  from openpilot.starpilot.speed_limits.tests.test_advance import Drive
  preview = Drive(confirm=confirmation)
  output = preview.tick()
  assert output.message.slcState.upcomingBoundaryId
  preview.sm['carControl'].enabled = preview.sm['carControl'].longActive = False
  prepared = preview.tick().message.slcState
  sm, cp = preview.sm, preview.cp
  sm.data['slcState'] = prepared
  sm.valid['slcState'] = sm.alive['slcState'] = True
  sm.logMonoTime['slcState'] = preview.now
  instance = owner(sm, cp, metric=True)
  stamp = preview.now + 10_000_000
  engage(instance, now=stamp)
  assert instance.v_cruise_helper.v_cruise_kph == 79.
  adopted = preview.tick(at=stamp, event=receipt(instance, now=stamp))
  assert adopted.message.slcState.acceptedSpeedLimit == 20.
  assert not adopted.message.slcState.hasPending and not adopted.message.slcState.upcomingBoundaryId
  assert adopted.message.slcState.actionStatus == 'adopt' and adopted.command is None


@pytest.mark.parametrize('current', [20., 25.])
def test_delayed_engagement_is_bound_to_current_limit(current):
  from openpilot.starpilot.speed_limits.tests.test_advance import Drive
  preview = Drive(confirm=True)
  assert preview.tick().message.slcState.upcomingBoundaryId
  preview.sm['carControl'].enabled = preview.sm['carControl'].longActive = False
  prepared = preview.tick().message.slcState
  sm, cp = preview.sm, preview.cp
  sm.data['slcState'] = prepared
  sm.valid['slcState'] = sm.alive['slcState'] = True
  sm.logMonoTime['slcState'] = preview.now
  instance = owner(sm, cp, metric=True)
  stamp = preview.now + 10_000_000
  engage(instance, now=stamp)
  event = receipt(instance, now=stamp)
  pending = preview.tick(at=stamp + 40_000_000, current=current).message.slcState
  delayed = preview.tick(at=stamp + 90_000_000, current=current, event=event)
  state = delayed.message.slcState
  assert not delayed.result.errors and delayed.command is None
  assert sm['carState'].vCruise == 79. and state.acceptedSpeedLimit == 20.
  assert (state.actionStatus == 'adopt') == (current == 20.)
  assert state.hasPending == (current != 20.)
  if current != 20.:
    assert state.presentationId != event.presentation_id
    assert state.decisionId == pending.decisionId
    assert state.pendingSinceMonoTime == pending.pendingSinceMonoTime
