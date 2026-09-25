#!/usr/bin/env python3
"""Host-side analysis of a lateral characterization drive.

Inputs: the route's rlogs (a local directory, or pulled from the comma over ssh) and the JSON
sidecar written by lateral_maneuversd. The sidecar's mono_ns times are the rlog logMonoTime
clock, so every maneuver window is cut straight from the logs.

Per maneuver (completed attempts only):
  - actuation delay: cross-correlation of the TI 0x249 command vs measured lateral accel over
    0-800 ms (sign of the command/accel relation is taken from the correlation itself)
  - desired->actual delay by the same method
  - steps: rise (10-90 %), overshoot, settling (10 % band), steady-state error per transition
  - sines: gain and phase of actual vs desired at the commanded frequency
  - straight holds: ping-pong (0x249 sign flips/s, error sign flips/s) and the amplified noise
    sigma(des-act) * (1 + lsf(v)/Kp) against the logged friction threshold
  - every maneuver: tracking RMS, slew-cap fraction (|d cmd| >= 15 per frame), command vs
    request gap (request = carControl.actuators.torque * 599), road roll/pitch

Outputs report.md + report.json with recommendations for SteerDelay, the FLM 'standard'
friction-threshold table and TISteerKp, each with the evidence it came from.

  analyze.py --sidecar run.json --rlogs /path/to/route_dir --out out/
  analyze.py --route 0000012a--abcdef0123 --pull --out out/   # ssh to the comma

A plan driven over several drives (resume) gives one sidecar per route: pass them all
(--sidecar/--rlogs or --route are repeatable; one --rlogs dir may hold every route). Results
are merged per block id: a block's data comes from the newest run in which it completed (else
the newest run with any completed maneuver of it). Sidecars may come from different plan files
(e.g. a reduced plan, then the full one): a block is merged when its content (speed, settings,
maneuvers) matches the newest sidecar that has that block id; mismatching blocks are ignored and
listed in the report.
"""
import argparse
import json
import math
import os
import subprocess
from collections import defaultdict

import numpy as np

from openpilot.tools.lateral_maneuvers.characterization.plan import FRICTION_SPEED_KNOTS, FRICTION_TABLES, MPH_TO_MS

TI_ADDR = 0x249
TI_MAX = 599
SLEW_CAP = 15  # TI units per 10 ms frame (apply_ti_steer_torque_limits step)
FS = 100.0  # analysis grid, Hz
MAX_LAG_S = 0.8
MIN_CORR = 0.3
CMD_DEADBAND = 5  # TI units; smaller commands do not count as a sign flip
ERR_DEADBAND = 0.02  # m/s^2
KP_DEFAULT = 0.3  # controlsd TISteerKp fallback
LOW_SPEED_X = [0, 10, 20, 30]  # latcontrol_torque.LOW_SPEED_X/Y (fallback when lowSpeedFactor is not logged)
LOW_SPEED_Y = [12, 10.5, 8, 5]
THRESHOLD_MARGIN = 1.25  # recommended threshold = margin * amplified noise sigma
THRESHOLD_RANGE = (0.30, 2.0)

DEVICE = "comma@100.64.90.15"
SSH_KEY = os.path.expanduser("~/.ssh/openclaw_comma_ed25519")
DEVICE_REALDATA = "/data/media/0/realdata"
DEVICE_SIDECARS = "/data/media/0/lateral_characterization"


# ---------------------------------------------------------------------------
# extraction

def decode_ti(dat):
  return ((dat[0] & 0x0F) << 8 | dat[1]) - 2048


def extract_series(msgs):
  """rlog events -> {name: (t_s, values)} for every signal the analysis uses."""
  cols = defaultdict(lambda: ([], []))

  def add(name, t, v):
    cols[name][0].append(t)
    cols[name][1].append(v)

  for m in msgs:
    which = m.which()
    t = m.logMonoTime * 1e-9
    if which == "sendcan":
      for c in m.sendcan:
        if c.address == TI_ADDR and c.src == 0 and len(c.dat) >= 2:
          add("cmd", t, decode_ti(c.dat))
    elif which == "carControl":
      cc = m.carControl
      add("req", t, float(cc.actuators.torque) * TI_MAX)
      add("lat_active", t, float(cc.latActive))
      if len(cc.orientationNED) == 3:
        add("roll", t, float(cc.orientationNED[0]))
        add("pitch", t, float(cc.orientationNED[1]))
    elif which == "controlsState":
      lat = m.controlsState.lateralControlState
      if lat.which() == "torqueState":
        add("des", t, float(lat.torqueState.desiredLateralAccel))
        add("act", t, float(lat.torqueState.actualLateralAccel))
    elif which == "carState":
      add("v", t, float(m.carState.vEgo))
      add("pressed", t, float(m.carState.steeringPressed))
    elif which == "starpilotLateralState":
      sp = m.starpilotLateralState
      if sp.active:
        add("fric", t, float(sp.frictionThreshold))
        add("lsf", t, float(sp.lowSpeedFactor))
  out = {}
  for k, (t, v) in cols.items():
    t, v = np.asarray(t, float), np.asarray(v, float)
    order = np.argsort(t, kind="stable")
    out[k] = (t[order], v[order])
  return out


