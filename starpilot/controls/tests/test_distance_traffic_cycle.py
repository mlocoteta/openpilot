from types import SimpleNamespace

import pytest

from openpilot.starpilot.common import distance_cycle as dc
from openpilot.starpilot.common.starpilot_variables import BUTTON_FUNCTIONS
from openpilot.starpilot.controls import starpilot_card as spc
from openpilot.starpilot.controls.tests.test_starpilot_card import FakeParams, make_car_state, make_sm, make_toggles

AGG, STD, REL = dc.AGGRESSIVE, dc.STANDARD, dc.RELAXED
DISTANCE_KEYS = ("distance", "distance_long", "distance_very_long")
DISTANCE_ACTIONS = ("experimental_mode", "bookmark", "force_coast", "pulse_and_glide", "pause_lateral",
                    "pause_longitudinal", "switchback_mode", "traffic_mode")


class CycleParams(FakeParams):
  def put_nonblocking(self, key, value):
    self.put(key, value)


def cycle_toggles(**overrides):
  values = {f"{action}_via_{key}": False for action in DISTANCE_ACTIONS for key in DISTANCE_KEYS}
  values.update(distance_cycle_via_distance=True, distance_traffic_cycle=True)
  values.update(overrides)
  return make_toggles(**values)


@pytest.fixture
def card(monkeypatch, tmp_path):
  monkeypatch.setattr(spc, "Params", CycleParams)
  monkeypatch.setattr(spc, "ERROR_LOGS_PATH", tmp_path)
  monkeypatch.setattr(dc, "TRAFFIC_STATE_PATH", tmp_path / "distance_cycle_traffic")
  return spc.StarPilotCard(SimpleNamespace(brand="honda"), SimpleNamespace(alternativeExperience=0))


def cycle_sm(personality):
  sm = make_sm()
  sm["selfdriveState"].personality = personality
  return sm


def short_press(card, sm, toggles, frames=3):
  pressed = SimpleNamespace(distancePressed=True)
  for _ in range(frames):
    card.update(make_car_state(), pressed, sm, toggles)
  return card.update(make_car_state(), SimpleNamespace(distancePressed=False), sm, toggles)


def selfdrived_reads_param(card, sm):
  sm["selfdriveState"].personality = card.params.get("LongitudinalPersonality")
  card._distance_cycle_personality = None  # selfdrived caught up


def test_next_cycle_state_order():
  assert dc.next_cycle_state(REL, True) == (AGG, False)   # traffic -> aggressive
  assert dc.next_cycle_state(AGG, True) == (AGG, False)
  assert dc.next_cycle_state(AGG, False) == (STD, False)  # aggressive -> standard
  assert dc.next_cycle_state(STD, False) == (REL, False)  # standard -> relaxed
  assert dc.next_cycle_state(REL, False) == (AGG, True)   # relaxed -> traffic (aggressive underneath)


def test_full_cycle_returns_to_start():
  state = (AGG, True)
  seen = []
  for _ in range(4):
    state = dc.next_cycle_state(*state)
    seen.append(dc.cycle_lead_distance_bars(*state))
  assert state == (AGG, True)
  assert seen == [2, 3, 4, 1]


@pytest.mark.parametrize("personality, traffic, bars", (
  (AGG, True, 1), (STD, True, 1), (AGG, False, 2), (STD, False, 3), (REL, False, 4),
))
def test_cycle_lead_distance_bars(personality, traffic, bars):
  assert dc.cycle_lead_distance_bars(personality, traffic) == bars


def test_honda_acc_hud_encodes_four_bars_as_zero():
  from opendbc.can.packer import CANPacker
  from opendbc.can.parser import CANParser
  from opendbc.car.honda.hondacan import create_acc_hud
  from opendbc.car.honda.values import CAR

  dbc = "honda_accord_2017_can_generated"
  packer = CANPacker(dbc)
  CP = SimpleNamespace(carFingerprint=CAR.HONDA_ACCORD_9G)
  for bars, raw in ((1, 1), (2, 2), (3, 3), (4, 0)):
    hud = SimpleNamespace(leadDistanceBars=bars, leadVisible=True)
    stock_acc_hud = {"FCM_OFF": 0, "FCM_OFF_2": 0, "FCM_PROBLEM": 0, "ICONS": 0}
    address, dat, _bus = create_acc_hud(packer, 0, CP, True, 20.0, 0.0, hud, 30, False, stock_acc_hud)
    assert address == 780
    assert (dat[5] >> 6) & 3 == raw
    parser = CANParser(dbc, [("ACC_HUD", 0)], 0)
    parser.update([(0, [(780, dat, 0)])])
    assert parser.vl["ACC_HUD"]["HUD_DISTANCE"] == raw


def test_short_press_cycles_all_four_states(card):
  toggles = cycle_toggles()
  sm = cycle_sm(REL)
  card.params.put("LongitudinalPersonality", REL)

  expected = [(AGG, True), (AGG, False), (STD, False), (REL, False), (AGG, True)]
  for personality, traffic in expected:
    ret = short_press(card, sm, toggles)
    assert ret.trafficModeEnabled is traffic
    assert card.params.get("LongitudinalPersonality") == personality
    selfdrived_reads_param(card, sm)


