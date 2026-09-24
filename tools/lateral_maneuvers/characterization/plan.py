#!/usr/bin/env python3
"""Characterization plan: schema, validation/clamping and maneuver profiles.

Pure Python + numpy so it can be unit tested and used by the host-side report
without the compiled openpilot stack.

A plan is an ordered list of blocks. Each block runs at one target speed with one
set of controller settings and contains an ordered list of maneuvers:

  hold  zero lateral accel for duration_s (noise / ping-pong baseline)
  step  doublet +a for T, -a for 2T, +a for T, then 1 s at 0. The doublet returns
        heading and lateral position to zero; peak lateral offset is a*T^2.
  sine  half-amplitude lead-in half cycle, (2*cycles - 1) full-amplitude half cycles,
        half-amplitude tail half cycle. Heading is zero-mean, so the car does not
        drift off the road; the full-amplitude part is used for the gain/phase fit.
"""
import argparse
import copy
import json
import math
import sys

import numpy as np

PLAN_VERSION = 1
PLAN_PATH = "/data/lateral_characterization_plan.json"

DT = 0.05  # s, must equal openpilot.common.realtime.DT_MDL (lateral_maneuversd polls modelV2)
MPH_TO_MS = 0.44704

# Safety envelope (requirement 2). Plans are clamped to this; the runner clamps again per frame.
LAT_ACCEL_ABS_MAX = 1.0  # m/s^2
LOW_SPEED_MPH = 12.0
LOW_SPEED_LAT_ACCEL_MAX = 0.6  # m/s^2 at <= 12 mph
SINE_FREQ_MAX = 0.8  # Hz
SINE_FREQ_MIN = 0.05  # Hz
SPEED_MPH_MIN = 5.0
SPEED_MPH_MAX = 45.0
STEP_HOLD_MIN, STEP_HOLD_MAX = 0.5, 5.0  # s
HOLD_MIN, HOLD_MAX = 2.0, 30.0  # s
SINE_CYCLES_MIN, SINE_CYCLES_MAX = 2, 6
STEP_SETTLE_S = 1.0  # zero-accel tail after a step doublet
DEFAULT_MAX_DISPLACEMENT_M = 3.0  # predicted peak lateral offset from the open-loop profile
MAX_DISPLACEMENT_LIMIT_M = 6.0
DEFAULT_SPEED_TOLERANCE_MPS = 0.7  # same as stock MAX_SPEED_DEV
SPEED_TOLERANCE_RANGE = (0.3, 1.5)
DEFAULT_MAX_ATTEMPTS = 4

# FLM "standard" base friction-threshold family (latcontrol_vehicle_tunes.FLM_FRICTION_SPEED_KNOTS).
FRICTION_SPEED_KNOTS = [0.0, 5.0, 10.0, 15.0, 25.0]  # m/s
FRICTION_TABLES = {
  "flat": [0.30, 0.30, 0.30, 0.30, 0.30],  # == stock STANDARD_FRICTION_THRESHOLD below 75 mph
  "lowspeed": [2.0, 1.2, 0.45, 0.35, 0.30],
}
FRICTION_VALUE_RANGE = (0.05, 3.0)
STEER_DELAY_RANGE = (0.01, 1.0)  # starpilot_variables clamps SteerDelay to this range
TI_STEER_KP_RANGE = (0.3, 3.0)  # TISteerKp slider range

# Settings that can be switched live between maneuvers, and ones that cannot.
LIVE_SETTINGS = ("steer_delay", "friction_table", "ti_steer_kp")
RESTART_REQUIRED_SETTINGS = {
  "steer_friction": ("SteerFriction applies live, but controlsd only pushes torque params while a custom/live value is " +
                     "in use, so restoring the stock value does not reach LatControlTorque until controlsd restarts."),
  "steer_lat_accel": "SteerLatAccel has the same one-way live path as SteerFriction (restore needs a restart).",
  "steer_kp": "SteerKP is ignored on the TI car: controlsd replaces the Kp schedule with TISteerKp every frame.",
  "sigmoid": "TISigmoidA/B/C swap the torque lookup table; out of scope for this tool (static gain is fine).",
}

