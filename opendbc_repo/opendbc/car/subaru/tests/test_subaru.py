import inspect
from collections import defaultdict
from types import SimpleNamespace

import pytest

from opendbc.can import CANPacker, CANParser
from opendbc.car import Bus, structs
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.carcontroller import CarController
from opendbc.car.subaru.carstate import CarState
from opendbc.car.subaru.fingerprints import FW_VERSIONS
from opendbc.car.fw_versions import match_fw_to_car
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR, DBC, CanBus, SubaruFlags, SubaruSafetyFlags
from opendbc.car.structs import CarParams


def make_sng_controller(flags=0, prev_close_distance=4.0):
  controller = object.__new__(CarController)
  controller.CP = SimpleNamespace(flags=flags)
  controller.frame = 60
  controller.last_standstill_frame = 0
  controller.prev_close_distance = prev_close_distance
  controller.epb_resume_frames_remaining = -1
  return controller


def make_sng_state(close_distance=4.0, standstill=True):
  cc = SimpleNamespace(enabled=True, hudControl=SimpleNamespace(leadVisible=True))
  cs = SimpleNamespace(
    close_distance=close_distance,
    out=SimpleNamespace(standstill=standstill),
  )
  return cc, cs


def test_global_sng_keeps_standstill_alive_without_manual_parking_brake_toggle():
  controller = make_sng_controller()
  cc, cs = make_sng_state()

  throttle_cmd, speed_cmd = controller.stop_and_go(cc, cs, manual_parking_brake=False)

  assert throttle_cmd is False
  assert speed_cmd is True


def test_manual_parking_brake_sng_still_sends_resume_throttle():
  controller = make_sng_controller(prev_close_distance=3.9)
  cc, cs = make_sng_state(close_distance=4.0)

  throttle_cmd, speed_cmd = controller.stop_and_go(cc, cs, manual_parking_brake=True)

  assert throttle_cmd is True
  assert speed_cmd is True


def test_preglobal_sng_does_not_send_standstill_keepalive_without_manual_toggle():
  controller = make_sng_controller(flags=SubaruFlags.PREGLOBAL)
  cc, cs = make_sng_state()

  throttle_cmd, speed_cmd = controller.stop_and_go(cc, cs, manual_parking_brake=False)

  assert throttle_cmd is False
  assert speed_cmd is False


