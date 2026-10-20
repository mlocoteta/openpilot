"""JSON sidecar with every block/maneuver/settings event of a characterization run.

Written to /data/media/0/lateral_characterization/<route>.json (rewritten atomically on
every event, so a crash loses nothing already logged). Event times carry the log clock
(`mono_ns`, same clock as rlog logMonoTime) so the host report can cut the rlogs without
reading any device params.
"""
import json
import os
import time

from openpilot.tools.lateral_maneuvers.characterization.settings import _atomic_write_json

SIDECAR_DIR = "/data/media/0/lateral_characterization"
SIDECAR_VERSION = 1


def boot_ns():
  try:
    return time.clock_gettime_ns(time.CLOCK_BOOTTIME)  # openpilot logMonoTime clock
  except (AttributeError, OSError):
    return time.monotonic_ns()


def _safe_name(name):
  keep = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
  return keep.strip("._") or "unknown"


class Sidecar:
  def __init__(self, directory=SIDECAR_DIR, header=None, log=None):
    self.directory = directory
    self.log = log or (lambda *a, **k: None)
    self.doc = {"version": SIDECAR_VERSION, "startedWall": time.time(), "startedBootNs": boot_ns(), "events": []}  # noqa: TID251 (human-readable wall time)
    self.doc.update(header or {})
    self.path = None

  def set_route(self, route):
    """Pick the file name once the route is known; keeps events logged before that."""
    if self.path is not None or not route:
      return
    base = os.path.join(self.directory, _safe_name(route))
    path, n = base + ".json", 1
    while os.path.exists(path):  # daemon restarted within the same route
      n += 1
      path = f"{base}.{n}.json"
    self.doc["route"] = route
    self.path = path
    self.flush()

  def event(self, kind, mono_ns, **fields):
    entry = {"type": kind, "mono_ns": int(mono_ns), "boot_ns": boot_ns(), "wall": round(time.time(), 3)}  # noqa: TID251 (human-readable wall time)
    entry.update(fields)
    self.doc["events"].append(entry)
    self.flush()
    return entry

  def flush(self):
    if self.path is None:
      return
    try:
      _atomic_write_json(self.path, self.doc)
    except OSError as e:
      self.log(f"lateral characterization: sidecar write failed: {e}")


def load(path):
  with open(path) as f:
    return json.load(f)
