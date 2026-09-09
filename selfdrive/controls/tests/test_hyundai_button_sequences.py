from itertools import product
from types import SimpleNamespace

import pytest

from opendbc.car.hyundai.values import CAR as HYUNDAI_CAR, HyundaiFlags
from openpilot.selfdrive.controls.lib.drive_helpers import (
  get_lateral_active,
  update_lateral_fault_latch,
)
from openpilot.starpilot.controls import starpilot_card as spc


class FakeParams:
  def __init__(self, *args, **kwargs):
    self._store = {}

  def get(self, key):
    return self._store.get(key)

  def get_bool(self, key):
    return bool(self._store.get(key, False))

  def put_bool(self, key, value):
    self._store[key] = bool(value)

  def put(self, key, value):
    self._store[key] = value

  def get_int(self, key, default=0):
    return int(self._store.get(key, default))

  def put_int(self, key, value):
    self._store[key] = int(value)

  def put_bool_nonblocking(self, key, value):
    self.put_bool(key, value)


class FakeSM(dict):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.updated = {"starpilotPlan": False}


def make_sm():
  return FakeSM({
    "carControl": SimpleNamespace(longActive=False, latActive=False),
    "selfdriveState": SimpleNamespace(active=False, alertType=[], experimentalMode=False),
    "starpilotSelfdriveState": SimpleNamespace(alertType=[]),
    "starpilotPlan": SimpleNamespace(lateralCheck=True),
    "liveCalibration": SimpleNamespace(calPerc=100),
  })


def make_toggles(**overrides):
  defaults = {
    "always_on_lateral": True,
    "always_on_lateral_lkas": False,
    "always_on_lateral_main": False,
    "always_on_lateral_pause_speed": 0.0,
    "lkas_allowed_for_aol": True,
    "main_cruise_aol_toggle": False,
    "main_cruise_slc_adopt": False,
    "speed_limit_controller": False,
    "openpilot_longitudinal": False,
    "pulse_and_glide_available": False,
    "pulse_and_glide_via_cancel": False,
    "pulse_and_glide_via_cancel_long": False,
    "pulse_and_glide_via_cancel_very_long": False,
    "pulse_and_glide_via_lkas": False,
    "has_canfd_media_buttons": False,
    "experimental_mode_available": False,
    "conditional_experimental_mode": False,
    "conditional_chill_mode": False,
    "safe_mode": False,
  }
  for key in ("lkas", "main_cruise", "cancel", "cancel_long", "cancel_very_long", "distance",
              "distance_long", "distance_very_long", "mode", "mode_long", "mode_very_long",
              "star", "star_long", "star_very_long"):
    for prefix in ("experimental_mode_via_", "bookmark_via_", "force_coast_via_",
                   "pause_lateral_via_", "pause_longitudinal_via_", "switchback_mode_via_",
                   "traffic_mode_via_"):
      defaults[f"{prefix}{key}"] = False
  for slot in range(1, 4):
    for key in ("lkas", "main_cruise", "cancel", "distance"):
      defaults[f"favorite_{slot}_via_{key}"] = False
  defaults.update(overrides)
  return SimpleNamespace(**defaults)


def make_car_state(*, available=False, enabled=False, gear=None, button_type=None,
                   brake_pressed=False, v_ego=15.0):
  events = [] if button_type is None else [SimpleNamespace(type=button_type, pressed=True)]
  return SimpleNamespace(
    buttonEvents=events,
    cruiseState=SimpleNamespace(available=available, enabled=enabled),
    gearShifter=spc.GearShifter.drive if gear is None else gear,
    brakePressed=brake_pressed,
    gasPressed=False,
    standstill=False,
    vEgo=v_ego,
  )


HYUNDAI_PLATFORM_CASES = (
  pytest.param(HYUNDAI_CAR.HYUNDAI_ELANTRA_HEV_2024,
               HyundaiFlags.CHECKSUM_CRC8 | HyundaiFlags.CAMERA_SCC | HyundaiFlags.HYBRID,
               id="elantra-hybrid-2024-26"),
  pytest.param(HYUNDAI_CAR.HYUNDAI_SONATA,
               HyundaiFlags.MANDO_RADAR | HyundaiFlags.CHECKSUM_CRC8,
               id="sonata"),
  pytest.param(HYUNDAI_CAR.HYUNDAI_SONATA_HYBRID,
               HyundaiFlags.MANDO_RADAR | HyundaiFlags.CHECKSUM_CRC8 | HyundaiFlags.HYBRID,
               id="sonata-hybrid"),
  pytest.param(HYUNDAI_CAR.HYUNDAI_KONA_NON_SCC,
               HyundaiFlags.NON_SCC | HyundaiFlags.ALT_LIMITS,
               id="kona-non-scc"),
)


