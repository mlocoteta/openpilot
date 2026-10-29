"""Toyota preparation changes execution, not SLC approval or native cruise SET."""

from types import SimpleNamespace

import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.structs import car
from opendbc.car.toyota.interface import CarInterface
from opendbc.car.toyota.prius_sdsu import RETROFIT_EPS
from opendbc.car.toyota.values import CAR, ToyotaFlags
from openpilot.cereal import messaging
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.selfdrive.car.cruise import CRUISE_LONG_PRESS, IMPERIAL_INCREMENT, VCruiseHelper, SlcPendingConfirmation, V_CRUISE_MIN, slc_target_kph
from openpilot.starpilot.car.toyota.tests.test_pedal_caller_native import firmware
from openpilot.starpilot.longitudinal.cruise_intervals import read_cruise_intervals
from openpilot.starpilot.speed_limits.runtime import Action, CruiseEvent, Runtime
from openpilot.starpilot.speed_limits.runtime_settings import parse
from openpilot.starpilot.speed_limits.tests import test_runtime_replay as replay
from openpilot.starpilot.speed_limits.toyota import eligible, projection


@pytest.fixture(params=[
  pytest.param((CAR.TOYOTA_COROLLA_TSS2, {}, False), id='native-tss2'),
  pytest.param((CAR.TOYOTA_PRIUS, {0: {0x2FF: 8}}, False), id='prius-sdsu'),
  pytest.param((CAR.TOYOTA_PRIUS, {0: {0x2FF: 4}}, False), id='prius-advert'),
  pytest.param((CAR.TOYOTA_PRIUS, {0: {0x2FF: 8}}, True), id='prius-eps-mod'),
  pytest.param((CAR.TOYOTA_PRIUS_RETROFIT, {0: {0x2FF: 8}}, True), id='prius-retrofit-sdsu'),
  pytest.param((CAR.TOYOTA_PRIUS_RETROFIT, {0: {0x2FF: 4}}, True), id='prius-retrofit-advert'),
  pytest.param((CAR.TOYOTA_COROLLA, {0: {0x2FF: 8}}, False), id='tssp-corolla'),
  pytest.param((CAR.TOYOTA_PRIUS_V, {0: {0x2FF: 8}}, False), id='tssp-prius-v'),
  pytest.param((CAR.LEXUS_IS, {0: {0x2FF: 8}}, False), id='tssp-alternate-main'),
  pytest.param((CAR.TOYOTA_RAV4, {2: {0x343: 8}}, False), id='tssp-dsu-bypass'),
  pytest.param((CAR.TOYOTA_CAMRY, {0: {0x2AA: 8}}, False), id='tssp-radar-filter'),
  pytest.param((CAR.TOYOTA_RAV4_TSS2_2022, {}, False), id='tss2-radar-disabled'),
])
def helper(request):
  candidate, sources, eps_mod = request.param
  fp = gen_empty_fingerprint()
  fp.update(sources)
  fw = firmware(CAR.TOYOTA_PRIUS if candidate == CAR.TOYOTA_PRIUS_RETROFIT else candidate)
  if eps_mod:
    for row in fw:
      if row.ecu == car.CarParams.Ecu.eps:
        row.fwVersion = RETROFIT_EPS
  cp = CarInterface.get_params(candidate, fp, fw, True, False, False)
  assert cp.pcmCruise and cp.openpilotLongitudinalControl and not cp.flags & ToyotaFlags.GAS_INTERCEPTOR
  assert eligible(cp)
  result = VCruiseHelper(cp)
  result.v_cruise_kph = result.v_cruise_cluster_kph = 50.0
  assert result.toyota is not None
  result.toyota.engaged = result.toyota.owns_target = True
  return result


def state(native=60., cluster=None, *, active=True, button=None, pressed=True, stopped=False):
  return car.CarState(canValid=True, standstill=stopped,
    cruiseState={'available': True, 'enabled': active, 'speed': native / 3.6,
                 'speedCluster': (native if cluster is None else cluster) / 3.6, 'standstill': stopped},
    buttonEvents=[] if button is None else [car.CarState.ButtonEvent(type=button, pressed=pressed)])


