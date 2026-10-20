import json
import os

import pytest

from openpilot.tools.lateral_maneuvers.characterization import plan as P
from openpilot.tools.lateral_maneuvers.characterization import progress as PR
from openpilot.tools.lateral_maneuvers.characterization import runner as R
from openpilot.tools.lateral_maneuvers.characterization import settings as S
from openpilot.tools.lateral_maneuvers.characterization.sidecar import Sidecar
from openpilot.tools.lateral_maneuvers.characterization.tests.test_runner import ORIGINAL, DictStore, SimCar, drive, small_plan


@pytest.fixture
def paths(tmp_path):
  return {"progress": str(tmp_path / "progress.json"), "snap": str(tmp_path / "snap.json"),
          "sidecar": str(tmp_path / "sidecar"), "plan": str(tmp_path / "plan.json")}


def make_runner(paths, plan, ti_enabled=True, route="00000abc--deadbeef"):
  store = DictStore(ORIGINAL)
  mgr = S.SettingsManager(store, paths["snap"])
  sidecar = Sidecar(paths["sidecar"])
  sidecar.set_route(route)
  runner = R.CharacterizationRunner(plan, mgr, sidecar, ti_enabled=ti_enabled,
                                    completed=PR.completed_blocks(plan, paths["progress"]),
                                    on_block_complete=lambda b: PR.mark_block_complete(plan, b, paths["progress"]))
  car = SimCar(store, ti_enabled=ti_enabled)
  runner.start(int(1e12))
  return runner, car, store


def events(runner, kind):
  return [e for e in runner.sidecar.doc["events"] if e["type"] == kind]


# -- progress file -------------------------------------------------------------

def test_mark_reset_and_plan_edit(paths):
  plan = small_plan()
  assert PR.completed_blocks(plan, paths["progress"]) == set()
  assert PR.mark_block_complete(plan, "b2", paths["progress"]) == {"b2"}
  assert PR.mark_block_complete(plan, "b1", paths["progress"]) == {"b1", "b2"}
  with open(paths["progress"]) as f:
    doc = json.load(f)
  assert doc["plans"][PR.plan_hash(plan)]["completed"] == ["b1", "b2"]  # plan order
  s = PR.summary(plan, paths["progress"])
  assert (s["done"], s["total"], s["finished"], s["nextBlock"]) == (2, 2, True, None)

  edited = small_plan(max_attempts_per_maneuver=3)  # any plan edit -> new hash -> fresh progress
  assert PR.plan_hash(edited) != PR.plan_hash(plan)
  assert PR.completed_blocks(edited, paths["progress"]) == set()
  PR.mark_block_complete(edited, "b1", paths["progress"])
  assert PR.completed_blocks(plan, paths["progress"]) == {"b1", "b2"}  # other plan's progress kept

  assert PR.reset_progress(paths["progress"]) is True
  assert not os.path.exists(paths["progress"])
  assert PR.completed_blocks(plan, paths["progress"]) == set()
  assert PR.reset_progress(paths["progress"]) is False


def test_hash_ignores_cosmetics_and_corrupt_file_is_empty(paths):
  plan = small_plan()
  again = small_plan()
  again["estimated_minutes"] = 99
  assert PR.plan_hash(plan) == PR.plan_hash(again)
  with open(paths["progress"], "w") as f:
    f.write("{nope")
  assert PR.completed_blocks(plan, paths["progress"]) == set()
  PR.mark_block_complete(plan, "b1", paths["progress"])  # corrupt file is replaced
  assert PR.completed_blocks(plan, paths["progress"]) == {"b1"}


def test_plan_status_and_texts(paths):
  st = PR.plan_status(paths["plan"], paths["progress"])
  assert not st["ok"] and "no plan" in st["error"]
  with open(paths["plan"], "w") as f:
    f.write('{"blocks": []}')
  st = PR.plan_status(paths["plan"], paths["progress"])
  assert not st["ok"] and "plan invalid" in st["error"]
  with open(paths["plan"], "w") as f:
    json.dump(P.build_plan("quick"), f)
  plan = P.load_plan(paths["plan"])
  st = PR.plan_status(paths["plan"], paths["progress"])
  assert st["ok"] and st["text"] == f"0/{len(plan['blocks'])} blocks done"
  for b in plan["blocks"][:3]:
    PR.mark_block_complete(plan, b["id"], paths["progress"])
  st = PR.plan_status(paths["plan"], paths["progress"])
  assert st["text"] == f"3/{len(plan['blocks'])} blocks done — resumes at block 4 next drive"


def test_cli_progress_and_reset(paths, capsys):
  with open(paths["plan"], "w") as f:
    json.dump(P.build_plan("quick"), f)
  plan = P.load_plan(paths["plan"])
  PR.mark_block_complete(plan, plan["blocks"][0]["id"], paths["progress"])
  assert P.main(["progress", paths["plan"], "--progress-file", paths["progress"]]) == 0
  assert "1/12 blocks done" in capsys.readouterr().out
  assert P.main(["reset-progress", "--progress-file", paths["progress"]]) == 0
  assert "deleted" in capsys.readouterr().out
  assert not os.path.exists(paths["progress"])


# -- runner --------------------------------------------------------------------

