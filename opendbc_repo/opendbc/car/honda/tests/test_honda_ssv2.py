"""Honda 9G Accord with the Serial Steering V2 (SSV2) board."""
from collections import defaultdict
from types import SimpleNamespace

import pytest

from opendbc.can import CANPacker, CANParser
from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.honda.carcontroller import CarController
from opendbc.car.honda.hondacan import CanBus
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.serial_steering import apply_ssv2_steer_torque_limits
from opendbc.car.honda.values import CAR, DBC, SSV2_DBC, SSV2_LIMITS, HondaFlags, get_pt_dbc

STEER_STATUS = 0x190
STEERING_CONTROL = 0xE4
LKAS_HUD = 0x33D


def get_test_toggles() -> SimpleNamespace:
  return SimpleNamespace(always_on_lateral_lkas=False, force_torque_controller=False, nnff=False, nnff_lite=False)


def ssv2_fingerprint(steer_status_len=4, bus=2):
  fingerprint = gen_empty_fingerprint()
  for b in (0, 2):
    fingerprint[b].update({0x158: 8, 0x17C: 8, 0x1A6: 8, 0x201: 6})  # pedal interceptor car
  fingerprint[bus][STEER_STATUS] = steer_status_len
  return fingerprint


def get_cp(fingerprint=None):
  return CarInterface.get_params(CAR.HONDA_ACCORD_9G, fingerprint or ssv2_fingerprint(), [], False, False, False, get_test_toggles())


def honda_checksum(addr: int, dat: bytes) -> int:
  s = 0
  a = addr
  while a > 0:
    s += a & 0xF
    a >>= 4
  for i, b in enumerate(dat):
    if i == len(dat) - 1:
      b &= 0xF0
    s += (b >> 4) + (b & 0xF)
  return (8 - s) & 0xF


class TestSSV2Platform:
  @pytest.mark.parametrize("steer_status_len", [4, 5, None])
  def test_9g_is_always_ssv2(self, steer_status_len):
    # the fingerprint can't tell the boards apart (both 0x190 streams share a wire while fingerprinting)
    fingerprint = ssv2_fingerprint(steer_status_len or 4)
    if steer_status_len is None:
      del fingerprint[2][STEER_STATUS]
    CP = get_cp(fingerprint)
    assert CP.flags & HondaFlags.SERIAL_STEERING_V2
    assert get_pt_dbc(CP) == SSV2_DBC

  def test_other_hondas_never_ssv2(self):
    for car in (CAR.HONDA_CIVIC, CAR.ACURA_MDX_3G, CAR.HONDA_ODYSSEY, CAR.HONDA_ACCORD):
      CP = CarInterface.get_params(car, ssv2_fingerprint(), [], False, False, False, get_test_toggles())
      assert not CP.flags & HondaFlags.SERIAL_STEERING_V2, car
      assert get_pt_dbc(CP) == DBC[car][Bus.pt]
      assert CanBus(CP).steer == CanBus(CP).lkas


class TestSSV2Params:
  def test_tune(self):
    CP = get_cp()
    assert CP.lateralTuning.which() == "pid"
    assert list(CP.lateralParams.torqueBP) == [0, SSV2_LIMITS.STEER_MAX]
    assert list(CP.lateralParams.torqueV) == [0, SSV2_LIMITS.STEER_MAX]
    assert list(CP.lateralTuning.pid.kpV) == pytest.approx([0.4, 0.3])
    assert list(CP.lateralTuning.pid.kiV) == pytest.approx([0., 0.])
    assert CP.steerActuatorDelay == pytest.approx(0.3)

  def test_safety_params(self):
    # SSV2 adds no safety param: the bus 2 steering rule is part of every Nidec config.
    # 36 = NIDEC_ALT | GAS_INTERCEPTOR, as on the pedal 9G today.
    CP = get_cp()
    assert CP.safetyConfigs[0].safetyParam == 36
    assert CP.enableGasInterceptorDEPRECATED

  def test_buses(self):
    CAN = CanBus(get_cp())
    assert CAN.steer == CAN.camera == 2
    assert CAN.lkas == CAN.pt == 0  # LKAS_HUD stays on the car side


