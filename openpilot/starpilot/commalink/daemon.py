#!/usr/bin/env python3
"""CommaLink: Bluetooth Classic RFCOMM link from the comma to the Accord head unit (COMMALINK.md v1).

The head unit (Android 4.2, Clarion/Alps stack) has no BLE and can't reach the comma's Wi-Fi in the car, so this daemon
pushes the Galaxy /api/hud body to it over RFCOMM (one JSON object per line) and relays an allowlisted set of Galaxy
requests back. It reads everything through the local Galaxy HTTP server (127.0.0.1:8082, direct-local session), so
Galaxy's own owners (parked gating, preview/confirm, generation checks) still decide every write.

Roles (config "role"):
  server  the comma registers an RFCOMM profile (BlueZ ProfileManager1, SDP UUID ...00b1, channel picked by BlueZ) and
          the head unit connects as a client (createRfcommSocketToServiceRecord). Default.
  client  the comma looks the UUID up in the head unit's SDP (never a hard-coded channel) and connects to its listener.
  auto    both: the profile stays registered and client attempts run with backoff while no session is up.
One session at a time; a newer connection replaces the old one.

Bluetooth etiquette: never changes power/discoverable/pairable/class, never registers an agent, never pairs, never
scans. It does not take /data/starpilot/bluetooth-owner.lock (StarPort holds it for as long as AA runs, and an
RFCOMM DLC changes no adapter state). The head unit must already be bonded (one-time Honda "Add Bluetooth Device").

Enabled only when /data/starpilot/commalink.json exists with "enabled": true (see process_config.commalink_enabled).
Status for tests/diagnostics: /tmp/commalink-status.json every 5 s.
"""

from __future__ import annotations

import json
import os
import queue
import socket
import struct
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, unquote

CONFIG_PATH = "/data/starpilot/commalink.json"
STATUS_PATH = "/tmp/commalink-status.json"
UUID_COMMALINK = uuid.UUID("b0771e00-c0aa-4d1a-9b2e-0000000000b1")
GALAXY = "http://127.0.0.1:8082"
MAX_LINE = 65536
ROUTE_CHUNK = 400
HONDA_HU_NAMES = ("HandsFreeLink",)   # what the 2016-17 Accord Display Audio calls itself over BT

AF_BLUETOOTH, BTPROTO_L2CAP, BTPROTO_RFCOMM = 31, 0, 3
SOL_BLUETOOTH, BT_SECURITY = 274, 4
BT_SECURITY_MEDIUM = 2                # authenticated + encrypted with the existing bond; never triggers a new pairing on our side
SDP_PSM = 1
RFCOMM_UUID16 = b"\x19\x00\x03"

ALLOWED_PAGES = ("profiles", "conditional", "slc", "lane_change", "curve", "sounds", "sentry")
NAV_ACTIONS = ("clear", "select", "selectRoute")


def log(*a) -> None:
  print(time.strftime("%H:%M:%S"), "commalink:", *a, flush=True)


def load_config(path: str = CONFIG_PATH) -> dict:
  try:
    with open(path) as f:
      cfg = json.load(f)
  except (OSError, ValueError):
    return {"enabled": False}
  return cfg if isinstance(cfg, dict) else {"enabled": False}


# ------------------------------------------------------------------ Galaxy (local HTTP)

