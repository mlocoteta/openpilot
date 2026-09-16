from cereal import car

from openpilot.starpilot.common.car_params_capability import capability_car_params_bytes


class FakeParams:
  def __init__(self, values):
    self.values = values

  def get(self, key, encoding=None):
    value = self.values.get(key)
    return value.decode() if encoding and isinstance(value, bytes) else value

  def get_bool(self, key):
    return self.values.get(key) in (True, b"1", "1")


def cp_bytes(fingerprint, alpha_available=False):
  cp = car.CarParams.new_message()
  cp.carFingerprint = fingerprint
  cp.alphaLongitudinalAvailable = alpha_available
  return cp.to_bytes()


def test_matching_previous_route_unblocks_capability_after_transient_mock():
  hw1 = cp_bytes("TESLA_MODEL_S_HW1", alpha_available=True)
  params = FakeParams({
    "CarModel": "TESLA_MODEL_S_HW1", "ForceFingerprint": True,
    "CarParamsPersistent": cp_bytes("MOCK"), "CarParamsPrevRoute": hw1,
  })
  assert capability_car_params_bytes(params) == hw1


def test_live_recognized_params_take_precedence_over_previous_route():
  hw1 = cp_bytes("TESLA_MODEL_S_HW1", alpha_available=True)
  live = cp_bytes("TESLA_MODEL_S_HW1", alpha_available=False)
  params = FakeParams({
    "CarModel": "TESLA_MODEL_S_HW1", "ForceFingerprint": True, "IsOnroad": True,
    "CarParams": live, "CarParamsPersistent": cp_bytes("MOCK"), "CarParamsPrevRoute": hw1,
  })
  assert capability_car_params_bytes(params) == live


def test_previous_route_must_match_explicit_forced_model():
  previous = cp_bytes("TESLA_MODEL_S_HW1", alpha_available=True)
  params = FakeParams({
    "CarModel": "TESLA_MODEL_S_PREAP", "ForceFingerprint": True,
    "CarParamsPersistent": cp_bytes("MOCK"), "CarParamsPrevRoute": previous,
  })
  assert capability_car_params_bytes(params) is None

  params.values["CarModel"] = "TESLA_MODEL_S_HW1"
  params.values["ForceFingerprint"] = False
  assert capability_car_params_bytes(params) is None


def test_current_recognized_mismatch_blocks_stale_fallback():
  params = FakeParams({
    "CarModel": "TESLA_MODEL_S_HW1", "ForceFingerprint": True,
    "CarParamsPersistent": cp_bytes("TESLA_MODEL_S_PREAP"),
    "CarParamsPrevRoute": cp_bytes("TESLA_MODEL_S_HW1", alpha_available=True),
  })
  assert capability_car_params_bytes(params) is None
