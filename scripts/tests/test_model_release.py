from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import model_release
from scripts.model_release import (
  ReleaseError,
  parse_lfs_pointer,
  parse_pasted_release,
  prepare_huggingface_manifest,
  refresh_huggingface_manifest,
  runtime_file,
  update_manifest,
  upload_huggingface,
  validate_manifest_update,
)


RELEASE_TEXT = """
**BRANCH UPDATED — BIG**
[remove-avgpool](https://github.com/commaai/openpilot/pull/38681) #38681 [big] (Branch v5)
**Changed Files**
[big_driving_supercombo](https://github.com/commaai/openpilot/blob/remove-avgpool/openpilot/selfdrive/modeld/models/big_driving_supercombo.onnx)
**Recent Commits [f877]**
[f877d7a0ccc3cce943c76e285214c020cd65c899](https://github.com/commaai/openpilot/commit/f877d7a0ccc3cce943c76e285214c020cd65c899)
[faster compile](https://github.com/commaai/openpilot/commit/83a461eb4f0cb5737132c24b7a5ad5de46fc0fbb)
**Next Model Version [big]**
Model v4

Bmrlnap v4 (August 30, 2026) f877
"""


def test_parse_release_block():
  info = parse_pasted_release(RELEASE_TEXT, None, "v16")
  assert info.model_id == "bmrlnapv4"
  assert info.display_name == "Bmrlnap v4"
  assert info.release_date == "2026-08-30"
  assert info.branch == "remove-avgpool"
  assert info.source_ref == "f877d7a0ccc3cce943c76e285214c020cd65c899"
  assert info.source_path.endswith("big_driving_supercombo.onnx")
  assert info.input_format == "supercombo"
  assert info.uses_external_gpu
  assert info.commits == [
    "f877d7a0ccc3cce943c76e285214c020cd65c899",
    "83a461eb4f0cb5737132c24b7a5ad5de46fc0fbb",
  ]


def test_lfs_pointer_parser():
  pointer = (
    b"version https://git-lfs.github.com/spec/v1\n"
    b"oid sha256:" + b"a" * 64 + b"\n"
    b"size 123\n"
  )
  assert parse_lfs_pointer(pointer) == ("a" * 64, 123)


def test_sha_only_resolves_commit_metadata(monkeypatch):
  commit = "f877d7a0ccc3cce943c76e285214c020cd65c899"
  payloads = {
    f"https://api.github.com/repos/commaai/openpilot/commits/{commit}": {
      "commit": {"committer": {"date": "2026-08-31T00:41:06Z"}},
      "files": [{"filename": "openpilot/selfdrive/modeld/models/big_driving_supercombo.onnx"}],
    },
    f"https://api.github.com/repos/commaai/openpilot/commits/{commit}/pulls": [
      {"title": "BMRLNAP", "head": {"sha": commit, "ref": "remove-avgpool"}},
    ],
  }

  monkeypatch.setattr(model_release, "get_json_value", lambda url: payloads[url])
  info = parse_pasted_release(commit, None, "v16")

  assert info.model_id == "bmrlnap"
  assert info.display_name == "BMRLNAP"
  assert info.release_date == "2026-08-30"
  assert info.branch == "remove-avgpool"
  assert info.source_ref == commit
  assert info.source_path.endswith("big_driving_supercombo.onnx")
  assert info.uses_external_gpu


def test_runtime_scan_excludes_model_weights_but_flags_runtime_code():
  assert not runtime_file("openpilot/selfdrive/modeld/models/big_driving_supercombo.onnx")
  assert runtime_file("openpilot/selfdrive/modeld/compile_modeld.py")
  assert runtime_file("tinygrad/engine/jit.py")
  assert not runtime_file("README.md")


def test_update_manifest_replaces_one_entry(tmp_path: Path):
  manifest = tmp_path / "model_names_v25.json"
  manifest.write_text(json.dumps({"models": [{"id": "old"}]}) + "\n")
  info = parse_pasted_release(RELEASE_TEXT, "bmrlnapv4", "v16")
  path = update_manifest(
    tmp_path,
    info,
    {"size": 123, "sha256": "a" * 64, "chunk_count": 2},
    "v25",
  )
  payload = json.loads(path.read_text())
  assert len(payload["models"]) == 2
  entry = payload["models"][1]
  assert entry["id"] == "bmrlnapv4"
  assert entry["artifact_size"] == 123
  assert entry["artifact_chunk_count"] == 2
  assert entry["uses_external_gpu"]


