"""Regress StarPilot's route51 AOL-to-stalk transition against real Panda hooks."""
from types import SimpleNamespace
import pytest

from opendbc.can import CANPacker
from opendbc.car import structs
from opendbc.car.tesla.carcontroller import CarController
from opendbc.car.tesla.interface import CarInterface
from opendbc.car.tesla.values import CAR, DBC
from opendbc.safety.tests.libsafety import libsafety_py
from opendbc.car.tesla.preap.lateral import preap_lateral_authorized
from opendbc.car.tesla.preap.engagement import PreAPEngagement


@pytest.mark.parametrize('stock_main', [False, True])
def test_preap_aol_stalk_cancel_and_reengagement(stock_main):
  cp = CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_PREAP)
  controller = CarController(DBC[CAR.TESLA_MODEL_S_PREAP], cp)
  controller.stock_cc = None
  safety = libsafety_py.libsafety
  assert safety.set_safety_hooks(cp.safetyConfigs[0].safetyModel.raw, 0) == 0
  safety.init_tests()
  safety.set_alternative_experience(32)
  packer = CANPacker('tesla_can')
  state = structs.CarState.new_message()
  state.vEgoRaw = state.vEgo = 18.8
  state.gearShifter = structs.CarState.GearShifter.drive
  cs = SimpleNamespace(out=state.as_reader(), hands_on_level=0, cruiseEnabled=False,
                       di_cruise_state='STANDBY' if stock_main else 'OFF', engagement=PreAPEngagement(False, 500))
  panda = SimpleNamespace(safetyModel=cp.safetyConfigs[0].safetyModel, safetyParam=0,
                          safetyRxChecksInvalid=False, alternativeExperience=32, controlsAllowed=False)
  active_commands = 0

  for frame in range(600):
    safety.set_timer(frame * 10000)
    for name, values in (
      ('EPAS_sysStatus', {'EPAS_internalSAS': 0, 'EPAS_eacStatus': 1}),
      ('ESP_B', {'ESP_vehicleSpeed': 18.8 * 3.6}),
      ('DI_torque2', {'DI_gear': 4}),
      ('GTW_carState', {}),
      ('DI_state', {'DI_cruiseState': 1 if stock_main else 0}),
      ('STW_ACTN_RQ', {'SpdCtrlLvr_Stat': 2 if frame in (200, 500) else 1 if frame == 400 else 0}),
    ):
      addr, dat, bus = packer.make_can_msg(name, 0, values)
      assert safety.safety_rx_hook(libsafety_py.make_CANPacket(addr, bus, dat))

    button = 2 if frame in (200, 500) else 1 if frame == 400 else 0
    previous = 2 if frame in (201, 501) else 1 if frame == 401 else 0
    cs.engagement.process_buttons(button, previous, 10000 + frame * 10, 18.8, 'KPH', False, False, True, False)
    cs.engagement.check_can_engage(False, state.gearShifter, False)
    cs.cruiseEnabled = cs.engagement.cruiseEnabled
    panda.controlsAllowed = safety.get_controls_allowed()
    cs.preap_lateral_authorized = preap_lateral_authorized(cp, cs, [panda], not 300 <= frame < 320)
    cc = structs.CarControl.new_message()
    # AOL only, with no normal engagement. A delayed control packet continues
    # requesting steering even during cancel and telemetry loss.
    cc.enabled = False
    cc.latActive = True
    cc.cruiseControl.cancel = cs.cruiseEnabled
    cc.actuators.steeringAngleDeg = -12.2
    _, sends = controller.update(cc.as_reader(), cs, frame * 10000000, None)
    for addr, dat, bus in sends:
      assert safety.safety_tx_hook(libsafety_py.make_CANPacket(addr, bus, dat)), (frame, hex(addr), dat.hex())
      if addr == 0x488 and dat[2] >> 6 == 1:
        active_commands += 1
  assert active_commands == (290 if stock_main else 140)


@pytest.mark.parametrize('failure', ['stale', 'wrong_mode', 'wrong_param', 'rx_invalid', 'park', 'door', 'override', 'cancel'])
def test_preap_authorization_fails_closed(failure):
  cp = CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_PREAP)
  out = SimpleNamespace(gearShifter=structs.CarState.GearShifter.drive, doorOpen=False, steeringDisengage=False)
  cs = SimpleNamespace(out=out, engagement=SimpleNamespace(lateralEnabled=True), di_cruise_state='OFF')
  panda = SimpleNamespace(safetyModel=cp.safetyConfigs[0].safetyModel, safetyParam=0,
                          safetyRxChecksInvalid=False, alternativeExperience=32, controlsAllowed=True)
  assert preap_lateral_authorized(cp, cs, [panda], True)
  if failure == 'wrong_mode':
    panda.safetyModel = structs.CarParams.SafetyModel.noOutput
  if failure == 'wrong_param':
    panda.safetyParam = 1
  if failure == 'rx_invalid':
    panda.safetyRxChecksInvalid = True
  if failure == 'park':
    out.gearShifter = structs.CarState.GearShifter.park
  if failure == 'door':
    out.doorOpen = True
  if failure == 'override':
    out.steeringDisengage = True
  if failure == 'cancel':
    cs.engagement.lateralEnabled = False
  assert not preap_lateral_authorized(cp, cs, [panda], failure != 'stale')


@pytest.mark.parametrize('reset', ['cancel', 'override', 'door', 'park'])
def test_preap_physical_lateral_session_requires_new_pull_after_reset(reset):
  engagement = PreAPEngagement(False, 500)
  engagement.process_buttons(2, 0, 10000, 10., 'KPH', False, False, True, False)
  assert engagement.lateralEnabled
  if reset == 'cancel':
    engagement.process_buttons(1, 0, 11000, 10., 'KPH', False, False, True, False)
  elif reset == 'override':
    engagement.handle_steering_disengage(True)
    engagement.handle_steering_disengage(False)
  else:
    gear = structs.CarState.GearShifter.park if reset == 'park' else structs.CarState.GearShifter.drive
    engagement.check_can_engage(reset == 'door', gear, False)
    engagement.check_can_engage(False, structs.CarState.GearShifter.drive, False)
  assert not engagement.lateralEnabled
  engagement.process_buttons(2, 0, 12000, 10., 'KPH', False, False, True, False)
  assert engagement.lateralEnabled