def approval(target=70., accepted=1):
  return SimpleNamespace(hasAccepted=True, hasPending=False, driverOverrideActive=False, hasAcceptedAdjustedLimit=True,
    acceptedMonoTime=accepted, acceptedSpeedLimit=target / 3.6, speedLimit=target / 3.6,
    acceptedAdjustedLimit=target / 3.6, sessionId='drive', decisionId=0, presentationId=1, actionSequenceId=0, actionStatus='')


def update(helper, cs, approved=None, *, enabled=True, slc=True, metric=True, pending=None):
  helper.update_v_cruise(cs, enabled, metric, pending, slc_enabled=slc, slc_approved=approved)


@pytest.fixture(params=[False, True], ids=['normal-steps', 'swapped-steps'])
def swap(helper, tmp_path, request):
  params = Params(str(tmp_path))
  params.put_bool('ReverseCruise', request.param, block=True)
  params.put('CustomCruise', 3., block=True)
  params.put('CustomCruiseLong', 7., block=True)
  helper.intervals = read_cruise_intervals(params, helper.CP)
  return request.param


@pytest.mark.parametrize('metric', [False, True])
@pytest.mark.parametrize('button,sign', [('accelCruise', 1), ('decelCruise', -1)])
@pytest.mark.parametrize('held', [False, True])
def test_saved_toyota_steps_apply_to_slc_set_speed(helper, swap, metric, button, sign, held):
  increment = 1. if metric else IMPERIAL_INCREMENT
  initial = 70. if metric else slc_target_kph(50 * CV.MPH_TO_MS, False)
  helper.v_cruise_kph = helper.v_cruise_cluster_kph = initial
  approved = approval(initial)
  update(helper, state(140), approved, metric=metric)
  update(helper, state(140, button=button), approved, metric=metric)
  if held:
    for _ in range(CRUISE_LONG_PRESS):
      update(helper, state(140), approved, metric=metric)
    assert helper.slc_cruise_change is not None
  update(helper, state(140, button=button, pressed=False), approved, metric=metric)
  step = (1 if swap else 5) if held else (5 if swap else 1)
  target = initial + sign * step * increment
  assert helper.v_cruise_kph == pytest.approx(target)
  assert helper.v_cruise_cluster_kph == pytest.approx(target)
  if held:
    assert helper.slc_cruise_change is None
  else:
    assert helper.slc_cruise_change[:2] == pytest.approx((initial / 3.6, target / 3.6))


@pytest.mark.parametrize('button,response', [('accelCruise', 'accel'), ('decelCruise', 'decel')])
def test_saved_steps_do_not_change_confirmation_hold_or_release(helper, swap, button, response):
  pending = SlcPendingConfirmation('drive', 1, 1)
  update(helper, state(100), pending=pending)
  update(helper, state(100, button=button), pending=pending)
  assert helper.slc_consumed_button.button == response
  for _ in range(CRUISE_LONG_PRESS + 2):
    update(helper, state(100), pending=pending)
    assert helper.v_cruise_kph == 50 and helper.slc_cruise_change is None
  update(helper, state(100, button=button, pressed=False), pending=pending)
  assert helper.v_cruise_kph == 50 and helper.slc_cruise_change is None
  assert not helper.slc_suppressed_buttons


def test_raise_waits_for_release_then_uses_existing_application(helper, swap):
  approved = approval()
  update(helper, state(), approved)
  assert helper.toyota.status == 'raise_dash' and helper.v_cruise_kph == 50
  update(helper, state(60, button='accelCruise'), approved)
  for _ in range(60):
    update(helper, state(70), approved)
    assert helper.v_cruise_kph == 50 and helper.toyota.status == 'release_plus'
  update(helper, state(70, button='accelCruise', pressed=False), approved)
  assert helper.v_cruise_kph == 50 and helper.toyota.can_apply(70 / 3.6)
  helper.apply_slc_target(70 / 3.6, True)
  assert helper.v_cruise_kph == 70 and not helper.slc_suppressed_buttons


