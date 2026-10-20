"""MJPEG stream of the openpilot UI, served over the network.

Enabled with STREAM=1. Entirely self-contained: it needs nothing but the UI's
own render texture, so it is unaffected by the virtual-touchscreen workaround
used on devices with a dead digitizer. Removing that workaround does not
disturb this, and vice versa.

Capture only runs while somebody is actually watching. Without that gate the
render loop pays for a GPU readback, a downscale and a full JPEG encode on
every frame forever, even with no viewer -- which is enough to starve other
processes into "communication issue between processes".

Environment:
  STREAM=1            enable
  STREAM_PORT=8088    listen port
  STREAM_SCALE=2      integer downscale before encode (2 -> 1080x540)
  STREAM_QUALITY=50   JPEG quality
  STREAM_FPS=20       capture rate cap (render loop is the ceiling)
  STREAM_KEEP_AWAKE=1 hold the screen awake while a viewer is connected
"""
import io
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

from PIL import Image
import pyray as rl

# Integer downscale applied before JPEG encode. 2 -> 1080x540, still very
# legible on a laptop, and roughly a 4x cut in both encode cost and bytes.
_SCALE = max(1, int(os.getenv("STREAM_SCALE", "2")))
KEEP_AWAKE = os.getenv("STREAM_KEEP_AWAKE", "1") == "1"

# /snapshot is a one-shot GET that leaves no connection behind to keep capture
# alive, so keep capturing briefly after one rather than serving a stale frame.
SNAPSHOT_KEEPALIVE_S = 3.0

_state = None
_counter = 0
_small_rt = None
_gpu_scale_ok = True
_clients = 0
_clients_lock = threading.Lock()
_last_snapshot_req = 0.0


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
  daemon_threads = True
  allow_reuse_address = True


class StreamState:
  def __init__(self):
    self.frame = b""
    self.lock = threading.Lock()
    self.event = threading.Event()

  def update(self, jpeg):
    with self.lock:
      self.frame = jpeg
    self.event.set()

  def get(self):
    with self.lock:
      return self.frame

  def wait(self, t=2.0):
    self.event.wait(t)
    self.event.clear()


def _client_delta(n):
  global _clients
  with _clients_lock:
    _clients += n


def _capture_wanted() -> bool:
  """True only when somebody is actually watching."""
  if _clients > 0:
    return True
  return (time.monotonic() - _last_snapshot_req) < SNAPSHOT_KEEPALIVE_S


def _keep_awake_thread():
  """Reset the UI's interaction timer while a viewer is connected.

  When the screen dims, _set_awake(False) calls gui_app.set_should_render(False)
  and the render loop skips everything before capture_frame, so the stream stops
  updating and the next tap is swallowed waking the screen. This runs on its own
  thread precisely because the render loop is what stops.
  """
  dev = None
  while True:
    time.sleep(1.0)
    if _clients <= 0:
      continue
    if dev is None:
      try:
        from openpilot.selfdrive.ui.ui_state import device
        dev = device
      except Exception:
        continue
    try:
      dev.reset_interactive_timeout()
    except Exception:
      pass


PAGE = """<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>openpilot</title>
<style>
 html,body{margin:0;background:#000;height:100%;overflow:hidden}
 #wrap{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}
 img{max-width:100%;max-height:100%}
</style></head><body>
<div id="wrap"><img src="/stream" alt="openpilot"></div>
</body></html>"""