DEFAULT_VARIANTS = {
  "A": {"label": "baseline", "steer_delay": 0.01, "friction_table": "flat", "ti_steer_kp": 0.5},
  "B": {"label": "delay auto (lagd)", "steer_delay": "auto", "friction_table": "flat", "ti_steer_kp": 0.5},
  "C": {"label": "delay 0.5", "steer_delay": 0.5, "friction_table": "flat", "ti_steer_kp": 0.5},
  "F": {"label": "low-speed friction table", "steer_delay": 0.01, "friction_table": "lowspeed", "ti_steer_kp": 0.5},
  "K": {"label": "Kp 0.8", "steer_delay": 0.01, "friction_table": "flat", "ti_steer_kp": 0.8},
}
DEFAULT_SPEEDS_MPH = [8, 12, 15, 20, 30]
DEFAULT_VARIANT_ORDER = ["A", "B", "C", "F", "K"]


def standard_maneuvers(speed_mph):
  sine_amp = 0.2 if speed_mph <= LOW_SPEED_MPH else 0.3
  return [
    {"type": "hold", "duration_s": 10.0},
    {"type": "step", "amplitude": 0.3, "hold_s": 3.0},
    # 0.6 * 3^2 = 5.4 m peak offset; the displacement clamp shortens the hold to ~2.2 s.
    {"type": "step", "amplitude": 0.6, "hold_s": 2.0},
    {"type": "sine", "freq_hz": 0.2, "amplitude": sine_amp, "cycles": 2},
    {"type": "sine", "freq_hz": 0.4, "amplitude": sine_amp, "cycles": 3},
    {"type": "sine", "freq_hz": 0.7, "amplitude": sine_amp, "cycles": 4},
  ]


def quick_maneuvers(speed_mph):
  sine_amp = 0.2 if speed_mph <= LOW_SPEED_MPH else 0.3
  return [
    {"type": "hold", "duration_s": 8.0},
    {"type": "step", "amplitude": 0.3, "hold_s": 3.0},
    {"type": "sine", "freq_hz": 0.4, "amplitude": sine_amp, "cycles": 3},
  ]


MANEUVER_SETS = {"standard": standard_maneuvers, "quick": quick_maneuvers}
PRESETS = {
  "default": {"speeds": DEFAULT_SPEEDS_MPH, "variants": DEFAULT_VARIANT_ORDER, "maneuvers": "standard"},
  "quick": {"speeds": [8, 15, 30], "variants": ["A", "B", "F", "K"], "maneuvers": "quick"},
  "lowspeed": {"speeds": [8, 12, 15], "variants": ["A", "F", "K"], "maneuvers": "standard"},
}


class PlanError(ValueError):
  pass


def lat_accel_limit(speed_mph):
  return LOW_SPEED_LAT_ACCEL_MAX if speed_mph <= LOW_SPEED_MPH else LAT_ACCEL_ABS_MAX


def _num(value, name):
  if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
    raise PlanError(f"{name} must be a finite number, got {value!r}")
  return float(value)


def _clip(value, lo, hi, name, notes):
  clipped = min(max(value, lo), hi)
  if clipped != value:
    notes.append(f"{name} {value:g} clamped to {clipped:g}")
  return clipped


# ---------------------------------------------------------------------------
# settings

def normalize_settings(raw, notes=None):
  """Validate one settings dict. Returns canonical {steer_delay, friction_table, friction_table_name, ti_steer_kp}."""
  notes = notes if notes is not None else []
  if not isinstance(raw, dict):
    raise PlanError(f"settings must be an object, got {raw!r}")

  unknown = [k for k in raw if k not in LIVE_SETTINGS and k != "label"]
  for key in unknown:
    if key in RESTART_REQUIRED_SETTINGS:
      raise PlanError(f"setting '{key}' cannot be switched live: {RESTART_REQUIRED_SETTINGS[key]}")
    raise PlanError(f"unknown setting '{key}' (supported: {', '.join(LIVE_SETTINGS)})")

  out = {}
  if "steer_delay" in raw:
    delay = raw["steer_delay"]
    if delay == "auto":
      out["steer_delay"] = "auto"
    else:
      out["steer_delay"] = round(_clip(_num(delay, "steer_delay"), *STEER_DELAY_RANGE, "steer_delay", notes), 3)

  if "friction_table" in raw:
    table = raw["friction_table"]
    if isinstance(table, str):
      if table not in FRICTION_TABLES:
        raise PlanError(f"unknown friction_table '{table}' (named tables: {', '.join(FRICTION_TABLES)})")
      out["friction_table"] = list(FRICTION_TABLES[table])
      out["friction_table_name"] = table
    elif isinstance(table, (list, tuple)):
      if len(table) != len(FRICTION_SPEED_KNOTS):
        raise PlanError(f"friction_table needs {len(FRICTION_SPEED_KNOTS)} values for knots {FRICTION_SPEED_KNOTS} m/s")
      values = [round(_clip(_num(v, "friction_table value"), *FRICTION_VALUE_RANGE, "friction_table value", notes), 4)
                for v in table]
      out["friction_table"] = values
      name = next((n for n, t in FRICTION_TABLES.items() if np.allclose(t, values)), "custom")
      out["friction_table_name"] = name
    else:
      raise PlanError(f"friction_table must be a name or a list, got {table!r}")

  if "ti_steer_kp" in raw:
    out["ti_steer_kp"] = round(_clip(_num(raw["ti_steer_kp"], "ti_steer_kp"), *TI_STEER_KP_RANGE, "ti_steer_kp", notes), 3)

  return out


