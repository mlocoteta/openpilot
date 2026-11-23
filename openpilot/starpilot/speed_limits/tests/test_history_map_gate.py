"""F29 (Accord 9G): a remembered Maps limit needs map data this drive can read."""

import json
from dataclasses import replace
from unittest import mock

import pytest

from openpilot.common.params import Params
from openpilot.selfdrive.controls.plannerd import SavedSlcLifecycle
from openpilot.starpilot.speed_limits import acceptance as acc, history, planner_host
from openpilot.starpilot.ui.tests.test_slc_retention import NOW, RetentionDrive


def _saved_drive(tmp_path, source, fingerprint):
  drive = RetentionDrive(tmp_path)
  accepted, _, _ = drive.step(0)
  previous = accepted.result.state.acceptance.accepted
  previous = replace(previous, candidate=replace(previous.candidate, source=source))
  drive.cp = drive.cp.as_builder() if hasattr(drive.cp, 'as_builder') else drive.cp
  drive.cp.carFingerprint = fingerprint
  params = Params(str(tmp_path))
  saved = json.loads(history.encode(previous, 1))
  params.put('SLCQualifiedHistory', saved, block=True)
  params.put('SLCConfirmation', 1, block=True)
  return drive, params, saved


def _restart(drive, params):
  drive.runtime, _ = SavedSlcLifecycle(params, drive.cp, {}).refresh(NOW)
  drive.sm['slcDashboardObservation'].status = 'unknown'
  return drive.step(1000, received=False)


def test_accord_drops_remembered_map_limit_without_map_data(tmp_path):
  drive, params, saved = _saved_drive(tmp_path, 'map', 'HONDA_ACCORD_9G')
  with mock.patch.object(planner_host, 'map_data_available', return_value=False):
    output, _, target = _restart(drive, params)
  assert not output.result.errors
  assert not output.message.slcState.hasCeiling
  assert target == pytest.approx(70, abs=1e-4)   # SET, not the stale 45
  assert params.get('SLCQualifiedHistory') == saved  # the saved record is left alone


def test_accord_keeps_remembered_map_limit_when_map_data_exists(tmp_path):
  drive, params, _ = _saved_drive(tmp_path, 'map', 'HONDA_ACCORD_9G')
  with mock.patch.object(planner_host, 'map_data_available', return_value=True):
    output, _, target = _restart(drive, params)
  assert output.message.slcState.hasCeiling
  assert target == pytest.approx(45, abs=1e-4)


@pytest.mark.parametrize('source', ['dashboard', 'vision'])
def test_accord_other_remembered_sources_are_unchanged(tmp_path, source):
  drive, params, _ = _saved_drive(tmp_path, source, 'HONDA_ACCORD_9G')
  with mock.patch.object(planner_host, 'map_data_available', return_value=False):
    output, _, target = _restart(drive, params)
  assert output.message.slcState.hasCeiling
  assert target == pytest.approx(45, abs=1e-4)


def test_other_cars_keep_upstream_fallback(tmp_path):
  drive, params, _ = _saved_drive(tmp_path, 'map', 'TOYOTA_RAV4_TSS2')
  with mock.patch.object(planner_host, 'map_data_available', return_value=False):
    output, _, target = _restart(drive, params)
  assert output.message.slcState.hasCeiling
  assert target == pytest.approx(45, abs=1e-4)


def test_map_data_available_needs_a_selected_snapshot(tmp_path):
  from openpilot.starpilot.maps import shadow_lifecycle as shadow
  binary = tmp_path / 'mapd'
  binary.write_bytes(b'x')
  anchor = tmp_path / 'media'
  root = shadow.map_offline_root(anchor)   # namespace-aware (OPENPILOT_PREFIX)
  with (mock.patch.object(shadow, 'PROVIDER_BINARY', binary), mock.patch.object(shadow, 'STORAGE_ANCHOR', anchor),
        mock.patch.object(shadow, 'OFFLINE_ROOT', root)):
    assert not planner_host.map_data_available()          # no offline root (the car on 2026-11-22)
    root.mkdir(parents=True)
    assert not planner_host.map_data_available()          # root but nothing selected
    with mock.patch.object(shadow, '_selected_snapshot', return_value=True):
      assert planner_host.map_data_available()
      binary.unlink()
      assert not planner_host.map_data_available()        # no packaged provider


def test_restorable_previous_limit_passes_none_through():
  cp = mock.Mock(carFingerprint='HONDA_ACCORD_9G')
  assert planner_host.restorable_previous_limit(None, cp) is None
  candidate = acc.Candidate('map', acc.ObservationIdentity(acc.IdentityKind.SESSION_VALUE, session_id='s'), 20.)
  limit = acc.AcceptedLimit(candidate, 's', 0)
  with mock.patch.object(planner_host, 'map_data_available', return_value=False):
    assert planner_host.restorable_previous_limit(limit, cp) is None
  with mock.patch.object(planner_host, 'map_data_available', return_value=True):
    assert planner_host.restorable_previous_limit(limit, cp) is limit
