from openpilot.starpilot.common.maps_download_progress import (
  estimate_download_bytes,
  estimate_file_eta_seconds,
  estimate_eta_seconds,
  load_maps_storage_cache,
  load_size_cache,
  selection_key,
  storage_bytes,
)


def test_storage_bytes_and_selection_key(tmp_path):
  maps_path = tmp_path / "maps"
  maps_path.mkdir()
  (maps_path / "first.bin").write_bytes(b"1234")
  (maps_path / "nested").mkdir()
  (maps_path / "nested" / "second.bin").write_bytes(b"123456")

  assert storage_bytes(maps_path) == 10
  assert selection_key("us-ca,us-tx,us-ca") == "us-ca,us-tx"


def test_download_size_and_eta_estimates():
  assert estimate_download_bytes(100, total_files=10, downloaded_files=2) == 500
  assert estimate_download_bytes(0, total_files=10, downloaded_files=2) == 0
  assert estimate_eta_seconds(500, 100, 100) == 4
  assert estimate_eta_seconds(500, 500, 100) == 0


def test_load_size_cache_rejects_invalid_values():
  assert load_size_cache(b'{"us-ca":{"downloadBytes":123}}')["us-ca"]["downloadBytes"] == 123
  assert load_size_cache("not json") == {}
  assert load_size_cache("[]") == {}


def test_storage_cache_migrates_legacy_selection_without_claiming_storage_total():
  cache = load_maps_storage_cache('{"country:CA":{"downloadBytes":123,"totalFiles":4}}')

  assert cache.storage_bytes is None
  assert cache.maps_present is None
  assert cache.selection_estimate_bytes("country:CA") == 123
  assert cache.selection_total_files("country:CA") == 4

  migrated = load_maps_storage_cache(cache.to_json())
  assert migrated.storage_bytes is None
  assert migrated.selection_estimate_bytes("country:CA") == 123


def test_storage_cache_records_selection_delta_not_aggregate_storage():
  cache = load_maps_storage_cache("")
  cache.reconcile(10_000)
  cache.reconcile(
    18_000,
    selection_key="country:CA",
    baseline_storage_bytes=10_000,
    total_files=80,
    updated_at="2026-08-31T00:00:00",
  )

  assert cache.storage_bytes == 18_000
  assert cache.maps_present is True
  assert cache.selection_estimate_bytes("country:CA") == 8_000
  assert cache.selection_total_files("country:CA") == 80

  cache.reconcile(
    18_000,
    selection_key="country:CA",
    baseline_storage_bytes=18_000,
    total_files=80,
    updated_at="2026-09-01T00:00:00",
  )

  assert cache.selection_estimate_bytes("country:CA") == 0


def test_storage_cache_can_be_cleared_or_marked_unknown_without_false_presence():
  cache = load_maps_storage_cache("")
  cache.reconcile(128)
  cache.clear()

  assert cache.storage_bytes == 0
  assert cache.maps_present is False

  cache.mark_unknown()

  assert cache.storage_bytes is None
  assert cache.maps_present is None


def test_file_eta_uses_mapd_file_progress_without_storage_scans():
  assert estimate_file_eta_seconds(elapsed_seconds=10, total_files=10, downloaded_files=2) == 40
  assert estimate_file_eta_seconds(elapsed_seconds=10, total_files=10, downloaded_files=0) == 0
  assert estimate_file_eta_seconds(elapsed_seconds=10, total_files=2, downloaded_files=2) == 0
