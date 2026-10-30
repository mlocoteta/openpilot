from types import SimpleNamespace as NS

import pytest

from openpilot.starpilot.audio.blindspot_alert import ALERT_TYPE, KEYS, blindspot_alert
from openpilot.selfdrive.selfdrived.alertmanager import AlertManager
from openpilot.selfdrive.selfdrived.events import Alert, AlertSize, AlertStatus, AudibleAlert, ET, Priority, VisualAlert
from openpilot.common.params import Params
from openpilot.starpilot.ui.sounds_owner import SoundsOwner
from openpilot.starpilot.ui.feature_settings_state import FeatureSettingsRequest

NOW = 10_000_000_000


class Messages(dict):
  def __init__(self, active=False):
    super().__init__(deviceState=NS(started=True), carControl=NS(latActive=active))
    self.logMonoTime = dict.fromkeys(('deviceState', 'carControl', 'carState'), NOW - 10_000_000)
    self.healthy = True

  def all_checks(self, _services):
    return self.healthy


def car(**kw):
  return NS(**({'leftBlinker': True, 'rightBlinker': False, 'leftBlindspot': True, 'rightBlindspot': False,
               'canValid': True, 'canTimeout': False} | kw))


def test_independent_switches_and_active_lane_change():
  sm = Messages(active=True)
  assert blindspot_alert(car(), sm, loud=True, without_lateral=False, lane_change_blocked=True, now_ns=NOW)
  assert not blindspot_alert(car(), sm, loud=False, without_lateral=True, lane_change_blocked=False, now_ns=NOW)
  sm['carControl'].latActive = False
  assert blindspot_alert(car(), sm, loud=False, without_lateral=True, lane_change_blocked=False, now_ns=NOW)
  assert blindspot_alert(car(), sm, loud=False, without_lateral=True, lane_change_blocked=True, now_ns=NOW)
  assert not blindspot_alert(car(), sm, loud=True, without_lateral=False, lane_change_blocked=False, now_ns=NOW)
  assert not blindspot_alert(car(), sm, loud=False, without_lateral=False, lane_change_blocked=True, now_ns=NOW)


@pytest.mark.parametrize('fields', [{'leftBlinker': False}, {'rightBlinker': True},
  {'leftBlindspot': False, 'rightBlindspot': True}, {'canValid': False}, {'canTimeout': True}])
def test_no_wrong_side_hazards_or_invalid_can(fields):
  assert not blindspot_alert(car(**fields), Messages(), loud=False, without_lateral=True,
                            lane_change_blocked=False, now_ns=NOW)


def test_right_side_and_stale_or_offroad_inputs():
  cs = car(leftBlinker=False, leftBlindspot=False, rightBlinker=True, rightBlindspot=True)
  sm = Messages()
  def alert():
    return blindspot_alert(cs, sm, loud=False, without_lateral=True, lane_change_blocked=False, now_ns=NOW)
  assert alert()
  for key in sm.logMonoTime:
    stamp = sm.logMonoTime[key]
    sm.logMonoTime[key] = NOW - 3_000_000_000
    assert not alert()
    sm.logMonoTime[key] = NOW + 1
    assert not alert()
    sm.logMonoTime[key] = stamp
  sm.healthy = False
  assert not alert()
  sm.healthy = True
  sm['deviceState'].started = False
  assert not alert()


def test_disengaged_alert_survives_warning_filter_but_never_masks_takeover():
  alert = blindspot_alert(car(), Messages(), loud=False, without_lateral=True, lane_change_blocked=False, now_ns=NOW)
  assert alert.audible_alert == AudibleAlert.warningSoft
  manager = AlertManager()
  manager.add_many(1, [alert])
  manager.process_alerts(1, {ET.WARNING})
  assert manager.current_alert.alert_type == ALERT_TYPE
  takeover = Alert('Take Control', '', AlertStatus.critical, AlertSize.full, Priority.HIGHEST,
                   VisualAlert.steerRequired, AudibleAlert.warningImmediate, 1.)
  takeover.alert_type, takeover.event_type = 'takeover', ET.IMMEDIATE_DISABLE
  manager.add_many(2, [takeover])
  manager.process_alerts(2, {ET.WARNING})
  assert manager.current_alert.alert_type == 'takeover'


def test_switch_defaults_persistence_and_exact_authority(tmp_path):
  params = Params(str(tmp_path))
  allowed = True
  owner = SoundsOwner(params, lambda: allowed)
  for key in KEYS:
    row = next(row for row in owner.snapshot().rows if row.key == key)
    assert row.value == 'Off' and row.default_value == 'Off'
    request = FeatureSettingsRequest(key, row.source, 'On')
    assert owner.apply(request)
    assert params.get_bool(key)
    assert not owner.apply(request)
    allowed = False
    assert not owner.apply(FeatureSettingsRequest(key, b'1', 'Off'))
    allowed = True
    assert owner.apply(FeatureSettingsRequest(key, b'1', 'Off'))


def test_galaxy_sounds_switches_save_and_reset_with_session_checks(tmp_path):
  from openpilot.starpilot.galaxy.settings import AuthorityContext, SettingsGateway, SettingsChanged
  params = Params(str(tmp_path))
  class Context:
    def sample(self) -> AuthorityContext:
      return AuthorityContext(True, None, None)

  context = Context()
  gateway = SettingsGateway(params, context)
  for key, label in zip(KEYS, ('Loud Blindspot Alert', 'Blindspot Alert While Lateral Is Off'), strict=True):
    page = gateway.page('sounds', 'session', b'generation')
    index, row = next((i, row) for i, row in enumerate(page['rows']) if row['label'] == label)
    assert row['choices'] == ['Off', 'On'] and row['defaultValue'] == 'Off'
    pending = gateway.preview(page['view'], index, 0, 'session', b'generation', value='On')
    assert gateway.confirm(pending['intent'], 'session', b'generation')
    assert params.get_bool(key)
    page = gateway.page('sounds', 'session', b'generation')
    reset = gateway.preview(page['view'], index, 0, 'session', b'generation', reset_default=True)
    with pytest.raises(SettingsChanged):
      gateway.confirm(reset['intent'], 'session', b'generation', session_valid=lambda: False)
    assert params.get_bool(key)
    reset = gateway.preview(page['view'], index, 0, 'session', b'generation', reset_default=True)
    assert gateway.confirm(reset['intent'], 'session', b'generation')
    assert not params.get_bool(key)