def _rlog_files(directory):
  files = []
  for root, _, names in os.walk(directory):
    for n in names:
      if n.startswith("rlog"):
        files.append(os.path.join(root, n))

  def seg(path):
    part = os.path.basename(os.path.dirname(path)).rsplit("--", 1)[-1]
    return (int(part) if part.isdigit() else 0, path)
  return sorted(files, key=seg)


def load_rlogs(directory, route=None):
  from openpilot.tools.lib.logreader import _LogFileReader
  files = _rlog_files(directory)
  if route:  # a directory holding several routes: only this route's segments (log clocks differ per boot)
    files = [f for f in files if os.path.basename(os.path.dirname(f)).startswith(f"{route}--")] or files
  if not files:
    raise SystemExit(f"no rlog files under {directory}")
  msgs = []
  for fn in files:
    msgs.extend(_LogFileReader(fn, only_union_types=True))
  return extract_series(msgs)


def pull_route(route, dest, host=DEVICE, key=SSH_KEY):
  """Copy <route>--*/rlog* and the sidecar(s) from the comma (read-only on the device)."""
  os.makedirs(dest, exist_ok=True)
  ssh = ["ssh", "-i", key, "-o", "BatchMode=yes", host]
  remote = f"cd {DEVICE_REALDATA} && tar cf - {route}--*/rlog*"
  with subprocess.Popen(ssh + [remote], stdout=subprocess.PIPE) as p:
    subprocess.run(["tar", "xf", "-", "-C", dest], stdin=p.stdout, check=True)
  sidecars = subprocess.run(ssh + [f"ls {DEVICE_SIDECARS}/{route}*.json"], capture_output=True, text=True).stdout.split()
  local = []
  for s in sidecars:
    path = os.path.join(dest, os.path.basename(s))
    subprocess.run(["scp", "-i", key, "-o", "BatchMode=yes", f"{host}:{s}", path], check=True)
    local.append(path)
  return local


# ---------------------------------------------------------------------------
# signal helpers

def window(series, name, t0, t1):
  if name not in series:
    return np.array([]), np.array([])
  t, v = series[name]
  sel = (t >= t0) & (t <= t1)
  return t[sel], v[sel]


def resample(series, name, grid):
  if name not in series or len(series[name][0]) < 2:
    return None
  t, v = series[name]
  if grid[0] < t[0] - 0.1 or grid[-1] > t[-1] + 0.1:
    return None
  return np.interp(grid, t, v)


def xcorr_curve(x, y, max_lag_s=MAX_LAG_S, fs=FS):
  """Pearson correlation of x[n] with y[n + lag] for lag = 0..max_lag (y lags x)."""
  lags = np.arange(0, int(round(max_lag_s * fs)) + 1)
  corr = np.full(len(lags), np.nan)
  x = np.asarray(x, float) - np.mean(x)
  y = np.asarray(y, float) - np.mean(y)
  for i, k in enumerate(lags):
    a, b = x[:len(x) - k], y[k:]
    if len(a) < fs:  # need at least 1 s of overlap
      break
    sa, sb = np.std(a), np.std(b)
    if sa > 1e-9 and sb > 1e-9:
      corr[i] = float(np.mean((a - a.mean()) * (b - b.mean())) / (sa * sb))
  return lags / fs, corr


def delay_from_curve(lags, corr, sign=None, min_corr=MIN_CORR):
  """Lag (s) of the correlation peak with the given sign (+1/-1, None = strongest |corr|)."""
  if corr is None or np.all(np.isnan(corr)):
    return None, None
  c = np.nan_to_num(corr, nan=0.0)
  score = np.abs(c) if sign is None else sign * c
  i = int(np.argmax(score))
  if score[i] < min_corr:
    return None, float(c[i])
  lag = lags[i]
  if 0 < i < len(c) - 1:  # parabolic refinement
    y0, y1, y2 = score[i - 1], score[i], score[i + 1]
    den = y0 - 2 * y1 + y2
    if abs(den) > 1e-12:
      lag += 0.5 * (y0 - y2) / den * (lags[1] - lags[0])
  return float(lag), float(c[i])


def sign_flips(values, deadband):
  s = np.sign(values[np.abs(values) >= deadband])
  return int(np.count_nonzero(s[1:] != s[:-1])) if len(s) > 1 else 0


