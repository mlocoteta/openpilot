"""Honda 9G Accord Torque Interceptor (TI) discovery handshake.

Replays the board-state sequence measured in the last working rlog
(2026-09-11, segment 00000284--5800249712--75): 1571 frames OFF with VIOL=23,
200 frames OFF with VIOL=0, then RUN. The board only leaves OFF after a run of
zero-torque TI_STEERING_CONTROL frames, so torque must stay zero on the wire
until it reports RUN, and the frame must keep being sent while the gate is closed.
"""
import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus, apply_ti_steer_torque_limits, structs, ti_driver_limiter_binds, ti_driver_torque_limits
from opendbc.car.can_definitions import CanData
from opendbc.car.car_helpers import interfaces
from opendbc.car.honda import carcontroller, carstate, hondacan, interface
from opendbc.car.honda.values import CAR, DBC, TI_DISCOVERY_FRAMES, TI_FEEDBACK_TIMEOUT_FRAMES, TI_LIMITS, TI_STATE, TI_OPTION, \
                                     TI_RESET_HANDS_OFF_FRAMES, TI_RESET_BURST_FRAMES, TI_RESET_COOLDOWN_FRAMES, TI_RESET_MAX_ATTEMPTS, \
                                     TI_RESET_HANDS_OFF_TORQUE, TI_FEEDBACK_LOCKOUT_FRAMES, TI_LOCK_ZERO_SPEED, TI_LOCK_ZERO_ANGLE, \
                                     TI_STUCK_FRAMES
from opendbc.car.tests.test_car_interfaces import get_test_starpilot_toggles

TI_STEERING_CONTROL = 0x249
TI_FEEDBACK = 0x24A
DT_NS = 10_000_000


class FakeParams:
  def __init__(self, *args, **kwargs):
    pass

  def get_bool(self, key, *args, **kwargs):
    return key == "TorqueInterceptorEnabled"

  def get_float(self, key, *args, default=0.0, **kwargs):
    return default

  def get_int(self, key, *args, default=0, **kwargs):
    return default

  def get(self, *args, **kwargs):
    return None

  def put_float(self, *args, **kwargs):
    pass


def ti_feedback(state, viol=0, torque=0, version=6, ramp_down=0):
  return {"STATE": state, "VIOL": viol, "ERROR": 0, "VERSION_NUMBER": version,
          "RAMP_DOWN": ramp_down, "TI_TORQUE_SENSOR": torque}


def new_gate():
  cs = carstate.CarState.__new__(carstate.CarState)
  cs.reset_ti_gate()
  return cs


class TestTIGate:
  def test_measured_sequence_blocks_until_run(self):
    cs = new_gate()
    assert cs.ti_state == TI_STATE.OFF
    for _ in range(1571):
      assert not cs.update_ti_gate(ti_feedback(TI_STATE.OFF, viol=23))
    for _ in range(200):
      assert not cs.update_ti_gate(ti_feedback(TI_STATE.OFF))
    assert cs.update_ti_gate(ti_feedback(TI_STATE.RUN))

  @pytest.mark.parametrize("state", (TI_STATE.DISCOVER, TI_STATE.OFF, TI_STATE.DRIVER_OVER))
  def test_non_run_states_block(self, state):
    cs = new_gate()
    cs.update_ti_gate(ti_feedback(TI_STATE.RUN))
    assert not cs.update_ti_gate(ti_feedback(state))

  def test_ramp_down_blocks(self):
    cs = new_gate()
    assert cs.update_ti_gate(ti_feedback(TI_STATE.RUN))
    assert not cs.update_ti_gate(ti_feedback(TI_STATE.RUN, ramp_down=1))

  def test_fallback_only_without_any_feedback(self):
    cs = new_gate()
    for _ in range(TI_DISCOVERY_FRAMES - 1):
      assert not cs.update_ti_gate(None)
    assert cs.update_ti_gate(None)
    # Feedback arriving later takes over from the fallback.
    assert not cs.update_ti_gate(ti_feedback(TI_STATE.OFF))

  def test_no_reopen_after_dropout(self):
    cs = new_gate()
    assert cs.update_ti_gate(ti_feedback(TI_STATE.RUN))
    for _ in range(TI_FEEDBACK_TIMEOUT_FRAMES):
      assert cs.update_ti_gate(None)
    for _ in range(TI_DISCOVERY_FRAMES * 2):
      assert not cs.update_ti_gate(None)
    assert cs.update_ti_gate(ti_feedback(TI_STATE.RUN))



