from types import SimpleNamespace

import pytest

from opendbc.can import CANPacker
from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.nidec_interceptor import NidecInterceptor, create_command, pedal_crc, qualified
from opendbc.car.honda.values import CAR, DBC, HondaFlags

IDENTITIES = (
  CAR.ACURA_ILX, CAR.HONDA_CRV, CAR.HONDA_CRV_EU, CAR.HONDA_CRV_SA,
  CAR.HONDA_FIT, CAR.HONDA_FREED, CAR.HONDA_HRV, CAR.HONDA_CLARITY,
  CAR.HONDA_ODYSSEY, CAR.HONDA_ODYSSEY_TWN, CAR.ACURA_RDX, CAR.HONDA_PILOT,
  CAR.HONDA_RIDGELINE, CAR.HONDA_CIVIC, CAR.HONDA_ACCORD_9G,
  CAR.ACURA_MDX_3G, CAR.ACURA_MDX_3G_MMR, CAR.ACURA_TLX_1G,
)


def factory(identity, *, bus=0, length=6, sensor=True):
  fp = gen_empty_fingerprint()
  if sensor:
    fp[bus][0x201] = length
  return CarInterface.get_params(identity, fp, [], False, False, False)


@pytest.mark.parametrize("identity", IDENTITIES)
def test_nidec_interceptor_factory_and_real_controller_construction(identity):
  cp = factory(identity)
  assert qualified(cp)
  assert not cp.pcmCruise and cp.openpilotLongitudinalControl
  assert cp.autoResumeSng and cp.minEnableSpeed == -1
  assert cp.safetyConfigs[-1].safetyParam == (36 if cp.flags & HondaFlags.NIDEC_ALT_SCM_MESSAGES else 32)
  ci = CarInterface(cp)
  assert isinstance(ci.CC.nidec_interceptor, NidecInterceptor)
  assert 0x201 in ci.can_parsers[Bus.pt].message_states
  assert CarInterface.get_pid_accel_limits(cp, 30, 30) == (-4.0, 1.6)


@pytest.mark.parametrize("identity", IDENTITIES)
@pytest.mark.parametrize("options", ({"sensor": False}, {"bus": 2}, {"length": 5}, {"length": 8}))
def test_absent_wrong_bus_or_length_does_not_change_stock_authority(identity, options):
  actual = factory(identity, **options)
  stock = factory(identity, sensor=False)
  assert actual.to_dict() == stock.to_dict()
  assert not actual.flags & HondaFlags.GAS_INTERCEPTOR
  assert not qualified(actual)


@pytest.mark.parametrize("identity", (CAR.HONDA_ACCORD, CAR.HONDA_CRV_5G, CAR.HONDA_CITY_7G, CAR.HONDA_ACCORD_11G))
def test_bosch_sensor_never_admits_nidec_interceptor(identity):
  cp = factory(identity)
  assert not cp.flags & HondaFlags.GAS_INTERCEPTOR
  assert not qualified(cp)


@pytest.mark.parametrize("identity", IDENTITIES)
def test_actual_command_codec_has_dual_track_encoding_and_disabled_zero(identity):
  packer = CANPacker(DBC[identity][Bus.pt])
  for counter in range(16):
    for demand in (0.0, 0.001, 0.001001, 0.002, 0.1, 0.5, 1.0):
      address, data, bus = create_command(packer, demand, counter)
      assert (address, bus, len(data)) == (0x200, 0, 6)
      assert data[5] == pedal_crc(data)
      assert data[4] & 15 == counter
      first, second = int.from_bytes(data[:2], "big"), int.from_bytes(data[2:4], "big")
      if demand <= 0.001:
        assert first == second == 0 and data[4] & 0x80 == 0
      else:
        assert data[4] & 0x80
        assert abs(second - 2 * first) <= 1
        assert 329 <= first <= 1332
        assert (first * 0.253984064 - 83.3) == pytest.approx(demand * 255, abs=0.13)


