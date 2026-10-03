import numpy as np
import pytest

from opendbc.car.honda import pedal_learner as PL
from opendbc.car.honda.pedal_learner import PedalGasFactorGuard, applied_gas_factor, clamp_gas_factor


def steady(guard, gf, n, cmd=1.0, a_ego=0.5, v=20.0, braking=False, hill=0.0, allowed=True):
  for _ in range(n):
    gf = guard.update(gf, cmd, a_ego, v, cmd / 4.8, braking, hill, allowed)
  return gf


def test_start_is_clamped_to_band():
  assert PedalGasFactorGuard(1.12).start == PL.GAS_FACTOR_MIN
  assert PedalGasFactorGuard(2.69).start == PL.GAS_FACTOR_MAX
  assert PedalGasFactorGuard(1.4).start == 1.4
  assert clamp_gas_factor(float("nan")) == PL.GAS_FACTOR_DEFAULT


def test_learns_slowly_in_steady_conditions():
  g = PedalGasFactorGuard(1.4)
  gf = steady(g, 1.4, 50)        # 1 s of +0.5 m/s^2 under-delivery at 1 m/s^2, 20 m/s
  # stock (/150) adds 0.0033 per step (+0.17 per s); the guard 0.00033 after the 0.5 s settle window
  assert gf == pytest.approx(1.4 + 26 * 0.5 / PL.LEARN_DIV * 1.0, abs=1e-6)
  assert g.counts["ok"] == 26 and g.counts["cmd_change"] == 24
  gf = steady(g, gf, 50 * 10)    # +0.10 after ~6 s, then the per-drive limit holds it
  assert gf == pytest.approx(1.5) and g.counts["ok"] == 300 and g.counts["drive_limit"] > 200


def test_per_drive_change_limit_and_band():
  g = PedalGasFactorGuard(1.4)
  assert steady(g, 1.4, 50 * 600) == pytest.approx(1.5)                 # +0.10 per drive
  g = PedalGasFactorGuard(1.4)
  assert steady(g, 1.4, 50 * 600, cmd=0.6, a_ego=1.4) == pytest.approx(1.3)  # -0.10 per drive
  g = PedalGasFactorGuard(1.58)
  assert steady(g, 1.58, 50 * 600) == pytest.approx(PL.GAS_FACTOR_MAX)


@pytest.mark.parametrize("kwargs,reason", [
  ({"v": 5.0}, "speed"),
  ({"cmd": 0.1, "a_ego": -0.5}, "gas"),
  ({"hill": 0.8}, "hill"),
  ({"cmd": 2.0, "a_ego": 0.2}, "error"),
  ({"allowed": False}, "inactive"),
])
def test_rejected_samples_do_not_move_the_factor(kwargs, reason):
  g = PedalGasFactorGuard(1.4)
  assert steady(g, 1.4, 50 * 30, **kwargs) == 1.4
  assert g.counts[reason] > 0 and g.counts["ok"] == 0


def test_brake_holdoff_and_rising_command():
  g = PedalGasFactorGuard(1.4)
  gf = steady(g, 1.4, 10, braking=True)
  gf = steady(g, gf, PL.BRAKE_HOLDOFF_STEPS - 1)
  assert gf == 1.4 and g.counts["ok"] == 0
  # A ramping command (pedal-lag phase, 31a seg 24) is rejected.
  g = PedalGasFactorGuard(1.4)
  gf = 1.4
  for k in range(200):
    cmd = 0.3 + 0.02 * k
    gf = g.update(gf, cmd, cmd - 0.6, 15.0, cmd / 4.8, False, 0.0, True)
  assert gf == 1.4 and g.counts["cmd_change"] > 150


def test_applied_factor_low_speed_cap():
  assert applied_gas_factor(1.6, 0.0) == pytest.approx(1.0)
  assert applied_gas_factor(1.6, 6.0) == pytest.approx(1.0)
  assert applied_gas_factor(1.6, 9.0) == pytest.approx(1.3)
  assert applied_gas_factor(1.6, 12.0) == pytest.approx(1.6)
  assert applied_gas_factor(1.25, 30.0) == pytest.approx(1.25)
  assert all(applied_gas_factor(1.6, v) <= 1.6 for v in np.linspace(0, 40, 41))


def test_noise_does_not_random_walk():
  # 10 min of zero-mean aEgo noise (sigma 0.4) at steady cruise: stock random-walks, the guard barely moves.
  rng = np.random.default_rng(0)
  g = PedalGasFactorGuard(1.4)
  gf, stock = 1.4, 1.4
  for _ in range(50 * 600):
    a = 0.6 + rng.normal(0, 0.4)
    gf = g.update(gf, 0.6, a, 25.0, 0.6 / 4.8, False, 0.0, True)
    stock = float(np.clip(stock + (0.6 - a) / 150.0 * 0.6, 0.1, 3.0))
  assert abs(gf - 1.4) < 0.05
