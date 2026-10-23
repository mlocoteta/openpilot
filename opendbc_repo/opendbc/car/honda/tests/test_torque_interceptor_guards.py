"""Honda 9G Accord Torque Interceptor (TI), F04: lockout auto cold-reset and lockout-prevention guards.

Ported from the 6.x TI branch (test_honda_ti.py reset/guard classes, commits 764229e27 163e921f3
6e732153b aa7e4b70a 3faf2d17f). Sources: reports/2026-09-29-ti-lockout-prevention.md and
reports/2026-09-30-drives-312-313.md (G2 headroom guard with 0.2 s peak-hold).
"""
from collections import deque

import numpy as np
import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus, structs
from opendbc.car.honda import torque_interceptor
from opendbc.car.honda.tests.test_torque_interceptor import params, run_frame, ti_feedback
from opendbc.car.honda.torque_interceptor import (TI_FEEDBACK_LOCKOUT_FRAMES, TI_FEEDBACK_TIMEOUT_FRAMES, TI_LIMITS,
                                                 TI_LOCK_ZERO_ANGLE, TI_LOCK_ZERO_SPEED, TI_OPTION, TI_RESET_BURST_FRAMES,
                                                 TI_RESET_COOLDOWN_FRAMES, TI_RESET_HANDS_OFF_FRAMES, TI_RESET_HANDS_OFF_TORQUE,
                                                 TI_RESET_MAX_ATTEMPTS, TI_STATE, TI_STUCK_FRAMES, TiCarState, TorqueInterceptor,
                                                 apply_ti_steer_torque_limits, create_ti_steering_control,
                                                 ti_driver_limiter_binds, ti_driver_torque_limits, ti_output_headroom_limits)
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR, DBC

TI_STEERING_CONTROL = 0x249


def reset_step(ti, fb):
  """One carState frame of the TI path; returns the OPTION chosen for this frame."""
  ti.update_driver_torque(fb, 0, 30)
  ti.update_gate(fb)
  return ti.update_reset(fb)


