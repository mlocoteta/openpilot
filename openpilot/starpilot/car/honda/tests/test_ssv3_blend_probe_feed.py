"""openpilot side of the Accord 9G SSV3 blend probe: SSV3BlendProbe param -> car controller, auto-clear when the probe
ends (completed or aborted), starpilotCarState.ssv3 logging fields, and the onroad "Blend test" alert."""
from openpilot.cereal import log
from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.ssv3 import ProbeEnd, ProbeState
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.selfdrived.events import EVENTS, ET, ssv3_blend_probe_alert
from openpilot.starpilot.car.honda.ssv3_feed import PARAM_INTERVAL, PROBE_PARAM, blend_probe_alert_active, install, read_probe


class FakeParams:
  def __init__(self, values=None, fail_put=False):
    self.values = dict(values or {})
    self.puts = []
    self.fail_put = fail_put

  def get_bool(self, key):
    return bool(self.values.get(key, False))

  def get(self, key):
    if key == "Broken":
      raise OSError
    return self.values.get(key)

  def put(self, key, value):
    self.puts.append((key, value))
    if self.fail_put:
      raise OSError
    self.values[key] = value


class State:
  canValid = True


def ci(identity=CAR.HONDA_ACCORD_9G):
  return CarInterface(CarInterface.get_params(identity, gen_empty_fingerprint(), [], False, False, False))


def fw3(car):
  s = car.CS.ssv3
  s.fw3, s.version = True, 3


def test_param_registered_cleared_every_drive_default_off():
  text = open(__file__.rsplit("/starpilot/", 1)[0] + "/common/params_keys.h").read()
  assert ('{"SSV3BlendProbe", {CLEAR_ON_MANAGER_START | CLEAR_ON_ONROAD_TRANSITION | CLEAR_ON_OFFROAD_TRANSITION, '
          'INT, "0"}}') in text
  assert read_probe(FakeParams()) == 0
  assert read_probe(FakeParams({PROBE_PARAM: 3})) == 3
  assert read_probe(FakeParams({PROBE_PARAM: -4})) == 0
  assert read_probe(FakeParams({PROBE_PARAM: "garbage"})) == 0


def test_param_reaches_the_controller_once_a_second():
  car = ci()
  params = FakeParams({PROBE_PARAM: 1})
  feed = install(car, params)
  feed.update(State(), None, car_state_stamp=1)
  assert car.CC.ssv3.requested_probe == 1
  params.values[PROBE_PARAM] = 0
  for _ in range(PARAM_INTERVAL - 1):
    feed.update(State(), None, car_state_stamp=1)
  assert car.CC.ssv3.requested_probe == 1
  feed.update(State(), None, car_state_stamp=1)
  assert car.CC.ssv3.requested_probe == 0


def _finish(car, reason=ProbeEnd.BRAKE):
  probe = car.CC.ssv3.probe
  probe.program = 1
  probe._finish(reason)


def test_finished_probe_clears_the_param_and_never_rearms_on_a_stale_value():
  car = ci()
  params = FakeParams({PROBE_PARAM: 1})
  feed = install(car, params)
  feed.update(State(), None, car_state_stamp=1)
  _finish(car)
  feed.update(State(), None, car_state_stamp=1)
  assert params.puts == [(PROBE_PARAM, 0)]
  assert car.CC.ssv3.requested_probe == 0
  # the write is lost / not landed yet: the param still reads 1 -> nothing is handed over
  params.values[PROBE_PARAM] = 1
  for _ in range(5 * PARAM_INTERVAL):
    feed.update(State(), None, car_state_stamp=1)
    car.CC.ssv3.probe.update(car.CC.ssv3.requested_probe, None, 240)   # what the car controller does
    assert car.CC.ssv3.requested_probe == 0
  assert params.puts == [(PROBE_PARAM, 0)]        # cleared once, not every frame
  # once it reads 0, a fresh non-zero value arms again
  params.values[PROBE_PARAM] = 0
  for _ in range(PARAM_INTERVAL):
    feed.update(State(), None, car_state_stamp=1)
  params.values[PROBE_PARAM] = 2
  for _ in range(PARAM_INTERVAL):
    feed.update(State(), None, car_state_stamp=1)
  assert car.CC.ssv3.requested_probe == 2


