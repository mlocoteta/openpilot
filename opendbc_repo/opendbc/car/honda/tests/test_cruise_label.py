import math

from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.honda.hondacan import imperial_cluster_cruise_kph


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
