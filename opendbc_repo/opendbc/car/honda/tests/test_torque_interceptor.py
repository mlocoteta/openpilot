"""Honda 9G Accord Torque Interceptor (TI): qualification, discovery handshake and 0x249 output.

The handshake replays the board-state sequence measured in the last working 6.x rlog
(2026-09-11, segment 00000284--5800249712--75): 1571 frames OFF with VIOL=23, 200 frames OFF
with VIOL=0, then RUN. The board only leaves OFF after a run of zero-torque TI_STEERING_CONTROL
frames, so torque must stay zero on the wire until it reports RUN, and the frame must keep being
sent while the gate is closed.
"""
import math

import pytest

from opendbc.can import CANPacker, CANParser
from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.can_definitions import CanData
from opendbc.car.honda import nidec_interceptor, stock_aol
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.torque_interceptor import (TI_DISCOVERY_FRAMES, TI_FEEDBACK_TIMEOUT_FRAMES, TI_LIMITS, TI_SAFETY_PARAM,
                                                 TI_STATE, TI_STEER_ACTUATOR_DELAY, TiCarState, TorqueInterceptor,
                                                 apply_ti_steer_torque_limits, apply_torque_interceptor, ti_qualified,
                                                 ti_supported)
from opendbc.car.honda.values import CAR, DBC, HondaSafetyFlags

TI_STEERING_CONTROL = 0x249
DT_NS = 10_000_000


def params(identity=CAR.HONDA_ACCORD_9G, *, pedal=True, ti=True):
  fp = gen_empty_fingerprint()
  if pedal:
    fp[0][0x201] = 6
  cp = CarInterface.get_params(identity, fp, [], False, False, False)
  apply_torque_interceptor(cp, ti)
  return cp


def ti_feedback(state, viol=0, torque=0, version=6, ramp_down=0):
  return {"STATE": state, "VIOL": viol, "ERROR": 0, "VERSION_NUMBER": version,
          "RAMP_DOWN": ramp_down, "TI_TORQUE_SENSOR": torque}


class TestQualification:
  @pytest.mark.parametrize("pedal,base", ((True, 36), (False, 4)))
  def test_ti_bit_on_the_9g(self, pedal, base):
    cp = params(pedal=pedal)
    assert int(HondaSafetyFlags.TORQUE_INTERCEPTOR) == TI_SAFETY_PARAM == 4096
    assert cp.safetyConfigs[0].safetyParam == base | 4096
    assert ti_qualified(cp)
    assert cp.steerActuatorDelay == TI_STEER_ACTUATOR_DELAY

  @pytest.mark.parametrize("pedal,base", ((True, 36), (False, 4)))
  def test_off_leaves_the_stock_word(self, pedal, base):
    stock = params(pedal=pedal, ti=False)
    assert stock.safetyConfigs[0].safetyParam == base
    assert ti_supported(stock) and not ti_qualified(stock)
    # off -> on -> off restores the exact stock CarParams
    cp = params(pedal=pedal, ti=True)
    apply_torque_interceptor(cp, False)
    assert cp.safetyConfigs[0].safetyParam == base
    cp.steerActuatorDelay = stock.steerActuatorDelay
    assert cp.to_dict() == stock.to_dict()

  @pytest.mark.parametrize("identity", (CAR.HONDA_CIVIC, CAR.ACURA_MDX_3G, CAR.HONDA_CRV, CAR.HONDA_ACCORD, CAR.HONDA_ACCORD_11G))
  def test_other_hondas_never_get_the_bit(self, identity):
    cp = params(identity)
    assert not ti_supported(cp) and not ti_qualified(cp)
    assert not cp.safetyConfigs[0].safetyParam & TI_SAFETY_PARAM

  @pytest.mark.parametrize("field", ("passive", "dashcamOnly", "notCar"))
  def test_uncontrolled_car_is_not_supported(self, field):
    cp = params(ti=False)
    setattr(cp, field, True)
    apply_torque_interceptor(cp, True)
    assert not cp.safetyConfigs[0].safetyParam & TI_SAFETY_PARAM

  def test_pedal_interceptor_still_qualifies_with_ti(self):
    cp = params(pedal=True)
    assert nidec_interceptor.qualified(cp)
    ci = CarInterface(cp)
    assert ci.CC.nidec_interceptor is not None and ci.CC.ti is not None

  @pytest.mark.parametrize("pedal", (True, False))
  @pytest.mark.parametrize("experience", (0, 32))
  def test_ti_car_is_never_stock_aol(self, pedal, experience):
    cp = params(pedal=pedal)
    cp.alternativeExperience = experience
    assert not stock_aol.qualified(cp)
    assert not stock_aol.qualified(cp, marked_only=True)

  def test_construction_follows_the_bit(self):
    on = CarInterface(params(ti=True))
    assert isinstance(on.CC.ti, TorqueInterceptor) and isinstance(on.CS.ti, TiCarState)
    state = on.can_parsers[Bus.pt].message_states[0x24A]
    # NaN, not 0: 7.0 CANParser learns and then requires a freq-0 message, which would raise
    # canError while the silent board waits for the handshake.
    assert state.ignore_alive

    off = CarInterface(params(ti=False))
    assert off.CC.ti is None and off.CS.ti is None
    assert 0x24A not in off.can_parsers[Bus.pt].message_states

  def test_unqualified_controller_refuses(self):
    with pytest.raises(ValueError):
      TorqueInterceptor(params(ti=False))