class TestTIDriverTorque:
  """A missing TI_FEEDBACK frame must not read the stock EPS sensor (which sees the TI's own torque)."""
  STOCK_THR = 30

  def test_single_gap_holds_last_ti_torque(self):
    cs = new_gate()
    assert cs.update_ti_driver_torque(ti_feedback(TI_STATE.RUN, torque=2), 0, self.STOCK_THR) == (2, False)
    cs.update_ti_gate(ti_feedback(TI_STATE.RUN, torque=2))
    # gap frame: stock sensor reads 64 counts of TI-injected torque -> must not become a press
    torque, pressed = cs.update_ti_driver_torque(None, 64, self.STOCK_THR)
    assert (torque, pressed) == (2, False)
    cs.update_ti_gate(None)

  def test_hold_keeps_a_real_press(self):
    cs = new_gate()
    cs.update_ti_driver_torque(ti_feedback(TI_STATE.RUN, torque=-40), 0, self.STOCK_THR)
    cs.update_ti_gate(ti_feedback(TI_STATE.RUN, torque=-40))
    assert cs.update_ti_driver_torque(None, 0, self.STOCK_THR) == (-40, True)

  def test_real_driver_torque_detected_on_next_feedback_frame(self):
    cs = new_gate()
    for tq in (1, 3):
      cs.update_ti_driver_torque(ti_feedback(TI_STATE.RUN, torque=tq), 0, self.STOCK_THR)
      cs.update_ti_gate(ti_feedback(TI_STATE.RUN, torque=tq))
    cs.update_ti_driver_torque(None, 64, self.STOCK_THR); cs.update_ti_gate(None)
    assert cs.update_ti_driver_torque(ti_feedback(TI_STATE.RUN, torque=20), 64, self.STOCK_THR) == (20, True)

  def test_hold_is_bounded_by_feedback_timeout(self):
    cs = new_gate()
    cs.update_ti_driver_torque(ti_feedback(TI_STATE.RUN, torque=2), 0, self.STOCK_THR)
    cs.update_ti_gate(ti_feedback(TI_STATE.RUN, torque=2))
    for _ in range(TI_FEEDBACK_TIMEOUT_FRAMES):
      assert cs.update_ti_driver_torque(None, 64, self.STOCK_THR) == (2, False)
      assert cs.update_ti_gate(None)  # gate still open for exactly this window
    # feedback lost for longer than the gate tolerates: gate closes and the stock sensor is used again
    assert cs.update_ti_driver_torque(None, 64, self.STOCK_THR) == (64, True)
    assert not cs.update_ti_gate(None)

  def test_stock_sensor_before_any_feedback(self):
    cs = new_gate()
    assert cs.update_ti_driver_torque(None, 64, self.STOCK_THR) == (64, True)
    assert cs.update_ti_driver_torque(None, 10, self.STOCK_THR) == (10, False)


def reset_step(cs, fb):
  """One carState frame of the TI path; returns the OPTION chosen for this frame."""
  cs.update_ti_driver_torque(fb, 0, 30)
  cs.update_ti_gate(fb)
  return cs.update_ti_reset(fb)


