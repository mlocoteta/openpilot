#!/usr/bin/env python3
"""SSV3 board (2016-17 Accord) firmware update over CAN, run ON the comma device.

Wraps the board firmware's own tool (LKAS_EPS_V3 tools/flash_can.py + ssv3_image.py, copied next to
this file) with a panda transport on bus 0 and the guards the car needs. The host side
(projects/openpilot-rebase-maintenance/scripts/ssv3-can-flash.sh) checks comma-at-home, stops openpilot,
runs this, and always restarts openpilot afterwards.

  ssv3_flash.py --hello              snapshot 520/525, HELLO -> bootloader answers -> BOOT -> app back
  ssv3_flash.py --flash app.bin --confirm-flash
                                     full update through flash_can.Flasher (only with the owner's go)
  ssv3_flash.py --info               snapshot only, transmits nothing

Protocol (LKAS_EPS_V3 canboot/boot_protocol.h): 29-bit request 0x18DAE4F1, response 0x18DAF1E4, 8-byte
frames. HELLO [01 'SSV3' 0 0 0]: the application jumps to its CAN bootloader (or answers BUSY while
openpilot requests steering); the bootloader then has a 50 ms HELLO window, answers
[81 status where=1 protocol appValid 0 0 0] and stays (30 s idle timeout back to a valid app).
BOOT [05 'BOOT' 0 0 0] starts the application again. While in the bootloader the stock camera's serial
frames pass through untouched.

Guards (all must hold, else nothing is transmitted):
  * IsOffroad == 1 (param file) and openpilot stopped (no manager.py / pandad process)
  * ignition off, or ignition on and parked: gear P (0x188 or 0x191) and XMISSION_SPEED == 0 (0x158)
  * the board is heard on the bus (SS_STATUS 520), reports firmware >= 3, and is not steering
    (EPS_RAW 524 MODE != STEER, no 0xE4 with the request bit on the bus)
  * nothing else uses the bootloader IDs (listen first)
The panda is kept alive with heartbeats (it drops to SILENT + power save 2 s after the last one) and left
in SILENT afterwards; pandad reconfigures it on restart.
"""
import argparse
import json
import os
import subprocess
import sys
import time

REQUEST_ID = 0x18DAE4F1
RESPONSE_ID = 0x18DAF1E4
SS_STATUS = 520           # 10 Hz: VERSION_NUM, HARDWARE_REV
BOARD_DIAG = 525          # 10 Hz: TX_DROPPED, FIRMWARE_BUILD
EPS_RAW = 524             # MODE 0 passthrough 1 idle 2 steer
STEERING_CONTROL = 0xE4
GEARBOX_AUTO = 0x188      # 392, GEAR_SHIFTER 27|4@0+, 1 = P
GEARBOX_CVT = 0x191       # 401, GEAR_SHIFTER 44|5@0+, 1 = P
ENGINE_DATA = 0x158       # 344, XMISSION_SPEED 7|16@0+ x0.01 kph

CMD_HELLO, CMD_ERASE, CMD_WRITE, CMD_FINISH, CMD_BOOT = 1, 2, 3, 4, 5
STATUS = {0: "ok", 1: "bad request", 2: "out of range", 3: "not erased", 4: "flash error",
          5: "CRC mismatch", 6: "no valid application", 7: "busy: steering is active"}
STATUS_OK, STATUS_BUSY = 0, 7
WHERE_APP, WHERE_BOOTLOADER = 0, 1
MODE_STEER = 2
MIN_FIRMWARE = 3
HEARTBEAT_PERIOD = 0.25   # panda: SILENT + power save after 2 s without a heartbeat (ignition off)
IDLE_TIMEOUT = 30.0       # bootloader -> valid app with no commands

PARAMS_DIR = "/data/params/d"


class GuardError(Exception):
  pass


# ---------- frames ----------

def hello_frame() -> bytes:
  return bytes([CMD_HELLO]) + b"SSV3" + bytes(3)


def boot_frame() -> bytes:
  return bytes([CMD_BOOT]) + b"BOOT" + bytes(3)


