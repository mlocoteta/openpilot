from types import SimpleNamespace

import pytest

from openpilot.common.hardware.comma import hardware as comma_hardware
from openpilot.starpilot.system import big_core_freq
from openpilot.starpilot.system.big_core_freq import BIG_CLUSTER_MAX_KHZ, PARAM, UPSTREAM_MAX_KHZ, big_core_max_khz


class FakeParams:
  def __init__(self, value=None, error=None):
    self.value, self.error = value, error

  def get(self, key, return_default=False):
    assert key == PARAM and return_default
    if self.error is not None:
      raise self.error
    return self.value


@pytest.mark.parametrize("value,expected", [
  (None, UPSTREAM_MAX_KHZ),
  (0, UPSTREAM_MAX_KHZ),
  (-5, UPSTREAM_MAX_KHZ),
  (1000000, UPSTREAM_MAX_KHZ),          # never below the upstream cap
  (2400000, 2400000),
  (2419200, 2419200),
  (9999999, BIG_CLUSTER_MAX_KHZ),
])
def test_big_core_max_khz(value, expected):
  assert big_core_max_khz(FakeParams(value)) == expected


def test_unknown_key_or_bad_value_falls_back_to_upstream():
  assert big_core_max_khz(FakeParams(error=KeyError(PARAM))) == UPSTREAM_MAX_KHZ
  assert big_core_max_khz(FakeParams("fast")) == UPSTREAM_MAX_KHZ


def test_registered_default_raises_big_cluster():
  from openpilot.common.params import Params
  from openpilot.common.prefix import OpenpilotPrefix
  with OpenpilotPrefix():
    assert big_core_max_khz() == 2400000
    Params().put(PARAM, 0)
    assert big_core_max_khz() == UPSTREAM_MAX_KHZ


@pytest.mark.parametrize("khz", [UPSTREAM_MAX_KHZ, 2400000])
def test_set_power_save_caps_little_cluster_upstream_and_big_cluster_from_param(monkeypatch, khz):
  writes = []
  monkeypatch.setattr(comma_hardware, 'sudo_write', lambda val, path: writes.append((path, val)))
  monkeypatch.setattr(comma_hardware, 'affine_irq', lambda *a: None)
  monkeypatch.setattr(big_core_freq, 'big_core_max_khz', lambda params=None: khz)
  comma_hardware.HardwareComma.set_power_save(SimpleNamespace(amplifier=None), False)
  caps = {p: v for p, v in writes if p.endswith('scaling_max_freq')}
  assert caps == {
    '/sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq': '1689600',
    '/sys/devices/system/cpu/cpufreq/policy4/scaling_max_freq': str(khz),
  }
  # governors and core onlining unchanged
  assert ('/sys/devices/system/cpu/cpufreq/policy4/scaling_governor', 'performance') in writes
  assert ('/sys/devices/system/cpu/cpu4/online', '1') in writes


def test_power_save_writes_no_cap(monkeypatch):
  writes = []
  monkeypatch.setattr(comma_hardware, 'sudo_write', lambda val, path: writes.append((path, val)))
  monkeypatch.setattr(comma_hardware, 'affine_irq', lambda *a: None)
  comma_hardware.HardwareComma.set_power_save(SimpleNamespace(amplifier=None), True)
  assert not [p for p, _ in writes if p.endswith('scaling_max_freq')]
