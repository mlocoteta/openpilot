import json
import math
from dataclasses import dataclass, field
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


def estimate_file_eta_seconds(elapsed_seconds, total_files, downloaded_files):
  elapsed_seconds = max(float(elapsed_seconds or 0.0), 0.0)
  total_files = nonnegative_int(total_files)
  downloaded_files = min(nonnegative_int(downloaded_files), total_files)
  if elapsed_seconds <= 0 or downloaded_files <= 0 or downloaded_files >= total_files:
    return 0
  return max(1, math.ceil(elapsed_seconds * (total_files - downloaded_files) / downloaded_files))


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


MAPS_STORAGE_CACHE_PARAM = "MapsDownloadSizeCache"
MAPS_STORAGE_CACHE_VERSION = 2


@dataclass
class MapsStorageCache:
  """Persisted map storage state; ``None`` means it has not been reconciled yet."""

  storage_bytes: int | None = None
  _selections: dict[str, dict] = field(default_factory=dict)

  @property
  def storage_known(self) -> bool:
    return self.storage_bytes is not None

  @property
  def maps_present(self) -> bool | None:
    total_storage_bytes = self.storage_bytes
    if total_storage_bytes is None:
      return None
    return total_storage_bytes > 0

  def selection_estimate_bytes(self, selected_key):
    entry = self._selections.get(selected_key, {})
    if not isinstance(entry, dict):
      return 0
    return nonnegative_int(entry.get("estimatedAdditionalStorageBytes", entry.get("downloadBytes", 0)))

  def selection_total_files(self, selected_key):
    entry = self._selections.get(selected_key, {})
    return nonnegative_int(entry.get("totalFiles", 0)) if isinstance(entry, dict) else 0

  def selection_updated_at(self, selected_key):
    entry = self._selections.get(selected_key, {})
    return str(entry.get("updatedAt", "")) if isinstance(entry, dict) else ""

  def reconcile(self, total_storage_bytes, *, selection_key=None, baseline_storage_bytes=None, total_files=0, updated_at=""):
    self.storage_bytes = nonnegative_int(total_storage_bytes)
    if not selection_key:
      return

    entry = {
      "estimatedAdditionalStorageBytes": 0,
      "totalFiles": nonnegative_int(total_files),
      "updatedAt": str(updated_at or ""),
    }
    if baseline_storage_bytes is not None:
      entry["estimatedAdditionalStorageBytes"] = max(self.storage_bytes - nonnegative_int(baseline_storage_bytes), 0)
    self._selections[str(selection_key)] = entry

  def clear(self):
    self.storage_bytes = 0

  def mark_unknown(self):
    self.storage_bytes = None

  def to_json(self):
    selections = {
      key: {
        "estimatedAdditionalStorageBytes": self.selection_estimate_bytes(key),
        "totalFiles": self.selection_total_files(key),
        "updatedAt": self.selection_updated_at(key),
      }
      for key, entry in self._selections.items()
    }
    return json.dumps({
      "version": MAPS_STORAGE_CACHE_VERSION,
      "storageBytes": self.storage_bytes,
      "selections": selections,
    }, separators=(",", ":"))


def load_maps_storage_cache(raw_value):
  value = load_size_cache(raw_value)
  if value.get("version") == MAPS_STORAGE_CACHE_VERSION:
    storage_bytes_value = value.get("storageBytes")
    selections = value.get("selections")
    return MapsStorageCache(
      storage_bytes=nonnegative_int(storage_bytes_value) if storage_bytes_value is not None else None,
      _selections={str(key): dict(entry) for key, entry in selections.items() if isinstance(entry, dict)} if isinstance(selections, dict) else {},
    )

  return MapsStorageCache(_selections={str(key): dict(entry) for key, entry in value.items() if isinstance(entry, dict)})