class Galaxy:
  def __init__(self, base: str = GALAXY):
    self.base, self.cookie, self.lock = base, None, threading.Lock()

  def _session(self) -> None:
    with urllib.request.urlopen(urllib.request.Request(self.base + "/api/auth/session"), timeout=2) as r:
      for v in r.headers.get_all("Set-Cookie") or []:
        if "galaxy_session=" in v:
          self.cookie = v.split("galaxy_session=", 1)[1].split(";", 1)[0]

  def call(self, method: str, path: str, body=None, timeout: float = 2.0) -> tuple[int, bytes]:
    for attempt in range(2):
      with self.lock:
        if self.cookie is None:
          self._session()
        cookie = self.cookie
      data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
      req = urllib.request.Request(self.base + path, data=data, method=method,
                                   headers={"Accept": "application/json", "Content-Type": "application/json",
                                            "Cookie": f"galaxy_session={cookie}"})
      try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
          return r.status, r.read(1 << 20)
      except urllib.error.HTTPError as e:
        if e.code == 401 and attempt == 0:
          with self.lock:
            self.cookie = None
          continue
        return e.code, e.read(1 << 20)
    return 401, b'{"error":"no local Galaxy session"}'


# ------------------------------------------------------------------ allowlist (COMMALINK.md section 2, same as the HU side)

class Allow:
  def __init__(self):
    self.view_page: dict[str, str] = {}
    self.intent_page: dict[str, str] = {}

  def check(self, method: str, path: str, body) -> str | None:
    if not path.startswith("/") or path.startswith("//") or len(path) > 512 or any(c in path for c in "\r\n\\ "):
      return "not a local Galaxy path"
    parts = urlsplit(path)
    p = parts.path
    if parts.query and p != "/api/hud/route":
      return "query only allowed on /api/hud/route"
    if method == "GET":
      if p.startswith("/api/settings/pages/"):
        return None if unquote(p[len("/api/settings/pages/"):]) in ALLOWED_PAGES else "page not on the CommaLink allowlist"
      return None if p in ("/api/navigation/status", "/api/perf", "/api/hud/route") else "not on the CommaLink allowlist"
    if method == "POST":
      if p == "/api/settings/preview":
        v = body.get("view") if isinstance(body, dict) else None
        return None if isinstance(v, str) and v in self.view_page else "settings view not from an allowlisted page"
      if p == "/api/settings/confirm":
        if not isinstance(body, dict):
          return "no body"
        if "page" in body and body["page"] not in ALLOWED_PAGES:
          return "page not on the CommaLink allowlist"
        i = body.get("intent")
        return None if isinstance(i, str) and i in self.intent_page else "intent not from an allowlisted page"
      if p == "/api/navigation/action":
        a = body.get("action") if isinstance(body, dict) else None
        return None if a in NAV_ACTIONS else "navigation action not allowed"
      return None if p == "/api/navigation/search" else "not on the CommaLink allowlist"
    return "not on the CommaLink allowlist"

  def saw(self, method: str, path: str, body, status: int, reply) -> None:
    """Remember which allowlisted page a Galaxy view id / preview intent came from."""
    if status != 200 or not isinstance(reply, dict):
      return
    p = urlsplit(path).path
    if method == "GET" and p.startswith("/api/settings/pages/") and isinstance(reply.get("view"), str):
      self._put(self.view_page, reply["view"], unquote(p[len("/api/settings/pages/"):]))
    elif p == "/api/settings/preview" and isinstance(reply.get("intent"), str) and isinstance(body, dict):
      self._put(self.intent_page, reply["intent"], self.view_page.get(body.get("view"), ""))

  @staticmethod
  def _put(d: dict, k: str, v: str) -> None:
    if len(d) > 256:
      d.pop(next(iter(d)))
    d[k] = v


# ------------------------------------------------------------------ Bluetooth: SDP lookup + client connect

def bt_socket(proto: int) -> socket.socket:
  kind = socket.SOCK_SEQPACKET if proto == BTPROTO_L2CAP else socket.SOCK_STREAM
  return socket.socket(AF_BLUETOOTH, kind, proto)


