#!/usr/bin/env python3
"""Publish rebuilt artifacts under a manifest namespace without changing sources."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_manifest(path: Path) -> tuple[dict, list[dict]]:
  payload = json.loads(path.read_text(encoding="utf-8"))
  if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
    raise ValueError(f"Expected an object containing a models list: {path}")
  return payload, payload["models"]


def renamed_filename(filename: str, old_id: str, new_id: str) -> str:
  old_prefix = f"{old_id}_driving_tinygrad.pkl"
  if filename == old_prefix or filename.startswith(f"{old_prefix}."):
    return f"{new_id}_driving_tinygrad.pkl{filename[len(old_prefix):]}"
  return filename


def rename_model_files(directory: Path, old_id: str, new_id: str) -> None:
  if not directory.is_dir():
    return

  candidates = [
    path for path in directory.iterdir()
    if renamed_filename(path.name, old_id, new_id) != path.name
  ]
  if not candidates:
    return

  staged: list[tuple[Path, Path]] = []
  for source in candidates:
    temporary = source.with_name(f".{source.name}.namespace-tmp")
    if temporary.exists():
      temporary.unlink()
    source.rename(temporary)
    staged.append((temporary, directory / renamed_filename(source.name, old_id, new_id)))

  for temporary, destination in staged:
    if destination.exists():
      destination.unlink()
    temporary.rename(destination)

  checksum = directory / f"{new_id}_driving_tinygrad.pkl.sha256"
  if checksum.is_file():
    text = checksum.read_text(encoding="utf-8")
    text = text.replace(f"{old_id}_driving_tinygrad.pkl", f"{new_id}_driving_tinygrad.pkl")
    checksum.write_text(text, encoding="utf-8")


def remap_multipart_handoff(path: Path, id_map: dict[str, str]) -> None:
  if not path.is_file():
    return
  payload = json.loads(path.read_text(encoding="utf-8"))
  if not isinstance(payload, list):
    raise ValueError(f"Expected a multipart handoff list: {path}")
  for entry in payload:
    if not isinstance(entry, dict):
      continue
    old_id = str(entry.get("id") or "")
    new_id = id_map.get(old_id)
    if not new_id:
      continue
    entry["id"] = new_id
    for key in ("filename",):
      if entry.get(key):
        entry[key] = renamed_filename(str(entry[key]), old_id, new_id)
    entry["parts"] = [renamed_filename(str(part), old_id, new_id) for part in entry.get("parts", [])]
  path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_id_map(models: list[dict], suffix: str, manifest_version: str) -> dict[str, str]:
  """Append the namespace suffix without colliding with an existing source ID."""
  source_ids = [str(model["id"]) for model in models]
  source_id_set = set(source_ids)
  id_map: dict[str, str] = {}
  for old_id in source_ids:
    candidate = f"{old_id}{suffix}"
    if candidate in source_id_set:
      candidate = f"{old_id}{manifest_version}"
    while candidate in id_map.values():
      candidate += "_"
    id_map[old_id] = candidate
  return id_map


def namespace_workspace(
  workspace: Path,
  base_manifest: Path,
  manifest_version: str,
  suffix: str,
  completed_ids: list[str] | None = None,
) -> Path:
  payload, models = load_manifest(base_manifest)
  if not suffix or any(not str(model.get("id") or "") for model in models):
    raise ValueError("Every manifest model must have an ID and the suffix must be non-empty")

  id_map = build_id_map(models, suffix, manifest_version)
  if len(set(id_map.values())) != len(id_map):
    raise ValueError("The requested model namespace contains ID collisions")

  compiled = workspace / "compiled"
  ready = workspace / "ready-for-resources"
  ids_to_namespace = set(completed_ids) if completed_ids is not None else set(id_map)
  unknown_ids = sorted(ids_to_namespace - set(id_map))
  if unknown_ids:
    raise KeyError(f"IDs are not present in the base manifest: {', '.join(unknown_ids)}")
  missing = [
    old_id for old_id in ids_to_namespace
    if not (compiled / f"{old_id}_driving_tinygrad.pkl").is_file()
    and not (compiled / f"{id_map[old_id]}_driving_tinygrad.pkl").is_file()
  ]
  if missing:
    raise FileNotFoundError(f"Missing compiled artifacts for: {', '.join(sorted(missing))}")

  for old_id, new_id in id_map.items():
    if old_id not in ids_to_namespace:
      continue
    rename_model_files(compiled, old_id, new_id)
    rename_model_files(ready, old_id, new_id)

  namespaced_models = []
  for model in models:
    namespaced = dict(model)
    namespaced["id"] = id_map[str(model["id"])]
    namespaced_models.append(namespaced)

  output = dict(payload)
  output["models"] = namespaced_models
  output_path = workspace / "manifests" / f"model_names_{manifest_version}.json"
  output_path.parent.mkdir(parents=True, exist_ok=True)
  output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

  remap_multipart_handoff(ready / "multipart.json", id_map)
  (workspace / "source-maps" / f"model_id_namespace_{manifest_version}.json").write_text(
    json.dumps(id_map, indent=2) + "\n", encoding="utf-8",
  )
  return output_path


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--workspace", type=Path, required=True)
  parser.add_argument("--base-manifest", type=Path, required=True)
  parser.add_argument("--manifest-version", default="v23")
  parser.add_argument("--suffix", default="3")
  parser.add_argument(
    "--completed-ids",
    nargs="+",
    help="Only namespace these confirmed rebuilt IDs; still write the full manifest.",
  )
  args = parser.parse_args()

  output = namespace_workspace(args.workspace, args.base_manifest, args.manifest_version, args.suffix, args.completed_ids)
  print(output)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
