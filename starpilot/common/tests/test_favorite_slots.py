from openpilot.common.params import ParamKeyType
from openpilot.starpilot.common.favorite_slots import (
  FAVORITE_ACTION_ACCEL_COUNTER,
  FAVORITE_ACTION_DISTANCE_INCREASE,
  FAVORITE_ACTION_TRAFFIC_MODE_COUNTER,
  FAVORITE_ACTION_TOGGLE_TRAFFIC_MODE,
  FAVORITE_SLOTS_PARAM,
  default_favorite_slots,
  load_favorite_slots,
  toggle_favorite_slot,
)


class FakeParams:
  def __init__(self):
    self.store = {}
    self.types = {
      FAVORITE_SLOTS_PARAM: ParamKeyType.JSON,
      "AlphaLongitudinalEnabled": ParamKeyType.BOOL,
      "ForceOffroad": ParamKeyType.BOOL,
      "RedneckCruise": ParamKeyType.BOOL,
      "NotBool": ParamKeyType.INT,
    }

  def get(self, key):
    return self.store.get(key)

  def get_bool(self, key):
    return bool(self.store.get(key, False))

  def put(self, key, value):
    self.store[key] = value

  def put_bool(self, key, value):
    self.store[key] = bool(value)

  def put_bool_nonblocking(self, key, value):
    self.put_bool(key, value)

  def get_int(self, key, default=0):
    return int(self.store.get(key, default))

  def put_int(self, key, value):
    self.store[key] = int(value)

  def get_type(self, key):
    return self.types.get(key, ParamKeyType.STRING)


def test_load_favorite_slots_defaults_on_empty_payload():
  params = FakeParams()

  assert load_favorite_slots(params) == default_favorite_slots()


def test_load_favorite_slots_filters_non_bool_keys():
  params = FakeParams()
  params.put(FAVORITE_SLOTS_PARAM, [
    {"enabled": True, "show_onroad": True, "key": "NotBool", "label": "Bad"},
    {"enabled": True, "show_onroad": False, "key": "RedneckCruise", "label": "Redneck Cruise"},
  ])

  slots = load_favorite_slots(params)

  assert slots[0]["key"] is None
  assert slots[0]["enabled"] is True
  assert slots[1]["key"] == "RedneckCruise"
  assert slots[1]["show_onroad"] is False


def test_toggle_favorite_slot_ignores_disabled_slot():
  params = FakeParams()
  params.put("RedneckCruise", False)
  params.put(FAVORITE_SLOTS_PARAM, [
    {"enabled": False, "show_onroad": True, "key": "RedneckCruise", "label": "Redneck Cruise"},
  ])

  assert toggle_favorite_slot(0, params, FakeParams()) is False
  assert params.get_bool("RedneckCruise") is False


def test_toggle_favorite_slot_flips_bool_and_requests_refresh():
  params = FakeParams()
  memory = FakeParams()
  params.put("RedneckCruise", False)
  params.put(FAVORITE_SLOTS_PARAM, [
    {"enabled": True, "show_onroad": False, "key": "RedneckCruise", "label": "Redneck Cruise"},
  ])

  assert toggle_favorite_slot(0, params, memory) is True
  assert params.get_bool("RedneckCruise") is True
  assert memory.get_bool("StarPilotTogglesUpdated") is True


def test_toggle_favorite_slot_blocks_alpha_longitudinal_onroad():
  params = FakeParams()
  params.put("IsOnroad", True)
  params.put("AlphaLongitudinalEnabled", False)
  params.put(FAVORITE_SLOTS_PARAM, [
    {"enabled": True, "show_onroad": True, "key": "AlphaLongitudinalEnabled", "label": "Alpha Longitudinal"},
  ])

  assert toggle_favorite_slot(0, params, FakeParams()) is False
  assert params.get_bool("AlphaLongitudinalEnabled") is False


def test_toggle_favorite_slot_leaves_force_offroad_unrestricted():
  params = FakeParams()
  params.put("IsOnroad", True)
  params.put("ForceOffroad", False)
  params.put(FAVORITE_SLOTS_PARAM, [
    {"enabled": True, "show_onroad": True, "key": "ForceOffroad", "label": "Force Offroad"},
  ])

  assert toggle_favorite_slot(0, params, FakeParams()) is True
  assert params.get_bool("ForceOffroad") is True


def test_toggle_favorite_slot_action_increments_virtual_button_counter():
  params = FakeParams()
  memory = FakeParams()
  params.put(FAVORITE_SLOTS_PARAM, [
    {"enabled": True, "show_onroad": True, "key": FAVORITE_ACTION_DISTANCE_INCREASE, "label": "Distance + / RES"},
  ])

  assert toggle_favorite_slot(0, params, memory) is True
  assert memory.get_int(FAVORITE_ACTION_ACCEL_COUNTER) == 1


def test_toggle_favorite_slot_action_increments_traffic_mode_counter():
  params = FakeParams()
  memory = FakeParams()
  params.put(FAVORITE_SLOTS_PARAM, [
    {"enabled": True, "show_onroad": True, "key": FAVORITE_ACTION_TOGGLE_TRAFFIC_MODE, "label": "Toggle Traffic Mode"},
  ])

  assert toggle_favorite_slot(0, params, memory) is True
  assert memory.get_int(FAVORITE_ACTION_TRAFFIC_MODE_COUNTER) == 1
