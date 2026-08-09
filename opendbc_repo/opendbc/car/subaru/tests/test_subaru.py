from types import SimpleNamespace

import pytest

from opendbc.car import Bus
from opendbc.car.subaru.carcontroller import CarController
from opendbc.car.subaru.carstate import CarState
from opendbc.car.subaru.fingerprints import FW_VERSIONS
from opendbc.car.fw_versions import match_fw_to_car
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR, CanBus, SubaruFlags, SubaruSafetyFlags
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
    legacy_fw = FW_VERSIONS[CAR.SUBARU_LEGACY_2025]
    car_fw = [
      CarParams.CarFw(ecu=CarParams.Ecu.abs, fwVersion=b'\xa1 $\x11\x00', address=0x7b0, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.eps, fwVersion=b'[\xc0\xd1\x10\x00', address=0x746, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.fwdCamera, fwVersion=b'\x1a!\x08\x00C\x0e!\x08\x018', address=0x787, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.engine, fwVersion=b'\x08,\xa0p\x07', address=0x7a2, brand="subaru"),
      CarParams.CarFw(ecu=CarParams.Ecu.transmission, fwVersion=b'\xeb\x17U!r', address=0x7a3, brand="subaru"),
    ]
    exact, matches = match_fw_to_car(car_fw, "4S3BWGG67S3011945", allow_fuzzy=False, log=False)
    assert exact
    assert matches == {CAR.SUBARU_LEGACY_2025}


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
  assert CanBus.main_for_cp(CP) == CanBus.alt
  assert CanBus.angle_for_cp(CP) == CanBus.main
  assert parsers[Bus.pt].bus == CanBus.alt
  assert parsers[Bus.cam].bus == CanBus.camera
  assert parsers[Bus.alt].bus == CanBus.alt
  assert parsers[Bus.main].bus == CanBus.main
  assert controller.angle_bus == CanBus.main
  assert controller.status_bus == CanBus.camera


def test_legacy_2025_uses_d_platform_bus_layout():
  CP = CarInterface.get_non_essential_params(CAR.SUBARU_LEGACY_2025)
  parsers = CarState.get_can_parsers(CP)
  controller = CarController({}, CP)

  assert CP.flags & SubaruFlags.D_PLATFORM
  assert CP.safetyConfigs[0].safetyParam & SubaruSafetyFlags.D_PLATFORM
  assert CanBus.main_for_cp(CP) == CanBus.alt
  assert CanBus.angle_for_cp(CP) == CanBus.main
  assert parsers[Bus.pt].bus == CanBus.alt
  assert parsers[Bus.cam].bus == CanBus.camera
  assert parsers[Bus.alt].bus == CanBus.alt
  assert parsers[Bus.main].bus == CanBus.main
  assert controller.angle_bus == CanBus.main
  assert controller.status_bus == CanBus.camera


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
