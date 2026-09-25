"""Cross-drive progress for a characterization plan.

/data/lateral_characterization_progress.json holds, per plan hash, the ids of the blocks whose
maneuvers all completed. A block with a skipped maneuver or unverified settings is not complete
and is retried on the next drive. Editing the plan changes its hash, so it starts fresh (the
progress of other plans in the file is kept, so swapping plan files back and forth resumes each).

The file is rewritten atomically (fsync + rename) right after each completed block, so progress
survives process exit, car off and reboot. Deleting the file (reset_progress) starts every plan
from block 1 again.
"""
import copy
import hashlib
import json
import os
import time

PROGRESS_PATH = "/data/lateral_characterization_progress.json"
PROGRESS_VERSION = 1


def plan_hash(plan):
  """Stable hash of a normalized plan (derived/cosmetic fields excluded)."""
  content = copy.deepcopy(plan)
  content.pop("estimated_minutes", None)
  text = json.dumps(content, sort_keys=True, separators=(",", ":"))
  return hashlib.sha256(text.encode()).hexdigest()[:16]


def _read(path):
  try:
    with open(path) as f:
      payload = json.load(f)
  except (FileNotFoundError, OSError, ValueError):
    return {"version": PROGRESS_VERSION, "plans": {}}
  if not isinstance(payload, dict) or not isinstance(payload.get("plans"), dict):
    return {"version": PROGRESS_VERSION, "plans": {}}
  return payload


def completed_blocks(plan, path=PROGRESS_PATH):
  """Ids of the plan's blocks recorded as complete (ids not in the plan are ignored)."""
  entry = _read(path)["plans"].get(plan_hash(plan)) or {}
  done = entry.get("completed") if isinstance(entry, dict) else None
  ids = {b["id"] for b in plan["blocks"]}
  return {str(i) for i in done if str(i) in ids} if isinstance(done, list) else set()


def mark_block_complete(plan, block_id, path=PROGRESS_PATH):
  from openpilot.tools.lateral_maneuvers.characterization.settings import _atomic_write_json
  payload = _read(path)
  key = plan_hash(plan)
  entry = payload["plans"].get(key)
  if not isinstance(entry, dict):
    entry = {}
  done = [str(i) for i in entry.get("completed") or [] if isinstance(i, str)]
  if block_id not in done:
    done.append(block_id)
  order = {b["id"]: i for i, b in enumerate(plan["blocks"])}
  done.sort(key=lambda i: order.get(i, len(order)))
  payload["version"] = PROGRESS_VERSION
  payload["plans"][key] = {"name": plan["name"], "total": len(plan["blocks"]), "completed": done,
                           "updatedWall": time.time()}  # noqa: TID251 (human-readable wall time)
  _atomic_write_json(path, payload)
  return set(done)


def reset_progress(path=PROGRESS_PATH):
  """Delete the progress file (all plans). Returns True when a file was removed."""
  try:
    os.unlink(path)
    return True
  except FileNotFoundError:
    return False


def summary(plan, path=PROGRESS_PATH):
  done = completed_blocks(plan, path)
  total = len(plan["blocks"])
  nxt = next((i for i, b in enumerate(plan["blocks"]) if b["id"] not in done), None)
  return {"done": len(done), "total": total, "finished": len(done) >= total, "planHash": plan_hash(plan),
          "planName": plan["name"], "nextBlock": nxt + 1 if nxt is not None else None,
          "nextBlockId": plan["blocks"][nxt]["id"] if nxt is not None else None, "completed": sorted(done)}


def summary_text(s):
  """One line for the settings subtitle / Galaxy."""
  if s["finished"]:
    return f"All {s['total']} blocks done — reset progress to run again"
  if s["done"] == 0:
    return f"0/{s['total']} blocks done"
  return f"{s['done']}/{s['total']} blocks done — resumes at block {s['nextBlock']} next drive"


def plan_status(plan_path=None, progress_path=PROGRESS_PATH):
  """{ok, error, plan summary...} for UIs: never raises."""
  from openpilot.tools.lateral_maneuvers.characterization.plan import PLAN_PATH, PlanError, load_plan
  plan_path = plan_path or PLAN_PATH
  try:
    plan = load_plan(plan_path)
  except (PlanError, OSError) as e:
    return {"ok": False, "error": f"plan invalid: {e}", "planPath": plan_path}
  if plan is None:
    return {"ok": False, "error": f"no plan at {plan_path}", "planPath": plan_path}
  s = summary(plan, progress_path)
  s.update({"ok": True, "error": "", "planPath": plan_path, "text": summary_text(s),
            "estimatedMinutes": plan["estimated_minutes"]})
  return s
