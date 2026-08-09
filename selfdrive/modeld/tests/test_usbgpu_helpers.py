import io
from types import SimpleNamespace

import numpy as np

from openpilot.selfdrive.modeld.helpers import dump_oob, load_oob, tinygrad_dev_config
from scripts import model_compiler


def test_external_gpu_keeps_the_native_device_available():
  assert tinygrad_dev_config(True, tici=True) == "QCOM;USB+AMD:LLVM"
  assert tinygrad_dev_config(False, tici=True) == "QCOM"
  assert tinygrad_dev_config(True, tici=False) == "CPU:LLVM;USB+AMD:LLVM"


def test_out_of_band_artifact_round_trip():
  artifact = {"weights": np.arange(32, dtype=np.float32), "metadata": {"version": 1}}
  stream = io.BytesIO()
  dump_oob(artifact, stream)
  stream.seek(0)

  restored = load_oob(stream)
  assert restored["metadata"] == artifact["metadata"]
  np.testing.assert_array_equal(restored["weights"], artifact["weights"])


def test_external_gpu_probe_retries_until_pcie_is_ready(monkeypatch):
  results = [SimpleNamespace(returncode=1, stdout="", stderr="LTSSM=0x00"),
             SimpleNamespace(returncode=0, stdout="", stderr="")]
  calls = []
  monkeypatch.setattr(
    model_compiler.subprocess,
    "run",
    lambda *args, **kwargs: calls.append((args, kwargs)) or results.pop(0),
  )
  monkeypatch.setattr(model_compiler.time, "sleep", lambda seconds: calls.append(("sleep", seconds)))

  model_compiler.wait_for_external_gpu({"PYTHONPATH": "/tmp/openpilot"})

  assert len(calls) == 3
  assert calls[0][1]["env"]["DEV"] == "USB+AMD"
  assert calls[1] == ("sleep", 1)


def test_external_gpu_probe_reports_failure(monkeypatch):
  result = SimpleNamespace(returncode=1, stdout="", stderr="link unavailable")
  monkeypatch.setattr(model_compiler.subprocess, "run", lambda *args, **kwargs: result)
  monkeypatch.setattr(model_compiler.time, "sleep", lambda _: None)

  try:
    model_compiler.wait_for_external_gpu({})
  except RuntimeError as error:
    assert "link unavailable" in str(error)
  else:
    raise AssertionError("external GPU probe unexpectedly succeeded")