def settings_tag(settings):
  """Short human/regex-friendly tag, e.g. 'd0.01 fflat kp0.50'."""
  parts = []
  if "steer_delay" in settings:
    delay = settings["steer_delay"]
    parts.append("dauto" if delay == "auto" else f"d{delay:.2f}")
  if "friction_table" in settings:
    name = settings.get("friction_table_name", "custom")
    parts.append(f"f{name}")
  if "ti_steer_kp" in settings:
    parts.append(f"kp{settings['ti_steer_kp']:.2f}")
  return " ".join(parts)


# ---------------------------------------------------------------------------
# maneuvers

def _sine_halves(amplitude, cycles):
  return [amplitude / 2.0] + [amplitude] * (2 * cycles - 1) + [amplitude / 2.0]


def maneuver_profile(spec):
  """Dense (t, accel) arrays at DT for a validated maneuver spec (accel relative to baseline)."""
  kind = spec["type"]
  if kind == "hold":
    n = int(round(spec["duration_s"] / DT))
    t = np.arange(n + 1) * DT
    return t, np.zeros_like(t)

  if kind == "step":
    a, hold = spec["amplitude"], spec["hold_s"]
    levels = [(a, hold), (-a, 2 * hold), (a, hold), (0.0, STEP_SETTLE_S)]
    accel = []
    for level, dur in levels:
      accel.extend([level] * int(round(dur / DT)))
    accel.append(0.0)
    accel = np.array(accel)
    return np.arange(len(accel)) * DT, accel

  if kind == "sine":
    f, a, cycles = spec["freq_hz"], spec["amplitude"], spec["cycles"]
    half = 1.0 / (2.0 * f)
    halves = _sine_halves(a, cycles)
    duration = half * len(halves)
    t = np.arange(int(round(duration / DT)) + 1) * DT
    idx = np.minimum((t / half).astype(int), len(halves) - 1)
    amps = np.array(halves)[idx]
    accel = amps * np.sin(2.0 * np.pi * f * t)
    accel[-1] = 0.0
    return t, accel

  raise PlanError(f"unknown maneuver type {kind!r}")


def maneuver_meta(spec):
  """Timing metadata the analysis uses (offsets from maneuver start, seconds)."""
  kind = spec["type"]
  if kind == "hold":
    return {"window": [0.0, spec["duration_s"]]}
  if kind == "step":
    a, hold = spec["amplitude"], spec["hold_s"]
    transitions = [
      {"t": 0.0, "from": 0.0, "to": a, "hold_s": hold},
      {"t": hold, "from": a, "to": -a, "hold_s": 2 * hold},
      {"t": 3 * hold, "from": -a, "to": a, "hold_s": hold},
      {"t": 4 * hold, "from": a, "to": 0.0, "hold_s": STEP_SETTLE_S},
    ]
    return {"window": [0.0, 4 * hold + STEP_SETTLE_S], "transitions": transitions}
  if kind == "sine":
    f, cycles = spec["freq_hz"], spec["cycles"]
    half = 1.0 / (2.0 * f)
    # integer number of full-amplitude cycles right after the half-amplitude lead-in
    return {"window": [0.0, half * (2 * cycles + 1)], "fit_window": [half, half + (cycles - 1) / f],
            "freq_hz": f}
  raise PlanError(f"unknown maneuver type {kind!r}")


