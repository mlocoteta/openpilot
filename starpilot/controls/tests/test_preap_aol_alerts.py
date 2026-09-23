from types import SimpleNamespace

from openpilot.starpilot.controls.lib.starpilot_events import StarPilotEvents, StarPilotEventName


def test_preap_chimes_when_authorized_not_when_merely_selected():
  events = StarPilotEvents(None, None, None)
  cp = SimpleNamespace(carFingerprint='TESLA_MODEL_S_PREAP')
  cs = SimpleNamespace(alwaysOnLateralAllowed=True, alwaysOnLateralEnabled=False)
  for active, expected in ((False, []), (True, [StarPilotEventName.lkasEnable]),
                           (True, []), (False, [StarPilotEventName.lkasDisable]), (False, [])):
    events.events.clear()
    cs.alwaysOnLateralEnabled = active
    events.update_aol_alerts(cp, cs)
    assert events.events.names == expected


def test_ap1_preserves_selection_chime():
  events = StarPilotEvents(None, None, None)
  events.update_aol_alerts(SimpleNamespace(carFingerprint='TESLA_MODEL_S_HW1'),
                           SimpleNamespace(alwaysOnLateralAllowed=True, alwaysOnLateralEnabled=False))
  assert events.events.names == [StarPilotEventName.lkasEnable]
