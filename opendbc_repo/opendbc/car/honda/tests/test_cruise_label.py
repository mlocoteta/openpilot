"""Accord 9G dash set-speed label (7.0 port of 6.x F06 dash half, ce2fa4a56): set 70 mph must read "70", not "71"."""
import math

import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.honda import carcontroller
from opendbc.car.honda.hondacan import imperial_cluster_cruise_kph
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR


def cluster_mph(kph: int) -> int:
  # 9G Accord cluster: whole kph from ACC_HUD, shown as mph rounded up
  return math.ceil(kph / CV.MPH_TO_KPH)


class TestImperialClusterCruiseKph:
  def test_floor_identity(self):
    for mph in range(1, 161):
      assert cluster_mph(math.floor(mph * CV.MPH_TO_KPH)) == mph

  def test_every_mph_reads_back(self):
    for mph in range(1, 161):
      kph = imperial_cluster_cruise_kph(mph * CV.MPH_TO_MS)
      assert 0 < kph <= 250  # 252 = stopped, 255 = no speed
      if mph <= 155:
        assert cluster_mph(kph) == mph, (mph, kph)

  def test_old_grid_and_float_noise(self):
    # 1.6 kph grid values (pre-exact-mph) and float noise land on the same mph
    for mph in range(1, 156):
      for kph_in in (mph * 1.6, mph * CV.MPH_TO_KPH - 1e-9, mph * CV.MPH_TO_KPH + 1e-9):
        if round(kph_in / CV.MPH_TO_KPH) != mph:
          continue
        assert cluster_mph(imperial_cluster_cruise_kph(kph_in * CV.KPH_TO_MS)) == mph

  def test_reported_cases(self):
    assert imperial_cluster_cruise_kph(70 * CV.MPH_TO_MS) == 112
    assert imperial_cluster_cruise_kph(65 * CV.MPH_TO_MS) == 104
    # the old path: round-to-nearest in the packer gave 113 / 105 = "71" / "66"
    assert cluster_mph(round(70 * CV.MPH_TO_KPH)) == 71
    assert cluster_mph(round(65 * CV.MPH_TO_KPH)) == 66


# The carcontroller sends imperial_cluster_cruise_kph on the 9G only (imperial, Nidec HUD units).

CREATE_ACC_HUD = carcontroller.hondacan.create_acc_hud


def sent_cruise_speed(monkeypatch, identity, set_mph, is_metric=False):
  fp = gen_empty_fingerprint()
  fp[0][0x201] = 6
  cp = CarInterface.get_params(identity, fp, [], False, False, False)
  ci = CarInterface(cp)
  ci.update([])
  ci.CS.is_metric = is_metric
  sent = []

  def capture(packer, bus, CP, enabled, pcm_speed, pcm_accel, hud_control, hud_v_cruise, *args):
    sent.append(hud_v_cruise)
    return CREATE_ACC_HUD(packer, bus, CP, enabled, pcm_speed, pcm_accel, hud_control, hud_v_cruise, *args)

  monkeypatch.setattr(carcontroller.hondacan, "create_acc_hud", capture)
  cc = structs.CarControl(enabled=True, longActive=True)
  cc.hudControl.speedVisible = True
  cc.hudControl.setSpeed = set_mph * CV.MPH_TO_MS
  cc = cc.as_reader()
  for tick in range(20):
    ci.apply(cc, 1_000_000_000 + tick * 10_000_000)
  assert sent
  return sent[-1]


@pytest.mark.parametrize("mph,kph", [(70, 112), (65, 104), (25, 40), (55, 88)])
def test_9g_dash_label_reads_set_speed(monkeypatch, mph, kph):
  value = sent_cruise_speed(monkeypatch, CAR.HONDA_ACCORD_9G, mph)
  assert value == kph
  assert cluster_mph(value) == mph


def test_9g_metric_unchanged(monkeypatch):
  value = sent_cruise_speed(monkeypatch, CAR.HONDA_ACCORD_9G, 70, is_metric=True)
  assert value == pytest.approx(70 * CV.MPH_TO_KPH)


def test_other_nidec_unchanged(monkeypatch):
  value = sent_cruise_speed(monkeypatch, CAR.HONDA_CIVIC, 70)
  assert value == pytest.approx(70 * CV.MPH_TO_KPH)