def test_original_nidec_learning_and_inactive_zero():
  cp = factory(CAR.HONDA_CIVIC)
  owner = NidecInterceptor(cp)
  cc = structs.CarControl(longActive=True)
  cc.actuators.accel = 1.0
  cc.actuators.longControlState = "pid"
  cs = SimpleNamespace(out=SimpleNamespace(aEgo=0.5, gasPressed=False, brakePressed=False, vEgo=10.0))
  output = owner.update(cc, cs, 0.2, 0.0, 0.01)
  gas_factor = 1.0 + 0.5 / 150.0 * (0.2 * 4.8)
  wind_factor = 1.0 + 0.01 * 4.8 / 1000.0
  assert owner.bosch_gas_factor == pytest.approx(gas_factor)
  assert owner.bosch_wind_factor == pytest.approx(wind_factor)
  assert output == pytest.approx(0.2 * gas_factor + 0.01 * wind_factor * 0.75)
  cs.out.gasPressed = True
  owner.update(cc, cs, 0.2, 0.0, 0.01)
  assert owner.bosch_gas_factor == pytest.approx(gas_factor)
  cc.longActive = False
  assert owner.update(cc, cs, 0.0, 0.0, 0.01) == 0.0



def _pid(accel):
  cc = structs.CarControl(longActive=True)
  cc.actuators.accel = accel
  cc.actuators.longControlState = "pid"
  return cc


def test_accord_9g_guard_clamps_start_and_bounds_runaway():
  from opendbc.car.honda import pedal_learner as PL
  owner = NidecInterceptor(factory(CAR.HONDA_ACCORD_9G))
  assert owner.pedal_guard is not None
  owner.set_factors(2.044, 4.9)  # the first 7.0 drive's runaway value, as BoschLearningParams loads it
  assert owner.bosch_gas_factor == PL.GAS_FACTOR_MAX and owner.gas_factor_stored == pytest.approx(2.044)
  assert owner.bosch_wind_factor == PL.WIND_FACTOR_HOLD and owner.wind_factor_stored == pytest.approx(4.9)
  owner.set_factors(1.5566, 4.9)
  cc = _pid(1.0)
  cs = SimpleNamespace(out=SimpleNamespace(aEgo=0.0, gasPressed=False, brakePressed=False, vEgo=20.0))
  for _ in range(50 * 60):  # 1 min of a 1 m/s^2 under-delivery at 20 m/s: stock would run to its 3.0 clip
    owner.update(cc, cs, 1.0 / 4.8, 0.0, 0.05)
  assert owner.bosch_gas_factor == pytest.approx(PL.GAS_FACTOR_MAX)  # 1.5566 + 0.10 capped at 1.6
  cs.out.aEgo = 0.95
  for _ in range(50 * 60):  # low-speed launches never learn and are capped at 1.0
    cs.out.vEgo = 3.0
    output = owner.update(cc, cs, 1.0 / 4.8, 0.0, 0.002)
  assert owner.bosch_gas_factor == pytest.approx(PL.GAS_FACTOR_MAX)
  gas_mult = 0.4 + 0.6 * 3.0 / 10.0
  assert output == pytest.approx(gas_mult * (1.0 / 4.8 * 1.0 + 0.002 * owner.bosch_wind_factor * 0.75))


def test_accord_9g_guard_brake_holdoff_and_hill():
  owner = NidecInterceptor(factory(CAR.HONDA_ACCORD_9G))
  owner.set_factors(1.4, 1.0)
  cc = _pid(1.0)
  cs = SimpleNamespace(out=SimpleNamespace(aEgo=0.5, gasPressed=False, brakePressed=False, vEgo=20.0))
  for _ in range(200):
    owner.update(cc, cs, 1.0 / 4.8, 0.0, 0.05, apply_brake=1)
  assert owner.bosch_gas_factor == 1.4 and owner.pedal_guard.counts["brake"] == 200
  for _ in range(99):
    owner.update(cc, cs, 1.0 / 4.8, 0.0, 0.05)
  assert owner.bosch_gas_factor == 1.4
  owner.observe_orientation([0.0, 0.1, 0.0])  # ~5.7 deg grade, ~0.98 m/s^2
  for _ in range(100):
    owner.update(cc, cs, 1.0 / 4.8, 0.0, 0.05)
  assert owner.bosch_gas_factor == 1.4 and owner.pedal_guard.counts["hill"] > 0
  owner.observe_orientation([0.0, 0.0, 0.0])
  for _ in range(100):
    owner.update(cc, cs, 1.0 / 4.8, 0.0, 0.05)
  assert 1.4 < owner.bosch_gas_factor < 1.45