def test_rapid_presses_use_last_written_personality(card):
  # selfdriveState lags our param write by up to ~0.1 s; a quick second press must not reuse the stale value.
  toggles = cycle_toggles()
  sm = cycle_sm(AGG)
  short_press(card, sm, toggles)
  short_press(card, sm, toggles)
  assert card.params.get("LongitudinalPersonality") == REL
  ret = short_press(card, sm, toggles)
  assert ret.trafficModeEnabled is True
  assert card.params.get("LongitudinalPersonality") == AGG


def test_cycle_works_disengaged_and_long_press_untouched(card):
  toggles = cycle_toggles()
  sm = cycle_sm(STD)
  assert sm["carControl"].longActive is False
  short_press(card, sm, toggles)
  assert card.params.get("LongitudinalPersonality") == REL

  # A long hold must not also fire the short-press cycle.
  handled = []
  card.handle_button_event = lambda key, _sm, _toggles: handled.append(key)
  pressed = SimpleNamespace(distancePressed=True)
  for _ in range(card.long_press_threshold + 2):
    card.update(make_car_state(), pressed, sm, toggles)
  card.update(make_car_state(), SimpleNamespace(distancePressed=False), sm, toggles)
  assert handled == ["distance_long"]


def test_very_long_traffic_toggle_still_works(card):
  toggles = cycle_toggles(traffic_mode_via_distance_very_long=True)
  sm = cycle_sm(STD)
  sm["carControl"].longActive = True
  card.handle_button_event("distance_very_long", sm, toggles)
  assert card.traffic_mode_enabled is True
  # Next short press leaves traffic to aggressive.
  card.handle_button_event("distance", sm, toggles)
  assert card.traffic_mode_enabled is False
  assert card.params.get("LongitudinalPersonality") == AGG


def test_cycle_disabled_keeps_old_behavior(card):
  toggles = cycle_toggles(distance_cycle_via_distance=False, distance_traffic_cycle=False)
  sm = cycle_sm(REL)
  ret = short_press(card, sm, toggles)
  assert ret.trafficModeEnabled is False
  assert card.params.get("LongitudinalPersonality") is None


def test_safe_mode_blocks_cycle(card):
  card.params.put_bool("SafeMode", True)
  short_press(card, cycle_sm(REL), cycle_toggles())
  assert card.traffic_mode_enabled is False
  assert card.params.get("LongitudinalPersonality") is None


def test_traffic_state_persists_across_restart(card, monkeypatch):
  monkeypatch.setattr(spc, "save_traffic_state_nonblocking",
                      lambda enabled: dc._write_traffic_state(dc.TRAFFIC_STATE_PATH, enabled))
  toggles = cycle_toggles()
  short_press(card, cycle_sm(REL), toggles)
  assert card.traffic_mode_enabled is True
  assert dc.load_traffic_state() is True

  restarted = spc.StarPilotCard(SimpleNamespace(brand="honda"), SimpleNamespace(alternativeExperience=0))
  ret = restarted.update(make_car_state(), SimpleNamespace(distancePressed=False), cycle_sm(AGG), toggles)
  assert ret.trafficModeEnabled is True

  # Leaving traffic persists "off".
  short_press(restarted, cycle_sm(AGG), toggles)
  assert dc.load_traffic_state() is False


def test_nonblocking_save_writes_file(card):
  dc.save_traffic_state_nonblocking(True).join()
  assert dc.TRAFFIC_STATE_PATH.read_text() == "1\n"


def test_traffic_state_not_restored_when_cycle_off(card):
  dc.save_traffic_state_nonblocking(True).join()
  ret = card.update(make_car_state(), SimpleNamespace(distancePressed=False), cycle_sm(AGG),
                    cycle_toggles(distance_cycle_via_distance=False, distance_traffic_cycle=False))
  assert ret.trafficModeEnabled is False


def test_button_function_id_is_unique():
  assert BUTTON_FUNCTIONS["PERSONALITY_TRAFFIC_CYCLE"] == dc.PERSONALITY_TRAFFIC_CYCLE == 15
  assert list(BUTTON_FUNCTIONS.values()).count(15) == 1


def test_stale_toggles_fall_back_to_button_params(monkeypatch):
  # Old starpilot_process toggles have no cycle flags; onroad processes read the button params once.
  monkeypatch.setattr(dc, "_fallback_cycle_keys", None)
  monkeypatch.setattr(dc, "_read_fallback_cycle_keys", lambda: frozenset({"distance"}))
  stale = SimpleNamespace(openpilot_longitudinal=True)
  assert dc.distance_cycle_enabled(stale) is True
  assert dc.distance_cycle_via(stale, "distance") is True
  assert dc.distance_cycle_via(stale, "distance_long") is False
  assert dc.distance_cycle_via(stale, "lkas") is False
  assert dc.distance_cycle_enabled(SimpleNamespace(openpilot_longitudinal=False)) is False


def test_fresh_toggles_win_over_fallback(monkeypatch):
  monkeypatch.setattr(dc, "_fallback_cycle_keys", frozenset({"distance"}))
  fresh = SimpleNamespace(openpilot_longitudinal=True, distance_traffic_cycle=False, distance_cycle_via_distance=False)
  assert dc.distance_cycle_enabled(fresh) is False
  assert dc.distance_cycle_via(fresh, "distance") is False