def locked_gate():
  """A gate that reached RUN and then locked out (OFF, VIOL 23), as in the weekend rlogs."""
  cs = new_gate()
  for _ in range(10):
    assert reset_step(cs, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL
  reset_step(cs, ti_feedback(TI_STATE.OFF, viol=23, torque=60))
  assert cs.ti_locked_out
  return cs


LOCKED = ti_feedback(TI_STATE.OFF, viol=23)


class TestTIAutoReset:
  def test_no_reset_or_alert_during_startup(self):
    # startup replay (2026-09-11 rlog): long OFF + VIOL 23 before the first RUN, hands off
    cs = new_gate()
    for _ in range(1571):
      assert reset_step(cs, ti_feedback(TI_STATE.OFF, viol=23)) == TI_OPTION.NORMAL
      assert not cs.ti_locked_out
    for _ in range(200):
      assert reset_step(cs, ti_feedback(TI_STATE.OFF)) == TI_OPTION.NORMAL
      assert not cs.ti_locked_out
    assert reset_step(cs, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL
    assert cs.ti_run_seen and not cs.ti_locked_out

  def test_lockout_raises_alert(self):
    cs = locked_gate()
    assert cs.ti_locked_out and not cs.ti_lkas_allowed

  def test_driver_override_is_not_a_lockout(self):
    cs = new_gate()
    reset_step(cs, ti_feedback(TI_STATE.RUN))
    for _ in range(200):
      assert reset_step(cs, ti_feedback(TI_STATE.DRIVER_OVER, torque=90)) == TI_OPTION.NORMAL
      assert not cs.ti_locked_out
    reset_step(cs, ti_feedback(TI_STATE.DRIVER_OVER, viol=17, torque=90))
    assert cs.ti_locked_out

  def test_feedback_loss_after_run_alerts_but_never_resets(self):
    cs = new_gate()
    reset_step(cs, ti_feedback(TI_STATE.RUN))
    for _ in range(TI_FEEDBACK_LOCKOUT_FRAMES - 1):
      reset_step(cs, None)
      assert not cs.ti_locked_out  # tolerated gap
    for _ in range(1000):
      assert reset_step(cs, None) == TI_OPTION.NORMAL
      assert cs.ti_locked_out

  def test_reset_only_after_hands_off_debounce(self):
    cs = locked_gate()
    for _ in range(1000):  # driver still holding the wheel hard
      assert reset_step(cs, ti_feedback(TI_STATE.OFF, viol=23, torque=60)) == TI_OPTION.NORMAL
    # a short release interrupted by another grab restarts the debounce
    for _ in range(TI_RESET_HANDS_OFF_FRAMES - 5):
      assert reset_step(cs, LOCKED) == TI_OPTION.NORMAL
    assert reset_step(cs, ti_feedback(TI_STATE.OFF, viol=23, torque=-TI_RESET_HANDS_OFF_TORQUE - 1)) == TI_OPTION.NORMAL
    for _ in range(TI_RESET_HANDS_OFF_FRAMES - 1):
      assert reset_step(cs, LOCKED) == TI_OPTION.NORMAL
    assert reset_step(cs, LOCKED) == TI_OPTION.COLD_RESET
    assert cs.ti_reset_attempts == 1

  def test_light_touch_counts_as_hands_off(self):
    cs = locked_gate()
    opts = [reset_step(cs, ti_feedback(TI_STATE.OFF, viol=23, torque=TI_RESET_HANDS_OFF_TORQUE))
            for _ in range(TI_RESET_HANDS_OFF_FRAMES)]
    assert opts[-1] == TI_OPTION.COLD_RESET and TI_OPTION.COLD_RESET not in opts[:-1]

  def test_burst_length(self):
    cs = locked_gate()
    opts = [reset_step(cs, LOCKED) for _ in range(TI_RESET_HANDS_OFF_FRAMES + 50)]
    first = opts.index(TI_OPTION.COLD_RESET)
    assert first == TI_RESET_HANDS_OFF_FRAMES - 1
    assert opts[first:first + TI_RESET_BURST_FRAMES] == [TI_OPTION.COLD_RESET] * TI_RESET_BURST_FRAMES
    assert TI_OPTION.COLD_RESET not in opts[first + TI_RESET_BURST_FRAMES:]

  def test_no_reset_while_board_restarting(self):
    # VIOL cleared (the ~2 s OFF + VIOL 0 restart delay, or DISCOVER after a reset): alert stays, no reset
    cs = locked_gate()
    for state in (TI_STATE.OFF, TI_STATE.DISCOVER):
      for _ in range(1000):
        assert reset_step(cs, ti_feedback(state)) == TI_OPTION.NORMAL
        assert cs.ti_locked_out
    assert cs.ti_reset_attempts == 0

  def test_cooldown_and_retry_cap(self):
    cs = locked_gate()
    opts = [reset_step(cs, LOCKED) for _ in range(5000)]
    starts = [i for i, o in enumerate(opts) if o == TI_OPTION.COLD_RESET and (i == 0 or opts[i - 1] != o)]
    assert len(starts) == TI_RESET_MAX_ATTEMPTS
    assert all(b - a == TI_RESET_BURST_FRAMES + TI_RESET_COOLDOWN_FRAMES for a, b in zip(starts, starts[1:], strict=False))
    assert opts.count(TI_OPTION.COLD_RESET) == TI_RESET_MAX_ATTEMPTS * TI_RESET_BURST_FRAMES
    assert cs.ti_locked_out  # capped: alert remains until the board recovers by itself

  def test_recovery_clears_alert_and_counters(self):
    cs = locked_gate()
    for _ in range(5000):
      reset_step(cs, LOCKED)
    assert cs.ti_reset_attempts == TI_RESET_MAX_ATTEMPTS
    assert reset_step(cs, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL
    assert not cs.ti_locked_out and cs.ti_lkas_allowed
    assert (cs.ti_reset_attempts, cs.ti_reset_cooldown, cs.ti_reset_burst_left, cs.ti_hands_off_frames) == (0, 0, 0, 0)
    # a later lockout gets a fresh set of attempts
    opts = [reset_step(cs, LOCKED) for _ in range(TI_RESET_HANDS_OFF_FRAMES)]
    assert opts[-1] == TI_OPTION.COLD_RESET

  def test_run_mid_burst_stops_burst(self):
    cs = locked_gate()
    for _ in range(TI_RESET_HANDS_OFF_FRAMES + 2):
      reset_step(cs, LOCKED)
    assert cs.ti_reset_burst_left > 0
    assert reset_step(cs, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL
    assert reset_step(cs, ti_feedback(TI_STATE.RUN)) == TI_OPTION.NORMAL


class TestTIOptionPacking:
  @staticmethod
  def pack(steer, option=TI_OPTION.NORMAL):
    packer = CANPacker(DBC[CAR.HONDA_ACCORD_9G][Bus.pt])
    addr, dat, bus = hondacan.create_ti_steering_control(packer, steer, option)
    assert (addr, bus) == (TI_STEERING_CONTROL, 0)
    return dat

  def test_normal_frame_unchanged(self):
    # same bytes as the old hard-coded KEY = 3294744160 (0xC461CE60)
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
def ti_interface(monkeypatch):
  for module in (carstate, carcontroller, interface):
    monkeypatch.setattr(module, "Params", FakeParams, raising=False)
  toggles = get_test_starpilot_toggles()
  fingerprint = {bus: {} for bus in range(8)}
  CarInterface = interfaces[CAR.HONDA_ACCORD_9G]
  CP = CarInterface.get_params(CAR.HONDA_ACCORD_9G, fingerprint, [], alpha_long=False, is_release=False, docs=False,
                               starpilot_toggles=toggles)
  FPCP = CarInterface.get_starpilot_params(CAR.HONDA_ACCORD_9G, fingerprint, [], CP, toggles)
  CI = CarInterface(CP, FPCP)
  assert CI.CS.ti_enabled and CI.CC.has_ti
  return CI, toggles, CANPacker(DBC[CP.carFingerprint][Bus.pt])


def run_frame(CI, toggles, packer, frame, feedback, torque=0.5):
  msgs = []
  if feedback is not None:
    addr, dat, bus = packer.make_can_msg("TI_FEEDBACK", 0, feedback)
    msgs.append(CanData(addr, dat, bus))
  CI.update([(frame * DT_NS, msgs)], toggles)
  CC = structs.CarControl()
  CC.enabled = CC.latActive = True
  CC.actuators.torque = torque
  _, sends = CI.apply(CC.as_reader(), frame * DT_NS, toggles)
  ti = [dat for addr, dat, bus in sends if addr == TI_STEERING_CONTROL]
  assert len(ti) == 1 and ti[0] is not None, "TI frame must be sent every frame"
  dat = ti[0]
  request = ((dat[0] & 0x0F) << 8 | dat[1]) - 2048
  return request, dat


class TestTIController:
  def test_zero_torque_handshake_then_ramp(self, ti_interface):
    CI, toggles, packer = ti_interface
    frame = 0
    for _ in range(1571):
      request, dat = run_frame(CI, toggles, packer, frame, ti_feedback(TI_STATE.OFF, viol=23))
      assert request == 0 and len(dat) == 8
      frame += 1
    for _ in range(200):
      request, _ = run_frame(CI, toggles, packer, frame, ti_feedback(TI_STATE.OFF))
      assert request == 0
      frame += 1
    requests = [run_frame(CI, toggles, packer, frame + i, ti_feedback(TI_STATE.RUN))[0] for i in range(5)]
    assert requests == [TI_LIMITS.TI_STEER_DELTA_UP * (i + 1) for i in range(5)]

  def test_zero_request_wire_format(self, ti_interface):
    CI, toggles, packer = ti_interface
    _, dat = run_frame(CI, toggles, packer, 0, ti_feedback(TI_STATE.OFF))
    # LKAS_REQUEST and CHKSUM are 12-bit with a +2048 offset: neutral is 0x800.
    assert dat[0] & 0x0F == 0x8 and dat[1] == 0x00
    assert dat[2] == 0x08 and dat[3] == 0x00

  def test_dropout_zeroes_torque(self, ti_interface):
    CI, toggles, packer = ti_interface
    for frame in range(10):
      request, _ = run_frame(CI, toggles, packer, frame, ti_feedback(TI_STATE.RUN))
    assert request != 0
    for frame in range(10, 10 + TI_FEEDBACK_TIMEOUT_FRAMES + 1):
      request, _ = run_frame(CI, toggles, packer, frame, None)
    assert request == 0
    for frame in range(100, 100 + TI_DISCOVERY_FRAMES + 10):
      request, _ = run_frame(CI, toggles, packer, frame, None)
      assert request == 0

  def test_feedbackless_fallback(self, ti_interface):
    CI, toggles, packer = ti_interface
    for frame in range(TI_DISCOVERY_FRAMES - 1):
      request, _ = run_frame(CI, toggles, packer, frame, None)
      assert request == 0
    request, _ = run_frame(CI, toggles, packer, TI_DISCOVERY_FRAMES, None)
    assert request == TI_LIMITS.TI_STEER_DELTA_UP


class TestTIReportedOutput:
  """carOutput must report the TI command, not the stock LKAS limiter's output.

  controlsd freezes the lateral integrator whenever requested and reported torque differ,
  and torqued learns from the reported torque, so both need what the TI actually sent.
  """
  @staticmethod
  def apply(CI, toggles, packer, frame, feedback, torque):
    addr, dat, bus = packer.make_can_msg("TI_FEEDBACK", 0, feedback)
    CI.update([(frame * DT_NS, [CanData(addr, dat, bus)])], toggles)
    CC = structs.CarControl()
    CC.enabled = CC.latActive = True
    CC.actuators.torque = torque
    actuators, sends = CI.apply(CC.as_reader(), frame * DT_NS, toggles)
    dat = next(dat for addr, dat, bus in sends if addr == TI_STEERING_CONTROL)
    return actuators, ((dat[0] & 0x0F) << 8 | dat[1]) - 2048

  def test_reports_ti_command(self, ti_interface):
    CI, toggles, packer = ti_interface
    for frame in range(30):
      actuators, request = self.apply(CI, toggles, packer, frame, ti_feedback(TI_STATE.RUN), 0.5)
      assert actuators.torqueOutputCan == request
      assert actuators.torque == pytest.approx(request / TI_LIMITS.TI_STEER_MAX)
    # The TI reaches the request well before the stock limiter would, so the
    # integrator must not be treated as limited once it has.
    assert abs(0.5 - actuators.torque) < 1e-2

  def test_reports_zero_while_board_not_running(self, ti_interface):
    CI, toggles, packer = ti_interface
    for frame in range(50):
      actuators, request = self.apply(CI, toggles, packer, frame, ti_feedback(TI_STATE.OFF), 0.5)
      assert request == 0 and actuators.torque == 0.0 and actuators.torqueOutputCan == 0


class TestNidecWindBrake:
  def test_other_nidec_cars_keep_stock_curve(self):
    for v, expected in ((0.0, 0.001), (2.3, 0.002), (35.0, 0.15)):
      assert carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_CIVIC) == pytest.approx(expected)

  def test_accord_9g_brakes_for_mild_decel_at_highway_speed(self):
    v = 22.4  # 50 mph
    stock = carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_CIVIC)
    wind_brake = carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_ACCORD_9G)
    assert wind_brake == pytest.approx(0.136 / carcontroller.ACCORD_9G_BRAKE_ACCEL_PER_UNIT)
    assert wind_brake < stock / 2
    # brakes engage (hysteresis on at 0.02) for requests below ~-0.23 m/s^2 instead of ~-0.55
    assert (wind_brake + 0.02) * carcontroller.ACCORD_9G_BRAKE_ACCEL_PER_UNIT < 0.25

  def test_accord_9g_keeps_low_speed_floor_and_is_monotonic(self):
    assert carcontroller.get_honda_nidec_wind_brake(0.0, CAR.HONDA_ACCORD_9G) == pytest.approx(0.001)
    assert carcontroller.get_honda_nidec_wind_brake(2.3, CAR.HONDA_ACCORD_9G) >= 0.002
    speeds = [0.0, 1.0, 2.3, 5.0, 13.4, 22.4, 31.3, 40.2, 50.0]
    values = [carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_ACCORD_9G) for v in speeds]
    assert values == sorted(values)
    assert all(0.0 < w <= 0.15 for w in values)