def sdp_channels(address: str, service: uuid.UUID, timeout: float = 8.0) -> list[int]:
  """RFCOMM channels of the records that carry `service` in the peer's SDP (ServiceSearchAttributeRequest)."""
  s = bt_socket(BTPROTO_L2CAP)
  try:
    s.settimeout(timeout)
    s.connect((address, SDP_PSM))
    pattern = b"\x35\x11\x1c" + service.bytes
    attrs, cont, deadline = bytearray(), b"", time.monotonic() + timeout
    for tid in range(16):
      params = pattern + struct.pack(">H", 0x03F0) + b"\x35\x05\x0a" + struct.pack(">I", 0x0000FFFF) + bytes([len(cont)]) + cont
      s.settimeout(max(0.2, deadline - time.monotonic()))
      s.send(struct.pack(">BHH", 0x06, tid, len(params)) + params)
      pdu = s.recv(4096)
      pdu_id, _tid, length = struct.unpack(">BHH", pdu[:5])
      body = pdu[5:5 + length]
      if pdu_id != 0x07:
        raise OSError(f"SDP error PDU {pdu_id:#04x} {body[:2].hex()}")
      count = struct.unpack(">H", body[:2])[0]
      attrs += body[2:2 + count]
      cont = body[3 + count:3 + count + body[2 + count]]
      if not cont:
        break
  finally:
    s.close()
  out, start = [], 0
  while (i := attrs.find(RFCOMM_UUID16, start)) >= 0:
    if i + 4 < len(attrs) and attrs[i + 3] == 0x08:
      out.append(attrs[i + 4])
    start = i + 3
  return out


def rfcomm_connect(address: str, channel: int, timeout: float = 10.0) -> socket.socket:
  s = bt_socket(BTPROTO_RFCOMM)
  try:
    s.setsockopt(SOL_BLUETOOTH, BT_SECURITY, struct.pack("BB", BT_SECURITY_MEDIUM, 0))
    s.settimeout(timeout)
    s.connect((address, channel))
    return s
  except BaseException:
    s.close()
    raise


def paired_head_units() -> list[str]:
  """Bonded devices that look like the Honda head unit (bluetoothctl, read-only)."""
  try:
    out = subprocess.run(["bluetoothctl", "devices", "Paired"], capture_output=True, text=True, timeout=5).stdout
  except (OSError, subprocess.SubprocessError):
    return []
  found = []
  for line in out.splitlines():
    parts = line.split(" ", 2)
    if len(parts) == 3 and parts[0] == "Device" and parts[2].strip() in HONDA_HU_NAMES:
      found.append(parts[1])
  return found


# ------------------------------------------------------------------ Bluetooth: server role via BlueZ ProfileManager1

def vendor_dbus() -> None:
  try:
    import dbus_next  # noqa: F401
  except ImportError:   # vendored beside the Galaxy phone bridge; nothing is installed on the comma
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "galaxy_bluetooth", "vendor"))


def profile_interface(incoming: "queue.Queue[tuple[socket.socket, str]]"):
  """org.bluez.Profile1 object: bluetoothd hands each accepted RFCOMM connection over as an fd."""
  vendor_dbus()
  from dbus_next.service import ServiceInterface, method

  class Profile(ServiceInterface):
    def __init__(self):
      super().__init__("org.bluez.Profile1")

    @method()
    def Release(self):  # noqa: N802
      pass

    @method()
    def NewConnection(self, device: "o", fd: "h", properties: "a{sv}"):  # noqa: F821,N802
      addr = device.rsplit("dev_", 1)[-1].replace("_", ":")
      sock = socket.socket(fileno=os.dup(fd))
      os.close(fd)
      log("incoming RFCOMM from", addr)
      incoming.put((sock, addr))

    @method()
    def RequestDisconnection(self, device: "o"):  # noqa: F821,N802
      pass

  return Profile()


