#!/usr/bin/env python3
"""Virtual touchscreen for a comma device whose digitizer has failed.

Two jobs:

1. Exist. comma's raylib backend ("magic") opens /dev/input/event2 and treats a
   missing touch device as FATAL:

       WARNING: COMMA: Failed to open touch device at /dev/input/event2
       FATAL:   COMMA: Failed to initialize touch device

   When the digitizer dies, fts_ts never registers, event2 never appears, magic
   exits 1, and every UI process then dies with "COMMA: Failed to connect to
   magic" -> no DRM -> SIGSEGV. The panel and GPU are fine; magic logs a
   successful gbm_create_device and EGL 1.5 right before aborting on touch.

2. Inject. Serves a small HTTP API so taps from a browser become real touch
   events on the device, restoring touch input over the network.

A uinput device disappears when its fd closes, so this process must stay alive.
"""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

from evdev import UInput, AbsInfo, ecodes as e

# Screen (landscape) space -- what the HTTP API and the web page speak.
WIDTH, HEIGHT = 2160, 1080

# The digitizer this replaces is PORTRAIT-native, and raylib's COMMA backend
# rotates it in PollInputEvents. Decoded from _raylib_cffi_comma.abi3.so
# (InitPlatform reads .../gpio-som-id/som_id; som_id != 1 -> "flip" = 0):
#
#     Vector2.x = ABS_MT_POSITION_Y
#     Vector2.y = SCREEN_H - ABS_MT_POSITION_X
#
# so a landscape point maps back to the panel as:
#
#     ABS_MT_POSITION_X = HEIGHT - screen_y
#     ABS_MT_POSITION_Y = screen_x
#
# Feeding landscape coordinates straight through puts every touch off-screen
# (x=2160 -> screen_y = 1080-2160 = -1080), which is silent: no touch point,
# no indicator under SHOW_TOUCHES, no reaction.
PANEL_X_MAX, PANEL_Y_MAX = HEIGHT, WIDTH

MAX_SLOTS = 5
TOUCH_PORT = 8089
STREAM_PORT = 8088
TAP_HOLD_S = 0.06
# If a browser drops mid-drag we would otherwise hold contact down forever and
# wedge the UI, so release it if no move arrives for this long.
DRAG_IDLE_TIMEOUT_S = 1.5

# hardwared's touch_thread opens the digitizer by its udev by-path name rather
# than by event node, and dies with FileNotFoundError when it is missing. That
# kills hardwared, manager respawns the whole stack every ~2s, and each restart
# resets sm.frame so "not_onroad_cycle" never clears -- the device can then
# never go onroad. Pointing the by-path name at this virtual device fixes it.
TOUCH_BY_PATH = "/dev/input/by-path/platform-894000.i2c-event"

