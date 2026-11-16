"""9G Accord SSV3 developer EPS torque-blend probe (opendbc/car/honda/ssv3.py Ssv3BlendProbe).

Every abort condition, the start conditions, the command limits and window timing, through the real CarInterface
(CAN in -> 0xE4 out), and the TI path / other Hondas never reaching the probe.
"""
import math

import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.honda import ssv3
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import (PROBE_ABORT_ANGLE_DEG, PROBE_ABORT_YAW, PROBE_MAX_COUNTS, PROBE_PROGRAMS, PROBE_V_MAX,
                                    PROBE_V_MIN, ProbeEnd, ProbeInputs, ProbeState, Ssv3BlendProbe, probe_abort_reason,
                                    probe_start_ok)
from opendbc.car.honda.tests.test_ssv3 import ACCORD_DBC, fw3_400, fw3_427, ss_status
from opendbc.car.honda.tests.test_ssv3_tune import Board, params
from opendbc.car.honda.values import CAR, DBC, HondaFlags

HOLD = 1000    # frames (10 s)
REST = 500     # frames (5 s)
SETTLE = 200   # frames (2 s)


def good(**kw):
  base = dict(lat_active=True, cancel=False, v_ego=20 * ssv3.MPH, angle_deg=0.0, yaw=0.0, brake=False, gas=False,
              steer_fault=False, steer_status=0, fw3=True)
  base.update(kw)
  return ProbeInputs(**base)


# ---- limits and the program table ----

def test_program_table_limits():
  assert PROBE_MAX_COUNTS == 240
  for prog, windows in PROBE_PROGRAMS.items():
    assert prog > 0 and windows
    assert all(0 < abs(c) <= PROBE_MAX_COUNTS for c in windows), prog
    total = len(windows) * ssv3.PROBE_HOLD_S + (len(windows) - 1) * ssv3.PROBE_REST_S
    assert total <= ssv3.PROBE_TOTAL_S, prog
  assert ssv3.PROBE_HOLD_S <= 10.0 and ssv3.PROBE_REST_S >= 5.0 and ssv3.PROBE_TOTAL_S <= 90.0
  assert PROBE_PROGRAMS[1] == (60, -60, 120)
  assert PROBE_PROGRAMS[7] == (120, -120, 180, -180, 240)
  assert ssv3.PROBE_V_MIN == 10 * ssv3.MPH and ssv3.PROBE_V_MAX == 52 * ssv3.MPH
  assert ssv3.PROBE_START_V_MIN == 11 * ssv3.MPH and ssv3.PROBE_START_V_MAX == 50 * ssv3.MPH


# ---- the state machine on its own ----

@pytest.mark.parametrize("change,end", (
  (dict(lat_active=False), ProbeEnd.LAT_INACTIVE),
  (dict(brake=True), ProbeEnd.BRAKE),
  (dict(gas=True), ProbeEnd.GAS),
  (dict(cancel=True), ProbeEnd.CANCEL),
  (dict(v_ego=PROBE_V_MIN - 0.01), ProbeEnd.SPEED),
  (dict(v_ego=PROBE_V_MAX + 0.01), ProbeEnd.SPEED),
  (dict(v_ego=math.nan), ProbeEnd.SPEED),
  (dict(angle_deg=PROBE_ABORT_ANGLE_DEG + 0.1), ProbeEnd.ANGLE),
  (dict(angle_deg=-PROBE_ABORT_ANGLE_DEG - 0.1), ProbeEnd.ANGLE),
  (dict(angle_deg=math.nan), ProbeEnd.ANGLE),
  (dict(yaw=PROBE_ABORT_YAW + 0.001), ProbeEnd.YAW),
  (dict(yaw=-PROBE_ABORT_YAW - 0.001), ProbeEnd.YAW),
  (dict(yaw=math.nan), ProbeEnd.YAW),
  (dict(v_ego=45 * ssv3.MPH, yaw=0.08), ProbeEnd.YAW),        # 0.08 * 20.1 m/s = 1.61 m/s^2
  (dict(v_ego=45 * ssv3.MPH, yaw=-0.08), ProbeEnd.YAW),
  (dict(steer_fault=True), ProbeEnd.EPS_FAULT),
  (dict(steer_status=3), ProbeEnd.EPS_FAULT),
  (dict(steer_status=4), ProbeEnd.EPS_FAULT),
  (dict(steer_status=-1), ProbeEnd.EPS_FAULT),
  (dict(fw3=False), ProbeEnd.BOARD_LOST),
))
@pytest.mark.parametrize("phase", ("hold", "rest"))
def test_each_abort_ends_the_probe_at_once(change, end, phase):
  assert probe_abort_reason(good(**change)) == end
  p = Ssv3BlendProbe()
  for _ in range(SETTLE - 1):
    assert p.update(1, good(), 240) is None
  frames = 50 if phase == "hold" else HOLD + 50
  for _ in range(frames):
    p.update(1, good(), 240)
  assert p.state == (ProbeState.HOLD if phase == "hold" else ProbeState.REST)
  assert p.update(1, good(**change), 240) is None       # same frame: normal control
  assert p.state == ProbeState.DONE and p.end == end and p.finished and p.command == 0
  # stays off while the param still reads non-zero, even when everything is fine again
  for _ in range(3 * SETTLE):
    assert p.update(1, good(), 240) is None
  assert p.state == ProbeState.DONE
  # param cleared -> idle; only a fresh non-zero arms it again
  assert p.update(0, good(), 240) is None and p.state == ProbeState.IDLE


