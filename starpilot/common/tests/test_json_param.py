import json

from openpilot.starpilot.common.json_param import load_json_param

OVERRIDES = {"schemaVersion": 1, "baseFrictionThresholds": {"standard": {"speedKnots": [0, 5, 10, 15, 25],
                                                                          "values": [2.0, 1.2, 0.45, 0.35, 0.3]}}}


class JsonTypedParams:
  """Params.get for a JSON-typed key: returns the decoded object even when encoding= is passed."""

  def __init__(self, store):
    self.store = store

  def get(self, key, encoding=None):
    raw = self.store.get(key)
    return json.loads(raw) if raw is not None else None


def test_decoded_dict_passes_through():
  # regression: StarPilotVariables did json.loads(<dict>) -> TypeError -> flm_active_overrides = {} always
  params = JsonTypedParams({"FLMActiveOverrides": json.dumps(OVERRIDES)})
  value = params.get("FLMActiveOverrides", encoding="utf-8")
  assert isinstance(value, dict)
  assert load_json_param(value, {}) == OVERRIDES


def test_str_and_bytes_are_parsed():
  assert load_json_param(json.dumps(OVERRIDES), {}) == OVERRIDES
  assert load_json_param(json.dumps(OVERRIDES).encode(), {}) == OVERRIDES
  assert load_json_param('[1, 2]', []) == [1, 2]


def test_missing_empty_or_bad_values_fall_back():
  assert load_json_param(None, {}) == {}
  assert load_json_param("", {}) == {}
  assert load_json_param(b"  ", {}) == {}
  assert load_json_param("{not json", {}) == {}
  assert load_json_param([1, 2], {}) == {}  # wrong container type
  assert load_json_param({"a": 1}, []) == []
  assert load_json_param(None) == {}


def test_real_params_json_key_returns_dict():
  from openpilot.common.params import Params
  params = Params()
  params.put("FLMActiveOverrides", OVERRIDES)
  value = params.get("FLMActiveOverrides", encoding="utf-8")
  assert isinstance(value, dict)  # json.loads(value) would raise TypeError here
  assert load_json_param(value, {}) == OVERRIDES
  params.remove("FLMActiveOverrides")
  assert load_json_param(params.get("FLMActiveOverrides", encoding="utf-8"), {}) == {}