class TestNidecBrakeGain:
  def test_other_nidec_cars_keep_stock_gain(self):
    assert carcontroller.compute_gas_brake(-1.2, 20.0, CAR.HONDA_CIVIC) == (0.0, pytest.approx(0.25))
    assert carcontroller.compute_gas_brake(0.96, 20.0, CAR.HONDA_CIVIC) == (pytest.approx(0.2), 0.0)

  def test_accord_9g_brakes_harder_per_request_but_gas_unchanged(self):
    gas, brake = carcontroller.compute_gas_brake(-1.2, 20.0, CAR.HONDA_ACCORD_9G)
    assert gas == 0.0 and brake == pytest.approx(1.2 / 3.6)
    assert carcontroller.compute_gas_brake(0.96, 20.0, CAR.HONDA_ACCORD_9G) == (pytest.approx(0.2), 0.0)

  def test_accord_9g_creep_brake_unchanged_at_standstill(self):
    assert carcontroller.compute_gas_brake(0.0, 0.0, CAR.HONDA_ACCORD_9G)[1] == pytest.approx(0.15)
    assert carcontroller.compute_gas_brake(-3.6, 30.0, CAR.HONDA_ACCORD_9G)[1] == pytest.approx(1.0)


class TestTIDriverTorqueEndToEnd:
  def test_missing_feedback_frame_is_not_a_press(self, ti_interface):
    """Replays the weekend blip: stock STEER_TORQUE_SENSOR reads the TI's injected torque (64)."""
    CI, toggles, packer = ti_interface
    pressed = []
    for frame in range(1, 40):
      msgs = [CanData(*packer.make_can_msg("STEER_STATUS", 0, {"STEER_TORQUE_SENSOR": 64, "COUNTER": frame % 4}))]
      if frame != 20:  # one frame without TI_FEEDBACK
        msgs.append(CanData(*packer.make_can_msg("TI_FEEDBACK", 0, ti_feedback(TI_STATE.RUN, torque=1))))
      CS = CI.update([(frame * DT_NS, msgs)], toggles)[0]
      pressed.append(CS.steeringPressed)
      if frame >= 5:
        assert abs(CS.steeringTorque) <= 1
    assert not any(pressed[5:])


