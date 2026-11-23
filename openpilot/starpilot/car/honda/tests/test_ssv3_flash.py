"""ssv3_flash.py (SSV3 board update over CAN from the comma): frames, decoders, guards and the HELLO
handshake against a simulated board. No device, no panda."""
import importlib.util
import os
import sys

import pytest

from openpilot.starpilot.car.honda import ssv3_flash as sf

FW_TOOLS = os.path.expanduser("~/ssv3-fw3-src/tools")


# ---------- a fake clock and a simulated SSV3 board ----------

class Clock:
  def __init__(self):
    self.t = 100.0

  def __call__(self):
    self.t += 0.0005   # every look at the clock costs 0.5 ms of simulated time
    return self.t


class Board:
  """Application: 520/525 at 10 Hz; HELLO -> bootloader (or BUSY while steering). Bootloader: answers
  HELLO and BOOT, 30 s idle timeout back to the app. Mirrors canboot/boot_core.c + src/main.cpp."""

  def __init__(self, clock, version=3, hw=4, build=1, steering=False, present=True, stuck=False,
               ignore_boot=False, extra=None):
    self.clock, self.version, self.hw, self.build = clock, version, hw, build
    self.steering, self.present, self.stuck, self.ignore_boot = steering, present, stuck, ignore_boot
    self.where = "app"
    self.next_status = clock.t
    self.boot_entered = None
    self.last_cmd = None
    self.counter = 0
    self.out = []
    self.extra = extra or []    # (addr, data) frames other ECUs send every 10 ms
    self.next_extra = clock.t
    self.log = []

  def tick(self):
    now = self.clock.t
    if not self.present:
      return
    if self.where == "app":
      while now >= self.next_status:
        self.out.append((sf.SS_STATUS, bytes([(self.hw << 4) | self.version, 0x00, 0x10 | self.counter % 4])))
        self.out.append((sf.BOARD_DIAG, bytes([0, 0, 0, 0, 0, 0, self.build, 0])))
        self.counter += 1
        self.next_status += 0.1
    elif not self.stuck and now - self.last_cmd > sf.IDLE_TIMEOUT:
      self.to_app()
    while now >= self.next_extra:
      self.out.extend(self.extra)
      self.next_extra += 0.01

  def to_app(self):
    self.where = "app"
    self.next_status = self.clock.t + 0.1
    self.log.append(("app", self.clock.t))

  def receive(self, data):
    if not self.present:
      return
    self.tick()
    if self.where == "app":
      if data[:5] == sf.hello_frame()[:5] and len(data) == 8:
        if self.steering:
          self.out.append((sf.RESPONSE_ID, bytes([0x81, 7, 0, 1, 1, 0, 0, 0])))
        else:
          self.where = "boot"            # jumps; the HELLO itself is not answered
          self.boot_entered = self.clock.t
          self.last_cmd = self.clock.t
          self.log.append(("boot", self.clock.t))
      return
    self.last_cmd = self.clock.t
    if data == sf.hello_frame():
      self.out.append((sf.RESPONSE_ID, bytes([0x81, 0, 1, 1, 1, 0, 0, 0])))
    elif data == sf.boot_frame() and not self.ignore_boot:
      self.out.append((sf.RESPONSE_ID, bytes([0x85, 0, 0, 0, 0, 0, 0, 0])))
      self.to_app()
    elif data[0] not in (1, 5):
      self.out.append((sf.RESPONSE_ID, bytes([data[0] | 0x80, 1, 0, 0, 0, 0, 0, 0])))


class FakeTransport:
  def __init__(self, board, clock):
    self.board, self.clock = board, clock
    self.mode = "noOutput"
    self.sent = []
    self.modes = []

  def set_mode(self, name, param=0):
    self.mode = name
    self.modes.append(name)

  def enable_tx(self):
    self.set_mode("elm327", 1)

  def send(self, data):
    assert self.mode == "elm327", "transmitted outside ELM327 mode"
    self.sent.append(bytes(data))
    self.board.receive(bytes(data))

  def recv_all(self):
    self.clock.t += 0.001
    self.board.tick()
    out, self.board.out = self.board.out, []
    yield from out

  def health(self):
    return dict(IGN_ON)

  def close(self):
    self.set_mode("silent")


@pytest.fixture(autouse=True)
def fake_time(monkeypatch):
  clock = Clock()
  monkeypatch.setattr(sf.time, "monotonic", clock)
  monkeypatch.setattr(sf.time, "sleep", lambda s: setattr(clock, "t", clock.t + s))
  return clock