def test_failed_clear_still_keeps_it_off():
  car = ci()
  params = FakeParams({PROBE_PARAM: 1}, fail_put=True)
  feed = install(car, params)
  feed.update(State(), None, car_state_stamp=1)
  _finish(car, ProbeEnd.YAW)
  for _ in range(10 * PARAM_INTERVAL):
    feed.update(State(), None, car_state_stamp=1)
    car.CC.ssv3.probe.update(car.CC.ssv3.requested_probe, None, 240)
    assert car.CC.ssv3.requested_probe == 0


def test_companion_logs_the_probe():
  car = ci()
  fw3(car)
  feed = install(car, FakeParams({PROBE_PARAM: 1}))
  probe = car.CC.ssv3.probe
  probe.state, probe.program, probe.window, probe.command, probe.total = ProbeState.HOLD, 1, 2, 120, 3150
  car.CS.ssv3.steer_status = 4
  out = feed.update(State(), None, car_state_stamp=7).starpilotCarState.ssv3
  assert (out.blendProbeProgram, out.blendProbeState, out.blendProbeWindow, out.blendProbeCommand, out.blendProbeEnd) == \
         (1, ProbeState.HOLD, 2, 120, 0)
  assert abs(out.blendProbeTime - 31.5) < 1e-4 and out.steerStatus == 4
  probe.state = ProbeState.ARMED
  out = feed.update(State(), None, car_state_stamp=8).starpilotCarState.ssv3
  assert out.blendProbeWindow == -1


def test_firmware2_publishes_nothing():
  car = ci()
  feed = install(car, FakeParams({PROBE_PARAM: 1}))
  assert feed.update(State(), None, car_state_stamp=1) is None


class FakeSM(dict):
  def __init__(self, state, *, seen=True, alive=True, command=60, window=0):
    msg = log.Event.new_message()
    sp = msg.init('starpilotCarState')
    sp.ssv3.blendProbeState = state
    sp.ssv3.blendProbeCommand = command
    sp.ssv3.blendProbeWindow = window
    super().__init__(starpilotCarState=sp.as_reader() if hasattr(sp, 'as_reader') else sp)
    self.seen = {'starpilotCarState': seen}
    self.alive = {'starpilotCarState': alive}


class CP:
  def __init__(self, fp):
    self.carFingerprint = fp


def test_alert_only_on_the_9g_while_armed_or_running_and_fresh():
  cp = CP(CAR.HONDA_ACCORD_9G)
  for state, on in ((ProbeState.IDLE, False), (ProbeState.ARMED, True), (ProbeState.HOLD, True), (ProbeState.REST, True),
                    (ProbeState.DONE, False)):
    assert blend_probe_alert_active(cp, FakeSM(state)) == on
  assert not blend_probe_alert_active(cp, FakeSM(ProbeState.HOLD, alive=False))
  assert not blend_probe_alert_active(cp, FakeSM(ProbeState.HOLD, seen=False))
  assert not blend_probe_alert_active(CP(CAR.HONDA_CIVIC), FakeSM(ProbeState.HOLD))


def test_alert_text():
  ev = EVENTS[log.OnroadEvent.EventName.ssv3BlendProbe]
  assert set(ev) == {ET.PERMANENT}           # informational only: never blocks or ends engagement
  a = ssv3_blend_probe_alert(None, None, FakeSM(ProbeState.HOLD, command=-120, window=2), False, 0, None)
  assert (a.alert_text_1, a.alert_text_2) == ("Blend test running", "Window 3: 120 left. Hold straight")
  a = ssv3_blend_probe_alert(None, None, FakeSM(ProbeState.HOLD, command=60, window=0), False, 0, None)
  assert a.alert_text_2 == "Window 1: 60 right. Hold straight"
  assert ssv3_blend_probe_alert(None, None, FakeSM(ProbeState.REST), False, 0, None).alert_text_2 == "Rest: normal steering"
  assert ssv3_blend_probe_alert(None, None, FakeSM(ProbeState.ARMED), False, 0, None).alert_text_1 == "Blend test armed"
