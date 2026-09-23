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
