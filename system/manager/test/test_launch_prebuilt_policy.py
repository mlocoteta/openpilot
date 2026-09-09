from pathlib import Path
import re


LAUNCH_SCRIPT = Path(__file__).parents[3] / "launch_chffrplus.sh"


def test_prebuilt_marker_is_the_only_build_gate():
  script = LAUNCH_SCRIPT.read_text()

  assert "UsePrebuilt" not in script
  assert "prebuilt_runtime_compatible" not in script
  assert len(re.findall(r"\./build\.py", script)) == 1
  assert re.search(r'if \[ ! -f "\$DIR/prebuilt" \]; then\s+sp_launch_timing "build_start"\s+\./build\.py', script)