CAPS = {
    e.EV_KEY: [e.BTN_TOUCH],
    e.EV_ABS: [
        (e.ABS_X, AbsInfo(value=0, min=0, max=PANEL_X_MAX, fuzz=0, flat=0, resolution=0)),
        (e.ABS_Y, AbsInfo(value=0, min=0, max=PANEL_Y_MAX, fuzz=0, flat=0, resolution=0)),
        (e.ABS_MT_SLOT, AbsInfo(value=0, min=0, max=MAX_SLOTS - 1, fuzz=0, flat=0, resolution=0)),
        (e.ABS_MT_TRACKING_ID, AbsInfo(value=0, min=-1, max=65535, fuzz=0, flat=0, resolution=0)),
        (e.ABS_MT_POSITION_X, AbsInfo(value=0, min=0, max=PANEL_X_MAX, fuzz=0, flat=0, resolution=0)),
        (e.ABS_MT_POSITION_Y, AbsInfo(value=0, min=0, max=PANEL_Y_MAX, fuzz=0, flat=0, resolution=0)),
        (e.ABS_MT_TOUCH_MAJOR, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
    ],
}

_ui = None
_lock = threading.Lock()
_tracking_id = 0


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _to_panel(sx, sy):
    """Landscape screen point -> portrait panel coordinates."""
    return HEIGHT - sy, sx


def _down(x, y):
    global _tracking_id
    _tracking_id = (_tracking_id + 1) % 65535
    px, py = _to_panel(x, y)
    _ui.write(e.EV_ABS, e.ABS_MT_SLOT, 0)
    _ui.write(e.EV_ABS, e.ABS_MT_TRACKING_ID, _tracking_id)
    _ui.write(e.EV_ABS, e.ABS_MT_POSITION_X, px)
    _ui.write(e.EV_ABS, e.ABS_MT_POSITION_Y, py)
    _ui.write(e.EV_ABS, e.ABS_MT_TOUCH_MAJOR, 40)
    # single-touch compatibility for readers that ignore protocol B
    _ui.write(e.EV_KEY, e.BTN_TOUCH, 1)
    _ui.write(e.EV_ABS, e.ABS_X, px)
    _ui.write(e.EV_ABS, e.ABS_Y, py)
    _ui.syn()


def _move(x, y):
    px, py = _to_panel(x, y)
    _ui.write(e.EV_ABS, e.ABS_MT_SLOT, 0)
    _ui.write(e.EV_ABS, e.ABS_MT_POSITION_X, px)
    _ui.write(e.EV_ABS, e.ABS_MT_POSITION_Y, py)
    _ui.write(e.EV_ABS, e.ABS_X, px)
    _ui.write(e.EV_ABS, e.ABS_Y, py)
    _ui.syn()


def _up():
    _ui.write(e.EV_ABS, e.ABS_MT_SLOT, 0)
    _ui.write(e.EV_ABS, e.ABS_MT_TRACKING_ID, -1)
    _ui.write(e.EV_KEY, e.BTN_TOUCH, 0)
    _ui.syn()


def tap(x, y, hold=TAP_HOLD_S):
    x = _clamp(int(x), 0, WIDTH)
    y = _clamp(int(y), 0, HEIGHT)
    with _lock:
        _down(x, y)
        time.sleep(hold)
        _up()
    return x, y


def swipe(x1, y1, x2, y2, steps=12, duration=0.25):
    x1, y1 = _clamp(int(x1), 0, WIDTH), _clamp(int(y1), 0, HEIGHT)
    x2, y2 = _clamp(int(x2), 0, WIDTH), _clamp(int(y2), 0, HEIGHT)
    with _lock:
        _down(x1, y1)
        for i in range(1, steps + 1):
            _move(x1 + (x2 - x1) * i // steps, y1 + (y2 - y1) * i // steps)
            time.sleep(duration / steps)
        _up()
    return (x1, y1), (x2, y2)


# --- live drag ------------------------------------------------------------
# tap()/swipe() are one-shot gestures replayed on the device. A drag from the
# browser instead streams pointer moves, so contact is held open across many
# requests and the on-device touch follows the cursor in real time.
_contact = False
_last_touch = 0.0


def touch_down(x, y):
    global _contact, _last_touch
    x, y = _clamp(int(x), 0, WIDTH), _clamp(int(y), 0, HEIGHT)
    with _lock:
        if _contact:
            _move(x, y)
        else:
            _down(x, y)
            _contact = True
        _last_touch = time.time()
    return x, y


def touch_move(x, y):
    global _last_touch
    x, y = _clamp(int(x), 0, WIDTH), _clamp(int(y), 0, HEIGHT)
    with _lock:
        if _contact:
            _move(x, y)
            _last_touch = time.time()
    return x, y


def touch_up(x=None, y=None):
    global _contact
    with _lock:
        if _contact:
            if x is not None and y is not None:
                _move(_clamp(int(x), 0, WIDTH), _clamp(int(y), 0, HEIGHT))
            _up()
            _contact = False


def _watchdog():
    global _contact
    while True:
        time.sleep(0.25)
        with _lock:
            if _contact and time.time() - _last_touch > DRAG_IDLE_TIMEOUT_S:
                _up()
                _contact = False


PAGE = """<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>openpilot remote touch</title>
<style>
 html,body{margin:0;background:#000;height:100%;overflow:hidden;
   font-family:-apple-system,system-ui,sans-serif;color:#eee}
 #wrap{position:relative;width:100vw;height:100vh;display:flex;
   align-items:center;justify-content:center}
 img{max-width:100%;max-height:100%;touch-action:none;user-select:none;-webkit-user-drag:none}
 #hint{position:fixed;left:8px;bottom:8px;font-size:12px;opacity:.55}
 .ping{position:fixed;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;
   border:2px solid #6cf;pointer-events:none;animation:p .4s ease-out forwards}
 @keyframes p{from{transform:scale(.3);opacity:.9}to{transform:scale(1);opacity:0}}
</style></head><body>
<div id="wrap"><img id="v" src="/ui.mjpg" alt="openpilot"></div>
<div id="hint">drag to control &middot; first tap on a dark screen only wakes it</div>
<script>
const img = document.getElementById('v');
const W = __W__, H = __H__;
function devXY(cx, cy){
  const r = img.getBoundingClientRect();
  const x = cx - r.left, y = cy - r.top;
  if (x < 0 || y < 0 || x > r.width || y > r.height) return null;
  return {x: Math.round(x / r.width * W), y: Math.round(y / r.height * H)};
}
function ping(x,y){const d=document.createElement('div');d.className='ping';
  d.style.left=x+'px';d.style.top=y+'px';document.body.appendChild(d);
  setTimeout(()=>d.remove(),400);}
// One move request in flight at a time, always carrying the newest position.
// This self-paces to the actual round-trip time instead of queueing up a
// backlog of stale coordinates on a slow link.
let dragging=false, inflight=false, pending=null;
function pump(){
  if(inflight || !pending) return;
  const p = pending; pending = null; inflight = true;
  fetch(`/move?x=${p.x}&y=${p.y}`,{method:'POST'})
    .catch(()=>{}).then(()=>{ inflight=false; pump(); });
}
img.addEventListener('pointerdown', ev=>{
  const p = devXY(ev.clientX, ev.clientY); if(!p) return;
  ev.preventDefault();
  try { img.setPointerCapture(ev.pointerId); } catch(e){}
  dragging = true; pending = null; inflight = true;
  fetch(`/down?x=${p.x}&y=${p.y}`,{method:'POST'})
    .catch(()=>{}).then(()=>{ inflight=false; pump(); });
  ping(ev.clientX, ev.clientY);
});
img.addEventListener('pointermove', ev=>{
  if(!dragging) return;
  const p = devXY(ev.clientX, ev.clientY); if(!p) return;
  ev.preventDefault(); pending = p; pump();
});
function end(ev){
  if(!dragging) return;
  dragging = false; pending = null;
  const p = devXY(ev.clientX, ev.clientY);
  fetch('/up' + (p ? `?x=${p.x}&y=${p.y}` : ''),{method:'POST'}).catch(()=>{});
  ev.preventDefault();
}
img.addEventListener('pointerup', end);
img.addEventListener('pointercancel', end);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    # Without this, Nagle + delayed ACK adds ~40ms to every small request on a
    # reused keep-alive connection -- measured 62ms round trip vs 25ms on a
    # fresh one. Since moves are sent one at a time, that latency lands
    # directly on the drag.
    disable_nagle_algorithm = True

    def log_message(self, *a):
        pass

    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            page = PAGE.replace("__W__", str(WIDTH)).replace("__H__", str(HEIGHT))
            return self._send(200, page.encode(), "text/html; charset=utf-8")
        if u.path == "/ui.mjpg":
            return self._proxy_stream()
        if u.path == "/health":
            return self._send(200, json.dumps({"ok": True, "device": _ui.device.path}).encode())
        if u.path in ("/tap", "/swipe", "/down", "/move", "/up"):
            return self._act()
        return self._send(404, b"{}")

    def do_POST(self):
        return self._act()

    def do_OPTIONS(self):
        return self._send(204)

    def _act(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/tap":
                x, y = tap(q["x"][0], q["y"][0])
                return self._send(200, json.dumps({"tap": [x, y]}).encode())
            if u.path == "/swipe":
                a, b = swipe(q["x1"][0], q["y1"][0], q["x2"][0], q["y2"][0])
                return self._send(200, json.dumps({"swipe": [a, b]}).encode())
            if u.path == "/down":
                x, y = touch_down(q["x"][0], q["y"][0])
                return self._send(200, json.dumps({"down": [x, y]}).encode())
            if u.path == "/move":
                x, y = touch_move(q["x"][0], q["y"][0])
                return self._send(200, json.dumps({"move": [x, y]}).encode())
            if u.path == "/up":
                touch_up(q.get("x", [None])[0], q.get("y", [None])[0])
                return self._send(200, json.dumps({"up": True}).encode())
        except Exception as ex:
            return self._send(400, json.dumps({"error": str(ex)}).encode())
        return self._send(404, b"{}")

    def _proxy_stream(self):
        """Relay the UI process's MJPEG so the page is same-origin."""
        import http.client
        # Must close the upstream connection explicitly: without this it can
        # outlive the browser, and the UI then still counts a live stream client
        # and holds the screen awake forever after the tab is closed.
        c = None
        try:
            c = http.client.HTTPConnection("127.0.0.1", STREAM_PORT, timeout=10)
            c.request("GET", "/stream")
            r = c.getresponse()
            self.send_response(200)
            self.send_header("Content-Type", r.getheader("Content-Type", "multipart/x-mixed-replace; boundary=--frame"))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            while True:
                chunk = r.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except Exception:
            pass
        finally:
            if c is not None:
                try:
                    c.close()
                except Exception:
                    pass


class TServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _link_by_path(devnode):
    """Expose this device under the name hardwared expects."""
    try:
        os.makedirs(os.path.dirname(TOUCH_BY_PATH), exist_ok=True)
        if os.path.islink(TOUCH_BY_PATH) or os.path.exists(TOUCH_BY_PATH):
            os.unlink(TOUCH_BY_PATH)
        os.symlink(devnode, TOUCH_BY_PATH)
        print(f"linked {TOUCH_BY_PATH} -> {devnode}", flush=True)
    except Exception as ex:
        print(f"could not create by-path link: {ex}", flush=True)


def main():
    global _ui
    _ui = UInput(CAPS, name="virtual-touchscreen", version=1,
                 input_props=[e.INPUT_PROP_DIRECT])
    print(f"created {_ui.device.path} ({_ui.device.name})", flush=True)
    _link_by_path(_ui.device.path)
    threading.Thread(target=_watchdog, daemon=True).start()
    srv = TServer(("0.0.0.0", TOUCH_PORT), Handler)
    print(f"remote touch UI on http://0.0.0.0:{TOUCH_PORT}/", flush=True)
    try:
        srv.serve_forever()
    finally:
        _ui.close()


if __name__ == "__main__":
    main()
