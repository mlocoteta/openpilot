import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.hyundai.carcontroller import CarController
from opendbc.car.hyundai.carstate import CarState
from opendbc.car.hyundai.interface import CarInterface
from opendbc.car.hyundai.values import CAR, DBC, HyundaiFlags, HyundaiSafetyFlags
from openpilot.starpilot.lateral.controller_selection import default_selection

CARS = tuple(car for car in CAR if car.config.flags & HyundaiFlags.CANFD
             and not car.config.flags & HyundaiFlags.CANFD_ANGLE_STEERING)


@pytest.mark.parametrize('car,topology,aol',
                         [(car, topology, aol) for car in CARS
                          for topology in ('lfa', 'lkas', 'lkas_alt') for aol in (False, True)
                          if not (aol and car == CAR.KIA_EV6 and topology != 'lkas')])
def test_full_controller_steering_is_independent_of_longitudinal(car, topology, aol):
  fingerprint = gen_empty_fingerprint()
  if topology != 'lfa':
    fingerprint[2].update({0x110: 32, 0x362: 32} if topology == 'lkas_alt' else {0x50: 16, 0x2A4: 24})
  bus = 1 if topology != 'lfa' else 0
  fingerprint[bus].update({0x1CF: 8, 0x35: 32, 0x130: 16, 0x175: 24, 0xA0: 24, 0xEA: 24})
  fw = structs.CarParams.CarFw(ecu=structs.CarParams.Ecu.adas)
  stock = CarInterface.get_params(car, fingerprint, [fw], False, False, False)
  long = stock.as_reader().as_builder()
  long.openpilotLongitudinalControl = True
  long.pcmCruise = False
  long.safetyConfigs[-1].safetyParam |= int(HyundaiSafetyFlags.LONG)
  if aol:
    for cp in (stock, long):
      cp.safetyConfigs[-1].safetyParam |= 0x800
      cp.alternativeExperience = 32 if cp.openpilotLongitudinalControl else 0
  assert stock.lateralTuning.to_dict() == long.lateralTuning.to_dict()
  assert default_selection(stock) == default_selection(long)
  controllers = [CarController(DBC[car], cp) for cp in (stock, long)]
  states = []
  for cp in (stock, long):
    state = CarState(cp)
    state.out = structs.CarState(vEgo=2.0, vEgoRaw=2.0, canValid=True,
                                gearShifter=structs.CarState.GearShifter.drive)
    state.out.cruiseState.available = True
    state.lfa_block_msg = {**{f'BYTE{i}': 0 for i in range(3, 32)}, 'COUNTER': 0}
    state.is_metric = True
    states.append(state)
  address = {'lfa': 0x12A, 'lkas': 0x50, 'lkas_alt': 0x110}[topology]
  for frame in range(300):
    cc = structs.CarControl(enabled=not aol or frame < 150, latActive=True)
    cc.actuators.torque = (0.6 if frame % 80 < 40 else -0.6)
    cc.actuators.accel = -0.4 if frame % 50 < 25 else 0.5
    cc.hudControl.setSpeed = 20.0
    results = []
    for cp, controller, state in zip((stock, long), controllers, states, strict=True):
      state.out.vEgo = state.out.vEgoRaw = (2.0, 14.9, 15.0, 30.0)[frame // 75]
      state.out.steeringTorque = 0.0 if frame < 200 else 300.0
      state.out.steeringAngleDeg = 100.0 if frame < 120 else 0.0
      cc.longActive = cp.openpilotLongitudinalControl
      output, packets = controller.update(cc.as_reader(), state, 1_000_000_000 + frame * 10_000_000)
      steering = [packet for packet in packets if packet[0] == address]
      assert len(steering) == 1
      results.append((output.torqueOutputCan, steering))
    assert results[0] == results[1], (car, topology, frame, results)


@pytest.mark.parametrize('car', (CAR.KIA_EV6, CAR.HYUNDAI_IONIQ_5, CAR.KIA_NIRO_EV_2ND_GEN))
@pytest.mark.parametrize('mode', ('standard', 'starpilot'))
def test_selected_torque_law_is_independent_of_longitudinal(car, mode):
  from opendbc.car.vehicle_model import VehicleModel
  from openpilot.cereal import log
  from openpilot.selfdrive.controls.lib.latcontrol_torque import LatControlTorque
  from openpilot.starpilot.lateral.controller_selection import ControllerMode

  stock = CarInterface.get_non_essential_params(car)
  long = stock.as_reader().as_builder()
  long.openpilotLongitudinalControl = True
  long.pcmCruise = False
  long.safetyConfigs[-1].safetyParam |= int(HyundaiSafetyFlags.LONG)
  controllers = [LatControlTorque(cp.as_reader(), CarInterface(cp), .01, controller_mode=ControllerMode(mode))
                 for cp in (stock, long)]
  params = log.VehicleParameters.new_message(angleOffsetDeg=0.0, roll=0.0)
  state = structs.CarState(steeringAngleDeg=0.0, steeringPressed=False)
  for speed in (.3, 2.0, 5.0, 15.0, 30.0):
    state.vEgo = state.vEgoRaw = speed
    for frame in range(100):
      active = frame > 5
      state.steeringAngleDeg = 0.2 if frame % 40 < 20 else -0.2
      state.steeringPressed = frame > 80
      curvature = .0003 if frame % 50 < 25 else -.0003
      results = [controller.update(active, state, VehicleModel(cp), params, False, curvature, False, .28)
                 for cp, controller in zip((stock, long), controllers, strict=True)]
      assert results[0][:2] == results[1][:2]
      assert results[0][2].to_dict() == results[1][2].to_dict()
