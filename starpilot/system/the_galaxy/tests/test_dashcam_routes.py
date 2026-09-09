from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import io
import os
from pathlib import Path
import subprocess
import threading
import time

import pytest

from test_dashboard_stats import FakeParams, MODULE_DIR, _install_server_import_stubs


def _load_server_module():
  import importlib.util
  import sys

  _install_server_import_stubs()
  spec = importlib.util.spec_from_file_location("dashcam_routes_server", MODULE_DIR / "the_galaxy.py")
  module = importlib.util.module_from_spec(spec)
  sys.modules["dashcam_routes_server"] = module
  spec.loader.exec_module(module)
  return module


the_galaxy = _load_server_module()
utilities = the_galaxy.utilities
ROUTE_NAME = "0000006a--9f0a7bdf9c"


def _make_segment(root, route_name=ROUTE_NAME, segment_num=0):
  segment = root / f"{route_name}--{segment_num}"
  segment.mkdir(parents=True)
  return segment


def _make_client(monkeypatch, root):
  assert the_galaxy._import_galaxy_web_symbols()
  monkeypatch.setattr(the_galaxy, "FOOTAGE_PATHS", [str(root) + "/"])
  monkeypatch.setattr(the_galaxy, "params", FakeParams())
  app = the_galaxy.Flask(
    f"dashcam_routes_{time.monotonic_ns()}",
    template_folder=str(MODULE_DIR / "templates"),
    static_folder=str(MODULE_DIR / "assets"),
  )
  the_galaxy.setup(app)
  return app.test_client()


def test_process_route_is_metadata_only_and_retains_fields(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=3)
  (segment / "qlog.zst").write_bytes(b"log")
  (segment / "Morning school run").touch()
  started_at = datetime(2026, 8, 26, 15, 30, tzinfo=timezone.utc)
  monkeypatch.setattr(utilities, "get_route_start_time", lambda path: started_at)
  monkeypatch.setattr(utilities, "has_preserve_attr", lambda path: True)
  monkeypatch.setattr(utilities, "video_to_png", lambda *args: (_ for _ in ()).throw(AssertionError("preview generation must stay lazy")))

  result = utilities.process_route(str(tmp_path), ROUTE_NAME, segment_count=4, first_segment_num=3)

  assert result == {
    "name": ROUTE_NAME,
    "png": f"/thumbnails/{ROUTE_NAME}--3/preview.png",
    "timestamp": "Morning school run",
    "startedAt": "2026-08-26T15:30:00Z",
    "isCustomName": True,
    "is_preserved": True,
    "segmentCount": 4,
    "approxDurationSeconds": 240,
  }


def test_process_route_uses_display_timestamp_without_losing_started_at(monkeypatch, tmp_path):
  _make_segment(tmp_path)
  started_at = datetime(2026, 8, 26, 15, 30, tzinfo=timezone.utc)
  monkeypatch.setattr(utilities, "get_route_start_time", lambda path: started_at)

  result = utilities.process_route(str(tmp_path), ROUTE_NAME, segment_count=1)

  assert result["timestamp"] == started_at.isoformat()
  assert result["startedAt"] == "2026-08-26T15:30:00Z"
  assert result["isCustomName"] is False


def test_route_scan_deduplicates_using_footage_root_priority(monkeypatch):
  first = "/priority/"
  second = "/fallback/"
  details = {
    first: [(ROUTE_NAME, {"segmentCount": 2, "firstSegmentNum": 1})],
    second: [
      (ROUTE_NAME, {"segmentCount": 8, "firstSegmentNum": 0}),
      ("0000006b--9f0a7bdf9d", {"segmentCount": 1, "firstSegmentNum": 4}),
    ],
  }
  monkeypatch.setattr(utilities, "get_routes_with_segment_details", lambda path: details[path])

  entries = the_galaxy._route_scan_entries([first, second])

  assert entries == [
    (first, ROUTE_NAME, 2, 1),
    (second, "0000006b--9f0a7bdf9d", 1, 4),
  ]