@pytest.mark.parametrize('raw_first', [False, True])
def test_independent_native_messages_do_not_qualify_a_raise(helper, raw_first):
  approved = approval()
  update(helper, state(), approved)
  update(helper, state(70 if raw_first else 60, 60 if raw_first else 70), approved)
  assert helper.v_cruise_kph == 50 and helper.toyota.status == 'raise_dash'
  update(helper, state(70), approved)
  assert helper.toyota.can_apply(70 / 3.6)


@pytest.mark.parametrize('raw,display', [(112, 70), (113, 70), (160, 100)])
def test_imperial_integer_encoding_needs_no_guessed_calibration(helper, raw, display):
  target = display * 1.609344
  update(helper, state(raw, target), approval(target), metric=False)
  assert helper.toyota.can_apply(target / 3.6)
  helper.apply_slc_target(target / 3.6, False)
  assert helper.v_cruise_kph <= raw + 1e-4 and helper.v_cruise_cluster_kph <= target + 1e-4


@pytest.mark.parametrize('native,selected', [(50, 50), (70, 50), (60, 60)])
@pytest.mark.parametrize('native_update', ['press', 'hold', 'release'])
def test_minus_counts_once_even_when_native_update_precedes_release(helper, native, selected, native_update):
  helper.v_cruise_kph = helper.v_cruise_cluster_kph = selected
  approved = approval(80)
  update(helper, state(native), approved)
  update(helper, state(native - (native_update == 'press'), button='decelCruise'), approved)
  update(helper, state(native - (native_update != 'release')), approved)
  update(helper, state(native - 1, button='decelCruise', pressed=False), approved)
  assert helper.v_cruise_kph == pytest.approx(selected - 1)
  assert helper.toyota.status == 'cancelled'


@pytest.mark.parametrize('button,delta', [('accelCruise', 1), ('decelCruise', -1)])
@pytest.mark.parametrize('arrival', ['before_press', 'press', 'hold', 'release', 'after_release'])
def test_native_and_button_arrival_order_counts_one_step(helper, button, delta, arrival):
  helper.v_cruise_kph = helper.v_cruise_cluster_kph = 70.0
  update(helper, state(70), approval())
  for name, edge, pressed in [('before_press', None, True), ('press', button, True),
                               ('hold', None, True), ('release', button, False), ('after_release', None, True)]:
    if name == arrival:
      native = 70 + delta
    elif name == 'before_press':
      native = 70
    update(helper, state(native, button=edge, pressed=pressed), approval())
    if name == 'release' and arrival == 'after_release' and delta > 0:
      assert helper.v_cruise_kph == pytest.approx(70)
  assert helper.v_cruise_kph == pytest.approx(70 + delta)
  assert helper.toyota.manual_step is None


def test_late_plus_waits_for_both_native_readings_and_reports_once(helper):
  helper.v_cruise_kph = helper.v_cruise_cluster_kph = 70.0
  update(helper, state(70), approval())
  update(helper, state(70, button='accelCruise'), approval())
  update(helper, state(70, button='accelCruise', pressed=False), approval())
  assert helper.slc_cruise_change is None
  update(helper, state(71, 70), approval())
  assert helper.v_cruise_kph == pytest.approx(70) and helper.slc_cruise_change is None
  update(helper, state(71), approval())
  assert helper.slc_cruise_change is not None
  assert helper.slc_cruise_change[:2] == pytest.approx((70 / 3.6, 71 / 3.6))
  update(helper, state(71), approval())
  assert helper.slc_cruise_change is None


@pytest.mark.parametrize('cancel', ['disengagement', 'can', 'adoption', 'new_approval'])
def test_delayed_manual_raise_cannot_replay_after_withdrawal(helper, cancel):
  helper.v_cruise_kph = helper.v_cruise_cluster_kph = 70.0
  update(helper, state(70), approval())
  update(helper, state(70, button='accelCruise'), approval())
  update(helper, state(70, button='accelCruise', pressed=False), approval())
  assert helper.toyota.manual_step is not None
  if cancel == 'adoption':
    helper.apply_slc_target(60 / 3.6, True)
  elif cancel == 'new_approval':
    update(helper, state(70), approval(60, accepted=2))
  else:
    withdrawn = state(70, active=cancel != 'disengagement')
    withdrawn.canValid = cancel != 'can'
    update(helper, withdrawn, approval(), enabled=False)
  update(helper, state(90), approval(60, accepted=2) if cancel == 'new_approval' else approval())
  assert helper.toyota.manual_step is None
  assert helper.v_cruise_kph <= 70


