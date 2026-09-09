import json
from types import SimpleNamespace

import numpy as np
import pytest

from openpilot.starpilot.common.model_lab import (
  LATERAL_PLAN_COLUMNS,
  compose_model_outputs,
  hybrid_action_values,
  is_small_model_metadata,
  model_lab_manifest_eligible,
  model_lab_pair_display_name,
  model_lab_pair_display_name_from_params,
  normalize_model_lab_config,
  validate_model_lab_selection,
)


def _catalog_model(version="v15", *, small=True, eligible=True, artifact_available=True, artifact_installed=True):
  return {
    "version": version,
    "small": small,
    "modelLabEligible": eligible,
    "modelLabArtifactAvailable": artifact_available,
    "modelLabArtifactInstalled": artifact_installed,
  }


def test_manifest_eligibility_uses_explicit_size_and_legacy_gpu_inference():
  assert not is_small_model_metadata({"model_size": "small", "uses_external_gpu": True})
  assert not is_small_model_metadata({"model_size": "chestnut", "uses_external_gpu": False})
  assert is_small_model_metadata({"uses_external_gpu": False})
  assert not is_small_model_metadata({"uses_external_gpu": True})
  assert model_lab_manifest_eligible({"uses_external_gpu": False}, "v15")
  assert not model_lab_manifest_eligible({"uses_external_gpu": True}, "v16")
  assert not model_lab_manifest_eligible({"model_lab_eligible": False}, "v15")
  assert not model_lab_manifest_eligible({"uses_external_gpu": False}, "v7")


def test_config_normalization_is_closed_by_default():
  assert normalize_model_lab_config("not-json") == {
    "enabled": False,
    "lateralModel": "",
    "longitudinalModel": "",
  }
  assert normalize_model_lab_config('{"enabled": true, "lateralModel": " lat ", "longitudinalModel": "long"}') == {
    "enabled": True,
    "lateralModel": "lat",
    "longitudinalModel": "long",
  }


def test_model_lab_pair_display_name_is_compact_and_reads_enabled_config():
  assert model_lab_pair_display_name("South Carolina", "Pop Model V2") == "SC + PopV2"
  assert model_lab_pair_display_name("Falling Phoenix", "Down To Ride v6") == "FP + DTRv6"

  class FakeParams:
    def __init__(self, values):
      self.values = values

    def get(self, key):
      return self.values.get(key)

  params = FakeParams({
    "ModelLabConfig": json.dumps({
      "enabled": True,
      "lateralModel": "sc23",
      "longitudinalModel": "pop223",
    }),
    "AvailableModels": "sc23,pop223",
    "AvailableModelNames": "South Carolina,Pop Model V2",
  })
  assert model_lab_pair_display_name_from_params(params) == "SC + PopV2"

  params.values["ModelLabConfig"] = json.dumps({"enabled": False})
  assert model_lab_pair_display_name_from_params(params) == ""


@pytest.mark.parametrize(
  ("chestnut_ready", "catalog", "lateral", "longitudinal", "expected"),
  [
    (False, {"lat": _catalog_model(), "long": _catalog_model()}, "lat", "long", "Chestnut"),
    (True, {"lat": _catalog_model()}, "lat", "missing", "current manifest"),
    (True, {"lat": _catalog_model(small=False), "long": _catalog_model()}, "lat", "long", "Chestnut-class"),
    (True, {"lat": _catalog_model(artifact_available=False), "long": _catalog_model()}, "lat", "long", "no precompiled AMD"),
    (True, {"lat": _catalog_model(artifact_installed=False), "long": _catalog_model()}, "lat", "long", "not downloaded"),
  ],
)
def test_selection_validation_rejects_unsafe_pairs(chestnut_ready, catalog, lateral, longitudinal, expected):
  error = validate_model_lab_selection(
    {"enabled": True, "lateralModel": lateral, "longitudinalModel": longitudinal},
    catalog,
    chestnut_ready=chestnut_ready,
  )
  assert expected in error