def test_route_metadata_stream_batches_eight_with_progress_and_retained_fields():
  entries = [
    ("/routes/", f"{index:08x}--{index:010x}", index + 1, index % 3)
    for index in range(18)
  ]

  def process(path, name, segment_count, first_segment_num):
    return {
      "name": name,
      "png": f"/thumbnails/{name}--{first_segment_num}/preview.png",
      "timestamp": f"Route {segment_count}",
      "startedAt": "2026-08-26T15:30:00Z",
      "isCustomName": True,
      "is_preserved": False,
      "segmentCount": segment_count,
      "approxDurationSeconds": segment_count * 60,
    }

  events = list(the_galaxy._route_metadata_events(entries, "dongle", process))

  assert events[0] == {"routes": [], "progress": 0, "total": 18, "connectDongleId": "dongle"}
  assert [len(event["routes"]) for event in events[1:]] == [8, 8, 2]
  assert [event["progress"] for event in events[1:]] == [8, 16, 18]
  assert all(event["total"] == 18 for event in events)
  results = [route for event in events[1:] for route in event["routes"]]
  assert len(results) == 18
  assert all({
    "name", "png", "timestamp", "startedAt", "isCustomName",
    "is_preserved", "segmentCount", "approxDurationSeconds",
  } <= result.keys() for result in results)


def test_route_metadata_stream_cancels_queued_work_when_closed():
  entries = [("/routes/", f"{index:08x}--{index:010x}", 1, 0) for index in range(40)]
  release = threading.Event()
  started = []
  lock = threading.Lock()

  def process(path, name, segment_count, first_segment_num):
    index = int(name.split("--", 1)[0], 16)
    with lock:
      started.append(index)
    if index >= 8:
      release.wait(timeout=2)
    return {"name": name}

  stream = the_galaxy._route_metadata_events(entries, process_route=process)
  next(stream)
  batch = next(stream)
  assert len(batch["routes"]) == 8
  stream.close()
  release.set()
  time.sleep(0.1)

  # At most four already-running workers continue; the remaining queue is cancelled.
  assert len(started) <= 12


def test_thumbnail_path_validation_is_strict(tmp_path):
  _make_segment(tmp_path)
  valid = f"{ROUTE_NAME}--0/preview.png"

  assert the_galaxy._resolve_route_thumbnail(valid, [tmp_path]) == tmp_path / f"{ROUTE_NAME}--0" / "preview.png"
  for invalid in (
    "../preview.png",
    f"{ROUTE_NAME}--0/qcamera.ts",
    f"{ROUTE_NAME}--0/subdir/preview.png",
    f"{ROUTE_NAME}--nope/preview.png",
    f"/{ROUTE_NAME}--0/preview.png",
    f"{ROUTE_NAME}--0\\preview.png",
  ):
    assert the_galaxy._resolve_route_thumbnail(invalid, [tmp_path]) is None


def test_thumbnail_path_validation_rejects_symlinks_outside_the_footage_root(tmp_path):
  footage_root = tmp_path / "footage"
  outside_segment = tmp_path / "outside"
  footage_root.mkdir()
  outside_segment.mkdir()
  (footage_root / f"{ROUTE_NAME}--0").symlink_to(outside_segment, target_is_directory=True)

  assert the_galaxy._resolve_route_thumbnail(f"{ROUTE_NAME}--0/preview.png", [footage_root]) is None


def test_thumbnail_generation_is_lazy_and_reuses_completed_preview(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path)
  (segment / "qcamera.ts").write_bytes(b"video")
  calls = []

  def generate(source, output):
    calls.append((Path(source), Path(output)))
    Path(output).write_bytes(b"png")
    return True

  monkeypatch.setattr(utilities, "video_to_png", generate)
  relative_path = f"{ROUTE_NAME}--0/preview.png"

  first = the_galaxy._get_or_create_route_thumbnail(relative_path, [tmp_path])
  second = the_galaxy._get_or_create_route_thumbnail(relative_path, [tmp_path])

  assert first == second == segment / "preview.png"
  assert len(calls) == 1
  assert calls[0][0] == segment / "qcamera.ts"


def test_thumbnail_failure_returns_none_and_does_not_cache_partial_file(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path)
  (segment / "qcamera.ts").write_bytes(b"video")
  monkeypatch.setattr(utilities, "video_to_png", lambda source, output: False)

  result = the_galaxy._get_or_create_route_thumbnail(f"{ROUTE_NAME}--0/preview.png", [tmp_path])

  assert result is None
  assert not (segment / "preview.png").exists()


def test_duplicate_thumbnail_requests_share_one_generation_job(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path)
  (segment / "qcamera.ts").write_bytes(b"video")
  release = threading.Event()
  started = threading.Event()
  calls = []

  def generate(preview_path):
    calls.append(preview_path)
    started.set()
    release.wait(timeout=2)
    preview_path.write_bytes(b"png")
    return preview_path

  monkeypatch.setattr(the_galaxy, "_generate_route_thumbnail", generate)
  relative_path = f"{ROUTE_NAME}--0/preview.png"
  with ThreadPoolExecutor(max_workers=2) as callers:
    first = callers.submit(the_galaxy._get_or_create_route_thumbnail, relative_path, [tmp_path])
    assert started.wait(timeout=1)
    second = callers.submit(the_galaxy._get_or_create_route_thumbnail, relative_path, [tmp_path])
    time.sleep(0.05)
    release.set()
    assert first.result(timeout=1) == segment / "preview.png"
    assert second.result(timeout=1) == segment / "preview.png"

  assert len(calls) == 1
  assert the_galaxy._ROUTE_THUMBNAIL_EXECUTOR._max_workers == 2


