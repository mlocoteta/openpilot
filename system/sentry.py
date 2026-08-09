import glob
import os
import re
import sentry_sdk
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from sentry_sdk.integrations.threading import ThreadingIntegration

from openpilot.system.hardware import HARDWARE, PC
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware.hw import Paths
from openpilot.system.version import get_build_metadata, get_version

from openpilot.starpilot.common.starpilot_variables import ERROR_LOGS_PATH, params

class SentryProject(Enum):
  # python project
  SELFDRIVE = "https://7305139359a548fcb348ec09497dc389@bugsink.firestar.link/1"
  # native project
  SELFDRIVE_NATIVE = "https://7305139359a548fcb348ec09497dc389@bugsink.firestar.link/1"  # noqa: PIE796


def report_tombstone(fn: str, message: str, contents: str) -> None:
  cloudlog.error({'tombstone': message})

  with sentry_sdk.configure_scope() as scope:
    scope.set_extra("tombstone_fn", fn)
    scope.set_extra("tombstone", contents)

    # Attach qlog for debugging context
    qlogs = glob.glob(f"{Paths.log_root()}/*/qlog")
    if qlogs:
      scope.add_attachment(path=max(qlogs, key=os.path.getmtime), filename="qlog")

    sentry_sdk.capture_message(message=message)
    sentry_sdk.flush()


def capture_block():
  with sentry_sdk.push_scope():
    sentry_sdk.capture_message("Blocked user from using the development branch", level='info')
    sentry_sdk.flush()


def capture_message(message: str, *, level: str = "error", tags: dict[str, str] | None = None,
                    extras: dict[str, Any] | None = None, attachment_path: Path | None = None,
                    flush_timeout: float | None = None) -> None:
  try:
    with sentry_sdk.push_scope() as scope:
      for key, value in (tags or {}).items():
        scope.set_tag(key, value)
      for key, value in (extras or {}).items():
        scope.set_extra(key, value)
      if attachment_path is not None and attachment_path.is_file():
        scope.add_attachment(path=str(attachment_path), filename=attachment_path.name)

      sentry_sdk.capture_message(message, level=level)
      if flush_timeout is None:
        sentry_sdk.flush()
      else:
        sentry_sdk.flush(timeout=flush_timeout)
  except Exception:
    cloudlog.exception("sentry message")


def capture_exception(*args, crash_log=True, **kwargs) -> None:
  exc_text = traceback.format_exc()

  phrases_to_check = [
    "already exists. To overwrite it, set 'overwrite' to True",
    "failed after retry",
  ]

  if any(phrase in exc_text for phrase in phrases_to_check):
    return

  save_exception(exc_text, crash_log)
  cloudlog.error("crash", exc_info=kwargs.get('exc_info', 1))

  try:
    with sentry_sdk.push_scope() as scope:
      # Attach qlog for debugging context
      qlogs = glob.glob(f"{Paths.log_root()}/*/qlog")
      if qlogs:
        scope.add_attachment(path=max(qlogs, key=os.path.getmtime), filename="qlog")

      sentry_sdk.capture_exception(*args, **kwargs)
      sentry_sdk.flush()  # https://github.com/getsentry/sentry-python/issues/291
  except Exception:
    cloudlog.exception("sentry exception")


def capture_report(discord_user, report, starpilot_toggles):
  error_file_path = ERROR_LOGS_PATH / "error.txt"
  error_content = "No error log found."

  if error_file_path.exists():
    error_content = error_file_path.read_text()

  with sentry_sdk.push_scope() as scope:
    scope.set_context("Error Log", {"content": error_content})
    scope.set_context("Toggle Values", starpilot_toggles)
    sentry_sdk.capture_message(f"{discord_user} submitted report: {report}", level="fatal")
    sentry_sdk.flush()


def capture_flm_tune_submission(submission: dict) -> None:
  """Send an explicitly submitted FLM tune without attaching drive artifacts."""
  discord_user = str(submission.get("discordUsername", "Unknown") or "Unknown")
  car_name = str(submission.get("carName", "Unknown car") or "Unknown car")
  tune = submission.get("tune", {})
  if not isinstance(tune, dict):
    tune = {}

  capture_message(
    f"{car_name} Tune submitted by {discord_user}",
    level="info",
    tags={"report_type": "flm_tune_submission", "car_name": car_name},
    extras={"flm_tune": tune},
  )


def set_tag(key: str, value: str) -> None:
  sentry_sdk.set_tag(key, value)


def save_exception(exc_text: str, crash_log) -> None:
  files = [
    ERROR_LOGS_PATH / datetime.now().astimezone().strftime("%Y-%m-%d--%H-%M-%S.log"),
    ERROR_LOGS_PATH / "error.txt"
  ]

  for file_path in files:
    if file_path.name == "error.txt" and crash_log:
      lines = exc_text.splitlines()[-10:]
      file_path.write_text("\n".join(lines))
    else:
      file_path.write_text(exc_text)


def init(project: SentryProject) -> bool:
  if PC:
    return False

  build_metadata = get_build_metadata()
  short_branch = build_metadata.channel

  env = short_branch
  if re.search("test", short_branch, re.IGNORECASE):
    env = "Testing"

  dongle_id = params.get("DongleId", encoding="utf-8")
  installed = params.get("InstallDate", encoding="utf-8")
  updated = params.get("Updated", encoding="utf-8")

  integrations = []
  if project == SentryProject.SELFDRIVE:
    integrations.append(ThreadingIntegration(propagate_hub=True))

  sentry_sdk.init(project.value,
                  default_integrations=False,
                  release=get_version(),
                  integrations=integrations,
                  traces_sample_rate=1.0,
                  max_value_length=8192,
                  environment=env)

  sentry_sdk.set_user({"id": dongle_id})
  sentry_sdk.set_tag("origin", build_metadata.openpilot.git_origin)
  sentry_sdk.set_tag("branch", short_branch)
  sentry_sdk.set_tag("commit", build_metadata.openpilot.git_commit)
  sentry_sdk.set_tag("updated", updated)
  sentry_sdk.set_tag("installed", installed)
  sentry_sdk.set_tag("device", HARDWARE.get_device_type())

  if project == SentryProject.SELFDRIVE:
    sentry_sdk.Hub.current.start_session()

  return True
