from types import SimpleNamespace

from test_navigation_params import _params_client, the_galaxy


class _FakeCarParams:
  class SafetyModel:
    toyota = 42

  def __init__(self, brand="toyota", car_name="toyota"):
    self.brand = brand
    self.carName = car_name

  def __enter__(self):
    return self

  def __exit__(self, *args):
    return False


class _FakePanda:
  instances = []

  def __init__(self, **kwargs):
    self.kwargs = kwargs
    self.safety_modes = []
    self.commands = []
    self.instances.append(self)

  def __enter__(self):
    return self

  def __exit__(self, *args):
    return False

  def set_safety_mode(self, mode):
    self.safety_modes.append(mode)

  def can_send(self, address, data, bus):
    self.commands.append((address, data, bus))


def _install_door_stubs(monkeypatch, client, params, status_values):
  del client
  _FakePanda.instances = []
  monkeypatch.setattr(the_galaxy.car.CarParams, "from_bytes", lambda _: _FakeCarParams())
  monkeypatch.setattr(the_galaxy.car.CarParams, "SafetyModel", _FakeCarParams.SafetyModel, raising=False)
  monkeypatch.setattr(the_galaxy, "Panda", _FakePanda)
  monkeypatch.setattr(the_galaxy, "CANParser", lambda *args, **kwargs: SimpleNamespace())
  monkeypatch.setattr(the_galaxy.messaging, "sub_sock", lambda *args, **kwargs: object())
  monkeypatch.setattr(the_galaxy, "get_lock_status", lambda *args: status_values.pop(0))
  monkeypatch.setattr(the_galaxy.time, "sleep", lambda _: None)
  params.values["IsOnroad"] = False


def test_door_lock_rejects_onroad(monkeypatch):
  client, params = _params_client(monkeypatch, {"IsOnroad": True}, "pc")
  _install_door_stubs(monkeypatch, client, params, [])
  params.values["IsOnroad"] = True

  response = client.post("/api/doors/lock")

  assert response.status_code == 409
  assert not _FakePanda.instances


def test_door_lock_reports_success_only_after_confirmation(monkeypatch):
  client, params = _params_client(monkeypatch, {"IsOnroad": False}, "pc")
  _install_door_stubs(monkeypatch, client, params, [1, 0])

  response = client.post("/api/doors/lock")

  assert response.status_code == 200
  assert response.get_json() == {"message": "Doors locked!"}
  assert len(_FakePanda.instances) == 2
  assert all(len(instance.commands) == 2 for instance in _FakePanda.instances)
  assert all(instance.safety_modes == [42] for instance in _FakePanda.instances)


def test_door_unlock_reports_failure_after_bounded_retries(monkeypatch):
  client, params = _params_client(monkeypatch, {"IsOnroad": False}, "pc")
  _install_door_stubs(monkeypatch, client, params, [0] * 6)

  response = client.post("/api/doors/unlock")

  assert response.status_code == 502
  assert response.get_json() == {"error": "Unable to confirm that the doors were unlocked."}
  assert len(_FakePanda.instances) == 6


def test_door_feature_is_toyota_only(monkeypatch):
  client, params = _params_client(monkeypatch, {}, "tici")

  monkeypatch.setattr(the_galaxy.car.CarParams, "from_bytes", lambda _: _FakeCarParams(brand="honda", car_name="honda"))

  response = client.get("/api/car_features_check?tool=doors")

  assert response.status_code == 200
  assert response.get_json() == {"result": False}
  del params