def step_metrics(t, y, t_step, y_from, y_to, hold_s, pre=None):
  """Rise/overshoot/settling of y after a commanded step y_from -> y_to at t_step."""
  size = y_to - y_from
  if abs(size) < 1e-6:
    return None
  sel = (t >= t_step) & (t <= t_step + hold_s)
  if np.count_nonzero(sel) < 5:
    return None
  base = y_from if pre is None else pre
  tt, yn = t[sel] - t_step, (y[sel] - base) / (y_to - base if abs(y_to - base) > 1e-6 else size)
  i10, i90 = np.argmax(yn >= 0.1), np.argmax(yn >= 0.9)
  rise = float(tt[i90] - tt[i10]) if yn[i90] >= 0.9 and yn[i10] >= 0.1 else None
  t10 = float(tt[i10]) if yn[i10] >= 0.1 else None
  outside = np.nonzero(np.abs(yn - 1.0) > 0.1)[0]
  if len(outside) == 0:
    settle = 0.0
  elif outside[-1] < len(yn) - 1 and tt[-1] - tt[outside[-1] + 1] >= 0.2:
    settle = float(tt[outside[-1] + 1])
  else:
    settle = None  # never settled inside the hold
  tail = tt >= tt[-1] - 0.5
  return {"t": round(float(t_step), 3), "from": y_from, "to": y_to, "rise_s": rise, "t10_s": t10,
          "overshoot_pct": float(max(np.max(yn) - 1.0, 0.0) * 100), "settling_s": settle,
          "steady_state_error": float((np.mean(yn[tail]) - 1.0) * (y_to - base))}


def sine_fit(t, y, freq):
  """Least-squares amplitude and phase (rad) of y at freq (with offset + linear drift removed)."""
  w = 2 * math.pi * freq
  a = np.column_stack([np.sin(w * t), np.cos(w * t), np.ones_like(t), t - t.mean()])
  coef, *_ = np.linalg.lstsq(a, y, rcond=None)
  return float(math.hypot(coef[0], coef[1])), float(math.atan2(coef[1], coef[0]))


def low_speed_factor(v):
  return float((np.interp(v, LOW_SPEED_X, LOW_SPEED_Y) / max(v, 1.0)) ** 2)


def _mean(x):
  x = [v for v in x if v is not None and not (isinstance(v, float) and math.isnan(v))]
  return float(np.mean(x)) if x else None


def _median(x):
  x = [v for v in x if v is not None]
  return float(np.median(x)) if x else None


# ---------------------------------------------------------------------------
# sidecar -> maneuver windows

def maneuver_windows(sidecar):
  """Completed maneuver attempts: start/end events paired per block+maneuver."""
  out, open_ = [], {}
  for e in sidecar.get("events", []):
    key = (e.get("block"), e.get("maneuver"))
    if e["type"] == "maneuver_start":
      open_[key] = e
    elif e["type"] in ("maneuver_end", "maneuver_aborted") and key in open_:
      start = open_.pop(key)
      if e["type"] == "maneuver_end":
        out.append({"start": start, "t0": start["mono_ns"] * 1e-9, "t1": e["mono_ns"] * 1e-9})
  return out


