import io
import tarfile

from test_dashboard_stats import MODULE_DIR, _install_server_import_stubs


def _load_server_module():
  import importlib.util
  import sys

  _install_server_import_stubs()
  spec = importlib.util.spec_from_file_location("route_logs_server", MODULE_DIR / "the_galaxy.py")
  module = importlib.util.module_from_spec(spec)
  sys.modules["route_logs_server"] = module
  spec.loader.exec_module(module)
  return module


the_galaxy = _load_server_module()


def _make_route(root, name, segments, filename="rlog.zst", size=32):
  for segment_num in segments:
    segment_dir = root / f"{name}--{segment_num}"
    segment_dir.mkdir(parents=True)
    (segment_dir / filename).write_bytes(bytes([segment_num]) * size)
    # a sibling that must never be offered as a full log
    (segment_dir / "qlog.zst").write_bytes(b"q")


def _use_footage_root(monkeypatch, root):
  monkeypatch.setattr(the_galaxy, "FOOTAGE_PATHS", [str(root) + "/"])


def test_route_log_files_are_ordered_numerically(monkeypatch, tmp_path):
  _make_route(tmp_path, "0000006a--9f0a7bdf9c", [0, 1, 2, 10])
  _use_footage_root(monkeypatch, tmp_path)

  logs = the_galaxy._route_log_files("0000006a--9f0a7bdf9c")

  # 10 must sort after 2, not lexically between 1 and 2
  assert [segment for segment, _, _, _ in logs] == [
    "0000006a--9f0a7bdf9c--0",
    "0000006a--9f0a7bdf9c--1",
    "0000006a--9f0a7bdf9c--2",
    "0000006a--9f0a7bdf9c--10",
  ]
  assert {filename for _, filename, _, _ in logs} == {"rlog.zst"}
  assert [size for _, _, _, size in logs] == [32, 32, 32, 32]


def test_route_log_files_prefers_newest_available_format(monkeypatch, tmp_path):
  _make_route(tmp_path, "0000006a--9f0a7bdf9c", [0], filename="rlog.bz2")
  (tmp_path / "0000006a--9f0a7bdf9c--0" / "rlog.zst").write_bytes(b"zstd")
  _use_footage_root(monkeypatch, tmp_path)

  logs = the_galaxy._route_log_files("0000006a--9f0a7bdf9c")

  assert [filename for _, filename, _, _ in logs] == ["rlog.zst"]


def test_route_log_files_rejects_names_that_are_not_routes(monkeypatch, tmp_path):
  _make_route(tmp_path, "0000006a--9f0a7bdf9c", [0])
  _use_footage_root(monkeypatch, tmp_path)

  for name in ("", None, "..", "../..", "0000006a--9f0a7bdf9c--0", "0000006a--9f0a7bdf9cx", "/etc"):
    assert the_galaxy._route_log_files(name) == [], name


def test_route_log_files_skips_segments_without_logs(monkeypatch, tmp_path):
  _make_route(tmp_path, "0000006a--9f0a7bdf9c", [0, 1])
  (tmp_path / "0000006a--9f0a7bdf9c--1" / "rlog.zst").unlink()
  _use_footage_root(monkeypatch, tmp_path)

  logs = the_galaxy._route_log_files("0000006a--9f0a7bdf9c")

  assert [segment for segment, _, _, _ in logs] == ["0000006a--9f0a7bdf9c--0"]


def test_tar_buffer_hands_back_each_write_once():
  buffer = the_galaxy._TarBuffer()

  buffer.write(b"one")
  buffer.write(b"two")

  assert buffer.pop() == b"onetwo"
  assert buffer.pop() == b""


def test_streamed_archive_is_a_readable_tar(monkeypatch, tmp_path):
  _make_route(tmp_path, "0000006a--9f0a7bdf9c", [0, 1], size=4096)
  _use_footage_root(monkeypatch, tmp_path)
  logs = the_galaxy._route_log_files("0000006a--9f0a7bdf9c")

  buffer = the_galaxy._TarBuffer()
  chunks = []
  with tarfile.open(fileobj=buffer, mode="w|") as archive:
    for segment, filename, path, _ in logs:
      archive.add(path, arcname=f"{segment}/{filename}")
      chunks.append(buffer.pop())
  chunks.append(buffer.pop())

  # more than one chunk means a long route never has to be buffered whole
  assert sum(1 for chunk in chunks if chunk) > 1

  with tarfile.open(fileobj=io.BytesIO(b"".join(chunks)), mode="r:") as archive:
    assert archive.getnames() == [
      "0000006a--9f0a7bdf9c--0/rlog.zst",
      "0000006a--9f0a7bdf9c--1/rlog.zst",
    ]
    assert archive.extractfile("0000006a--9f0a7bdf9c--1/rlog.zst").read() == bytes([1]) * 4096
