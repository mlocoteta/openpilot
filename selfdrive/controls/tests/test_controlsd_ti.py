from types import SimpleNamespace

from openpilot.selfdrive.controls.controlsd import Controls


class FakeParams:
  def __init__(self, **values):
    self.values = {"TISigmoidEnabled": True, "TISigmoidLive": False, **values}

  def get_bool(self, key):
    return bool(self.values.get(key, False))

  def get_float(self, key):
    value = self.values.get(key, 0.0)
    if isinstance(value, Exception):
      raise value
    return value


class FakeLaC:
  def __init__(self):
    self.damping = None

  def update_honda_accord_low_speed_damping(self, *args):
    self.damping = args


def make_controls(**params):
  controls = Controls.__new__(Controls)
  controls.params = FakeParams(**params)
  controls.LaC = FakeLaC()
  controls.starpilot_toggles = SimpleNamespace(steerKp=[[0], [0.6]])
  controls._ti_kp = None
  controls._ti_sigmoid_hash = None
  controls._ti_error_logged_time = 0.0
  return controls


def test_ti_kp_replaces_steer_kp_every_frame():
  controls = make_controls(TISteerKp=0.45)
  assert controls._lateral_kp() == [[0], [0.6]]
  controls._update_ti_live_params()
  for _ in range(250):
    assert controls._lateral_kp() == [[0], [0.45]]


def test_ti_kp_default_matches_param_default():
  controls = make_controls()
  controls._update_ti_live_params()
  assert controls._lateral_kp() == [[0], [0.3]]


def test_ti_live_update_failure_is_logged_and_keeps_last_values(mocker):
  log = mocker.patch("openpilot.selfdrive.controls.controlsd.cloudlog")
  controls = make_controls(TISteerKp=0.45)
  controls._update_ti_live_params()
  controls.params.values["TISteerKp"] = RuntimeError("boom")
  controls._update_ti_live_params()
  controls._update_ti_live_params()
  assert controls._lateral_kp() == [[0], [0.45]]
  assert log.exception.call_count == 1


def make_limit_controls(ti_output=0.0):
  from collections import deque
  from openpilot.selfdrive.controls.controlsd import TI_OUTPUT_PIPELINE_FRAMES
  controls = make_controls()
  controls.steer_limited_by_safety = True  # stale value from an earlier frame
  controls._ti_torque_requests = deque([0.0] * TI_OUTPUT_PIPELINE_FRAMES, maxlen=TI_OUTPUT_PIPELINE_FRAMES)
  controls.sm = {'carOutput': SimpleNamespace(actuatorsOutput=SimpleNamespace(torque=ti_output))}
  return controls


def lat_cc(torque, lat_active=True):
  return SimpleNamespace(latActive=lat_active, actuators=SimpleNamespace(torque=torque))


def set_ti_output(controls, torque):
  controls.sm['carOutput'].actuatorsOutput.torque = torque


def test_ti_steer_limited_is_evaluated_without_selfdrive_active():
  # Always-on lateral: selfdriveState is inactive, but the lateral loop runs and must
  # not inherit a stale "limited" value that freezes the integrator for the whole drive.
  controls = make_limit_controls()
  controls._update_ti_steer_limited(lat_cc(0.0))
  assert not controls.steer_limited_by_safety


def test_ti_steer_limited_matches_output_to_recent_requests():
  controls = make_limit_controls()
  requests = [0.02, 0.04, 0.06, 0.08, 0.10]
  for n, req in enumerate(requests):
    # carOutput answers the request from two frames earlier (the TI kept up)
    set_ti_output(controls, requests[n - 2] if n >= 2 else 0.0)
    controls._update_ti_steer_limited(lat_cc(req))
    assert not controls.steer_limited_by_safety


def test_ti_steer_limited_flags_a_rate_limited_output():
  controls = make_limit_controls()
  requests = [0.3, 0.3, 0.3, 0.3]
  ti_out = [0.0, 0.0, 15 / 599, 30 / 599]  # slewing 15 counts/frame toward 0.3
  flags = []
  for req, out in zip(requests, ti_out, strict=True):
    set_ti_output(controls, out)
    controls._update_ti_steer_limited(lat_cc(req))
    flags.append(controls.steer_limited_by_safety)
  assert flags[-2:] == [True, True]


def test_ti_steer_limited_clears_when_lateral_inactive():
  controls = make_limit_controls(ti_output=0.5)
  controls._update_ti_steer_limited(lat_cc(0.0))
  assert controls.steer_limited_by_safety  # output 0.5 matches no recent request
  controls._update_ti_steer_limited(lat_cc(0.0, lat_active=False))
  assert not controls.steer_limited_by_safety
  assert list(controls._ti_torque_requests) == [0.0] * len(controls._ti_torque_requests)