def check_byte(frame7: bytes) -> int:
  """WRITE / FINISH check byte: XOR of bytes 0..6, XOR 0xA5 (bootCheckByte)."""
  x = 0xA5
  for b in frame7[:7]:
    x ^= b
  return x


def with_check(frame7: bytes) -> bytes:
  assert len(frame7) == 7
  return bytes(frame7) + bytes([check_byte(frame7)])


def parse_response(data: bytes):
  """[cmd|0x80, status, ...] -> dict, or None for anything that is not a bootloader response."""
  if len(data) != 8 or not data[0] & 0x80:
    return None
  cmd = data[0] & 0x7F
  out = {"cmd": cmd, "status": data[1], "status_text": STATUS.get(data[1], str(data[1])), "raw": data.hex()}
  if cmd == CMD_HELLO:
    out.update(where="bootloader" if data[2] == WHERE_BOOTLOADER else "app", protocol=data[3], app_valid=bool(data[4]))
  return out


# ---------- decoding the car / board frames ----------

def decode_ss_status(d: bytes) -> dict:
  # VERSION_NUM 0|4@1+ (low nibble of byte 0), HARDWARE_REV 7|4@0+ (high nibble of byte 0)
  return {"version": d[0] & 0x0F, "hardware": d[0] >> 4, "raw": d.hex()}


def decode_board_diag(d: bytes) -> dict:
  # TX_DROPPED 7|8@0+ = byte 0, FIRMWARE_BUILD 55|8@0+ = byte 6
  return {"tx_dropped": d[0], "build": d[6], "options": d[5] & 0x0F, "raw": d.hex()} if len(d) == 8 else {"raw": d.hex()}


def eps_raw_mode(d: bytes):
  # MODE 55|2@0+ = byte 6 bits 7..6
  return (d[6] >> 6) & 0x3 if len(d) == 8 else None


def steer_request(d: bytes) -> bool:
  # 0xE4 STEER_TORQUE_REQUEST 23|1@0+ = byte 2 bit 7
  return len(d) >= 3 and bool(d[2] & 0x80)


def gear_is_park(addr: int, d: bytes):
  if addr == GEARBOX_AUTO and len(d) >= 4:
    return (d[3] & 0x0F) == 1
  if addr == GEARBOX_CVT and len(d) >= 6:
    return (d[5] & 0x1F) == 1
  return None


def xmission_speed_kph(d: bytes) -> float:
  return ((d[0] << 8) | d[1]) * 0.01


class BusSnapshot:
  """What one listening window saw on the board's bus."""

  def __init__(self):
    self.counts = {}
    self.last = {}
    self.steer_requested = False
    self.seconds = 0.0

  def add(self, addr: int, data: bytes):
    self.counts[addr] = self.counts.get(addr, 0) + 1
    self.last[addr] = bytes(data)
    if addr == STEERING_CONTROL and steer_request(data):
      self.steer_requested = True

  def rate(self, addr: int) -> float:
    return self.counts.get(addr, 0) / self.seconds if self.seconds > 0 else 0.0

  def board(self) -> dict:
    out = {}
    if SS_STATUS in self.last:
      out.update(decode_ss_status(self.last[SS_STATUS]))
      out["rate_520"] = round(self.rate(SS_STATUS), 1)
    if BOARD_DIAG in self.last:
      diag = decode_board_diag(self.last[BOARD_DIAG])
      out.update({k: v for k, v in diag.items() if k != "raw"}, raw_525=diag["raw"])
      out["rate_525"] = round(self.rate(BOARD_DIAG), 1)
    if EPS_RAW in self.last:
      out["mode"] = eps_raw_mode(self.last[EPS_RAW])
    return out

  def parked(self):
    """True / False from gear + speed, None when the car says nothing (ignition off)."""
    park = None
    for addr in (GEARBOX_AUTO, GEARBOX_CVT):
      if addr in self.last:
        park = gear_is_park(addr, self.last[addr])
        break
    if park is None:
      return None
    speed = xmission_speed_kph(self.last[ENGINE_DATA]) if ENGINE_DATA in self.last else None
    return bool(park and speed is not None and speed < 0.1)

  def summary(self) -> dict:
    return {"seconds": round(self.seconds, 2), "board": self.board(), "parked": self.parked(),
            "steer_requested": self.steer_requested,
            "boot_ids_seen": REQUEST_ID in self.counts or RESPONSE_ID in self.counts,
            "ids": len(self.counts)}


