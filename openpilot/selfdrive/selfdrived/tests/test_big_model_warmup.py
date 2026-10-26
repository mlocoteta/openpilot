"""No engaging during the big-model warmup: 2026-10-25 routes 2f/30 engaged 0.1-1.6 s after "models loaded" and
card stalled ~0.14 s about 3 s later (every 7.0 drive), giving controlsMismatch / commIssue TAKE CONTROL IMMEDIATELY."""
import unittest
from unittest.mock import patch

from openpilot.selfdrive.selfdrived.events import ET, EventName, Events
from openpilot.selfdrive.selfdrived.selfdrived import BIG_MODEL_WARMUP_S, SelfdriveD


def fixture(loading, ready_t):
  drive = SelfdriveD.__new__(SelfdriveD)
  drive.big_model_loading = loading
  drive.big_model_ready_t = ready_t
  drive.events = Events()
  return drive


class TestBigModelWarmup(unittest.TestCase):
  def test_settling_spans_load_and_warmup(self):
    with patch('openpilot.selfdrive.selfdrived.selfdrived.time.monotonic', return_value=100.0):
      self.assertTrue(fixture(True, 0.).big_model_settling())
      self.assertTrue(fixture(False, 100.0 - 2.9).big_model_settling())  # where the card stall landed
      self.assertTrue(fixture(False, 100.0 - BIG_MODEL_WARMUP_S + 0.01).big_model_settling())
      self.assertFalse(fixture(False, 100.0 - BIG_MODEL_WARMUP_S - 0.01).big_model_settling())
      self.assertFalse(fixture(False, 0.).big_model_settling())  # never loaded (small model / no Chestnut)

  def test_warmup_is_no_entry_only(self):
    drive = fixture(False, 98.0)
    with patch('openpilot.selfdrive.selfdrived.selfdrived.time.monotonic', return_value=100.0):
      if drive.big_model_settling():
        drive.events.add(EventName.bigModelLoading)
    self.assertTrue(drive.events.contains(ET.NO_ENTRY))
    for kind in (ET.SOFT_DISABLE, ET.IMMEDIATE_DISABLE, ET.USER_DISABLE):
      self.assertFalse(drive.events.contains(kind))  # an engaged car is never dropped by it


if __name__ == '__main__':
  unittest.main()