class TestTIAutoResetEndToEnd:
  def test_lockout_alert_and_reset_on_the_wire(self, ti_interface):
    CI, toggles, packer = ti_interface

    def frame_(frame, fb):
      msgs = [CanData(*packer.make_can_msg("TI_FEEDBACK", 0, fb))]
      CS = CI.update([(frame * DT_NS, msgs)], toggles)[0]
      CC = structs.CarControl()
      CC.enabled = CC.latActive = True
      CC.actuators.torque = 0.5
      _, sends = CI.apply(CC.as_reader(), frame * DT_NS, toggles)
      dat = next(dat for addr, dat, bus in sends if addr == TI_STEERING_CONTROL)
      return CS, ((dat[0] & 0x0F) << 8 | dat[1]) - 2048, dat[7]

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
    # bursts at 139, 449, 759: capped at TI_RESET_MAX_ATTEMPTS
    assert options.count(TI_OPTION.COLD_RESET) == TI_RESET_MAX_ATTEMPTS * TI_RESET_BURST_FRAMES
    assert set(options) == {TI_OPTION.NORMAL, TI_OPTION.COLD_RESET}
    # board recovers
    for _ in range(20):
      CS, request, option = frame_(frame, ti_feedback(TI_STATE.RUN))
      assert not CS.steerFaultTemporary and option == TI_OPTION.NORMAL
      frame += 1
    assert request != 0


