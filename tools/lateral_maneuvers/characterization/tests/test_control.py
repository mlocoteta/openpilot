import json

import pytest

from openpilot.tools.lateral_maneuvers.characterization import control as C
from openpilot.tools.lateral_maneuvers.characterization import plan as P
from openpilot.tools.lateral_maneuvers.characterization import progress as PR


class JsonParams:
  """Params stand-in: JSON-typed LateralManeuverStatus comes back decoded, like Params.get."""

  def __init__(self):
    self.values = {"LongitudinalManeuverMode": True, "LateralManeuverMode": False,
                   "LateralManeuverStatus": {"state": "idle", "history": ["old"]}}
    self.writes = []

  def get(self, key, encoding=None):
    return self.values.get(key)

  def get_bool(self, key):
    return bool(self.values.get(key))

  def put(self, key, value):
    assert isinstance(value, dict)  # JSON param: a str would raise TypeError in Params.put
    self.writes.append(key)
    self.values[key] = json.loads(json.dumps(value))

  def put_bool(self, key, value):
    self.writes.append(key)
    self.values[key] = bool(value)


@pytest.fixture
def paths(tmp_path):
  return str(tmp_path / "plan.json"), str(tmp_path / "progress.json")


def test_arm_requires_valid_plan(paths):
  plan_path, progress_path = paths
  params = JsonParams()
  ok, msg = C.set_armed(params, True, plan_path=plan_path, progress_path=progress_path)
  assert not ok and "no plan" in msg
  assert params.writes == [] and params.values["LongitudinalManeuverMode"] is True
  with open(plan_path, "w") as f:
    f.write('{"blocks": [{"speed_mph": 99, "settings": {"ti_steer_kp": 0.5}}]}')
  ok, msg = C.set_armed(params, True, plan_path=plan_path, progress_path=progress_path)
  assert not ok and "plan invalid" in msg and params.writes == []


def test_arm_disarm_like_galaxy_and_touch_nothing_else(paths):
  plan_path, progress_path = paths
  with open(plan_path, "w") as f:
    json.dump(P.build_plan("quick"), f)
  plan = P.load_plan(plan_path)
  for b in plan["blocks"][:2]:
    PR.mark_block_complete(plan, b["id"], progress_path)
  params = JsonParams()
  ok, msg = C.set_armed(params, True, plan_path=plan_path, progress_path=progress_path)
  assert ok and msg == "2/12 blocks done — resumes at block 3 next drive"
  assert params.values["LateralManeuverMode"] is True and params.values["LongitudinalManeuverMode"] is False
  status = params.values["LateralManeuverStatus"]
  assert status["state"] == "armed" and status["uiText1"] == "Lateral Characterization Armed"
  assert status["progressDone"] == 2 and status["history"][0] == "old"
  # only the maneuver mode keys and the status popup are written (no ACC / longitudinal params)
  assert set(params.writes) == {"LateralManeuverMode", "LongitudinalManeuverMode", "LateralManeuverStatus"}

  ok, _ = C.set_armed(params, False, plan_path=plan_path, progress_path=progress_path)
  assert ok and params.values["LateralManeuverMode"] is False
  assert params.values["LateralManeuverStatus"]["state"] == "stopped"
  assert params.values["LongitudinalManeuverMode"] is False  # disarm does not re-enable longitudinal

  st = PR.plan_status(plan_path, progress_path)
  assert "2/12" in C.subtitle(st, armed=True) and C.subtitle(st, armed=True).startswith("Armed")
  assert C.reset(progress_path) is True
  assert PR.plan_status(plan_path, progress_path)["done"] == 0


def test_status_string_param_also_accepted(paths):
  plan_path, progress_path = paths
  with open(plan_path, "w") as f:
    json.dump(P.build_plan("quick"), f)
  params = JsonParams()
  params.values["LateralManeuverStatus"] = '{"history": ["a"]}'  # compat wrappers return str
  assert C.set_armed(params, True, plan_path=plan_path, progress_path=progress_path)[0]
  assert params.values["LateralManeuverStatus"]["history"][0] == "a"


def test_plan_status_cache_follows_file_changes(paths):
  plan_path, progress_path = paths
  with open(plan_path, "w") as f:
    json.dump(P.build_plan("quick"), f)
  a = PR.plan_status(plan_path, progress_path)
  with open(plan_path, "w") as f:
    json.dump(P.build_plan("lowspeed"), f)
  b = PR.plan_status(plan_path, progress_path)
  assert a["total"] == 12 and b["total"] == 9 and a["planHash"] != b["planHash"]