def test_selection_validation_accepts_distinct_ready_small_mixed_version_models():
  catalog = {"lat": _catalog_model("v15"), "long": _catalog_model("v9")}
  assert validate_model_lab_selection(
    {"enabled": True, "lateralModel": "lat", "longitudinalModel": "long"},
    catalog,
    chestnut_ready=True,
  ) is None
  assert validate_model_lab_selection({"enabled": False}, {}, chestnut_ready=False) is None


def test_composition_assigns_lateral_and_longitudinal_outputs_without_mutation():
  lateral_plan = np.full((1, 33, 15), 11.0, dtype=np.float32)
  longitudinal_plan = np.full((1, 33, 15), 22.0, dtype=np.float32)
  lateral_action = np.array([[1.5, 2.5]], dtype=np.float32)
  longitudinal_action = np.array([[3.5, 4.5]], dtype=np.float32)
  lateral = {
    "plan": lateral_plan,
    "plan_stds": lateral_plan + 1,
    "action": lateral_action,
    "action_stds": lateral_action + 1,
    "lane_lines": np.array([111.0]),
    "pose": np.array([113.0]),
    "lead": np.array([112.0]),
  }
  longitudinal = {
    "plan": longitudinal_plan,
    "plan_stds": longitudinal_plan + 2,
    "action": longitudinal_action,
    "action_stds": longitudinal_action + 2,
    "lane_lines": np.array([221.0]),
    "pose": np.array([223.0]),
    "lead": np.array([222.0]),
  }

  composed = compose_model_outputs(lateral, longitudinal)

  lateral_columns = set(LATERAL_PLAN_COLUMNS)
  for column in range(15):
    expected = 11.0 if column in lateral_columns else 22.0
    np.testing.assert_array_equal(composed["plan"][..., column], expected)
  assert composed["action"][0, 0] == lateral_action[0, 0]
  assert composed["action"][0, 1] == longitudinal_action[0, 1]
  assert composed["lane_lines"] is lateral["lane_lines"]
  assert composed["pose"] is lateral["pose"]
  assert composed["lead"] is longitudinal["lead"]
  np.testing.assert_array_equal(lateral_plan, 11.0)
  np.testing.assert_array_equal(longitudinal_plan, 22.0)

  composed_on_longitudinal_frame = compose_model_outputs(lateral, longitudinal, longitudinal)
  assert composed_on_longitudinal_frame["pose"] is longitudinal["pose"]


def test_composition_fails_closed_for_incompatible_plan_contracts():
  with pytest.raises(ValueError, match="incompatible"):
    compose_model_outputs(
      {"plan": np.zeros((1, 33, 15))},
      {"plan": np.zeros((1, 32, 15))},
    )


def test_composition_does_not_leak_longitudinal_values_into_lateral_only_fields():
  composed = compose_model_outputs(
    {"plan": np.zeros((1, 33, 15))},
    {
      "plan": np.zeros((1, 33, 15)),
      "desired_curvature": np.ones((1, 1)),
      "lane_lines": np.ones((1, 4, 33, 2)),
    },
  )
  assert "action" not in composed
  assert "desired_curvature" not in composed
  assert "lane_lines" not in composed


def test_composition_rejects_asymmetric_action_contracts():
  with pytest.raises(ValueError, match="matching action outputs"):
    compose_model_outputs(
      {"plan": np.zeros((1, 33, 15))},
      {"plan": np.zeros((1, 33, 15)), "action": np.ones((1, 2))},
    )


def test_hybrid_action_uses_only_the_assigned_responsibility():
  lateral = SimpleNamespace(desiredCurvature=0.125, desiredAcceleration=99, shouldStop=True)
  longitudinal = SimpleNamespace(desiredCurvature=88, desiredAcceleration=-0.75, shouldStop=False)
  assert hybrid_action_values(lateral, longitudinal) == {
    "desiredCurvature": 0.125,
    "desiredAcceleration": -0.75,
    "shouldStop": False,
  }