def analyze_maneuver(series, win, sign=None):
  start = win["start"]
  spec, meta, settings = start["spec"], start.get("meta") or {}, start.get("settings") or {}
  t0, t1 = win["t0"], win["t1"]
  grid = np.arange(t0, t1, 1.0 / FS)
  res = {"block": start.get("block"), "maneuver": start.get("maneuver"), "desc": start.get("maneuver_desc", ""),
         "type": spec["type"], "speed_mph": start.get("speed_mph"), "tag": start.get("tag", ""),
         "settings": settings, "active_settings": start.get("active_settings") or {}, "t0": round(t0, 3),
         "duration_s": round(t1 - t0, 3), "road_start": {k: start.get(k) for k in ("roll", "pitch")}}
  des, act = resample(series, "des", grid), resample(series, "act", grid)
  cmd = resample(series, "cmd", grid)
  if des is None or act is None or len(grid) < 2:
    res["error"] = "no controlsState torqueState in window"
    return res

  err = des - act
  res["tracking_rms"] = float(np.sqrt(np.mean(err ** 2)))
  res["v_mean"] = float(np.mean(resample(series, "v", grid))) if resample(series, "v", grid) is not None else None
  for name in ("roll", "pitch"):
    _, r = window(series, name, t0, t1)
    res[f"{name}_mean"] = float(np.mean(r)) if len(r) else None

  if cmd is not None:
    lags, corr = xcorr_curve(cmd, act)
    res["_xcorr_cmd"] = (lags, corr)
    res["cmd_delay_s"], res["cmd_corr"] = delay_from_curve(lags, corr, sign)
    tc, raw = window(series, "cmd", t0, t1)
    d = np.abs(np.diff(raw))
    res["slew_cap_frac"] = float(np.mean(d >= SLEW_CAP)) if len(d) else None
    res["cmd_max_abs"] = float(np.max(np.abs(raw))) if len(raw) else None
    if "req" in series and len(tc):
      gap = np.interp(tc, *series["req"]) - raw
      res["req_gap_mean_abs"] = float(np.mean(np.abs(gap)))
      res["req_gap_rms"] = float(np.sqrt(np.mean(gap ** 2)))
      res["req_gap_frac_ge_cap"] = float(np.mean(np.abs(gap) >= SLEW_CAP))
  lags, corr = xcorr_curve(des, act)
  res["des_act_delay_s"], res["des_act_corr"] = delay_from_curve(lags, corr, +1)

  kind = spec["type"]
  if kind == "step":
    steps = []
    t_rel = grid - t0
    for tr in meta.get("transitions", []):
      pre_sel = (t_rel >= tr["t"] - 0.3) & (t_rel < tr["t"])
      pre = float(np.mean(act[pre_sel])) if np.any(pre_sel) else None
      base = float(np.mean(des[pre_sel])) - tr["from"] if np.any(pre_sel) else 0.0  # baseline curvature accel
      m = step_metrics(t_rel, act, tr["t"], tr["from"] + base, tr["to"] + base, tr["hold_s"], pre=pre)
      if m is not None:
        steps.append(m)
    res["steps"] = steps
    res["overshoot_pct"] = _mean([s["overshoot_pct"] for s in steps])
    res["rise_s"] = _mean([s["rise_s"] for s in steps])
    res["settling_s"] = _mean([s["settling_s"] for s in steps])
    res["unsettled_steps"] = sum(s["settling_s"] is None for s in steps)
  elif kind == "sine":
    freq = meta.get("freq_hz", spec.get("freq_hz"))
    fw = meta.get("fit_window") or [0.0, t1 - t0]
    sel = (grid - t0 >= fw[0]) & (grid - t0 <= fw[1])
    if np.count_nonzero(sel) > FS / freq / 2:
      ad, pd = sine_fit(grid[sel], des[sel], freq)
      aa, pa = sine_fit(grid[sel], act[sel], freq)
      phase = (pa - pd + math.pi) % (2 * math.pi) - math.pi
      res.update({"freq_hz": freq, "gain": aa / ad if ad > 1e-6 else None, "phase_deg": math.degrees(phase),
                  "phase_delay_s": -phase / (2 * math.pi * freq)})
  elif kind == "hold":
    dur = max(t1 - t0, 1e-3)
    if cmd is not None:
      _, raw = window(series, "cmd", t0, t1)
      res["cmd_flips_per_s"] = sign_flips(raw, CMD_DEADBAND) / dur
    res["err_flips_per_s"] = sign_flips(err, ERR_DEADBAND) / dur
    sigma = float(np.std(err))
    _, lsf = window(series, "lsf", t0, t1)
    lsf_v = float(np.mean(lsf)) if len(lsf) else low_speed_factor(res["v_mean"] or start.get("speed_mph", 0) * MPH_TO_MS)
    kp = (res["active_settings"] or {}).get("ti_steer_kp") or settings.get("ti_steer_kp") or KP_DEFAULT
    _, fric = window(series, "fric", t0, t1)
    res.update({"noise_sigma": sigma, "lsf": lsf_v, "kp": float(kp),
                "amplified_noise_sigma": sigma * (1 + lsf_v / float(kp)),
                "friction_threshold": float(np.mean(fric)) if len(fric) else None})
    if res["friction_threshold"]:
      res["noise_to_threshold"] = res["amplified_noise_sigma"] / res["friction_threshold"]
  return res


def block_signatures(sidecar):
  """{block id: content hash} from the sidecar's plan (position in the plan is ignored)."""
  import hashlib
  out = {}
  for block in (sidecar.get("plan") or {}).get("blocks", []):
    content = {k: v for k, v in block.items() if k != "index"}
    out[block["id"]] = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]
  return out


def completed_block_ids(sidecar):
  """Blocks whose maneuvers all completed in this run (block_complete events, else from the plan)."""
  events = sidecar.get("events", [])
  ids = {e.get("block") for e in events if e["type"] == "block_complete"}
  ended = {e.get("maneuver") for e in events if e["type"] == "maneuver_end"}
  for block in (sidecar.get("plan") or {}).get("blocks", []):
    if block.get("maneuvers") and all(m["id"] in ended for m in block["maneuvers"]):
      ids.add(block["id"])
  return ids


def _run_key(sidecar, order):
  return (sidecar.get("startedWall") or 0.0, order)


def analyze_run(series, sidecar):
  return analyze_runs([(series, sidecar)])