def test_full_run_records_every_block(paths):
  plan = small_plan()
  runner, car, store = make_runner(paths, plan)
  outs = drive(runner, car, 6000)
  assert runner.finish_reason == "completed"
  assert PR.completed_blocks(plan, paths["progress"]) == {"b1", "b2"}
  assert [e["block"] for e in events(runner, "block_complete")] == ["b1", "b2"]
  assert outs[-1].text1 == "Characterization finished"
  assert not any(o.text1.startswith("Resuming") for o in outs)
  assert store.values == ORIGINAL


def test_resume_skips_completed_blocks(paths):
  plan = small_plan()
  PR.mark_block_complete(plan, "b1", paths["progress"])
  runner, car, store = make_runner(paths, plan)
  outs = drive(runner, car, 6000)
  start = events(runner, "run_start")[0]
  assert start["resumed_done"] == 1 and start["completed_blocks"] == ["b1"]
  assert [(e["block"], e["index"]) for e in events(runner, "block_start")] == [("b2", 2)]
  assert "maneuver_start" in [e["type"] for e in runner.sidecar.doc["events"]]
  assert {e["block"] for e in events(runner, "maneuver_start")} == {"b2"}
  assert any(o.text1 == "Resuming: block 2/2 (1 done)" for o in outs)
  assert runner.finish_reason == "completed" and outs[-1].text1 == "Characterization finished"
  assert PR.completed_blocks(plan, paths["progress"]) == {"b1", "b2"}
  assert store.values == ORIGINAL


def test_all_done_does_not_restart_or_touch_params(paths):
  plan = small_plan()
  for b in ("b1", "b2"):
    PR.mark_block_complete(plan, b, paths["progress"])
  runner, car, store = make_runner(paths, plan)
  assert runner.state == "done" and runner.already_complete
  assert not os.path.exists(paths["snap"])
  outs = [runner.step(car.frame_for(runner, None)) for _ in range(200)]
  assert all(not o.plan_valid for o in outs)
  assert outs[-1].text1 == "Characterization finished"
  assert "reset progress" in outs[-1].text2
  kinds = [e["type"] for e in runner.sidecar.doc["events"]]
  assert kinds == ["run_start", "run_end"]
  assert store.values == ORIGINAL and store.refresh_requests == 0
  runner.finish("process_exit", int(2e12))  # atexit: no-op
  assert [e["type"] for e in runner.sidecar.doc["events"]] == kinds


def test_skipped_maneuver_leaves_block_incomplete_then_retried(paths):
  plan = small_plan(max_attempts_per_maneuver=2)
  runner, car, store = make_runner(paths, plan)

  def hook(i, runner, car):
    car.speed_offset = 0.0
    if runner.player is not None and runner.player.active and runner.player.spec["type"] == "step" \
       and runner.player.frame > 5:
      car.speed_offset = 2.0
  outs = drive(runner, car, 8000, hook)
  assert [e["maneuver"] for e in events(runner, "maneuver_skipped")] == ["b1m2"]
  assert [e["complete"] for e in events(runner, "block_end")] == [False, True]
  assert PR.completed_blocks(plan, paths["progress"]) == {"b2"}
  assert runner.finish_reason == "pass_incomplete"
  assert outs[-1].text1 == "Pass done: 1/2 blocks complete"
  assert store.values == ORIGINAL

  # next drive (new process): only b1 runs, then the plan is finished
  runner2, car2, store2 = make_runner(paths, plan, route="00000abd--deadbeef")
  outs2 = drive(runner2, car2, 8000)
  assert [e["block"] for e in events(runner2, "block_start")] == ["b1"]
  assert any(o.text1 == "Resuming: block 1/2 (1 done)" for o in outs2)
  assert runner2.finish_reason == "completed"
  assert PR.completed_blocks(plan, paths["progress"]) == {"b1", "b2"}


def test_unverified_settings_block_not_complete(paths):
  plan = small_plan()
  runner, car, _ = make_runner(paths, plan, ti_enabled=False)  # TISteerKp never confirmed
  drive(runner, car, 12000)
  assert [e["block"] for e in events(runner, "block_skipped")] == ["b1", "b2"]
  assert PR.completed_blocks(plan, paths["progress"]) == set()
  assert runner.finish_reason == "pass_incomplete"


def test_exit_mid_block_keeps_earlier_progress(paths):
  plan = small_plan()
  runner, car, store = make_runner(paths, plan)

  def hook(i, runner, car):
    if runner.block is not None and runner.block["id"] == "b2" and runner.player is not None and runner.player.active:
      raise KeyboardInterrupt
  with pytest.raises(KeyboardInterrupt):
    try:
      drive(runner, car, 8000, hook)
    finally:
      runner.finish("process_exit", int(2e12))
  assert PR.completed_blocks(plan, paths["progress"]) == {"b1"}
  assert store.values == ORIGINAL


def test_progress_write_failure_does_not_stop_run(paths):
  plan = small_plan()
  store = DictStore(ORIGINAL)
  logs = []

  def fail(block_id):
    raise OSError("disk full")
  runner = R.CharacterizationRunner(plan, S.SettingsManager(store, paths["snap"]), None, log=logs.append,
                                    on_block_complete=fail)
  runner.start(int(1e12))
  car = SimCar(store)
  out = None
  for _ in range(6000):
    out = runner.step(car.frame_for(runner, out))
    if runner.state == "done" and runner.restore_verifier is None:
      break
  assert runner.finish_reason == "completed"
  assert any("progress write failed" in line for line in logs)