def test_param_back_to_zero_while_running_stops_it():
  p = Ssv3BlendProbe()
  for _ in range(SETTLE + 10):
    p.update(1, good(), 240)
  assert p.state == ProbeState.HOLD
  assert p.update(0, good(), 240) is None
  assert p.end == ProbeEnd.STOPPED and p.finished


def test_total_time_limit(monkeypatch):
  monkeypatch.setitem(PROBE_PROGRAMS, 99, (60,) * 8)   # 115 s if nothing stopped it
  p = Ssv3BlendProbe()
  for _ in range(SETTLE):
    p.update(99, good(), 240)
  n = 0
  while p.state != ProbeState.DONE:
    p.update(99, good(), 240)
    n += 1
    assert n < 10000
  assert p.end == ProbeEnd.TIME_LIMIT
  assert n == 9000            # 90 s of running frames (the first one was the settle frame), the next aborts


def test_unknown_program_and_arm_timeout():
  p = Ssv3BlendProbe()
  assert p.update(42, good(), 240) is None
  assert p.end == ProbeEnd.BAD_PROGRAM and p.finished
  p = Ssv3BlendProbe()
  for _ in range(12000 - 1):
    assert p.update(1, good(angle_deg=40.0), 240) is None    # never allowed to start
  assert p.state == ProbeState.ARMED
  p.update(1, good(angle_deg=40.0), 240)
  assert p.end == ProbeEnd.ARM_TIMEOUT and p.finished


@pytest.mark.parametrize("change", (
  dict(angle_deg=30.0), dict(angle_deg=-31.0), dict(yaw=0.05), dict(yaw=-0.06), dict(v_ego=10.9 * ssv3.MPH),
  dict(v_ego=50.1 * ssv3.MPH), dict(lat_active=False), dict(brake=True), dict(gas=True), dict(steer_status=3),
  dict(fw3=False), dict(yaw=math.nan),
))
def test_start_conditions(change):
  assert not probe_start_ok(good(**change))
  p = Ssv3BlendProbe()
  for _ in range(3 * SETTLE):
    assert p.update(1, good(**change), 240) is None
  assert p.state == ProbeState.ARMED


def test_armed_waits_for_a_full_settle_and_does_not_abort_on_pedals():
  p = Ssv3BlendProbe()
  for i in range(SETTLE - 1):
    assert p.update(1, good(), 240) is None
  # a brake press while only armed is not an abort (nothing is being commanded); it restarts the settle timer
  assert p.update(1, good(brake=True), 240) is None and p.state == ProbeState.ARMED
  for i in range(SETTLE - 1):
    assert p.update(1, good(), 240) is None
  assert p.update(1, good(), 240) == pytest.approx(-60 / 240)
  assert p.state == ProbeState.HOLD


def test_window_timing_and_values():
  p = Ssv3BlendProbe()
  for _ in range(SETTLE - 1):
    p.update(1, good(), 240)
  out = [p.update(1, good(), 240) for _ in range(3 * HOLD + 2 * REST + 5)]
  expect = [-60 / 240] * HOLD + [None] * REST + [60 / 240] * HOLD + [None] * REST + [-120 / 240] * HOLD + [None] * 5
  assert out == expect
  assert p.end == ProbeEnd.COMPLETED


