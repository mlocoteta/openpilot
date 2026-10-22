"""Honda pedal interceptor wired with its two sensor tracks swapped (HondaPedalSwapped param)."""
import pytest

from opendbc.can import CANPacker
from opendbc.can.dbc import pedal_checksum
from opendbc.car import create_gas_interceptor_command, structs
from opendbc.car.car_helpers import interfaces
from opendbc.car.honda import carcontroller, carstate, interface, pedal_tracks
from opendbc.car.honda.pedal_tracks import CONFIRM_FRAMES, PedalTrackCheck
from opendbc.car.honda.values import CAR, HondaFlags
from opendbc.car.tests.test_car_interfaces import get_test_starpilot_toggles

DBC = "honda_accord_2017_can_ssv2_generated"
DT_NS = 10_000_000
REST = (236, 531)      # 9G Accord rlog, pedal released (track 2 ~ 2.2x track 1)
PRESSED = (600, 1320)


def tracks(dat):
  return (dat[0] << 8) | dat[1], (dat[2] << 8) | dat[3]


def make_params(swapped):
  class Params:
    def __init__(self, *args, **kwargs):
      pass

    def get_bool(self, key, *args, **kwargs):
      return swapped if key == "HondaPedalSwapped" else False

    def get_float(self, key, *args, default=0.0, **kwargs):
      return default

    def get_int(self, key, *args, default=0, **kwargs):
      return default

    def get(self, *args, **kwargs):
      return None

    def put_float(self, *args, **kwargs):
      pass
  return Params


def make_interface(monkeypatch, swapped, pedal=True):
  for module in (carstate, carcontroller, interface):
    monkeypatch.setattr(module, "Params", make_params(swapped), raising=False)
  toggles = get_test_starpilot_toggles()
  fingerprint = {bus: {} for bus in range(8)}
  if pedal:
    fingerprint[0] = {0x201: 6}
  CarInterface = interfaces[CAR.HONDA_ACCORD_9G]
  CP = CarInterface.get_params(CAR.HONDA_ACCORD_9G, fingerprint, [], alpha_long=True, is_release=False, docs=False,
                               starpilot_toggles=toggles)
  return CarInterface(CP, CarInterface.get_starpilot_params(CAR.HONDA_ACCORD_9G, fingerprint, [], CP, toggles)), toggles


class TestCommand:
  packer = CANPacker(DBC)

  @pytest.mark.parametrize("gas", [0.05, 0.2, 0.5, 1.0])
  def test_swapped_command_exchanges_the_tracks(self, gas):
    _, normal, _ = create_gas_interceptor_command(self.packer, gas, 3)
    _, swapped, _ = create_gas_interceptor_command(self.packer, gas, 3, swap_channels=True)
    n1, n2 = tracks(normal)
    assert n2 > 1.9 * n1                     # track 2 is scaled twice track 1
    assert tracks(swapped) == (n2, n1)
    assert swapped[4] == normal[4]           # ENABLE + counter
    assert swapped[5] == pedal_checksum(0x200, None, swapped)

  @pytest.mark.parametrize("swap", [False, True])
  def test_zero_gas_is_zero_on_both_tracks(self, swap):
    _, dat, _ = create_gas_interceptor_command(self.packer, 0.0, 5, swap_channels=swap)
    assert tracks(dat) == (0, 0) and not dat[4] & 0x80


class TestParam:
  @pytest.mark.parametrize("swapped", [False, True])
  def test_flag_follows_param(self, monkeypatch, swapped):
    CI, _ = make_interface(monkeypatch, swapped)
    assert bool(CI.CP.flags & HondaFlags.PEDAL_SIGNALS_SWAPPED) == swapped
    assert CI.CC.pedal_signals_swapped == swapped
    assert CI.CS.pedal_tracks.swapped_setting == swapped

  def test_no_flag_without_pedal(self, monkeypatch):
    CI, _ = make_interface(monkeypatch, True, pedal=False)
    assert not CI.CP.flags & HondaFlags.PEDAL_SIGNALS_SWAPPED
    assert CI.CS.pedal_tracks is None


