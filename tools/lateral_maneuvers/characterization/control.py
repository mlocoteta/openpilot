"""Arm/disarm + progress for the on-device settings toggle (same effect as Galaxy start/stop).

Arming sets LateralManeuverMode (manager then runs lateral_maneuversd while onroad), turns
LongitudinalManeuverMode off and writes the LateralManeuverStatus popup, exactly like
/api/lateral_maneuvers/start. Nothing here touches ACC set speed or longitudinal params.
"""
import time

from openpilot.starpilot.common.json_param import load_json_param
from openpilot.tools.lateral_maneuvers.characterization.progress import PROGRESS_PATH, plan_status, reset_progress

STATUS_PARAM = "LateralManeuverStatus"


def _history(status, line):
  history = [str(h) for h in (status.get("history") or []) if str(h).strip()] if isinstance(status.get("history"), list) else []
  history.append(line)
  status["history"] = history[-120:]


def _status(params):
  return load_json_param(params.get(STATUS_PARAM, encoding="utf-8"), {})


def set_armed(params, enabled, mode_params=None, source="comma settings", plan_path=None, progress_path=PROGRESS_PATH):
  """params: raw Params for the status JSON; mode_params: object whose put_bool writes the mode keys
  (the settings panel passes its cached params so the toggle updates immediately). Returns (ok, message)."""
  mode_params = mode_params or params
  status = _status(params)
  now = time.monotonic()
  if enabled:
    ps = plan_status(plan_path, progress_path)
    if not ps["ok"]:
      return False, ps["error"]
    mode_params.put_bool("LongitudinalManeuverMode", False)
    mode_params.put_bool("LateralManeuverMode", True)
    status.update({"state": "armed", "phase": "", "maneuver": "", "runIndex": 0, "runTotal": ps["total"],
                   "stepIndex": 0, "stepTotal": 0, "phaseStepIndex": 0, "phaseStepTotal": 0, "uiShow": True,
                   "uiSize": "mid", "uiText1": "Lateral Characterization Armed", "uiText2": ps["text"],
                   "progressDone": ps["done"], "progressTotal": ps["total"], "updatedAtSec": now})
    _history(status, f"Armed from {source}: plan '{ps['planName']}', {ps['text']}.")
    message = ps["text"]
  else:
    mode_params.put_bool("LateralManeuverMode", False)
    status.update({"state": "stopped", "uiShow": True, "uiSize": "small", "uiText1": "Lateral Maneuvers Stopped",
                   "uiText2": "Test mode disabled.", "updatedAtSec": now})
    _history(status, f"Stopped from {source}.")
    message = "disarmed"
  params.put(STATUS_PARAM, status)
  return True, message


def reset(progress_path=PROGRESS_PATH):
  return reset_progress(progress_path)


def subtitle(status, armed):
  """Settings-row subtitle for a plan_status() dict."""
  if not status["ok"]:
    return f"Unavailable: {status['error']}. Write the plan with tools/lateral_maneuvers/characterization/plan.py."
  prefix = "Armed · " if armed else ""
  return f"{prefix}Plan '{status['planName']}': {status['text']}."
