"""The 9G Accord (2016-17, 4-cyl) fingerprints by FW, with the versions the old SSV2 branches matched it on.

Old lists: mlocoteta/openpilot sunnypilot_SSV2 077d7091e16 (second ACCORD_NIDEC_4_CYL dict, the one in effect) and
master_SSV2_0.9 94f6c85cb2e (ACCORD_NIDEC): identical. The 2023 port ac9315f6a70 had only the first version of each.
Honda has no CAN fingerprints any more, so FW is the only automatic path. The old lists also had the combination meter
(78109-T2F-L110/L010); that ECU is a data-collection ECU in current opendbc (not allowed in FW_VERSIONS) and is only
logged. Without it the match is looser than in 2023, never stricter, so a car that matched then matches now.
"""
import itertools

import pytest

from opendbc.car.fingerprints import FW_VERSIONS
from opendbc.car.fw_versions import match_fw_to_car
from opendbc.car.honda.values import CAR
from opendbc.car.structs import CarParams

CarFw = CarParams.CarFw
Ecu = CarParams.Ecu

RADAR = (Ecu.fwdRadar, 0x18dab0f1)
VSA = (Ecu.vsa, 0x18da28f1)
SRS = (Ecu.srs, 0x18da53f1)
METER = (Ecu.combinationMeter, 0x18da60f1)

OLD_9G_4CYL = {
  RADAR: [b'36161-T2F-A140\x00\x00'],
  VSA: [b'57114-T2F-X840\x00\x00', b'57114-T2F-X830\x00\x00'],
  METER: [b'78109-T2F-L110\x00\x00', b'78109-T2F-L010\x00\x00'],
  SRS: [b'77959-T2F-A030\x00\x00', b'77959-T2F-A020\x00\x00'],
}

# Other old 9G variants: not this car and not supported as HONDA_ACCORD_9G on this branch
OLD_9G_V6 = {RADAR: b'36161-T3M-A340\x00\x00', VSA: b'57114-T3M-X840\x00\x00', METER: b'78109-T3M-A310\x00\x00',
             SRS: b'77959-T3L-C030\x00\x00'}
OLD_9G_HYBRID = {(Ecu.gateway, 0x18daeff1): b'38897-T3W-0130\x00\x00', RADAR: b'36161-T3Z-A830\x00\x00',
                 METER: b'78109-T3Z-A220\x00\x00', SRS: b'77959-T3Z-A020\x00\x00'}


def car_fw(versions: dict) -> list[CarFw]:
  return [CarFw(ecu=ecu, fwVersion=version, address=addr, subAddress=0, brand='honda', request=[], responseAddress=addr + 8)
          for (ecu, addr), version in versions.items()]


def old_combinations():
  ecus = list(OLD_9G_4CYL)
  for versions in itertools.product(*(OLD_9G_4CYL[ecu] for ecu in ecus)):
    yield dict(zip(ecus, versions, strict=True))


class TestAccord9GFingerprint:
  @pytest.mark.parametrize("versions", list(old_combinations()))
  def test_old_versions_match_exactly(self, versions):
    exact, matches = match_fw_to_car(car_fw(versions), "", allow_fuzzy=False)
    assert exact and matches == {CAR.HONDA_ACCORD_9G}

  @pytest.mark.parametrize("missing", [METER, VSA])
  def test_non_essential_ecu_may_be_missing(self, missing):
    versions = next(old_combinations())
    del versions[missing]
    exact, matches = match_fw_to_car(car_fw(versions), "", allow_fuzzy=False)
    assert exact and matches == {CAR.HONDA_ACCORD_9G}

  def test_radar_required(self):
    versions = next(old_combinations())
    del versions[RADAR]
    _, matches = match_fw_to_car(car_fw(versions), "", allow_fuzzy=False)
    assert CAR.HONDA_ACCORD_9G not in matches

  @pytest.mark.parametrize("ecu, version", [(RADAR, b'36161-T2F-A240\x00\x00'), (SRS, b'77959-T2F-A040\x00\x00'),
                                            (VSA, b'57114-T2F-X850\x00\x00')])
  def test_unknown_version_no_exact_match(self, ecu, version):
    versions = next(old_combinations())
    versions[ecu] = version
    _, matches = match_fw_to_car(car_fw(versions), "", allow_fuzzy=False)
    assert CAR.HONDA_ACCORD_9G not in matches

  def test_fuzzy_agrees(self):
    for versions in old_combinations():
      _, matches = match_fw_to_car(car_fw(versions), "", allow_exact=False)
      assert matches == {CAR.HONDA_ACCORD_9G}

  @pytest.mark.parametrize("versions", [OLD_9G_V6, OLD_9G_HYBRID], ids=["v6", "hybrid"])
  def test_other_9g_variants_not_matched(self, versions):
    _, matches = match_fw_to_car(car_fw(versions), "")
    assert CAR.HONDA_ACCORD_9G not in matches

  def test_versions_unique_to_9g(self):
    ours = {v for vs in FW_VERSIONS[CAR.HONDA_ACCORD_9G].values() for v in vs}
    for car, ecus in FW_VERSIONS.items():
      if car == CAR.HONDA_ACCORD_9G:
        continue
      shared = ours & {v for vs in ecus.values() for v in vs}
      assert not shared, f"{car} shares 9G FW versions {shared}"

  @pytest.mark.parametrize("car", [c for c in CAR if c != CAR.HONDA_ACCORD_9G and c in FW_VERSIONS])
  def test_other_hondas_never_9g(self, car):
    # every version of every other Honda in the database: the first and the last of each ECU list
    for pick in (0, -1):
      versions = {(ecu, addr): vs[pick] for (ecu, addr, _), vs in FW_VERSIONS[car].items()}
      _, matches = match_fw_to_car(car_fw(versions), "")
      assert CAR.HONDA_ACCORD_9G not in matches
