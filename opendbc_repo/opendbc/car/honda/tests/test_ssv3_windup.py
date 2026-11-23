"""9G Accord SSV3 wind-up guard and ramp-in (opendbc/car/honda/ssv3.py Ssv3WindupGuard).

Through the real CarInterface (CAN in -> 0xE4 out): while the board has cut LKAS (524 MODE != STEER with our request),
the EPS is not acking (400 EPS_LKAS_ACK = 0), or the EPS serial link dropped (400 LIN_INTERFACE_FATAL_ERROR, or no
EPS frame at all), openpilot's command never winds up, CarControl.actuatorsOutput.torque differs from the request
(controlsd's steer_limited_by_safety -> integrator frozen), and on release the command ramps in from where it was
held instead of stepping back. No carState fault/pressed flag is raised for any of it. TI path and firmware 2 unchanged.
"""
import pytest

from opendbc.can import CANPacker
from opendbc.car import structs
from opendbc.car.honda import ssv3
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import (ACK_DEBOUNCE_FRAMES, BOARD_LEAD_IN_FRAMES, SERIAL_GAP_FRAMES,
                                    Ssv3Cut, Ssv3WindupGuard)
from opendbc.car.honda.hondacan import honda_checksum
from opendbc.car.honda.tests.test_ssv3 import ACCORD_DBC, _finish, car_frames, fw2_400, fw2_427, fw3_427, fw3_raw, ss_status
from opendbc.car.honda.tests.test_ssv3_tune import params
from opendbc.car.honda.values import CarControllerParams

STEP = 240 * 3 * 0.01        # STEER_DELTA_UP/DOWN = 3 per s of normalized torque at 100 Hz -> 7.2 counts per frame
MODE_IDLE, MODE_STEER = 1, 2


def eps_400(counter, *, ack=True, lin_fatal=False, driver=0):
  d = bytearray(5)
  d[0] = driver & 0xFF
  d[1] = (driver >> 8) & 0x01
  d[1] |= lin_fatal << 2       # LIN_INTERFACE_FATAL_ERROR: DBC 10|1@0+ = byte 1 bit 2
  d[4] = ack << 7
  return _finish(400, d, counter & 3)


def eps_raw_524(counter, *, mode=MODE_STEER, request=True):
  return fw3_raw(524, counter, [0, 0, 0, 0, 0, counter & 0xFF, (mode << 6) | (request << 5) | 7])


