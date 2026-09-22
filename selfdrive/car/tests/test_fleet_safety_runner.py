"""Runner orchestration tests: no native libraries, route downloads, or vehicle IO."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def runner():
  spec = importlib.util.spec_from_file_location("fleet_safety_runner_test", Path(__file__).with_name("fleet_safety.py"))
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


def test_inventory_missing_route_remains_uncovered(runner, monkeypatch):
  monkeypatch.setitem(sys.modules, "opendbc.car.values", SimpleNamespace(PLATFORMS={"covered": None, "exempt": None, "missing": None}))
  monkeypatch.setitem(sys.modules, "opendbc.car.tests.routes", SimpleNamespace(
    routes=[SimpleNamespace(car_model="covered", route="route-a", segment=2)], non_tested_cars=["exempt"]))
  entries = {entry["platform"]: entry for entry in runner.inventory()}
  assert entries["covered"]["status"] == "pending"
  assert entries["covered"]["routes"] == [{"route": "route-a", "segment": 2}]
  assert entries["exempt"]["declared_without_route"]
  assert entries["exempt"]["status"] == "uncovered"
  assert entries["missing"]["status"] == "uncovered"


def configure_main(runner, monkeypatch, tmp_path, routes):
  monkeypatch.setattr(sys, "argv", ["fleet_safety", "--all", "--scenario", "recorded", "--out", str(tmp_path)])
  monkeypatch.setattr(runner, "inventory", lambda: [dict(platform="test-platform", routes=routes,
                                                        declared_without_route=False, status="pending" if routes else "uncovered")])
  monkeypatch.setattr(runner, "build_safety", lambda *args: tmp_path / "mock-safety")


def test_missing_route_fails_run(runner, monkeypatch, tmp_path):
  configure_main(runner, monkeypatch, tmp_path, [])
  (tmp_path / "results.json").write_text(json.dumps(dict(cases=[], counts={"pass": 1})))
  monkeypatch.setattr(runner.subprocess, "run", lambda *args, **kwargs: pytest.fail("No route may launch a worker"))
  assert runner.main() == 1
  report = json.loads((tmp_path / "results.json").read_text())
  assert report["counts"] == {"uncovered": 1}


def test_failed_build_cannot_leave_stale_pass(runner, monkeypatch, tmp_path):
  configure_main(runner, monkeypatch, tmp_path, [])
  (tmp_path / "results.json").write_text(json.dumps(dict(cases=[], counts={"pass": 1})))

  def failed_build(*args):
    raise OSError("compiler unavailable")

  monkeypatch.setattr(runner, "build_safety", failed_build)
  assert runner.main() == 1
  report = json.loads((tmp_path / "results.json").read_text())
  assert report["counts"] == {"error": 1}
  assert report["cases"][0]["reason"] == "Safety build failed"


@pytest.mark.parametrize("status,returncode,expected", [
  ("pass", 0, 0), ("failed", 1, 1), ("uncovered", 1, 1), ("error", 1, 1),
])
def test_worker_status_controls_overall_result(runner, monkeypatch, tmp_path, status, returncode, expected):
  configure_main(runner, monkeypatch, tmp_path, [dict(route="registered-route", segment=2)])

  def worker(command, **kwargs):
    path = Path(command[command.index("--worker") + 1])
    case = json.loads(path.read_text())
    path.with_suffix(".result.json").write_text(json.dumps(dict(status=status, execution_id=case["execution_id"])))
    return SimpleNamespace(returncode=returncode)

  monkeypatch.setattr(runner.subprocess, "run", worker)
  assert runner.main() == expected
  report = json.loads((tmp_path / "results.json").read_text())
  assert report["counts"] == {status: 1}


def test_crashed_worker_cannot_reuse_previous_pass(runner, monkeypatch, tmp_path):
  configure_main(runner, monkeypatch, tmp_path, [dict(route="new-route", segment=2)])
  (tmp_path / "case_0000.result.json").write_text(json.dumps(dict(status="pass", route="old-route")))
  monkeypatch.setattr(runner.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1))
  assert runner.main() == 1
  report = json.loads((tmp_path / "results.json").read_text())
  assert report["counts"] == {"error": 1}


def test_worker_nonzero_exit_cannot_report_pass(runner, monkeypatch, tmp_path):
  configure_main(runner, monkeypatch, tmp_path, [dict(route="registered-route", segment=2)])

  def worker(command, **kwargs):
    path = Path(command[command.index("--worker") + 1])
    case = json.loads(path.read_text())
    path.with_suffix(".result.json").write_text(json.dumps(dict(status="pass", execution_id=case["execution_id"])))
    return SimpleNamespace(returncode=1)

  monkeypatch.setattr(runner.subprocess, "run", worker)
  assert runner.main() == 1


def test_wrong_execution_identity_cannot_report_pass(runner, monkeypatch, tmp_path):
  configure_main(runner, monkeypatch, tmp_path, [dict(route="registered-route", segment=2)])

  def worker(command, **kwargs):
    path = Path(command[command.index("--worker") + 1])
    path.with_suffix(".result.json").write_text(json.dumps(dict(status="pass", execution_id="other-run")))
    return SimpleNamespace(returncode=0)

  monkeypatch.setattr(runner.subprocess, "run", worker)
  assert runner.main() == 1
  report = json.loads((tmp_path / "results.json").read_text())
  assert report["counts"] == {"error": 1}