def test_prepare_manifest_refreshes_live_copy_before_adding_model(tmp_path: Path, monkeypatch):
  manifest = tmp_path / "model_names_v25.json"
  manifest.write_text(json.dumps({"models": [{"id": "stale"}]}) + "\n")
  live_payload = {
    "models": [{
      "id": "small-model",
      "model_lab_eligible": True,
      "accelerator_artifacts": {
        "chestnut": {
          "artifact_filename": "small-model_driving_chestnut_tinygrad.pkl",
          "artifact_sha256": "b" * 64,
          "execution_device": "AMD",
        },
      },
    }],
  }

  def fake_refresh(path, bucket):
    assert bucket == "StarPilot-Driving/StarPilot-Resources"
    path.write_text(json.dumps(live_payload) + "\n")
    return live_payload

  monkeypatch.setattr(model_release, "refresh_huggingface_manifest", fake_refresh)
  info = parse_pasted_release(RELEASE_TEXT, "bmrlnapv4", "v16")
  prepared = prepare_huggingface_manifest(
    manifest,
    info,
    {"size": 123, "sha256": "a" * 64, "chunk_count": 2},
    "StarPilot-Driving/StarPilot-Resources",
    "v25",
  )

  models = {entry["id"]: entry for entry in json.loads(prepared.read_text())["models"]}
  assert set(models) == {"small-model", "bmrlnapv4"}
  assert models["small-model"] == live_payload["models"][0]
  assert models["bmrlnapv4"]["artifact_sha256"] == "a" * 64


def test_manifest_guard_rejects_unrelated_accelerator_metadata_regression():
  chestnut = {"execution_device": "AMD", "artifact_sha256": "a" * 64}
  before = {"models": [
    {"id": "keep", "accelerator_artifacts": {"chestnut": chestnut}},
    {"id": "replace", "accelerator_artifacts": {"chestnut": chestnut}},
  ]}
  after = {"models": [{"id": "keep"}, {"id": "replace"}]}

  with pytest.raises(ReleaseError, match="keep:chestnut"):
    validate_manifest_update(before, after, "replace")

  validate_manifest_update(
    {"models": [{"id": "replace", "accelerator_artifacts": {"chestnut": chestnut}}]},
    {"models": [{"id": "replace"}]},
    "replace",
  )

  with pytest.raises(ReleaseError, match="unrelated model entries: keep"):
    validate_manifest_update(
      {"models": [{"id": "keep", "model_lab_eligible": True}]},
      {"models": [{"id": "keep", "model_lab_eligible": False}, {"id": "replace"}]},
      "replace",
    )


def test_refresh_manifest_is_atomic_and_uses_hugging_face_bucket(tmp_path: Path, monkeypatch):
  manifest = tmp_path / "model_names_v25.json"
  manifest.write_text(json.dumps({"models": [{"id": "stale"}]}) + "\n")
  live_payload = {"models": [{"id": "live"}]}
  commands = []

  monkeypatch.setattr(model_release, "find_hf", lambda: "/usr/bin/hf")

  def fake_run(command, **kwargs):
    commands.append(command)
    Path(command[4]).write_text(json.dumps(live_payload) + "\n")

  monkeypatch.setattr(model_release, "run", fake_run)
  assert refresh_huggingface_manifest(manifest, "owner/resources") == live_payload
  assert json.loads(manifest.read_text()) == live_payload
  assert commands[0][0:4] == [
    "/usr/bin/hf",
    "buckets",
    "cp",
    "hf://buckets/owner/resources/manifests/model_names_v25.json",
  ]


def test_refresh_manifest_keeps_local_copy_when_live_json_is_invalid(tmp_path: Path, monkeypatch):
  manifest = tmp_path / "model_names_v25.json"
  original = {"models": [{"id": "safe"}]}
  manifest.write_text(json.dumps(original) + "\n")
  monkeypatch.setattr(model_release, "find_hf", lambda: "/usr/bin/hf")
  monkeypatch.setattr(model_release, "run", lambda command, **kwargs: Path(command[4]).write_text("{"))

  with pytest.raises(ReleaseError, match="Invalid live Hugging Face manifest"):
    refresh_huggingface_manifest(manifest, "owner/resources")
  assert json.loads(manifest.read_text()) == original


def test_upload_refreshes_manifest_after_artifacts(tmp_path: Path, monkeypatch):
  artifact_dir = tmp_path / "artifacts"
  artifact_dir.mkdir()
  manifest = tmp_path / "resources" / "model_names_v25.json"
  manifest.parent.mkdir()
  manifest.write_text(json.dumps({"models": [{"id": "old"}]}) + "\n")
  source = tmp_path / "model.onnx"
  calls = []
  info = parse_pasted_release(RELEASE_TEXT, "bmrlnapv4", "v16")
  result = {
    "path": str(artifact_dir),
    "files": ["bmrlnapv4_driving_tinygrad.pkl"],
    "size": 123,
    "sha256": "a" * 64,
    "chunk_count": 0,
  }

  monkeypatch.setattr(model_release, "hf_copy", lambda source, bucket, remote: calls.append(("copy", remote)))

  def fake_prepare(path, release_info, release_result, bucket, version):
    calls.append(("prepare", path.name))
    return path

  monkeypatch.setattr(model_release, "prepare_huggingface_manifest", fake_prepare)
  returned = upload_huggingface(
    info, result, tmp_path, "owner/resources", "v25", manifest, True, source,
  )

  assert returned == manifest
  assert calls == [
    ("copy", "models/v25/bmrlnapv4/bmrlnapv4_driving_tinygrad.pkl"),
    ("copy", "onnx/bmrlnapv4/model.onnx"),
    ("prepare", "model_names_v25.json"),
    ("copy", "manifests/model_names_v25.json"),
  ]