def board_is_normal(snap: BusSnapshot, before: dict) -> bool:
  """The application is running: 520 and 525 at ~10 Hz with the version/build seen before."""
  b = snap.board()
  if b.get("rate_520", 0) < 7 or b.get("rate_525", 0) < 7:
    return False
  # build None = any build (after a flash whose build number is not known up front)
  return (b.get("version") == before.get("version") and b.get("hardware") == before.get("hardware") and
          (before.get("build") is None or b.get("build") == before.get("build")))


# ---------- guards ----------

def read_param(name: str, params_dir: str = PARAMS_DIR):
  try:
    with open(os.path.join(params_dir, name), "rb") as f:
      return f.read().decode(errors="replace").strip()
  except OSError:
    return None


def openpilot_running(pgrep=None) -> list:
  pgrep = pgrep or (lambda pat: subprocess.run(["pgrep", "-f", pat], capture_output=True).returncode == 0)
  return [name for name, pat in (("manager", "manager.py"), ("pandad", "pandad")) if pgrep(pat)]


def check_host_guards(params_dir: str = PARAMS_DIR, pgrep=None):
  if read_param("IsOffroad", params_dir) != "1":
    raise GuardError("IsOffroad is not 1: the car is onroad (or its state is unknown)")
  if read_param("IsOnroad", params_dir) == "1":
    raise GuardError("IsOnroad is 1")
  running = openpilot_running(pgrep)
  if running:
    raise GuardError(f"openpilot is still running ({', '.join(running)}); stop it first")


def check_bus_guards(snap: BusSnapshot, health: dict, require_board: bool = True):
  """Raises GuardError unless it is safe to say HELLO / flash. Returns the board info."""
  ignition = bool(health.get("ignition_line") or health.get("ignition_can"))
  parked = snap.parked()
  if ignition and parked is not True:
    raise GuardError(f"ignition is on and the car is not confirmed parked (gear P, speed 0): parked={parked}")
  if parked is False:
    raise GuardError("the car reports it is not parked (gear not P or moving)")
  if snap.steer_requested:
    raise GuardError("0xE4 with the steer request bit is on the bus: something is commanding steering")
  if snap.summary()["boot_ids_seen"]:
    raise GuardError("something else is already using 0x18DAE4F1 / 0x18DAF1E4 on this bus")
  board = snap.board()
  if require_board:
    if "version" not in board:
      raise GuardError("no SS_STATUS (520) from the board: wrong bus, or the board is unpowered "
                       "(ignition off?). Turn the ignition ON with the engine off, in P, and rerun.")
    if board["version"] < MIN_FIRMWARE:
      raise GuardError(f"the board reports firmware {board['version']}; the CAN bootloader needs firmware 3")
    if board.get("mode") == MODE_STEER:
      raise GuardError("the board reports MODE STEER")
  return board


# ---------- panda transport ----------

class PandaBus:
  """Panda on one bus, kept awake with heartbeats. send()/recv_all() match flash_can's transport API."""

  def __init__(self, bus: int = 0, panda=None):
    if panda is None:
      from panda import Panda
      panda = Panda()
    self.panda = panda
    self.bus = bus
    self._last_hb = 0.0
    self.heartbeat(force=True)
    try:
      self.panda.set_power_save(0)
    except Exception:
      pass
    self.set_mode("noOutput")     # receive + ACK, transmit nothing
    self.panda.can_clear(0xFFFF)

  def set_mode(self, name: str, param: int = 0):
    from opendbc.car.structs import CarParams
    mode = {"silent": CarParams.SafetyModel.silent, "noOutput": CarParams.SafetyModel.noOutput,
            "elm327": CarParams.SafetyModel.elm327}[name]
    self.panda.set_safety_mode(mode, param)

  def enable_tx(self):
    # ELM327: 8-byte frames to (addr & 0x1FFF00FF) == 0x18DA00F1 only. Param 1: keep bus 1 off the OBD port.
    self.set_mode("elm327", 1)

  def heartbeat(self, force: bool = False):
    now = time.monotonic()
    if force or now - self._last_hb >= HEARTBEAT_PERIOD:
      self.panda.send_heartbeat(engaged=False)
      self._last_hb = now

  def health(self) -> dict:
    return self.panda.health()

  def send(self, data: bytes):
    self.heartbeat()
    self.panda.can_send(REQUEST_ID, bytes(data), self.bus)

  def recv_all(self):
    self.heartbeat()
    for addr, data, bus in self.panda.can_recv():
      if bus == self.bus:
        yield addr, bytes(data)

  def close(self):
    try:
      self.set_mode("silent")
    except Exception:
      pass