def test_release_during_can_fault_cannot_leave_preparation_stuck(helper):
  update(helper, state(60), approval())
  update(helper, state(60, button='accelCruise'), approval())
  release = state(70, button='accelCruise', pressed=False)
  release.canValid = False
  update(helper, release, approval())
  update(helper, state(70), approval())
  assert not helper.toyota.plus_held and helper.toyota.can_apply(70 / 3.6)


@pytest.mark.parametrize('button,raw,display', [('accelCruise', 114, 71), ('decelCruise', 111, 69)])
@pytest.mark.parametrize('early', [False, True])
def test_imperial_native_rounding_and_arrival_order_preserve_one_step(helper, button, raw, display, early):
  original = 70 * 1.609344
  helper.v_cruise_kph, helper.v_cruise_cluster_kph = 112., original
  update(helper, state(112, original), approval(original), metric=False)
  if early:
    update(helper, state(raw, display * 1.609344), approval(original), metric=False)
  update(helper, state(raw if early else 112, display * 1.609344 if early else original, button=button), approval(original), metric=False)
  update(helper, state(raw if early else 112, display * 1.609344 if early else original, button=button, pressed=False), approval(original), metric=False)
  update(helper, state(raw, display * 1.609344), approval(original), metric=False)
  assert round(helper.v_cruise_cluster_kph / 1.609344) == display
  assert helper.toyota.manual_step is None


def test_minus_at_bound_cancels_without_fabricating_speed_change(helper):
  helper.v_cruise_kph = helper.v_cruise_cluster_kph = V_CRUISE_MIN
  update(helper, state(button='decelCruise'), approval())
  update(helper, state(button='decelCruise', pressed=False), approval())
  assert helper.toyota.status == 'cancelled' and helper.slc_cruise_change is None
  update(helper, state(80), approval(70, accepted=2))
  assert helper.toyota.can_apply(70 / 3.6)


def test_minus_at_applied_native_ceiling_keeps_driver_intent(helper):
  helper.v_cruise_kph = helper.v_cruise_cluster_kph = 70.0
  update(helper, state(70), approval())
  update(helper, state(69, button='decelCruise'), approval())
  update(helper, state(69, button='decelCruise', pressed=False), approval())
  assert helper.v_cruise_kph == pytest.approx(69)
  assert helper.slc_cruise_change is not None
  assert helper.slc_cruise_change[:2] == pytest.approx((70 / 3.6, 69 / 3.6))
  update(helper, state(80), approval())
  assert helper.toyota.status == 'cancelled' and not helper.toyota.can_apply(70 / 3.6)


def test_host_enabled_native_resume_does_not_add_software_step(helper, swap):
  update(helper, state(80, active=False, button='accelCruise'), approval(50), enabled=True)
  update(helper, state(80), approval(50), enabled=True)
  update(helper, state(80, button='accelCruise', pressed=False), approval(50), enabled=True)
  assert helper.v_cruise_kph == 50 and helper.slc_cruise_change is None


def test_source_gap_does_not_erase_minus_cancellation_at_bound(helper):
  helper.v_cruise_kph = helper.v_cruise_cluster_kph = V_CRUISE_MIN
  update(helper, state(), approval())
  update(helper, state())
  update(helper, state(button='decelCruise'))
  update(helper, state(button='decelCruise', pressed=False))
  update(helper, state(80), approval())
  assert helper.toyota.status == 'cancelled' and helper.slc_cruise_change is None


def test_main_off_ends_retained_ownership_even_without_native_set(helper):
  update(helper, state(80), approval(50))
  off = state(0, active=False)
  off.cruiseState.available = False
  update(helper, off, slc=False, enabled=False)
  assert not helper.toyota.owns_target
  update(helper, state(80), slc=False)
  assert helper.v_cruise_kph == pytest.approx(80)