def predicted_displacement(spec):
  """Peak |lateral offset| (m) of the open-loop profile: double integral of lat accel."""
  _, accel = maneuver_profile(spec)
  vel = np.cumsum(accel) * DT
  pos = np.cumsum(vel) * DT
  return float(np.max(np.abs(pos))) if len(pos) else 0.0


def normalize_maneuver(raw, speed_mph, max_displacement_m):
  notes = []
  if not isinstance(raw, dict) or "type" not in raw:
    raise PlanError(f"maneuver must be an object with a 'type', got {raw!r}")
  kind = raw["type"]
  a_max = lat_accel_limit(speed_mph)

  if kind == "hold":
    spec = {"type": "hold", "duration_s": _clip(_num(raw.get("duration_s", 10.0), "duration_s"), HOLD_MIN, HOLD_MAX,
                                                "duration_s", notes)}
  elif kind == "step":
    amp = abs(_num(raw.get("amplitude", 0.3), "amplitude"))
    amp = _clip(amp, 0.05, a_max, "step amplitude", notes)
    hold = _clip(_num(raw.get("hold_s", 3.0), "hold_s"), STEP_HOLD_MIN, STEP_HOLD_MAX, "hold_s", notes)
    max_hold = math.sqrt(max_displacement_m / amp)
    if hold > max_hold:
      new_hold = max(math.floor(max_hold / DT) * DT, STEP_HOLD_MIN)
      notes.append(f"hold_s {hold:g} shortened to {new_hold:.2f} " +
                   f"(peak lateral offset {amp * hold ** 2:.1f} m > {max_displacement_m:g} m)")
      hold = new_hold
    spec = {"type": "step", "amplitude": round(amp, 3), "hold_s": round(hold, 2)}
  elif kind == "sine":
    freq = _clip(_num(raw.get("freq_hz", 0.4), "freq_hz"), SINE_FREQ_MIN, SINE_FREQ_MAX, "freq_hz", notes)
    amp = _clip(abs(_num(raw.get("amplitude", 0.3), "amplitude")), 0.05, a_max, "sine amplitude", notes)
    cycles = raw.get("cycles", 3)
    if isinstance(cycles, bool) or not isinstance(cycles, int):
      raise PlanError(f"cycles must be an integer, got {cycles!r}")
    cycles = int(_clip(cycles, SINE_CYCLES_MIN, SINE_CYCLES_MAX, "cycles", notes))
    spec = {"type": "sine", "freq_hz": round(freq, 3), "amplitude": round(amp, 3), "cycles": cycles}
    disp = predicted_displacement(spec)
    if disp > max_displacement_m:
      scaled = spec["amplitude"] * max_displacement_m / disp
      notes.append(f"sine amplitude {spec['amplitude']:g} reduced to {scaled:.3f} (peak lateral offset {disp:.1f} m)")
      spec["amplitude"] = round(scaled, 3)
  else:
    raise PlanError(f"unknown maneuver type {kind!r} (hold, step, sine)")

  spec["notes"] = notes
  spec["duration_s"] = round(float(maneuver_profile(spec)[0][-1]), 2)
  spec["displacement_m"] = round(predicted_displacement(spec), 2)
  spec["desc"] = maneuver_desc(spec)
  return spec


def maneuver_desc(spec):
  kind = spec["type"]
  if kind == "hold":
    return f"hold {spec['duration_s']:.0f}s"
  if kind == "step":
    return f"step ±{spec['amplitude']:.1f} {spec['hold_s']:.1f}s"
  return f"sine {spec['freq_hz']:.1f}Hz ±{spec['amplitude']:.1f}"


# ---------------------------------------------------------------------------
# plan