def listen(transport, seconds: float, clock=None, idle=lambda: time.sleep(0.002)) -> BusSnapshot:
  clock = clock or time.monotonic
  snap = BusSnapshot()
  start = clock()
  while clock() - start < seconds:
    got = False
    for addr, data in transport.recv_all():
      snap.add(addr, data)
      got = True
    if not got:
      idle()
  snap.seconds = clock() - start
  return snap


def responses(transport, store=None):
  out = []
  for addr, data in transport.recv_all():
    if store is not None:
      store.add(addr, data)
    if addr == RESPONSE_ID and len(data) == 8:
      r = parse_response(data)
      if r:
        out.append(r)
  return out


def hello(transport, timeout: float = 2.0, clock=None) -> dict:
  """Repeat HELLO (every ~5 ms, like flash_can.enter_bootloader) until the bootloader answers.
  Returns the response dict; status BUSY = the application refused (steering)."""
  clock = clock or time.monotonic   # looked up per call (tests patch it)
  deadline = clock() + timeout
  sent = 0
  while clock() < deadline:
    transport.send(hello_frame())
    sent += 1
    end = clock() + 0.005
    while clock() < end:
      for r in responses(transport):
        if r["cmd"] != CMD_HELLO:
          continue
        if r["status"] == STATUS_BUSY or (r["status"] == STATUS_OK and r.get("where") == "bootloader"):
          r["hellos_sent"] = sent
          return r
  raise TimeoutError(f"no HELLO answer after {sent} frames in {timeout:.1f} s")


def boot(transport, timeout: float = 0.2, retries: int = 5, clock=None) -> dict:
  clock = clock or time.monotonic   # looked up per call (tests patch it)
  for _ in range(retries):
    transport.send(boot_frame())
    deadline = clock() + timeout
    while clock() < deadline:
      for r in responses(transport):
        if r["cmd"] == CMD_BOOT:
          return r
  raise TimeoutError("no response to BOOT")


def wait_for_app(transport, before: dict, max_wait: float, step: float = 1.0, clock=None):
  """Listen in `step` windows until the application is back (520/525 ~10 Hz, same version/build)."""
  clock = clock or time.monotonic   # looked up per call (tests patch it)
  start = clock()
  snaps = []
  while clock() - start < max_wait:
    snap = listen(transport, step, clock=clock)
    snaps.append(snap.board())
    if board_is_normal(snap, before):
      return True, round(clock() - start, 1), snaps[-1]
  return False, round(clock() - start, 1), snaps[-1] if snaps else {}


# ---------- modes ----------

