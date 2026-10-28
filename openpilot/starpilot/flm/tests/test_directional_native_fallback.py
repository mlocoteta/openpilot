"""A dead native direction must not monopolize another measurable correction."""
from dataclasses import replace
from openpilot.starpilot.flm.live_trial_contract import SOURCE_EXPERIMENT_STEP
from openpilot.starpilot.flm.tests.test_live_tracking import episode
from openpilot.starpilot.flm.tests.test_tracking_source_context import owner, refresh
from openpilot.starpilot.flm.tests.test_directional_native_visibility import feature

def test_quantized_preference_allows_a_different_measurable_calming_hook():
  o = owner()
  for i in range(40):
    e = episode(o, i, 'center_taper_max', kind='subtle')
    dead = feature(error=-0.5)
    center = feature(name='center_taper_max', error=0.05)
    e = replace(e, sensitivity=(dead, center), normalization_accel=max(0.1, e.goal_rms))
    refresh(o, e.end_ns)
    o.observe_episode(e, now_ns=e.end_ns)
    if o.offer_state is not None:
      break
  assert o.offer_state is not None
  assert o.offer_state['names'] == ('center_taper_max',)
  assert o.offer_state['target']['center_taper_max'] == SOURCE_EXPERIMENT_STEP
  assert o.offer_state['target']['ff_gain_right'] == 0.0
  assert not o.offer_state.get('accepted', False) and (not any(o.accepted.values()))
