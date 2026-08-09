import json
import math
from pathlib import Path


def nonnegative_int(value):
  try:
    return max(int(value or 0), 0)
  except (TypeError, ValueError):
    return 0


def storage_bytes(path):
  path = Path(path)
  if not path.exists():
    return 0

  total = 0
  try:
    for item in path.rglob("*"):
      try:
        if item.is_file():
          total += item.stat().st_size
      except OSError:
        continue
  except OSError:
    return total
  return total


def selection_key(selected_locations):
  if isinstance(selected_locations, str):
    selected_locations = selected_locations.split(",")
  return ",".join(sorted({str(location).strip() for location in selected_locations if str(location).strip()}))


def estimate_download_bytes(storage_delta_bytes, total_files, downloaded_files):
  storage_delta_bytes = nonnegative_int(storage_delta_bytes)
  total_files = nonnegative_int(total_files)
  downloaded_files = nonnegative_int(downloaded_files)
  if storage_delta_bytes <= 0 or downloaded_files <= 0 or total_files <= 0:
    return 0
  return max(storage_delta_bytes, math.ceil(storage_delta_bytes * total_files / downloaded_files))


def estimate_eta_seconds(estimated_download_bytes, storage_delta_bytes, bytes_per_second):
  remaining_bytes = max(nonnegative_int(estimated_download_bytes) - nonnegative_int(storage_delta_bytes), 0)
  bytes_per_second = float(bytes_per_second or 0.0)
  if remaining_bytes <= 0 or bytes_per_second <= 0:
    return 0
  return max(1, math.ceil(remaining_bytes / bytes_per_second))


def load_size_cache(raw_value):
  if isinstance(raw_value, bytes):
    raw_value = raw_value.decode("utf-8", errors="ignore")
  if not raw_value:
    return {}
  try:
    value = json.loads(raw_value)
  except (TypeError, ValueError):
    return {}
  return value if isinstance(value, dict) else {}