def test_timed_out_thumbnail_job_stays_deduplicated_until_completion(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path)
  (segment / "qcamera.ts").write_bytes(b"video")
  release = threading.Event()
  started = threading.Event()
  calls = []

  def generate(preview_path):
    calls.append(preview_path)
    started.set()
    release.wait(timeout=2)
    preview_path.write_bytes(b"png")
    return preview_path

  monkeypatch.setattr(the_galaxy, "_generate_route_thumbnail", generate)
  monkeypatch.setattr(the_galaxy, "ROUTE_THUMBNAIL_WAIT_SECONDS", 0.01)
  relative_path = f"{ROUTE_NAME}--0/preview.png"
  preview_key = str((tmp_path / f"{ROUTE_NAME}--0" / "preview.png").resolve())

  assert the_galaxy._get_or_create_route_thumbnail(relative_path, [tmp_path]) is None
  assert started.is_set()
  assert preview_key in the_galaxy._ROUTE_THUMBNAIL_FUTURES

  # A retry while the original job is still running must reuse that job.
  assert the_galaxy._get_or_create_route_thumbnail(relative_path, [tmp_path]) is None
  assert len(calls) == 1

  release.set()
  for _ in range(100):
    if preview_key not in the_galaxy._ROUTE_THUMBNAIL_FUTURES:
      break
    time.sleep(0.01)

  assert preview_key not in the_galaxy._ROUTE_THUMBNAIL_FUTURES
  assert the_galaxy._get_or_create_route_thumbnail(relative_path, [tmp_path]) == segment / "preview.png"
  assert len(calls) == 1


def test_routes_endpoint_uses_sse_no_buffering_headers(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path)
  (segment / "qlog.zst").write_bytes(b"log")
  monkeypatch.setattr(utilities, "get_route_start_time", lambda path: datetime(2026, 8, 26, tzinfo=timezone.utc))
  client = _make_client(monkeypatch, tmp_path)

  response = client.get("/api/routes")

  assert response.status_code == 200
  assert response.mimetype == "text/event-stream"
  assert response.headers["X-Accel-Buffering"] == "no"
  assert "no-cache" in response.headers["Cache-Control"]
  assert b'"progress": 1' in response.data
  assert b'"startedAt": "2026-08-26T00:00:00Z"' in response.data


def test_thumbnail_endpoint_sets_cache_headers(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path)
  preview = segment / "preview.png"
  preview.write_bytes(b"not-a-real-png-but-send-file-does-not-mind")
  client = _make_client(monkeypatch, tmp_path)

  with client.get(f"/thumbnails/{ROUTE_NAME}--0/preview.png") as response:
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.headers["Cache-Control"] == f"public, max-age={the_galaxy.ROUTE_THUMBNAIL_CACHE_SECONDS}"
    assert response.data == preview.read_bytes()


def test_rename_and_reset_keep_logs_and_use_both_reset_urls(monkeypatch, tmp_path):
  segments = [_make_segment(tmp_path, segment_num=number) for number in (0, 3)]
  for segment in segments:
    (segment / "qlog.zst").write_bytes(b"log")
    (segment / "Old_name").touch()
  monkeypatch.setattr(utilities, "get_route_start_time", lambda path: datetime(2026, 8, 26, tzinfo=timezone.utc))
  client = _make_client(monkeypatch, tmp_path)

  renamed = client.post("/api/routes/rename", json={"old": ROUTE_NAME, "new": "New name"})
  assert renamed.status_code == 200
  assert renamed.get_json()["name"] == "New_name"
  assert all((segment / "New_name").exists() for segment in segments)
  assert all((segment / "qlog.zst").read_bytes() == b"log" for segment in segments)

  reset = client.post("/api/routes/reset_name", json={"name": ROUTE_NAME})
  assert reset.status_code == 200
  assert reset.get_json()["timestamp"].startswith("2026-08-26")
  assert all(not (segment / "New_name").exists() for segment in segments)
  assert all((segment / "qlog.zst").exists() for segment in segments)

  # The legacy URL remains available for older clients.
  for segment in segments:
    (segment / "Another_name").touch()
  assert client.post("/api/routes/clear_name", json={"name": ROUTE_NAME}).status_code == 200


