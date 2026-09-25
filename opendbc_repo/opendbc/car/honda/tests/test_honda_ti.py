"""Honda 9G Accord Torque Interceptor (TI) discovery handshake.

Replays the board-state sequence measured in the last working rlog
(2026-09-11, segment 00000284--5800249712--75): 1571 frames OFF with VIOL=23,
200 frames OFF with VIOL=0, then RUN. The board only leaves OFF after a run of
zero-torque TI_STEERING_CONTROL frames, so torque must stay zero on the wire
until it reports RUN, and the frame must keep being sent while the gate is closed.
"""
import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus, structs
from opendbc.car.can_definitions import CanData
from opendbc.car.car_helpers import interfaces
from opendbc.car.honda import carcontroller, carstate, interface
from opendbc.car.honda.values import CAR, DBC, TI_DISCOVERY_FRAMES, TI_FEEDBACK_TIMEOUT_FRAMES, TI_LIMITS, TI_STATE
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