def analyze_runs(runs):
  """runs: [(series, sidecar)] of one plan, one entry per route/sidecar."""
  runs = sorted(enumerate(runs), key=lambda r: _run_key(r[1][1], r[0]))
  newest = runs[-1][1][1]
  # canonical content per block id: the newest sidecar that has the block
  canonical = {}
  for _, (_, sidecar) in reversed(runs):
    for block_id, sig in block_signatures(sidecar).items():
      canonical.setdefault(block_id, sig)

  # newest wins per block: prefer runs that completed the block, then any run with data for it
  per_block, ignored, used_orders = defaultdict(list), [], set()
  for order, (series, sidecar) in runs:
    complete = completed_block_ids(sidecar)
    sigs = block_signatures(sidecar)
    for w in maneuver_windows(sidecar):
      block_id = w["start"].get("block")
      if block_id in sigs and sigs[block_id] != canonical.get(block_id):
        if not any(i["route"] == sidecar.get("route") and i["block"] == block_id for i in ignored):
          ignored.append({"route": sidecar.get("route"), "block": block_id,
                          "reason": "block content differs from the newest plan with this block id"})
        continue
      used_orders.add(order)
      per_block[block_id].append((order, series, sidecar, w, block_id in complete))
  used = [(order, series, sidecar) for order, (series, sidecar) in runs if order in used_orders or sidecar is newest]
  chosen, results = {}, []
  for block, entries in per_block.items():
    best = max(entries, key=lambda e: (e[4], _run_key(e[2], e[0])))
    chosen[block] = best[2].get("route")
    for order, series, sidecar, w, _ in entries:
      if order == best[0]:
        res = analyze_maneuver(series, w)
        res["route"] = sidecar.get("route")
        results.append(res)
  # command->accel sign: consensus of the strongest correlations, then re-pick delays with it
  peaks = [r["cmd_corr"] for r in results if r.get("cmd_corr") is not None and abs(r["cmd_corr"]) >= MIN_CORR]
  sign = 1 if not peaks or sum(np.sign(peaks)) >= 0 else -1
  for r in results:
    if "_xcorr_cmd" in r:
      lags, corr = r.pop("_xcorr_cmd")
      r["cmd_delay_s"], r["cmd_corr"] = delay_from_curve(lags, corr, sign)
  incident_types = ("maneuver_aborted", "maneuver_skipped", "block_skipped", "paused", "settings_retry")
  report = {"route": newest.get("route"), "routes": [sc.get("route") for _, _, sc in used],
            "plan": (newest.get("plan") or {}).get("name"),
            "git": {"commit": newest.get("gitCommit"), "branch": newest.get("gitBranch")},
            "cmd_accel_sign": sign, "maneuvers": results, "block_sources": chosen, "ignored_blocks": ignored,
            "incidents": [{**e, "route": sc.get("route")} for _, _, sc in used for e in sc.get("events", [])
                          if e["type"] in incident_types],
            "run_end": next((e for e in reversed(newest.get("events", [])) if e["type"] == "run_end"), None)}
  report["blocks"] = summarize_blocks(results)
  report["recommendation"] = recommend(results)
  return report


# ---------------------------------------------------------------------------
# aggregation + recommendations

def _setting_value(settings, key):
  if key == "friction_table":
    return settings.get("friction_table_name") or json.dumps(settings.get("friction_table"))
  return settings.get(key)


def summarize_blocks(results):
  blocks = defaultdict(list)
  for r in results:
    blocks[(r["block"], r["speed_mph"], r["tag"])].append(r)
  out = []
  for (block, speed, tag), rs in blocks.items():
    def by(k, typ=None, rs=rs):
      return _mean([r.get(k) for r in rs if typ is None or r["type"] == typ])
    out.append({"block": block, "speed_mph": speed, "tag": tag, "maneuvers": len(rs),
                "cmd_delay_s": _median([r.get("cmd_delay_s") for r in rs]),
                "des_act_delay_s": _median([r.get("des_act_delay_s") for r in rs]),
                "tracking_rms": by("tracking_rms"), "tracking_rms_dynamic": _mean(
                  [r.get("tracking_rms") for r in rs if r["type"] in ("step", "sine")]),
                "overshoot_pct": by("overshoot_pct", "step"), "rise_s": by("rise_s", "step"),
                "settling_s": by("settling_s", "step"),
                "sine": {f"{r['freq_hz']:g}": {"gain": r.get("gain"), "phase_deg": r.get("phase_deg")}
                         for r in rs if r["type"] == "sine" and "freq_hz" in r},
                "cmd_flips_per_s": by("cmd_flips_per_s", "hold"), "err_flips_per_s": by("err_flips_per_s", "hold"),
                "amplified_noise_sigma": by("amplified_noise_sigma", "hold"),
                "friction_threshold": by("friction_threshold", "hold"),
                "slew_cap_frac": by("slew_cap_frac"), "req_gap_mean_abs": by("req_gap_mean_abs"),
                "roll_mean": by("roll_mean"), "pitch_mean": by("pitch_mean")})
  return sorted(out, key=lambda b: (b["speed_mph"] or 0, str(b["block"])))


