import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from openpilot.common.params import Params, ParamKeyType
from openpilot.starpilot.galaxy.developer_settings import DeveloperSettingsOwner
from openpilot.starpilot.lateral.chubbs_lane import KEY, ChubbsLaneCentering, selected
from openpilot.starpilot.lateral.lane_runtime import LaneCenteringHost
from openpilot.starpilot.lateral.tests.test_blendful import frame
from openpilot.starpilot.ui.feature_settings_state import FeatureSettingsRequest


def action():
  return SimpleNamespace(desiredCurvature=0.0, desiredAcceleration=-0.3, shouldStop=True)


def apply(policy, outputs=None, **overrides):
  values = {"active": True, "desire": 0, "lane_change": 0}
  values.update(overrides)
  return policy.apply(frame(center=.5) if outputs is None else outputs, action(), 20., **values)


def test_default_off_and_typed_persistence(tmp_path):
  params = Params(str(tmp_path))
  assert params.get_type(KEY) == ParamKeyType.BOOL
  assert params.get_default_value(KEY) is False
  assert not selected(params)
  for raw in (b"", b"0", b"true", b"1\n", b"1" * 9):
    Path(params.get_param_path(KEY)).write_bytes(raw)
    assert not selected(params)
  params.put_bool(KEY, True, block=True)
  assert selected(params)
  assert selected(Params(str(tmp_path)))


def test_disabled_never_reads_outputs_or_changes_actions():
  policy = ChubbsLaneCentering(False)
  original = action()
  assert policy.apply(None, original, 20., active=True, desire=0, lane_change=0) is original
  assert vars(original) == vars(action())
  assert policy.policy is None


def test_centers_without_modifying_longitudinal():
  policy = ChubbsLaneCentering(True)
  result = None
  for _ in range(120):
    result = apply(policy)
  assert result.desiredCurvature > 0
  assert result.desiredAcceleration == -.3 and result.shouldStop
  assert policy.policy.trust > .9


@pytest.mark.parametrize("field,value", [("active", False), ("desire", 1), ("desire", 2), ("lane_change", 1)])
def test_no_correction_during_inactive_turn_or_lane_change(field, value):
  policy = ChubbsLaneCentering(True)
  for _ in range(80):
    apply(policy)
  assert policy.policy.curvature != 0
  assert apply(policy, **{field: value}).desiredCurvature == 0
  assert policy.policy.curvature == 0


@pytest.mark.parametrize("case", ["missing", "shape", "nan", "zero_std", "negative_std", "probability", "plan_x", "dtype"])
def test_unsupported_or_corrupt_outputs_preserve_model_action(case):
  outputs = frame(center=.5)
  if case == "missing":
    del outputs["lane_lines_stds"]
  elif case == "shape":
    outputs["lane_lines"] = outputs["lane_lines"][:, :3]
  elif case == "nan":
    outputs["lane_lines"][0, 1, 0, 0] = np.nan
  elif case == "zero_std":
    outputs["lane_lines_stds"][:] = 0
  elif case == "negative_std":
    outputs["lane_lines_stds"][:] = -1
  elif case == "probability":
    outputs["lane_lines_prob"][:] = 2
  elif case == "plan_x":
    outputs["plan"][0, :, 0] = 0
  elif case == "dtype":
    outputs["plan"] = outputs["plan"].astype(object)
  result = apply(ChubbsLaneCentering(True), outputs)
  assert vars(result) == vars(action())


def test_normal_lane_controller_is_not_stacked_and_selection_is_frozen(tmp_path):
  params = Params(str(tmp_path))
  params.put_bool("LaneCentering", True, block=True)
  params.put_bool(KEY, True, block=True)
  host = LaneCenteringHost(params)
  assert host.sample(None, now_ns=1, lateral_active=True, longitudinal_active=False) is None
  params.put_bool(KEY, False, block=True)
  assert host.sample(None, now_ns=2, lateral_active=True, longitudinal_active=False) is None
  assert not LaneCenteringHost(params).chubbs_enabled


def test_developer_row_and_parked_exact_write(tmp_path):
  params = Params(str(tmp_path))
  parked = [True]
  owner = DeveloperSettingsOwner(params, lambda: parked[0])
  row = next(row for row in owner.snapshot().rows if row.key == KEY)
  assert row.label == "Try Chubbs Lane Centering" and row.value == "Off"
  assert owner.apply(FeatureSettingsRequest(KEY, None, "On"))
  assert selected(params)
  assert not owner.apply(FeatureSettingsRequest(KEY, None, "Off"))
  parked[0] = False
  assert not owner.apply(FeatureSettingsRequest(KEY, b"1", "Off"))
  assert selected(params)


def test_actual_modeld_call_preserves_driver_override_and_desire():
  source = Path(__file__).resolve().parents[3] / "selfdrive/modeld/modeld.py"
  tree = ast.parse(source.read_text())
  call = next(node for node in ast.walk(tree) if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
              and ast.unparse(node.value.func) == "chubbs.apply")
  code = compile(ast.fix_missing_locations(ast.Module(body=[call], type_ignores=[])), str(source), "exec")
  class State(dict):
    def all_checks(self, services):
      return True
  state = State(carControl=SimpleNamespace(latActive=True),
                carState=SimpleNamespace(canValid=True, canTimeout=False, steeringPressed=False))
  policy = ChubbsLaneCentering(True)
  for _ in range(100):
    result = action()
    scope = {"chubbs": policy, "model_output": frame(center=.5), "action": result, "v_ego": 20., "sm": state,
             "desire": 0, "DH": SimpleNamespace(lane_change_state=0)}
    exec(code, scope)
  assert result.desiredCurvature > 0
  state["carState"].steeringPressed = True
  result = action()
  scope["action"] = result
  exec(code, scope)
  assert result.desiredCurvature == 0
