import json
import re
from pathlib import Path

import pytest

from openpilot.system.manager import prebuilt_guard as g

ROOT = Path(__file__).parents[3]


def test_parses_every_params_key():
  text = (ROOT / g.PARAMS_KEYS_H).read_text()
  entries = g.parse_params_keys(text)
  assert len(entries) == len(re.findall(r'^\s*\{"', text, re.MULTILINE))
  assert entries["TorqueInterceptorEnabled"] == {"flags": 0x02, "type": 1, "default": "1", "stock": "1"}
  assert entries["AccessToken"]["flags"] == 0x04 | 0x20 and entries["AccessToken"]["default"] is None
  assert entries["ThemesDownloaded"]["default"] == "{}"


def test_parses_quoted_braces_and_commas():
  text = 'keys = {\n  {"A", {PERSISTENT, JSON, "{\\"x\\": [1, 2]}", "}"}},\n  {"B", {CLEAR_ON_MANAGER_START, INT}},\n};'
  entries = g.parse_params_keys(text)
  assert entries["A"]["default"] == '{"x": [1, 2]}' and entries["A"]["stock"] == "}"
  assert entries["B"] == {"flags": 0x04, "type": 2, "default": None, "stock": None}


@pytest.fixture
def fw_tree(tmp_path):
  for rel in (*g.FW_SOURCE_FILES, "panda/board/main.c", "opendbc_repo/opendbc/safety/modes/honda.h",
              "opendbc_repo/opendbc/safety/tests/test_honda.py"):
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text(rel)
  for name in g.FW_TARGETS:
    g.fw_bin(name, tmp_path).parent.mkdir(parents=True, exist_ok=True)
    g.fw_bin(name, tmp_path).write_bytes(name.encode())
  return tmp_path


def test_stamp_roundtrip_and_detection(fw_tree):
  assert not g.check_panda(fw_tree)[0]  # no stamp
  stamp = g.write_stamp(basedir=fw_tree)
  assert set(stamp["bins"]) == set(g.FW_TARGETS)
  assert g.check_panda(fw_tree)[0]

  # tests and build outputs are not firmware sources
  (fw_tree / "opendbc_repo/opendbc/safety/tests/test_honda.py").write_text("changed")
  (fw_tree / "panda/board/obj/gitversion.h").write_text("changed")
  assert g.check_panda(fw_tree)[0]

  # a Dom "build" commit swaps the bins without touching sources
  g.fw_bin("panda_h7", fw_tree).write_bytes(b"dom build")
  ok, why = g.check_panda(fw_tree)
  assert not ok and "panda_h7" in why
  g.write_stamp(["panda_h7"], basedir=fw_tree)
  assert g.check_panda(fw_tree)[0]

  # a safety change without a rebuild
  (fw_tree / "opendbc_repo/opendbc/safety/modes/honda.h").write_text("0x249 changed")
  assert not g.check_panda(fw_tree)[0]


def test_failed_repair_is_not_retried_forever(tmp_path, monkeypatch):
  monkeypatch.setattr(g, "STATE_PATH", tmp_path / "state.json")
  monkeypatch.setattr(g, "LOG_PATH", tmp_path / "guard.log")
  monkeypatch.setattr(g, "check_params", lambda: (False, "stale"))
  monkeypatch.setattr(g, "check_panda", lambda: (True, "ok"))
  monkeypatch.setattr(g, "fingerprint", lambda: "fp")
  calls = []
  monkeypatch.setattr(g, "repair_params", lambda budget: calls.append(1) or False)

  assert [g.guard() for _ in range(4)] == [1, 1, 1, 1]
  assert len(calls) == g.MAX_FAILURES
  assert json.loads((tmp_path / "state.json").read_text()) == {"fp": g.MAX_FAILURES}


def test_clean_tree_does_nothing(tmp_path, monkeypatch):
  monkeypatch.setattr(g, "LOG_PATH", tmp_path / "guard.log")
  monkeypatch.setattr(g, "check_params", lambda: (True, "ok"))
  monkeypatch.setattr(g, "check_panda", lambda: (True, "ok"))
  monkeypatch.setattr(g, "repair_params", lambda budget: pytest.fail("repaired a clean tree"))
  monkeypatch.setattr(g, "repair_panda", lambda budget: pytest.fail("repaired a clean tree"))
  assert g.guard() == 0


def test_repair_restores_previous_binaries_on_failure(tmp_path, monkeypatch):
  base = tmp_path / "tree"
  for rel in g.PARAMS_OUTPUTS:
    (base / rel).parent.mkdir(parents=True, exist_ok=True)
    (base / rel).write_text(f"old {rel}")
  monkeypatch.setattr(g, "BASEDIR", base)
  monkeypatch.setattr(g, "BACKUP_DIR", tmp_path / "backup")
  monkeypatch.setattr(g, "LOG_PATH", tmp_path / "guard.log")
  monkeypatch.setattr(g, "run_scons", lambda targets, budget: False)
  assert not g.repair_params(g.Budget(10))
  assert all((base / rel).read_text() == f"old {rel}" for rel in g.PARAMS_OUTPUTS)
  assert not (tmp_path / "backup").exists()


def test_launch_runs_guard_before_manager_on_prebuilt_tici():
  script = (ROOT / "launch_chffrplus.sh").read_text()
  pattern = (r'if \[ -f "\$DIR/prebuilt" \] && \[ -f /TICI \]; then\s+sp_launch_timing "prebuilt_guard_start"\s+' +
             r'python3 \./prebuilt_guard\.py \|\|')
  hook = re.search(pattern, script)
  assert hook
  assert hook.start() < script.index('sp_launch_timing "manager_start"')


def test_stamp_file_is_consistent_when_present():
  if not (ROOT / g.PANDA_STAMP).exists():
    pytest.skip("no stamp committed yet")
  stamp = json.loads((ROOT / g.PANDA_STAMP).read_text())
  assert stamp["sources_sha256"] == g.fw_source_hash(ROOT), "firmware sources changed: rebuild panda/board/obj on device"
  for name in g.FW_TARGETS:
    assert stamp["bins"][name] == g.sha256_file(g.fw_bin(name, ROOT)), f"{name} differs from its stamp"