class TestSubaruFingerprint:
  def test_fw_version_format(self):
    for platform, fws_per_ecu in FW_VERSIONS.items():
      for (ecu, _, _), fws in fws_per_ecu.items():
        fw_size = len(fws[0])
        for fw in fws:
          if platform in (CAR.SUBARU_ASCENT_2023, CAR.SUBARU_LEGACY_2025) and ecu == CarParams.Ecu.fwdCamera:
            assert len(fw) > 0, f"{platform} {ecu}: empty firmware response"
          else:
            assert len(fw) == fw_size, f"{platform} {ecu}: {len(fw)} {fw_size}"

  def test_outback_2024_firmware(self):
    outback_fw = FW_VERSIONS[CAR.SUBARU_OUTBACK_2023]
    assert b'\xa1 $\x17\x00' in outback_fw[(CarParams.Ecu.abs, 0x7b0, None)]
    assert b'\xfb,\xa2p\x07' in outback_fw[(CarParams.Ecu.engine, 0x7a2, None)]
    assert b'\xa9\x17w!r' in outback_fw[(CarParams.Ecu.transmission, 0x7a3, None)]

    car_fw = [
      CarParams.CarFw(ecu=CarParams.Ecu.abs, fwVersion=b'\xa1 $\x17\x00', address=0x7b0, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.eps, fwVersion=b'+\xc0\x12\x11\x00', address=0x746, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.fwdCamera, fwVersion=b'\t!\x08\x046\x05!\x08\x01/', address=0x787, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.engine, fwVersion=b'\xfb,\xa2p\x07', address=0x7a2, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.transmission, fwVersion=b'\xa9\x17w!r', address=0x7a3, brand="subaru"),
    ]
    exact, matches = match_fw_to_car(car_fw, "4S4BTGUD6R3155987", allow_fuzzy=False, log=False)
    assert exact
    assert matches == {CAR.SUBARU_OUTBACK_2023}

  def test_legacy_2025_firmware(self):
    car_fw = [
      CarParams.CarFw(ecu=CarParams.Ecu.abs, fwVersion=b'\xa1 $\x11\x00', address=0x7b0, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.eps, fwVersion=b'[\xc0\xd1\x10\x00', address=0x746, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.fwdCamera, fwVersion=b'\x1a!\x08\x00C\x0e!\x08\x018', address=0x787, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.fwdCamera, fwVersion=b'\x20\x02\x0e', address=0x787, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.engine, fwVersion=b'\x08,\xa0p\x07', address=0x7a2, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.transmission, fwVersion=b'\xeb\x17U!r', address=0x7a3, brand="subaru"),
    ]
    exact, matches = match_fw_to_car(car_fw, "4S3BWGG67S3011945", allow_fuzzy=False, log=False)
    assert exact
    assert matches == {CAR.SUBARU_LEGACY_2025}

  def test_ascent_2025_firmware(self):
    car_fw = [
      CarParams.CarFw(ecu=CarParams.Ecu.abs, fwVersion=b'\xa5 %\x03\x01', address=0x7b0, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.eps, fwVersion=b'\x55\xc0\xd0\x10', address=0x746, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.fwdCamera, fwVersion=b'\x17!\x08\x01A\x12!\x08\x00;', address=0x787, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.fwdCamera, fwVersion=b'\x20\x02\x0e', address=0x787, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.engine, fwVersion=b'\x11,\xa00\x07', address=0x7a2, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.transmission, fwVersion=b'\x05\xfe\xe7\x00\x00', address=0x7a3, brand="subaru"),
    ]
    exact, matches = match_fw_to_car(car_fw, "4S4WMAAD9S3414980", allow_fuzzy=False, log=False)
    assert exact
    assert matches == {CAR.SUBARU_ASCENT_2023}

  def test_ascent_2025_firmware_without_engine_response(self):
    car_fw = [
      CarParams.CarFw(ecu=CarParams.Ecu.abs, fwVersion=b'\xa5 %\x03\x01', address=0x7b0, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.eps, fwVersion=b'\x55\xc0\xd0\x10', address=0x746, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.fwdCamera, fwVersion=b'\x17!\x08\x01A\x00\x00\x00\x00\x00', address=0x787, brand="subaru"),
    ]
    exact, matches = match_fw_to_car(car_fw, "4S4WMAAD9S3414980", allow_fuzzy=False, log=False)
    assert exact
    assert matches == {CAR.SUBARU_ASCENT_2023}


ANGLE_PLATFORMS = (
  CAR.SUBARU_FORESTER_2022,
  CAR.SUBARU_OUTBACK_2023,
  CAR.SUBARU_LEGACY_2025,
  CAR.SUBARU_ASCENT_2023,
  CAR.SUBARU_CROSSTREK_2025,
)


@pytest.mark.parametrize("platform", ANGLE_PLATFORMS)
def test_angle_platform_params(platform):
  CP = CarInterface.get_non_essential_params(platform)

  assert CP.flags & SubaruFlags.LKAS_ANGLE
  assert CP.steerControlType == CarParams.SteerControlType.angle
  assert CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.LKAS_ANGLE
  assert not CP.dashcamOnly
  assert not CP.alphaLongitudinalAvailable


def test_torque_platform_does_not_enable_angle_safety():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_IMPREZA_2020)

  assert not (CP.flags & SubaruFlags.LKAS_ANGLE)
  assert CP.steerControlType == CarParams.SteerControlType.torque
  assert not (CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.LKAS_ANGLE)


def test_outback_2023_uses_d_platform_bus_layout():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_OUTBACK_2023)
  parsers = CarState.get_can_parsers(CP)
  controller = CarController({}, CP)

  assert CP.flags & SubaruFlags.D_PLATFORM
  assert CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.D_PLATFORM
  assert not (CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.LEGACY_2025_ANGLE_LIMITS)
  assert CanBus.main_for_cp(CP) == CanBus.alt
  assert CanBus.angle_for_cp(CP) == CanBus.main
  assert parsers[Bus.pt].bus == CanBus.alt
  assert parsers[Bus.cam].bus == CanBus.camera
  assert parsers[Bus.alt].bus == CanBus.alt
  assert parsers[Bus.main].bus == CanBus.main
  assert controller.angle_bus == CanBus.main
  assert controller.status_bus == CanBus.main