def test_preserve_unpreserve_and_delete_route_endpoints(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path)
  client = _make_client(monkeypatch, tmp_path)
  attributes = set()
  deleted = []
  monkeypatch.setattr(the_galaxy, "PRESERVE_COUNT", 10)
  monkeypatch.setattr(the_galaxy.os, "listxattr", lambda path: list(attributes), raising=False)
  monkeypatch.setattr(the_galaxy.os, "getxattr", lambda path, name: the_galaxy.PRESERVE_ATTR_VALUE, raising=False)
  monkeypatch.setattr(the_galaxy.os, "setxattr", lambda path, name, value: attributes.add(name), raising=False)
  monkeypatch.setattr(the_galaxy.os, "removexattr", lambda path, name: attributes.discard(name), raising=False)
  monkeypatch.setattr(the_galaxy, "delete_file", deleted.append)

  assert client.post(f"/api/routes/{ROUTE_NAME}/preserve").status_code == 200
  assert the_galaxy.PRESERVE_ATTR_NAME in attributes
  assert client.delete(f"/api/routes/{ROUTE_NAME}/preserve").status_code == 200
  assert the_galaxy.PRESERVE_ATTR_NAME not in attributes
  assert client.delete(f"/api/routes/{ROUTE_NAME}").status_code == 200
  assert deleted == [str(segment)]


def test_preserve_follows_the_first_surviving_segment(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=3)  # --0 and --1 already aged out
  client = _make_client(monkeypatch, tmp_path)
  attributes = {}
  monkeypatch.setattr(the_galaxy, "PRESERVE_COUNT", 10)
  monkeypatch.setattr(the_galaxy.os, "listxattr", lambda path: list(attributes.get(str(path), ())), raising=False)
  monkeypatch.setattr(the_galaxy.os, "getxattr", lambda path, name: the_galaxy.PRESERVE_ATTR_VALUE, raising=False)
  monkeypatch.setattr(the_galaxy.os, "setxattr", lambda path, name, value: attributes.setdefault(str(path), set()).add(name), raising=False)
  monkeypatch.setattr(the_galaxy.os, "removexattr", lambda path, name: attributes[str(path)].discard(name), raising=False)

  assert client.post(f"/api/routes/{ROUTE_NAME}/preserve").status_code == 200
  assert attributes == {str(segment): {the_galaxy.PRESERVE_ATTR_NAME}}
  assert utilities.process_route(str(tmp_path) + "/", ROUTE_NAME, 1, 3)["is_preserved"] is True

  assert client.delete(f"/api/routes/{ROUTE_NAME}/preserve").status_code == 200
  assert attributes[str(segment)] == set()


def test_preserve_limit_counts_routes_not_segments(monkeypatch, tmp_path):
  for segment_num in (5, 6, 7):
    _make_segment(tmp_path, segment_num=segment_num)
  client = _make_client(monkeypatch, tmp_path)
  monkeypatch.setattr(the_galaxy, "PRESERVE_COUNT", 1)
  monkeypatch.setattr(the_galaxy.os, "listxattr", lambda path: [the_galaxy.PRESERVE_ATTR_NAME], raising=False)
  monkeypatch.setattr(the_galaxy.os, "getxattr", lambda path, name: the_galaxy.PRESERVE_ATTR_VALUE, raising=False)
  monkeypatch.setattr(the_galaxy.os, "setxattr", lambda path, name, value: None, raising=False)

  # Three preserved segments belong to one route, so the cap of 1 is not already spent on it.
  assert client.post(f"/api/routes/{ROUTE_NAME}/preserve").status_code == 200
  assert client.post("/api/routes/00000099--9f0a7bdf9c/preserve").status_code == 400