def setup(fake_time, **kw):
  board = Board(fake_time, **kw)
  return board, FakeTransport(board, fake_time)


IGN_OFF = {"ignition_line": False, "ignition_can": False}
IGN_ON = {"ignition_line": True, "ignition_can": True}


# ---------- frames ----------

def test_frames():
  assert sf.hello_frame() == bytes.fromhex("0153535633000000")
  assert sf.boot_frame() == bytes.fromhex("05424f4f54000000")
  frame = bytes([3, 0x10, 0x00, 0xDE, 0xAD, 0xBE, 0xEF])
  x = 0xA5
  for b in frame:
    x ^= b
  assert sf.check_byte(frame) == x
  assert sf.with_check(frame) == frame + bytes([x])
  assert all(len(f) == 8 for f in (sf.hello_frame(), sf.boot_frame(), sf.with_check(frame)))


def test_ids_pass_panda_elm327_safety():
  # elm327_tx_hook: (addr & 0x1FFF00FF) == 0x18DA00F1, 8 bytes
  assert (sf.REQUEST_ID & 0x1FFF00FF) == 0x18DA00F1
  assert sf.REQUEST_ID == 0x18DAE4F1 and sf.RESPONSE_ID == 0x18DAF1E4


@pytest.mark.skipif(not os.path.exists(os.path.join(FW_TOOLS, "flash_can.py")), reason="LKAS_EPS_V3 tools not copied")
def test_frames_match_the_firmware_tool():
  spec = importlib.util.spec_from_file_location("flash_can", os.path.join(FW_TOOLS, "flash_can.py"))
  sys.path.insert(0, FW_TOOLS)
  try:
    fc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fc)
  finally:
    sys.path.remove(FW_TOOLS)
  assert (fc.REQUEST_ID, fc.RESPONSE_ID) == (sf.REQUEST_ID, sf.RESPONSE_ID)
  assert bytes([fc.CMD_HELLO]) + b"SSV3" + bytes(3) == sf.hello_frame()
  assert bytes([fc.CMD_BOOT]) + b"BOOT" + bytes(3) == sf.boot_frame()
  frame = bytes([4, 0x34, 0x12, 1, 2, 3, 4])
  assert fc.with_check(frame) == sf.with_check(frame)
  assert fc.STATUS == sf.STATUS


def test_parse_response():
  r = sf.parse_response(bytes([0x81, 0, 1, 1, 1, 0, 0, 0]))
  assert r["cmd"] == sf.CMD_HELLO and r["status"] == 0 and r["where"] == "bootloader" and r["app_valid"]
  assert sf.parse_response(bytes([0x81, 7, 0, 1, 1, 0, 0, 0]))["status_text"].startswith("busy")
  assert sf.parse_response(bytes([0x01, 0, 0, 0, 0, 0, 0, 0])) is None
  assert sf.parse_response(bytes([0x81, 0])) is None


# ---------- decoders ----------

def test_board_decoders():
  # the car's board, live 2026-11-14: 0x208 = 43 00 16 -> firmware 3, hardware 4
  assert sf.decode_ss_status(bytes.fromhex("430016"))["version"] == 3
  assert sf.decode_ss_status(bytes.fromhex("430016"))["hardware"] == 4
  assert sf.decode_ss_status(bytes.fromhex("420206"))["version"] == 2
  d = sf.decode_board_diag(bytes([5, 0, 0, 0, 0, 0x0D, 1, 0x30]))
  assert d["tx_dropped"] == 5 and d["build"] == 1 and d["options"] == 0x0D
  assert sf.eps_raw_mode(bytes([0, 0, 0, 0, 0, 0, 0x80, 0])) == sf.MODE_STEER
  assert sf.steer_request(bytes([0, 0, 0x80, 0, 0]))
  assert not sf.steer_request(bytes([0x7f, 0xff, 0x0f, 0, 0]))


def _packer():
  try:
    from opendbc.can import CANPacker, CANParser
    from opendbc.car import Bus
    from opendbc.car.honda.values import DBC, CAR
    name = DBC[CAR.HONDA_ACCORD_9G][Bus.pt]
    return CANPacker(name), CANParser, name
  except Exception as e:  # pragma: no cover
    pytest.skip(f"opendbc not built: {e}")


