"""Car-specific longitudinal numbers for the 9G Accord (Nidec, optional pedal interceptor).

The pedal/brake features on this branch were measured on Mat's TI car (2026-09..10 drives). This branch is
for a different 9G, so every number that came from that car defaults to stock Dom behaviour here; only the
mechanisms are ported. To tune the new car, write /data/accord_9g_tune.json (read once when card/controlsd
start, so restart openpilot or reboot after editing):

  {"preset": "ti_car"}                                     all of the TI car's values
  {"brake_accel_per_unit": 4.0, "aero_wind_brake": true}   stock plus individual fields

Fields override the preset. Unknown fields, out-of-range values or a broken file fall back to stock
(logged to carlog). Not car-specific and always on: the dash set-speed label, the pedal learner log, the
LongitudinalActuatorDelay param reaching the planner/modeld (the value is the device's own param).
"""
import dataclasses
import json
import math
import os
from contextlib import contextmanager

from opendbc.car.carlog import carlog

TUNE_FILE = "/data/accord_9g_tune.json"


@dataclasses.dataclass(frozen=True)
class Accord9GTune:
  # m/s^2 of decel per unit of Nidec brake command. Stock 4.8; the TI car measured 2.8-3.8 (used 3.6).
  brake_accel_per_unit: float = 4.8
  # Free decel from drag: stock Nidec curve (False) or the aero estimate (True; TI car got ~0 free decel at 50 mph).
  aero_wind_brake: bool = False
  # Pedal gas-factor guard (pedal_learner.py): gated, 10x slower, per-drive limited learner with a band and a
  # launch-speed cap. Off = stock learner (clip 0.1-3.0). The band is where the TI car tracked unbiased.
  gas_guard: bool = False
  gas_factor_min: float = 1.2
  gas_factor_max: float = 1.6
  gas_factor_default: float = 1.4
  low_speed_gas_cap: float = 1.0
  # Cruise-hold brake deadband (cruise_brake_deadband.py). Needs aero_wind_brake (its pedal-close estimate
  # uses the aero curve). pedal_close_wind_factor = the learned HondaWindFactorParams (~5 on the TI car).
  cruise_brake_deadband: bool = False
  pedal_close_wind_factor: float = 5.0
  # Long-PID brake-onset integrator hold (longcontrol_vehicle_tunes.py).
  brake_onset_hold: bool = False
  brake_onset_i_floor: float = -0.4


STOCK = Accord9GTune()
TI_CAR = Accord9GTune(brake_accel_per_unit=3.6, aero_wind_brake=True, gas_guard=True,
                      cruise_brake_deadband=True, brake_onset_hold=True)
PRESETS = {"stock": STOCK, "ti_car": TI_CAR}

_RANGES = {
  "brake_accel_per_unit": (2.0, 6.0),
  "gas_factor_min": (0.1, 3.0),
  "gas_factor_max": (0.1, 3.0),
  "gas_factor_default": (0.1, 3.0),
  "low_speed_gas_cap": (0.1, 3.0),
  "pedal_close_wind_factor": (0.1, 5.0),
  "brake_onset_i_floor": (-1.0, 0.0),
}


def parse_tune(data) -> Accord9GTune:
  """Raises ValueError on anything that isn't a valid tune."""
  if not isinstance(data, dict):
    raise ValueError("tune file must be a JSON object")
  data = dict(data)
  preset = data.pop("preset", "stock")
  if not isinstance(preset, str) or preset not in PRESETS:
    raise ValueError(f"unknown preset {preset!r}")
  fields = {f.name: f for f in dataclasses.fields(Accord9GTune)}
  changes = {}
  for key, value in data.items():
    if key not in fields:
      raise ValueError(f"unknown field {key!r}")
    if isinstance(getattr(STOCK, key), bool):
      if not isinstance(value, bool):
        raise ValueError(f"{key} must be true/false")
    else:
      if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{key} must be a number")
      lo, hi = _RANGES[key]
      if not lo <= value <= hi:
        raise ValueError(f"{key}={value} outside {lo}..{hi}")
      value = float(value)
    changes[key] = value
  tune = dataclasses.replace(PRESETS[preset], **changes)
  if not tune.gas_factor_min <= tune.gas_factor_default <= tune.gas_factor_max:
    raise ValueError("need gas_factor_min <= gas_factor_default <= gas_factor_max")
  if tune.cruise_brake_deadband and not tune.aero_wind_brake:
    raise ValueError("cruise_brake_deadband needs aero_wind_brake")
  return tune


def load_tune(path: str | None = None) -> Accord9GTune:
  path = path or TUNE_FILE
  if not os.path.exists(path):
    return STOCK
  try:
    with open(path) as f:
      tune = parse_tune(json.load(f))
  except (OSError, ValueError) as e:
    carlog.error(f"Accord 9G tune: ignoring {path} ({e}); using stock values")
    return STOCK
  carlog.warning(f"Accord 9G tune from {path}: {tune}")
  return tune


_override: Accord9GTune | None = None
_cache: Accord9GTune | None = None


def get_tune() -> Accord9GTune:
  global _cache
  if _override is not None:
    return _override
  if _cache is None:
    _cache = load_tune()
  return _cache


@contextmanager
def use_tune(tune: Accord9GTune):
  """Tests: run with this tune instead of the file."""
  global _override
  prev, _override = _override, tune
  try:
    yield tune
  finally:
    _override = prev