def test_legacy_2025_uses_gen2_angle_bus_layout():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_LEGACY_2025)
  parsers = CarState.get_can_parsers(CP)
  controller = CarController({}, CP)

  assert not (CP.flags & SubaruFlags.D_PLATFORM)
  assert not (CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.D_PLATFORM)
  assert not (CP.flags & SubaruFlags.D_PLATFORM_CAMERA)
  assert not (CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.D_PLATFORM_CAMERA)
  assert CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.FIXED_ANGLE_LIMITS
  assert CanBus.main_for_cp(CP) == CanBus.main
  assert CanBus.angle_for_cp(CP) == CanBus.main
  assert parsers[Bus.pt].bus == CanBus.main
  assert parsers[Bus.cam].bus == CanBus.camera
  assert parsers[Bus.alt].bus == CanBus.alt
  assert Bus.main not in parsers
  assert controller.angle_bus == CanBus.main
  assert controller.status_bus == CanBus.main


def test_legacy_2025_uses_validated_angle_request_limits():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_LEGACY_2025)
  controller = CarController({}, CP)
  CC = SimpleNamespace(
    enabled=False,
    latActive=False,
    actuators=SimpleNamespace(steeringAngleDeg=-73.05),
  )
  CS = SimpleNamespace(out=SimpleNamespace(
    vEgoRaw=2.4,
    steeringAngleDeg=-75.27,
    steeringRateDeg=0.0,
    steeringPressed=False,
    gearShifter=structs.CarState.GearShifter.drive,
    standstill=False,
  ))

  controller.lateral_angle(CC, CS)
  CC.latActive = True
  msg = controller.lateral_angle(CC, CS)
  parser = CANParser(DBC[CP.carFingerprint][Bus.pt], [("ES_LKAS_ANGLE", 0)], CanBus.main)
  parser.update([(1, [msg])])

  assert parser.can_valid
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 1
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(-73.05)

  CS.out.standstill = True
  msg = controller.lateral_angle(CC, CS)
  parser.update([(2, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(CS.out.steeringAngleDeg)


def test_legacy_2025_engagement_continues_from_last_sent_angle():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_LEGACY_2025)
  controller = CarController({}, CP)
  CC = SimpleNamespace(
    enabled=False,
    latActive=False,
    actuators=SimpleNamespace(steeringAngleDeg=3.17),
  )
  CS = SimpleNamespace(out=SimpleNamespace(
    vEgoRaw=13.9,
    steeringAngleDeg=-0.14,
    steeringRateDeg=0.0,
    steeringPressed=False,
    gearShifter=structs.CarState.GearShifter.drive,
    standstill=False,
  ))
  parser = CANParser(DBC[CP.carFingerprint][Bus.pt], [("ES_LKAS_ANGLE", 0)], CanBus.main)

  msg = controller.lateral_angle(CC, CS)
  parser.update([(1, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(-0.14)

  # CarState can advance between the last inactive command and the first active one.
  # Continue from the command panda accepted rather than skipping ahead to the newer sample.
  CS.out.steeringAngleDeg = -0.09
  CC.latActive = True
  msg = controller.lateral_angle(CC, CS)
  parser.update([(2, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 1
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(0.47)


def test_legacy_2025_waits_for_manual_steering_to_settle_before_reengaging():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_LEGACY_2025)
  controller = CarController({}, CP)
  CC = SimpleNamespace(
    enabled=True,
    latActive=True,
    actuators=SimpleNamespace(steeringAngleDeg=-100.0),
  )
  CS = SimpleNamespace(out=SimpleNamespace(
    vEgoRaw=6.2,
    steeringAngleDeg=-121.55,
    steeringRateDeg=350.0,
    steeringPressed=True,
    gearShifter=structs.CarState.GearShifter.drive,
    standstill=False,
  ))
  parser = CANParser(DBC[CP.carFingerprint][Bus.pt], [("ES_LKAS_ANGLE", 0)], CanBus.main)

  msg = controller.lateral_angle(CC, CS)
  parser.update([(1, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(CS.out.steeringAngleDeg)

  CS.out.steeringPressed = False
  CS.out.steeringAngleDeg = -113.78
  msg = controller.lateral_angle(CC, CS)
  parser.update([(2, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(CS.out.steeringAngleDeg)

  for i in range(9):
    CS.out.steeringAngleDeg += 0.5
    CS.out.steeringRateDeg = 20.0
    msg = controller.lateral_angle(CC, CS)
    parser.update([(3 + i, [msg])])
    assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0
    assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(CS.out.steeringAngleDeg)

  for i in range(6):
    if i % 2:
      CS.out.steeringAngleDeg += 0.5
    CS.out.steeringRateDeg = 0.0 if i % 2 == 0 else 20.0
    msg = controller.lateral_angle(CC, CS)
    parser.update([(12 + i, [msg])])
    assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0
    assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(CS.out.steeringAngleDeg)

  CS.out.steeringRateDeg = 0.0
  for i in range(8):
    msg = controller.lateral_angle(CC, CS)
    parser.update([(18 + i, [msg])])
    assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0

  measured_angle = CS.out.steeringAngleDeg
  msg = controller.lateral_angle(CC, CS)
  parser.update([(26, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 1
  assert abs(parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] - measured_angle) < 0.1


def test_legacy_2025_manual_handoff_reclaim_is_gradual():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_LEGACY_2025)
  controller = CarController({}, CP)
  CC = SimpleNamespace(
    enabled=False,
    latActive=True,
    actuators=SimpleNamespace(steeringAngleDeg=-20.0),
  )
  CS = SimpleNamespace(out=SimpleNamespace(
    vEgoRaw=3.7,
    steeringAngleDeg=2.5,
    steeringRateDeg=-45.0,
    steeringPressed=True,
    gearShifter=structs.CarState.GearShifter.drive,
    standstill=False,
  ))
  parser = CANParser(DBC[CP.carFingerprint][Bus.pt], [("ES_LKAS_ANGLE", 0)], CanBus.main)

  msg = controller.lateral_angle(CC, CS)
  parser.update([(1, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0

  CS.out.steeringPressed = False
  CS.out.steeringRateDeg = 0.0
  for i in range(19):
    msg = controller.lateral_angle(CC, CS)
    parser.update([(2 + i, [msg])])

  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 1
  first_reclaim_angle = parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"]
  assert first_reclaim_angle == pytest.approx(CS.out.steeringAngleDeg, abs=0.1)

  reclaim_angles = []
  for i in range(6):
    msg = controller.lateral_angle(CC, CS)
    parser.update([(20 + i, [msg])])
    reclaim_angles.append(parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"])

  assert all(reclaim_angles[i] >= reclaim_angles[i + 1] for i in range(len(reclaim_angles) - 1))
  assert reclaim_angles[-1] > CC.actuators.steeringAngleDeg


def test_ascent_2023_uses_gen2_angle_bus_layout():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_ASCENT_2023)
  parsers = CarState.get_can_parsers(CP)
  controller = CarController({}, CP)

  assert not (CP.flags & SubaruFlags.D_PLATFORM)
  assert not (CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.D_PLATFORM)
  assert not (CP.flags & SubaruFlags.D_PLATFORM_CAMERA)
  assert not (CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.D_PLATFORM_CAMERA)
  assert CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.FIXED_ANGLE_LIMITS
  assert CanBus.main_for_cp(CP) == CanBus.main
  assert CanBus.angle_for_cp(CP) == CanBus.main
  assert parsers[Bus.pt].bus == CanBus.main
  assert parsers[Bus.cam].bus == CanBus.camera
  assert parsers[Bus.alt].bus == CanBus.alt
  assert Bus.main not in parsers
  assert controller.angle_bus == CanBus.main
  assert controller.status_bus == CanBus.main


def test_other_angle_platforms_keep_existing_bus_layout():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_CROSSTREK_2025)
  parsers = CarState.get_can_parsers(CP)

  assert not (CP.flags & SubaruFlags.D_PLATFORM)
  assert not (CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.D_PLATFORM)
  assert parsers[Bus.pt].bus == CanBus.main
  assert parsers[Bus.cam].bus == CanBus.camera
  assert parsers[Bus.alt].bus == CanBus.alt


def test_angle_controller_tracks_driver_override():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_CROSSTREK_2025)
  controller = CarController({}, CP)
  CC = SimpleNamespace(latActive=True, actuators=SimpleNamespace(steeringAngleDeg=15.0))
  CS = SimpleNamespace(out=SimpleNamespace(vEgoRaw=15.0, steeringAngleDeg=2.0, steeringTorque=250.0))

  msg = controller.lateral_angle(CC, CS)

  assert controller.driver_override
  assert controller.apply_steer_last == CS.out.steeringAngleDeg
  assert msg[0] == 0x124


def test_ascent_angle_controller_uses_fixed_angle_rate_limits():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_ASCENT_2023)
  controller = CarController({}, CP)
  CC = SimpleNamespace(latActive=True, actuators=SimpleNamespace(steeringAngleDeg=-14.88))
  CS = SimpleNamespace(out=SimpleNamespace(
    vEgoRaw=21.66,
    steeringAngleDeg=-25.77,
    steeringRateDeg=0.0,
    steeringTorque=-149.0,
    steeringPressed=False,
  ))
  parser = CANParser(DBC[CP.carFingerprint][Bus.pt], [("ES_LKAS_ANGLE", 0)], CanBus.main)

  msg = controller.lateral_angle(CC, CS)
  parser.update([(1, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 1
  assert CS.out.steeringAngleDeg < parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] < -25.0


def test_ascent_angle_controller_yields_until_manual_steering_settles():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_ASCENT_2023)
  controller = CarController({}, CP)
  CC = SimpleNamespace(latActive=True, actuators=SimpleNamespace(steeringAngleDeg=-10.0))
  CS = SimpleNamespace(out=SimpleNamespace(
    vEgoRaw=21.66,
    steeringAngleDeg=-25.06,
    steeringRateDeg=35.0,
    steeringTorque=-149.0,
    steeringPressed=True,
  ))
  parser = CANParser(DBC[CP.carFingerprint][Bus.pt], [("ES_LKAS_ANGLE", 0)], CanBus.main)

  msg = controller.lateral_angle(CC, CS)
  parser.update([(1, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(CS.out.steeringAngleDeg)

  CS.out.steeringPressed = False
  CS.out.steeringAngleDeg = -17.91
  CS.out.steeringRateDeg = 0.0
  for i in range(18):
    msg = controller.lateral_angle(CC, CS)
    parser.update([(2 + i, [msg])])
    assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 0

  msg = controller.lateral_angle(CC, CS)
  parser.update([(20, [msg])])
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Request"] == 1
  assert parser.vl["ES_LKAS_ANGLE"]["LKAS_Output"] == pytest.approx(CS.out.steeringAngleDeg, abs=0.1)


def test_lkas_hud_state_uses_lateral_active():
  update_source = inspect.getsource(CarController.update)

  assert "create_es_lkas_state(self.packer, self.frame // 10, CS.es_lkas_state_msg, CC.latActive" in update_source
  assert "create_es_lkas_state(self.packer, self.frame // 10, CS.es_lkas_state_msg, CC.enabled" not in update_source


@pytest.mark.parametrize(("enabled", "expected"), ((False, 0), (True, 1)))
def test_lkas_hud_active_bit_follows_lateral_state(enabled, expected):
  dbc = DBC[CAR.SUBARU_LEGACY_2025][Bus.pt]
  packer = CANPacker(dbc)
  parser = CANParser(dbc, [("ES_LKAS_State", 0)], CanBus.main)
  stock_lkas_state = defaultdict(int, {"LKAS_ACTIVE": 1})

  msg = subarucan.create_es_lkas_state(
    packer, 0, stock_lkas_state, enabled, 0, False, False, False, False, CanBus.main,
  )
  parser.update([(1, [msg])])

  assert parser.can_valid
  assert parser.vl["ES_LKAS_State"]["LKAS_ACTIVE"] == expected