def ti_limit(target, last, s, guard=True, zero=False):
  return apply_ti_steer_torque_limits(target, last, s, TI_LIMITS, output_guard=guard, force_zero=zero)


def ti_output(s, cmd):
  return s + cmd / TI_LIMITS.TI_OUTPUT_TORQUE_DIV


class TestTIOutputHeadroomGuard:
  """lockout-prevention report 2026-09-29, section 7 #1: s + cmd/12 must stay inside +40/-35 when both agree."""
  FAST = TI_LIMITS.TI_STEER_DELTA_DOWN_FAST

  @pytest.mark.parametrize("s", (1, 10, 30, 39, 40, 60))
  def test_caps_same_direction_positive(self, s):
    last, out = TI_LIMITS.TI_STEER_MAX, []
    for _ in range(20):
      last = ti_limit(TI_LIMITS.TI_STEER_MAX, last, s)
      out.append(last)
    assert out[-1] == max((TI_LIMITS.TI_OUTPUT_GUARD_POS - s) * TI_LIMITS.TI_OUTPUT_TORQUE_DIV, 0)
    assert ti_output(s, out[-1]) <= max(TI_LIMITS.TI_OUTPUT_GUARD_POS, s)

  @pytest.mark.parametrize("s", (-1, -10, -20, -35, -60))
  def test_caps_same_direction_negative(self, s):
    last = -TI_LIMITS.TI_STEER_MAX
    for _ in range(20):
      last = ti_limit(-TI_LIMITS.TI_STEER_MAX, last, s)
    assert last == min((-TI_LIMITS.TI_OUTPUT_GUARD_NEG - s) * TI_LIMITS.TI_OUTPUT_TORQUE_DIV, 0)

  def test_fast_step_toward_zero_when_binding(self):
    # trip #34 (route 310): s = 27, cmd 434 -> 49.6 counts, pushing 434 -> 156 at 60/frame
    seq, last = [], 434
    while True:
      nxt = ti_limit(434, last, 27)
      if nxt == last:
        break
      seq.append(last - nxt)
      last = nxt
    assert last == (40 - 27) * 12 and seq[:-1] == [self.FAST] * (len(seq) - 1) and seq[-1] <= self.FAST
    # without the guard binding the normal down-rate applies
    assert ti_limit(0, 300, 0) == 300 - TI_LIMITS.TI_STEER_DELTA_DOWN

  def test_up_rate_unchanged(self):
    assert ti_limit(TI_LIMITS.TI_STEER_MAX, 0, 10) == TI_LIMITS.TI_STEER_DELTA_UP
    assert ti_limit(-TI_LIMITS.TI_STEER_MAX, 0, -10) == -TI_LIMITS.TI_STEER_DELTA_UP

  @pytest.mark.parametrize("s", range(-80, 81, 8))
  @pytest.mark.parametrize("target", (-599, -300, -40, -1, 0, 1, 40, 300, 599))
  @pytest.mark.parametrize("last", (-599, -200, -10, 0, 10, 200, 599))
  def test_never_alters_opposing_or_unaffected_commands(self, s, target, last):
    guarded, stock = ti_limit(target, last, s), ti_limit(target, last, s, guard=False)
    if s * target <= 0:  # opposing the driver, or no driver direction: the guard never touches it
      assert guarded == stock
    else:
      # same direction: never more torque than without the guard, never the other way past zero
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


