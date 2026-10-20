#!/usr/bin/env python3
"""Pre-manager guard for trees launched with the `prebuilt` marker (TICI only).

With `prebuilt`, launch never runs SCons, so the device runs whatever binaries git
tracks. Merges from StarPilot Dom (and every `updated` hard reset) restore Dom's
builds, which lack this fork's params keys and the panda 0x249 allow-list:
TorqueInterceptorEnabled silently reads False (and manager_init's clear_all deletes
its file), and pandad flashes firmware that blocks the TI.

Checks, both fast when nothing is wrong:
  params: every key in common/params_keys.h must resolve in the compiled table
          (check_key, never get()) with the same flags/type/default/stock value,
          and the table must hold no extra keys.
  panda:  panda/board/obj/fork_fw_stamp.json records a hash of the firmware sources
          and the sha256 of each app bin built from them. Both must match the tree.

On a failure it rebuilds only the affected targets (SCons -j2, then -j1, with
--cache-disable and the venv on PATH), verifies the result, and restores the
previous binaries if the rebuild fails. Runs once per boot, bounded by a time
budget; a fingerprint that already failed twice is not retried.

  prebuilt_guard.py               check and repair (launch_chffrplus.sh)
  prebuilt_guard.py --check       check only, exit 1 on a problem
  prebuilt_guard.py --write-stamp record the current firmware sources + bins
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

BASEDIR = Path(__file__).resolve().parents[2]
PARAMS_KEYS_H = "common/params_keys.h"
PANDA_OBJ = "panda/board/obj"
PANDA_STAMP = f"{PANDA_OBJ}/fork_fw_stamp.json"

# Everything that goes into the panda app firmware (see panda/SConscript).
FW_SOURCE_DIRS = ("panda/board", "panda/crypto", "panda/certs", "opendbc_repo/opendbc/safety")
FW_SOURCE_FILES = ("panda/SConscript",)
FW_SOURCE_SUFFIXES = (".c", ".h", ".s", ".ld", ".py", ".pub")
FW_SOURCE_EXCLUDE = ("panda/board/obj", "opendbc_repo/opendbc/safety/tests")

# App images pandad can flash on a comma three / 3X (STM32H7 internal panda).
FW_TARGETS = (
  "panda_h7", "panda_h7_remote", "panda_h7_hkg_remote", "panda_h7_can_ignition_only",
  "panda_h7_remote_can_ignition_only", "panda_h7_hkg_remote_can_ignition_only",
  "panda_h7_tesla_wake", "panda_h7_tesla_wake_can_ignition_only",
)

PARAMS_OUTPUTS = ("common/libcommon.a", "common/params.o", "common/params_pyx.so", "common/params_pyx.cpp")

# common/params.h
KEY_FLAGS = {"PERSISTENT": 0x02, "CLEAR_ON_MANAGER_START": 0x04, "CLEAR_ON_ONROAD_TRANSITION": 0x08,
             "CLEAR_ON_OFFROAD_TRANSITION": 0x10, "DONT_LOG": 0x20, "DEVELOPMENT_ONLY": 0x40,
             "CLEAR_ON_IGNITION_ON": 0x80}
KEY_TYPES = {"STRING": 0, "BOOL": 1, "INT": 2, "FLOAT": 3, "TIME": 4, "JSON": 5, "BYTES": 6}

DATA = Path("/data") if Path("/data").is_dir() else Path("/tmp")
LOG_PATH = Path(os.getenv("SP_PREBUILT_GUARD_LOG", DATA / "prebuilt_guard.log"))
STATE_PATH = Path(os.getenv("SP_PREBUILT_GUARD_STATE", DATA / "prebuilt_guard_state.json"))
BACKUP_DIR = Path(os.getenv("SP_PREBUILT_GUARD_BACKUP", DATA / "prebuilt_guard_backup"))
BUDGET_S = float(os.getenv("SP_PREBUILT_GUARD_BUDGET", "2400"))
JOBS = (2, 1)
MAX_FAILURES = 2
LOG_KEEP_LINES = 400


def log(msg: str) -> None:
  line = f"{datetime.datetime.now().isoformat(timespec='seconds')} prebuilt_guard: {msg}"
  print(line, flush=True)
  try:
    with open(LOG_PATH, "a") as f:
      f.write(line + "\n")
  except OSError:
    pass


def trim_log() -> None:
  try:
    lines = LOG_PATH.read_text().splitlines()
    if len(lines) > LOG_KEEP_LINES:
      LOG_PATH.write_text("\n".join(lines[-LOG_KEEP_LINES:]) + "\n")
  except OSError:
    pass


def sha256_file(path: Path) -> str | None:
  try:
    return hashlib.sha256(path.read_bytes()).hexdigest()
  except OSError:
    return None


# ---------------------------------------------------------------- params

def _split_fields(body: str) -> list[str]:
  fields, cur, quoted, escaped = [], [], False, False
  for ch in body:
    if quoted:
      cur.append(ch)
      if escaped:
        escaped = False
      elif ch == "\\":
        escaped = True
      elif ch == '"':
        quoted = False
    elif ch == '"':
      quoted = True
      cur.append(ch)
    elif ch == ",":
      fields.append("".join(cur).strip())
      cur = []
    else:
      cur.append(ch)
  if "".join(cur).strip():
    fields.append("".join(cur).strip())
  return fields


UNKNOWN = object()  # a C++ expression (e.g. std::to_string(...)); not compared


def _c_string(field: str):
  if field in ("", "std::nullopt"):
    return None
  if not (field.startswith('"') and field.endswith('"')):
    return UNKNOWN
  return field[1:-1].encode().decode("unicode_escape")


def parse_params_keys(text: str) -> dict[str, dict]:
  """Parse the `{"Key", {FLAGS, TYPE, "default", "stock", level, TIER}},` table."""
  entries: dict[str, dict] = {}
  i = text.index("keys = {")
  while True:
    start = text.find('{"', i)
    if start < 0:
      break
    name_end = text.index('"', start + 2)
    name = text[start + 2:name_end]
    open_brace = text.index("{", name_end)
    # scan to the closing brace, ignoring braces inside string literals
    j, quoted, escaped = open_brace + 1, False, False
    while True:
      ch = text[j]
      if quoted:
        if escaped:
          escaped = False
        elif ch == "\\":
          escaped = True
        elif ch == '"':
          quoted = False
      elif ch == '"':
        quoted = True
      elif ch == "}":
        break
      j += 1
    fields = _split_fields(text[open_brace + 1:j])
    flags = 0
    for flag in fields[0].split("|"):
      flags |= KEY_FLAGS[flag.strip()]
    default = _c_string(fields[2]) if len(fields) > 2 else None
    stock = _c_string(fields[3]) if len(fields) > 3 else None
    entries[name] = {"flags": flags, "type": KEY_TYPES[fields[1].strip()], "default": default,
                     "stock": stock if stock is not None else default}
    i = j
  return entries


def _params_report_main() -> int:
  """Runs in a child process so a rebuilt params_pyx.so is loaded fresh."""
  from openpilot.common.params_pyx import Params, UnknownKeyName  # the raw table, not the Dom wrapper

  source = parse_params_keys((BASEDIR / PARAMS_KEYS_H).read_text())
  params = Params()
  problems: list[str] = []

  def as_python(key, value):
    if value is None:
      return None
    try:
      return params.cpp2python(key, value.encode())
    except Exception as e:
      return f"<unconvertible: {type(e).__name__}>"

  for key, attrs in source.items():
    try:
      params.check_key(key)
    except UnknownKeyName:
      problems.append(f"missing key {key}")
      continue
    if int(params.get_key_flag(key)) != attrs["flags"]:
      problems.append(f"{key}: flags {int(params.get_key_flag(key)):#x} != {attrs['flags']:#x}")
    if int(params.get_type(key)) != attrs["type"]:
      problems.append(f"{key}: type {int(params.get_type(key))} != {attrs['type']}")
    for field, getter in (("default", params.get_default_value), ("stock", params.get_stock_value)):
      if attrs[field] is not UNKNOWN and getter(key) != as_python(key, attrs[field]):
        problems.append(f"{key}: {field} {getter(key)!r} != {attrs[field]!r}")

  compiled = {k.decode() if isinstance(k, bytes) else k for k in params.all_keys()}
  problems += [f"extra key {k}" for k in sorted(compiled - set(source))]
  print(json.dumps({"keys": len(source), "compiled": len(compiled), "problems": problems}))
  return 0


def check_params() -> tuple[bool, str]:
  env = dict(os.environ, PYTHONPATH=f"{BASEDIR}:{BASEDIR}/starpilot/third_party")
  try:
    out = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--params-report"], cwd=BASEDIR, env=env,
                         capture_output=True, text=True, timeout=120)
  except subprocess.TimeoutExpired:
    return False, "params report timed out"
  if out.returncode != 0:
    tail = (out.stderr or out.stdout).strip().splitlines()[-1:] or ["no output"]
    return False, f"params_pyx unusable: {tail[0]}"
  report = json.loads(out.stdout.strip().splitlines()[-1])
  problems = report["problems"]
  if problems:
    shown = "; ".join(problems[:8]) + (f"; ... {len(problems) - 8} more" if len(problems) > 8 else "")
    return False, f"{len(problems)} params table mismatches: {shown}"
  return True, f"{report['keys']} keys match the compiled table"


# ---------------------------------------------------------------- panda

def fw_source_files(basedir: Path = BASEDIR) -> list[Path]:
  files = [basedir / f for f in FW_SOURCE_FILES]
  for d in FW_SOURCE_DIRS:
    for p in (basedir / d).rglob("*"):
      rel = p.relative_to(basedir).as_posix()
      if not p.is_file() or "__pycache__" in rel or rel.startswith(FW_SOURCE_EXCLUDE):
        continue
      if p.suffix in FW_SOURCE_SUFFIXES:
        files.append(p)
  return sorted(set(files))


def fw_source_hash(basedir: Path = BASEDIR) -> str:
  h = hashlib.sha256()
  for p in fw_source_files(basedir):
    h.update(p.relative_to(basedir).as_posix().encode() + b"\0")
    h.update(p.read_bytes() + b"\0")
  return h.hexdigest()


def fw_bin(name: str, basedir: Path = BASEDIR) -> Path:
  return basedir / PANDA_OBJ / f"{name}.bin.signed"


def read_stamp(basedir: Path = BASEDIR) -> dict:
  try:
    return json.loads((basedir / PANDA_STAMP).read_text())
  except (OSError, ValueError):
    return {}


def write_stamp(names=None, basedir: Path = BASEDIR) -> dict:
  """Record the current source hash and bin hashes (all app bins, or just `names`)."""
  stamp = read_stamp(basedir) if names is not None else {}
  bins = stamp.get("bins", {})
  if names is None:
    names = sorted(p.name[:-len(".bin.signed")] for p in (basedir / PANDA_OBJ).glob("*.bin.signed"))
  for name in names:
    bins[name] = sha256_file(fw_bin(name, basedir))
  stamp = {"sources_sha256": fw_source_hash(basedir), "bins": dict(sorted(bins.items())),
           "note": "system/manager/prebuilt_guard.py; regenerate with --write-stamp after rebuilding panda/board/obj"}
  (basedir / PANDA_STAMP).write_text(json.dumps(stamp, indent=2) + "\n")
  return stamp


def check_panda(basedir: Path = BASEDIR) -> tuple[bool, str]:
  stamp = read_stamp(basedir)
  if not stamp:
    return False, f"no stamp at {PANDA_STAMP}"
  if stamp.get("sources_sha256") != fw_source_hash(basedir):
    return False, "firmware sources changed since the tracked bins were built"
  stale = [n for n in FW_TARGETS if stamp.get("bins", {}).get(n) is None or
           stamp["bins"][n] != sha256_file(fw_bin(n, basedir))]
  if stale:
    return False, f"bins differ from the stamp: {', '.join(stale)}"
  return True, "firmware bins match their sources"


# ---------------------------------------------------------------- rebuild

class Budget:
  def __init__(self, seconds: float):
    self.deadline = time.monotonic() + seconds

  def left(self) -> float:
    return self.deadline - time.monotonic()


def run_scons(targets: list[str], budget: Budget) -> bool:
  env = dict(os.environ)
  env["PATH"] = "/usr/local/venv/bin:" + env.get("PATH", "")  # cythonize and scons live in the venv
  env["PYTHONPATH"] = f"{BASEDIR}:{BASEDIR}/opendbc_repo"
  for jobs in JOBS:
    if budget.left() < 60:
      log(f"time budget exhausted before -j{jobs}")
      return False
    cmd = [sys.executable, "-m", "SCons", "--cache-disable", f"-j{jobs}", *targets]
    log(f"running: {' '.join(cmd[1:])} (budget {int(budget.left())}s)")
    t0 = time.monotonic()
    out_path = LOG_PATH.with_suffix(".scons.log")
    with open(out_path, "w") as out:
      proc = subprocess.Popen(cmd, cwd=BASEDIR, env=env, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
      try:
        rc = proc.wait(timeout=budget.left())
      except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        log(f"-j{jobs} timed out after {int(time.monotonic() - t0)}s")
        return False
    tail = out_path.read_text(errors="replace").strip().splitlines()[-3:]
    log(f"-j{jobs} exit {rc} after {int(time.monotonic() - t0)}s: {' | '.join(tail)}")
    if rc == 0:
      return True
  return False


def backup(paths: list[str]) -> None:
  shutil.rmtree(BACKUP_DIR, ignore_errors=True)
  for rel in paths:
    src = BASEDIR / rel
    if src.is_file():
      dst = BACKUP_DIR / rel
      dst.parent.mkdir(parents=True, exist_ok=True)
      shutil.copy2(src, dst)


def restore(paths: list[str]) -> None:
  for rel in paths:
    src = BACKUP_DIR / rel
    if src.is_file():
      shutil.copy2(src, BASEDIR / rel)
  log(f"restored previous {', '.join(paths)}")


def remove(paths: list[str]) -> None:
  for rel in paths:
    (BASEDIR / rel).unlink(missing_ok=True)


def repair_params(budget: Budget) -> bool:
  backup(list(PARAMS_OUTPUTS))
  remove(list(PARAMS_OUTPUTS))  # SCons hashes content; stale archives must go
  ok = run_scons(["common/params_pyx.so"], budget) and check_params()[0]
  if not ok:
    restore(list(PARAMS_OUTPUTS))
  shutil.rmtree(BACKUP_DIR, ignore_errors=True)
  return ok


def repair_panda(budget: Budget) -> bool:
  outputs = [f"{PANDA_OBJ}/{n}.bin.signed" for n in FW_TARGETS]
  intermediates = [f"{PANDA_OBJ}/{n}/{f}" for n in FW_TARGETS for f in ("main.elf", "main.bin")]
  backup(outputs + intermediates)
  remove(outputs + intermediates)  # tracked files git may have swapped under SCons
  ok = run_scons(outputs, budget) and all(fw_bin(n).is_file() and fw_bin(n).stat().st_size > 0 for n in FW_TARGETS)
  if ok:
    write_stamp(FW_TARGETS)
    ok = check_panda()[0]
  if not ok:
    restore(outputs + intermediates)
  shutil.rmtree(BACKUP_DIR, ignore_errors=True)
  return ok


def fingerprint() -> str:
  h = hashlib.sha256()
  for rel in (PARAMS_KEYS_H, "common/libcommon.a", "common/params_pyx.so", PANDA_STAMP,
              *(f"{PANDA_OBJ}/{n}.bin.signed" for n in FW_TARGETS)):
    h.update(f"{rel}={sha256_file(BASEDIR / rel)}\n".encode())
  h.update(fw_source_hash().encode())
  return h.hexdigest()[:16]


def load_state() -> dict:
  try:
    return json.loads(STATE_PATH.read_text())
  except (OSError, ValueError):
    return {}


def guard() -> int:
  trim_log()
  t0 = time.monotonic()
  checks = {"params": check_params(), "panda": check_panda()}
  for name, (ok, why) in checks.items():
    log(f"{name}: {'ok' if ok else 'STALE'} ({why})")
  if all(ok for ok, _ in checks.values()):
    log(f"all checks passed in {time.monotonic() - t0:.1f}s")
    return 0

  fp = fingerprint()
  state = load_state()
  failures = state.get(fp, 0)
  if failures >= MAX_FAILURES:
    log(f"rebuild already failed {failures}x for tree {fp}; not retrying. Fix by hand (see REBASE_NOTES.md).")
    return 1

  budget = Budget(BUDGET_S)
  ok = True
  if not checks["params"][0]:
    ok &= repair_params(budget)
    log(f"params rebuild {'OK' if ok else 'FAILED'}: {check_params()[1]}")
  if not checks["panda"][0]:
    panda_ok = repair_panda(budget)
    ok &= panda_ok
    log(f"panda firmware rebuild {'OK (pandad will flash it on start)' if panda_ok else 'FAILED'}: {check_panda()[1]}")

  if ok:
    state.pop(fp, None)
  else:
    state[fp] = failures + 1
  try:
    STATE_PATH.write_text(json.dumps(state))
  except OSError:
    pass
  log(f"done in {int(time.monotonic() - t0)}s, {'repaired' if ok else 'NOT repaired'}")
  return 0 if ok else 1


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("--check", action="store_true", help="check only; exit 1 on a problem")
  parser.add_argument("--write-stamp", action="store_true", help="record current firmware sources + bins")
  parser.add_argument("--params-report", action="store_true", help=argparse.SUPPRESS)
  args = parser.parse_args()

  if args.params_report:
    return _params_report_main()
  if args.write_stamp:
    print(json.dumps(write_stamp(), indent=2))
    return 0
  if args.check:
    results = [("params", *check_params()), ("panda", *check_panda())]
    for name, ok, why in results:
      print(f"{name}: {'ok' if ok else 'STALE'} ({why})")
    return 0 if all(ok for _, ok, _ in results) else 1
  return guard()


if __name__ == "__main__":
  sys.exit(main())