@pytest.mark.parametrize('off_first', [False, True])
def test_off_retains_only_current_native_engagement_and_discloses_resume(helper, off_first):
  update(helper, state(70), approval(50))
  if off_first:
    update(helper, state(70), slc=False)
    assert helper.v_cruise_kph == 50 and helper.toyota.status == 'off_hold'
  update(helper, state(70, active=False), approval(50), enabled=False, slc=not off_first)
  update(helper, state(70, active=False), enabled=False, slc=False)
  assert helper.toyota.status == 'off_resume' and helper.toyota.target_kph == pytest.approx(70)
  update(helper, state(70), slc=False)
  assert helper.v_cruise_kph == pytest.approx(70) and helper.toyota.status == ''


def test_resume_on_seeds_lower_target_before_approval_can_execute(helper):
  update(helper, state(80), approval(50))
  update(helper, state(80, active=False), approval(50), enabled=False)
  update(helper, state(80, button='accelCruise'), approval(50))
  assert helper.v_cruise_kph == 50


def test_standstill_resume_keeps_native_meaning(helper, swap):
  update(helper, state(stopped=True, button='accelCruise'), pending=SlcPendingConfirmation('drive', 1, 1))
  assert helper.slc_consumed_button is None
  for _ in range(CRUISE_LONG_PRESS + 2):
    update(helper, state(stopped=True))
  update(helper, state(button='accelCruise', pressed=False))
  assert helper.v_cruise_kph == 50 and helper.slc_cruise_change is None


def test_missing_can_does_not_release_retained_set_to_native(helper):
  update(helper, state(80), approval(50))
  stale = state(80)
  stale.canValid = False
  update(helper, stale, slc=False)
  assert helper.v_cruise_kph == 50 and helper.slc_pcm and not helper.toyota.can_apply(80 / 3.6)


@pytest.mark.parametrize('field,value', [
  ('brand', 'honda'), ('pcmCruise', False), ('openpilotLongitudinalControl', False),
  ('notCar', True), ('passive', True), ('dashcamOnly', True),
])
def test_ineligible_configurations_keep_existing_handling(helper, field, value):
  setattr(helper.CP, field, value)
  assert not eligible(helper.CP)
  assert VCruiseHelper(helper.CP).toyota is None


def test_pedal_owners_keep_existing_handling(helper):
  helper.CP.flags |= int(ToyotaFlags.GAS_INTERCEPTOR)
  assert not eligible(helper.CP)
  assert VCruiseHelper(helper.CP).toyota is None


@pytest.mark.parametrize('manual', [False, True])
def test_runtime_waits_for_bound_fresh_card_projection(helper, manual):
  fixture = replay.RuntimeReplayTests()
  fixture.setUp()
  sm = fixture.sm
  sm['carState'].vCruise = sm['carState'].vCruiseCluster = 50.0
  sm.data['starpilotCarState'] = messaging.new_message('starpilotCarState').starpilotCarState
  runtime = Runtime(parse({'SpeedLimitController': True, 'SLCConfirmation': manual,
                           'SLCConfirmationHigher': True, 'SLCPriority1': 'Dashboard'}), session_id='drive')

  def tick(stamp, **kwargs):
    sm.advance(stamp)
    sm.valid['starpilotCarState'] = sm.alive['starpilotCarState'] = True
    companion = sm['starpilotCarState']
    companion.sourceCarStateMonoTime = stamp
    helper.toyota.publish(companion.toyotaCruise)
    return runtime.step(sm, helper.CP, now_ns=stamp, **kwargs)

  pending = tick(2_000_000_000).message.slcState
  accepted_ns = 2_000_000_000 + (10_000_000 if manual else 0)
  request = Action('drive', 1, pending.decisionId, pending.presentationId, 'accept') if manual else None
  accepted = tick(accepted_ns, request=request)
  assert accepted.message.slcState.hasAccepted and accepted.command is None
  update(helper, state(60), accepted.message.slcState)
  assert tick(accepted_ns + 10_000_000).command is None
  update(helper, state(100), accepted.message.slcState)
  ready = tick(accepted_ns + 20_000_000)
  assert ready.command is not None and ready.command.slcCruiseCommand.targetMps == pytest.approx(25.0)
  sm.valid['starpilotCarState'] = False
  assert projection(sm, accepted_ns + 20_000_000) is None
  sm.valid['starpilotCarState'] = True
  sm['starpilotCarState'].toyotaCruise.acceptedMonoTime += 1
  assert runtime.step(sm, helper.CP, now_ns=accepted_ns + 20_000_000).command is None


