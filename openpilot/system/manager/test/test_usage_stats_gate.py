from unittest.mock import mock_open, patch

from openpilot.system.manager import process_config


def _enabled(text=None, error=None):
  opener = mock_open(read_data=text or "")
  if error is not None:
    opener.side_effect = error
  with patch("builtins.open", opener):
    return process_config.usage_stats_enabled(True, None, None)


def test_usage_stats_is_off_without_the_flag_file():
  assert _enabled(error=FileNotFoundError()) is False


def test_usage_stats_needs_enabled_true():
  assert _enabled('{"enabled": true}') is True
  for text in ('{"enabled": false}', '{"enabled": 1}', '{}', '[]', 'not json'):
    assert _enabled(text) is False, text


def test_usage_stats_process_uses_the_gate():
  proc = next(p for p in process_config.procs if p.name == "usage_stats")
  assert proc.should_run is process_config.usage_stats_enabled
