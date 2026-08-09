import hashlib
import io
import json
import sys
from pathlib import Path

from scripts import model_compiler
from scripts.model_compiler import split_oversized_artifact
from openpilot.common import file_chunker
from openpilot.selfdrive.modeld import compile_modeld
from openpilot.starpilot.assets import download_functions
from openpilot.starpilot.assets import model_manager
from openpilot.starpilot.assets.model_manager import MANIFEST_CANDIDATES, ModelManager
from openpilot.starpilot.common.model_versions import UNIFIED_ARTIFACT_FORMAT


def test_v22_is_the_only_manifest_candidate():
  assert MANIFEST_CANDIDATES == ("v22",)


def test_behavior_version_does_not_control_artifact_layout():
  manager = object.__new__(ModelManager)
  assert manager._required_files("example", UNIFIED_ARTIFACT_FORMAT) == [
    "example_driving_tinygrad.pkl",
  ]
  assert manager._required_files("example", "") == [
    "example_driving_tinygrad.pkl",
  ]
  assert manager._required_files("example", "split") == []


def test_external_gpu_requirement_is_cached_from_manifest(tmp_path, monkeypatch):
  monkeypatch.setattr(model_manager, "MODELS_PATH", tmp_path)
  manager = object.__new__(ModelManager)
  metadata = manager._build_artifact_metadata_map([
    {"id": "large", "artifact_format": UNIFIED_ARTIFACT_FORMAT, "uses_external_gpu": True},
    {"id": "normal", "artifact_format": UNIFIED_ARTIFACT_FORMAT},
  ])
  (tmp_path / model_manager.ARTIFACT_METADATA_CACHE).write_text(json.dumps(metadata))

  assert model_manager.model_uses_external_gpu("large")
  assert not model_manager.model_uses_external_gpu("normal")
  assert not model_manager.model_uses_external_gpu("missing")


def test_external_gpu_compilation_is_opt_in(tmp_path, monkeypatch):
  invocations = []
  monkeypatch.setattr(model_compiler, "build_compile_env", lambda: {
    "DEV": "QCOM", "IMAGE": "2", "NOLOCALS": "1", "OPENPILOT_HACKS": "1",
  })
  monkeypatch.setattr(model_compiler.subprocess, "run", lambda command, **kwargs: invocations.append((command, kwargs)))
  monkeypatch.setattr(model_compiler, "wait_for_external_gpu", lambda _: None)
  files = {"driving_supercombo": tmp_path / "model.onnx"}

  model_compiler.compile_driving("normal", files, "supercombo", "v15", tmp_path, "policy")
  model_compiler.compile_driving("large", files, "supercombo", "v15", tmp_path, "policy", external_gpu=True)

  normal_command, normal_kwargs = invocations[0]
  external_command, external_kwargs = invocations[1]
  assert "--out-of-band" not in normal_command
  assert normal_kwargs["env"]["DEV"] == "QCOM"
  assert normal_kwargs["env"]["IMAGE"] == "2"
  assert "--out-of-band" in external_command
  assert external_kwargs["env"]["DEV"] == "USB+AMD:LLVM"
  assert external_kwargs["env"]["WARP_DEV"] == "QCOM"
  assert all(flag not in external_kwargs["env"] for flag in ("IMAGE", "NOLOCALS", "OPENPILOT_HACKS"))


def test_gpu_is_external_gpu_cli_alias(monkeypatch):
  monkeypatch.setattr(sys, "argv", ["models", "--model", "large", "--gpu"])
  args = model_compiler.parse_args()
  assert args.external_gpu


def test_requested_model_id_uses_only_staged_source(tmp_path):
  source = tmp_path / "big_driving_supercombo.onnx"
  source.touch()
  assert model_compiler.resolve_model_files(tmp_path, "lebowski") == {
    "driving_supercombo": source,
  }


def test_regular_fat_onnx_is_parsed_in_place(tmp_path, monkeypatch):
  source = tmp_path / "big_driving_supercombo.onnx"
  source.write_bytes(b"model")
  monkeypatch.setattr(file_chunker, "open_file_chunked", lambda _: (_ for _ in ()).throw(AssertionError("must not copy")))

  assert compile_modeld.read_file_chunked_to_disk(source) == str(source)


def test_chunked_fat_onnx_is_streamed_to_disk(tmp_path, monkeypatch):
  payload = b"fat model" * 1024

  class StreamingOnly(io.BytesIO):
    def read(self, size=-1):
      assert size >= 0, "staging must not materialize the whole ONNX"
      return super().read(size)

  monkeypatch.setattr(file_chunker, "open_file_chunked", lambda _: StreamingOnly(payload))
  source = tmp_path / "big_driving_supercombo.onnx"
  staged = compile_modeld.read_file_chunked_to_disk(source)
  try:
    assert staged == f"{source}.unchunked"
    assert Path(staged).read_bytes() == payload
  finally:
    Path(staged).unlink(missing_ok=True)


def test_onnx_preflight_accepts_graph_without_reading_weights(tmp_path):
  source = tmp_path / "model.onnx"
  source.write_bytes(b"\x08\x09\x3a\x02\x12\x00")

  model_compiler.validate_onnx_source(source)