def test_same_limit_adoption_recovers_cancelled_toyota_through_real_runtime(helper):
  from openpilot.starpilot.ui.onroad_state import OnroadState, slc_controls, speed_limit_from_message
  from openpilot.starpilot.ui.presentation import Profile

  fixture = replay.RuntimeReplayTests()
  fixture.setUp()
  sm = fixture.sm
  sm.data['starpilotCarState'] = messaging.new_message('starpilotCarState').starpilotCarState
  runtime = Runtime(parse({'SpeedLimitController': True, 'SLCPriority1': 'Dashboard'}), session_id='drive')

  def tick(stamp, **kwargs):
    sm['carState'].vCruise = helper.v_cruise_kph
    sm['carState'].vCruiseCluster = helper.v_cruise_cluster_kph
    sm.advance(stamp)
    sm.valid['starpilotCarState'] = sm.alive['starpilotCarState'] = True
    sm['starpilotCarState'].sourceCarStateMonoTime = stamp
    helper.toyota.publish(sm['starpilotCarState'].toyotaCruise)
    return runtime.step(sm, helper.CP, now_ns=stamp, **kwargs)

  tick(2_000_000_000)
  accepted = tick(5_000_000_000).message.slcState
  update(helper, state(60), accepted)
  assert helper.toyota.status == 'raise_dash'
  update(helper, state(60, button='decelCruise'), accepted)
  update(helper, state(59, button='decelCruise', pressed=False), accepted)
  event = CruiseEvent(1, 5_010_000_000, 50 / 3.6, 49 / 3.6, 'decel', 'card-producer', 5_010_000_000)
  changed = tick(5_010_000_000, cruise_event=event).message.slcState
  assert changed.driverOverrideActive
  update(helper, state(100), changed)
  assert helper.toyota.status == 'cancelled' and not helper.toyota.can_apply(25.)
  screen = OnroadState(True, False, 20., helper.v_cruise_cluster_kph, speed_limit_from_message(changed),
                       metric=True, longitudinal_active=True, slc_system_long_available=True, toyota_cruise_status=helper.toyota.status)
  assert all(slc_controls(profile, screen) == () for profile in Profile)
  adopted = tick(5_020_000_000, request=Action('drive', 1, 0, changed.presentationId, 'adopt')).message.slcState
  assert adopted.actionStatus == 'adopt' and not adopted.driverOverrideActive
  assert adopted.acceptedMonoTime == accepted.acceptedMonoTime
  update(helper, state(100), adopted)
  command = tick(5_030_000_000).command.slcCruiseCommand
  assert command.targetMps == pytest.approx(25.) and helper.toyota.can_apply(command.targetMps)
  helper.apply_slc_target(command.targetMps, True)
  assert helper.v_cruise_kph == pytest.approx(90)
  applied_ns = 5_035_000_000
  applied = tick(applied_ns, cruise_event=CruiseEvent(2, applied_ns, 49 / 3.6, 90 / 3.6, '', 'card-producer',
    applied_ns, 'commandApplied', 'drive', command.decisionId, command.presentationId, command.commandId))
  assert applied.message.slcState.commandStatus == 'applied'

  # The persisted receipt must not undo another minus; only a new adoption may.
  update(helper, state(100, button='decelCruise'), adopted)
  update(helper, state(99, button='decelCruise', pressed=False), adopted)
  update(helper, state(100), adopted)
  assert helper.toyota.status == 'cancelled'
  event = CruiseEvent(3, 5_040_000_000, 90 / 3.6, 89 / 3.6, 'decel', 'card-producer', 5_040_000_000)
  changed = tick(5_040_000_000, cruise_event=event).message.slcState
  readopted = tick(5_050_000_000, request=Action('drive', 2, 0, changed.presentationId, 'adopt')).message.slcState
  update(helper, state(80), readopted)
  assert helper.toyota.status == 'raise_dash' and not helper.toyota.can_apply(25.)
  update(helper, state(100), readopted)
  assert helper.toyota.can_apply(25.)
