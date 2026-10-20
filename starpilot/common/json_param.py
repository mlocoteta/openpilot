import json


def load_json_param(value, default=None):
  """Decode a JSON-typed param value.

  Params.get() already returns the decoded dict/list for JSON-typed keys, while older
  STRING-typed keys and compat wrappers return str/bytes. Accept all of them; anything
  unparsable or of a different container type than `default` returns `default`.
  """
  if default is None:
    default = {}
  if isinstance(value, (bytes, bytearray)):
    value = value.decode("utf-8", errors="replace")
  if isinstance(value, str):
    value = value.strip()
    if not value:
      return default
    try:
      value = json.loads(value)
    except ValueError:
      return default
  if isinstance(default, (dict, list)) and not isinstance(value, type(default)):
    return default
  return value