@pytest.mark.parametrize("gear,park", [(1, True), (2, False), (4, False), (8, False), (0, False)])
def test_gear_decoder_matches_the_dbc_auto(gear, park):
  packer, _, _ = _packer()
  addr, dat, _ = packer.make_can_msg("GEARBOX_AUTO", 0, {"GEAR_SHIFTER": gear})
  assert addr == sf.GEARBOX_AUTO and sf.gear_is_park(addr, dat) is park


@pytest.mark.parametrize("gear,park", [(1, True), (2, False), (3, False), (4, False), (7, False), (10, False)])
def test_gear_decoder_matches_the_dbc_cvt(gear, park):
  packer, _, _ = _packer()
  addr, dat, _ = packer.make_can_msg("GEARBOX_CVT", 0, {"GEAR_SHIFTER": gear})
  assert addr == sf.GEARBOX_CVT and sf.gear_is_park(addr, dat) is park


@pytest.mark.parametrize("kph", [0.0, 0.05, 3.2, 120.5])
def test_speed_decoder_matches_the_dbc(kph):
  packer, _, _ = _packer()
  addr, dat, _ = packer.make_can_msg("ENGINE_DATA", 0, {"XMISSION_SPEED": kph})
  assert addr == sf.ENGINE_DATA and sf.xmission_speed_kph(dat) == pytest.approx(kph, abs=0.006)


def test_board_decoders_match_the_ssv3_dbc():
  # SS_STATUS / BOARD_DIAG / EPS_RAW / 0xE4 are in the 9G's SSV3 fragment
  packer, _, _ = _packer()
  _, d520, _ = packer.make_can_msg("SS_STATUS", 0, {"VERSION_NUM": 3, "HARDWARE_REV": 4})
  assert sf.decode_ss_status(d520)["version"] == 3 and sf.decode_ss_status(d520)["hardware"] == 4
  _, d525, _ = packer.make_can_msg("BOARD_DIAG", 0, {"FIRMWARE_BUILD": 7, "TX_DROPPED": 2})
  assert sf.decode_board_diag(d525)["build"] == 7 and sf.decode_board_diag(d525)["tx_dropped"] == 2
  _, d524, _ = packer.make_can_msg("EPS_RAW", 0, {"MODE": 2})
  assert sf.eps_raw_mode(d524) == sf.MODE_STEER
  _, de4, _ = packer.make_can_msg("STEERING_CONTROL", 0, {"STEER_TORQUE": 0, "STEER_TORQUE_REQUEST": 1})
  assert sf.steer_request(de4)


# ---------- guards ----------

def params_dir(tmp_path, **values):
  for k, v in values.items():
    (tmp_path / k).write_text(v)
  return str(tmp_path)


def test_host_guards(tmp_path):
  none = lambda pat: False
  sf.check_host_guards(params_dir(tmp_path, IsOffroad="1"), pgrep=none)
  with pytest.raises(sf.GuardError, match="IsOffroad"):
    sf.check_host_guards(params_dir(tmp_path / "..", IsOffroad="0"), pgrep=none)
  d = tmp_path / "missing"
  d.mkdir()
  with pytest.raises(sf.GuardError, match="IsOffroad"):
    sf.check_host_guards(str(d), pgrep=none)
  d2 = tmp_path / "onroad"
  d2.mkdir()
  with pytest.raises(sf.GuardError, match="IsOnroad"):
    sf.check_host_guards(params_dir(d2, IsOffroad="1", IsOnroad="1"), pgrep=none)
  with pytest.raises(sf.GuardError, match="pandad"):
    sf.check_host_guards(params_dir(tmp_path, IsOffroad="1"), pgrep=lambda pat: pat == "pandad")
  with pytest.raises(sf.GuardError, match="manager"):
    sf.check_host_guards(params_dir(tmp_path, IsOffroad="1"), pgrep=lambda pat: pat == "manager.py")


def snap_with(*frames, seconds=1.0):
  s = sf.BusSnapshot()
  for addr, data in frames:
    s.add(addr, data)
  s.seconds = seconds
  return s


BOARD = [(sf.SS_STATUS, bytes.fromhex("430016"))] * 10 + [(sf.BOARD_DIAG, bytes([0, 0, 0, 0, 0, 0, 1, 0]))] * 10
PARK_AUTO = (sf.GEARBOX_AUTO, bytes([0, 0, 0, 0x01, 0, 0]))
DRIVE_AUTO = (sf.GEARBOX_AUTO, bytes([0, 0, 0, 0x08, 0, 0]))
STOPPED = (sf.ENGINE_DATA, bytes(8))
MOVING = (sf.ENGINE_DATA, bytes([0x01, 0x40, 0, 0, 0, 0, 0, 0]))


