import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus, gen_empty_fingerprint
from opendbc.car.hyundai.interface import CarInterface
from opendbc.car.hyundai.radar_interface import (STINGER_2022_EGO_SPEED_OFFSET, RadarInterface, decode_stinger_2022_triplet,
                                                 get_radar_can_parser, Stinger2022ObjectDecoder)
from opendbc.car.hyundai.values import CAR, DBC

STINGER_ADDRS = range(0x238, 0x256)
# Golden triplet payloads (object_id=24, distance=10.85, lateral=-0.2, absolute_speed=5.15)
GOLDEN = tuple(bytes.fromhex(dat) for dat in ("06ca7fcb8379f530", "8fc973d946180b18", "89504654ffe604e8"))


def stinger_fingerprint(addrs=STINGER_ADDRS, length=8):
  fp = gen_empty_fingerprint()
  for addr in addrs:
    fp[1][addr] = length
  return fp


def stinger_triplet(absolute_speed: float, lateral: float = -0.2):
  # Golden triplet with the speed and lateral fields rewritten
  a, b, c = GOLDEN
  raw = int.from_bytes(a, "big")
  for start, size, value in ((16, 12, round((lateral + 102.4) / 0.05)), (32, 12, round((absolute_speed + 100.0) / 0.05))):
    shift = 64 - start - size
    raw = (raw & ~(((1 << size) - 1) << shift)) | (value << shift)
  return decode_stinger_2022_triplet(0, (raw.to_bytes(8, "big"), b, c))


