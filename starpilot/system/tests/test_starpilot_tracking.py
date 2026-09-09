from datetime import UTC, datetime

from openpilot.starpilot.system.starpilot_tracking import StarPilotTracking


class FakeParams:
  def __init__(self):
    self.writes = []

  def put(self, key, value):
    self.writes.append((key, value))


def test_flush_persists_time_since_last_checkpoint():
  params = FakeParams()
  tracking = StarPilotTracking.__new__(StarPilotTracking)
  tracking.params = params
  tracking.starpilot_stats = {"StarPilotMeters": 1000}
  tracking.tracked_time = 12.5
  tracking.previously_enabled = True
  tracking.drive_added = False
  tracking.model_name = "test-model"

  tracking.flush(datetime(2026, 8, 27, tzinfo=UTC), time_validated=True)

  assert tracking.tracked_time == 0
  assert tracking.starpilot_stats["StarPilotSeconds"] == 12.5
  assert tracking.starpilot_stats["TrackedTime"] == 12.5
  assert tracking.starpilot_stats["ModelTimes"] == {"test-model": 12.5}
  assert tracking.starpilot_stats["StarPilotDrives"] == 1
  assert params.writes == [("StarPilotStats", dict(sorted(tracking.starpilot_stats.items())))]


def test_flush_does_not_count_a_drive_without_star_pilot_engagement():
  params = FakeParams()
  tracking = StarPilotTracking.__new__(StarPilotTracking)
  tracking.params = params
  tracking.starpilot_stats = {"StarPilotMeters": 1000}
  tracking.tracked_time = 12.5
  tracking.previously_enabled = False
  tracking.drive_added = False
  tracking.model_name = "test-model"

  tracking.flush()

  assert tracking.tracked_time == 12.5
  assert params.writes == []
