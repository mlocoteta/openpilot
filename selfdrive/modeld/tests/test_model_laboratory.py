import json
from types import SimpleNamespace

import numpy as np
from tinygrad.uop.ops import Ops, UOpMetaClass

from openpilot.selfdrive.modeld import dmonitoringmodeld
from openpilot.selfdrive.modeld import modeld


class FakeParams:
  def __init__(self, config):
    self.config = config
    self.values = {}

  def get(self, key):
    if key == "ModelLabConfig":
      return self.config
    return None

  def put(self, key, value):
    self.values[key] = value


def test_runtime_request_accepts_two_ready_small_mixed_version_models(tmp_path, monkeypatch):
  config = {"enabled": True, "lateralModel": "lat", "longitudinalModel": "long"}
  params = FakeParams(config)
  (tmp_path / ".model_versions.json").write_text(json.dumps({"lat": "v15", "long": "v9"}))
  (tmp_path / "lat_driving_tinygrad.pkl").write_bytes(b"lat")
  (tmp_path / "long_driving_tinygrad.pkl").write_bytes(b"long")
  monkeypatch.setattr(modeld, "MODELS_PATH", tmp_path)
  monkeypatch.setattr(
    modeld,
    "load_model_artifact_metadata",
    lambda model_id: {"model_size": "small", "model_lab_eligible": model_id in {"lat", "long"}},
  )
  monkeypatch.setattr(modeld, "model_accelerator_artifact_available", lambda model_id: model_id in {"lat", "long"})
  monkeypatch.setattr(modeld, "model_accelerator_artifact_installed", lambda model_id: model_id in {"lat", "long"})

  normalized, error = modeld._model_lab_runtime_request(params, chestnut_ready=True)

  assert error is None
  assert normalized == config


def test_runtime_request_revalidates_hardware_version_and_size(tmp_path, monkeypatch):
  params = FakeParams({"enabled": True, "lateralModel": "lat", "longitudinalModel": "long"})
  (tmp_path / ".model_versions.json").write_text(json.dumps({"lat": "v15", "long": "v9"}))
  for model_id in ("lat", "long"):
    (tmp_path / f"{model_id}_driving_tinygrad.pkl").write_bytes(b"artifact")
  monkeypatch.setattr(modeld, "MODELS_PATH", tmp_path)
  monkeypatch.setattr(modeld, "load_model_artifact_metadata", lambda _model_id: {"model_size": "small"})
  monkeypatch.setattr(modeld, "model_accelerator_artifact_available", lambda _model_id: True)
  monkeypatch.setattr(modeld, "model_accelerator_artifact_installed", lambda _model_id: True)

  assert "Chestnut" in modeld._model_lab_runtime_request(params, chestnut_ready=False)[1]
  assert modeld._model_lab_runtime_request(params, chestnut_ready=True)[1] is None

  (tmp_path / ".model_versions.json").write_text(json.dumps({"lat": "v15", "long": "v7"}))
  assert "compatible small model" in modeld._model_lab_runtime_request(params, chestnut_ready=True)[1]

  (tmp_path / ".model_versions.json").write_text(json.dumps({"lat": "v15", "long": "v9"}))
  monkeypatch.setattr(
    modeld,
    "load_model_artifact_metadata",
    lambda model_id: {"model_size": "chestnut" if model_id == "long" else "small"},
  )
  assert "compatible small model" in modeld._model_lab_runtime_request(params, chestnut_ready=True)[1]


def test_model_lab_moves_driver_monitoring_off_external_gpu_runner_core():
  enabled = FakeParams({"enabled": True, "lateralModel": "lat", "longitudinalModel": "long"})
  disabled = FakeParams({"enabled": False, "lateralModel": "lat", "longitudinalModel": "long"})

  assert dmonitoringmodeld.dmonitoring_cpu_cores(enabled, chestnut_ready=True) == [0, 1, 2, 3]
  assert dmonitoringmodeld.dmonitoring_cpu_cores(enabled, chestnut_ready=False) == 7
  assert dmonitoringmodeld.dmonitoring_cpu_cores(disabled, chestnut_ready=True) == 7


