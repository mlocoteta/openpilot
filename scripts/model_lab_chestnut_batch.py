#!/usr/bin/env python3
"""Build and publish Chestnut/AMD variants for every small manifest model.

The queue is intentionally sequential.  It keeps only one ONNX source and one
compiler output on the comma, copies each verified artifact back to the host,
uploads it, then publishes a freshly merged manifest.  The state file makes an
interrupted run resumable without rebuilding completed models.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
  sys.path.insert(0, str(SCRIPTS_DIR))

from model_compiler import detect_component
from model_rebuild_pipeline import ensure_workspace, extract_model, find_model_paths, ensure_git_ref


DEFAULT_REMOTE = os.environ.get("STAR_PILOT_MODEL_REMOTE", "comma@192.168.3.110")
DEFAULT_BUCKET = os.environ.get("STARPILOT_HF_BUCKET", "StarPilot-Driving/StarPilot-Resources")
DEFAULT_ARTIFACT_DIR = Path.home() / "StarPilot-Model-Lab-Artifacts" / "v25"
DEFAULT_MANIFEST = DEFAULT_ARTIFACT_DIR / "model_names_v25.json"
DEFAULT_SOURCE_MAP = SCRIPTS_DIR / "model_source_map_v25.json"
DEFAULT_OPENPILOT = Path.home() / "openpilot"
REMOTE_ROOT = "/data/openpilot"
SSH_OPTIONS = (
  "-o", "ConnectTimeout=10",
  "-o", "ConnectionAttempts=1",
  "-o", "ServerAliveInterval=30",
  "-o", "ServerAliveCountMax=600",
)
RSYNC_SSH = "ssh -o ConnectTimeout=10 -o ConnectionAttempts=1 -o ServerAliveInterval=30 -o ServerAliveCountMax=600"
SAFE_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
COMPONENT_FILENAMES = {
  "driving_supercombo": "driving_supercombo.onnx",
  "driving_vision": "driving_vision.onnx",
  "driving_policy": "driving_policy.onnx",
  "driving_on_policy": "driving_on_policy.onnx",
  "driving_off_policy": "driving_off_policy.onnx",
}


def utc_now() -> str:
  return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_json(path: Path):
  return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  temporary = path.with_suffix(path.suffix + ".tmp")
  temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
  temporary.replace(path)


def sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def run(command: list[str], *, capture: bool = False, check: bool = True, timeout: int | None = None,
        stdout=None, stderr=None) -> subprocess.CompletedProcess:
  return subprocess.run(
    command,
    text=capture,
    capture_output=capture,
    check=check,
    timeout=timeout,
    stdout=stdout,
    stderr=stderr,
  )


def validate_model_id(model_id: str) -> str:
  if not SAFE_MODEL_ID.fullmatch(model_id):
    raise ValueError(f"Unsafe model ID: {model_id!r}")
  return model_id


class Batch:
  def __init__(self, args: argparse.Namespace):
    self.args = args
    self.hf = shutil.which("hf")
    if not self.hf:
      raise FileNotFoundError("Hugging Face CLI (hf) is not installed")
    self.artifact_dir = args.artifact_dir.expanduser().resolve()
    self.workspace = self.artifact_dir / "batch"
    self.sources_workspace = self.workspace / "source-workspace"
    self.sources_dir = self.sources_workspace / "onnx"
    self.logs_dir = self.workspace / "logs"
    self.results_dir = self.workspace / "results"
    self.state_path = self.results_dir / "chestnut_batch_state.json"
    self.manifest_path = args.manifest.expanduser().resolve()
    self.source_map = load_json(args.source_map.expanduser().resolve())
    self.manifest = load_json(self.manifest_path)
    self.models = self.manifest.get("models", self.manifest)
    if not isinstance(self.models, list):
      raise ValueError("Manifest must contain a models list")
    self.models_by_id = {str(model.get("id") or ""): model for model in self.models}
    ensure_workspace(self.sources_workspace)
    self.logs_dir.mkdir(parents=True, exist_ok=True)
    self.results_dir.mkdir(parents=True, exist_ok=True)
    self.state = self._load_state()
    self.inventory = self._load_inventory()

  @property
  def bucket_root(self) -> str:
    return f"hf://buckets/{self.args.bucket}"

  def _load_state(self) -> dict:
    if self.state_path.is_file():
      state = load_json(self.state_path)
      state.setdefault("models", {})
      state["resumed_at"] = utc_now()
      return state
    return {
      "remote": self.args.remote,
      "bucket": self.args.bucket,
      "started_at": utc_now(),
      "models": {},
    }

  def save_state(self) -> None:
    self.state["updated_at"] = utc_now()
    write_json(self.state_path, self.state)

  def _load_inventory(self) -> dict[str, list[dict]]:
    result = run(
      [self.hf, "buckets", "ls", "-R", f"{self.bucket_root}/onnx/", "--format", "json"],
      capture=True,
    )
    entries = json.loads(result.stdout)
    inventory: dict[str, list[dict]] = {}
    for entry in entries:
      path = str(entry.get("path") or "")
      parts = Path(path).parts
      if len(parts) == 3 and parts[0] == "onnx" and path.endswith(".onnx"):
        inventory.setdefault(parts[1], []).append(entry)
    return inventory

  def selected_models(self) -> list[dict]:
    requested = {validate_model_id(value) for value in self.args.ids.split(",") if value} if self.args.ids else set()
    selected = [model for model in self.models if not bool(model.get("uses_external_gpu", False))]
    if requested:
      unknown = requested - self.models_by_id.keys()
      if unknown:
        raise ValueError(f"Unknown manifest model IDs: {', '.join(sorted(unknown))}")
      selected = [model for model in selected if model["id"] in requested]
    if self.args.limit:
      selected = selected[:self.args.limit]
    return selected

  def source_plan(self, model: dict) -> dict:
    model_id = validate_model_id(model["id"])
    source = self.source_map.get(model_id)
    if not isinstance(source, dict):
      raise KeyError(f"No source mapping for small model {model_id}")
    source_id = validate_model_id(str(source.get("source_id") or model_id))
    archived = self.inventory.get(source_id, [])
    if archived:
      components = [detect_component(Path(entry["path"])) for entry in archived]
      if None in components or len(set(components)) != len(components):
        raise ValueError(f"Ambiguous archived ONNX components for {model_id} ({source_id})")
      self._validate_components(model_id, source["input_format"], set(components))
      signature_payload = {
        "input_format": source["input_format"],
        "version": str(model.get("version") or ""),
        "files": sorted(
          (detect_component(Path(entry["path"])), str(entry.get("xet_hash") or ""), int(entry.get("size") or 0))
          for entry in archived
        ),
      }
      signature = hashlib.sha256(json.dumps(signature_payload, sort_keys=True).encode()).hexdigest()
      return {"kind": "archive", "source_id": source_id, "files": archived, "signature": signature, **source}

    repo = self.args.openpilot.expanduser().resolve()
    ensure_git_ref(repo, source["ref"])
    paths = find_model_paths(repo, source["ref"], source["input_format"], False)
    components = {detect_component(Path(path)) for path in paths}
    self._validate_components(model_id, source["input_format"], components)
    signature = hashlib.sha256(
      f"git:{source['ref']}:{source['input_format']}:{model.get('version', '')}".encode()
    ).hexdigest()
    return {"kind": "git", "source_id": source_id, "files": paths, "signature": signature, **source}

  @staticmethod
  def _validate_components(model_id: str, input_format: str, components: set[str | None]) -> None:
    if input_format == "supercombo" and components != {"driving_supercombo"}:
      raise ValueError(f"{model_id} needs one supercombo source, found {sorted(str(c) for c in components)}")
    if input_format == "split" and (
      "driving_vision" not in components or not {"driving_policy", "driving_on_policy"} & components
    ):
      raise ValueError(f"{model_id} has incomplete split sources: {sorted(str(c) for c in components)}")

  def audit(self) -> dict:
    selected = self.selected_models()
    report = {"total": len(selected), "archive": [], "git": [], "failures": {}}
    for model in selected:
      model_id = model["id"]
      try:
        plan = self.source_plan(model)
        report[plan["kind"]].append(model_id)
      except Exception as error:
        report["failures"][model_id] = str(error)
    report["ready"] = report["total"] - len(report["failures"])
    print(json.dumps(report, indent=2), flush=True)
    return report

  def remote(self, command: str, *, capture: bool = False, check: bool = True,
             timeout: int | None = None, stdout=None, stderr=None) -> subprocess.CompletedProcess:
    return run(
      ["ssh", *SSH_OPTIONS, self.args.remote, command],
      capture=capture,
      check=check,
      timeout=timeout,
      stdout=stdout,
      stderr=stderr,
    )

  def hardware_preflight(self) -> None:
    command = (
      f"set -eu; cd {shlex.quote(REMOTE_ROOT)}; "
      "test \"$(cat /data/params/d/IsOffroad 2>/dev/null)\" = 1; "
      "/usr/local/venv/bin/python3 -c "
      + shlex.quote("from openpilot.system.hardware.chestnut.flash import link_up; raise SystemExit(0 if link_up() else 1)")
      + "; test -x /data/openpilot/models"
    )
    result = self.remote(command, capture=True, check=False, timeout=20)
    if result.returncode:
      raise RuntimeError("Comma must be reachable, offroad, and connected to an active Chestnut PCIe link")

  def active_remote_compiles(self) -> list[str]:
    result = self.remote("pgrep -af '[c]ompile_modeld.py' || true", capture=True, check=False, timeout=20)
    if result.returncode and not result.stdout:
      raise RuntimeError(f"Could not inspect remote compiler: {result.stderr.strip()}")
    return [line for line in result.stdout.splitlines() if line.strip()]

  def wait_for_remote_idle(self) -> None:
    active = self.active_remote_compiles()
    while active:
      print(f"REMOTE_BUSY processes={len(active)}", flush=True)
      time.sleep(30)
      active = self.active_remote_compiles()

  def _source_dir(self, model_id: str) -> Path:
    return self.sources_dir / validate_model_id(model_id)

  def prepare_source(self, model: dict, plan: dict) -> Path:
    model_id = model["id"]
    source_dir = self._source_dir(model_id)
    if source_dir.is_dir():
      shutil.rmtree(source_dir)
    source_dir.mkdir(parents=True)
    if plan["kind"] == "archive":
      for entry in plan["files"]:
        component = detect_component(Path(entry["path"]))
        if component is None:
          raise ValueError(f"Unknown source component: {entry['path']}")
        destination = source_dir / f"{model_id}_{COMPONENT_FILENAMES[component]}"
        run([
          self.hf, "buckets", "cp",
          f"{self.bucket_root}/{entry['path']}", str(destination), "--format", "quiet",
        ])
        expected_size = int(entry.get("size") or 0)
        if expected_size and destination.stat().st_size != expected_size:
          raise ValueError(f"Downloaded source size mismatch for {destination.name}")
    else:
      extract_model(model_id, self.source_map[model_id], self.args.openpilot.expanduser().resolve(), self.sources_workspace)
      for path in sorted(source_dir.glob("*.onnx")):
        component = detect_component(path)
        if component is None:
          raise ValueError(f"Unknown extracted source component: {path.name}")
        archive_name = f"{plan['source_id']}_{COMPONENT_FILENAMES[component]}"
        destination = f"{self.bucket_root}/onnx/{plan['source_id']}/{archive_name}"
        run([self.hf, "buckets", "cp", str(path), destination, "--format", "quiet"])
      print(f"SOURCE_ARCHIVED id={model_id} source_id={plan['source_id']}", flush=True)
    return source_dir

  def remote_paths(self, model_id: str) -> tuple[str, str]:
    validate_model_id(model_id)
    return (
      f"{REMOTE_ROOT}/uncompiledmodels/{model_id}",
      f"{REMOTE_ROOT}/compiledmodels/{model_id}_driving_tinygrad.pkl",
    )

  def cleanup_remote(self, model_id: str, *, source: bool = True, output: bool = True) -> None:
    remote_source, remote_output = self.remote_paths(model_id)
    targets = []
    if source:
      targets.append(shlex.quote(remote_source))
    if output:
      targets.append(shlex.quote(remote_output))
    if targets:
      self.remote("rm -rf -- " + " ".join(targets), check=False, timeout=30)

  def stage_source(self, model_id: str, source_dir: Path) -> None:
    remote_source, _ = self.remote_paths(model_id)
    self.cleanup_remote(model_id)
    self.remote(f"mkdir -p {shlex.quote(remote_source)} {shlex.quote(REMOTE_ROOT + '/compiledmodels')}")
    run([
      "rsync", "-az", "-e", RSYNC_SSH, "--exclude=._*",
      f"{source_dir}/", f"{self.args.remote}:{remote_source}/",
    ])

  def compile(self, model: dict, plan: dict) -> Path:
    model_id = model["id"]
    remote_source, remote_output = self.remote_paths(model_id)
    command = " ".join([
      f"cd {shlex.quote(REMOTE_ROOT)} && ./models",
      "--model", shlex.quote(model_id),
      "--input-dir", shlex.quote(remote_source),
      "--output-dir", shlex.quote(REMOTE_ROOT + "/compiledmodels"),
      "--input-format", shlex.quote(plan["input_format"]),
      "--version", shlex.quote(str(model.get("version") or "")),
      "--gpu", "--no-split",
    ])
    log_path = self.logs_dir / f"{model_id}.log"
    print(f"COMPILE_START id={model_id} source={plan['kind']} version={model.get('version', '')}", flush=True)
    started = time.monotonic()
    with log_path.open("ab") as log:
      log.write(f"\n=== START {utc_now()} ===\n".encode())
      result = self.remote(command, check=False, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
      self.wait_for_remote_idle()
      if not self.remote_file_exists(remote_output):
        raise RuntimeError(f"Chestnut compilation failed; see {log_path}")
    elapsed = time.monotonic() - started
    print(f"COMPILE_DONE id={model_id} seconds={elapsed:.1f}", flush=True)
    return self.pull_artifact(model_id)

  def remote_file_exists(self, path: str) -> bool:
    result = self.remote(f"test -f {shlex.quote(path)}", check=False, timeout=20)
    return result.returncode == 0

  def pull_artifact(self, model_id: str) -> Path:
    _, remote_output = self.remote_paths(model_id)
    destination = self.artifact_dir / f"{model_id}_driving_chestnut_tinygrad.pkl"
    incoming = destination.with_suffix(destination.suffix + ".incoming")
    incoming.unlink(missing_ok=True)
    run(["rsync", "-az", "-e", RSYNC_SSH, f"{self.args.remote}:{remote_output}", str(incoming)])
    if not incoming.is_file() or incoming.stat().st_size == 0:
      raise FileNotFoundError(f"No compiler output for {model_id}")
    incoming.replace(destination)
    destination.chmod(0o644)
    return destination

  def artifact_metadata(self, model_id: str, artifact: Path) -> dict:
    expected_name = f"{model_id}_driving_chestnut_tinygrad.pkl"
    if artifact.name != expected_name or not artifact.is_file():
      raise ValueError(f"Invalid local Chestnut artifact path for {model_id}: {artifact}")
    return {
      "artifact_format": "tinygrad_single_v1",
      "artifact_filename": artifact.name,
      "artifact_size": artifact.stat().st_size,
      "artifact_sha256": sha256_file(artifact),
      "artifact_chunk_count": 0,
      "execution_device": "AMD",
    }

  def upload_artifact(self, model_id: str, artifact: Path) -> None:
    destination = f"{self.bucket_root}/models/v25/{model_id}/{artifact.name}"
    run([self.hf, "buckets", "cp", str(artifact), destination, "--format", "quiet"])
    listing = run([self.hf, "buckets", "ls", "-R", destination, "--format", "json"], capture=True)
    entries = json.loads(listing.stdout)
    if len(entries) != 1 or int(entries[0].get("size") or 0) != artifact.stat().st_size:
      raise RuntimeError(f"Uploaded artifact verification failed for {model_id}")

  def completed_metadata(self) -> dict[str, dict]:
    completed = {}
    for model_id, record in self.state.get("models", {}).items():
      if record.get("status") == "published" and isinstance(record.get("artifact"), dict):
        completed[model_id] = record["artifact"]
    return completed

  def publish_manifest(self) -> None:
    incoming = self.workspace / "live_manifest.json"
    run([
      self.hf, "buckets", "cp",
      f"{self.bucket_root}/manifests/model_names_v25.json", str(incoming), "--format", "quiet",
    ])
    payload = load_json(incoming)
    models = payload.get("models", payload)
    completed = self.completed_metadata()
    for model in models:
      if bool(model.get("uses_external_gpu", False)):
        continue
      model["model_size"] = "small"
      model["model_lab_eligible"] = True
      if model["id"] in completed:
        artifacts = model.get("accelerator_artifacts")
        if not isinstance(artifacts, dict):
          artifacts = {}
        artifacts["chestnut"] = completed[model["id"]]
        model["accelerator_artifacts"] = artifacts
    write_json(self.manifest_path, payload if isinstance(payload, dict) else {"models": models})
    run([
      self.hf, "buckets", "cp", str(self.manifest_path),
      f"{self.bucket_root}/manifests/model_names_v25.json", "--format", "quiet",
    ])
    print(f"MANIFEST_PUBLISHED completed={len(completed)}", flush=True)

  def valid_existing_artifact(self, model_id: str) -> tuple[Path, dict] | None:
    path = self.artifact_dir / f"{model_id}_driving_chestnut_tinygrad.pkl"
    if not path.is_file():
      return None
    metadata = self.artifact_metadata(model_id, path)
    manifest_artifact = (
      self.models_by_id[model_id].get("accelerator_artifacts", {}).get("chestnut", {})
      if isinstance(self.models_by_id[model_id].get("accelerator_artifacts"), dict) else {}
    )
    if (manifest_artifact.get("artifact_size") == metadata["artifact_size"]
        and manifest_artifact.get("artifact_sha256") == metadata["artifact_sha256"]):
      return path, metadata
    state_artifact = self.state.get("models", {}).get(model_id, {}).get("artifact", {})
    if (state_artifact.get("artifact_size") == metadata["artifact_size"]
        and state_artifact.get("artifact_sha256") == metadata["artifact_sha256"]):
      return path, metadata
    return None

  @staticmethod
  def source_record(plan: dict) -> dict:
    return {
      "kind": plan["kind"],
      "source_id": plan["source_id"],
      "ref": plan["ref"],
      "signature": plan["signature"],
    }

  def equivalent_artifact(self, model_id: str, plan: dict) -> tuple[str, Path] | None:
    """Find a completed artifact built from byte-identical ONNXs and ABI."""
    for candidate_id, record in self.state.get("models", {}).items():
      if candidate_id == model_id or record.get("status") != "published":
        continue
      candidate_signature = record.get("source", {}).get("signature")
      if not candidate_signature and candidate_id in self.models_by_id:
        try:
          candidate_signature = self.source_plan(self.models_by_id[candidate_id])["signature"]
        except Exception:
          continue
      candidate_path = self.artifact_dir / f"{candidate_id}_driving_chestnut_tinygrad.pkl"
      if candidate_signature == plan["signature"] and candidate_path.is_file():
        return candidate_id, candidate_path
    return None

  def process_model(self, model: dict) -> None:
    model_id = model["id"]
    plan = self.source_plan(model)
    existing = self.valid_existing_artifact(model_id)
    if existing:
      artifact, metadata = existing
      if self.state.get("models", {}).get(model_id, {}).get("status") != "published":
        self.upload_artifact(model_id, artifact)
      self.state["models"][model_id] = {
        "status": "published",
        "source": self.source_record(plan),
        "artifact": metadata,
        "completed_at": utc_now(),
      }
      self.save_state()
      print(f"SKIP_VERIFIED id={model_id} bytes={metadata['artifact_size']}", flush=True)
      return

    equivalent = self.equivalent_artifact(model_id, plan)
    if equivalent:
      source_model_id, source_artifact = equivalent
      artifact = self.artifact_dir / f"{model_id}_driving_chestnut_tinygrad.pkl"
      shutil.copy2(source_artifact, artifact)
      metadata = self.artifact_metadata(model_id, artifact)
      self.upload_artifact(model_id, artifact)
      self.state["models"][model_id] = {
        "status": "published",
        "source": self.source_record(plan),
        "derived_from": source_model_id,
        "artifact": metadata,
        "completed_at": utc_now(),
      }
      self.save_state()
      print(f"PUBLISHED_DEDUP id={model_id} identical_to={source_model_id} bytes={metadata['artifact_size']}", flush=True)
      return

    self.hardware_preflight()
    self.wait_for_remote_idle()
    source_dir = self.prepare_source(model, plan)
    try:
      self.stage_source(model_id, source_dir)
      artifact = self.compile(model, plan)
      metadata = self.artifact_metadata(model_id, artifact)
      self.upload_artifact(model_id, artifact)
      self.state["models"][model_id] = {
        "status": "published",
        "source": self.source_record(plan),
        "artifact": metadata,
        "completed_at": utc_now(),
      }
      self.save_state()
      print(f"PUBLISHED id={model_id} bytes={metadata['artifact_size']} sha256={metadata['artifact_sha256']}", flush=True)
    finally:
      self.cleanup_remote(model_id)
      if source_dir.is_dir():
        shutil.rmtree(source_dir)

  def run_queue(self) -> int:
    selected = self.selected_models()
    audit = self.audit()
    if audit["failures"]:
      raise RuntimeError(f"Source audit failed for {len(audit['failures'])} small models")
    if self.args.dry_run:
      return 0

    failures = 0
    for index, model in enumerate(selected, 1):
      model_id = model["id"]
      print(f"QUEUE index={index}/{len(selected)} id={model_id}", flush=True)
      try:
        self.process_model(model)
      except Exception as error:
        failures += 1
        self.state["models"][model_id] = {
          "status": "failed",
          "error": str(error),
          "failed_at": utc_now(),
        }
        self.save_state()
        print(f"FAILED id={model_id} error={error}", file=sys.stderr, flush=True)
        if self.args.stop_on_failure:
          break
        continue
      if not self.args.no_publish:
        try:
          self.publish_manifest()
        except Exception as error:
          failures += 1
          self.state["manifest_error"] = {"error": str(error), "at": utc_now(), "after_model": model_id}
          self.save_state()
          print(f"MANIFEST_FAILED after={model_id} error={error}", file=sys.stderr, flush=True)
          if self.args.stop_on_failure:
            break
    self.state["finished_at"] = utc_now()
    self.state["failures"] = failures
    self.save_state()
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("command", choices=("audit", "run"), nargs="?", default="run")
  parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
  parser.add_argument("--source-map", type=Path, default=DEFAULT_SOURCE_MAP)
  parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
  parser.add_argument("--openpilot", type=Path, default=DEFAULT_OPENPILOT)
  parser.add_argument("--remote", default=DEFAULT_REMOTE)
  parser.add_argument("--bucket", default=DEFAULT_BUCKET)
  parser.add_argument("--ids", default="", help="Optional comma-separated manifest model IDs")
  parser.add_argument("--limit", type=int, default=0)
  parser.add_argument("--dry-run", action="store_true")
  parser.add_argument("--no-publish", action="store_true")
  parser.add_argument("--stop-on-failure", action="store_true")
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  batch = Batch(args)
  if args.command == "audit":
    return 1 if batch.audit()["failures"] else 0
  return batch.run_queue()


if __name__ == "__main__":
  raise SystemExit(main())