class TestStingerRadar:
  def test_golden_triplet(self):
    obj = decode_stinger_2022_triplet(0, GOLDEN)
    assert obj.object_id == 24
    assert obj.distance == pytest.approx(10.85)
    assert obj.lateral_raw == pytest.approx(-0.2)
    assert obj.absolute_speed == pytest.approx(5.15)

  def test_triplet_rejects_inconsistent_frames(self):
    a, b, c = GOLDEN
    assert decode_stinger_2022_triplet(0, (a, b)) is None
    assert decode_stinger_2022_triplet(10, GOLDEN) is None
    assert decode_stinger_2022_triplet(0, (a, b, c[:7])) is None
    assert decode_stinger_2022_triplet(0, (a, c, b)) is None
    assert decode_stinger_2022_triplet(0, (bytes(8),) * 3) is None

  def test_decoder_requires_fresh_complete_triplet(self):
    dec = Stinger2022ObjectDecoder()
    assert dec.update(1_000_000_000, 0x238, GOLDEN[0], 1) is None
    assert dec.update(1_000_000_000, 0x239, GOLDEN[1], 1) is None
    assert dec.update(1_000_000_000, 0x23A, GOLDEN[2], 0) is None  # wrong bus
    obj = dec.update(1_000_000_000, 0x23A, GOLDEN[2], 1)
    assert obj is not None and obj.object_id == 24
    # the cycle was consumed: a repeated last frame cannot reuse old parts
    assert dec.update(1_020_000_000, 0x23A, GOLDEN[2], 1) is None
    # parts further apart than 20 ms are rejected
    dec.update(2_000_000_000, 0x238, GOLDEN[0], 1)
    dec.update(2_000_000_000, 0x239, GOLDEN[1], 1)
    assert dec.update(2_030_000_000, 0x23A, GOLDEN[2], 1) is None

  @pytest.mark.parametrize("absolute_speed, lateral, settled", [
    (-0.45, -0.2, 0.0),    # in-path lead settling after braking to a stop
    (-0.65, 1.5, 0.0),
    (-0.75, -0.2, -0.75),  # beyond the undershoot band: measured reversal
    (-0.45, 3.0, -0.45),   # adjacent lane: left as measured
    (-2.5, 5.0, -2.5),     # oncoming traffic
    (0.0, -0.2, 0.0),
    (1.2, -0.2, 1.2),
  ])
  def test_stopped_lead_undershoot(self, absolute_speed, lateral, settled):
    obj = stinger_triplet(absolute_speed, lateral)
    assert obj.absolute_speed == pytest.approx(absolute_speed)
    assert obj.settled_absolute_speed() == pytest.approx(settled)
    assert obj.relative_speed(5.0) == pytest.approx(settled - (5.0 - STINGER_2022_EGO_SPEED_OFFSET))

  @pytest.mark.parametrize("ego_speed, offset", [
    (0.0, 0.0),
    (0.5, 0.5 * STINGER_2022_EGO_SPEED_OFFSET),
    (1.0, STINGER_2022_EGO_SPEED_OFFSET),
    (30.0, STINGER_2022_EGO_SPEED_OFFSET),
  ])
  def test_ego_speed_offset(self, ego_speed, offset):
    obj = stinger_triplet(1.2)
    assert obj.relative_speed(ego_speed) == pytest.approx(1.2 - ego_speed + offset)

  def test_radar_unavailable_follows_fingerprint(self):
    assert not CarInterface.get_params(CAR.KIA_STINGER_2022, stinger_fingerprint(), [], False, False, False).radarUnavailable
    assert CarInterface.get_params(CAR.KIA_STINGER_2022, gen_empty_fingerprint(), [], False, False, False).radarUnavailable
    for missing in (0x238, 0x247, 0x255):
      fp = stinger_fingerprint()
      del fp[1][missing]
      assert CarInterface.get_params(CAR.KIA_STINGER_2022, fp, [], False, False, False).radarUnavailable
    # wrong length, or the bank on the wrong bus
    assert CarInterface.get_params(CAR.KIA_STINGER_2022, stinger_fingerprint(length=24), [], False, False, False).radarUnavailable
    fp = gen_empty_fingerprint()
    fp[0].update(dict.fromkeys(STINGER_ADDRS, 8))
    assert CarInterface.get_params(CAR.KIA_STINGER_2022, fp, [], False, False, False).radarUnavailable

  def test_other_cars_unaffected(self):
    for car in (CAR.KIA_STINGER, CAR.HYUNDAI_SONATA, CAR.GENESIS_G80):
      cp = CarInterface.get_params(car, stinger_fingerprint(), [], False, False, False)
      assert cp.radarUnavailable
      assert not RadarInterface(cp).stinger_2022
    assert get_radar_can_parser(CarInterface.get_params(CAR.KIA_STINGER, stinger_fingerprint(), [], False, False, False)) is None

  def test_radar_interface(self):
    CP = CarInterface.get_params(CAR.KIA_STINGER_2022, stinger_fingerprint(), [], False, False, False)
    assert not CP.radarUnavailable
    radar = RadarInterface(CP)
    assert radar.trigger_msg == 0x255
    packer = CANPacker(DBC[CP.carFingerprint][Bus.pt])

    # Before WHL_SPD11 is received, the radar reports canError and no points
    startup_data = radar.update([(900_000_000, [(0x255, bytes(8), 1)])])
    assert startup_data is not None
    assert startup_data.errors.canError
    assert len(startup_data.points) == 0

    whl_msg = packer.make_can_msg("WHL_SPD11", 0, {"WHL_SPD_FL": 50.0, "WHL_SPD_FR": 50.0, "WHL_SPD_RL": 50.0, "WHL_SPD_RR": 50.0})
    can_frames = [(whl_msg[0], whl_msg[1], 0)]
    can_frames += [(0x238 + i, payload, 1) for i, payload in enumerate(GOLDEN)]
    can_frames.append((0x255, bytes(8), 1))  # trigger

    radar_data = radar.update([(1_000_000_000, can_frames)])
    assert radar_data is not None
    assert not radar_data.errors.canError
    assert len(radar_data.points) == 1
    pt = radar_data.points[0]
    assert pt.dRel == pytest.approx(10.85)
    assert pt.yRel == pytest.approx(0.2)  # left-positive in the car frame: -lateral_raw
    v_ego = 50.0 * (1000.0 / 3600.0)
    assert pt.vRel == pytest.approx(5.15 - (v_ego - STINGER_2022_EGO_SPEED_OFFSET))

    # A cycle without the object drops the track
    radar_data2 = radar.update([(1_050_000_000, [(0x255, bytes(8), 1)])])
    assert radar_data2 is not None
    assert len(radar_data2.points) == 0

  def test_error_cycle_discards_objects(self):
    CP = CarInterface.get_params(CAR.KIA_STINGER_2022, stinger_fingerprint(), [], False, False, False)
    radar = RadarInterface(CP)
    packer = CANPacker(DBC[CP.carFingerprint][Bus.pt])

    # An object decoded while the cycle errors out (no wheel speed yet) is not carried into the next cycle
    error_frames = [(0x238 + i, payload, 1) for i, payload in enumerate(GOLDEN)] + [(0x255, bytes(8), 1)]
    error_data = radar.update([(1_000_000_000, error_frames)])
    assert error_data is not None and error_data.errors.canError

    whl_msg = packer.make_can_msg("WHL_SPD11", 0, {"WHL_SPD_FL": 50.0, "WHL_SPD_FR": 50.0, "WHL_SPD_RL": 50.0, "WHL_SPD_RR": 50.0})
    radar_data = radar.update([(1_050_000_000, [(whl_msg[0], whl_msg[1], 0), (0x255, bytes(8), 1)])])
    assert radar_data is not None
    assert not radar_data.errors.canError
    assert len(radar_data.points) == 0

  def test_no_trigger_no_output(self):
    CP = CarInterface.get_params(CAR.KIA_STINGER_2022, stinger_fingerprint(), [], False, False, False)
    radar = RadarInterface(CP)
    assert radar.update([(1_000_000_000, [(0x238, GOLDEN[0], 1)])]) is None
    radar_unavailable = RadarInterface(CarInterface.get_params(CAR.KIA_STINGER_2022, gen_empty_fingerprint(), [], False, False, False))
    assert radar_unavailable.update([(1_000_000_000, [(0x255, bytes(8), 1)])]) is None