def normalize_plan(raw):
  """Validate and clamp a plan dict. Raises PlanError on anything it cannot make safe."""
  if not isinstance(raw, dict):
    raise PlanError("plan must be a JSON object")
  version = raw.get("version", PLAN_VERSION)
  if version != PLAN_VERSION:
    raise PlanError(f"unsupported plan version {version!r} (expected {PLAN_VERSION})")

  notes = []
  speed_tol = _clip(_num(raw.get("speed_tolerance_mps", DEFAULT_SPEED_TOLERANCE_MPS), "speed_tolerance_mps"),
                    *SPEED_TOLERANCE_RANGE, "speed_tolerance_mps", notes)
  max_disp = _clip(_num(raw.get("max_displacement_m", DEFAULT_MAX_DISPLACEMENT_M), "max_displacement_m"),
                   0.5, MAX_DISPLACEMENT_LIMIT_M, "max_displacement_m", notes)
  max_attempts = raw.get("max_attempts_per_maneuver", DEFAULT_MAX_ATTEMPTS)
  if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 20:
    raise PlanError("max_attempts_per_maneuver must be an integer in [1, 20]")

  variants = {}
  for name, settings in (raw.get("variants") or {}).items():
    variants[str(name)] = normalize_settings(settings, notes)
    if isinstance(settings, dict) and "label" in settings:
      variants[str(name)]["label"] = str(settings["label"])

  blocks_raw = raw.get("blocks")
  if not isinstance(blocks_raw, list) or not blocks_raw:
    raise PlanError("plan needs a non-empty 'blocks' list")

  blocks = []
  for i, block in enumerate(blocks_raw):
    if not isinstance(block, dict):
      raise PlanError(f"block {i} must be an object")
    speed_mph = _num(block.get("speed_mph"), f"block {i} speed_mph")
    if not SPEED_MPH_MIN <= speed_mph <= SPEED_MPH_MAX:
      raise PlanError(f"block {i} speed_mph {speed_mph:g} outside [{SPEED_MPH_MIN:g}, {SPEED_MPH_MAX:g}]")

    block_notes = []
    settings = {}
    variant = block.get("variant")
    if variant is not None:
      if str(variant) not in variants:
        raise PlanError(f"block {i} uses unknown variant {variant!r}")
      settings.update({k: v for k, v in variants[str(variant)].items() if k != "label"})
    if block.get("settings"):
      settings.update(normalize_settings(block["settings"], block_notes))
    if not settings:
      raise PlanError(f"block {i} has no settings (give 'variant' and/or 'settings')")

    maneuvers_raw = block.get("maneuvers", "standard")
    if isinstance(maneuvers_raw, str):
      if maneuvers_raw not in MANEUVER_SETS:
        raise PlanError(f"block {i} unknown maneuver set {maneuvers_raw!r} ({', '.join(MANEUVER_SETS)})")
      maneuvers_raw = MANEUVER_SETS[maneuvers_raw](speed_mph)
    if not isinstance(maneuvers_raw, list) or not maneuvers_raw:
      raise PlanError(f"block {i} needs a non-empty maneuvers list")

    block_id = str(block.get("id") or f"b{i + 1:02d}")
    maneuvers = []
    for j, m in enumerate(maneuvers_raw):
      spec = normalize_maneuver(m, speed_mph, max_disp)
      spec["index"] = j
      spec["id"] = f"{block_id}m{j + 1}"
      maneuvers.append(spec)

    blocks.append({
      "index": i,
      "id": block_id,
      "speed_mph": speed_mph,
      "speed_mps": round(speed_mph * MPH_TO_MS, 3),
      "variant": str(variant) if variant is not None else None,
      "label": variants.get(str(variant), {}).get("label", "") if variant is not None else "",
      "settings": settings,
      "tag": settings_tag(settings),
      "notes": block_notes,
      "maneuvers": maneuvers,
    })

  ids = [b["id"] for b in blocks]
  if len(set(ids)) != len(ids):
    raise PlanError("block ids must be unique")

  plan = {
    "version": PLAN_VERSION,
    "name": str(raw.get("name", "custom")),
    "speed_tolerance_mps": speed_tol,
    "max_displacement_m": max_disp,
    "max_attempts_per_maneuver": max_attempts,
    "enable_advanced_lateral_tune": bool(raw.get("enable_advanced_lateral_tune", False)),
    "variants": variants,
    "blocks": blocks,
    "notes": notes,
  }
  plan["estimated_minutes"] = round(estimate_duration_s(plan) / 60.0, 1)
  return plan


def load_plan(path=PLAN_PATH):
  """Returns the normalized plan, or None when the file does not exist."""
  try:
    with open(path) as f:
      raw = json.load(f)
  except FileNotFoundError:
    return None
  except json.JSONDecodeError as e:
    raise PlanError(f"{path}: invalid JSON: {e}") from e
  return normalize_plan(raw)