class Car:
  """A fw3 SSV3 car: each step() feeds one 10 ms CAN batch and runs the car controller once."""

  def __init__(self, ti=False, firmware=3):
    self.ci = CarInterface(params(ti=ti))
    self.packer = CANPacker(ACCORD_DBC)
    self.tick = 0
    self.firmware = firmware

  def step(self, torque, *, ack=True, mode=MODE_STEER, request=True, lin_fatal=False, eps_frame=True, lat=True,
           send_524=True):
    tick = self.tick
    board = []
    if eps_frame:
      if self.firmware == 3:
        board += [(400, eps_400(tick, ack=ack, lin_fatal=lin_fatal), 0), (427, fw3_427(tick, 0), 0)]
        if send_524:
          board.append((524, eps_raw_524(tick, mode=mode, request=request), 0))
      else:
        board += [(400, fw2_400(tick), 0), (427, fw2_427(tick, 0), 0)]
    if tick % 10 == 0:
      board.append((520, ss_status(tick // 10, self.firmware), 0))
    t = 1_000_000_000 + tick * 10_000_000
    cs = self.ci.update([(t, car_frames(self.packer, tick, board))])
    cc = structs.CarControl(latActive=lat, enabled=lat)
    cc.actuators.torque = torque
    actuators, sends = self.ci.apply(cc.as_reader(), t)
    e4 = [f for f in sends if f[0] == 0xE4]
    assert len(e4) == 1
    self.tick += 1
    wire = int.from_bytes(e4[0][1][0:2], "big", signed=True)
    return wire, float(actuators.torque), cs

  def run(self, n, torque, **kw):
    return [self.step(torque, **kw) for _ in range(n)]

  def at_full_left(self):
    out = self.run(80, 1.0)               # fw3 confirmed after 3 SS_STATUS frames; ramp to -240 (left = negative wire)
    assert self.ci.CS.ssv3.fw3
    assert out[-1][0] == -240
    return out


def steer_limited(requested, output):
  # controlsd: steer_limited_by_safety = abs(CC.actuators.torque - CO.actuatorsOutput.torque) > 1e-2 -> the torque
  # controller's freeze_integrator (latcontrol_torque.py) and no saturation timer
  return abs(requested - output) > 1e-2


# ---- each cut signal freezes the command and the integrator ----

@pytest.mark.parametrize("cut", ("no_ack", "board_idle", "board_passthrough"))
def test_eps_or_board_cut_drops_the_command_and_freezes_the_integrator(cut):
  car = Car()
  car.at_full_left()
  kw = {"no_ack": dict(ack=False), "board_idle": dict(mode=MODE_IDLE), "board_passthrough": dict(mode=0)}[cut]
  out = car.run(150, 1.0, **kw)            # the controller keeps asking for full left the whole time (wind-up)
  wires = [o[0] for o in out]
  # the board's own IDLE is believed at once; the EPS ack needs ACK_DEBOUNCE_FRAMES
  debounce = ACK_DEBOUNCE_FRAMES if cut == "no_ack" else 1
  assert all(w == -240 for w in wires[:debounce - 1])
  # nothing is applied: straight to the -1 keep-alive (request kept, never an LKAS-off 0) and held there
  assert all(w == -1 for w in wires[debounce - 1:])
  # integrator frozen on every cut frame, and no alert flags in carState
  for _, out_torque, cs in out[debounce:]:
    assert steer_limited(1.0, out_torque)
    assert not cs.steerFaultTemporary and not cs.steerFaultPermanent and not cs.steeringPressed
  assert car.ci.CC.ssv3.guard.reason & (Ssv3Cut.EPS_NO_ACK if cut == "no_ack" else Ssv3Cut.BOARD_IDLE)


def test_board_idle_chatter_at_the_hysteresis_edge_keeps_the_command_down():
  """ff 209 s: at |driver| 84-90 the board flips IDLE/STEER every 2-5 frames while the EPS still acks. After each IDLE
  the board sends its 5-frame zero lead-in, so nothing of ours is applied until BOARD_LEAD_IN_FRAMES STEER frames."""
  car = Car()
  car.at_full_left()
  out = []
  for idle_n, steer_n in ((4, 2), (1, 3), (3, 4), (2, 1), (5, 4)) * 4:
    out += car.run(idle_n, 1.0, mode=MODE_IDLE) + car.run(steer_n, 1.0)
  out += car.run(2, 1.0, mode=MODE_IDLE)   # the last IDLE; the board's lead-in follows
  assert all(o[0] == -1 for o in out)
  back = [o[0] for o in car.run(BOARD_LEAD_IN_FRAMES + 30, 1.0)]
  assert all(w == -1 for w in back[:BOARD_LEAD_IN_FRAMES - 1])
  ramp = back[BOARD_LEAD_IN_FRAMES - 1:]
  assert abs(ramp[0]) <= STEP + 1 and all(abs(b) - abs(a) <= STEP + 1 for a, b in zip(ramp, ramp[1:], strict=False))


def test_board_idle_without_our_request_bit_is_not_a_cut():
  car = Car()
  car.at_full_left()
  out = car.run(20, 1.0, mode=MODE_IDLE, request=False)
  assert all(o[0] == -240 for o in out) and car.ci.CC.ssv3.guard.reason == 0


@pytest.mark.parametrize("cut", ("lin_fatal", "serial_gap"))
def test_serial_link_drop_holds_the_command_no_growth_no_step(cut):
  car = Car()
  car.run(30, 0.0)
  ramp = car.run(10, 1.0)                  # half-way up the ramp
  held = ramp[-1][0]
  assert -100 < held < -30
  if cut == "lin_fatal":
    out = car.run(5, 1.0, lin_fatal=True)
  else:
    out = car.run(SERIAL_GAP_FRAMES + 3, 1.0, eps_frame=False)
    # the first SERIAL_GAP_FRAMES - 1 empty updates are ordinary batching jitter: the ramp goes on; detected on the
    # SERIAL_GAP_FRAMES-th, from where it holds
    assert all(abs(o[0] - (held - STEP * (i + 1))) <= 1 for i, o in enumerate(out[:SERIAL_GAP_FRAMES - 1]))
    held = out[SERIAL_GAP_FRAMES - 2][0]
    out = out[SERIAL_GAP_FRAMES - 1:]
  for wire, out_torque, cs in out:
    assert wire == held                    # hold: neither grows (wind-up) nor drops (the EPS may still be applying)
    assert steer_limited(1.0, out_torque)
    assert not cs.steerFaultTemporary and not cs.steeringPressed
  # link back: the normal ramp continues from the held value
  back = car.run(3, 1.0)
  assert all(abs(b[0] - (held - STEP * (i + 1))) <= 1 for i, b in enumerate(back))   # float ramp, rounded wire


def test_short_gap_below_threshold_is_ignored():
  car = Car()
  car.at_full_left()
  out = car.run(SERIAL_GAP_FRAMES - 1, 1.0, eps_frame=False)   # ordinary batching jitter
  assert all(o[0] == -240 for o in out)


# ---- ramp-in on release ----

@pytest.mark.parametrize("cut", ("no_ack", "board_idle"))
def test_release_ramps_in_from_where_the_eps_is_not_the_stale_command(cut):
  car = Car()
  car.at_full_left()
  kw = dict(ack=False) if cut == "no_ack" else dict(mode=MODE_IDLE)
  car.run(100, 1.0, **kw)                  # long cut (3.7 s spells / low-speed refusals)
  back = [o[0] for o in car.run(40 + BOARD_LEAD_IN_FRAMES, 1.0)]
  if cut == "board_idle":
    assert all(w == -1 for w in back[:BOARD_LEAD_IN_FRAMES - 1])   # the board's own zero lead-in
    back = back[BOARD_LEAD_IN_FRAMES - 1:]
  # first applied frame: one rate-limit step from the floor, then the normal up-rate, no 240 slam
  assert abs(back[0]) <= STEP + 1
  assert all(abs(b) - abs(a) <= STEP + 1 for a, b in zip([-1] + back, back, strict=False))
  assert back[-1] == -240


def test_ack_flicker_of_one_frame_is_ignored():
  car = Car()
  car.at_full_left()
  out = []
  for _ in range(10):
    out.append(car.step(1.0, ack=False))
    out += car.run(ACK_DEBOUNCE_FRAMES, 1.0)
  assert all(o[0] == -240 for o in out)


def test_low_speed_refusal_like_the_logs():
  """fc 327 s: the EPS stops acking below ~3 mph while openpilot stays latActive and keeps asking for more."""
  car = Car()
  car.run(60, -0.3)
  out = car.run(400, -1.0, ack=False)     # 4 s refusal while the controller winds up
  assert max(abs(o[0]) for o in out[ACK_DEBOUNCE_FRAMES:]) == 1
  assert all(not o[2].steerFaultTemporary and not o[2].steeringPressed for o in out)
  assert all(steer_limited(-1.0, o[1]) for o in out[ACK_DEBOUNCE_FRAMES:])


def test_engage_ramp_waits_for_the_eps_ack():
  car = Car()
  car.run(30, 0.0, lat=False)
  # latActive starts; the EPS acks ~130 ms (13 frames) later
  out = car.run(13, 0.5, ack=False) + car.run(40, 0.5)
  wires = [o[0] for o in out]
  assert max(abs(w) for w in wires[ACK_DEBOUNCE_FRAMES:13]) == 1
  assert abs(wires[13]) <= STEP + 1         # starts from 0 once the EPS listens, no pre-wound step
  assert wires[-1] == -120


# ---- firmware 2, no 524, TI ----

def test_firmware2_never_cuts():
  car = Car(firmware=2)
  out = car.run(120, 1.0, eps_frame=True)
  assert out[-1][0] == -240 and car.ci.CC.ssv3.guard.reason == 0
  gap = car.run(10, 1.0, eps_frame=False)
  assert all(o[0] == -240 for o in gap)


def test_no_524_frames_means_no_board_cut():
  car = Car()
  out = car.run(150, 1.0, send_524=False)
  assert out[-1][0] == -240 and car.ci.CC.ssv3.guard.reason == 0


def test_ti_path_has_no_guard_and_zero_0xe4():
  car = Car(ti=True)
  assert car.ci.CC.ssv3 is None and car.ci.CS.ssv3 is None
  out = car.run(50, 1.0, ack=False, mode=MODE_IDLE, lin_fatal=True)
  assert {o[0] for o in out} == {0}


# ---- the guard on its own ----

def test_guard_unit_caps():
  class S:
    fw3, eps_lkas_ack, board_request, board_mode, lin_fatal, frames_without_400 = True, True, True, 2, False, 0
  g, s = Ssv3WindupGuard(), S()
  assert g.update(s, True) == 0 and g.limit(0.9, 0.5) == 0.9
  s.lin_fatal = True
  assert g.update(s, True) == Ssv3Cut.LIN_FATAL
  assert g.limit(0.9, 0.5) == 0.5 and g.limit(-0.9, 0.5) == -0.5 and g.limit(0.2, 0.5) == 0.2
  s.board_mode = 1
  assert g.update(s, True) == Ssv3Cut.LIN_FATAL | Ssv3Cut.BOARD_IDLE
  assert g.limit(0.9, 0.5) == 0.0 and g.limit(-0.9, 0.5) == 0.0
  s.board_mode, s.lin_fatal = 2, False
  for _ in range(BOARD_LEAD_IN_FRAMES - 1):
    assert g.update(s, True) == Ssv3Cut.BOARD_IDLE   # lead-in latch
  assert g.update(s, True) == 0
  s.board_request, s.board_mode = False, 1           # IDLE without our request bit: not a cut
  assert g.update(s, True) == 0
  s.eps_lkas_ack = False
  assert not g.update(s, True) & Ssv3Cut.EPS_NO_ACK     # debounce: one frame is not enough
  g.update(s, True)
  assert g.reason & Ssv3Cut.EPS_NO_ACK and g.limit(0.9, 0.5) == 0.0
  assert g.update(s, False) == 0 and g.no_ack_frames == 0     # not latActive: reset
  s.fw3 = False
  assert g.update(s, True) == 0 and g.update(None, True) == 0


def test_steer_max_lookup_is_the_ssv3_clamp():
  assert max(abs(v) for v in CarControllerParams(params(ti=False)).STEER_LOOKUP_V) == 240


def test_ssv3_module_constants():
  assert (ACK_DEBOUNCE_FRAMES, BOARD_LEAD_IN_FRAMES, SERIAL_GAP_FRAMES) == (2, 5, 4)
  assert ssv3.BOARD_MODE_STEER == 2
  # retired 2026-11-23: blend probe and deadband compensation
  assert not hasattr(ssv3, "Ssv3BlendProbe") and not hasattr(ssv3, "deadband_compensate")
  assert honda_checksum  # imported for frame builders
