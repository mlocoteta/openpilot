"""A slower blocking cadence must not relax receiver frequency thresholds."""
from openpilot.cereal import messaging
from openpilot.starpilot.flm.steerlearnerd import source_receiver


def test_motion_pacing_preserves_every_original_frequency_threshold():
  services = ['deviceMotion', 'extrinsicsCalibration', 'carState', 'pandaStates',
              'lateralDelay', 'vehicleParameters', 'driverMonitoringState', 'onroadEvents', 'aolSafetyWire']
  before = messaging.SubMaster(services, ignore_alive=['aolSafetyWire'], ignore_valid=['aolSafetyWire'],
                              ignore_avg_freq=['aolSafetyWire', 'carState'])
  after = source_receiver(services)
  assert after.non_polled_services == set(services) - {'deviceMotion'}
  assert before.update_freq == after.update_freq
  for name in services:
    first, second = before.freq_tracker[name], after.freq_tracker[name]
    assert (first.min_freq, first.max_freq) == (second.min_freq, second.max_freq)
  assert before.ignore_average_freq == after.ignore_average_freq
  assert before.ignore_alive == after.ignore_alive and before.ignore_valid == after.ignore_valid