class ProfileServer(threading.Thread):
  """Registers the CommaLink SPP record with bluetoothd; incoming connections arrive as fds via Profile1.NewConnection."""

  def __init__(self, incoming: "queue.Queue[tuple[socket.socket, str]]", channel: int = 0):
    super().__init__(name="commalink-profile", daemon=True)
    self.incoming, self.channel = incoming, channel
    self.registered = threading.Event()
    self.error: str | None = None

  def run(self) -> None:
    import asyncio
    try:
      asyncio.run(self._main())
    except Exception as e:  # noqa: BLE001
      self.error = repr(e)
      log("profile server stopped:", self.error)

  async def _main(self) -> None:
    vendor_dbus()
    from dbus_next import BusType, Variant
    from dbus_next.aio import MessageBus

    profile = profile_interface(self.incoming)
    bus = await MessageBus(bus_type=BusType.SYSTEM, negotiate_unix_fd=True).connect()
    path = "/org/starpilot/commalink"
    bus.export(path, profile)
    intro = await bus.introspect("org.bluez", "/org/bluez")
    mgr = bus.get_proxy_object("org.bluez", "/org/bluez", intro).get_interface("org.bluez.ProfileManager1")
    opts = {"Name": Variant("s", "CommaLink"), "Role": Variant("s", "server"),
            "RequireAuthentication": Variant("b", True), "RequireAuthorization": Variant("b", False),
            "AutoConnect": Variant("b", False)}
    if self.channel:
      opts["Channel"] = Variant("q", self.channel)
    await mgr.call_register_profile(path, str(UUID_COMMALINK), opts)
    self.registered.set()
    log("profile registered", UUID_COMMALINK)
    await bus.wait_for_disconnect()
    raise RuntimeError("system bus disconnected")


# ------------------------------------------------------------------ one session