def test_bus_guards_pass():
  assert sf.check_bus_guards(snap_with(*BOARD), IGN_OFF)["version"] == 3       # ignition off: car silent
  assert sf.check_bus_guards(snap_with(*BOARD, PARK_AUTO, STOPPED), IGN_ON)["build"] == 1
  assert sf.check_bus_guards(snap_with(*BOARD, (sf.GEARBOX_CVT, bytes([1, 0, 0, 0, 0, 1, 0, 0])), STOPPED), IGN_ON)


@pytest.mark.parametrize("frames,health,match", [
  ((*BOARD,), IGN_ON, "not confirmed parked"),                      # ignition on, car says nothing
  ((*BOARD, DRIVE_AUTO, STOPPED), IGN_ON, "not confirmed parked"),
  ((*BOARD, PARK_AUTO, MOVING), IGN_ON, "not confirmed parked"),
  ((*BOARD, PARK_AUTO), IGN_ON, "not confirmed parked"),            # no speed frame
  ((*BOARD, DRIVE_AUTO, STOPPED), IGN_OFF, "not parked"),
  ((*BOARD, (sf.STEERING_CONTROL, bytes([0, 0, 0x80, 0, 0]))), IGN_OFF, "steer request"),
  ((*BOARD, (sf.RESPONSE_ID, bytes(8))), IGN_OFF, "already using"),
  ((*BOARD, (sf.REQUEST_ID, bytes(8))), IGN_OFF, "already using"),
  (((sf.BOARD_DIAG, bytes(8)),), IGN_OFF, "no SS_STATUS"),
  (((sf.SS_STATUS, bytes.fromhex("420206")),), IGN_OFF, "firmware 2"),
  ((*BOARD, (sf.EPS_RAW, bytes([0, 0, 0, 0, 0, 0, 0x80, 0]))), IGN_OFF, "MODE STEER"),
])
def test_bus_guards_refuse(frames, health, match):
  with pytest.raises(sf.GuardError, match=match):
    sf.check_bus_guards(snap_with(*frames), health)


# ---------- HELLO handshake against the simulated board ----------

def test_hello_round_trip(fake_time):
  board, t = setup(fake_time)
  report = {}
  assert sf.run_hello(t, report, IGN_OFF) == 0
  assert report["guards"] == "passed"
  assert report["before"]["board"]["version"] == 3 and report["before"]["board"]["build"] == 1
  assert report["hello"]["where"] == "bootloader" and report["hello"]["status"] == 0 and report["hello"]["app_valid"]
  assert report["boot"]["status"] == 0
  assert report["after"]["app_normal"] and report["after"]["waited_s"] < 3
  assert [k for k, _ in board.log] == ["boot", "app"]
  # only HELLO / BOOT went out, all in ELM327 mode, and the panda ended in noOutput
  assert set(t.sent) <= {sf.hello_frame(), sf.boot_frame()}
  assert t.modes[0] == "elm327" and t.modes[-1] == "noOutput"
  assert not any(f[0] in (sf.CMD_ERASE, sf.CMD_WRITE, sf.CMD_FINISH) for f in t.sent)


def test_hello_refused_while_steering(fake_time):
  board, t = setup(fake_time, steering=True)
  report = {}
  assert sf.run_hello(t, report, IGN_OFF) == 3
  assert report["hello"]["status"] == sf.STATUS_BUSY
  assert board.where == "app" and report["after"]["app_normal"]
  assert sf.boot_frame() not in t.sent


def test_no_answer_is_reported_not_retried_forever(fake_time):
  board, t = setup(fake_time, present=False)
  # board absent -> the guard refuses before anything is sent
  with pytest.raises(sf.GuardError):
    sf.run_hello(t, {}, IGN_OFF)
  assert t.sent == []


def test_board_heard_but_hello_unanswered(fake_time, monkeypatch):
  board, t = setup(fake_time)
  monkeypatch.setattr(board, "receive", lambda data: None)   # the app ignores HELLO
  report = {}
  assert sf.run_hello(t, report, IGN_OFF) == 2
  assert report["hello"]["answer"] is None
  assert report["after"]["app_normal"]
  assert len(t.sent) < 1000          # one bounded burst (2 s at ~5 ms), no retry loop