def locked_gate():
  """A gate that reached RUN and then locked out (OFF, VIOL 23), as in the weekend rlogs."""
  ti = TiCarState()
  for _ in range(10):
    assert reset_step(ti, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL
  reset_step(ti, ti_feedback(TI_STATE.OFF, viol=23, torque=60))
  assert ti.locked_out
  return ti


LOCKED = ti_feedback(TI_STATE.OFF, viol=23)


class TestAutoReset:
  def test_no_reset_or_alert_during_startup(self):
    # startup replay (2026-09-11 rlog): long OFF + VIOL 23 before the first RUN, hands off
    ti = TiCarState()
    for _ in range(1571):
      assert reset_step(ti, ti_feedback(TI_STATE.OFF, viol=23)) == TI_OPTION.NORMAL
      assert not ti.locked_out
    for _ in range(200):
      assert reset_step(ti, ti_feedback(TI_STATE.OFF)) == TI_OPTION.NORMAL
      assert not ti.locked_out
    assert reset_step(ti, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL
    assert ti.run_seen and not ti.locked_out

  def test_lockout_raises_alert(self):
    ti = locked_gate()
    assert ti.locked_out and not ti.lkas_allowed

  def test_driver_override_is_not_a_lockout(self):
    ti = TiCarState()
    reset_step(ti, ti_feedback(TI_STATE.RUN))
    for _ in range(200):
      assert reset_step(ti, ti_feedback(TI_STATE.DRIVER_OVER, torque=90)) == TI_OPTION.NORMAL
      assert not ti.locked_out
    reset_step(ti, ti_feedback(TI_STATE.DRIVER_OVER, viol=17, torque=90))
    assert ti.locked_out

  def test_feedback_loss_after_run_alerts_but_never_resets(self):
    ti = TiCarState()
    reset_step(ti, ti_feedback(TI_STATE.RUN))
    for _ in range(TI_FEEDBACK_LOCKOUT_FRAMES - 1):
      reset_step(ti, None)
      assert not ti.locked_out  # tolerated gap
    for _ in range(1000):
      assert reset_step(ti, None) == TI_OPTION.NORMAL
      assert ti.locked_out

  def test_reset_only_after_hands_off_debounce(self):
    ti = locked_gate()
    for _ in range(1000):  # driver still holding the wheel hard
      assert reset_step(ti, ti_feedback(TI_STATE.OFF, viol=23, torque=60)) == TI_OPTION.NORMAL
    # a short release interrupted by another grab restarts the debounce
    for _ in range(TI_RESET_HANDS_OFF_FRAMES - 5):
      assert reset_step(ti, LOCKED) == TI_OPTION.NORMAL
    assert reset_step(ti, ti_feedback(TI_STATE.OFF, viol=23, torque=-TI_RESET_HANDS_OFF_TORQUE - 1)) == TI_OPTION.NORMAL
    for _ in range(TI_RESET_HANDS_OFF_FRAMES - 1):
      assert reset_step(ti, LOCKED) == TI_OPTION.NORMAL
    assert reset_step(ti, LOCKED) == TI_OPTION.COLD_RESET
    assert ti.reset_attempts == 1

  def test_light_touch_counts_as_hands_off(self):
    ti = locked_gate()
    opts = [reset_step(ti, ti_feedback(TI_STATE.OFF, viol=23, torque=TI_RESET_HANDS_OFF_TORQUE))
            for _ in range(TI_RESET_HANDS_OFF_FRAMES)]
    assert opts[-1] == TI_OPTION.COLD_RESET and TI_OPTION.COLD_RESET not in opts[:-1]

  def test_burst_length(self):
    ti = locked_gate()
    opts = [reset_step(ti, LOCKED) for _ in range(TI_RESET_HANDS_OFF_FRAMES + 50)]
    first = opts.index(TI_OPTION.COLD_RESET)
    assert first == TI_RESET_HANDS_OFF_FRAMES - 1
    assert opts[first:first + TI_RESET_BURST_FRAMES] == [TI_OPTION.COLD_RESET] * TI_RESET_BURST_FRAMES
    assert TI_OPTION.COLD_RESET not in opts[first + TI_RESET_BURST_FRAMES:]

  def test_no_reset_while_board_restarting(self):
    # VIOL cleared (the ~2 s OFF + VIOL 0 restart delay, or DISCOVER after a reset): alert stays, no reset
    ti = locked_gate()
    for state in (TI_STATE.OFF, TI_STATE.DISCOVER):
      for _ in range(1000):
        assert reset_step(ti, ti_feedback(state)) == TI_OPTION.NORMAL
        assert ti.locked_out
    assert ti.reset_attempts == 0

  def test_cooldown_and_retry_cap(self):
    ti = locked_gate()
    opts = [reset_step(ti, LOCKED) for _ in range(5000)]
    starts = [i for i, o in enumerate(opts) if o == TI_OPTION.COLD_RESET and (i == 0 or opts[i - 1] != o)]
    assert len(starts) == TI_RESET_MAX_ATTEMPTS
    assert all(b - a == TI_RESET_BURST_FRAMES + TI_RESET_COOLDOWN_FRAMES for a, b in zip(starts, starts[1:], strict=False))
    assert opts.count(TI_OPTION.COLD_RESET) == TI_RESET_MAX_ATTEMPTS * TI_RESET_BURST_FRAMES
    assert ti.locked_out  # capped: alert remains until the board recovers by itself

  def test_recovery_clears_alert_and_counters(self):
    ti = locked_gate()
    for _ in range(5000):
      reset_step(ti, LOCKED)
    assert ti.reset_attempts == TI_RESET_MAX_ATTEMPTS
    assert reset_step(ti, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL
    assert not ti.locked_out and ti.lkas_allowed
    assert (ti.reset_attempts, ti.reset_cooldown, ti.reset_burst_left, ti.hands_off_frames) == (0, 0, 0, 0)
    # a later lockout gets a fresh set of attempts
    opts = [reset_step(ti, LOCKED) for _ in range(TI_RESET_HANDS_OFF_FRAMES)]
    assert opts[-1] == TI_OPTION.COLD_RESET

  def test_run_mid_burst_stops_burst(self):
    ti = locked_gate()
    for _ in range(TI_RESET_HANDS_OFF_FRAMES + 2):
      reset_step(ti, LOCKED)
    assert ti.reset_burst_left > 0
    assert reset_step(ti, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL
    assert reset_step(ti, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL


class TestOptionPacking:
  @staticmethod
  def pack(steer, option=TI_OPTION.NORMAL):
    packer = CANPacker(DBC[CAR.HONDA_ACCORD_9G][Bus.pt])
    addr, dat, bus = create_ti_steering_control(packer, steer, option)
    assert (addr, bus) == (TI_STEERING_CONTROL, 0)
    return dat

  def test_normal_frame_unchanged(self):
    # same bytes as the old hard-coded KEY = 3294744160 (0xC461CE60)
    assert torque_interceptor.TI_KEY == 3294744160
    assert self.pack(0)[4:] == bytes([0xC4, 0x61, 0xCE, 0x60])
    assert self.pack(-123)[4:] == bytes([0xC4, 0x61, 0xCE, 0x60])

  def test_cold_reset_option_byte(self):
    dat = self.pack(0, TI_OPTION.COLD_RESET)
    assert dat[4:] == bytes([0xC4, 0x61, 0xCE, 0x61])
    assert dat[:4] == self.pack(0)[:4]  # torque bytes (the only ones panda checks) are unchanged

  @pytest.mark.parametrize("steer", (1, -1, 150, -599))
  def test_never_reset_with_torque(self, steer):
    assert self.pack(steer, TI_OPTION.COLD_RESET)[7] == TI_OPTION.NORMAL


@pytest.fixture
def ti_car():
  cp = params()
  ci = CarInterface(cp)
  ci.update([])
  return ci, CANPacker(DBC[cp.carFingerprint][Bus.pt])


class TestAutoResetEndToEnd:
  def test_lockout_alert_and_reset_on_the_wire(self, ti_car):
    ci, packer = ti_car

    def frame_(frame, fb):
      request, dat, _, _ = run_frame(ci, packer, frame, fb)
      return ci.CS.out, request, dat[7]

    frame = 0
    for _ in range(200):  # startup, then RUN with torque
      CS, request, option = frame_(frame, ti_feedback(TI_STATE.OFF, viol=23))
      assert not CS.steerFaultTemporary and request == 0 and option == TI_OPTION.NORMAL
      frame += 1
    for _ in range(50):
      CS, request, option = frame_(frame, ti_feedback(TI_STATE.RUN))
      assert not CS.steerFaultTemporary and option == TI_OPTION.NORMAL
      frame += 1
    assert request != 0
    # driver yanks the wheel -> lockout, then lets go
    options = []
    for i in range(1000):
      torque = 80 if i < 100 else 0
      CS, request, option = frame_(frame, ti_feedback(TI_STATE.OFF, viol=23, torque=torque))
      assert CS.steerFaultTemporary and request == 0
      options.append(option)
      frame += 1
    assert TI_OPTION.COLD_RESET not in options[:100 + TI_RESET_HANDS_OFF_FRAMES - 1]
    assert options.count(TI_OPTION.COLD_RESET) == TI_RESET_MAX_ATTEMPTS * TI_RESET_BURST_FRAMES
    assert set(options) == {TI_OPTION.NORMAL, TI_OPTION.COLD_RESET}
    # board recovers
    for _ in range(20):
      CS, request, option = frame_(frame, ti_feedback(TI_STATE.RUN))
      assert not CS.steerFaultTemporary and option == TI_OPTION.NORMAL
      frame += 1
    assert request != 0


def ti_limit(target, last, s, guard=True, zero=False, hold=None):
  return apply_ti_steer_torque_limits(target, last, s, TI_LIMITS, output_guard=guard, force_zero=zero, guard_driver_torque=hold)


def ti_output(s, cmd):
  return s + cmd / TI_LIMITS.TI_OUTPUT_TORQUE_DIV


class TestOutputHeadroomGuard:
  """G2: s + cmd/12 stays inside +50/-45 for every s, using a 0.2 s peak-hold of s; 60/frame toward zero only while the guard cuts."""
  FAST = TI_LIMITS.TI_STEER_DELTA_DOWN_FAST
  POS, NEG, DIV = TI_LIMITS.TI_OUTPUT_GUARD_POS, TI_LIMITS.TI_OUTPUT_GUARD_NEG, TI_LIMITS.TI_OUTPUT_TORQUE_DIV

  @pytest.mark.parametrize("s", (1, 10, 30, 39, 40, 49, 50, 60))
  def test_caps_same_direction_positive(self, s):
    last, out = TI_LIMITS.TI_STEER_MAX, []
    for _ in range(20):
      last = ti_limit(TI_LIMITS.TI_STEER_MAX, last, s)
      out.append(last)
    assert out[-1] == min(max((self.POS - s) * self.DIV, 0), TI_LIMITS.TI_STEER_MAX)
    assert ti_output(s, out[-1]) <= max(self.POS, s)

  @pytest.mark.parametrize("s", (-1, -10, -20, -35, -45, -60))
  def test_caps_same_direction_negative(self, s):
    last = -TI_LIMITS.TI_STEER_MAX
    for _ in range(20):
      last = ti_limit(-TI_LIMITS.TI_STEER_MAX, last, s)
    assert last == max(min((-self.NEG - s) * self.DIV, 0), -TI_LIMITS.TI_STEER_MAX)

  def test_continuous_at_zero(self):
    for s in (-3, -1, 0, 1, 3):
      lo, hi = ti_output_headroom_limits(s, s, TI_LIMITS)
      assert hi == min((self.POS - s) * self.DIV, TI_LIMITS.TI_STEER_MAX)
      assert lo == (-self.NEG - s) * self.DIV
    for s in range(-80, 80):
      lo0, hi0 = ti_output_headroom_limits(s, s, TI_LIMITS)
      lo1, hi1 = ti_output_headroom_limits(s + 1, s + 1, TI_LIMITS)
      assert 0 <= hi0 - hi1 <= self.DIV and 0 <= lo0 - lo1 <= self.DIV
      assert -TI_LIMITS.TI_STEER_MAX <= lo0 <= 0 <= hi0 <= TI_LIMITS.TI_STEER_MAX

  def test_peak_hold_uses_each_side(self):
    assert ti_output_headroom_limits(-20, 30, TI_LIMITS) == ((-self.NEG + 20) * self.DIV, (self.POS - 30) * self.DIV)
    last, held = -540, []
    for s in (-3, 3, -1, 2, 0, -3):
      last = ti_limit(-TI_LIMITS.TI_STEER_MAX, last, s, hold=(-3, 3))
      held.append(last)
    assert held == [(-self.NEG + 3) * self.DIV] * len(held)

  def test_hands_off_noise_does_not_chatter(self):
    hold, last, cmds = deque(maxlen=TI_LIMITS.TI_OUTPUT_GUARD_HOLD_FRAMES), 557, []
    for n in range(200):
      s = (-3, 1, 3, -2, 0, 2)[n % 6]
      hold.append(s)
      last = ti_limit(TI_LIMITS.TI_STEER_MAX, last, s, hold=(min(hold), max(hold)))
      cmds.append(last)
    steps = np.diff(cmds)
    assert not any(steps[i] < 0 and np.any(steps[i + 1:i + 6] > 0) for i in range(len(steps)))
    assert cmds[-1] == (self.POS - 3) * self.DIV

  def test_fast_step_toward_zero_only_when_guard_cuts(self):
    # trip #34 (route 310): s = 27, cmd 434 -> 49.6 counts, pushing 434 -> 276 at 60/frame
    seq, last = [], 434
    while True:
      nxt = ti_limit(434, last, 27)
      if nxt == last:
        break
      seq.append(last - nxt)
      last = nxt
    assert last == (self.POS - 27) * self.DIV and seq[:-1] == [self.FAST] * (len(seq) - 1) and seq[-1] <= self.FAST
    assert ti_limit(0, 300, 0) == 300 - TI_LIMITS.TI_STEER_DELTA_DOWN
    assert ti_limit(0, -300, 0) == -300 + TI_LIMITS.TI_STEER_DELTA_DOWN
    # the driver limiter cutting (opposing hand) keeps the normal down-rate: no fast step there
    assert ti_limit(599, 599, -20) == 599 - TI_LIMITS.TI_STEER_DELTA_DOWN
    assert ti_limit(-599, -599, 20) == -599 + TI_LIMITS.TI_STEER_DELTA_DOWN

  def test_up_rate_unchanged(self):
    assert ti_limit(TI_LIMITS.TI_STEER_MAX, 0, 10) == TI_LIMITS.TI_STEER_DELTA_UP
    assert ti_limit(-TI_LIMITS.TI_STEER_MAX, 0, -10) == -TI_LIMITS.TI_STEER_DELTA_UP

  @pytest.mark.parametrize("s", range(-80, 81, 8))
  @pytest.mark.parametrize("target", (-599, -300, -40, -1, 0, 1, 40, 300, 599))
  @pytest.mark.parametrize("last", (-599, -200, -10, 0, 10, 200, 599))
  def test_guard_only_removes_torque(self, s, target, last):
    guarded, stock = ti_limit(target, last, s), ti_limit(target, last, s, guard=False)
    lo, hi = ti_output_headroom_limits(s, s, TI_LIMITS)
    if lo <= target <= hi and lo <= last <= hi:
      assert guarded == stock
    assert abs(guarded) <= abs(stock) or guarded * stock <= 0
    assert abs(guarded - last) <= max(self.FAST, TI_LIMITS.TI_STEER_DELTA_UP)
    assert abs(guarded) <= TI_LIMITS.TI_STEER_MAX

  @pytest.mark.parametrize("s", range(-60, 61, 5))
  def test_driver_limiter_binds_only_against_an_opposing_hand(self, s):
    lo, hi = ti_driver_torque_limits(s, TI_LIMITS)
    for target in (-599, -300, -40, 0, 40, 300, 599):
      binds = ti_driver_limiter_binds(target, s, TI_LIMITS)
      assert binds == (ti_limit(target, target, s, guard=False) != target)
      assert binds == (not lo <= target <= hi)
      if binds:
        assert s * target < 0 and abs(s) > TI_LIMITS.TI_STEER_DRIVER_ALLOWANCE

  def test_force_zero_ramps_fast(self):
    assert ti_limit(300, 300, 0, zero=True) == 300 - self.FAST
    assert ti_limit(-300, -100, 0, zero=True) == -100 + self.FAST
    assert ti_limit(300, 30, 0, zero=True) == 0
    assert ti_limit(300, 0, 0, zero=True) == 0


class FakeCS:
  def __init__(self, s=0.0, v=10.0, angle=0.0, feedback_seen=True, no_feedback_frames=0):
    self.out = structs.CarState()
    self.out.steeringTorque, self.out.vEgo, self.out.steeringAngleDeg = s, v, angle
    self.ti = TiCarState()
    self.ti.feedback_seen, self.ti.no_feedback_frames = feedback_seen, no_feedback_frames


@pytest.fixture
def ti_ctl():
  return TorqueInterceptor(params())


def ctl_steps(ctl, cs, target, n):
  out = []
  for _ in range(n):
    ctl.driver_torque_hold.append(cs.out.steeringTorque)  # as update() does every frame
    ctl.apply_steer_last = ctl._apply_steer(cs, target)
    ctl.frame += 1
    out.append(ctl.apply_steer_last)
  return out


class TestControllerGuards:
  def test_guard_off_without_ti_feedback(self, ti_ctl):
    # feedbackless fallback: steeringTorque is the stock sensor, not TI counts -> no output guard
    out = ctl_steps(ti_ctl, FakeCS(s=30, feedback_seen=False), 300, 40)
    assert out[-1] == 300
    ti_ctl.apply_steer_last = 0
    out = ctl_steps(ti_ctl, FakeCS(s=30), 300, 40)
    assert out[-1] == (TI_LIMITS.TI_OUTPUT_GUARD_POS - 30) * 12

  def test_guard_uses_held_torque_within_gate_timeout(self, ti_ctl):
    out = ctl_steps(ti_ctl, FakeCS(s=30, no_feedback_frames=TI_FEEDBACK_TIMEOUT_FRAMES), 300, 40)
    assert out[-1] == (TI_LIMITS.TI_OUTPUT_GUARD_POS - 30) * 12

  def test_guard_holds_the_torque_peak_for_0_2_s(self, ti_ctl):
    ti_ctl.apply_steer_last = 240
    ctl_steps(ti_ctl, FakeCS(s=30), 300, 1)
    out = ctl_steps(ti_ctl, FakeCS(s=0), 300, TI_LIMITS.TI_OUTPUT_GUARD_HOLD_FRAMES - 1)
    assert out == [240] * (TI_LIMITS.TI_OUTPUT_GUARD_HOLD_FRAMES - 1)
    assert ctl_steps(ti_ctl, FakeCS(s=0), 300, 4) == [255, 270, 285, 300]

  def test_near_lock_low_speed_zeroes(self, ti_ctl):
    ti_ctl.apply_steer_last = 450
    out = ctl_steps(ti_ctl, FakeCS(v=2.7, angle=454), 599, 20)
    assert out[:3] == [390, 330, 270] and out[-1] == 0
    out = ctl_steps(ti_ctl, FakeCS(v=2.7, angle=-TI_LOCK_ZERO_ANGLE - 1), -599, 5)
    assert out == [0] * 5
    assert ctl_steps(ti_ctl, FakeCS(v=2.7, angle=TI_LOCK_ZERO_ANGLE - 1), 599, 3) == [15, 30, 45]
    ti_ctl.apply_steer_last = 0
    assert ctl_steps(ti_ctl, FakeCS(v=TI_LOCK_ZERO_SPEED + 0.1, angle=454), 599, 3) == [15, 30, 45]

  @pytest.mark.parametrize("target", (-19, -5, 1, 10, 19))
  def test_small_command_never_held(self, ti_ctl, target):
    out = ctl_steps(ti_ctl, FakeCS(), target, 400)
    run, longest = 0, 0
    for a, b in zip(out, out[1:], strict=False):
      run = run + 1 if a == b and a != 0 else 0
      longest = max(longest, run)
      assert abs(b - a) < 20
    assert longest < TI_STUCK_FRAMES
    assert out.count(0) >= 400 // (TI_STUCK_FRAMES + 3) and out.count(target) > 300

  @pytest.mark.parametrize("target", (0, 20, -20, 300))
  def test_other_commands_held(self, ti_ctl, target):
    out = ctl_steps(ti_ctl, FakeCS(), target, 200)
    assert out[-150:] == [target] * 150

  def test_guard_carlog_rate_limited(self, ti_ctl, monkeypatch):
    logs = []
    monkeypatch.setattr(torque_interceptor.carlog, "warning", logs.append)
    for _ in range(5):  # guard toggling on/off (s = 0 outlasts the 0.2 s hold)
      ctl_steps(ti_ctl, FakeCS(s=30), 300, 10)
      ctl_steps(ti_ctl, FakeCS(s=0), 300, 30)
    assert len(logs) == 1 and logs[0].startswith("TI output guard")
    ctl_steps(ti_ctl, FakeCS(s=0), 0, 1000)
    ctl_steps(ti_ctl, FakeCS(s=30), 300, 1)
    assert len(logs) == 2


class TestGuardsEndToEnd:
  def test_same_direction_driver_torque_caps_command(self, ti_car):
    ci, packer = ti_car
    requests = [run_frame(ci, packer, f, ti_feedback(TI_STATE.RUN, torque=30))[0] for f in range(60)]
    assert max(requests) <= (TI_LIMITS.TI_OUTPUT_GUARD_POS - 30) * 12
    assert requests[-1] == (TI_LIMITS.TI_OUTPUT_GUARD_POS - 30) * 12

  def test_short_feedback_gap_is_not_a_lockout(self, ti_car):
    ci, packer = ti_car

    def step(frame, fb):
      request = run_frame(ci, packer, frame, fb)[0]
      return ci.CS.out, request

    frame = 0
    for _ in range(30):
      step(frame, ti_feedback(TI_STATE.RUN))
      frame += 1
    # route 310: 0.15-0.23 s gaps with the TI in RUN + VIOL 0 -> no fault, torque gate closes at 0.2 s
    for i in range(TI_FEEDBACK_LOCKOUT_FRAMES - 1):
      CS, request = step(frame, None)
      frame += 1
      assert not CS.steerFaultTemporary
      if i >= TI_FEEDBACK_TIMEOUT_FRAMES:
        assert request == 0
    CS, request = step(frame, ti_feedback(TI_STATE.RUN))
    frame += 1
    assert not CS.steerFaultTemporary and request == TI_LIMITS.TI_STEER_DELTA_UP
    # >= 0.5 s: a lockout
    for _ in range(TI_FEEDBACK_LOCKOUT_FRAMES):
      CS, request = step(frame, None)
      frame += 1
    assert CS.steerFaultTemporary and ci.CS.ti.locked_out and request == 0
