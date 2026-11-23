"""9G Accord SSV3 wind-up guard with board firmware build 4 (526 BLEND_STATE; report 2026-11-19-ssv3-guard-526.md).

Build 4 no longer drops to IDLE on a driver override: the board stays in STEER and scales our command by its blend gain,
and 400 STEER_APPLIED is the torque actually sent. Through the real CarInterface (CAN in -> 0xE4 out), with a simulated
build-4 board (applied = last frame's command x gain): a full or >= 50 % cut drops the command to the +-1 keep-alive
(as for an IDLE cut), a partial cut holds it, the release ramps in alongside the board's own ramp, a ridden-through EPS
gap holds without a drop, and STEER_APPLIED far below our command is caught on its own. No 526 = build-3 rules.
"""
import pytest

from opendbc.can import CANPacker, CANParser
from opendbc.car import structs
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import (APPLIED_DEBOUNCE, APPLIED_LATCH_FRAMES, BLEND_RELEASE_STREAK, BLEND_STALE_FRAMES, Ssv3Cut,
                                    Ssv3WindupGuard)
from opendbc.car.honda.tests.test_ssv3 import ACCORD_DBC, car_frames, fw3_400, fw3_427, fw3_raw, ss_status
from opendbc.car.honda.tests.test_ssv3_tune import params
from opendbc.car.honda.tests.test_ssv3_windup import STEP, steer_limited

MODE_STEER = 2


def blend_526(counter, *, gain=255, gap=False, gap_ms=10, blend_active=True):
  flags = (gap << 0) | (blend_active << 3)
  return fw3_raw(526, counter, [gain, 0, 0, (-40) & 0xFF, gap_ms, 0, flags])


