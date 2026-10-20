from types import SimpleNamespace

from cereal import car, log
import pytest

from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.controls.lib.longcontrol import LongControl, LongCtrlState
from openpilot.selfdrive.controls.lib.standstill_hold import (
  HOLD_TIMEOUT_S, MODE_HOLD_ONLY, MODE_OFF, MODE_RESUME, REASON_DOOR, REASON_GEAR, REASON_NONE, REASON_SEATBELT,
  REASON_TIMEOUT, StandstillHold, brake_request_reason, low_speed_set_applies, low_speed_set_kph, read_mode,
  resume_set_speed_kph,
)

GearShifter = car.CarState.GearShifter
State = log.SelfdriveState.OpenpilotState
STOP_ACCEL = -2.0  # Mat's 9G carParams stopAccel


def cs(standstill=True, brake=False, gas=False, door=False, belt=False, gear=GearShifter.drive, v=0.0):
  return SimpleNamespace(standstill=standstill, brakePressed=brake, gasPressed=gas, doorOpen=door,
                         seatbeltUnlatched=belt, gearShifter=gear, vEgo=v, aEgo=0.0,
                         cruiseState=SimpleNamespace(standstill=False))


class FakeParams:
  def __init__(self, value=None, exc=None):
    self.value, self.exc = value, exc

  def get_int(self, key):
    if self.exc is not None:
      raise self.exc
    return self.value


@pytest.mark.parametrize("value, expected", [(0, MODE_OFF), (1, MODE_RESUME), (2, MODE_HOLD_ONLY), (3, MODE_OFF), (-1, MODE_OFF)])
def test_read_mode(value, expected):
  assert read_mode(FakeParams(value)) == expected


def test_read_mode_unknown_key_is_off():
  # a device whose params_pyx.so wasn't rebuilt raises UnknownKeyName: the feature must stay off
  from openpilot.common.params import UnknownKeyName
  assert read_mode(FakeParams(exc=UnknownKeyName("StandstillEngageMode"))) == MODE_OFF


def test_arms_only_from_pre_enabled_at_standstill_on_brake():
  h = StandstillHold()
  assert not h.update(MODE_RESUME, State.preEnabled, True, cs(brake=False), 0.)  # no brake
  assert not h.update(MODE_RESUME, State.preEnabled, True, cs(brake=True, standstill=False), 0.)  # rolling
  assert not h.update(MODE_RESUME, State.enabled, True, cs(brake=True), 0.)  # already engaged at a light: stock
  assert not h.update(MODE_OFF, State.preEnabled, True, cs(brake=True), 0.)  # feature off
  assert not h.update(MODE_RESUME, State.preEnabled, False, cs(brake=True), 0.)  # not engaged
  assert h.update(MODE_RESUME, State.preEnabled, True, cs(brake=True), 0.)


@pytest.mark.parametrize("mode", [MODE_RESUME, MODE_HOLD_ONLY])
def test_hold_never_self_releases(mode):
  h = StandstillHold()
  assert h.update(mode, State.preEnabled, True, cs(brake=True), 0.)
  # brake released, engaged, then everything that should only prompt for the brake
  for t, c in enumerate([cs(), cs(door=True), cs(belt=True), cs(gear=GearShifter.park), cs(gear=GearShifter.neutral),
                         cs(gear=GearShifter.reverse), cs(standstill=False, v=0.3)]):
    assert h.update(mode, State.enabled, True, c, 1. + t)
  # the mode param changing mid-hold doesn't release it either
  assert h.update(MODE_OFF, State.enabled, True, cs(), 10.)
  assert h.mode == mode
  assert h.update(mode, State.enabled, True, cs(), 10. + HOLD_TIMEOUT_S * 2)


def test_gas_ends_hold():
  h = StandstillHold()
  h.update(MODE_RESUME, State.preEnabled, True, cs(brake=True), 0.)
  h.update(MODE_RESUME, State.enabled, True, cs(), 1.)
  assert not h.update(MODE_RESUME, State.enabled, True, cs(gas=True), 2.)
  assert h.ended_by_gas
  assert not h.update(MODE_RESUME, State.overriding, True, cs(gas=True), 2.01)
  assert not h.ended_by_gas  # only on the frame it ended
  # gas released while stopped again: no re-arm without a new SET + brake
  assert not h.update(MODE_RESUME, State.enabled, True, cs(), 3.)


