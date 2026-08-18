import io

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


def test_external_gpu_probe_matches_upstream_retry_loop(monkeypatch):
  from openpilot.system.hardware.chestnut import flash

  calls = []
  results = iter((False, False, True))
  monkeypatch.setattr(flash, "link_up", lambda: calls.append("probe") or next(results))
  monkeypatch.setattr(model_compiler.time, "sleep", lambda seconds: calls.append(("sleep", seconds)))

  model_compiler.wait_for_external_gpu()

  assert calls == ["probe", ("sleep", 1), "probe", ("sleep", 1), "probe"]