def test_boot_lost_falls_back_to_the_idle_timeout(fake_time):
  board, t = setup(fake_time, ignore_boot=True)
  report = {}
  assert sf.run_hello(t, report, IGN_OFF) == 0
  assert "error" in report["boot"]
  assert report["after"]["app_normal"] and report["after"]["waited_s"] >= sf.IDLE_TIMEOUT - 2


def test_stuck_in_bootloader_is_reported(fake_time):
  board, t = setup(fake_time, ignore_boot=True, stuck=True)
  report = {}
  assert sf.run_hello(t, report, IGN_OFF) == 4
  assert "USB DFU" in report["STUCK"]
  assert not report["after"]["app_normal"]


def test_guard_failure_sends_nothing(fake_time):
  board, t = setup(fake_time, extra=[DRIVE_AUTO, STOPPED])
  with pytest.raises(sf.GuardError):
    sf.run_hello(t, {}, IGN_ON)
  assert t.sent == [] and "elm327" not in t.modes


def test_parked_with_ignition_on(fake_time):
  board, t = setup(fake_time, extra=[PARK_AUTO, STOPPED])
  report = {}
  assert sf.run_hello(t, report, IGN_ON) == 0
  assert report["before"]["parked"] is True


def test_flash_needs_explicit_confirmation():
  with pytest.raises(SystemExit, match="confirm-flash"):
    sf.main(["--flash", "x.bin"])


class FakePanda:
  def __init__(self):
    self.calls = []

  def send_heartbeat(self, engaged=True):
    self.calls.append(("hb", engaged))

  def set_power_save(self, v):
    self.calls.append(("ps", v))

  def set_safety_mode(self, mode, param=0):
    self.calls.append(("mode", int(mode), param))

  def can_clear(self, bus):
    pass

  def can_send(self, addr, dat, bus):
    self.calls.append(("tx", addr, bytes(dat), bus))

  def can_recv(self):
    return [(sf.SS_STATUS, b"\x43\x00\x16", 0), (sf.SS_STATUS, b"\x43\x00\x16", 128), (0x123, b"\x00", 2)]


def test_panda_bus_transport(fake_time):
  from opendbc.car.structs import CarParams
  p = FakePanda()
  bus = sf.PandaBus(0, panda=p)
  assert ("hb", False) in p.calls and ("ps", 0) in p.calls
  assert ("mode", int(CarParams.SafetyModel.noOutput), 0) in p.calls
  assert list(bus.recv_all()) == [(sf.SS_STATUS, b"\x43\x00\x16")]   # own bus only, no TX echo (bus 128)
  bus.enable_tx()
  assert p.calls[-1][:3] == ("mode", int(CarParams.SafetyModel.elm327), 1)
  bus.send(sf.hello_frame())
  assert ("tx", sf.REQUEST_ID, sf.hello_frame(), 0) in p.calls
  fake_time.t += 1.0
  n = sum(1 for c in p.calls if c[0] == "hb")
  list(bus.recv_all())
  assert sum(1 for c in p.calls if c[0] == "hb") == n + 1         # heartbeats keep the panda out of SILENT
  bus.close()
  assert p.calls[-1][:2] == ("mode", int(CarParams.SafetyModel.silent))


def test_waits_for_the_board_to_power_up(fake_time):
  # openpilot stopped while offroad, then the ignition goes ON (P, engine off): the board appears late
  board, t = setup(fake_time, extra=[PARK_AUTO, STOPPED])
  board.present = False
  on_at = fake_time.t + 20.0
  orig = board.tick

  def tick():
    if not board.present and fake_time.t >= on_at:
      board.present = True
      board.next_status = fake_time.t + 0.1
    orig()
  board.tick = tick
  report = {}
  assert sf.run_hello(t, report, None, wait_board=60) == 0      # health read after the wait: ignition on
  assert report["health"]["ignition_line"] and report["before"]["parked"] is True


def test_wait_board_gives_up(fake_time):
  board, t = setup(fake_time, present=False)
  start = fake_time.t
  with pytest.raises(sf.GuardError, match="no SS_STATUS"):
    sf.run_hello(t, {}, IGN_OFF, wait_board=10)
  assert 10 <= fake_time.t - start < 15 and t.sent == []
