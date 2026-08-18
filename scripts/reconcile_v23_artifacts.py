#!/usr/bin/env python3
"""Normalize rebuilt artifacts and the v23 manifest into one release namespace."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_TO_RELEASE = {
  "opv8": "opv83",
  "opv9": "opv93",
  "opv10": "opv103",
  "opv11": "opv113",
  "opv12": "opv123",
  "opv13": "opv133",
  "op16": "op163",
  "op16d": "op16d3",
  "op16dv2": "op16dv23",
  "rlv1dl": "rlv1dl3",
  "deeprl3": "deeprl33",
  "deeprl3v2": "deeprl3v23",
  "ms2": "ms23",
  "pp222": "pp2223",
  "nn222": "nn2223",
  "pop2": "pop23",
  "nid22": "nid223",
  "kerrygold22": "kerrygold223",
  "karnbir": "karnbir3",
  "karnbir2": "karnbir23",
  "michael-rl": "michael-rl3",
  "michael-rl2": "michael-rl23",
  "tobyrl": "tobyrl3",
  "nopp": "nopp3",
  "drl": "drl3",
  "deeprl33": "deeprl333",
  "rl34": "rl343",
  "gyhu": "gyhu3",
  "rdf2": "rdf23",
}


def sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def renamed_name(filename: str, old_id: str, new_id: str) -> str:
  prefix = f"{old_id}_driving_tinygrad.pkl"
  if filename == prefix or filename.startswith(f"{prefix}."):
    return f"{new_id}_driving_tinygrad.pkl{filename[len(prefix):]}"
  return filename


def normalize_artifact_names(directory: Path) -> None:
  if not directory.is_dir():
    return
  for path in directory.glob("._*"):
    path.unlink(missing_ok=True)

  # Snapshot the input names. Some source IDs are also release IDs (for
  # example deeprl3 -> deeprl33 and deeprl33 -> deeprl333); scanning the live
  # directory would apply those mappings twice.
  original_paths = list(directory.iterdir())
  moves = []
  for old_id, new_id in SOURCE_TO_RELEASE.items():
    sources = [path for path in original_paths if path.exists() and renamed_name(path.name, old_id, new_id) != path.name]
    for source in sources:
      destination = directory / renamed_name(source.name, old_id, new_id)
      moves.append((source, destination))

  source_paths = {source for source, _ in moves}
  temporary_moves = []
  for index, (source, destination) in enumerate(moves):
    if destination.exists() and destination not in source_paths:
      if source.is_file() and destination.is_file() and source.stat().st_size == destination.stat().st_size and sha256(source) == sha256(destination):
        source.unlink()
        continue
      raise FileExistsError(f"Refusing to overwrite conflicting artifact: {destination}")
    temporary = directory / f".__reconcile_{index}__{source.name}"
    if temporary.exists():
      raise FileExistsError(f"Temporary reconciliation path already exists: {temporary}")
    source.rename(temporary)
    temporary_moves.append((temporary, destination, source.name))

  for temporary, destination, source_name in temporary_moves:
    if destination.exists():
      raise FileExistsError(f"Refusing to overwrite conflicting artifact: {destination}")
    if destination.name.endswith(".pkl.sha256"):
      checksum_text = temporary.read_text(encoding="utf-8")
      checksum_text = checksum_text.replace(source_name.removesuffix(".sha256"), destination.name.removesuffix(".sha256"))
      temporary.write_text(checksum_text, encoding="utf-8")
    temporary.rename(destination)


def normalize_manifest(path: Path) -> None:
  payload = json.loads(path.read_text(encoding="utf-8"))
  models = payload.get("models", [])
  normalized = []
  seen = set()
  duplicate_base_removed = False
  for model in models:
    entry = dict(model)
    if entry.get("id") == "deeprl3v23_":
      if duplicate_base_removed:
        continue
      entry["id"] = "deeprl33"
      duplicate_base_removed = True
    if entry["id"] in seen:
      raise ValueError(f"Duplicate v23 model ID: {entry['id']}")
    seen.add(entry["id"])
    normalized.append(entry)

  if "rdf23" not in seen:
    insert_at = next((index + 1 for index, model in enumerate(normalized) if model.get("id") == "rdfv23"), len(normalized))
    normalized.insert(insert_at, {
      "id": "rdf23",
      "name": "Regret Driven Framework V2 👀📡",
      "version": "v15",
      "series": "OP Series",
      "released": "2026-08-10",
      "community_favorite": False,
    })

  payload["models"] = normalized
  path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--workspace", type=Path, required=True)
  args = parser.parse_args()
  normalize_artifact_names(args.workspace / "compiled")
  normalize_artifact_names(args.workspace / "ready-for-resources")
  normalize_manifest(args.workspace / "manifests/model_names_v23.json")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