class StreamHandler(BaseHTTPRequestHandler):
  protocol_version = "HTTP/1.1"
  # Each MJPEG frame goes out as several small writes; Nagle would sit on them
  # waiting for an ACK and add tens of ms of latency to the video.
  disable_nagle_algorithm = True

  def log_message(self, *a):
    pass

  def do_GET(self):
    global _last_snapshot_req

    if self.path in ("/", "/index.html"):
      body = PAGE.encode()
      self.send_response(200)
      self.send_header("Content-Type", "text/html; charset=utf-8")
      self.send_header("Content-Length", str(len(body)))
      self.end_headers()
      self.wfile.write(body)

    elif self.path == "/stream":
      self.send_response(200)
      self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=--frame")
      self.send_header("Cache-Control", "no-cache")
      self.send_header("Access-Control-Allow-Origin", "*")
      self.end_headers()
      _client_delta(1)
      try:
        while True:
          self.server._state.wait(2.0)
          f = self.server._state.get()
          if f:
            self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " +
                             str(len(f)).encode() + b"\r\n\r\n")
            self.wfile.write(f)
            self.wfile.write(b"\r\n")
      except (BrokenPipeError, ConnectionResetError, OSError):
        pass
      finally:
        _client_delta(-1)

    elif self.path == "/snapshot":
      was_idle = not _capture_wanted()
      _last_snapshot_req = time.monotonic()
      # capture was gated off, so the stored frame is stale; wait for the render
      # loop to produce a fresh one now that demand is registered
      if was_idle:
        self.server._state.wait(1.0)
      f = self.server._state.get()
      if f:
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(f)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(f)
      else:
        self.send_response(503)
        self.send_header("Content-Length", "0")
        self.end_headers()

    else:
      self.send_response(404)
      self.send_header("Content-Length", "0")
      self.end_headers()


def start(port: int = 8088):
  """Start the MJPEG server. Call once, from the UI process."""
  global _state
  _state = StreamState()
  srv = ThreadingHTTPServer(("0.0.0.0", port), StreamHandler)
  srv._state = _state
  threading.Thread(target=srv.serve_forever, daemon=True).start()
  if KEEP_AWAKE:
    threading.Thread(target=_keep_awake_thread, daemon=True).start()
  return _state


def _downscaled_image(app):
  """Shrink on the GPU so the readback moves 1/4 the pixels.

  glReadPixels of the full 2160x1080 RGBA target is ~9.3 MB per frame and
  stalls the pipeline; blitting into a half-size render target first cuts that
  to ~2.3 MB and drops the CPU-side resize pass entirely. Safe because the call
  site runs after end_drawing().
  """
  global _small_rt
  src = app._render_texture.texture
  w, h = src.width // _SCALE, src.height // _SCALE
  if _small_rt is None or _small_rt.texture.width != w or _small_rt.texture.height != h:
    if _small_rt is not None:
      rl.unload_render_texture(_small_rt)
    _small_rt = rl.load_render_texture(w, h)
    rl.set_texture_filter(_small_rt.texture, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
  rl.begin_texture_mode(_small_rt)
  rl.draw_texture_pro(src,
                      rl.Rectangle(0, 0, float(src.width), float(src.height)),
                      rl.Rectangle(0, 0, float(w), float(h)),
                      rl.Vector2(0, 0), 0.0, rl.WHITE)
  rl.end_texture_mode()
  return rl.load_image_from_texture(_small_rt.texture)


def capture_frame(app, quality: int = 50, target_fps: int = 20):
  """Call from the render loop, after end_drawing()."""
  global _counter, _gpu_scale_ok

  if _state is None or app._render_texture is None:
    return
  if not _capture_wanted():
    return

  _counter += 1
  skip = max(1, app._target_fps // max(1, target_fps))
  if _counter % skip != 0:
    return

  si = None
  if _SCALE > 1 and _gpu_scale_ok:
    try:
      si = _downscaled_image(app)
    except Exception:
      # never let a streaming optimisation take the UI down
      _gpu_scale_ok = False
      si = None
  cpu_reduce = si is None and _SCALE > 1
  if si is None:
    si = rl.load_image_from_texture(app._render_texture.texture)

  # The GPU blit already flips the bottom-up render target, so only the direct
  # readback paths still need the "raw" decoder's negative orientation.
  orient = 1 if (_SCALE > 1 and not cpu_reduce) else -1
  try:
    # Wrap the readback in place rather than copying it, and let the decoder do
    # the vertical flip instead of a full transpose pass.
    img = Image.frombuffer("RGBA", (si.width, si.height),
                           rl.ffi.buffer(si.data, si.width * si.height * 4),
                           "raw", "RGBA", 0, orient)
    if cpu_reduce:
      img = img.reduce(_SCALE)
    # convert() materialises a new image, so the GL buffer is free after this
    img = img.convert("RGB")
  finally:
    rl.unload_image(si)

  buf = io.BytesIO()
  img.save(buf, "JPEG", quality=quality, optimize=False)
  _state.update(buf.getvalue())