@pytest.mark.parametrize(("fingerprint", "flags"), HYUNDAI_PLATFORM_CASES)
@pytest.mark.parametrize("mapping", ("lkas", "main"))
def test_hyundai_aol_mapping_survives_brake_and_cruise_reenable(
  monkeypatch, tmp_path, fingerprint, flags, mapping,
):
  monkeypatch.setattr(spc, "Params", FakeParams)
  monkeypatch.setattr(spc, "ERROR_LOGS_PATH", tmp_path)

  card = spc.StarPilotCard(
    SimpleNamespace(brand="hyundai", carFingerprint=fingerprint, flags=flags),
    SimpleNamespace(alternativeExperience=spc.ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL),
  )
  toggles = make_toggles(
    always_on_lateral_lkas=mapping == "lkas",
    main_cruise_aol_toggle=mapping == "main",
  )
  sm = make_sm()
  starpilot_car_state = SimpleNamespace(distancePressed=False)
  button_type = spc.ButtonType.lkas if mapping == "lkas" else spc.ButtonType.mainCruise

  pressed = make_car_state(button_type=button_type)
  card.update(pressed, starpilot_car_state, sm, toggles)
  assert pressed.buttonEvents
  assert starpilot_car_state.alwaysOnLateralAllowed is True
  assert starpilot_car_state.alwaysOnLateralEnabled is True

  active = make_car_state(available=True, enabled=True)
  sm["selfdriveState"].active = True
  card.update(active, starpilot_car_state, sm, toggles)

  braking = make_car_state(available=True, enabled=False, brake_pressed=True)
  sm["selfdriveState"].active = False
  card.update(braking, starpilot_car_state, sm, toggles)
  assert starpilot_car_state.alwaysOnLateralEnabled is True

  reenabled = make_car_state(available=True, enabled=True)
  sm["selfdriveState"].active = True
  card.update(reenabled, starpilot_car_state, sm, toggles)
  assert starpilot_car_state.alwaysOnLateralAllowed is True
  assert starpilot_car_state.alwaysOnLateralEnabled is True


@pytest.mark.parametrize(("fingerprint", "flags"), HYUNDAI_PLATFORM_CASES)
@pytest.mark.parametrize("mapping", ("lkas", "main"))
def test_hyundai_button_sequences_are_total(monkeypatch, tmp_path, fingerprint, flags, mapping):
  monkeypatch.setattr(spc, "Params", FakeParams)
  monkeypatch.setattr(spc, "ERROR_LOGS_PATH", tmp_path)

  card = spc.StarPilotCard(
    SimpleNamespace(brand="hyundai", carFingerprint=fingerprint, flags=flags),
    SimpleNamespace(alternativeExperience=spc.ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL),
  )
  toggles = make_toggles(
    always_on_lateral_lkas=mapping == "lkas",
    main_cruise_aol_toggle=mapping == "main",
  )
  sm = make_sm()
  starpilot_car_state = SimpleNamespace(distancePressed=False)
  button_types = (None, spc.ButtonType.lkas, spc.ButtonType.mainCruise,
                  spc.ButtonType.cancel, spc.ButtonType.accelCruise,
                  spc.ButtonType.decelCruise)

  for sequence in product(button_types, repeat=3):
    for frame, button_type in enumerate(sequence):
      gear = spc.GearShifter.neutral if frame == 1 else spc.GearShifter.drive
      car_state = make_car_state(
        available=frame != 1,
        enabled=frame == 2,
        gear=gear,
        button_type=button_type,
        brake_pressed=frame == 1,
      )
      sm["selfdriveState"].active = frame == 2
      result = card.update(car_state, starpilot_car_state, sm, toggles)
      assert not result.alwaysOnLateralEnabled or result.alwaysOnLateralAllowed


def test_elantra_hybrid_fault_latch_rearms_on_cruise_rising_edge():
  faulted = False
  previous_cruise_enabled = False

  def step(cruise_enabled, steer_fault_temporary):
    nonlocal faulted, previous_cruise_enabled
    cruise_reenabled = cruise_enabled and not previous_cruise_enabled
    faulted = update_lateral_fault_latch(
      faulted,
      lateral_requested=True,
      steer_fault_temporary=steer_fault_temporary,
      reset=cruise_reenabled,
    )
    lateral_active = get_lateral_active(
      False, False, True, steer_fault_temporary, False,
      False, False, True, faulted,
    )
    previous_cruise_enabled = cruise_enabled
    return lateral_active

  assert step(True, False) is True
  assert step(False, True) is False
  assert step(False, False) is False
  assert step(True, False) is True


@pytest.mark.parametrize("gear", (spc.GearShifter.neutral, spc.GearShifter.park, spc.GearShifter.reverse))
def test_lkas_aol_does_not_stick_enabled_in_non_driving_gears(monkeypatch, tmp_path, gear):
  monkeypatch.setattr(spc, "Params", FakeParams)
  monkeypatch.setattr(spc, "ERROR_LOGS_PATH", tmp_path)

  card = spc.StarPilotCard(
    SimpleNamespace(brand="hyundai", carFingerprint=HYUNDAI_CAR.HYUNDAI_SONATA),
    SimpleNamespace(alternativeExperience=spc.ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL),
  )
  toggles = make_toggles(always_on_lateral_lkas=True)
  sm = make_sm()
  starpilot_car_state = SimpleNamespace(distancePressed=False)

  card.update(make_car_state(button_type=spc.ButtonType.lkas), starpilot_car_state, sm, toggles)
  result = card.update(make_car_state(gear=gear), starpilot_car_state, sm, toggles)
  assert result.alwaysOnLateralEnabled is False