class TestSSV2Limits:
  L = SSV2_LIMITS

  def test_rate_up_and_down(self):
    assert apply_ssv2_steer_torque_limits(239, 0, 0, self.L) == self.L.STEER_DELTA_UP
    assert apply_ssv2_steer_torque_limits(-239, 0, 0, self.L) == -self.L.STEER_DELTA_UP
    assert apply_ssv2_steer_torque_limits(0, 200, 0, self.L) == 200 - self.L.STEER_DELTA_DOWN
    assert apply_ssv2_steer_torque_limits(0, -200, 0, self.L) == -200 + self.L.STEER_DELTA_DOWN
    # crossing zero is limited to DELTA_UP on the far side
    assert apply_ssv2_steer_torque_limits(-239, 3, 0, self.L) == -self.L.STEER_DELTA_UP

  def test_max(self):
    last = 0
    for _ in range(200):
      last = apply_ssv2_steer_torque_limits(1000, last, 0, self.L)
    assert last == self.L.STEER_MAX

  @pytest.mark.parametrize("driver", [0, 10, 25, 30, 35, 38, 40, 100, 256])
  def test_driver_window_is_symmetric(self, driver):
    # the window shrinks the same way for driver torque in either direction, and for either command sign
    results = {apply_ssv2_steer_torque_limits(cmd * 239, cmd * 239, sgn * driver, self.L) * cmd
               for cmd in (1, -1) for sgn in (1, -1)}
    assert len(results) == 1
    allowed = results.pop()
    expected = max(0, min(self.L.STEER_MAX, self.L.STEER_MAX - (driver - self.L.STEER_DRIVER_ALLOWANCE) * self.L.STEER_DRIVER_MULTIPLIER))
    # starting at the max, one frame can only drop by DELTA_DOWN
    assert allowed == max(expected, self.L.STEER_MAX - self.L.STEER_DELTA_DOWN)

  def test_driver_torque_fades_to_zero(self):
    last = 239
    for _ in range(100):
      last = apply_ssv2_steer_torque_limits(239, last, 40, self.L)
    assert last == 0


def make_cs(steering_torque=0.0, v_ego=20.0):
  return SimpleNamespace(
    out=SimpleNamespace(vEgo=v_ego, aEgo=0.0, steeringPressed=False, gasPressed=False, brakePressed=False,
                        steeringTorque=steering_torque, cruiseState=SimpleNamespace(available=True)),
    v_cruise_factor=1.0, acc_hud=defaultdict(int), lkas_hud=False, stock_brake=defaultdict(int), is_metric=False,
    dash_speed_seen=False,
  )


def make_cc(torque, lat_active=True):
  CC = structs.CarControl.new_message()
  CC.enabled = lat_active
  CC.latActive = lat_active
  CC.longActive = False
  CC.hudControl.visualAlert = structs.CarControl.HUDControl.VisualAlert.none
  CC.actuators.torque = torque
  return CC.as_reader()


class TestSSV2Controller:
  @pytest.fixture
  def controller(self, monkeypatch):
    class FakeParams:
      def get_float(self, key, default=0.0):
        return default

      def get_bool(self, key, default=False):
        return default

      def get(self, key, default=None):
        return default

    monkeypatch.setattr("opendbc.car.honda.carcontroller.Params", lambda: FakeParams())
    CP = get_cp()
    # the CarInterface hands the controller the DBC of its parsers, which is the SSV2 DBC
    dbc_names = {Bus.pt: get_pt_dbc(CP), Bus.radar: DBC[CP.carFingerprint][Bus.radar]}
    return CarController(dbc_names, CP)

  def _steer(self, controller, CC, CS):
    _, can_sends = controller.update(CC, CS, 0, get_test_toggles())
    steer = [m for m in can_sends if m[0] == STEERING_CONTROL]
    assert len(steer) == 1, steer
    return steer[0], can_sends

  def _decode(self, frame):
    addr, dat, bus = frame
    torque = int.from_bytes(dat[0:2], "big", signed=True)
    request = bool(dat[2] & 0x80)
    return bus, torque, request, (dat[4] >> 4) & 0x3

  def test_bus_sign_and_ramp(self, controller):
    torques = []
    for _ in range(60):
      frame, _ = self._steer(controller, make_cc(1.0), make_cs())
      bus, torque, request, _ = self._decode(frame)
      assert bus == 2
      assert request
      torques.append(torque)
    # positive (left) openpilot torque is negative on CAN, ramped by DELTA_UP to the max
    assert torques[0] == -SSV2_LIMITS.STEER_DELTA_UP
    assert all(b - a == -SSV2_LIMITS.STEER_DELTA_UP for a, b in zip(torques, torques[1:], strict=False) if b > -SSV2_LIMITS.STEER_MAX)
    assert torques[-1] == -SSV2_LIMITS.STEER_MAX

  def test_checksum_and_counter(self, controller):
    counters = []
    for _ in range(8):
      frame, _ = self._steer(controller, make_cc(0.5), make_cs())
      addr, dat, _ = frame
      assert len(dat) == 5
      assert dat[-1] & 0xF == honda_checksum(addr, dat)
      counters.append(self._decode(frame)[3])
    assert all((b - a) % 4 == 1 for a, b in zip(counters, counters[1:], strict=False))

  def test_zero_torque_clears_request(self, controller):
    frame, _ = self._steer(controller, make_cc(0.0), make_cs())
    _, torque, request, _ = self._decode(frame)
    assert torque == 0 and not request

  def test_lat_inactive_resets_ramp(self, controller):
    for _ in range(60):
      self._steer(controller, make_cc(1.0), make_cs())
    frame, _ = self._steer(controller, make_cc(1.0, lat_active=False), make_cs())
    _, torque, request, _ = self._decode(frame)
    assert torque == 0 and not request
    # after a one-frame drop the board gets a fresh ramp, not a step back to the old torque
    frame, _ = self._steer(controller, make_cc(1.0), make_cs())
    assert self._decode(frame)[1] == -SSV2_LIMITS.STEER_DELTA_UP

  def test_driver_override_fades(self, controller):
    for _ in range(60):
      self._steer(controller, make_cc(1.0), make_cs())
    for _ in range(40):
      frame, _ = self._steer(controller, make_cc(1.0), make_cs(steering_torque=-60))
    assert self._decode(frame)[1] == 0

  def test_lkas_hud_stays_on_car_bus(self, controller):
    hud_buses = set()
    for _ in range(30):
      _, can_sends = self._steer(controller, make_cc(1.0), make_cs())
      hud_buses |= {m[2] for m in can_sends if m[0] == LKAS_HUD}
    assert hud_buses == {0}

  def test_reported_torque(self, controller):
    for _ in range(60):
      self._steer(controller, make_cc(1.0), make_cs())
    new_actuators, _ = controller.update(make_cc(1.0), make_cs(), 0, get_test_toggles())
    assert new_actuators.torque == pytest.approx(1.0)
    assert new_actuators.torqueOutputCan == -SSV2_LIMITS.STEER_MAX