class Session:
  def __init__(self, sock: socket.socket, via: str, galaxy: Galaxy, allow: Allow, stats: dict, version: str, dongle):
    self.sock, self.via, self.g, self.allow, self.stats = sock, via, galaxy, allow, stats
    self.version, self.dongle = version, dongle
    self.out: "queue.Queue[bytes]" = queue.Queue(maxsize=32)
    self.closed = threading.Event()
    self.last_rx = time.monotonic()
    self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="commalink-req")
    self.inflight, self.inflight_lock = 0, threading.Lock()
    self.route_gen, self.route_retry = None, 0.0
    self.rtts: "deque[int]" = deque(maxlen=240)   # last ~20 min of 5 s pings

  def close(self) -> None:
    if not self.closed.is_set():
      self.closed.set()
      try:
        self.sock.shutdown(socket.SHUT_RDWR)
      except OSError:
        pass
      self.sock.close()
      self.pool.shutdown(wait=False)

  def queue_frame(self, obj: dict) -> bool:
    return self.queue_line(json.dumps(obj, separators=(",", ":")).encode() + b"\n")

  def queue_line(self, line: bytes) -> bool:
    if len(line) > MAX_LINE:               # COMMALINK.md section 2: max 64 KiB per line, the HU drops longer ones
      self.stats["oversize"] = self.stats.get("oversize", 0) + 1
      return False
    try:
      self.out.put_nowait(line)
      return True
    except queue.Full:
      self.stats["dropped"] += 1
      return False

  def _write(self, data: bytes) -> None:
    self.sock.settimeout(3.0)              # peer stopped reading for 3 s = dead link
    self.sock.sendall(data)
    self.stats["bytesTx"] += len(data)

  def reader(self) -> None:
    buf = b""
    try:
      self.sock.settimeout(None)
      while not self.closed.is_set():
        chunk = self.sock.recv(4096)
        if not chunk:
          break
        self.last_rx = time.monotonic()
        buf += chunk
        while b"\n" in buf:
          line, buf = buf.split(b"\n", 1)
          self.handle(line)
        if len(buf) > MAX_LINE:
          buf = b""
    except OSError:
      pass
    finally:
      self.closed.set()

  def handle(self, line: bytes) -> None:
    try:
      f = json.loads(line)
    except ValueError:
      return
    if not isinstance(f, dict):
      return
    t = f.get("t")
    if t == "hello":
      log("HU hello", f.get("role"), f.get("version"))
      self.stats["huHello"] = {k: f.get(k) for k in ("role", "version", "proto")}
    elif t == "ping":
      self.queue_frame({"t": "pong", "ts": f.get("ts")})
    elif t == "pong" and isinstance(f.get("ts"), int):
      rtt = int(time.time() * 1000) - f["ts"]
      if 0 <= rtt < 60000:
        self.rtts.append(rtt)
        r = sorted(self.rtts)
        self.stats.update(pongs=self.stats["pongs"] + 1, rttLastMs=rtt, rttP50Ms=r[len(r) // 2],
                          rttP95Ms=r[min(len(r) - 1, (len(r) * 95) // 100)])
    elif t == "req":
      rid, m, p, b = f.get("id"), f.get("m"), f.get("p"), f.get("b")
      why = self.allow.check(m, p, b) if isinstance(p, str) and m in ("GET", "POST") else "bad request"
      if why is not None:
        self.queue_frame({"t": "res", "id": rid, "s": 403, "b": {"error": why}})
      else:
        with self.inflight_lock:
          busy = self.inflight >= 4
          if not busy:
            self.inflight += 1
        if busy:
          self.queue_frame({"t": "res", "id": rid, "s": 429, "b": {"error": "comma busy"}})
        else:
          self.pool.submit(self._relay, rid, m, p, b)

  def _relay(self, rid, m, p, b) -> None:
    try:
      s, raw = self.g.call(m, p, b if m == "POST" else None, timeout=6.0)
      try:
        reply = json.loads(raw) if raw else None
      except ValueError:
        reply = {"error": "comma sent a non-JSON reply"}
      self.allow.saw(m, p, b, s, reply)
      line = json.dumps({"t": "res", "id": rid, "s": s, "b": reply}, separators=(",", ":")).encode() + b"\n"
      if len(line) > MAX_LINE:
        self.stats["oversize"] = self.stats.get("oversize", 0) + 1
        self.queue_frame({"t": "res", "id": rid, "s": 502, "b": {"error": "reply over the 64 KiB CommaLink line limit"}})
      else:
        self.queue_line(line)
    except Exception as e:  # noqa: BLE001
      self.queue_frame({"t": "res", "id": rid, "s": 502, "b": {"error": f"comma Galaxy unavailable: {type(e).__name__}"}})
    finally:
      with self.inflight_lock:
        self.inflight -= 1

  def send_route(self, gen) -> None:
    if time.monotonic() < self.route_retry:
      return
    s, raw = self.g.call("GET", f"/api/hud/route?gen={gen}")
    if s != 200:
      self.route_retry = time.monotonic() + 10.0   # route endpoint not on this build yet: the HU just has no line
      return
    j = json.loads(raw)
    coords, cong = j.get("coords") or [], j.get("cong")
    n = max(1, -(-max(len(coords) - 1, 1) // (ROUTE_CHUNK - 1)))
    for i in range(n):
      a, e = i * (ROUTE_CHUNK - 1), min(len(coords), i * (ROUTE_CHUNK - 1) + ROUTE_CHUNK)
      frame = {"t": "route", "gen": j.get("gen", gen), "i": i, "n": n, "coords": coords[a:e]}
      if isinstance(cong, list):
        frame["cong"] = cong[a:max(a, e - 1)]
      self.queue_frame(frame)
    self.route_gen = gen

  def run(self) -> str:
    """Blocks until the link drops. Returns the reason."""
    rd = threading.Thread(target=self.reader, name="commalink-rx", daemon=True)
    rd.start()
    self.queue_frame({"t": "hello", "proto": 1, "role": "comma", "version": self.version, "dongle": self.dongle})
    next_hud, last_ping, last_hud, onroad = 0.0, 0.0, time.monotonic(), False
    try:
      while not self.closed.is_set():
        now = time.monotonic()
        if now >= next_hud:
          next_hud = now + (0.25 if onroad else 1.0)
          try:
            s, raw = self.g.call("GET", "/api/hud", timeout=1.5)
          except Exception as e:  # noqa: BLE001
            s, raw = 0, b""
            self.stats["lastGalaxyError"] = type(e).__name__
          if s == 200 and raw:
            body = raw.strip()
            if b"\n" in body:
              body = json.dumps(json.loads(body), separators=(",", ":")).encode()
            if self.queue_line(b'{"t":"hud","d":' + body + b"}\n"):
              self.stats["hudFrames"] += 1
              last_hud = now
            try:
              d = json.loads(body)
              onroad = bool(d.get("onroad"))
              nav = d.get("nav") or {}
              if nav.get("active") and nav.get("gen") is not None and nav.get("gen") != self.route_gen:
                self.send_route(nav.get("gen"))
            except (ValueError, AttributeError, OSError):
              pass
        # the HU answers pong: proves the return path while hud frames flow (every 5 s). Without hud frames
        # (Galaxy down/slow) ping at 1 Hz so the HU's 3 s watchdog still sees the link (COMMALINK.md: >= 1 Hz).
        if now - last_ping >= 5.0 or (now - last_hud >= 1.0 and now - last_ping >= 1.0):
          last_ping = now
          self.queue_frame({"t": "ping", "ts": int(time.time() * 1000)})
          self.stats["pingsSent"] += 1
        try:
          data = self.out.get(timeout=max(0.01, min(next_hud - time.monotonic(), 1.0)))
        except queue.Empty:
          continue
        self._write(data)
        if time.monotonic() - self.last_rx > 15.0:  # HU sends hello/pong; 15 s of silence with writes OK = half-open, drop
          return "no reply from the head unit for 15 s"
      return "peer closed"
    except OSError as e:
      return f"write failed: {e!r}"
    finally:
      self.close()


# ------------------------------------------------------------------ supervisor

class CommaLink:
  def __init__(self, cfg: dict):
    self.cfg = cfg
    self.role = cfg.get("role", "server")
    self.galaxy, self.allow = Galaxy(cfg.get("galaxy", GALAXY)), Allow()
    self.incoming: "queue.Queue[tuple[socket.socket, str]]" = queue.Queue()
    self.stats = {"role": self.role, "sessions": 0, "hudFrames": 0, "bytesTx": 0, "dropped": 0, "connectFails": 0,
                  "lastError": None, "state": "starting", "via": None, "since": None, "huHello": None,
                  "pingsSent": 0, "pongs": 0, "rttLastMs": None, "rttP50Ms": None, "rttP95Ms": None}
    self.version = self._version()
    self.dongle = self._dongle()

  @staticmethod
  def _version() -> str:
    try:
      return subprocess.run(["git", "-C", "/data/openpilot", "rev-parse", "--short", "HEAD"], capture_output=True,
                            text=True, timeout=5).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
      return "unknown"

  @staticmethod
  def _dongle():
    try:
      from openpilot.common.params import Params
      v = Params().get("DongleId")
      return v.decode() if isinstance(v, bytes) else v
    except Exception:  # noqa: BLE001
      return None

  def write_status(self) -> None:
    try:
      tmp = STATUS_PATH + ".tmp"
      with open(tmp, "w") as f:
        json.dump(dict(self.stats, at=time.time()), f)
      os.replace(tmp, STATUS_PATH)
    except OSError:
      pass

  def try_client(self) -> tuple[socket.socket, str] | None:
    hus = [self.cfg["hu"]] if self.cfg.get("hu") else paired_head_units()
    for addr in hus:
      try:
        chans = sdp_channels(addr, UUID_COMMALINK)
        if not chans:
          self.stats["lastError"] = f"{addr}: CommaLink not in SDP"
          continue
        return rfcomm_connect(addr, chans[0]), f"client {addr} ch{chans[0]}"
      except OSError as e:
        self.stats["lastError"] = f"{addr}: {e!r}"
    return None

  def run(self) -> None:
    if self.role in ("server", "auto"):
      ProfileServer(self.incoming, int(self.cfg.get("channel", 0))).start()
    backoff, next_try, last_status = 5.0, 0.0, 0.0
    pending: tuple[socket.socket, str] | None = None
    while True:
      if pending is None:
        try:
          pending = self.incoming.get(timeout=1.0)
          pending = (pending[0], f"server {pending[1]}")
        except queue.Empty:
          pass
      if pending is None and self.role in ("client", "auto") and time.monotonic() >= next_try:
        pending = self.try_client()
        if pending is None:
          self.stats["connectFails"] += 1
          next_try, backoff = time.monotonic() + backoff, min(backoff * 2, 30.0)
      if time.monotonic() - last_status > 5:
        last_status = time.monotonic()
        self.write_status()
      if pending is None:
        self.stats["state"] = "waiting"
        continue
      sock, via = pending
      pending = None
      backoff, next_try = 5.0, 0.0
      self.stats.update(state="connected", via=via, since=time.time(), sessions=self.stats["sessions"] + 1)
      self.write_status()
      log("session up", via)
      sess = Session(sock, via, self.galaxy, self.allow, self.stats, self.version, self.dongle)
      t = threading.Thread(target=lambda: self.stats.__setitem__("lastError", sess.run()), name="commalink-session", daemon=True)
      t.start()
      while t.is_alive():                 # a newer incoming connection replaces this one
        try:
          pending = self.incoming.get(timeout=1.0)
          pending = (pending[0], f"server {pending[1]}")
          log("newer connection, replacing", via)
          sess.close()
          break
        except queue.Empty:
          if time.monotonic() - last_status > 5:
            last_status = time.monotonic()
            self.write_status()
      t.join(timeout=5)
      log("session down", via, self.stats.get("lastError"))
      self.stats.update(state="waiting", via=None)
      next_try = time.monotonic() + 2.0


def tcp_listener(port: int, incoming: "queue.Queue[tuple[socket.socket, str]]") -> None:
  """Host/emulator stand-in for the RFCOMM server role (same bytes)."""
  ls = socket.create_server(("0.0.0.0", port), reuse_port=False)
  while True:
    s, a = ls.accept()
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    incoming.put((s, f"tcp:{a[0]}"))


def main(argv=None) -> None:
  import argparse
  ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
  ap.add_argument("--config", default=os.environ.get("COMMALINK_CONFIG", CONFIG_PATH))
  ap.add_argument("--role", choices=("server", "client", "auto"), help="override config role (hand-run tests)")
  ap.add_argument("--hu", help="head-unit BT address (default: bonded HandsFreeLink devices)")
  ap.add_argument("--galaxy", help="Galaxy base URL (default http://127.0.0.1:8082)")
  ap.add_argument("--tcp-listen", type=int, help="host test: accept TCP instead of RFCOMM (no Bluetooth)")
  ap.add_argument("--force", action="store_true", help="run even if the config file is missing/disabled")
  a = ap.parse_args(argv)
  cfg = load_config(a.config)
  if not (cfg.get("enabled") or a.force):
    log("disabled (no", a.config, "with enabled: true)")
    while not load_config(a.config).get("enabled"):
      time.sleep(30)
    cfg = load_config(a.config)
  for k in ("role", "hu", "galaxy"):
    if getattr(a, k):
      cfg[k] = getattr(a, k)
  try:
    os.nice(10)
  except OSError:
    pass
  link = CommaLink(cfg)
  if a.tcp_listen:
    link.role = link.stats["role"] = "tcp"
    threading.Thread(target=tcp_listener, args=(a.tcp_listen, link.incoming), daemon=True).start()
  link.run()


if __name__ == "__main__":
  main()
