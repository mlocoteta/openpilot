from types import SimpleNamespace

import pytest

from cereal import car
from openpilot.system.manager.process_config import allow_uploads, managed_processes


class FakeParams:
  def __init__(self, always_allow_uploads: bool = False):
    self.always_allow_uploads = always_allow_uploads

  def get_bool(self, key: str) -> bool:
    assert key == "AlwaysAllowUploads"
    return self.always_allow_uploads


@pytest.mark.parametrize(
  "started,no_uploads,no_onroad_uploads,always_allow_uploads,expected",
  [
    (True, False, False, False, True),
    (False, False, False, False, True),
    (True, True, False, False, False),
    (False, True, False, False, False),
    (True, True, True, False, False),
    (False, True, True, False, True),
    (True, True, False, True, True),
  ],
)
def test_allow_uploads(started, no_uploads, no_onroad_uploads, always_allow_uploads, expected):
  params = FakeParams(always_allow_uploads)
  toggles = SimpleNamespace(no_uploads=no_uploads, no_onroad_uploads=no_onroad_uploads)

  assert allow_uploads(started, params, car.CarParams.new_message(), toggles) is expected


def test_uploader_runs_at_background_priority():
  assert managed_processes["uploader"].nice == 19