def test_onnx_preflight_rejects_empty_truncated_and_lfs_sources(tmp_path):
  empty = tmp_path / "empty.onnx"
  empty.touch()
  truncated = tmp_path / "truncated.onnx"
  truncated.write_bytes(b"\x3a\x08bad")
  pointer = tmp_path / "pointer.onnx"
  pointer.write_text("version https://git-lfs.github.com/spec/v1\n")

  for source, message in ((empty, "empty"), (truncated, "truncated"), (pointer, "Git LFS pointer")):
    try:
      model_compiler.validate_onnx_source(source)
    except ValueError as error:
      assert message in str(error)
    else:
      raise AssertionError(f"{source} should have failed validation")


def test_dropbox_urls_are_direct_downloads():
  url = "https://www.dropbox.com/scl/fi/id/model.pkl?rlkey=key&st=value&dl=0"
  normalized = download_functions.normalize_download_url(url)
  assert normalized.count("dl=1") == 1
  assert "dl=0" not in normalized
  assert "rlkey=key" in normalized


def test_download_verification_uses_manifest_size_and_sha(tmp_path, monkeypatch):
  artifact = tmp_path / "model.pkl"
  artifact.write_bytes(b"unified model")
  monkeypatch.setattr(download_functions, "get_remote_file_size", lambda *args, **kwargs: 0)

  assert download_functions.verify_download(
    artifact,
    "https://example.com/model.pkl",
    allow_unknown_size=True,
    expected_size=artifact.stat().st_size,
    expected_sha256="02f64c1311bd6392462fa9c7c929b002057f261fdcef2050554c08694e7d2120",
  )
  assert not download_functions.verify_download(
    artifact,
    "https://example.com/model.pkl",
    allow_unknown_size=True,
    expected_size=artifact.stat().st_size + 1,
  )


def test_lfs_pointer_is_not_accepted_as_model(tmp_path, monkeypatch):
  artifact = tmp_path / "model.pkl"
  artifact.write_text(
    "version https://git-lfs.github.com/spec/v1\n"
    f"oid sha256:{'0' * 64}\n"
    "size 123456789\n",
  )
  monkeypatch.setattr(download_functions, "get_remote_file_size", lambda *args, **kwargs: artifact.stat().st_size)
  assert not download_functions.verify_download(artifact, "https://example.com/model.pkl")


def test_multipart_download_is_atomic_and_checksum_verified(tmp_path, monkeypatch):
  payload = b"first part" + b"second part"
  expected_sha = hashlib.sha256(payload).hexdigest()
  part_payloads = {
    "https://example.com/model.pkl.p00": b"first part",
    "https://example.com/model.pkl.p01": b"second part",
  }

  class FakeResponse:
    def __init__(self, data):
      self.data = data
      self.text = data.decode()

    def __enter__(self):
      return self

    def __exit__(self, *args):
      pass

    def raise_for_status(self):
      pass

    def iter_content(self, chunk_size):
      del chunk_size
      yield self.data

  def fake_get(url, **kwargs):
    del kwargs
    if url.endswith(".sha256"):
      return FakeResponse(f"{expected_sha}  model.pkl\n".encode())
    return FakeResponse(part_payloads[url])

  def fake_size(url, **kwargs):
    del kwargs
    return len(part_payloads.get(url, b""))

  class FakeParams:
    def get_bool(self, key):
      del key
      return False

    def put(self, key, value):
      del key, value

  monkeypatch.setattr(download_functions.requests, "get", fake_get)
  monkeypatch.setattr(download_functions, "get_remote_file_size", fake_size)
  destination = tmp_path / "model.pkl"

  assert download_functions.download_multipart_file(
    "cancel", destination, "progress", "https://example.com/model.pkl", "download", FakeParams(),
  )
  assert destination.read_bytes() == payload


def test_multipart_checksum_failure_leaves_no_model(tmp_path, monkeypatch):
  class FakeResponse:
    text = f"{'0' * 64}  model.pkl"

    def __enter__(self):
      return self

    def __exit__(self, *args):
      pass

    def raise_for_status(self):
      pass

    def iter_content(self, chunk_size):
      del chunk_size
      yield b"corrupt"

  monkeypatch.setattr(download_functions.requests, "get", lambda *args, **kwargs: FakeResponse())
  monkeypatch.setattr(
    download_functions,
    "get_remote_file_size",
    lambda url, **kwargs: len(b"corrupt") if url.endswith(".p00") else 0,
  )

  class FakeParams:
    def get_bool(self, key):
      del key
      return False

    def put(self, key, value):
      del key, value

  destination = tmp_path / "model.pkl"
  assert not download_functions.download_multipart_file(
    "cancel", destination, "progress", "https://example.com/model.pkl", "download", FakeParams(),
  )
  assert not destination.exists()


def test_oversized_artifact_split_round_trip(tmp_path):
  artifact = tmp_path / "model.pkl"
  artifact.write_bytes(b"multipart artifact")

  outputs = split_oversized_artifact(artifact, chunk_size=10, force=True)
  part_paths = [path for path in outputs if path.suffix != ".sha256"]
  assert len(part_paths) == 2
  assert b"".join(path.read_bytes() for path in part_paths) == artifact.read_bytes()
