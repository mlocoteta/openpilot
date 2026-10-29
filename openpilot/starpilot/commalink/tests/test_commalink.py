"""Host tests for commalinkd over the TCP stand-in (same bytes as RFCOMM) against a fake local Galaxy."""
import json
import queue
import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from openpilot.starpilot.commalink import daemon


class FakeGalaxy(BaseHTTPRequestHandler):
  onroad = True
  nav_gen = 3
  hud_calls = 0
  writes = []

  def log_message(self, *a):
    pass

  def reply(self, code, obj, cookie=None):
    b = json.dumps(obj).encode()
    self.send_response(code)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(b)))
    if cookie:
      self.send_header("Set-Cookie", f"galaxy_session={cookie}; HttpOnly; Path=/")
    self.end_headers()
    self.wfile.write(b)

  def authed(self):
    if "galaxy_session=tok" not in (self.headers.get("Cookie") or ""):
      self.reply(401, {"error": "Refresh the local Galaxy session"})
      return False
    return True

  def do_GET(self):  # noqa: N802
    if self.path == "/api/auth/session":
      return self.reply(200, {"authenticated": True}, cookie="tok")
    if not self.authed():
      return
    if self.path == "/api/hud":
      FakeGalaxy.hud_calls += 1
      return self.reply(200, {"schemaVersion": 2, "onroad": FakeGalaxy.onroad, "vEgo": 27.0, "pad": "x" * 600,
                              "nav": {"active": True, "gen": FakeGalaxy.nav_gen}})
    if self.path.startswith("/api/hud/route"):
      return self.reply(200, {"gen": FakeGalaxy.nav_gen, "coords": [[i, i] for i in range(900)], "cong": ["low"] * 899})
    if self.path == "/api/settings/pages/slc":
      return self.reply(200, {"page": "slc", "view": "v1", "rows": []})
    return self.reply(404, {"error": "nope"})

  def do_POST(self):  # noqa: N802
    if not self.authed():
      return
    n = int(self.headers.get("Content-Length") or 0)
    body = json.loads(self.rfile.read(n) or b"null")
    FakeGalaxy.writes.append((self.path, body))
    if self.path == "/api/settings/preview":
      return self.reply(200, {"intent": "i1"})
    return self.reply(200, {"ok": True})


class Client:
  def __init__(self, port):
    self.s = socket.create_connection(("127.0.0.1", port), timeout=5)
    self.frames = queue.Queue()
    threading.Thread(target=self._rx, daemon=True).start()

  def _rx(self):
    buf = b""
    try:
      while True:
        c = self.s.recv(65536)
        if not c:
          break
        buf += c
        while b"\n" in buf:
          line, buf = buf.split(b"\n", 1)
          self.frames.put(json.loads(line))
    except OSError:
      pass

  def send(self, obj):
    self.s.sendall(json.dumps(obj).encode() + b"\n")

  def wait(self, t, timeout=5.0, pred=lambda f: True):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
      try:
        f = self.frames.get(timeout=0.2)
      except queue.Empty:
        continue
      if f.get("t") == t and pred(f):
        return f
    raise AssertionError(f"no {t} frame")


class TestCommaLink(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), FakeGalaxy)
    threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    cls.port = s.getsockname()[1]
    s.close()
    cfg = {"enabled": True, "galaxy": f"http://127.0.0.1:{cls.httpd.server_address[1]}"}
    cls.link = daemon.CommaLink(cfg)
    cls.link.role = "tcp"
    threading.Thread(target=daemon.tcp_listener, args=(cls.port, cls.link.incoming), daemon=True).start()
    threading.Thread(target=cls.link.run, daemon=True).start()
    time.sleep(0.3)

  def test_hello_hud_rate_route_ping(self):
    FakeGalaxy.onroad = True
    c = Client(self.port)
    c.send({"t": "hello", "proto": 1, "role": "hu", "version": "test"})
    hello = c.wait("hello")
    self.assertEqual((hello["proto"], hello["role"]), (1, "comma"))
    first = c.wait("hud")
    self.assertEqual(first["d"]["schemaVersion"], 2)
    parts = [c.wait("route", pred=lambda f: f["i"] == i) for i in range(3)]
    self.assertEqual([p["n"] for p in parts], [3, 3, 3])
    self.assertEqual(parts[0]["coords"][-1], parts[1]["coords"][0])        # chunks share the boundary point
    self.assertEqual(sum(len(p["coords"]) for p in parts) - 2, 900)
    self.assertEqual(sum(len(p["cong"]) for p in parts), 899)
    t0, n = time.monotonic(), 0
    while time.monotonic() - t0 < 3.0:
      c.wait("hud")
      n += 1
    self.assertGreaterEqual(n, 10)                                            # ~4 Hz onroad
    self.assertLessEqual(n, 14)
    ping = c.wait("ping", timeout=7)
    c.send({"t": "pong", "ts": ping["ts"]})
    c.s.close()

  def test_requests_allowlist(self):
    c = Client(self.port)
    c.send({"t": "req", "id": 1, "m": "GET", "p": "/api/settings/pages/torque", "b": None})
    self.assertEqual(c.wait("res", pred=lambda f: f["id"] == 1)["s"], 403)
    c.send({"t": "req", "id": 2, "m": "POST", "p": "/api/settings/preview", "b": {"view": "v1", "row": 0, "value": 1}})
    self.assertEqual(c.wait("res", pred=lambda f: f["id"] == 2)["s"], 403)   # view not seen yet
    c.send({"t": "req", "id": 3, "m": "GET", "p": "/api/settings/pages/slc", "b": None})
    self.assertEqual(c.wait("res", pred=lambda f: f["id"] == 3)["b"]["view"], "v1")
    c.send({"t": "req", "id": 4, "m": "POST", "p": "/api/settings/preview", "b": {"view": "v1", "row": 0, "value": 1}})
    self.assertEqual(c.wait("res", pred=lambda f: f["id"] == 4)["b"]["intent"], "i1")
    c.send({"t": "req", "id": 5, "m": "POST", "p": "/api/settings/confirm", "b": {"intent": "i1"}})
    self.assertEqual(c.wait("res", pred=lambda f: f["id"] == 5)["s"], 200)
    c.send({"t": "req", "id": 6, "m": "POST", "p": "/api/navigation/action", "b": {"action": "start"}})
    self.assertEqual(c.wait("res", pred=lambda f: f["id"] == 6)["s"], 403)
    c.send({"t": "req", "id": 7, "m": "POST", "p": "/api/settings/confirm", "b": {"intent": "forged"}})
    self.assertEqual(c.wait("res", pred=lambda f: f["id"] == 7)["s"], 403)
    self.assertNotIn(("/api/settings/confirm", {"intent": "forged"}), FakeGalaxy.writes)
    c.s.close()

  def test_newer_connection_replaces_and_offroad_rate(self):
    FakeGalaxy.onroad = False
    a = Client(self.port)
    a.wait("hud")
    b = Client(self.port)
    b.wait("hello")
    time.sleep(0.5)
    t0, n = time.monotonic(), 0
    while time.monotonic() - t0 < 3.0:
      b.wait("hud")
      n += 1
    self.assertLessEqual(n, 5)                                                # ~1 Hz parked
    a.s.settimeout(3)
    with self.assertRaises((OSError, AssertionError)):
      while True:
        if not a.s.recv(65536):
          raise OSError("closed")
    b.s.close()
    FakeGalaxy.onroad = True


if __name__ == "__main__":
  unittest.main()
