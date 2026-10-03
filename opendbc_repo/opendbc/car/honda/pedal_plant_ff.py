"""Model-based pedal feedforward for the Accord 9G Nidec pedal interceptor.

System identification on all local drives (2026-10-03: 34 drives with long-PID gas, 2ea..31c, rlogs + qlogs,
5.8 h; validated 10-fold by drive, sysid/gasfactor/sysid_plant.py and sysid_ff.py in openpilot-rebase-maintenance):
  - the pedal acts as a power request (the CVT holds the ratio for it): at fixed pedal aEgo * v is ~constant
    above ~3 m/s, so the plant is  aEgo = K(pf) / max(v, V0) + C0 + CD * v^2
  - pf is the commanded pedal through 0.1 s dead time and a 0.4 s first-order lag
  - held-out R^2 of aEgo: this compact model 0.79, a free speed x pedal table 0.82, gradient-boosted trees 0.87,
    against 0.66 for "aEgo = accel command" (what the stock map plus learner assumes)
  - pitch is left out: as a feedforward it made closed-loop tracking worse (the long PID integrator already carries
    grade, and calibrated pitch is noisy and ~0.6x physical scale; reports/2026-10-03-pedal-response-factors.md)

The feedforward inverts the compact plant for the commanded accel plus a short lead for the pedal lag. Closed-loop
replay against held-out-drive trees (12 drives, 1.95 h): launch (v < 6 m/s) tracking RMSE 0.344 -> 0.261 m/s^2 and
overshoot share 12.0 % -> 6.9 % versus the gas-factor guard, 6-12 m/s 0.280 -> 0.254, >= 12 m/s unchanged.

Safety net: the guarded stock map (pedal_learner.py) still runs and its pedal is the reference. The feedforward is
only used in the long PID state with no brake and blends in over 0.5-2 m/s, and its pedal is clamped to the guarded
map's pedal +- ENVELOPE. touch /data/pedal_plant_ff_disabled (read at car start) to fall back to the guard alone.
"""
import os

import numpy as np

# Compact plant fit (sysid_ff_model.json, full data). K: pedal -> "power" (m^2/s^3 per unit mass).
K_BP = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.55, 0.8]
K_V = [0.612, 0.694, 1.595, 3.751, 7.827, 11.111, 14.539, 19.640, 23.237, 34.260]
V0 = 2.0          # m/s; below this the launch is torque-limited, not power-limited
C0 = -0.0935      # m/s^2: rolling resistance + engine braking left after creep
CD = -0.000194    # 1/m: aerodynamic drag (m/s^2 per (m/s)^2)

LEAD_S = 0.3            # s: lead on the accel command for the identified 0.1 s + 0.4 s pedal lag
LEAD_FILTER_S = 0.2     # s: low-pass on the command derivative
LEAD_CLAMP = 0.5        # m/s^2: max lead contribution
BLEND_BP = [0.5, 2.0]   # m/s: feedforward weight 0 -> 1 (standstill launches keep the guarded map)
ENVELOPE = 0.12         # pedal units: max deviation from the guarded map's pedal (95 % of logged |diff| < ~0.1)
MAX_PEDAL = K_BP[-1]    # the fit has no data above this pedal
DISABLE_FILE = "/data/pedal_plant_ff_disabled"

_K_STRICT = np.array(K_V) + np.arange(len(K_V)) * 1e-6


def pedal_for_accel(accel: float, v_ego: float) -> float:
  """Steady-state inverse of the compact plant on flat ground: the pedal that holds `accel` at `v_ego`."""
  power = (accel - C0 - CD * v_ego ** 2) * max(v_ego, V0)
  return float(np.clip(np.interp(power, _K_STRICT, K_BP), 0.0, MAX_PEDAL))


def accel_for_pedal(pedal: float, v_ego: float) -> float:
  """Forward compact plant (steady state, flat): for tests and logging."""
  return float(np.interp(pedal, K_BP, K_V) / max(v_ego, V0) + C0 + CD * v_ego ** 2)


def ff_disabled_by_file() -> bool:
  try:
    return os.path.exists(DISABLE_FILE)
  except OSError:
    return False


class PedalPlantFeedforward:
  def __init__(self, dt: float):
    self.dt = dt
    self.last_accel: float | None = None
    self.d_accel = 0.0
    self.active_steps = 0
    self.total_steps = 0

  def reset(self):
    self.last_accel = None
    self.d_accel = 0.0

  def update(self, accel: float, v_ego: float, guard_pedal: float, use: bool) -> float:
    """One step at the pedal rate. Returns the pedal to send.

    guard_pedal: the guarded stock map's pedal for this step (the fallback and the envelope centre).
    use: the feedforward may act (long PID state, long active, no openpilot or driver brake).
    The lead filter runs every step so it is settled when `use` turns on.
    """
    self.total_steps += 1
    if self.last_accel is None:
      self.last_accel = accel
    rate = (accel - self.last_accel) / self.dt
    self.last_accel = accel
    self.d_accel += (rate - self.d_accel) * self.dt / (LEAD_FILTER_S + self.dt)
    if not use:
      return guard_pedal
    lead = float(np.clip(LEAD_S * self.d_accel, -LEAD_CLAMP, LEAD_CLAMP))
    ff = pedal_for_accel(accel + lead, v_ego)
    ff = float(np.clip(ff, guard_pedal - ENVELOPE, guard_pedal + ENVELOPE))
    w = float(np.interp(v_ego, BLEND_BP, [0.0, 1.0]))
    self.active_steps += 1
    return float(np.clip(w * ff + (1.0 - w) * guard_pedal, 0.0, 1.0))