def test_command_magnitude_clamped(monkeypatch):
  monkeypatch.setitem(PROBE_PROGRAMS, 98, (500, -2000))
  p = Ssv3BlendProbe()
  out = [p.update(98, good(), 240) for _ in range(SETTLE + 2 * HOLD + REST)]
  vals = {round(-v * 240) for v in out if v is not None}
  assert vals == {240, -240}


# ---- through the real CarInterface ----

def pt_frames(cp, packer, tick, *, kph=30.0, angle=0.0, brake=False, gas=False):
  from opendbc.can import CANDefine
  gear_name = "GEARBOX_CVT" if cp.transmissionType == structs.CarParams.TransmissionType.cvt else "GEARBOX_AUTO"
  gears = CANDefine(DBC[cp.carFingerprint][Bus.pt]).dv[gear_name]["GEAR_SHIFTER"]
  drive = next(value for value, label in gears.items() if label == "D")
  sources = {
    "ENGINE_DATA": {"XMISSION_SPEED": kph},
    "WHEEL_SPEEDS": {"WHEEL_SPEED_FL": kph, "WHEEL_SPEED_FR": kph, "WHEEL_SPEED_RL": kph, "WHEEL_SPEED_RR": kph},
    "SCM_BUTTONS": {"CRUISE_BUTTONS": 0, "CRUISE_SETTING": 0, "MAIN_ON": 1},
    "SCM_FEEDBACK": {},
    "CAR_SPEED": {},
    "SEATBELT_STATUS": {"SEATBELT_DRIVER_LATCHED": 1},
    "STEERING_SENSORS": {"STEER_ANGLE": angle},
    "VSA_STATUS": {},
    "POWERTRAIN_DATA": {"ACC_STATUS": 0, "PEDAL_GAS": 0.5 if gas else 0, "BRAKE_PRESSED": int(brake),
                        "BRAKE_SWITCH": int(brake)},
    "CRUISE": {},
    gear_name: {"GEAR_SHIFTER": drive},
    "STANDSTILL": {},
    "DOORS_STATUS": {},
  }
  frames = [packer.make_can_msg(name, 0, fields) for name, fields in sources.items()]
  frames += [packer.make_can_msg(name, 2, {}) for name in ("BRAKE_COMMAND", "ACC_HUD", "LKAS_HUD")]
  return frames