def run_hello(transport, report: dict, health: dict):
  pre = listen(transport, 1.0)
  report["before"] = pre.summary()
  report["health"] = {k: health.get(k) for k in ("ignition_line", "ignition_can", "voltage", "safety_mode", "controls_allowed")}
  before = check_bus_guards(pre, health)
  report["guards"] = "passed"

  transport.enable_tx()
  try:
    try:
      r = hello(transport)
    except TimeoutError as e:
      report["hello"] = {"answer": None, "error": str(e)}
      transport.set_mode("noOutput")
      ok, waited, board = wait_for_app(transport, before, 3.0)
      report["after"] = {"app_normal": ok, "waited_s": waited, "board": board}
      return 2
    report["hello"] = r
    if r["status"] == STATUS_BUSY:
      transport.set_mode("noOutput")
      ok, waited, board = wait_for_app(transport, before, 3.0)
      report["after"] = {"app_normal": ok, "waited_s": waited, "board": board}
      return 3
    # in the bootloader now: ask it to start the application
    try:
      report["boot"] = boot(transport)
    except TimeoutError as e:
      report["boot"] = {"error": str(e)}
  finally:
    transport.set_mode("noOutput")

  ok, waited, board = wait_for_app(transport, before, IDLE_TIMEOUT + 8.0)
  report["after"] = {"app_normal": ok, "waited_s": waited, "board": board}
  if not ok:
    report["STUCK"] = ("board not back in its application after the bootloader idle timeout: "
                       "recovery is the USB DFU bootloader (tools/flash_usb.py), by hand")
    return 4
  return 0


def run_flash(transport, report: dict, health: dict, firmware: str, tools_dir: str):
  sys.path.insert(0, tools_dir)
  import flash_can   # noqa: E402  (LKAS_EPS_V3 tools/, copied next to this file)
  import ssv3_image  # noqa: E402
  app = ssv3_image.load_app(firmware)
  report["image"] = {"path": firmware, "bytes": len(app), "crc": f"{ssv3_image.stm32_crc(app):08x}"}
  pre = listen(transport, 1.0)
  report["before"] = pre.summary()
  before = check_bus_guards(pre, health)
  report["guards"] = "passed"
  transport.enable_tx()
  try:
    f = flash_can.Flasher(transport, log=lambda m: report.setdefault("log", []).append(m))
    t0 = time.monotonic()
    f.flash(app)
    report["flash_s"] = round(time.monotonic() - t0, 1)
  finally:
    transport.set_mode("noOutput")
  expected = {"version": before["version"], "hardware": before["hardware"], "build": report.get("expected_build")}
  ok, waited, board = wait_for_app(transport, expected, 10.0)
  report["after"] = {"app_normal": ok, "waited_s": waited, "board": board}
  if not ok:
    report["STUCK"] = "the new application is not reporting as expected: check it; recovery is USB DFU, by hand"
    return 4
  return 0


def main(argv=None):
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  mode = ap.add_mutually_exclusive_group(required=True)
  mode.add_argument("--info", action="store_true")
  mode.add_argument("--hello", action="store_true")
  mode.add_argument("--flash", metavar="BIN")
  ap.add_argument("--confirm-flash", action="store_true", help="required with --flash")
  ap.add_argument("--expected-build", type=int, help="FIRMWARE_BUILD the new image reports")
  ap.add_argument("--bus", type=int, default=0)
  ap.add_argument("--report", default="-")
  ap.add_argument("--tools-dir", default=os.path.dirname(os.path.abspath(__file__)))
  args = ap.parse_args(argv)
  if args.flash and not args.confirm_flash:
    sys.exit("--flash needs --confirm-flash (owner's explicit go)")

  report = {"mode": "info" if args.info else "hello" if args.hello else "flash", "bus": args.bus,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "expected_build": args.expected_build}
  rc = 1
  transport = None
  try:
    check_host_guards()
    transport = PandaBus(args.bus)
    health = transport.health()
    if args.info:
      snap = listen(transport, 1.0)
      report["before"] = snap.summary()
      rc = 0
    elif args.hello:
      rc = run_hello(transport, report, health)
    else:
      rc = run_flash(transport, report, health, args.flash, args.tools_dir)
  except GuardError as e:
    report["refused"] = str(e)
    rc = 5
  except Exception as e:  # report everything, the host restores openpilot either way
    report["error"] = f"{type(e).__name__}: {e}"
    rc = 1
  finally:
    if transport is not None:
      transport.close()
  report["rc"] = rc
  text = json.dumps(report, indent=1, default=str)
  if args.report == "-":
    print(text)
  else:
    with open(args.report, "w") as f:
      f.write(text + "\n")
    print(text)
  return rc


if __name__ == "__main__":
  sys.exit(main())