class TestGate:
  def test_measured_sequence_blocks_until_run(self):
    cs = TiCarState()
    assert cs.state == TI_STATE.OFF
    for _ in range(1571):
      assert not cs.update_gate(ti_feedback(TI_STATE.OFF, viol=23))
    for _ in range(200):
      assert not cs.update_gate(ti_feedback(TI_STATE.OFF))
    assert cs.update_gate(ti_feedback(TI_STATE.RUN))

  @pytest.mark.parametrize("state", (TI_STATE.DISCOVER, TI_STATE.OFF, TI_STATE.DRIVER_OVER))
  def test_non_run_states_block(self, state):
    cs = TiCarState()
    cs.update_gate(ti_feedback(TI_STATE.RUN))
    assert not cs.update_gate(ti_feedback(state))

  def test_ramp_down_blocks(self):
    cs = TiCarState()
    assert cs.update_gate(ti_feedback(TI_STATE.RUN))
    assert not cs.update_gate(ti_feedback(TI_STATE.RUN, ramp_down=1))

  def test_fallback_only_without_any_feedback(self):
    cs = TiCarState()
    for _ in range(TI_DISCOVERY_FRAMES - 1):
      assert not cs.update_gate(None)
    assert cs.update_gate(None)
    # Feedback arriving later takes over from the fallback.
    assert not cs.update_gate(ti_feedback(TI_STATE.OFF))

  def test_no_reopen_after_dropout(self):
    cs = TiCarState()
    assert cs.update_gate(ti_feedback(TI_STATE.RUN))
    for _ in range(TI_FEEDBACK_TIMEOUT_FRAMES):
      assert cs.update_gate(None)
    for _ in range(TI_DISCOVERY_FRAMES * 2):
      assert not cs.update_gate(None)
    assert cs.update_gate(ti_feedback(TI_STATE.RUN))


class TestDriverTorque:
  def test_ti_sensor_replaces_stock(self):
    cs = TiCarState()
    assert cs.update_driver_torque(ti_feedback(TI_STATE.RUN, torque=10), 64, 30) == (10, False)
    assert cs.update_driver_torque(ti_feedback(TI_STATE.RUN, torque=-16), 64, 30) == (-16, True)

  def test_short_gap_holds_last_ti_reading(self):
    # The stock EPS sensor sees the TI's own torque; a gap must not read it as the driver.
    cs = TiCarState()
    cs.update_driver_torque(ti_feedback(TI_STATE.RUN, torque=3), 0, 30)
    cs.update_gate(ti_feedback(TI_STATE.RUN))
    for _ in range(TI_FEEDBACK_TIMEOUT_FRAMES):
      assert cs.update_driver_torque(None, 64, 30) == (3, False)
      cs.update_gate(None)
    assert cs.update_driver_torque(None, 64, 30) == (64, True)

  def test_stock_sensor_before_any_feedback(self):
    assert TiCarState().update_driver_torque(None, 31, 30) == (31, True)


class TestLimits:
  def test_rate_limit_both_directions(self):
    assert apply_ti_steer_torque_limits(599, 0, 0, TI_LIMITS) == 15
    assert apply_ti_steer_torque_limits(599, 300, 0, TI_LIMITS) == 315
    assert apply_ti_steer_torque_limits(-599, 300, 0, TI_LIMITS) == 285
    assert apply_ti_steer_torque_limits(-599, -300, 0, TI_LIMITS) == -315

  def test_cap(self):
    assert apply_ti_steer_torque_limits(2000, 595, 0, TI_LIMITS) == 599
    assert apply_ti_steer_torque_limits(-2000, -595, 0, TI_LIMITS) == -599

  def test_driver_opposing_clamps_toward_zero(self):
    # driver pushes left 20 TI counts: right torque allowed = 599 + (5 - 20) * 40 = -1 -> 0
    assert apply_ti_steer_torque_limits(300, 0, -20, TI_LIMITS) == 0
    # with the driver: no extra limit beyond the cap/rate
    assert apply_ti_steer_torque_limits(300, 0, 20, TI_LIMITS) == 15


@pytest.fixture
def ti_car():
  cp = params()
  ci = CarInterface(cp)
  ci.update([])
  return ci, CANPacker(DBC[cp.carFingerprint][Bus.pt])


