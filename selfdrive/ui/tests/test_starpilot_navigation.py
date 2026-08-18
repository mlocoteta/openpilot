import hashlib
import json

from openpilot.selfdrive.ui.layouts.settings.starpilot.navigation import (
  MapboxSearchClient,
  _NavigationParams,
  _add_favorite_destination,
  _favorite_destination_id,
  _favorite_payload_for_galaxy,
  _load_favorite_destinations,
  _remove_favorite_destination,
  _update_favorite_destination,
)


def test_favorites_get_stable_ids_and_deduplicate_by_id():
  favorite = {
    "name": "Home",
    "latitude": "41.881832",
    "longitude": "-87.623177",
    "routeId": "main",
  }
  expected_id = _favorite_destination_id(favorite)

  added = _add_favorite_destination("[]", favorite)
  duplicate = _add_favorite_destination(json.dumps(added), {**favorite, "id": expected_id})

  assert added == [{**favorite, "latitude": 41.881832, "longitude": -87.623177, "id": expected_id}]
  assert duplicate == added
  assert _load_favorite_destinations(json.dumps(added)) == added


def test_favorite_id_preserves_galaxy_hash_input_for_numeric_coordinates():
  favorite = {"name": "One", "latitude": 1.0, "longitude": 2.0}
  expected = hashlib.sha1(b"2.0,1.0||One").hexdigest()

  assert _favorite_destination_id(favorite) == expected


def test_new_favorites_use_galaxys_default_route_id_contract():
  destination = {"name": "Home", "latitude": 1.0, "longitude": 2.0}

  assert _favorite_payload_for_galaxy(destination)["routeId"] == "main"
  assert _favorite_payload_for_galaxy({**destination, "routeId": "alternate"})["routeId"] == "alternate"


def test_favorite_special_locations_are_mutually_exclusive():
  raw = json.dumps([
    {"id": "home", "name": "Home", "latitude": 1, "longitude": 2, "is_home": True},
    {"id": "work", "name": "Work", "latitude": 3, "longitude": 4},
  ])

  updated = _update_favorite_destination(raw, {"id": "work"}, is_work=True)

  assert updated is not None
  assert updated[0].get("is_home") is True
  assert updated[1].get("is_work") is True
  assert updated[1].get("is_home") is None


def test_favorite_rename_can_target_legacy_route_id_without_coordinates():
  raw = json.dumps([{
    "name": "Old name",
    "routeId": "route-1",
    "latitude": 1,
    "longitude": 2,
  }])

  updated = _update_favorite_destination(raw, {"routeId": "route-1"}, name="New name")

  assert updated is not None
  assert updated[0]["name"] == "New name"


def test_favorite_can_be_removed_by_legacy_payload_identity():
  raw = json.dumps([
    {"name": "Keep", "latitude": 1, "longitude": 2},
    {"name": "Remove", "latitude": 3, "longitude": 4},
  ])

  updated = _remove_favorite_destination(raw, {"name": "Remove", "latitude": 3, "longitude": 4})

  assert [favorite["name"] for favorite in updated] == ["Keep"]


def test_navigation_params_commits_destination_and_clears_runtime_state():
  class FakeParams:
    def __init__(self):
      self.values = {}
      self.removed = []

    def get(self, key, encoding=None, default=None):
      value = self.values.get(key, default)
      if encoding == "utf-8" and isinstance(value, bytes):
        return value.decode("utf-8")
      return value

    def put(self, key, value):
      self.values[key] = value

    def remove(self, key):
      self.removed.append(key)
      self.values.pop(key, None)

  params = FakeParams()
  memory = FakeParams()
  navigation = _NavigationParams(params, memory)

  destination = navigation.set_destination({"name": "Home", "latitude": 1, "longitude": 2})
  assert navigation.clear_navigation() is True

  assert destination["place_name"] == "Home"
  assert params.values["ApiCache_NavDestinations"][0]["place_name"] == "Home"
  assert "NavDestination" in params.removed
  assert memory.removed == ["NavInstructionState", "NavInstructionCollapsed"]


class FakeResponse:
  def __init__(self, payload, status_code=200):
    self._payload = payload
    self.status_code = status_code

  def raise_for_status(self):
    if self.status_code >= 400:
      raise RuntimeError(f"HTTP {self.status_code}")

  def json(self):
    return self._payload


class FakeSession:
  def __init__(self):
    self.calls = []

  def get(self, url, *, params, timeout):
    self.calls.append((url, params, timeout))
    if url.endswith("/suggest"):
      return FakeResponse({
        "suggestions": [{
          "name": "OpenAI",
          "full_address": "OpenAI, San Francisco, CA",
          "mapbox_id": "place.openai",
        }],
      })
    return FakeResponse({
      "features": [{
        "properties": {"name": "OpenAI", "full_address": "OpenAI, San Francisco, CA"},
        "geometry": {"coordinates": [-122.401, 37.789]},
      }],
    })


def test_mapbox_search_and_retrieve_use_public_token_only():
  session = FakeSession()
  client = MapboxSearchClient(session=session)

  results = client.search("openai", "public-token", "session-token", proximity=(-122.4, 37.8), language="en")
  resolved = client.resolve(results[0], "public-token", "session-token")

  assert results[0].name == "OpenAI"
  assert results[0].latitude is None
  assert resolved.to_destination() == {
    "name": "OpenAI",
    "place_name": "OpenAI",
    "latitude": 37.789,
    "longitude": -122.401,
  }
  assert session.calls[0][1]["access_token"] == "public-token"
  assert "secret" not in session.calls[0][1]