class Car4:
  """A firmware-3 board reporting build 4: 400 (with STEER_APPLIED), 427, 524 in STEER, 526 every frame."""

  def __init__(self, ti=False, send_526=True):
    self.ci = CarInterface(params(ti=ti))
    self.packer = CANPacker(ACCORD_DBC)
    self.tick = 0
    self.send_526 = send_526
    self.last_wire = 0
    self.applied = 0

  def step(self, torque, *, gain=255, eps_frame=True, gap=False, applied=None, ack=True, lat=True):
    tick = self.tick
    if applied is None:
      # the board applies last frame's command x gain (one frame lag), truncating toward zero like blendApply()
      p = self.last_wire * gain
      applied = p // 255 if p >= 0 else -((-p) // 255)
    board = []
    if eps_frame:
      self.applied = applied
      board += [(400, fw3_400(tick, steer=applied, lkas_ack=ack), 0), (427, fw3_427(tick, 0), 0),
                (524, fw3_raw(524, tick, [0, 0, 0, 0, 0, tick & 0xFF, (MODE_STEER << 6) | (1 << 5) | 7]), 0)]
    if self.send_526:
      board.append((526, blend_526(tick, gain=gain, gap=gap, gap_ms=40 if gap else 10), 0))
    if tick % 10 == 0:
      board.append((520, ss_status(tick // 10, 3), 0))
    t = 1_000_000_000 + tick * 10_000_000
    cs = self.ci.update([(t, car_frames(self.packer, tick, board))])
    cc = structs.CarControl(latActive=lat, enabled=lat)
    cc.actuators.torque = torque
    actuators, sends = self.ci.apply(cc.as_reader(), t)
    e4 = [f for f in sends if f[0] == 0xE4]
    assert len(e4) == 1
    self.tick += 1
    wire = int.from_bytes(e4[0][1][0:2], "big", signed=True)
    self.last_wire = wire
    return wire, float(actuators.torque), cs

  def run(self, n, torque, **kw):
    return [self.step(torque, **kw) for _ in range(n)]

  def at_full_left(self):
    out = self.run(80, 1.0)
    assert self.ci.CS.ssv3.fw3 and self.ci.CS.ssv3.blend_state
    assert out[-1][0] == -240 and self.reason == 0
    return out

  @property
  def reason(self):
    return self.ci.CC.ssv3.guard.reason


def no_alerts(out):
  return all(not cs.steerFaultTemporary and not cs.steerFaultPermanent and not cs.steeringPressed for _, _, cs in out)


def test_526_decodes_the_firmware_test_frame():
  # firmware test_blend_v4 output: "526: 00 2d 2d d8 07 00 08 33"
  parser = CANParser(ACCORD_DBC, [("BLEND_STATE", 0)], 0)
  parser.update([(1, [(526, bytes.fromhex("002d2dd807000833"), 0)])])
  vl = parser.vl["BLEND_STATE"]
  assert (vl["BLEND_GAIN"], vl["DRIVER_FILTERED"], vl["DRIVER_HOLD"], vl["DRIVER_ZERO"]) == (0, 45, 45, -5.0)
  assert (vl["EPS_GAP_MS"], vl["EPS_GAP_COUNT"], vl["EPS_GAP_ACTIVE"], vl["BOARD_BLEND_ACTIVE"]) == (7, 0, 0, 1)
  assert vl["EPS_GAP_FAULTS"] == 0 and vl["COUNTER"] == 3


def test_526_4bit_counter_and_checksum_pass_the_parser():
  parser = CANParser(ACCORD_DBC, [("BLEND_STATE", 0)], 0)
  for i in range(40):
    parser.update([(1_000_000_000 + i * 10_000_000, [(526, blend_526(i, gain=200, gap=True), 0)])])
  assert parser.can_valid and parser.message_states[526].counter_fail == 0
  assert parser.vl["BLEND_STATE"]["BLEND_GAIN"] == 200 and parser.vl["BLEND_STATE"]["EPS_GAP_ACTIVE"] == 1


def test_normal_steering_and_road_bumps_are_not_cuts():
  car = Car4()
  car.at_full_left()
  out = car.run(100, 1.0)
  # pothole-class board cuts (<= ~7 %, gain >= 237) for a few frames
  out += car.run(4, 1.0, gain=237) + car.run(30, 1.0)
  assert all(o[0] == -240 for o in out) and car.reason == 0


def test_full_cut_at_zero_torque_drops_to_keep_alive_and_freezes_the_integrator():
  """Hard push: the board stays in STEER and sends 0 torque (gain 0). Before, openpilot could not see this."""
  car = Car4()
  car.at_full_left()
  out = car.run(4, 1.0, gain=128) + car.run(200, 1.0, gain=0)
  wires = [o[0] for o in out]
  assert wires[:4] == [-240] * 4                 # gain 128: a 50 % cut is not reached yet... it holds
  assert all(w == -1 for w in wires[4:])          # cap 0 from the first frame the cut reaches 50 %
  assert all(steer_limited(1.0, o[1]) for o in out[4:]) and no_alerts(out)
  assert car.reason & Ssv3Cut.BOARD_BLEND and not car.reason & Ssv3Cut.BOARD_IDLE


def test_the_same_override_without_526_winds_up_like_before():
  """Build-3 rules with a board that stays in STEER: nothing is seen (the gap 526 closes)."""
  car = Car4(send_526=False)
  car.run(80, 1.0)
  out = car.run(100, 1.0, gain=0)
  assert all(o[0] == -240 for o in out) and car.reason == 0


@pytest.mark.parametrize("gain", (127, 85, 40))
def test_partial_cut_of_half_or_more_drops_to_keep_alive(gain):
  car = Car4()
  car.at_full_left()
  out = car.run(150, 1.0, gain=gain)
  assert out[0][0] == -1 and all(o[0] == -1 for o in out)
  assert car.reason & Ssv3Cut.BOARD_BLEND


@pytest.mark.parametrize("gain", (229, 180, 128))
def test_light_partial_cut_holds_no_growth_no_drop(gain):
  car = Car4()
  car.run(30, 0.0)
  held = car.run(10, 1.0)[-1][0]                 # half-way up the ramp
  assert -100 < held < -30
  out = car.run(150, 1.0, gain=gain)
  assert all(o[0] == held for o in out)          # neither winds up nor drops (part of it is still applied)
  assert all(steer_limited(1.0, o[1]) for o in out) and no_alerts(out)
  assert car.reason == Ssv3Cut.BLEND_PARTIAL       # no APPLIED_LOW: applied = held x gain is what 526 explains


def test_cut_chatter_around_the_threshold_stays_down():
  car = Car4()
  car.at_full_left()
  out = []
  for _ in range(30):
    out += car.run(2, 1.0, gain=120) + car.run(1, 1.0, gain=140) + car.run(2, 1.0, gain=100)
  assert all(o[0] == -1 for o in out)


def _release_gains():
  # firmware: +ceil(1024/50) per frame on a 0..1024 scale, reported as round(x * 255 / 1024)
  g, out = 0, []
  while g < 1024:
    g = min(1024, g + 21)
    out.append((g * 255 + 512) // 1024)
  return out


def test_release_ramps_in_with_the_board_no_step():
  car = Car4()
  car.at_full_left()
  car.run(150, 1.0, gain=0)                      # long full cut: wire at -1
  out, applied = [], []
  for g in _release_gains():
    out.append(car.step(1.0, gain=g))
    applied.append(car.ci.CS.ssv3.steer_applied)
  out += car.run(40, 1.0)
  wires = [o[0] for o in out]
  # our command stays at the keep-alive until the board's release is seen, then ramps at the normal rate
  assert all(w == -1 for w in wires[:BLEND_RELEASE_STREAK - 1])
  ramp = wires[BLEND_RELEASE_STREAK - 1:]
  assert abs(ramp[0]) <= STEP + 1
  assert all(abs(b) - abs(a) <= STEP + 1 for a, b in zip(ramp, ramp[1:], strict=False))
  assert wires[-1] == -240 and car.reason == 0
  # what the board gave the EPS: no step (product of the two ramps)
  # (slope of gain x command <= 240 x 5/255 + 7.2 counts per frame)
  assert all(abs(b - a) <= 13 for a, b in zip(applied, applied[1:], strict=False))
  # both ramps run together: full LKAS within ~0.5 s of the release starting
  assert wires[len(_release_gains())] == -240 or abs(wires[len(_release_gains())]) > 200


def test_regrab_during_release_drops_again():
  car = Car4()
  car.at_full_left()
  car.run(100, 1.0, gain=0)
  for g in _release_gains()[:20]:
    car.step(1.0, gain=g)
  assert car.reason == 0                        # releasing: the ramp-in runs
  out = car.run(20, 1.0, gain=30)                # the driver grabs again: the gain drops at once
  assert all(o[0] == -1 for o in out) and car.reason & Ssv3Cut.BOARD_BLEND


def test_eps_gap_ride_through_holds_without_a_drop():
  """A 70 ms EPS serial gap on build 4: no 400/427/524, 526 says EPS_GAP_ACTIVE, the board fades its gain from
  30 ms and ramps back after. The guard holds (no growth, no drop to the keep-alive) and then resumes the ramp."""
  car = Car4()
  car.run(30, 0.0)
  held = car.run(10, 1.0)[-1][0]
  assert -100 < held < -30
  # gap: frozen 20-30 ms, then linear fade to 0 at 100 ms (gain at 40/50/60/70 ms)
  gap_gains = [255, 255, 255, 219, 182, 146, 109]
  out = [car.step(1.0, gain=g, eps_frame=False, gap=i >= 1) for i, g in enumerate(gap_gains)]
  wires_gap = [o[0] for o in out]
  assert all(abs(w) >= abs(held) - 1 for w in wires_gap)     # never dropped
  assert all(abs(w) <= abs(held) + 2 * STEP + 1 for w in wires_gap)   # held once the gap is seen
  hold_at = wires_gap[-1]
  # the EPS is back: the board ramps its gain up from 109 over ~0.25 s
  back_gains = [114, 119, 124] + list(range(129, 256, 5)) + [255] * 30
  back = [car.step(1.0, gain=g) for g in back_gains]
  wires = [o[0] for o in back]
  assert all(abs(w) >= abs(hold_at) for w in wires)          # no BOARD_BLEND drop for the gap fade
  assert all(abs(b) - abs(a) <= STEP + 1 for a, b in zip([hold_at] + wires, wires, strict=False))
  assert wires[-1] == -240
  assert no_alerts(out + back)


def test_applied_far_below_the_command_is_caught_without_526_explaining_it():
  car = Car4()
  car.at_full_left()
  out = car.run(200, 1.0, applied=0)             # 526 says full gain, yet the board reports 0 sent
  wires = [o[0] for o in out]
  assert all(w == -240 for w in wires[:APPLIED_DEBOUNCE - 1])
  first = APPLIED_DEBOUNCE - 1                   # cut on the debounce frame itself
  assert all(w == -1 for w in wires[first:first + APPLIED_LATCH_FRAMES])
  # then it re-checks with a short ramp and drops again: never winds up, mostly at the keep-alive
  rest = wires[first:]
  assert max(abs(w) for w in rest) <= 10 * STEP   # ramp to the 30-count window floor + window + debounce (~65)
  assert sum(w == -1 for w in rest) > 0.7 * len(rest)
  assert all(steer_limited(1.0, o[1]) for o in out[first:]) and no_alerts(out)
  # the board applies again: the ramp-in completes
  back = car.run(APPLIED_LATCH_FRAMES + 40, 1.0)
  assert back[-1][0] == -240 and car.reason == 0


def test_applied_lag_on_a_rising_command_is_not_a_cut():
  car = Car4()
  car.run(30, 0.0)
  # applied lags our command by two frames while ramping (worst case of the 1-2 frame board/EPS lag)
  hist = [0, 0]
  out = []
  for _ in range(60):
    o = car.step(1.0, applied=hist[-2])
    hist.append(o[0])
    out.append(o)
  assert out[-1][0] == -240 and car.reason == 0
  assert not any(abs(b) < abs(a) for a, b in zip([o[0] for o in out], [o[0] for o in out][1:], strict=False))


def test_526_stopping_returns_to_build3_rules():
  car = Car4()
  car.at_full_left()
  car.send_526 = False
  car.run(BLEND_STALE_FRAMES + 1, 1.0)
  assert not car.ci.CS.ssv3.blend_state
  out = car.run(50, 1.0, applied=0)               # STEER_APPLIED is not read without 526 (build-3 meaning)
  assert all(o[0] == -240 for o in out) and car.reason == 0


def test_build4_still_catches_eps_no_ack():
  car = Car4()
  car.at_full_left()
  out = car.run(20, 1.0, ack=False)
  assert out[-1][0] == -1 and car.reason & Ssv3Cut.EPS_NO_ACK


def test_ti_path_ignores_526():
  car = Car4(ti=True)
  assert car.ci.CC.ssv3 is None and car.ci.CS.ssv3 is None
  out = car.run(50, 1.0, gain=0, applied=0)
  assert {o[0] for o in out} == {0}


def test_guard_unit_blend_rules():
  class S:
    fw3, eps_lkas_ack, board_request, board_mode, lin_fatal, frames_without_400 = True, True, True, 2, False, 0
    blend_state, blend_gain, blend_rise_frames, eps_gap_active, frames_since_eps_gap = True, 255, 0, False, 60
    new_400, steer_applied = True, 0
  g, s = Ssv3WindupGuard(), S()
  assert g.update(s, True) == 0
  s.blend_gain = 127
  assert g.update(s, True) == Ssv3Cut.BOARD_BLEND and g.limit(0.9, 0.5) == 0.0
  s.blend_gain = 200
  assert g.update(s, True) == Ssv3Cut.BLEND_PARTIAL and g.limit(0.9, 0.5) == 0.5
  s.blend_rise_frames = BLEND_RELEASE_STREAK
  s.blend_gain = 50
  assert g.update(s, True) == 0                   # releasing
  s.blend_rise_frames, s.eps_gap_active, s.frames_since_eps_gap = 0, True, 0
  assert g.update(s, True) == Ssv3Cut.SERIAL_GAP | Ssv3Cut.BLEND_PARTIAL   # gap fade: hold, never cap 0
  s.eps_gap_active, s.frames_since_eps_gap, s.blend_gain = False, 60, 255
  for w in (-100, -100, -100, -100):
    g.note_sent(w)
  s.steer_applied = -50                          # exactly half: applied
  assert g.update(s, True) == 0 and g.update(s, True) == 0
  s.steer_applied = -49
  assert g.update(s, True) == 0                   # debounce
  assert g.update(s, True) == Ssv3Cut.APPLIED_LOW and g.limit(-0.9, -0.5) == 0.0
  s.steer_applied = -100
  for _ in range(APPLIED_LATCH_FRAMES - 1):       # latched (the next commands are +-1: nothing to compare)
    assert g.update(s, True) == Ssv3Cut.APPLIED_LOW
  assert g.update(s, True) == 0
  for w in (-100, -100, 40, -100):               # mixed signs: no reference, no check
    g.note_sent(w)
  s.steer_applied = 0
  g.update(s, True)
  assert g.update(s, True) == 0
  s.blend_state = False                           # build 3: the 526 rules are off entirely
  s.blend_gain = 0
  assert g.update(s, True) == 0
