from __future__ import annotations

UNIFIED_ARTIFACT_FORMAT = "tinygrad_single_v1"


def parse_model_version(version: str | None) -> int | None:
  text = str(version or "").strip().lower()
  if not text.startswith("v"):
    return None

  raw_number = text[1:]
  if not raw_number.isdigit():
    return None
  return int(raw_number)


def is_tinygrad_model_version(version: str | None) -> bool:
  parsed = parse_model_version(version)
  return parsed is not None and parsed >= 8


def uses_split_off_policy_artifacts(version: str | None) -> bool:
  parsed = parse_model_version(version)
  return parsed is not None and 12 <= parsed < 16


def uses_combined_driving_artifacts(version: str | None) -> bool:
  del version
  return True


def is_supported_artifact_format(artifact_format: str | None) -> bool:
  # Unified manifests are the default. Keep the explicit field optional
  # for compatibility with generated or externally hosted entries.
  return str(artifact_format or "").strip() in {"", UNIFIED_ARTIFACT_FORMAT}


def driving_artifact_filename(model_id: str, artifact_format: str | None = UNIFIED_ARTIFACT_FORMAT) -> str:
  if not is_supported_artifact_format(artifact_format):
    raise ValueError(f"Unsupported driving model artifact format: {artifact_format!r}")
  return f"{model_id}_driving_tinygrad.pkl"
