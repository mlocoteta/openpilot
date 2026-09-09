from types import SimpleNamespace

from openpilot.selfdrive.ui.mici.layouts.settings import software
from openpilot.selfdrive.ui.mici.widgets.button import BigButton


def _make_button() -> software.CheckUpdateButton:
  button = object.__new__(software.CheckUpdateButton)
  button._press_start_t = None
  button._press_action = ""
  button._fast_update_state = software.FastUpdateDisplayState()
  button._fast_update_state_lock = software.threading.Lock()
  return button


def test_fast_update_uses_local_galaxy_api(monkeypatch):
  monkeypatch.delenv("SP_GALAXY_PORT", raising=False)

  assert software._galaxy_api_url("") == "http://127.0.0.1:8082/api/update/fast"
  assert software._galaxy_api_url("/status") == "http://127.0.0.1:8082/api/update/fast/status"


def test_long_press_opens_fast_update_confirmation(monkeypatch):
  button = _make_button()
  button._press_start_t = 1.0
  confirmation_calls = []

  monkeypatch.setattr(software.rl, "get_time", lambda: 1.0 + software.FAST_UPDATE_HOLD_SECONDS)
  monkeypatch.setattr(BigButton, "_handle_mouse_release", lambda *_args: None)
  monkeypatch.setattr(button, "_show_fast_update_confirmation", lambda: confirmation_calls.append(True))

  button._handle_mouse_release(SimpleNamespace())

  assert confirmation_calls == [True]


def test_short_press_keeps_normal_updater_path(monkeypatch):
  button = _make_button()
  button._press_start_t = 1.0
  button._press_action = "download update"
  downloads = []
  confirmations = []

  monkeypatch.setattr(software.rl, "get_time", lambda: 1.0 + software.FAST_UPDATE_HOLD_SECONDS - 0.1)
  monkeypatch.setattr(BigButton, "_handle_mouse_release", lambda *_args: None)
  monkeypatch.setattr(software, "system_time_valid", lambda: True)
  monkeypatch.setattr(software, "_request_update_download", lambda: downloads.append(True))
  monkeypatch.setattr(button, "_show_fast_update_confirmation", lambda: confirmations.append(True))

  class ImmediateThread:
    def __init__(self, target, daemon):
      self.target = target

    def start(self):
      self.target()

  monkeypatch.setattr(software.threading, "Thread", ImmediateThread)
  button.set_enabled = lambda *_args: None
  button.set_icon = lambda *_args: None
  button._state = software.UpdaterState.IDLE
  button._txt_update_icon = None

  button._handle_mouse_release(SimpleNamespace())

  assert downloads == [True]
  assert confirmations == []


def test_fast_update_worker_uses_galaxy_endpoint(monkeypatch):
  button = _make_button()
  requests = []
  responses = [
    {"message": "started"},
    {
      "running": True,
      "stage": "updating",
      "progressDetail": "Fetching latest shallow commit...",
      "lastError": "",
    },
    {
      "running": False,
      "stage": "rebooting",
      "progressDetail": "Update complete. Please wait for device to reboot.",
      "lastError": "",
    },
  ]

  def request(path="", method="GET"):
    requests.append((path, method))
    return responses.pop(0)

  monkeypatch.setattr(software, "_galaxy_fast_update_request", request)
  monkeypatch.setattr(software.time, "sleep", lambda *_args: None)

  button._run_fast_update()

  assert requests == [("", "POST"), ("/status", "GET"), ("/status", "GET")]
  assert button._get_fast_update_state().stage == "rebooting"