def compare_setting(results, key):
  """Matched comparison of one setting: maneuvers with the same speed/maneuver and all other
  settings equal. Returns {value: {metric: mean ratio vs the group's best, ...}} + raw means."""
  groups = defaultdict(lambda: defaultdict(list))
  for r in results:
    if r.get("error") or key not in r["settings"]:
      continue
    others = json.dumps({k: _setting_value(r["settings"], k) for k in sorted(r["settings"]) if k not in (key, "friction_table_name")})
    groups[(r["speed_mph"], r["desc"], others)][str(_setting_value(r["settings"], key))].append(r)
  metrics = defaultdict(lambda: defaultdict(list))
  speeds = defaultdict(set)
  for (speed, _, _), by_value in groups.items():
    if len(by_value) < 2:
      continue
    for value, rs in by_value.items():
      speeds[value].add(speed)
      for m in ("tracking_rms", "overshoot_pct", "cmd_flips_per_s", "err_flips_per_s", "phase_delay_s"):
        v = _mean([r.get(m) for r in rs])
        if v is not None:
          metrics[value][m].append(v)
      if rs[0]["type"] in ("step", "sine"):
        metrics[value]["tracking_rms_dynamic"].append(_mean([r.get("tracking_rms") for r in rs]))
      if rs[0]["type"] == "hold":
        metrics[value]["tracking_rms_hold"].append(_mean([r.get("tracking_rms") for r in rs]))
  return {v: {"n": len(ms.get("tracking_rms", [])), "speeds_mph": sorted(speeds[v]),
              **{m: _mean(x) for m, x in ms.items()}} for v, ms in metrics.items()}


def _best(cmp, metric="tracking_rms_dynamic", fallback="tracking_rms"):
  scored = {v: (m.get(metric) if m.get(metric) is not None else m.get(fallback)) for v, m in cmp.items()}
  scored = {v: s for v, s in scored.items() if s is not None}
  return (min(scored, key=scored.get), scored) if scored else (None, scored)


def recommend(results):
  rec = {}
  delays = [r["cmd_delay_s"] for r in results if r.get("cmd_delay_s") is not None and abs(r.get("cmd_corr") or 0) >= 0.5]
  measured = _median(delays)

  # SteerDelay
  cmp = compare_setting(results, "steer_delay")
  best, scored = _best(cmp)
  sd = {"measured_cmd_to_accel_delay_s": measured, "n_delay_estimates": len(delays), "variants": cmp}
  if best is not None:
    sd["value"] = best if best == "auto" else float(best)
    sd["why"] = (f"lowest matched step/sine tracking RMS ({', '.join(f'{v}: {s:.3f}' for v, s in sorted(scored.items()))} m/s²)")
  elif measured is not None:
    sd["value"] = round(round(measured / 0.05) * 0.05, 2)
    sd["why"] = "no matched SteerDelay variants; measured 0x249->lat accel delay rounded to 0.05 s"
  else:
    sd["value"], sd["why"] = None, "insufficient data"
  rec["steer_delay"] = sd

  # friction threshold table from amplified noise in straight holds
  holds = [r for r in results if r["type"] == "hold" and r.get("amplified_noise_sigma") is not None]
  by_speed = defaultdict(list)
  for r in holds:
    by_speed[(r.get("v_mean") or r["speed_mph"] * MPH_TO_MS)].append(r["amplified_noise_sigma"])
  ft = {"variants": compare_setting(results, "friction_table"), "noise_by_speed": {}}
  if by_speed:
    vs = sorted(by_speed)
    sig = [float(np.median(by_speed[v])) for v in vs]
    ft["noise_by_speed"] = {f"{v:.2f}": s for v, s in zip(vs, sig, strict=True)}
    table = [float(np.clip(THRESHOLD_MARGIN * np.interp(k, vs, sig), *THRESHOLD_RANGE)) for k in FRICTION_SPEED_KNOTS]
    table = [round(round(x / 0.05) * 0.05, 2) for x in table]
    closest = min(FRICTION_TABLES, key=lambda n: float(np.sum((np.array(FRICTION_TABLES[n]) - table) ** 2)))
    ft.update({"value": table, "knots_mps": FRICTION_SPEED_KNOTS, "closest_named": closest,
               "why": f"{THRESHOLD_MARGIN:g} x median amplified noise sigma(des-act)*(1+lsf/Kp) from straight holds, " +
                      f"clamped to {THRESHOLD_RANGE}; closest named table '{closest}'"})
    fl = ft["variants"]
    if "flat" in fl and "lowspeed" in fl and fl["flat"].get("cmd_flips_per_s") and fl["lowspeed"].get("cmd_flips_per_s") is not None:
      ft["ping_pong_ratio_lowspeed_vs_flat"] = fl["lowspeed"]["cmd_flips_per_s"] / fl["flat"]["cmd_flips_per_s"]
  else:
    ft.update({"value": None, "why": "no straight holds analyzed"})
  rec["friction_table"] = ft

  # TISteerKp: prefer the higher gain only if it tracks better without more ping-pong/overshoot
  cmp = compare_setting(results, "ti_steer_kp")
  kp = {"variants": cmp}
  if len(cmp) >= 2:
    vals = sorted(cmp, key=float)
    lo, hi = cmp[vals[0]], cmp[vals[-1]]
    rms_lo = lo.get("tracking_rms_dynamic") or lo.get("tracking_rms")
    rms_hi = hi.get("tracking_rms_dynamic") or hi.get("tracking_rms")
    better = rms_lo is not None and rms_hi is not None and rms_hi <= 0.95 * rms_lo
    flips_ok = not (lo.get("cmd_flips_per_s") and hi.get("cmd_flips_per_s") and hi["cmd_flips_per_s"] > 1.25 * lo["cmd_flips_per_s"])
    over_ok = (hi.get("overshoot_pct") or 0.0) < 30.0
    pick = vals[-1] if better and flips_ok and over_ok else vals[0]
    kp["value"] = float(pick)
    kp["why"] = (f"Kp {vals[-1]}: step/sine tracking RMS {_f(rms_hi)} vs {_f(rms_lo)} m/s² at Kp {vals[0]} " +
                 f"(needs >=5% better), ping-pong ok={flips_ok}, overshoot {_f(hi.get('overshoot_pct'), '.0f')}% ok={over_ok}")
  else:
    kp.update({"value": None, "why": "no matched TISteerKp variants"})
  rec["ti_steer_kp"] = kp
  return rec