class TestTrackCheck:
  @pytest.mark.parametrize("setting", [False, True])
  @pytest.mark.parametrize("wired_swapped", [False, True])
  def test_detects_wiring(self, setting, wired_swapped):
    check = PedalTrackCheck(setting)
    t1, t2 = REST[::-1] if wired_swapped else REST
    for _ in range(CONFIRM_FRAMES - 1):
      check.update(t1, t2)
    assert check.observed is None and not check.mismatch
    check.update(t1, t2)
    assert check.observed == wired_swapped
    assert check.mismatch == (setting != wired_swapped)

  def test_latches_once(self):
    check = PedalTrackCheck(False)
    for _ in range(CONFIRM_FRAMES):
      check.update(*REST)
    for _ in range(3 * CONFIRM_FRAMES):
      check.update(*REST[::-1])
    assert check.observed is False and not check.mismatch

  @pytest.mark.parametrize("t1, t2", [(0, 0), (50, 120), (400, 500), (500, 400)])
  def test_unpowered_or_ambiguous_never_decides(self, t1, t2):
    check = PedalTrackCheck(False)
    for _ in range(3 * CONFIRM_FRAMES):
      check.update(t1, t2)
    assert check.observed is None and not check.mismatch

  def test_interrupted_streak_restarts(self):
    check = PedalTrackCheck(False)
    for _ in range(CONFIRM_FRAMES - 1):
      check.update(*REST[::-1])
    check.update(*REST)
    for _ in range(CONFIRM_FRAMES - 2):
      check.update(*REST[::-1])
    assert check.observed is None

  def test_logs(self, monkeypatch):
    lines = []
    monkeypatch.setattr(pedal_tracks.carlog, "warning", lambda msg, *a: lines.append(("w", msg)))
    monkeypatch.setattr(pedal_tracks.carlog, "error", lambda msg, *a: lines.append(("e", msg)))
    for setting in (False, True):
      check = PedalTrackCheck(setting)
      for _ in range(CONFIRM_FRAMES):
        check.update(*REST)
    assert lines[0][0] == "w" and "tracks normal" in lines[0][1]
    assert lines[1][0] == "e" and "look normal" in lines[1][1] and "HondaPedalSwapped=1" in lines[1][1]


class TestEndToEnd:
  def _drive(self, monkeypatch, setting, wired_swapped, sensor=REST, frames=2 * CONFIRM_FRAMES + 50):
    CI, toggles = make_interface(monkeypatch, setting)
    packer = CANPacker(DBC)
    CC = structs.CarControl()
    CC.enabled = CC.longActive = True
    CC.actuators.accel = 1.0
    CC.actuators.longControlState = structs.CarControl.Actuators.LongControlState.pid
    CC = CC.as_reader()
    t1, t2 = sensor[::-1] if wired_swapped else sensor
    gas_frames, gas_pressed = [], []
    for frame in range(frames):
      can = []
      if frame % 2 == 0:
        _, dat, _ = packer.make_can_msg("GAS_SENSOR", 0, {"INTERCEPTOR_GAS": t1, "INTERCEPTOR_GAS2": t2,
                                                         "STATE": 0, "COUNTER_PEDAL": (frame // 2) % 16})
        can.append((0x201, dat, 0))
      CS = CI.update([(frame * DT_NS, can)], toggles)[0]
      gas_pressed.append(CS.gasPressed)
      _, sends = CI.apply(CC, frame * DT_NS, toggles)
      gas_frames += [tracks(dat) for addr, dat, bus in sends if addr == 0x200]
    return CI, gas_frames, gas_pressed

  @pytest.mark.parametrize("swapped", [False, True])
  def test_matching_setting_sends_gas_in_wiring_order(self, monkeypatch, swapped):
    CI, gas_frames, _ = self._drive(monkeypatch, swapped, swapped)
    assert CI.CS.pedal_tracks.observed == swapped and not CI.CS.pedal_tracks.mismatch
    t1, t2 = gas_frames[-1]
    assert t1 > 0 and t2 > 0
    assert (t1 > t2) == swapped     # the larger (track-2 scaled) value goes to whichever byte pair feeds track 2

  @pytest.mark.parametrize("setting", [False, True])
  def test_mismatch_stops_gas(self, monkeypatch, setting):
    CI, gas_frames, _ = self._drive(monkeypatch, setting, not setting)
    assert CI.CS.pedal_tracks.mismatch
    assert any(f != (0, 0) for f in gas_frames[:CONFIRM_FRAMES // 2])  # before the check confirms
    assert all(f == (0, 0) for f in gas_frames[-CONFIRM_FRAMES // 2:])

  @pytest.mark.parametrize("setting", [False, True])
  @pytest.mark.parametrize("wired_swapped", [False, True])
  def test_gas_pressed_ignores_track_order(self, monkeypatch, setting, wired_swapped):
    _, _, rest = self._drive(monkeypatch, setting, wired_swapped, REST, frames=20)
    _, _, pressed = self._drive(monkeypatch, setting, wired_swapped, PRESSED, frames=20)
    assert not any(rest[2:]) and all(pressed[2:])