def test_disengage_ends_hold():
  h = StandstillHold()
  h.update(MODE_HOLD_ONLY, State.preEnabled, True, cs(brake=True), 0.)
  assert not h.update(MODE_HOLD_ONLY, State.disabled, False, cs(brake=True), 1.)
  assert not h.ended_by_gas


def test_held_seconds():
  h = StandstillHold()
  assert h.held_s(5.) == 0.
  h.update(MODE_RESUME, State.preEnabled, True, cs(brake=True), 5.)
  assert h.held_s(65.) == pytest.approx(60.)


@pytest.mark.parametrize("c, held, reason", [
  (cs(), 0., REASON_NONE),
  (cs(gear=GearShifter.sport), 0., REASON_NONE),
  (cs(door=True), 0., REASON_DOOR),
  (cs(belt=True), 0., REASON_SEATBELT),
  (cs(gear=GearShifter.park), 0., REASON_GEAR),
  (cs(gear=GearShifter.reverse), 0., REASON_GEAR),
  (cs(gear=GearShifter.neutral), 0., REASON_GEAR),
  (cs(), HOLD_TIMEOUT_S - 0.1, REASON_NONE),
  (cs(), HOLD_TIMEOUT_S, REASON_TIMEOUT),
  (cs(door=True), HOLD_TIMEOUT_S, REASON_DOOR),
])
def test_brake_request_reason(c, held, reason):
  assert brake_request_reason(c, held) == reason


def test_resume_set_speed():
  floor = 11.3
  assert resume_set_speed_kph(0., floor, False, 145., 1.6) == pytest.approx(40.0)  # 25 mph on the imperial grid
  assert resume_set_speed_kph(0., floor, True, 145., 1.6) == pytest.approx(40.0)
  assert resume_set_speed_kph(72.0, floor, False, 145., 1.6) == pytest.approx(72.0)  # last set speed (45 mph)
  assert resume_set_speed_kph(floor, floor, False, 145., 1.6) == pytest.approx(40.0)  # the 7 mph floor isn't a set speed
  assert resume_set_speed_kph(200., floor, False, 145., 1.6) == pytest.approx(145.)


def make_cp():
  CP = car.CarParams.new_message()
  CP.longitudinalTuning.kpBP = [0.0]
  CP.longitudinalTuning.kpV = [0.5]
  CP.longitudinalTuning.kiBP = [0.0]
  CP.longitudinalTuning.kiV = [0.1]
  CP.startingState = False
  CP.enableGasInterceptorDEPRECATED = True
  CP.carFingerprint = "HONDA_ACCORD_9G"
  CP.brand = "honda"
  return CP


def toggles():
  return SimpleNamespace(custom_accel_profile=False, startAccel=1.0, stopAccel=STOP_ACCEL, stoppingDecelRate=0.3,
                         vEgoStarting=0.5, vEgoStopping=0.5)


def run_engage(hold: bool, frames=200):
  """Standstill engage at a red light with no lead: the planner wants to go (aTarget +0.2, shouldStop False)."""
  LoC = LongControl(make_cp())
  c = SimpleNamespace(vEgo=0.0, aEgo=0.0, brakePressed=False, gasPressed=False, standstill=True,
                      cruiseState=SimpleNamespace(standstill=False))
  out = []
  for _ in range(frames):
    out.append(LoC.update(True, c, 0.2, False, (-3.5, 2.0), toggles(), standstill_hold=hold))
  return LoC, out


def test_longcontrol_hold_brakes_fully_from_first_frame():
  LoC, out = run_engage(hold=True)
  assert LoC.long_control_state == LongCtrlState.stopping
  assert all(a == pytest.approx(STOP_ACCEL) for a in out)


def test_longcontrol_without_hold_creeps():
  # the logged failure: after a standstill engage the stock path doesn't brake (the car creeps off)
  LoC, out = run_engage(hold=False)
  assert max(out) > -0.1


def test_longcontrol_hold_ignores_inactive():
  LoC = LongControl(make_cp())
  c = SimpleNamespace(vEgo=0.0, aEgo=0.0, brakePressed=False, gasPressed=False, standstill=True,
                      cruiseState=SimpleNamespace(standstill=False))
  assert LoC.update(False, c, 0.2, False, (-3.5, 2.0), toggles(), standstill_hold=True) == 0.
  assert LoC.long_control_state == LongCtrlState.off