def test_delete_all_non_preserved_keeps_entire_preserved_route_across_roots(monkeypatch, tmp_path):
  standard = tmp_path / "standard"
  high_resolution = tmp_path / "high_resolution"
  preserved_route = ROUTE_NAME
  ordinary_route = "0000006b--9f0a7bdf9d"
  preserved_marker = _make_segment(standard, preserved_route, 3)
  preserved_other_root = _make_segment(high_resolution, preserved_route, 4)
  ordinary_standard = _make_segment(standard, ordinary_route, 0)
  ordinary_other_root = _make_segment(high_resolution, ordinary_route, 1)
  unrelated = high_resolution / "video_cache"
  unrelated.mkdir()

  client = _make_client(monkeypatch, standard)
  monkeypatch.setattr(the_galaxy, "FOOTAGE_PATHS", [str(standard), str(high_resolution)])
  monkeypatch.setattr(utilities, "has_preserve_attr", lambda path: path == str(preserved_marker))
  monkeypatch.setattr(utilities, "stop_dashboard_background_analysis", lambda: None)
  monkeypatch.setattr(the_galaxy, "delete_file", lambda path: Path(path).rmdir())
  history_calls = []
  monkeypatch.setattr(utilities, "clear_dashboard_route_history", lambda params, retained_route_names=None: history_calls.append(retained_route_names) or 1)
  factory_delete_calls = []
  monkeypatch.setattr(the_galaxy, "_run_factory_reset_delete", factory_delete_calls.append)

  response = client.delete("/api/routes/delete_all?include_preserved=false")

  assert response.status_code == 200
  assert response.get_json()["deletedRoutes"] == 1
  assert response.get_json()["preservedRoutes"] == 1
  assert preserved_marker.is_dir()
  assert preserved_other_root.is_dir()
  assert not ordinary_standard.exists()
  assert not ordinary_other_root.exists()
  assert unrelated.is_dir()
  assert history_calls == [{preserved_route}]
  assert factory_delete_calls == []


def test_delete_all_including_preserved_keeps_existing_full_wipe_behavior(monkeypatch, tmp_path):
  first_root = tmp_path / "standard"
  second_root = tmp_path / "high_resolution"
  _make_segment(first_root)
  _make_segment(second_root)
  client = _make_client(monkeypatch, first_root)
  monkeypatch.setattr(the_galaxy, "FOOTAGE_PATHS", [str(first_root) + "/", str(second_root), str(first_root)])
  monkeypatch.setattr(utilities, "stop_dashboard_background_analysis", lambda: None)
  history_calls = []
  monkeypatch.setattr(utilities, "clear_dashboard_route_history", lambda params, retained_route_names=None: history_calls.append(retained_route_names) or 2)
  factory_delete_calls = []
  monkeypatch.setattr(the_galaxy, "_run_factory_reset_delete", factory_delete_calls.append)

  response = client.delete("/api/routes/delete_all?include_preserved=true")

  assert response.status_code == 200
  assert factory_delete_calls == [str(first_root), str(second_root)]
  assert history_calls == [None]
  assert "including preserved routes" in response.get_json()["message"]


def test_video_cache_evicts_oldest_instead_of_wiping_everything(monkeypatch, tmp_path):
  """A tight disk used to delete every cached mp4, so playback re-muxed on every request."""
  cache = tmp_path / "video_cache"
  cache.mkdir()
  monkeypatch.setattr(utilities, "VIDEO_CACHE_PATH", cache)
  monkeypatch.setattr(utilities, "VIDEO_CACHE_MAX_BYTES", 300)

  for index in range(4):
    entry = cache / f"{index}.mp4"
    entry.write_bytes(b"x" * 100)
    os.utime(entry, (1000 + index, 1000 + index))

  utilities._prune_video_cache()

  survivors = sorted(path.name for path in cache.glob("*.mp4"))
  # Budget is 300 bytes of 400 used, so only the oldest goes.
  assert survivors == ["1.mp4", "2.mp4", "3.mp4"]


def test_video_cache_never_evicts_the_entry_being_written(monkeypatch, tmp_path):
  cache = tmp_path / "video_cache"
  cache.mkdir()
  monkeypatch.setattr(utilities, "VIDEO_CACHE_PATH", cache)
  monkeypatch.setattr(utilities, "VIDEO_CACHE_MAX_BYTES", 50)

  for index in range(3):
    entry = cache / f"{index}.mp4"
    entry.write_bytes(b"x" * 100)
    os.utime(entry, (1000 + index, 1000 + index))

  keep = cache / "0.mp4"
  utilities._prune_video_cache(keep_path=keep)

  assert keep.exists()