class TestSSV2CarState:
  def _parse(self, values):
    packer = CANPacker(SSV2_DBC)
    parser = CANParser(SSV2_DBC, [("STEER_STATUS", 100)], 2)
    frames = []
    for i in range(10):
      msg = packer.make_can_msg("STEER_STATUS", 2, {**values, "COUNTER": i % 4})
      frames.append((int(i * 1e7), [msg]))
    parser.update(frames)
    return parser

  def test_layout(self):
    dbc_parser = self._parse({"STEER_TORQUE_SENSOR": -42, "STEER_STATUS": 3, "LIN_INTERFACE_FATAL_ERROR": 1})
    assert dbc_parser.can_valid
    vl = dbc_parser.vl["STEER_STATUS"]
    assert vl["STEER_TORQUE_SENSOR"] == -42
    assert vl["STEER_STATUS"] == 3
    assert vl["LIN_INTERFACE_FATAL_ERROR"] == 1

  def test_bad_checksum_rejected(self):
    packer = CANPacker(SSV2_DBC)
    parser = CANParser(SSV2_DBC, [("STEER_STATUS", 100)], 2)
    addr, dat, bus = packer.make_can_msg("STEER_STATUS", 2, {"STEER_TORQUE_SENSOR": 10, "COUNTER": 1})
    bad = bytes(dat[:-1]) + bytes([dat[-1] ^ 0x01])
    parser.update([(0, [(addr, bad, bus)])])
    assert parser.vl["STEER_STATUS"]["STEER_TORQUE_SENSOR"] == 0

  @pytest.mark.parametrize("status,fatal,temporary,permanent", [
    (0, 0, False, False),     # normal
    (3, 0, False, False),     # low speed lockout
    (4, 0, False, False),     # no torque alert 2
    (2, 0, True, False),      # no torque alert 1
    (6, 0, True, False),      # tmp fault
    (11, 0, True, False),     # EPS fail for oversteer (not in the VAL table)
    (0, 1, False, True),      # LIN interface fatal error
  ])
  def test_faults(self, status, fatal, temporary, permanent):
    CP = get_cp()
    CI = CarInterface(CP, CarInterface.get_starpilot_params(CP.carFingerprint, ssv2_fingerprint(), [], CP, get_test_toggles()))
    # the parsers register messages on first access, so run one update before feeding frames
    CI.CS.update(CI.can_parsers, get_test_toggles())
    packer = CANPacker(SSV2_DBC)
    frames = []
    for i in range(10):
      msgs = [packer.make_can_msg("STEER_STATUS", 2, {"STEER_STATUS": status, "LIN_INTERFACE_FATAL_ERROR": fatal,
                                                       "STEER_TORQUE_SENSOR": 17, "COUNTER": i % 4})]
      frames.append((int(i * 1e7), msgs))
    for cp in CI.can_parsers.values():
      cp.update(frames)
    ret, _ = CI.CS.update(CI.can_parsers, get_test_toggles())
    assert ret.steeringTorque == 17
    assert ret.steerFaultTemporary == temporary
    assert ret.steerFaultPermanent == permanent
    # the pt bus copy of STEER_STATUS is not used
    assert "STEER_STATUS" not in CI.can_parsers[Bus.pt].vl or CI.can_parsers[Bus.pt].vl["STEER_STATUS"]["STEER_TORQUE_SENSOR"] == 0
