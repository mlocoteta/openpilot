from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import Ssv3Option
from opendbc.car.honda.values import CAR
from openpilot.starpilot.car.honda.ssv3_feed import OPTION_PARAMS, install, read_options


class FakeParams:
  def __init__(self, values):
    self.values = values

  def get_bool(self, key):
    if key == "Broken":
      raise OSError
    return self.values.get(key, False)


class State:
  canValid = True


def ci(identity=CAR.HONDA_ACCORD_9G):
  return CarInterface(CarInterface.get_params(identity, gen_empty_fingerprint(), [], False, False, False))


def test_params_are_registered_and_default_off():
  text = open(__file__.rsplit("/starpilot/", 1)[0] + "/common/params_keys.h").read()
  for key, _ in OPTION_PARAMS:
    assert f'{{"{key}", {{PERSISTENT, BOOL, "0"}}}}' in text
  assert read_options(FakeParams({})) == 0
  assert read_options(FakeParams({k: True for k, _ in OPTION_PARAMS})) == Ssv3Option.ALL


def test_only_the_9g_gets_a_feed():
  assert install(ci(CAR.ACURA_MDX_3G), FakeParams({})) is None
  assert install(ci(), FakeParams({})) is not None


def test_firmware2_publishes_nothing_and_sends_no_options():
  car = ci()
  feed = install(car, FakeParams({"SSV3TorqueBlendDisable": True}))
  for _ in range(250):
    assert feed.update(State(), None, car_state_stamp=1) is None
  assert car.CC.ssv3.requested_options == Ssv3Option.TORQUE_BLEND_DISABLE   # requested ...
  assert car.CC.ssv3.options(car.CS) == 0                                    # ... but never sent on firmware 2


def test_firmware3_companion():
  car = ci()
  feed = install(car, FakeParams({"SSV3LsbToggleDisable": True}))
  s = car.CS.ssv3
  s.fw3, s.version, s.hardware_rev, s.eps_lkas_ack, s.motor_torque = True, 3, 4, True, -42
  msg = feed.update(State(), None, car_state_stamp=123)
  out = msg.starpilotCarState.ssv3
  assert (out.firmwareVersion, out.hardwareRev, out.epsLkasAck, out.cameraFault, out.motorTorque, out.options) == \
         (3, 4, True, False, -42, Ssv3Option.LSB_TOGGLE_DISABLE)
  assert msg.starpilotCarState.sourceCarStateMonoTime == 123


def test_deadband_comp_param_registered_default_off_and_read():
  from openpilot.starpilot.car.honda.ssv3_feed import DEADBAND_COMP_PARAM, read_deadband_comp
  text = open(__file__.rsplit("/starpilot/", 1)[0] + "/common/params_keys.h").read()
  assert DEADBAND_COMP_PARAM == "SSV3DeadbandComp"
  assert '{"SSV3DeadbandComp", {PERSISTENT, BOOL, "0"}}' in text
  assert read_deadband_comp(FakeParams({})) is False
  assert read_deadband_comp(FakeParams({"SSV3DeadbandComp": True})) is True

  class Broken:
    def get_bool(self, key):
      raise OSError
  assert read_deadband_comp(Broken()) is False
  car = ci()
  feed = install(car, FakeParams({"SSV3DeadbandComp": True}))
  feed.update(State(), None, car_state_stamp=1)
  assert car.CC.ssv3.requested_deadband_comp is True
  assert car.CC.ssv3.deadband_comp(car.CS) is False          # firmware 2: never
  car.CS.ssv3.fw3 = True
  assert car.CC.ssv3.deadband_comp(car.CS) is True


def test_windup_guard_state_is_logged():
  from opendbc.car.honda.ssv3 import Ssv3Cut
  car = ci()
  feed = install(car, FakeParams({}))
  s = car.CS.ssv3
  s.fw3, s.version, s.eps_lkas_ack, s.board_mode, s.board_request, s.lin_fatal = True, 3, False, 1, True, True
  car.CC.ssv3.guard.reason = Ssv3Cut.EPS_NO_ACK | Ssv3Cut.BOARD_IDLE | Ssv3Cut.LIN_FATAL
  out = feed.update(State(), None, car_state_stamp=5).starpilotCarState.ssv3
  assert out.lkasCut and out.cutReason == 7
  assert (out.boardMode, out.boardSteerRequest, out.linFatalError, out.deadbandComp) == (1, True, True, False)
  car.CC.ssv3.guard.reason = 0
  out = feed.update(State(), None, car_state_stamp=6).starpilotCarState.ssv3
  assert not out.lkasCut and out.cutReason == 0
