from openpilot.selfdrive.ui.mici.layouts.settings.device import _request_user_reboot


class FakeParams:
  def __init__(self):
    self.writes = []

  def put_bool(self, key, value):
    self.writes.append((key, value))


def test_mici_user_reboot_bypasses_automatic_reboot_deferral():
  params = FakeParams()

  _request_user_reboot(params)

  assert params.writes == [("DoUserReboot", True)]