# ---------------------------------------------------------------------------
# output

def _f(x, fmt=".3f"):
  return "–" if x is None else format(x, fmt)


def render_markdown(report):
  rec = report["recommendation"]
  sd, ft, kp = rec["steer_delay"], rec["friction_table"], rec["ti_steer_kp"]
  routes = report.get("routes") or [report.get("route")]
  lines = [f"# Lateral characterization — {', '.join(str(r) for r in routes)}", "",
           f"Plan `{report.get('plan')}`, branch `{report['git'].get('branch')}` @ `{report['git'].get('commit')}`. " +
           f"0x249→lat-accel sign: {'+' if report['cmd_accel_sign'] > 0 else '−'}.", "",
           "## Recommendation", "",
           f"- **SteerDelay:** {sd.get('value')} — {sd.get('why')}. Measured 0x249→lat accel delay " +
           f"{_f(sd.get('measured_cmd_to_accel_delay_s'))} s (n={sd.get('n_delay_estimates')}).",
           f"- **Friction threshold table** @ {FRICTION_SPEED_KNOTS} m/s: {ft.get('value')} — {ft.get('why')}."
           + (f" Ping-pong lowspeed/flat = {ft['ping_pong_ratio_lowspeed_vs_flat']:.2f}." if ft.get("ping_pong_ratio_lowspeed_vs_flat") else ""),
           f"- **TISteerKp:** {kp.get('value')} — {kp.get('why')}.", "",
           "## Blocks", "",
           "| block | mph | settings | delay cmd→a (s) | des→act (s) | RMS dyn | overshoot % | rise s | settle s " +
           "| flips/s cmd | flips/s err | σ amp | thr | slew-cap | req gap | roll | pitch |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
  for b in report["blocks"]:
    lines.append(f"| {b['block']} | {b['speed_mph']:g} | {b['tag']} | {_f(b['cmd_delay_s'], '.2f')} | " +
                 f"{_f(b['des_act_delay_s'], '.2f')} | {_f(b['tracking_rms_dynamic'])} | {_f(b['overshoot_pct'], '.0f')} | " +
                 f"{_f(b['rise_s'], '.2f')} | {_f(b['settling_s'], '.2f')} | {_f(b['cmd_flips_per_s'], '.2f')} | " +
                 f"{_f(b['err_flips_per_s'], '.2f')} | {_f(b['amplified_noise_sigma'])} | {_f(b['friction_threshold'], '.2f')} | " +
                 f"{_f(b['slew_cap_frac'], '.2f')} | {_f(b['req_gap_mean_abs'], '.1f')} | {_f(b['roll_mean'], '.3f')} | " +
                 f"{_f(b['pitch_mean'], '.3f')} |")
  lines += ["", "## Sine response (gain / phase °)", ""]
  for b in report["blocks"]:
    if b["sine"]:
      parts = ", ".join(f"{f} Hz: {_f(s['gain'], '.2f')} / {_f(s['phase_deg'], '.0f')}" for f, s in b["sine"].items())
      lines.append(f"- {b['block']} ({b['speed_mph']:g} mph, {b['tag']}): {parts}")
  lines += ["", "## Matched variant comparisons", ""]
  for name, key in (("SteerDelay", "steer_delay"), ("Friction table", "friction_table"), ("TISteerKp", "ti_steer_kp")):
    for v, m in (rec[key].get("variants") or {}).items():
      lines.append(f"- {name} {v}: RMS dyn {_f(m.get('tracking_rms_dynamic'))}, RMS hold {_f(m.get('tracking_rms_hold'))}, " +
                   f"overshoot {_f(m.get('overshoot_pct'), '.0f')}%, cmd flips/s {_f(m.get('cmd_flips_per_s'), '.2f')}, " +
                   f"speeds {m.get('speeds_mph')}")
  if len(routes) > 1 or report.get("ignored_blocks"):
    lines += ["", "## Runs merged (newest completed run wins per block)", ""]
    lines += [f"- {b}: {r}" for b, r in sorted((report.get("block_sources") or {}).items(), key=lambda x: str(x[0]))]
    lines += [f"- ignored {i['block']} from {i['route']}: {i['reason']}" for i in report.get("ignored_blocks") or []]
  lines += ["", "## Incidents", ""]
  for e in report["incidents"] or []:
    lines.append(f"- {e['type']} {e.get('block', '')} {e.get('maneuver', '')}: {e.get('reason', e.get('pending', ''))}")
  if not report["incidents"]:
    lines.append("- none")
  end = report.get("run_end") or {}
  lines += ["", f"Run end: {end.get('reason', 'not logged')}; restored {end.get('restored')}", ""]
  return "\n".join(lines)


def _jsonable(o):
  if isinstance(o, dict):
    return {str(k): _jsonable(v) for k, v in o.items()}
  if isinstance(o, (list, tuple)):
    return [_jsonable(v) for v in o]
  if isinstance(o, (np.floating, float)):
    return None if math.isnan(o) else float(o)
  if isinstance(o, np.integer):
    return int(o)
  return o


def write_report(report, out_dir):
  os.makedirs(out_dir, exist_ok=True)
  with open(os.path.join(out_dir, "report.json"), "w") as f:
    json.dump(_jsonable(report), f, indent=1)
  with open(os.path.join(out_dir, "report.md"), "w") as f:
    f.write(render_markdown(report))
  return os.path.join(out_dir, "report.md")


def main(argv=None):
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--sidecar", action="append", default=[], help="sidecar JSON (repeatable: one per route/run)")
  ap.add_argument("--rlogs", action="append", default=[],
                  help="directory with <route>--<seg>/rlog* (repeatable, paired with --sidecar; one dir may hold all routes)")
  ap.add_argument("--route", action="append", default=[], help="route name (e.g. 0000012a--abcdef0123) for --pull, repeatable")
  ap.add_argument("--pull", action="store_true", help="copy rlogs + sidecar from the comma over ssh")
  ap.add_argument("--host", default=DEVICE)
  ap.add_argument("--key", default=SSH_KEY)
  ap.add_argument("--out", default="lateral_characterization_report")
  args = ap.parse_args(argv)

  sidecar_paths, rlog_dirs = list(args.sidecar), list(args.rlogs)
  if args.pull:
    if not args.route:
      ap.error("--pull needs --route")
    rlog_dir = rlog_dirs[0] if rlog_dirs else os.path.join(args.out, "rlogs")
    rlog_dirs = [rlog_dir]
    for route in args.route:
      sidecar_paths += pull_route(route, rlog_dir, args.host, args.key)
  if not rlog_dirs or not sidecar_paths:
    ap.error("need --rlogs and --sidecar (or --route --pull)")
  if len(rlog_dirs) not in (1, len(sidecar_paths)):
    ap.error("give one --rlogs for all sidecars or one per --sidecar")
  runs, cache = [], {}
  for i, path in enumerate(sidecar_paths):
    with open(path) as f:
      sidecar = json.load(f)
    rlog_dir = rlog_dirs[0] if len(rlog_dirs) == 1 else rlog_dirs[i]
    key = (rlog_dir, sidecar.get("route"))
    if key not in cache:
      cache[key] = load_rlogs(rlog_dir, sidecar.get("route"))
    runs.append((cache[key], sidecar))
  report = analyze_runs(runs)
  path = write_report(report, args.out)
  with open(path) as f:
    print(f.read())


if __name__ == "__main__":
  main()
