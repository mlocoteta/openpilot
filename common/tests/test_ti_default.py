import re
from pathlib import Path

from openpilot.common.params import Params, ParamKeyFlag

KEY = "TorqueInterceptorEnabled"
ROOT = Path(__file__).resolve().parents[2]


def _params_keys_entry():
  src = (ROOT / "common" / "params_keys.h").read_text()
  m = re.search(r'\{"' + KEY + r'",\s*\{([^}]*)\}\}', src)
  assert m, f"{KEY} missing from params_keys.h"
  return [f.strip() for f in m.group(1).split(",")]


class TestTorqueInterceptorDefault:
  def test_source_entry_is_persistent_and_on(self):
    flags, ptype, default, stock, *_ = _params_keys_entry()
    assert flags == "PERSISTENT"  # no CLEAR_ON_* flags
    assert ptype == "BOOL"
    assert default == '"1"'
    assert stock == '"1"'

  def test_compiled_table_matches_source(self):
    params = Params()
    params.check_key(KEY)  # raises UnknownKeyName on a stale params_pyx.so/libcommon.a
    assert params.get_key_flag(KEY) == ParamKeyFlag.PERSISTENT
    assert params.get_default_value(KEY) in ("1", b"1", True)
    assert params.get_stock_value(KEY) in ("1", b"1", True)

  def test_missing_value_reads_on_with_defaults(self):
    params = Params()
    params.remove(KEY)
    assert Params(return_defaults=True).get_bool(KEY)

  def test_survives_clear_all(self):
    params = Params()
    params.put_bool(KEY, True)
    for flag in (ParamKeyFlag.CLEAR_ON_MANAGER_START, ParamKeyFlag.CLEAR_ON_ONROAD_TRANSITION,
                 ParamKeyFlag.CLEAR_ON_OFFROAD_TRANSITION, ParamKeyFlag.CLEAR_ON_IGNITION_ON,
                 ParamKeyFlag.DEVELOPMENT_ONLY):
      params.clear_all(flag)
    assert params.get_bool(KEY)

  def test_excluded_from_reset_sync_and_restore(self):
    from openpilot.starpilot.common.starpilot_variables import EXCLUDED_KEYS as STARPILOT_EXCLUDED_KEYS
    assert KEY in STARPILOT_EXCLUDED_KEYS  # device sync, toggle backups, param profiles
    src = (ROOT / "selfdrive/ui/layouts/settings/starpilot/system_settings.py").read_text()
    block = src.split("EXCLUDED_KEYS = {", 1)[1].split("}", 1)[0]
    assert f'"{KEY}"' in block  # "Reset toggles to defaults/stock" in the UI
