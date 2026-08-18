import pytest

from openpilot.selfdrive.modeld import modeld


class FakeParams:
  def __init__(self):
    self.values = {}

  def put(self, key, value):
    self.values[key] = value


def test_incompatible_downloaded_model_falls_back_to_builtin(monkeypatch):
  calls = []
  builtin_model = object()

  def load_model(cam_w, cam_h, external_gpu_active):
    calls.append((cam_w, cam_h, external_gpu_active))
    if len(calls) == 1:
      raise TypeError("incompatible artifact")
    return builtin_model

  params = FakeParams()
  monkeypatch.setattr(modeld, "ModelState", load_model)
  monkeypatch.setattr(modeld.cloudlog, "exception", lambda *_args, **_kwargs: None)

  assert modeld._load_model_state(1928, 1208, "custom-model", False, params) is builtin_model
  assert calls == [(1928, 1208, False), (1928, 1208, False)]
  assert params.values == {
    "Model": modeld.BUILTIN_MODEL_KEY,
    "DrivingModel": modeld.BUILTIN_MODEL_KEY,
    "DrivingModelName": "Regret Driven Framework V4",
  }


def test_builtin_model_load_failure_is_not_hidden(monkeypatch):
  monkeypatch.setattr(modeld, "ModelState", lambda *_args: (_ for _ in ()).throw(TypeError("bad builtin")))

  with pytest.raises(TypeError, match="bad builtin"):
    modeld._load_model_state(1928, 1208, modeld.BUILTIN_MODEL_KEY, False, FakeParams())
