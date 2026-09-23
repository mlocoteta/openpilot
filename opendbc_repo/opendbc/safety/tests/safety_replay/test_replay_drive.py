import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def replay_module(monkeypatch):
  # Load the sibling source explicitly, without native safety libraries or a
  # host-runtime snapshot. These tests isolate replay accounting, not CAN rules.
  monkeypatch.setitem(sys.modules, "opendbc.car.carlog", SimpleNamespace(carlog=Mock()))
  monkeypatch.setitem(sys.modules, "opendbc.safety.tests.libsafety", SimpleNamespace(libsafety_py=SimpleNamespace()))
  monkeypatch.setitem(sys.modules, "opendbc.safety.tests.safety_replay.helpers",
                      SimpleNamespace(package_can_msg=lambda msg: msg, init_segment=Mock()))
  spec = importlib.util.spec_from_file_location("replay_drive_accounting", Path(__file__).with_name("replay_drive.py"))
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  module.tqdm = lambda msgs: msgs
  return module


@pytest.mark.parametrize("controls,aol,accepted,post_controls,post_aol", [
  (False, True, False, False, True),   # AOL-only denial must fail replay.
  (False, True, False, False, False),  # A TX hook can revoke AOL permission.
  (True, False, False, False, False),  # A TX hook can revoke controls permission.
  (False, False, False, False, False),  # Expected inactive blocks remain allowed.
  (False, False, False, True, True),  # Post-hook permission must not misclassify a block.
  (False, True, True, False, True),
  (True, False, True, True, False),
  (True, True, True, True, True),      # Count overlapping permissions only once.
])
def test_tx_authorization_accounted_before_hook(replay_module, capsys, controls, aol, accepted, post_controls, post_aol):
  state = SimpleNamespace(controls=controls, aol=aol)

  def tx_hook(msg):
    state.controls = post_controls
    state.aol = post_aol
    return accepted

  safety = Mock()
  safety.set_safety_hooks.return_value = 0
  safety.get_controls_allowed.side_effect = lambda: state.controls
  safety.get_aol_allowed.side_effect = lambda: state.aol
  safety.safety_tx_hook.side_effect = tx_hook
  replay_module.libsafety_py.libsafety = safety
  packet = SimpleNamespace(address=0x488, src=0, dat=b"\x00" * 4)
  msg = SimpleNamespace(logMonoTime=0, sendcan=[packet], which=lambda: "sendcan")

  result = replay_module.replay_drive([msg], 10, 0, 0)

  lateral_allowed = controls or aol
  assert result == (accepted or not lateral_allowed)
  safety.safety_tx_hook.assert_called_once_with(packet)
  output = capsys.readouterr().out
  assert "total openpilot msgs: 1\n" in output
  assert f"total msgs with controls allowed: {int(controls)}\n" in output
  assert f"blocked msgs: {int(not accepted)}\n" in output
  assert f"blocked with controls allowed: {int(controls and not accepted)}\n" in output
  assert f"total msgs with lateral allowed: {int(lateral_allowed)}\n" in output
  assert f"blocked with lateral allowed: {int(lateral_allowed and not accepted)}\n" in output