def test_combined_video_streams_fragmented_mp4_without_a_full_cache_file(monkeypatch, tmp_path):
  cache = tmp_path / "video_cache"
  first = tmp_path / "first.hevc"
  second = tmp_path / "second.hevc"
  first.write_bytes(b"first")
  second.write_bytes(b"second")
  monkeypatch.setattr(utilities, "VIDEO_CACHE_PATH", cache)
  captured = {}

  class FakeProcess:
    def __init__(self):
      self.stdout = io.BytesIO(b"streamed-video")
      self.returncode = None

    def wait(self, timeout=None):
      self.returncode = 0
      return 0

    def poll(self):
      return self.returncode

  def popen(command, **kwargs):
    captured["command"] = command
    list_path = Path(command[command.index("-i") + 1])
    captured["list_path"] = list_path
    captured["list_contents"] = list_path.read_text()
    return FakeProcess()

  monkeypatch.setattr(utilities.subprocess, "Popen", popen)

  payload = b"".join(utilities.ffmpeg_stream_concatenated_mp4([first, second], chunk_size=4))

  assert payload == b"streamed-video"
  assert "frag_keyframe+empty_moov+default_base_moof" in captured["command"]
  assert captured["command"][-1] == "pipe:1"
  assert captured["list_contents"] == f"file '{first}'\nfile '{second}'\n"
  assert not captured["list_path"].exists()
  assert not list(cache.glob("*.mp4"))


def test_combined_video_stream_has_a_hard_timeout(monkeypatch, tmp_path):
  cache = tmp_path / "video_cache"
  source = tmp_path / "first.hevc"
  source.write_bytes(b"first")
  monkeypatch.setattr(utilities, "VIDEO_CACHE_PATH", cache)
  monkeypatch.setattr(utilities, "VIDEO_STREAM_TIMEOUT_SECONDS", 0.01)

  class HangingStdout:
    def read(self, _):
      time.sleep(10)
      return b""

    def close(self):
      pass

  class HangingProcess:
    def __init__(self):
      self.stdout = HangingStdout()
      self.returncode = None
      self.terminated = False

    def poll(self):
      return self.returncode

    def terminate(self):
      self.terminated = True
      self.returncode = -15

    def wait(self, timeout=None):
      del timeout
      return self.returncode

  process = HangingProcess()
  monkeypatch.setattr(utilities.subprocess, "Popen", lambda *args, **kwargs: process)

  with pytest.raises(TimeoutError, match="Timed out streaming"):
    b"".join(utilities.ffmpeg_stream_concatenated_mp4([source], chunk_size=4))

  assert process.terminated
  assert not list(cache.glob("route-download-*.txt"))


def test_route_endpoints_reject_invalid_names(monkeypatch, tmp_path):
  client = _make_client(monkeypatch, tmp_path)

  for method, path in (
    (client.delete, "/api/routes/not-a-route"),
    (client.post, "/api/routes/not-a-route/preserve"),
    (client.delete, "/api/routes/not-a-route/preserve"),
    (client.get, "/api/routes/not-a-route"),
    (client.get, "/video/not-a-route/combined"),
  ):
    assert method(path).status_code == 400


def _stub_remux(monkeypatch, tmp_path, payload=b"wrapped-video"):
  """Stand in for the ffmpeg remux, returning a real file so send_file can stream it."""
  wrapped = tmp_path / "wrapped.mp4"
  wrapped.write_bytes(payload)
  monkeypatch.setattr(utilities, "ffmpeg_mp4_wrap_to_path", lambda path: wrapped)
  return wrapped


def test_sparse_route_metadata_and_video_downloads(monkeypatch, tmp_path):
  segments = [_make_segment(tmp_path, segment_num=number) for number in (0, 3, 11)]
  for segment in segments:
    (segment / "fcamera.hevc").write_bytes(b"hevc")
  monkeypatch.setattr(utilities, "get_route_start_time", lambda path: datetime(2026, 8, 26, tzinfo=timezone.utc))
  _stub_remux(monkeypatch, tmp_path)
  monkeypatch.setattr(utilities, "ffmpeg_stream_concatenated_mp4", lambda paths: iter((b"combined-", b"video")))
  client = _make_client(monkeypatch, tmp_path)

  metadata = client.get(f"/api/routes/{ROUTE_NAME}")
  assert metadata.status_code == 200
  assert metadata.get_json()["segment_urls"] == [f"/video/{ROUTE_NAME}--{number}" for number in (0, 3, 11)]
  # One minute per segment, without probing each one with ffprobe.
  assert metadata.get_json()["total_duration"] == 180

  with client.get(f"/video/{ROUTE_NAME}--3?camera=forward") as segment_video:
    assert segment_video.status_code == 200
    assert segment_video.mimetype == "video/mp4"
    assert segment_video.data == b"wrapped-video"

  with client.get(f"/video/{ROUTE_NAME}/combined?camera=forward") as combined_video:
    assert combined_video.status_code == 200
    assert combined_video.mimetype == "video/mp4"
    assert combined_video.data == b"combined-video"
    assert combined_video.headers["X-Accel-Buffering"] == "no"