class Car:
  def __init__(self, ti=False):
    self.ci = CarInterface(params(pedal=False, ti=ti))
    self.packer = CANPacker(ACCORD_DBC)
    self.board = Board()
    self.tick = 0

  def step(self, *, torque=0.05, lat=True, cancel=False, cc_cancel=False, yaw=0.0, eps_status=0, send_520=True, program=None, **pt):
    t = 1_000_000_000 + self.tick * 10_000_000
    frames = pt_frames(self.ci.CP, self.packer, self.tick, **pt)
    frames += [(400, fw3_400(self.tick, lkas_ack=True, eps_status=eps_status), 0), (427, fw3_427(self.tick, 0), 0)]
    if send_520 and self.tick % 10 == 0:
      frames.append((520, ss_status(self.tick // 10, 3), 0))
    cs = self.ci.update([(t, frames)])
    if program is not None and self.ci.CC.ssv3 is not None:
      self.ci.CC.ssv3.requested_probe = program
    if cancel:   # driver CANCEL button press
      cs.buttonEvents = [structs.CarState.ButtonEvent(type=structs.CarState.ButtonEvent.Type.cancel, pressed=True)]
    cc = structs.CarControl(latActive=lat, enabled=lat)
    cc.actuators.torque = torque
    cc.cruiseControl.cancel = cc_cancel
    cc.angularVelocity = [0.0, 0.0, yaw] if yaw is not None else []
    _, sends = self.ci.apply(cc.as_reader(), t)
    self.tick += 1
    e4 = [f for f in sends if f[0] == 0xE4]
    assert len(e4) == 1
    dat = e4[0][1]
    return cs, int.from_bytes(dat[0:2], "big", signed=True), dat

  @property
  def probe(self):
    return self.ci.CC.ssv3.probe


def warmed(**kw):
  car = Car(**kw)
  for _ in range(100):       # fw3 confirmed, vEgo settled
    car.step()
  assert car.ci.CC.ssv3.probe.state == ProbeState.IDLE
  return car


def into_hold(car, frames=200):
  for _ in range(SETTLE):
    car.step(program=1)
  out = [car.step(program=1)[1] for _ in range(frames)]
  assert car.probe.state == ProbeState.HOLD
  return out


def test_full_program_through_carinterface():
  car = warmed()
  normal = car.step()[1]
  assert normal == -12          # 0.05 * 240, wire sign
  armed = [car.step(program=1)[1] for _ in range(SETTLE - 1)]
  assert set(armed) == {-12}    # armed: normal control
  wire = [car.step(program=1)[1] for _ in range(3 * HOLD + 2 * REST + 50)]
  assert car.probe.end == ProbeEnd.COMPLETED
  # rate limit (STEER_DELTA 3/s = 0.03/frame = 7.2 counts) on every step, including in and out of the windows
  seq = [normal] + armed + wire
  assert max(abs(b - a) for a, b in zip(seq, seq[1:])) <= 8
  # holds: the exact counts once ramped; rests: back to normal control
  assert set(wire[100:HOLD]) == {60}
  assert set(wire[HOLD + 100:HOLD + REST]) == {-12}
  assert set(wire[HOLD + REST + 100:2 * HOLD + REST]) == {-60}
  assert set(wire[2 * HOLD + 2 * REST + 100:3 * HOLD + 2 * REST]) == {120}
  assert set(wire[-30:]) == {-12}
  assert max(abs(w) for w in wire) <= PROBE_MAX_COUNTS
  # request bit always on, no option bits added by the probe
  _, _, dat = car.step(program=1)
  assert dat[2] & 0x80 and dat[2] & 0x0F == 0


ABORTS = (
  ("lat", dict(lat=False), ProbeEnd.LAT_INACTIVE),
  ("brake", dict(brake=True), ProbeEnd.BRAKE),
  ("gas", dict(gas=True), ProbeEnd.GAS),
  ("cancel", dict(cancel=True), ProbeEnd.CANCEL),
  ("slow", dict(kph=12.0), ProbeEnd.SPEED),
  ("fast", dict(kph=86.0), ProbeEnd.SPEED),
  ("angle", dict(angle=50.0), ProbeEnd.ANGLE),
  ("angle_neg", dict(angle=-50.0), ProbeEnd.ANGLE),
  ("yaw", dict(yaw=0.3), ProbeEnd.YAW),
  ("lat_accel", dict(kph=72.0, yaw=0.08), ProbeEnd.YAW),
  ("yaw_missing", dict(yaw=None), ProbeEnd.YAW),
  ("eps_lockout", dict(eps_status=3), ProbeEnd.EPS_FAULT),
  ("eps_tmp_fault", dict(eps_status=6), ProbeEnd.EPS_FAULT),
)


@pytest.mark.parametrize("name,change,end", ABORTS, ids=[a[0] for a in ABORTS])
def test_every_abort_through_carinterface(name, change, end):
  car = warmed()
  hold = into_hold(car)
  assert hold[-1] == 60
  frames = []
  for i in range(150):
    frames.append(car.step(program=1, **change)[1])
    if car.probe.state == ProbeState.DONE:
      break
  assert car.probe.end == end, (car.probe.end, name)
  # pedals/cancel/lat/yaw/angle/status act on the very frame; speed waits for vEgo to cross the band
  assert len(frames) <= (60 if name in ("slow", "fast") else 1)
  # from the aborting frame on: normal control, rate limited down from the hold value
  tail = [car.step(program=1, **change)[1] for _ in range(40)]
  if change.get("lat") is False:
    assert set(tail) == {0}
  else:
    seq = [hold[-1]] + frames + tail
    assert max(abs(b - a) for a, b in zip(seq, seq[1:])) <= 8
    assert tail[-1] == -12
  assert car.probe.state == ProbeState.DONE


def test_openpilot_cruise_cancel_command_does_not_abort():
  # always-on-lateral: controlsd asserts CC.cruiseControl.cancel continuously while latActive stays True
  car = warmed()
  into_hold(car)
  for _ in range(300):
    car.step(program=1, cc_cancel=True)
  assert car.probe.state in (ProbeState.HOLD, ProbeState.REST) and car.probe.end == ProbeEnd.NONE


def test_driver_cancel_button_aborts():
  car = warmed()
  into_hold(car)
  car.step(program=1, cancel=True)
  assert car.probe.end == ProbeEnd.CANCEL


def test_board_lost_through_carinterface():
  car = warmed()
  into_hold(car)
  for _ in range(80):
    car.step(program=1, send_520=False)
    if car.probe.state == ProbeState.DONE:
      break
  assert car.probe.end == ProbeEnd.BOARD_LOST


def test_probe_off_by_default_bytes_identical():
  # requested_probe 0 (the default): the probe is never consulted and the 0xE4 stream is what it was before
  a, b = warmed(), warmed()
  b.ci.CC.ssv3.probe.update = None   # would raise if called
  for i in range(300):
    torque = 0.3 * math.sin(i / 20)
    assert a.step(torque=torque)[2] == b.step(torque=torque)[2]


def test_ti_path_never_reaches_the_probe(monkeypatch):
  def boom(*_a, **_k):
    raise AssertionError("probe consulted on the TI path")
  monkeypatch.setattr(ProbeInputs, "from_car", classmethod(lambda cls, *a: boom()))
  monkeypatch.setattr(Ssv3BlendProbe, "update", boom)
  car = Car(ti=True)
  assert car.ci.CC.ssv3 is None and car.ci.CC.ti is not None
  for i in range(400):
    _, torque, dat = car.step(torque=0.3, program=1)
    assert torque == 0 and dat[2] & 0x0F == 0       # TI: 0xE4 carries zero torque, no option bits


@pytest.mark.parametrize("identity", (CAR.HONDA_CIVIC, CAR.HONDA_ACCORD, CAR.ACURA_MDX_3G, CAR.HONDA_CRV_5G))
def test_other_hondas_have_no_probe(identity):
  ci = CarInterface(CarInterface.get_params(identity, gen_empty_fingerprint(), [], False, False, False))
  assert ci.CC.ssv3 is None


def test_9g_pedal_flag_irrelevant():
  car = Car()
  assert not car.ci.CP.flags & HondaFlags.BOSCH
  assert car.ci.CC.ssv3 is not None and car.ci.CC.ssv3.requested_probe == 0


# ---- program 7: highway band, up to the full 240 range ----

def test_program_7_state_machine():
  p = Ssv3BlendProbe()
  for _ in range(SETTLE - 1):
    p.update(7, good(v_ego=45 * ssv3.MPH), 240)
  out = [p.update(7, good(v_ego=45 * ssv3.MPH), 240) for _ in range(5 * HOLD + 4 * REST + 5)]
  expect = []
  for c in (120, -120, 180, -180, 240):
    expect += [-c / 240] * HOLD + [None] * REST
  expect = expect[:-REST] + [None] * 5
  assert out == expect
  assert p.end == ProbeEnd.COMPLETED
  assert (5 * 10 + 4 * 5) < ssv3.PROBE_TOTAL_S


def test_program_7_through_carinterface_at_45_mph():
  car = warmed()
  for _ in range(150):                     # bring vEgo to 45 mph (72.4 kph)
    car.step(kph=72.4)
  armed = [car.step(program=7, kph=72.4)[1] for _ in range(SETTLE - 1)]
  wire = [car.step(program=7, kph=72.4)[1] for _ in range(5 * HOLD + 4 * REST + 50)]
  assert car.probe.end == ProbeEnd.COMPLETED, car.probe.end
  seq = armed + wire
  assert max(abs(b - a) for a, b in zip(seq, seq[1:])) <= 8        # STEER_DELTA unchanged
  for k, c in enumerate((120, -120, 180, -180, 240)):
    start = k * (HOLD + REST)
    assert set(wire[start + 100 + 40:start + HOLD]) == {c}, (k, c)
  assert max(abs(w) for w in wire) == 240


def test_lat_accel_abort_is_speed_aware():
  # same yaw rate: fine at 20 mph, over the limit at 45 mph
  assert probe_abort_reason(good(v_ego=20 * ssv3.MPH, yaw=0.15)) == ProbeEnd.NONE
  assert probe_abort_reason(good(v_ego=45 * ssv3.MPH, yaw=0.15)) == ProbeEnd.YAW
  assert probe_abort_reason(good(v_ego=45 * ssv3.MPH, yaw=0.07)) == ProbeEnd.NONE
  assert probe_abort_reason(good(v_ego=11 * ssv3.MPH, yaw=0.26)) == ProbeEnd.YAW     # absolute ceiling
