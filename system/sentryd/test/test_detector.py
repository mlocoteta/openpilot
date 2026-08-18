from openpilot.system.sentryd.detector import MotionDetector


def test_motion_detector_ignores_small_changes():
  detector = MotionDetector(sensitivity=0.1)
  assert detector.update((0.0, 0.0, 9.8), now=0.0) is None
  assert detector.update((0.0, 0.0, 9.85), now=0.1) is None
  assert detector.trigger_count == 0


def test_motion_detector_warns_once_after_sustained_motion():
  detector = MotionDetector(sensitivity=0.1, warning_trigger_count=3)
  detector.update((0.0, 0.0, 9.8), now=0.0)

  assert detector.update((0.0, 0.0, 10.0), now=0.1) is None
  assert detector.update((0.0, 0.0, 9.8), now=0.2) is None
  assert detector.update((0.0, 0.0, 10.0), now=0.3) == "warning"
  assert detector.update((0.0, 0.0, 9.8), now=0.4) is None


def test_motion_detector_alarms_after_time_threshold():
  detector = MotionDetector(
    sensitivity=0.1,
    warning_trigger_count=2,
    alarm_trigger_count=3,
    alarm_time=1.0,
  )
  detector.update((0.0, 0.0, 9.8), now=0.0)
  detector.update((0.0, 0.0, 10.0), now=0.1)
  assert detector.update((0.0, 0.0, 9.8), now=0.2) == "warning"

  assert detector.update((0.0, 0.0, 10.0), now=0.5) is None
  assert detector.update((0.0, 0.0, 9.8), now=1.0) is None
  assert detector.update((0.0, 0.0, 10.0), now=1.1) == "alarm"
  assert detector.update((0.0, 0.0, 9.8), now=1.2) is None


def test_motion_detector_resets_after_quiet_period():
  detector = MotionDetector(sensitivity=0.1, warning_trigger_count=2, reset_time=1.0)
  detector.update((0.0, 0.0, 9.8), now=0.0)
  detector.update((0.0, 0.0, 10.0), now=0.1)
  detector.update((0.0, 0.0, 9.8), now=0.2)
  detector.update((0.0, 0.0, 9.8), now=1.3)

  assert detector.trigger_count == 0
  assert detector.trigger_started_at is None