def test_route_metadata_never_probes_segments_with_ffprobe(monkeypatch, tmp_path):
  """Probing each segment put one subprocess per segment in front of playback."""
  for number in (0, 1, 2):
    segment = _make_segment(tmp_path, segment_num=number)
    (segment / "fcamera.hevc").write_bytes(b"hevc")

  def explode(path):
    raise AssertionError(f"ffprobe must stay off the route metadata path: {path}")

  monkeypatch.setattr(utilities, "get_video_duration", explode)
  monkeypatch.setattr(utilities, "get_route_start_time", lambda path: datetime(2026, 8, 26, tzinfo=timezone.utc))
  client = _make_client(monkeypatch, tmp_path)

  metadata = client.get(f"/api/routes/{ROUTE_NAME}")
  assert metadata.status_code == 200
  assert metadata.get_json()["total_duration"] == 180


def test_low_quality_serves_the_wrapped_qcamera_preview(monkeypatch, tmp_path):
  """qcamera.ts is tiny, but it still needs the mp4 wrap - MPEG-TS will not play in a <video>."""
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  (segment / "qcamera.ts").write_bytes(b"ts")

  preview_mp4 = tmp_path / "preview.mp4"
  preview_mp4.write_bytes(b"preview-video")
  full_mp4 = tmp_path / "full.mp4"
  full_mp4.write_bytes(b"full-video")

  wrapped = []
  def wrap(path):
    wrapped.append(os.path.basename(str(path)))
    return preview_mp4 if str(path).endswith("qcamera.ts") else full_mp4

  monkeypatch.setattr(utilities, "ffmpeg_mp4_wrap_to_path", wrap)
  client = _make_client(monkeypatch, tmp_path)

  with client.get(f"/video/{ROUTE_NAME}--0?camera=forward&quality=low") as low:
    assert low.status_code == 200
    assert low.mimetype == "video/mp4"
    assert low.data == b"preview-video"

  with client.get(f"/video/{ROUTE_NAME}--0?camera=forward") as full:
    assert full.data == b"full-video"
  assert wrapped == ["qcamera.ts", "fcamera.hevc"]


def test_low_quality_falls_through_to_the_full_stream_when_qcamera_is_missing(monkeypatch, tmp_path):
  """The player always asks for the preview, so a missing one must never be an error."""
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  _stub_remux(monkeypatch, tmp_path)
  client = _make_client(monkeypatch, tmp_path)

  with client.get(f"/video/{ROUTE_NAME}--0?camera=forward&quality=low") as low:
    assert low.status_code == 200
    assert low.data == b"wrapped-video"


