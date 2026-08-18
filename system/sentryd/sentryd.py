#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import threading
import time
from pathlib import Path
from uuid import uuid4

import cereal.messaging as messaging
import requests
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.system.camerad.snapshot import jpeg_write, snapshot
from openpilot.system.hardware import PC
from openpilot.system.hardware.hw import Paths

from openpilot.system.sentryd.detector import MotionDetector


ARM_DELAY_SECONDS = 90.0
LOOP_INTERVAL_SECONDS = 0.1
SENSITIVITY = 0.04
WARNING_TRIGGER_COUNT = 10
ALARM_TRIGGER_COUNT = 25
ALARM_TIME_SECONDS = 30.0
RESET_TIME_SECONDS = 60.0
MAX_EVENT_DIRECTORIES = 100


def event_root() -> Path:
  if PC:
    return Path(Paths.comma_home()) / "starpilot" / "data" / "sentryd"
  return Path("/data/media/0/sentryd")


def galaxy_event_url() -> str:
  default_port = "8083" if PC else "8082"
  port = os.environ.get("SP_GALAXY_PORT", default_port)
  return f"http://127.0.0.1:{port}/api/sentry/events"


def _utc_now() -> str:
  return datetime.now(timezone.utc).isoformat()


class SentryMode:
  def __init__(self, params: Params | None = None, sm=None, clock=time.monotonic):
    self.params = params or Params(return_defaults=True)
    self.sm = sm or messaging.SubMaster(["accelerometer"])
    self.clock = clock
    self.detector = MotionDetector(
      sensitivity=SENSITIVITY,
      warning_trigger_count=WARNING_TRIGGER_COUNT,
      alarm_trigger_count=ALARM_TRIGGER_COUNT,
      alarm_time=ALARM_TIME_SECONDS,
      reset_time=RESET_TIME_SECONDS,
      clock=clock,
    )
    self.started_at = clock()
    self.armed = False
    self._last_status = None

  def _write_status(self, state: str, **extra) -> None:
    status_values = {"state": state, **extra}
    if status_values == self._last_status:
      return
    status = {**status_values, "updatedAt": _utc_now()}
    try:
      self.params.put("SentryModeStatus", json.dumps(status, separators=(",", ":")))
    except Exception:
      cloudlog.exception("sentryd: failed to write status")
    self._last_status = status_values

  def _capture_images(self, event_id: str) -> list[str]:
    self.params.put_bool("SentryModeCapture", True)
    try:
      rear, front = snapshot(allow_existing=True)
    except Exception:
      cloudlog.exception("sentryd: snapshot failed")
      return []
    finally:
      self.params.put_bool("SentryModeCapture", False)

    if rear is None and front is None:
      return []

    directory = event_root() / event_id
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    if rear is not None:
      rear_path = directory / "wide.jpg"
      jpeg_write(str(rear_path), rear)
      paths.append(str(rear_path))
    if front is not None:
      front_path = directory / "driver.jpg"
      jpeg_write(str(front_path), front)
      paths.append(str(front_path))
    return paths

  def _trim_old_events(self) -> None:
    root = event_root()
    if not root.exists():
      return
    try:
      directories = sorted((path for path in root.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime)
      for directory in directories[:-MAX_EVENT_DIRECTORIES]:
        for child in directory.iterdir():
          child.unlink(missing_ok=True)
        directory.rmdir()
    except OSError:
      cloudlog.exception("sentryd: failed to trim old events")

  def _publish_event(self, event: dict) -> None:
    self.params.put("SentryModeLastEvent", json.dumps(event, separators=(",", ":")))
    self._write_status(event["kind"], eventId=event["eventId"])

    def publish():
      for attempt in range(3):
        try:
          response = requests.post(galaxy_event_url(), json=event, timeout=3)
          response.raise_for_status()
          return
        except requests.RequestException as error:
          if attempt == 2:
            cloudlog.warning(f"sentryd: Galaxy notification unavailable: {error}")
          else:
            time.sleep(1.0)

    threading.Thread(target=publish, name="sentryd-galaxy-publish", daemon=True).start()

  def _handle_detection(self, kind: str) -> None:
    event_id = f"{int(time.time())}-{uuid4().hex[:8]}"
    event = {
      "eventId": event_id,
      "kind": kind,
      "detectedAt": _utc_now(),
      "imagePaths": [],
      "message": "Movement detected while parked." if kind == "warning" else "Sustained movement detected while parked.",
    }
    if kind == "alarm":
      event["imagePaths"] = self._capture_images(event_id)
      self._trim_old_events()
    self._publish_event(event)

  def update(self) -> None:
    now = self.clock()
    if now - self.started_at < ARM_DELAY_SECONDS:
      self._write_status("arming", secondsRemaining=max(0, int(ARM_DELAY_SECONDS - (now - self.started_at))))
      return

    if not self.armed:
      self.armed = True
      self._write_status("armed")

    message = self.sm["accelerometer"]
    if message is None or message.acceleration is None:
      self._write_status("sensor_unavailable")
      return

    try:
      detection = self.detector.update(message.acceleration.v, now=now)
    except (TypeError, ValueError):
      self._write_status("sensor_unavailable")
      return

    if detection is not None:
      self._handle_detection(detection)

  def run(self) -> None:
    self._write_status("starting")
    while self.params.get_bool("SentryModeEnabled"):
      self.sm.update(0)
      self.update()
      time.sleep(LOOP_INTERVAL_SECONDS)
    self._write_status("disabled")


def main() -> None:
  SentryMode().run()


if __name__ == "__main__":
  main()