def test_model_lab_loader_uses_installed_artifact_and_manifest_version(monkeypatch):
  calls = []

  def fake_model_state(cam_w, cam_h, external_gpu_active, **kwargs):
    calls.append((cam_w, cam_h, external_gpu_active, kwargs))
    return SimpleNamespace(model_id="lat", uses_external_gpu=True)

  monkeypatch.setattr(modeld, "ModelState", fake_model_state)
  monkeypatch.setattr(modeld, "model_accelerator_artifact_available", lambda _model_id: True)
  monkeypatch.setattr(modeld, "model_accelerator_artifact_installed", lambda _model_id: True)
  monkeypatch.setattr(modeld, "model_accelerator_artifact_path", lambda _model_id: modeld.Path("/models/lat-amd.pkl"))
  loaded = modeld._load_model_lab_model(1928, 1208, "lat", "v11")

  assert loaded.model_id == "lat"
  assert calls == [(1928, 1208, True, {
    "model_id_override": "lat",
    "write_model_version": False,
    "model_version_override": "v11",
    "model_path_override": modeld.Path("/models/lat-amd.pkl"),
    "force_external_gpu": True,
  })]


def test_model_lab_finite_output_guard_checks_both_models():
  assert modeld._model_outputs_finite({"plan": np.zeros(2)}, {"lead": np.ones(2)})
  assert not modeld._model_outputs_finite({"plan": np.array([np.nan])}, {"lead": np.ones(2)})


def test_model_lab_isolates_only_realized_buffer_uops(monkeypatch):
  buffer_key = (Ops.BUFFER, "serialized-model-buffer")
  shape_key = (Ops.RESHAPE, "shared-input-shape")
  buffer_value, shape_value = object(), object()
  monkeypatch.setattr(UOpMetaClass, "ucache", {buffer_key: buffer_value, shape_key: shape_value})

  assert modeld._isolate_next_model_artifact_load() == 1
  assert UOpMetaClass.ucache == {shape_key: shape_value}


def test_model_lab_loads_and_warms_both_amd_models_before_returning(monkeypatch):
  calls = []

  class FakeModel:
    def __init__(self, model_id):
      self.model_id = model_id
      self.image_history_pipeline = modeld.IMAGE_HISTORY_IN_POLICY
      self.warped_input_shape = (2, 6, 128, 256)
      self.WARP_DEV = "QCOM"

    def warmup(self):
      calls.append(("warmup", self.model_id))

  monkeypatch.setattr(modeld, "wait_for_external_gpu_power_ready", lambda CP: calls.append(("power", CP)))
  monkeypatch.setattr(modeld, "wait_usbgpu_link", lambda: calls.append("link"))
  monkeypatch.setattr(modeld, "_set_hcq_wait_timeout", lambda timeout: calls.append(("timeout", timeout)))
  monkeypatch.setattr(modeld, "_close_tinygrad_disk_cache_connection", lambda: calls.append("close_cache"))
  monkeypatch.setattr(
    modeld,
    "_isolate_next_model_artifact_load",
    lambda: calls.append("isolate_buffers") or 7,
  )
  monkeypatch.setattr(
    modeld,
    "_load_model_lab_model",
    lambda _w, _h, model_id, version: calls.append(("load", model_id, version)) or FakeModel(model_id),
  )

  pair = modeld._load_model_lab_models(1928, 1208, "lat", "long", "v15", "v9", "car-params")

  assert [model.model_id for model in pair] == ["lat", "long"]
  assert calls == [
    ("power", "car-params"),
    ("timeout", modeld.BIG_MODEL_LOAD_WAIT_TIMEOUT_MS),
    "link",
    "isolate_buffers",
    ("load", "lat", "v15"),
    ("warmup", "lat"),
    "isolate_buffers",
    ("load", "long", "v9"),
    ("warmup", "long"),
    "close_cache",
    ("timeout", modeld.BIG_MODEL_RUN_WAIT_TIMEOUT_MS),
  ]


def test_model_lab_requires_shareable_camera_preprocessing():
  compatible = SimpleNamespace(
    image_history_pipeline=modeld.IMAGE_HISTORY_IN_POLICY,
    warped_input_shape=(2, 6, 128, 256),
    WARP_DEV="QCOM",
  )
  legacy = SimpleNamespace(
    image_history_pipeline=modeld.IMAGE_HISTORY_IN_WARP,
    warped_input_shape=(2, 6, 128, 256),
    WARP_DEV="QCOM",
  )
  different_shape = SimpleNamespace(
    image_history_pipeline=modeld.IMAGE_HISTORY_IN_POLICY,
    warped_input_shape=(2, 6, 256, 512),
    WARP_DEV="QCOM",
  )

  assert modeld._model_lab_shared_warp_compatible(compatible, compatible)
  assert not modeld._model_lab_shared_warp_compatible(compatible, legacy)
  assert not modeld._model_lab_shared_warp_compatible(compatible, different_shape)