def test_accord_9g_wind_factor_held():
  # 2026-10-25 route 30: the stock wind learner had walked to 3.3, the long PID sat at -0.3 m/s^2 to cancel the
  # extra pedal and the brake tapped ~16 times a minute at a 50 mph cruise. The 9G holds the factor instead.
  from opendbc.car.honda import pedal_learner as PL
  owner = NidecInterceptor(factory(CAR.HONDA_ACCORD_9G))
  owner.set_factors(1.25, 3.304)
  assert owner.bosch_wind_factor == PL.WIND_FACTOR_HOLD == 2.3
  assert owner.learner_start == (1.25, 2.3)
  wind_brake = 0.091  # stock table at 22 m/s
  cs = SimpleNamespace(out=SimpleNamespace(aEgo=0.0, gasPressed=False, brakePressed=False, vEgo=22.0))
  for accel in (0.6, -0.4):  # a minute each of under- and over-delivery: the stock law would move it ~25 %
    cc = _pid(accel)
    for _ in range(50 * 60):
      output = owner.update(cc, cs, max(accel, 0.0) / 4.8, max(-accel, 0.0) / 4.8, wind_brake)
    assert owner.bosch_wind_factor == PL.WIND_FACTOR_HOLD
  assert output == pytest.approx(1.0 * (0.0 * 1.25 - 0.4 / 4.8 + wind_brake * 2.3 * 0.75))
  owner.log_learner()  # the per-drive log names the held and stored values


@pytest.mark.parametrize("identity", [i for i in IDENTITIES if i != CAR.HONDA_ACCORD_9G])
def test_other_interceptor_cars_keep_stock_learner(identity):
  owner = NidecInterceptor(factory(identity))
  assert owner.pedal_guard is None
  owner.set_factors(2.5, 1.0)
  assert owner.bosch_gas_factor == 2.5
  cs = SimpleNamespace(out=SimpleNamespace(aEgo=0.0, gasPressed=False, brakePressed=False, vEgo=22.0))
  for _ in range(100):
    owner.update(_pid(0.6), cs, 0.6 / 4.8, 0.0, 0.091)
  assert owner.bosch_wind_factor > 1.0 and owner.bosch_gas_factor > 2.5


def source_frames(cp, packer, tick, *, sensor=True, level=0, state=0):
  from opendbc.can import CANDefine
  from opendbc.can.dbc import DBC as CANDBC

  dbc = CANDBC(DBC[cp.carFingerprint][Bus.pt])
  gear_name = "GEARBOX_CVT" if cp.transmissionType == structs.CarParams.TransmissionType.cvt else "GEARBOX_AUTO"
  gears = CANDefine(DBC[cp.carFingerprint][Bus.pt]).dv[gear_name]["GEAR_SHIFTER"]
  drive = next(value for value, label in gears.items() if label == "D")
  pt_sources = {
    "ENGINE_DATA": {"XMISSION_SPEED": 30},
    "WHEEL_SPEEDS": {"WHEEL_SPEED_FL": 30, "WHEEL_SPEED_FR": 30, "WHEEL_SPEED_RL": 30, "WHEEL_SPEED_RR": 30},
    "SCM_BUTTONS": {"CRUISE_BUTTONS": 0, "CRUISE_SETTING": 0},
    "SCM_FEEDBACK": {},
    "CAR_SPEED": {},
    "SEATBELT_STATUS": {"SEATBELT_DRIVER_LATCHED": 1},
    "STEER_STATUS": {"STEER_STATUS": 0},
    "STEERING_SENSORS": {},
    "VSA_STATUS": {},
    "POWERTRAIN_DATA": {"ACC_STATUS": 0, "PEDAL_GAS": 0, "BRAKE_PRESSED": 0},
    "CRUISE": {},
    gear_name: {"GEAR_SHIFTER": drive},
    "HYBRID_BRAKE_ERROR" if cp.flags & HondaFlags.HYBRID else "STANDSTILL": {},
  }
  selected_scm = "SCM_BUTTONS" if cp.flags & HondaFlags.NIDEC_ALT_SCM_MESSAGES else "SCM_FEEDBACK"
  pt_sources[selected_scm]["MAIN_ON"] = 1
  if cp.flags & HondaFlags.HAS_ALL_DOOR_STATES:
    pt_sources["DOORS_STATUS"] = {}
  if sensor:
    pt_sources["GAS_SENSOR"] = {"INTERCEPTOR_GAS": level, "INTERCEPTOR_GAS2": level, "STATE": state,
                                "COUNTER_PEDAL": tick % 16}
  frames = []
  for bus, sources in ((0, pt_sources), (2, {"BRAKE_COMMAND": {}, "ACC_HUD": {}, "LKAS_HUD": {}})):
    for name, fields in sources.items():
      assert name in dbc.name_to_msg, name
      assert fields.keys() <= dbc.name_to_msg[name].sigs.keys(), (name, fields)
      frames.append(packer.make_can_msg(name, bus, fields))
  return frames


