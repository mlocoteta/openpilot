from openpilot.starpilot.common.maps_download_progress import (
  estimate_download_bytes,
  estimate_eta_seconds,
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
