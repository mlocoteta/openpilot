import pytest

from cereal import custom

from opendbc.can import CANPacker, CANParser
from opendbc.car import Bus, structs
from opendbc.car.fw_versions import match_fw_to_car
from opendbc.car.tesla.carcontroller import CarController
from opendbc.car.tesla.carstate import CarState
from opendbc.car.tesla.fingerprints import FW_VERSIONS
from opendbc.car.tesla.interface import CarInterface
from opendbc.car.tesla.teslacan_legacy import TeslaCANRaven
from opendbc.car.tesla.values import CANBUS, CAR, DBC, TeslaSafetyFlags


def test_hw1_is_distinct_from_preap_and_does_not_change_can_buses():
  preap = CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_PREAP)
  hw1 = CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_HW1)

  assert preap.safetyConfigs[0].safetyModel == structs.CarParams.SafetyModel.teslaPreAP
  assert hw1.safetyConfigs[0].safetyModel == structs.CarParams.SafetyModel.tesla
  assert hw1.safetyConfigs[0].safetyParam == TeslaSafetyFlags.FLAG_HW1.value
  assert hw1.radarTimeStepDEPRECATED == pytest.approx(0.125)
  assert preap.radarTimeStepDEPRECATED == pytest.approx(0.05)
  assert CANBUS.party == 0 and CANBUS.autopilot_party == 2
  assert CarState.get_can_parsers(hw1)[Bus.ap_pt].bus == 2
  assert CarState.get_can_parsers(hw1)[Bus.chassis].message_states[0x211].ignore_alive
  assert CarState.get_can_parsers(preap)[Bus.party].bus == 0


def test_hw1_requires_explicit_alpha_long_for_acceleration():
  ret = CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_HW1)
  hw1 = CarInterface._get_params(ret, CAR.TESLA_MODEL_S_HW1, {0: {0x201: 5}}, [], True, False, False)
  assert hw1.openpilotLongitudinalControl
  assert hw1.safetyConfigs[0].safetyParam == TeslaSafetyFlags.FLAG_HW1.value | TeslaSafetyFlags.LONG_CONTROL.value


def test_ap1_eps_fw_matches_hw1_without_matching_preap():
  version = FW_VERSIONS[CAR.TESLA_MODEL_S_HW1][(structs.CarParams.Ecu.eps, 0x730, None)][0]
  fw = structs.CarParams.CarFw(ecu=structs.CarParams.Ecu.eps, address=0x730, brand="tesla", fwVersion=version)
  exact, candidates = match_fw_to_car([fw], "", log=False)
  assert exact and candidates == {CAR.TESLA_MODEL_S_HW1}


def test_hw1_display_and_cruise_bytes_do_not_change_preap_signals():
  # Captured bus-0 DI_state (0x368) from the AP1 route: display 9 MPH, set speed 10 MPH.
  parser = CANParser("tesla_can", [(0x368, 0)], 0)
  parser.message_states[0x368].ignore_counter = True
  frames = [(0x368, bytes.fromhex("84185e3009980a2d"), 0)]
  parser.update([(1_000_000_000, frames)])
  parser.update([(2_000_000_000, frames)])
  state = parser.vl["DI_state"]
  assert state["DI_hw1DigitalSpeed"] == 9
  assert state["DI_hw1CruiseSet"] == 10
  assert state["DI_digitalSpeed"] == 10
  assert state["DI_cruiseSet"] != 10


def test_hw1_packer_emits_bus_zero_with_matching_checksums():
  packer = CANPacker(DBC[CAR.TESLA_MODEL_S_HW1][Bus.party])
  tesla_can = TeslaCANRaven({CANBUS.party: packer})
  for msg, expected_addr, checksum_index in (
    (tesla_can.create_steering_control(0, 0, False), 0x488, 3),
    (tesla_can.create_longitudinal_command(13, 0, 0, 10, False, False), 0x2b9, 7),
  ):
    addr, data, bus = msg
    assert addr == expected_addr and bus == 0
    assert data[checksum_index] == TeslaCANRaven.checksum(addr, data[:checksum_index])


def test_hw1_cancel_clears_acceleration_and_does_not_request_max_speed():
  cp = CarInterface._get_params(CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_HW1),
                                CAR.TESLA_MODEL_S_HW1, {0: {}}, [], True, False, False)
  controller = CarController(DBC[CAR.TESLA_MODEL_S_HW1], cp)
  state = CarState(cp, custom.StarPilotCarParams.new_message())
  state.out.vEgo = 10.
  cc = structs.CarControl.new_message()
  cc.longActive = True
  cc.cruiseControl.cancel = True
  cc.actuators.accel = 2.
  _, sends = controller.update(cc.as_reader(), state, 0, None)
  _, data, bus = next(msg for msg in sends if msg[0] == 0x2b9)
  assert bus == 0
  parser = CANParser("tesla_can", [(0x2b9, 0)], 0)
  parser.update([(1_000_000_000, [(0x2b9, data, bus)])])
  decoded = parser.vl["DAS_control"]
  assert decoded["DAS_accState"] == 13
  assert decoded["DAS_accelMin"] == pytest.approx(0, abs=0.05)
  assert decoded["DAS_accelMax"] == pytest.approx(0, abs=0.05)
  assert decoded["DAS_setSpeed"] != 200


def test_hw1_carstate_uses_ap1_powertrain_and_chassis():
  cp = CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_HW1)
  parsers = CarState.get_can_parsers(cp)
  frames = [
    (0x155, bytes.fromhex("000000000005e308"), 0),  # ESP speed 15.07 kph
    (0x368, bytes.fromhex("84185e3009980a2d"), 0),
    (0x201, bytes.fromhex("5444008df2"), 0),
  ]
  for parser in parsers.values():
    for addr in (0x155, 0x368, 0x201):
      _ = parser.vl[addr]
      parser.message_states[addr].ignore_counter = True
      parser.message_states[addr].ignore_checksum = True
    parser.update([(1_000_000_000, frames)])
    parser.update([(2_000_000_000, frames)])
  state = CarState(cp, custom.StarPilotCarParams.new_message())
  ret, _ = state.update(parsers, None)
  assert not ret.cruiseState.enabled
  assert ret.cruiseState.speed == pytest.approx(10 * 0.44704)
  assert ret.vEgoRaw == pytest.approx(15.07 / 3.6)
  assert not ret.seatbeltUnlatched

  # A stale belt frame cannot allow an engagement indefinitely.
  for parser in parsers.values():
    parser.update([(4_000_000_000, [])])
  ret, _ = state.update(parsers, None)
  assert ret.seatbeltUnlatched


def test_hw1_can_use_rcm_buckle_when_sdm1_is_absent():
  cp = CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_HW1)
  parsers = CarState.get_can_parsers(cp)
  packer = CANPacker(DBC[CAR.TESLA_MODEL_S_HW1][Bus.chassis])
  addr, data, bus = packer.make_can_msg("RCM_status", 0, {"RCM_buckleDriverStatus": 1})
  assert addr == 0x211 and bus == 0
  frames = [(addr, data, bus)]
  for parser in parsers.values():
    _ = parser.vl["RCM_status"]
    parser.update([(1_000_000_000, frames)])
  state = CarState(cp, custom.StarPilotCarParams.new_message())
  out, _ = state.update(parsers, None)
  assert not out.seatbeltUnlatched