@pytest.mark.parametrize("identity", IDENTITIES)
def test_whole_parser_sensor_expiry_recovery_and_physical_threshold(identity):
  cp = factory(identity)
  ci = CarInterface(cp)
  packer = CANPacker(DBC[identity][Bus.pt])
  for tick in range(50):
    cs = ci.update([(1_000_000_000 + tick * 10_000_000, source_frames(cp, packer, tick))])
  assert cs.canValid and not cs.canTimeout and not cs.gasPressed
  tick = 50
  cs = ci.update([(1_000_000_000 + tick * 10_000_000, source_frames(cp, packer, tick, level=492))])
  assert not cs.gasPressed
  tick += 1
  cs = ci.update([(1_000_000_000 + tick * 10_000_000, source_frames(cp, packer, tick, level=493))])
  assert cs.gasPressed
  tick += 1
  cs = ci.update([(1_000_000_000 + tick * 10_000_000, source_frames(cp, packer, tick, state=1))])
  assert cs.gasPressed
  for tick in range(53, 105):
    cs = ci.update([(1_000_000_000 + tick * 10_000_000, source_frames(cp, packer, tick, sensor=False))])
  assert not cs.canValid
  for tick in range(105, 155):
    cs = ci.update([(1_000_000_000 + tick * 10_000_000, source_frames(cp, packer, tick))])
  assert cs.canValid and not cs.gasPressed
  command = structs.CarControl(longActive=True)
  command.actuators.accel = 1.0
  command.actuators.longControlState = "pid"
  for tick in range(155, 159):
    output, frames = ci.apply(command.as_reader(), 1_000_000_000 + tick * 10_000_000)
    pedal = [frame for frame in frames if frame[0] == 0x200]
    assert len(pedal) == (1 if (tick - 155) % 2 == 0 else 0)
    for frame in frames:
      if frame[0] == 0x30C:
        from opendbc.can import CANParser
        hud = CANParser(DBC[identity][Bus.pt], [("ACC_HUD", 10)], 0)
        hud.update([(2_600_000_000, [frame])])
        assert hud.vl["ACC_HUD"]["PCM_GAS"] == 0
        assert hud.vl["ACC_HUD"]["PCM_SPEED"] == 0
    for frame in pedal:
      assert frame[1][4] & 0x80 and frame[1][5] == pedal_crc(frame[1])
  command.longActive = False
  _, frames = ci.apply(command.as_reader(), 2_600_000_000)
  disabled = next(frame for frame in frames if frame[0] == 0x200)
  assert disabled[1][:4] == bytes(4) and disabled[1][4] & 0x80 == 0


@pytest.mark.parametrize("identity", (CAR.HONDA_CIVIC, CAR.ACURA_ILX))
def test_interceptor_actual_card_params_ipc_controls_startup(identity, monkeypatch):
  from opendbc.car.honda.tests.test_startup_profiles import exercise_final_cp_publication_and_disabled_startup
  from opendbc.car.honda.tests import test_startup_profiles as startup
  original_factory = startup.gen_empty_fingerprint

  def observed_fingerprint():
    fp = original_factory()
    fp[0][0x201] = 6
    return fp
  monkeypatch.setattr(startup, "gen_empty_fingerprint", observed_fingerprint)
  exercise_final_cp_publication_and_disabled_startup(identity, monkeypatch)