# Overheads used for the drive-time estimate: TIMER (2 s) stabilizing + 1 s completion
# holdoff per maneuver, settings apply/verify per block, re-targeting ACC per speed change.
PER_MANEUVER_OVERHEAD_S = 4.0
PER_BLOCK_OVERHEAD_S = 6.0
PER_SPEED_CHANGE_OVERHEAD_S = 25.0


def estimate_duration_s(plan):
  total = 0.0
  prev_speed = None
  for block in plan["blocks"]:
    if block["speed_mph"] != prev_speed:
      total += PER_SPEED_CHANGE_OVERHEAD_S
      prev_speed = block["speed_mph"]
    total += PER_BLOCK_OVERHEAD_S
    for m in block["maneuvers"]:
      total += m["duration_s"] + PER_MANEUVER_OVERHEAD_S
  return total


def build_plan(preset="default", speeds=None, variants=None, maneuvers=None, name=None):
  base = PRESETS[preset]
  speeds = list(speeds or base["speeds"])
  variant_order = list(variants or base["variants"])
  maneuver_set = maneuvers or base["maneuvers"]
  unknown = [v for v in variant_order if v not in DEFAULT_VARIANTS]
  if unknown:
    raise PlanError(f"unknown variants {unknown} (known: {', '.join(DEFAULT_VARIANTS)})")
  blocks = []
  for speed in speeds:
    for variant in variant_order:
      blocks.append({"id": f"s{int(round(speed)):02d}{variant}", "speed_mph": speed, "variant": variant,
                     "maneuvers": maneuver_set})
  return {
    "version": PLAN_VERSION,
    "name": name or preset,
    "variants": copy.deepcopy({k: DEFAULT_VARIANTS[k] for k in variant_order}),
    "blocks": blocks,
  }


def summarize(plan):
  lines = [f"plan '{plan['name']}': {len(plan['blocks'])} blocks, ~{plan['estimated_minutes']} min"]
  for block in plan["blocks"]:
    man = ", ".join(m["desc"] for m in block["maneuvers"])
    lines.append(f"  {block['id']:>6} {block['speed_mph']:>4g} mph  {block['tag']:<28} {man}")
    for note in block["notes"] + [n for m in block["maneuvers"] for n in m["notes"]]:
      lines.append(f"         note: {note}")
  for note in plan["notes"]:
    lines.append(f"  note: {note}")
  return "\n".join(lines)


def main(argv=None):
  parser = argparse.ArgumentParser(description="Write or check a lateral characterization plan")
  sub = parser.add_subparsers(dest="cmd", required=True)
  gen = sub.add_parser("generate", help="write a plan JSON from a preset")
  gen.add_argument("--preset", choices=sorted(PRESETS), default="default")
  gen.add_argument("--speeds", help="comma separated mph, e.g. 8,12,15")
  gen.add_argument("--variants", help=f"comma separated variant ids from {','.join(DEFAULT_VARIANTS)}")
  gen.add_argument("--maneuvers", choices=sorted(MANEUVER_SETS))
  gen.add_argument("-o", "--output", default="-", help=f"output path ('-' = stdout; device path {PLAN_PATH})")
  chk = sub.add_parser("check", help="validate a plan file and print the clamped summary")
  chk.add_argument("path", nargs="?", default=PLAN_PATH)
  args = parser.parse_args(argv)

  if args.cmd == "generate":
    speeds = [float(s) for s in args.speeds.split(",")] if args.speeds else None
    variants = args.variants.split(",") if args.variants else None
    raw = build_plan(args.preset, speeds, variants, args.maneuvers)
    plan = normalize_plan(raw)
    text = json.dumps(raw, indent=2) + "\n"
    if args.output == "-":
      sys.stdout.write(text)
    else:
      with open(args.output, "w") as f:
        f.write(text)
    print(summarize(plan), file=sys.stderr)
    return 0

  plan = load_plan(args.path)
  if plan is None:
    print(f"{args.path}: not found (lateral_maneuversd will run the stock maneuvers)")
    return 1
  print(summarize(plan))
  return 0


if __name__ == "__main__":
  sys.exit(main())