def run_frame(ci, packer, frame, feedback, torque=0.5, lat_active=True):
  msgs = []
  if feedback is not None:
    addr, dat, bus = packer.make_can_msg("TI_FEEDBACK", 0, feedback)
    msgs.append(CanData(addr, dat, bus))
  ci.update([(frame * DT_NS, msgs)])
  cc = structs.CarControl()
  cc.enabled = cc.latActive = lat_active
  cc.actuators.torque = torque
  actuators, sends = ci.apply(cc.as_reader(), frame * DT_NS)
  ti = [dat for addr, dat, bus in sends if addr == TI_STEERING_CONTROL]
  assert len(ti) == 1, "TI frame must be sent every frame"
  assert [bus for addr, dat, bus in sends if addr == TI_STEERING_CONTROL] == [0]
  dat = ti[0]
  request = ((dat[0] & 0x0F) << 8 | dat[1]) - 2048
  e4 = [dat for addr, dat, bus in sends if addr == 0xE4]
  return request, dat, actuators, e4


class TestController:
  def test_zero_torque_handshake_then_ramp(self, ti_car):
    ci, packer = ti_car
    frame = 0
    for _ in range(1571):
      request, dat, _, _ = run_frame(ci, packer, frame, ti_feedback(TI_STATE.OFF, viol=23))
      assert request == 0 and len(dat) == 8
      frame += 1
    for _ in range(200):
      assert run_frame(ci, packer, frame, ti_feedback(TI_STATE.OFF))[0] == 0
      frame += 1
    requests = [run_frame(ci, packer, frame + i, ti_feedback(TI_STATE.RUN))[0] for i in range(5)]
    assert requests == [TI_LIMITS.TI_STEER_DELTA_UP * (i + 1) for i in range(5)]

  def test_zero_request_wire_format(self, ti_car):
    ci, packer = ti_car
    _, dat, _, _ = run_frame(ci, packer, 0, ti_feedback(TI_STATE.OFF))
    # LKAS_REQUEST and CHKSUM are 12-bit with a +2048 offset: neutral is 0x800.
    assert dat[0] & 0x0F == 0x8 and dat[1] == 0x00
    assert dat[2] == 0x08 and dat[3] == 0x00
    assert dat[4:8] == bytes((0xC4, 0x61, 0xCE, 0x60))

  def test_lat_inactive_sends_neutral(self, ti_car):
    ci, packer = ti_car
    for frame in range(10):
      request, _, _, _ = run_frame(ci, packer, frame, ti_feedback(TI_STATE.RUN), lat_active=False)
      assert request == 0

  def test_dropout_zeroes_torque(self, ti_car):
    ci, packer = ti_car
    for frame in range(10):
      request, _, _, _ = run_frame(ci, packer, frame, ti_feedback(TI_STATE.RUN))
    assert request != 0
    for frame in range(10, 10 + TI_FEEDBACK_TIMEOUT_FRAMES + 1):
      request, _, _, _ = run_frame(ci, packer, frame, None)
    assert request == 0
    for frame in range(100, 100 + TI_DISCOVERY_FRAMES + 10):
      assert run_frame(ci, packer, frame, None)[0] == 0

  def test_feedbackless_fallback(self, ti_car):
    ci, packer = ti_car
    # the fixture's initial update is the first silent carState frame
    for frame in range(TI_DISCOVERY_FRAMES - 2):
      assert run_frame(ci, packer, frame, None)[0] == 0
    assert run_frame(ci, packer, TI_DISCOVERY_FRAMES, None)[0] == TI_LIMITS.TI_STEER_DELTA_UP

  def test_car_output_reports_the_ti_command(self, ti_car):
    ci, packer = ti_car
    for frame in range(4):
      request, _, actuators, e4 = run_frame(ci, packer, frame, ti_feedback(TI_STATE.RUN))
      assert actuators.torqueOutputCan == request
      assert math.isclose(actuators.torque, request / TI_LIMITS.TI_STEER_MAX, rel_tol=1e-6)  # float32 field
      # 0xE4 still goes out (request bit follows latActive) but never carries torque
      parser = CANParser(DBC[CAR.HONDA_ACCORD_9G][Bus.pt], [("STEERING_CONTROL", math.nan)], 0)
      parser.update([(frame * DT_NS, [CanData(0xE4, e4[0], 0)])])
      assert parser.vl["STEERING_CONTROL"]["STEER_TORQUE"] == 0
      assert parser.vl["STEERING_CONTROL"]["STEER_TORQUE_REQUEST"] == 1

  def test_steering_pressed_from_ti_sensor(self, ti_car):
    ci, packer = ti_car
    run_frame(ci, packer, 0, ti_feedback(TI_STATE.RUN, torque=40))
    assert ci.CS.out.steeringPressed and ci.CS.out.steeringTorque == 40
    run_frame(ci, packer, 1, ti_feedback(TI_STATE.RUN, torque=5))
    assert not ci.CS.out.steeringPressed


def test_stock_9g_without_ti_is_unchanged():
  cp = params(ti=False)
  ci = CarInterface(cp)
  ci.update([])
  cc = structs.CarControl()
  cc.enabled = cc.latActive = True
  cc.actuators.torque = 0.5
  _, sends = ci.apply(cc.as_reader(), 0)
  assert TI_STEERING_CONTROL not in [addr for addr, dat, bus in sends]