def test_model_state_reuses_shared_warp_without_preprocessing_again():
  shared_warp = object()
  policy_calls = []

  class FakeOutput:
    @staticmethod
    def numpy():
      return np.zeros(2, dtype=np.float32)

  state = modeld.ModelState.__new__(modeld.ModelState)
  state.image_history_pipeline = modeld.IMAGE_HISTORY_IN_POLICY
  state.desire_key = "desire"
  state.numpy_inputs = {"desire": np.zeros((1, modeld.ModelConstants.DESIRE_LEN), dtype=np.float32)}
  state.npy = {
    "desire": np.zeros(modeld.ModelConstants.DESIRE_LEN, dtype=np.float32),
    "tfm": np.zeros((3, 3), dtype=np.float32),
    "big_tfm": np.zeros((3, 3), dtype=np.float32),
  }
  state.prev_desire = np.zeros(modeld.ModelConstants.DESIRE_LEN, dtype=np.float32)
  state.prev_desired_curv_key = None
  state.road_key = "road"
  state.wide_key = "wide"
  state.input_queues = {"history": "longitudinal-history"}
  state.warp_input_keys = ()
  state.policy_input_keys = ("history",)
  state.warp_enqueue = lambda **_kwargs: (_ for _ in ()).throw(AssertionError("second warp must not run"))
  state.run_policy = lambda **kwargs: policy_calls.append(kwargs) or [FakeOutput()]
  state.uses_external_gpu = False
  state.model_type = "supercombo"
  state.parser = SimpleNamespace(parse_outputs=lambda _outputs: {"plan": np.zeros(1, dtype=np.float32)})
  state.output_slices = {"plan": slice(0, 1)}
  state.last_warp_output = None

  output = state.run(
    {},
    {"road": np.eye(3, dtype=np.float32), "wide": np.eye(3, dtype=np.float32)},
    {"desire": np.zeros(modeld.ModelConstants.DESIRE_LEN, dtype=np.float32)},
    False,
    shared_warp=shared_warp,
  )

  assert output is not None
  assert policy_calls == [{"history": "longitudinal-history", "warped": shared_warp}]
  assert state.last_warp_output is shared_warp


def test_each_runner_receives_its_own_input_names_and_shared_frame_data():
  model = SimpleNamespace(
    road_key="road",
    wide_key="wide",
    desire_key="desire_pulse",
    numpy_inputs={"action_t": object(), "prev_action": object(), "lateral_control_params": object()},
    off_policy_enabled=False,
    off_policy_numpy_inputs={},
  )
  previous_action = SimpleNamespace(desiredCurvature=0.25, desiredAcceleration=-0.5)
  road_buffer, wide_buffer = object(), object()
  road_transform = np.eye(3, dtype=np.float32)
  wide_transform = np.eye(3, dtype=np.float32) * 2
  desire = np.arange(8, dtype=np.float32)
  traffic = np.array([1, 0], dtype=np.float32)
  lateral_control = np.array([10.0, 0.2], dtype=np.float32)

  buffers, transforms, inputs = modeld._runner_frame_args(
    model,
    road_buffer,
    wide_buffer,
    road_transform,
    wide_transform,
    desire,
    traffic,
    0.3,
    0.6,
    previous_action,
    10.0,
    lateral_control,
  )

  assert buffers == {"road": road_buffer, "wide": wide_buffer}
  np.testing.assert_array_equal(transforms["road"], road_transform)
  np.testing.assert_array_equal(transforms["wide"], wide_transform)
  np.testing.assert_array_equal(inputs["desire_pulse"], desire)
  np.testing.assert_allclose(inputs["action_t"], [0.3, 0.6])
  np.testing.assert_allclose(inputs["prev_action"], [25.0, -0.5])
  np.testing.assert_array_equal(inputs["lateral_control_params"], lateral_control)


def test_runtime_status_records_requested_pair_and_fallback_error():
  params = FakeParams({})
  config = {"lateralModel": "lat", "longitudinalModel": "long"}

  modeld._set_model_lab_runtime(
    params,
    requested=True,
    active=False,
    config=config,
    error="synthetic fallback",
  )

  assert params.values["ModelLabRuntime"] == {
    "requested": True,
    "active": False,
    "lateralModel": "lat",
    "longitudinalModel": "long",
    "schedule": "sequential_20hz",
    "executionDevice": "",
    "error": "synthetic fallback",
  }