def test_low_quality_falls_through_when_the_preview_cannot_be_wrapped(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  (segment / "qcamera.ts").write_bytes(b"ts")

  full_mp4 = tmp_path / "full.mp4"
  full_mp4.write_bytes(b"full-video")

  def wrap(path):
    if str(path).endswith("qcamera.ts"):
      raise ValueError("corrupt preview")
    return full_mp4

  monkeypatch.setattr(utilities, "ffmpeg_mp4_wrap_to_path", wrap)
  client = _make_client(monkeypatch, tmp_path)

  with client.get(f"/video/{ROUTE_NAME}--0?camera=forward&quality=low") as low:
    assert low.status_code == 200
    assert low.data == b"full-video"


def test_only_the_road_camera_has_a_preview(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "ecamera.hevc").write_bytes(b"hevc")
  (segment / "qcamera.ts").write_bytes(b"ts")
  _stub_remux(monkeypatch, tmp_path)
  client = _make_client(monkeypatch, tmp_path)

  with client.get(f"/video/{ROUTE_NAME}--0?camera=wide&quality=low") as wide:
    assert wide.data == b"wrapped-video"


def test_preview_timeout_does_not_wait_again_for_the_full_stream(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  (segment / "qcamera.ts").write_bytes(b"ts")
  calls = []

  def not_ready(path):
    calls.append(Path(path).name)
    return None

  monkeypatch.setattr(the_galaxy, "_get_or_create_segment_mp4", not_ready)
  client = _make_client(monkeypatch, tmp_path)

  response = client.get(f"/video/{ROUTE_NAME}--0?camera=forward&quality=low")
  assert response.status_code == 503
  assert calls == ["qcamera.ts"]


def test_in_progress_segment_is_not_playable(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  (segment / "qcamera.ts").write_bytes(b"ts")
  (segment / "rlog.lock").touch()
  client = _make_client(monkeypatch, tmp_path)

  response = client.get(f"/video/{ROUTE_NAME}--0?camera=forward&quality=low")
  assert response.status_code == 409
  assert "still being recorded" in response.get_json()["error"]


def test_completed_segment_remux_reuses_the_disk_cache(monkeypatch, tmp_path):
  source = tmp_path / "fcamera.hevc"
  source.write_bytes(b"hevc")
  os.utime(source, (1000, 1000))
  cache = tmp_path / "video_cache"
  monkeypatch.setattr(utilities, "VIDEO_CACHE_PATH", cache)
  calls = []

  def wrap(command, check, timeout):
    calls.append(timeout)
    Path(command[-1]).write_bytes(b"mp4")

  monkeypatch.setattr(utilities.subprocess, "run", wrap)
  first = utilities.ffmpeg_mp4_wrap_to_path(source)
  second = utilities.ffmpeg_mp4_wrap_to_path(source)

  assert first == second
  assert len(calls) == 1
  assert 0 < calls[0] <= utilities.VIDEO_REMUX_TIMEOUT_SECONDS


def test_segment_remux_timeout_is_bounded_and_removes_partial_output(monkeypatch, tmp_path):
  source = tmp_path / "fcamera.hevc"
  source.write_bytes(b"hevc")
  cache = tmp_path / "video_cache"
  monkeypatch.setattr(utilities, "VIDEO_CACHE_PATH", cache)
  timeouts = []

  def timeout(command, check, timeout):
    timeouts.append(timeout)
    Path(command[-1]).write_bytes(b"partial")
    raise subprocess.TimeoutExpired(command, timeout)

  monkeypatch.setattr(utilities.subprocess, "run", timeout)

  with pytest.raises(ValueError, match="Timed out processing video file"):
    utilities.ffmpeg_mp4_wrap_to_path(source)

  assert len(timeouts) == 1
  assert 0 < timeouts[0] <= utilities.VIDEO_REMUX_TIMEOUT_SECONDS
  assert not list(cache.glob("*.mp4"))


def test_segment_video_falls_back_across_cameras(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  _stub_remux(monkeypatch, tmp_path)
  client = _make_client(monkeypatch, tmp_path)

  with client.get(f"/video/{ROUTE_NAME}--0?camera=forward") as forward:
    assert forward.data == b"wrapped-video"
  # No ecamera.hevc on disk for this segment.
  assert client.get(f"/video/{ROUTE_NAME}--0?camera=wide").status_code == 404
  assert client.get("/video/not-a-segment?camera=forward").status_code == 400


def test_segment_video_supports_range_requests(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  _stub_remux(monkeypatch, tmp_path, payload=b"0123456789")
  client = _make_client(monkeypatch, tmp_path)

  with client.get(f"/video/{ROUTE_NAME}--0?camera=forward", headers={"Range": "bytes=2-5"}) as partial:
    assert partial.status_code == 206
    assert partial.data == b"2345"
  assert partial.headers["Content-Range"] == "bytes 2-5/10"

  # A malformed range used to raise inside the hand-rolled parser.
  with client.get(f"/video/{ROUTE_NAME}--0?camera=forward", headers={"Range": "bytes=abc"}) as malformed_range:
    assert malformed_range.status_code in (200, 416)


def test_head_request_prepares_full_quality_without_sending_the_body(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  _stub_remux(monkeypatch, tmp_path)
  client = _make_client(monkeypatch, tmp_path)

  with client.head(f"/video/{ROUTE_NAME}--0?camera=forward") as prepared:
    assert prepared.status_code == 200
    assert prepared.mimetype == "video/mp4"
    assert prepared.data == b""


def test_concurrent_requests_for_one_segment_share_a_single_remux(monkeypatch, tmp_path):
  segment = _make_segment(tmp_path, segment_num=0)
  (segment / "fcamera.hevc").write_bytes(b"hevc")
  wrapped = tmp_path / "wrapped.mp4"
  wrapped.write_bytes(b"wrapped-video")

  calls = []
  started = threading.Event()

  def slow_remux(path):
    calls.append(path)
    started.set()
    time.sleep(0.3)
    return wrapped

  monkeypatch.setattr(utilities, "ffmpeg_mp4_wrap_to_path", slow_remux)
  client = _make_client(monkeypatch, tmp_path)

  results = []
  def fetch():
    with client.get(f"/video/{ROUTE_NAME}--0?camera=forward") as response:
      results.append(response.status_code)

  threads = [threading.Thread(target=fetch) for _ in range(4)]
  for thread in threads:
    thread.start()
  for thread in threads:
    thread.join()

  assert results == [200, 200, 200, 200]
  assert len(calls) == 1