@pytest.fixture
def ti_cc(ti_interface):
  return ti_interface[0].CC


def fake_cs(s=0.0, v=10.0, angle=0.0, feedback_seen=True, no_feedback_frames=0):
  out = structs.CarState()
  out.steeringTorque, out.vEgo, out.steeringAngleDeg = s, v, angle
  cs = carstate.CarState.__new__(carstate.CarState)
  cs.reset_ti_gate()
  cs.out = out
  cs.ti_feedback_seen, cs.ti_no_feedback_frames = feedback_seen, no_feedback_frames
  return cs


def cc_steps(cc, cs, target, n):
  out = []
  for _ in range(n):
    cc.ti_apply_steer_last = cc._ti_apply_steer(cs, target)
    cc.frame += 1
    out.append(cc.ti_apply_steer_last)
  return out


class TestTIControllerGuards:
  def test_guard_off_without_ti_feedback(self, ti_cc):
    # feedbackless fallback: steeringTorque is the stock sensor, not TI counts -> no output guard
    out = cc_steps(ti_cc, fake_cs(s=30, feedback_seen=False), 300, 40)
    assert out[-1] == 300
    ti_cc.ti_apply_steer_last = 0
    out = cc_steps(ti_cc, fake_cs(s=30), 300, 40)
    assert out[-1] == (40 - 30) * 12

  def test_guard_uses_held_torque_within_gate_timeout(self, ti_cc):
    out = cc_steps(ti_cc, fake_cs(s=30, no_feedback_frames=TI_FEEDBACK_TIMEOUT_FRAMES), 300, 40)
    assert out[-1] == 120

  def test_near_lock_low_speed_zeroes(self, ti_cc):
    ti_cc.ti_apply_steer_last = 450
    out = cc_steps(ti_cc, fake_cs(v=2.7, angle=454), 599, 20)
    assert out[:3] == [390, 330, 270] and out[-1] == 0
    out = cc_steps(ti_cc, fake_cs(v=2.7, angle=-TI_LOCK_ZERO_ANGLE - 1), -599, 5)
    assert out == [0] * 5
    # out of the region: normal ramp resumes
    assert cc_steps(ti_cc, fake_cs(v=2.7, angle=TI_LOCK_ZERO_ANGLE - 1), 599, 3) == [15, 30, 45]
    ti_cc.ti_apply_steer_last = 0
    assert cc_steps(ti_cc, fake_cs(v=TI_LOCK_ZERO_SPEED + 0.1, angle=454), 599, 3) == [15, 30, 45]

  @pytest.mark.parametrize("target", (-19, -5, 1, 10, 19))
  def test_small_command_never_held(self, ti_cc, target):
    out = cc_steps(ti_cc, fake_cs(), target, 400)
    run, longest = 0, 0
    for a, b in zip(out, out[1:], strict=False):
      run = run + 1 if a == b and a != 0 else 0
      longest = max(longest, run)
      assert abs(b - a) < 20
    assert longest < TI_STUCK_FRAMES
    assert out.count(0) >= 400 // (TI_STUCK_FRAMES + 3) and out.count(target) > 300

  @pytest.mark.parametrize("target", (0, 20, -20, 300))
  def test_other_commands_held(self, ti_cc, target):
    out = cc_steps(ti_cc, fake_cs(), target, 200)
    assert out[-150:] == [target] * 150

  def test_guard_carlog_rate_limited(self, ti_cc, monkeypatch):
    logs = []
    monkeypatch.setattr(carcontroller.carlog, "warning", logs.append)
    for _ in range(5):  # guard toggling on/off every 10 frames
      cc_steps(ti_cc, fake_cs(s=30), 300, 10)
      cc_steps(ti_cc, fake_cs(s=0), 300, 10)
    assert len(logs) == 1 and logs[0].startswith("TI output guard")
    cc_steps(ti_cc, fake_cs(s=0), 0, 1000)
    cc_steps(ti_cc, fake_cs(s=30), 300, 1)
    assert len(logs) == 2


class TestTIGuardsEndToEnd:
  def test_same_direction_driver_torque_caps_command(self, ti_interface):
    CI, toggles, packer = ti_interface
    requests = [run_frame(CI, toggles, packer, f, ti_feedback(TI_STATE.RUN, torque=30), torque=0.5)[0] for f in range(60)]
    assert max(requests) <= (40 - 30) * 12 and requests[-1] == 120

  def test_short_feedback_gap_is_not_a_lockout(self, ti_interface):
    CI, toggles, packer = ti_interface

    def step(frame, fb):
      msgs = [CanData(*packer.make_can_msg("TI_FEEDBACK", 0, fb))] if fb is not None else []
      CS = CI.update([(frame * DT_NS, msgs)], toggles)[0]
      CC = structs.CarControl()
      CC.enabled = CC.latActive = True
      CC.actuators.torque = 0.5
      _, sends = CI.apply(CC.as_reader(), frame * DT_NS, toggles)
      dat = next(dat for addr, dat, bus in sends if addr == TI_STEERING_CONTROL)
      return CS, ((dat[0] & 0x0F) << 8 | dat[1]) - 2048

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
    assert CS.steerFaultTemporary and CI.CS.ti_locked_out and request == 0
