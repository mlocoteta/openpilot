from dataclasses import replace

import pytest

from openpilot.starpilot.ui.onroad_customization import validate_document
from openpilot.starpilot.ui.onroad_state import slc_controls
from openpilot.starpilot.ui.presentation import Profile
from openpilot.starpilot.ui.tests.test_onroad_customization import road
from openpilot.starpilot.ui.unified_speed_presentation import toyota_cruise_notice


@pytest.mark.parametrize('status', ['raise_dash', 'release_plus', 'off_hold', 'off_resume'])
def test_guidance_remains_when_buttons_hidden_and_has_no_touch_action(status):
  state = road(toyota_cruise_status=status, toyota_cruise_target_kph=112.65408, metric=False)
  state.customization['layouts']['compact']['speed_limit_actions']['enabled'] = False
  assert toyota_cruise_notice(state)[2:] == ('70', 'mph')
  assert not slc_controls(Profile.COMPACT, state)
  assert toyota_cruise_notice(replace(state, toyota_cruise_status='ready')) is None


def test_stopped_timer_yields_only_when_its_area_is_needed_for_slc():
  from unittest.mock import Mock
  from openpilot.starpilot.ui.onroad import OnroadView
  state = road(toyota_cruise_status='raise_dash', toyota_cruise_target_kph=70)
  state.customization['layouts']['compact']['stopped_timer']['enabled'] = True
  assert validate_document(state.customization) == state.customization
  view = OnroadView.__new__(OnroadView)
  view.personality = Mock()
  view.fonts = Mock(profile=Profile.COMPACT)
  view._stopped_timer(state, 134)
  view.fonts.draw.assert_not_called()
  view.fonts.measure.return_value = Mock(width=100, height=20)
  view._stopped_timer(replace(state, toyota_cruise_status=''), 134)
  assert view.fonts.draw.called
