from openpilot.selfdrive.controls.lib.drive_helpers import get_kona_non_scc_lateral_active, get_lateral_active


def test_get_lateral_active_requires_enabled_without_aol():
  assert not get_lateral_active(False, True, False, False, False, False, False, True)


def test_get_lateral_active_allows_aol_while_disabled():
  assert get_lateral_active(False, False, True, False, False, False, False, True)


def test_get_lateral_active_does_not_retry_after_a_latched_temporary_fault():
  assert not get_lateral_active(False, False, True, False, False, False, False, True, True)
  assert get_lateral_active(False, False, True, False, False, False, False, True, False)


def test_kona_non_scc_aol_waits_for_driver_steering_to_release():
  assert not get_kona_non_scc_lateral_active(
    False, False, True, False, False, False, False, True, True, False,
  )
  assert get_kona_non_scc_lateral_active(
    False, False, True, False, False, False, False, True, False, False,
  )
  assert get_kona_non_scc_lateral_active(
    False, False, True, False, False, False, False, True, True, True,
  )


def test_kona_non_scc_aol_gate_does_not_change_fault_or_normal_lateral_gates():
  assert not get_kona_non_scc_lateral_active(
    False, False, True, True, False, False, False, True, False, False,
  )
  assert get_kona_non_scc_lateral_active(
    True, True, False, False, False, False, False, True, True, False,
  )


def test_kona_non_scc_does_not_retry_after_a_latched_temporary_fault():
  assert not get_kona_non_scc_lateral_active(
    False, False, True, False, False, False, False, True, False, False, True,
  )


def test_get_lateral_active_honors_manual_pause_while_cruise_is_engaged():
  assert not get_lateral_active(True, True, False, False, False, False, False, False)
