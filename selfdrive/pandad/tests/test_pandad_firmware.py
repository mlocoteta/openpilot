import importlib.util
from pathlib import Path
import re
import subprocess

import pytest


PANDAD_PATH = Path(__file__).resolve().parents[1] / "pandad.py"
SPEC = importlib.util.spec_from_file_location("pandad_under_test", PANDAD_PATH)
assert SPEC is not None and SPEC.loader is not None
PANDAD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PANDAD)

REPO_ROOT = PANDAD_PATH.parents[2]
PANDA_H7_FIRMWARE = REPO_ROOT / "panda/board/obj/panda_h7.bin.signed"
PANDA_FIRMWARE_SOURCE_PREFIXES = (
  "opendbc_repo/opendbc/safety/",
  "panda/board/",
  "panda/crypto/",
  "panda/drivers/",
)
PANDA_FIRMWARE_SOURCE_EXCLUSIONS = (
  "opendbc_repo/opendbc/safety/tests/",
  "panda/board/obj/",
)


class FakeParams:
  def __init__(self, ignore_ignition_line):
    self.ignore_ignition_line = ignore_ignition_line

  def get_bool(self, key):
    assert key == "IgnoreIgnitionLine"
    return self.ignore_ignition_line


@pytest.mark.parametrize(("enabled", "expected"), [
  (True, True),
  (False, False),
])
def test_ignore_ignition_line_follows_toggle(enabled, expected):
  assert PANDAD.get_ignore_ignition_line(FakeParams(enabled)) == expected


def test_tracked_panda_firmware_includes_current_safety_sources():
  version_match = re.search(rb"DEV-([0-9a-f]{8})-DEBUG", PANDA_H7_FIRMWARE.read_bytes())
  assert version_match is not None
  firmware_commit = version_match.group(1).decode()

  try:
    changed_files = subprocess.check_output(
      ["git", "diff", "--name-only", f"{firmware_commit}..HEAD", "--", *PANDA_FIRMWARE_SOURCE_PREFIXES],
      cwd=REPO_ROOT,
      text=True,
    ).splitlines()
    changed_files += subprocess.check_output(
      ["git", "diff", "--name-only", "HEAD", "--", *PANDA_FIRMWARE_SOURCE_PREFIXES],
      cwd=REPO_ROOT,
      text=True,
    ).splitlines()
  except subprocess.CalledProcessError:
    pytest.skip("firmware source commit is unavailable in this checkout")

  stale_sources = sorted({path for path in changed_files if not path.startswith(PANDA_FIRMWARE_SOURCE_EXCLUSIONS)})
  assert stale_sources == [], f"panda firmware must be rebuilt after changing: {stale_sources}"
