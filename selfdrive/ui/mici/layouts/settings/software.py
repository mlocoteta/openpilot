import json
import os
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum

import pyray as rl

from openpilot.common.time_helpers import system_time_valid
from openpilot.selfdrive.ui.lib.starpilot_version import STARPILOT_DISPLAY_VERSION
from openpilot.selfdrive.ui.mici.layouts.settings.device import EngagedConfirmationButton
from openpilot.selfdrive.ui.mici.widgets.button import BigButton, BigParamControl
from openpilot.selfdrive.ui.mici.widgets.dialog import BigConfirmationDialog, BigDialog
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import FontWeight, MousePos, gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.widgets.scroller import NavScroller

UPDATER_TIMEOUT = 10.0
FAST_UPDATE_HOLD_SECONDS = 0.8
FAST_UPDATE_POLL_SECONDS = 0.5
FAST_UPDATE_REQUEST_TIMEOUT = 5.0


@dataclass
class FastUpdateDisplayState:
  stage: str = "idle"
  message: str = ""
  error: str = ""


def _galaxy_api_url(path: str) -> str:
  port = os.getenv("SP_GALAXY_PORT", "8082")
  return f"http://127.0.0.1:{port}/api/update/fast{path}"


def _galaxy_fast_update_request(path: str = "", method: str = "GET") -> dict:
  request = urllib.request.Request(_galaxy_api_url(path), method=method)
  try:
    with urllib.request.urlopen(request, timeout=FAST_UPDATE_REQUEST_TIMEOUT) as response:
      payload = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as error:
    try:
      payload = json.loads(error.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
      payload = {}
    raise RuntimeError(payload.get("error") or str(error)) from error
  except (OSError, urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError) as error:
    raise RuntimeError(f"Galaxy fast update unavailable: {error}") from error

  if not isinstance(payload, dict):
    raise RuntimeError("Galaxy returned an invalid fast update response")
  return payload


def _split_description(desc: str) -> tuple[str, str, str, str] | None:
  parts = [p.strip() for p in desc.split(" / ")]
  if len(parts) != 4:
    return None
  version, branch, commit, date = parts
  return version, branch, commit, date


def _update_failed() -> bool:
  failed_count = ui_state.params.get("UpdateFailedCount")
  try:
    return False if failed_count is None else int(failed_count) > 0
  except (TypeError, ValueError):
    return False


def _request_update_check():
  ui_state.params_memory.put_bool("ManualUpdateInitiated", True)
  os.system("pkill -SIGUSR1 -f system.updated.updated")


def _request_update_download():
  ui_state.params_memory.put_bool("ManualUpdateInitiated", True)
  os.system("pkill -SIGHUP -f system.updated.updated")


class UpdaterState(IntEnum):
  IDLE = 0
  WAITING_FOR_UPDATER = 1
  UPDATER_RESPONDING = 2


class SoftwareInfoLayoutMici(Widget):
  def __init__(self):
    super().__init__()

    self.set_rect(rl.Rectangle(0, 0, 360, 180))

    subheader_color = rl.Color(255, 255, 255, int(255 * 0.9 * 0.65))
    max_width = int(self._rect.width - 20)
    self._version_label = UnifiedLabel("version", 48, max_width=max_width, font_weight=FontWeight.DISPLAY, wrap_text=False)
    self._version_text_label = UnifiedLabel("", 32, max_width=max_width, text_color=subheader_color,
                                            font_weight=FontWeight.ROMAN, wrap_text=False)

    self._branch_label = UnifiedLabel("branch", 48, max_width=max_width, font_weight=FontWeight.DISPLAY, wrap_text=False)
    self._branch_text_label = UnifiedLabel("", 32, max_width=max_width, text_color=subheader_color,
                                           font_weight=FontWeight.ROMAN, wrap_text=False)

  def _update_state(self):
    desc = _split_description(ui_state.params.get("UpdaterCurrentDescription") or "")
    if desc is not None:
      _, branch, commit, date = desc
      self._version_text_label.set_text(f"{STARPILOT_DISPLAY_VERSION} ({date})")
      self._branch_text_label.set_text(f"{branch} ({commit})")
    else:
      self._version_text_label.set_text(STARPILOT_DISPLAY_VERSION if ui_state.params.get("Version") else "N/A")
      self._branch_text_label.set_text(ui_state.params.get("GitBranch") or "N/A")

  def _render(self, _):
    self._version_label.set_position(self._rect.x + 20, self._rect.y - 10)
    self._version_label.render()

    self._version_text_label.set_position(self._rect.x + 20, self._rect.y + 68 - 25)
    self._version_text_label.render()

    self._branch_label.set_position(self._rect.x + 20, self._rect.y + 114 - 30)
    self._branch_label.render()

    self._branch_text_label.set_position(self._rect.x + 20, self._rect.y + 161 - 25)
    self._branch_text_label.render()


class CheckUpdateButton(BigButton):
  def __init__(self):
    self._txt_update_icon = gui_app.texture("icons_mici/settings/device/update.png", 64, 75)
    self._txt_up_to_date_icon = gui_app.texture("icons_mici/settings/device/up_to_date.png", 64, 64)
    super().__init__("check for update", "", self._txt_update_icon)

    self._waiting_for_updater_t: float | None = None
    self._hide_value_t: float | None = None
    self._state: UpdaterState = UpdaterState.IDLE
    self._press_start_t: float | None = None
    self._press_action = ""
    self._fast_update_state = FastUpdateDisplayState()
    self._fast_update_state_lock = threading.Lock()

    ui_state.add_offroad_transition_callback(self.offroad_transition)

  def offroad_transition(self):
    if ui_state.is_offroad():
      self.set_enabled(True)

  def _handle_mouse_press(self, mouse_pos: MousePos):
    super()._handle_mouse_press(mouse_pos)
    self._press_start_t = rl.get_time()
    self._press_action = self.get_value()

  def _handle_mouse_release(self, mouse_pos: MousePos):
    held_for = 0.0 if self._press_start_t is None else rl.get_time() - self._press_start_t
    self._press_start_t = None
    super()._handle_mouse_release(mouse_pos)

    if held_for >= FAST_UPDATE_HOLD_SECONDS:
      self._show_fast_update_confirmation()
      return

    if self._get_fast_update_state().stage == "error":
      self._set_fast_update_state(stage="idle")
      return

    if not system_time_valid():
      dlg = BigDialog("", tr("Please connect to Wi-Fi to update."))
      gui_app.push_widget(dlg)
      return

    self.set_enabled(False)
    self._state = UpdaterState.WAITING_FOR_UPDATER
    self.set_icon(self._txt_update_icon)

    def run():
      if self._press_action == "download update":
        _request_update_download()
      else:
        _request_update_check()

    threading.Thread(target=run, daemon=True).start()

  def _show_fast_update_confirmation(self):
    if not system_time_valid():
      gui_app.push_widget(BigDialog("", tr("Please connect to Wi-Fi to update.")))
      return
    if ui_state.started:
      return

    gui_app.push_widget(BigConfirmationDialog(
      "slide to\nfast update",
      self._txt_update_icon,
      self._start_fast_update,
      red=True,
    ))

  def _set_fast_update_state(self, *, stage: str, message: str = "", error: str = ""):
    with self._fast_update_state_lock:
      self._fast_update_state = FastUpdateDisplayState(stage, message, error)

  def _get_fast_update_state(self) -> FastUpdateDisplayState:
    with self._fast_update_state_lock:
      state = self._fast_update_state
      return FastUpdateDisplayState(state.stage, state.message, state.error)

  def _start_fast_update(self):
    if ui_state.started:
      return

    state = self._get_fast_update_state()
    if state.stage not in ("idle", "error"):
      return

    self._set_fast_update_state(stage="starting", message="starting fast update...")
    threading.Thread(target=self._run_fast_update, daemon=True).start()

  def _run_fast_update(self):
    try:
      _galaxy_fast_update_request(method="POST")

      while True:
        status = _galaxy_fast_update_request("/status")
        stage = str(status.get("stage") or "updating")
        error = str(status.get("lastError") or "").strip()
        message = str(
          status.get("progressDetail") or
          status.get("progressLabel") or
          status.get("message") or
          "fast update in progress..."
        ).strip()

        if error or stage == "error":
          self._set_fast_update_state(stage="error", message="fast update failed", error=error or message)
          return

        self._set_fast_update_state(stage=stage, message=message)
        if not bool(status.get("running")):
          return
        time.sleep(FAST_UPDATE_POLL_SECONDS)
    except Exception as error:
      current = self._get_fast_update_state()
      if current.stage != "rebooting":
        self._set_fast_update_state(stage="error", message="fast update failed", error=str(error))

  def set_value(self, value: str):
    super().set_value(value)
    self.set_text("" if value else "check for update")

  def _update_state(self):
    super()._update_state()

    if ui_state.started:
      self._press_start_t = None
      self.set_enabled(False)
      return

    fast_update_state = self._get_fast_update_state()
    if fast_update_state.stage != "idle":
      self.set_rotate_icon(fast_update_state.stage not in ("error", "rebooting"))
      if fast_update_state.stage == "error":
        self.set_enabled(True)
        self.set_value(fast_update_state.error or fast_update_state.message)
      elif fast_update_state.stage == "rebooting":
        self.set_enabled(False)
        self.set_value("update complete\nrebooting...")
      else:
        self.set_enabled(False)
        self.set_value(fast_update_state.message or "fast update in progress...")
      self.set_text("fast update")
      return

    updater_state = ui_state.params.get("UpdaterState") or ""

    if self._state == UpdaterState.WAITING_FOR_UPDATER:
      self.set_rotate_icon(True)
      if updater_state != "idle":
        self._state = UpdaterState.UPDATER_RESPONDING

      if self._waiting_for_updater_t is None:
        self._waiting_for_updater_t = rl.get_time()

      if self._waiting_for_updater_t is not None and rl.get_time() - self._waiting_for_updater_t > UPDATER_TIMEOUT:
        self.set_rotate_icon(False)
        self.set_value("updater failed\nto respond")
        self._state = UpdaterState.IDLE
        self._hide_value_t = rl.get_time()

    elif self._state == UpdaterState.UPDATER_RESPONDING:
      if updater_state == "idle":
        self.set_rotate_icon(False)
        self._state = UpdaterState.IDLE
        self._hide_value_t = rl.get_time()
      elif self.get_value() != updater_state:
        self.set_value(updater_state)

    elif self._state == UpdaterState.IDLE:
      self.set_rotate_icon(False)
      if _update_failed():
        self.set_enabled(True)
        if self.get_value() != "failed to update":
          self.set_value("failed to update")

      elif ui_state.params.get_bool("UpdaterFetchAvailable"):
        self.set_enabled(True)
        if self.get_value() != "download update":
          self.set_value("download update")

      elif self._hide_value_t is not None:
        self.set_enabled(True)
        if self.get_value() == "checking...":
          self.set_value("up to date")
          self.set_icon(self._txt_up_to_date_icon)

        if rl.get_time() - self._hide_value_t > 3.0:
          self._hide_value_t = None
          self.set_value("")
          self.set_icon(self._txt_update_icon)
      elif self.get_value() != "":
        self.set_value("")

    if self._state != UpdaterState.WAITING_FOR_UPDATER:
      self._waiting_for_updater_t = None


class InstallUpdateButton(BigButton):
  def __init__(self):
    super().__init__("install update", "", gui_app.texture("icons_mici/settings/device/reboot.png", 64, 70))
    self.set_visible(lambda: ui_state.is_offroad() and ui_state.params.get_bool("UpdateAvailable"))

  def _update_state(self):
    super()._update_state()

    desc = _split_description(ui_state.params.get("UpdaterNewDescription") or "")
    value = f"{STARPILOT_DISPLAY_VERSION} ({desc[1]})" if desc is not None else ""
    if self.get_value() != value:
      self.set_value(value)

  def _handle_mouse_release(self, mouse_pos: MousePos):
    super()._handle_mouse_release(mouse_pos)

    self.set_enabled(False)

    def run():
      ui_state.params.put_bool("DoReboot", True)

    threading.Thread(target=run, daemon=True).start()


class BranchSelectPage(NavScroller):
  def __init__(self, on_select: Callable[[str], None]):
    super().__init__()

    params = ui_state.params
    current_git_branch = params.get("GitBranch") or ""
    branches_str = params.get("UpdaterAvailableBranches") or ""
    branches = [b for b in branches_str.split(",") if b]

    for hidden_branch in ("StarPilot-Vetting", "MAKE-PRS-HERE"):
      if hidden_branch in branches:
        branches.remove(hidden_branch)

    for branch in [current_git_branch, "devel-staging", "devel", "nightly", "nightly-dev", "master"]:
      if branch in branches:
        branches.remove(branch)
        branches.insert(0, branch)

    current_target = params.get("UpdaterTargetBranch") or ""
    check_icon = gui_app.texture("icons_mici/settings/device/up_to_date.png", 64, 64)

    buttons = []
    if not branches:
      btn = BigButton("no branches", "check for update first", scroll=True)
      btn.set_enabled(False)
      buttons.append(btn)
    else:
      for branch in branches:
        btn = BigButton(branch, "", check_icon if branch == current_target else None, scroll=True)
        btn.set_click_callback(lambda b=branch: self.dismiss(lambda: on_select(b)))
        buttons.append(btn)

    self._scroller.add_widgets(buttons)


class TargetBranchButton(BigButton):
  def __init__(self):
    super().__init__("target branch", ui_state.params.get("UpdaterTargetBranch") or "")
    self._download_icon = gui_app.texture("icons_mici/settings/device/update.png", 64, 75)
    self.set_click_callback(self._on_click)
    self.set_visible(not ui_state.params.get_bool("IsTestedBranch"))
    self.set_enabled(lambda: ui_state.is_offroad())

  def _update_state(self):
    super()._update_state()

    target = ui_state.params.get("UpdaterTargetBranch") or ""
    if self.get_value() != target:
      self.set_value(target)

  def _on_click(self):
    gui_app.push_widget(BranchSelectPage(self._on_select))

  def _on_select(self, branch: str):
    previous = ui_state.params.get("UpdaterTargetBranch") or ""
    ui_state.params.put("UpdaterTargetBranch", branch)
    self.set_value(branch)
    _request_update_check()

    if branch != previous:
      gui_app.push_widget(BigConfirmationDialog("slide to\ndownload", self._download_icon, _request_update_download))


class SoftwareLayoutMici(NavScroller):
  def __init__(self):
    super().__init__()

    def uninstall_openpilot_callback():
      ui_state.params.put_bool("DoUninstall", True)

    self._automatic_updates_btn = BigParamControl("auto updates", "AutomaticUpdates")

    uninstall_openpilot_btn = EngagedConfirmationButton("uninstall\nStarPilot", "uninstall",
                                                        gui_app.texture("icons_mici/settings/device/uninstall.png", 64, 64),
                                                        uninstall_openpilot_callback, exit_on_confirm=False)

    self._scroller.add_widgets([
      SoftwareInfoLayoutMici(),
      CheckUpdateButton(),
      InstallUpdateButton(),
      TargetBranchButton(),
      self._automatic_updates_btn,
      uninstall_openpilot_btn,
    ])

  def _update_state(self):
    super()._update_state()
    self._automatic_updates_btn.refresh()
