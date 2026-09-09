#!/usr/bin/env python3
"""Compile staged v25 models on the desktop comma and publish their artifacts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = Path("/Volumes/agnos/StarPilot-v25-rebuild-2026-09-03")
SOURCE_MAP = REPO_ROOT / "scripts/model_source_map_v25.json"
BASE_MANIFEST = WORKSPACE / "manifests/model_names_v25.json"
READY_DIR = WORKSPACE / "ready-for-resources"
RESULTS_DIR = WORKSPACE / "results"
LOG_DIR = WORKSPACE / "logs"
REMOTE = "comma@192.168.3.111"
HF = Path.home() / ".local/bin/hf"
HF_BUCKET = "StarPilot-Driving/StarPilot-Resources"
MANIFEST_VERSION = "v25"

SKIP_COMPILE = {"bmrlnapv6"}


def write_json(path: Path, payload: object) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  temporary = path.with_suffix(path.suffix + ".tmp")
  temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
  temporary.replace(path)


def artifact_paths(model_id: str) -> list[Path]:
  prefix = f"{model_id}_driving_tinygrad.pkl"
  return sorted(path for path in READY_DIR.glob(f"{prefix}*") if path.is_file())


def upload_file(path: Path, remote_path: str) -> None:
  destination = f"hf://buckets/{HF_BUCKET}/{remote_path}"
  for attempt in range(1, 4):
    result = subprocess.run(
      [str(HF), "buckets", "cp", str(path), destination, "--format", "quiet"],
      text=True,
      capture_output=True,
      check=False,
    )
    if result.returncode == 0:
      return
    if attempt == 3:
      detail = (result.stderr or result.stdout).strip()
      raise RuntimeError(f"HF upload failed for {path.name}: {detail}")
    time.sleep(attempt * 10)


def upload_model(model_id: str) -> list[str]:
  paths = artifact_paths(model_id)
  if not paths:
    raise FileNotFoundError(f"No ready artifact files for {model_id}")
  uploaded = []
  for path in paths:
    upload_file(path, f"models/{MANIFEST_VERSION}/{model_id}/{path.name}")
    uploaded.append(path.name)
  return uploaded


def run_compile(model_id: str) -> None:
  environment = os.environ.copy()
  environment["STAR_PILOT_MODEL_REMOTE"] = REMOTE
  environment["PYTHONUNBUFFERED"] = "1"
  command = [
    sys.executable,
    str(REPO_ROOT / "scripts/model_rebuild_pipeline.py"),
    "compile",
    "--model",
    model_id,
    "--workspace",
    str(WORKSPACE),
    "--source-map",
    str(SOURCE_MAP),
    "--base-manifest",
    str(BASE_MANIFEST),
  ]
  log_path = LOG_DIR / f"overnight-{model_id}.log"
  with log_path.open("ab") as log:
    log.write(f"\n=== START {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} ===\n".encode())
    result = subprocess.run(command, cwd=REPO_ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
  if result.returncode:
    raise RuntimeError(f"Compilation failed; see {log_path}")


def remote_compile_ids() -> set[str]:
  """Return model IDs currently compiling on the device.

  SSH can time out while the remote process survives. Checking the device
  before starting another model prevents two compiles from sharing the GPU.
  """
  result = subprocess.run(
    [
      "ssh",
      "-o",
      "ConnectTimeout=10",
      "-o",
      "ConnectionAttempts=1",
      "-o",
      "ServerAliveInterval=30",
      "-o",
      "ServerAliveCountMax=600",
      REMOTE,
      "pgrep -af '[c]ompile_modeld.py' || true",
    ],
    text=True,
    capture_output=True,
    timeout=20,
    check=False,
  )
  if result.returncode and not result.stdout:
    raise RuntimeError(f"Could not inspect remote compiler: {result.stderr.strip()}")
  model_ids = set()
  for line in result.stdout.splitlines():
    marker = "/compiledmodels/"
    suffix = "_driving_tinygrad.pkl"
    if marker in line and suffix in line:
      model_ids.add(line.split(marker, 1)[1].split(suffix, 1)[0].split()[0])
  return model_ids


def wait_for_remote_idle() -> set[str]:
  active = remote_compile_ids()
  while active:
    print(f"  waiting for remote compiler(s): {', '.join(sorted(active))}", flush=True)
    time.sleep(30)
    active = remote_compile_ids()
  return active


def recover_remote_artifact(model_id: str) -> bool:
  """Pull a valid artifact left behind after an SSH disconnect."""
  local_output = WORKSPACE / "compiled" / f"{model_id}_driving_tinygrad.pkl"
  os.environ["STAR_PILOT_MODEL_REMOTE"] = REMOTE
  from model_rebuild_pipeline import pull_remote_artifact, stage_ready_artifact

  try:
    pull_remote_artifact(
      f"/data/openpilot/compiledmodels/{model_id}_driving_tinygrad.pkl",
      local_output,
    )
  except (FileNotFoundError, ValueError, subprocess.CalledProcessError, OSError):
    return False
  local_output.chmod(0o644)
  stage_ready_artifact(local_output, WORKSPACE)
  return True


def prepare_model(model_id: str) -> None:
  """Recover a completed orphan first, otherwise wait before compiling."""
  active = remote_compile_ids()
  if not active:
    if recover_remote_artifact(model_id):
      print(f"  recovered completed remote artifact for {model_id}", flush=True)
    return
  print(f"  remote compile detected before {model_id}: {', '.join(sorted(active))}", flush=True)
  wait_for_remote_idle()
  if model_id in active and recover_remote_artifact(model_id):
    print(f"  recovered {model_id} after remote SSH disconnect", flush=True)


def recover_after_failure(model_id: str) -> bool:
  """Recover a valid remote result instead of launching a concurrent retry."""
  active = remote_compile_ids()
  if active:
    print(f"  compile session ended locally; waiting on remote: {', '.join(sorted(active))}", flush=True)
    wait_for_remote_idle()
  return recover_remote_artifact(model_id)


def main() -> int:
  if not BASE_MANIFEST.is_file():
    raise FileNotFoundError(f"Expected current HF manifest at {BASE_MANIFEST}")
  source_map = json.loads(SOURCE_MAP.read_text())
  manifest = json.loads(BASE_MANIFEST.read_text())
  manifest_models = manifest.get("models", manifest)
  manifest_by_id = {model["id"]: model for model in manifest_models}
  manifest_ids = set(manifest_by_id)
  staged_ids = sorted(
    path.name for path in (WORKSPACE / "onnx").iterdir()
    if path.is_dir() and any(path.glob("*.onnx"))
  )
  requested_ids = {
    model_id.strip() for model_id in os.environ.get("STAR_PILOT_MODEL_IDS", "").split(",")
    if model_id.strip()
  }
  if requested_ids:
    staged_ids = [model_id for model_id in staged_ids if model_id in requested_ids]
  for model_id in staged_ids:
    source_map.setdefault(model_id, {
      "input_format": "auto",
      "uses_external_gpu": bool(manifest_by_id.get(model_id, {}).get("uses_external_gpu")),
    })
  missing_from_manifest = sorted(set(staged_ids) - manifest_ids)
  if missing_from_manifest:
    raise ValueError(f"Staged IDs missing from v25 manifest: {', '.join(missing_from_manifest)}")

  status_path = RESULTS_DIR / "overnight_status.json"
  status = {
    "remote": REMOTE,
    "manifest": f"models/{MANIFEST_VERSION}",
    "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "models": {},
    "unresolved_sources": ["berightthere", "rdf53", "rdf63"],
  }
  write_json(status_path, status)

  for model_id in staged_ids:
    if model_id in SKIP_COMPILE:
      status["models"][model_id] = {"status": "skipped_existing_artifact"}
      write_json(status_path, status)
      continue
    try:
      artifact = WORKSPACE / "compiled" / f"{model_id}_driving_tinygrad.pkl"
      if not artifact.is_file():
        prepare_model(model_id)
      if not artifact.is_file():
        try:
          run_compile(model_id)
        except Exception:
          if not recover_after_failure(model_id):
            raise
      uploaded = upload_model(model_id)
      status["models"][model_id] = {"status": "compiled_uploaded", "files": uploaded}
    except Exception as error:
      status["models"][model_id] = {"status": "failed", "error": str(error)}
    write_json(status_path, status)

  try:
    upload_file(BASE_MANIFEST, f"manifests/model_names_{MANIFEST_VERSION}.json")
    status["manifest_status"] = "uploaded"
  except Exception as error:
    status["manifest_status"] = "failed"
    status["manifest_error"] = str(error)
  status["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
  write_json(status_path, status)
  return 0 if status.get("manifest_status") == "uploaded" else 1


if __name__ == "__main__":
  raise SystemExit(main())