def test_longcontrol_resumes_after_gas_ends_hold():
  # Resume mode: the gas press overrides (longActive False -> reset), then normal control picks up from stopped
  LoC, _ = run_engage(hold=True, frames=50)
  c = SimpleNamespace(vEgo=0.0, aEgo=0.0, brakePressed=False, gasPressed=True, standstill=True,
                      cruiseState=SimpleNamespace(standstill=False))
  LoC.reset()
  LoC.update(False, c, 0.5, False, (-3.5, 2.0), toggles())  # overriding frame
  c.gasPressed, c.vEgo, c.standstill = False, 1.0, False
  outs = [LoC.update(True, c, 0.5, False, (-3.5, 2.0), toggles()) for _ in range(int(1. / DT_CTRL))]
  assert LoC.long_control_state == LongCtrlState.pid
  assert outs[-1] > 0.


# --- low-speed SET: speed limit + SLC offset instead of the 7 mph floor ---

MPH = 0.44704
FLOOR_KPH = 7.0 * 1.609344
INC = 1.6  # IMPERIAL_INCREMENT


def lss(limit_mph=0., offset_mph=0., last_kph=0., metric=False):
  return low_speed_set_kph(limit_mph * MPH, offset_mph * MPH, last_kph, FLOOR_KPH, metric, 8., 145., INC)


@pytest.mark.parametrize("mode, v_mph, standstill, brake, expected", [
  (MODE_RESUME, 0., True, True, True),       # standstill engage that will hold
  (MODE_HOLD_ONLY, 0., True, True, True),
  (MODE_OFF, 0., True, True, False),         # nothing holds the car: keep the 7 mph floor
  (MODE_RESUME, 0., True, False, False),     # no brake -> no hold
  (MODE_OFF, 5., False, False, True),        # rolling 5 mph crawl fix applies in every mode
  (MODE_RESUME, 8.9, False, True, True),
  (MODE_RESUME, 9.0, False, False, False),   # 9 mph and up: stock engage (SetSpeedLimit / current speed)
  (MODE_OFF, 40., False, False, False),
])
def test_low_speed_set_applies(mode, v_mph, standstill, brake, expected):
  assert low_speed_set_applies(mode, v_mph * MPH, standstill, brake) is expected


def test_low_speed_set_limit_plus_offset_on_imperial_grid():
  assert lss(30., 5.) == pytest.approx(35 * INC)   # 30 mph limit + 5 mph offset -> 35 mph (56.0 on the 1.6 grid)
  assert lss(25., 0.) == pytest.approx(25 * INC)
  assert lss(29.6, 0.) == pytest.approx(30 * INC)  # vision/map limits in m/s snap to whole mph
  assert lss(45., -3.) == pytest.approx(42 * INC)  # negative offsets work too


def test_low_speed_set_limit_wins_over_last_set():
  assert lss(30., 5., last_kph=65 * INC) == pytest.approx(35 * INC)


def test_low_speed_set_fallbacks():
  assert lss(0., 5., last_kph=45 * INC) == pytest.approx(45 * INC)  # no known limit -> last set speed this drive
  assert lss(0., 0., last_kph=0.) == pytest.approx(25 * INC)        # no limit, no set speed -> 25 mph
  assert lss(0., 0., last_kph=FLOOR_KPH) == pytest.approx(25 * INC)  # the old 7 mph floor isn't a real set speed
  assert lss(0.5, 0., last_kph=0.) == pytest.approx(25 * INC)       # sub-1 m/s limit = unknown


def test_low_speed_set_metric_and_clamp():
  assert low_speed_set_kph(50 / 3.6, 5 / 3.6, 0., FLOOR_KPH, True, 8., 145., INC) == pytest.approx(55.)
  assert lss(100., 10.) == pytest.approx(145.)  # V_CRUISE_MAX


def test_low_speed_set_grid_reads_back_as_exact_mph():
  # the 9G dash label (honda-cruise-label-mph) and the UI read vCruise through imperial_grid_to_exact_kph
  from openpilot.selfdrive.car.cruise import imperial_grid_to_exact_kph
  assert imperial_grid_to_exact_kph(lss(30., 5.), False) / 1.609344 == pytest.approx(35.0)
