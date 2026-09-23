"""Synthetic-input coverage of the real StarPilotCard latch across all platforms.

CP/FPCP come from current interfaces with empty CAN fingerprints/firmware and
isolated default settings. These tests do not model CAN safety, selfdrived,
physical buttons, firmware-dependent variants, or vehicle actuation. Skipped
active sequences are coverage gaps, not evidence of fleet compatibility.
"""

import importlib
from types import SimpleNamespace

import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.car_helpers import interfaces
from opendbc.car.values import PLATFORMS
from openpilot.common import params as params_module
from openpilot.starpilot.controls.tests.test_starpilot_card import FakeParams, make_car_state, make_sm, make_toggles, spc


class FleetParams(FakeParams):
  def get_bool(self, key, default=False):
    return bool(self._store.get(key, default))

  def get_float(self, key, default=0.0):
    return float(self._store.get(key, default))


@pytest.fixture
def isolated_settings(monkeypatch, tmp_path):
  # Interfaces have both imported Params aliases and dynamic imports. The Pre-AP
  # configuration also retains a Params instance, so isolate all three forms.
  monkeypatch.setattr(params_module, "Params", FleetParams)
  for name in {"opendbc.car.interfaces", *(interface.__module__ for interface in interfaces.values())}:
    module = importlib.import_module(name)
    if hasattr(module, "Params"):
      monkeypatch.setattr(module, "Params", FleetParams)
  monkeypatch.setattr(importlib.import_module("opendbc.car.tesla.preap.nap_conf"), "_params", FleetParams())
  monkeypatch.setattr(spc, "Params", FleetParams)
  monkeypatch.setattr(spc, "ERROR_LOGS_PATH", tmp_path)


def fleet_config(platform, mode, enabled=True):
  toggles = make_toggles(always_on_lateral=enabled, always_on_lateral_main=mode == "main",
                         always_on_lateral_lkas=mode == "engage", lkas_allowed_for_aol=mode == "engage",
                         always_on_lateral_pause_speed=5.0)
  fingerprint = gen_empty_fingerprint()
  interface = interfaces[platform]
  cp = interface.get_params(platform, fingerprint, [], False, False, docs=False, starpilot_toggles=toggles)
  fp = interface.get_starpilot_params(platform, fingerprint, [], cp, toggles)
  assert cp.carFingerprint == platform
  # Card startup installs this feature bit after the interface returns FPCP.
  # This is an explicit feature-on fixture, not a call to the full card daemon.
  if enabled and spc.always_on_lateral_available(cp):
    cp.alternativeExperience |= spc.ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL
    fp.alternativeExperience |= spc.ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL
  else:
    cp.alternativeExperience &= ~spc.ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL
    fp.alternativeExperience &= ~spc.ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL
  return cp, fp, toggles


class Sequence:
  def __init__(self, cp, fp, toggles):
    self.card = spc.StarPilotCard(cp, fp)
    self.toggles = toggles
    self.sm = make_sm()
    self.cs = make_car_state()
    self.output = SimpleNamespace(distancePressed=False)
    self.preap_authorized = None

  def step(self, expected, *, frames=1):
    for _ in range(frames):
      kwargs = {} if self.preap_authorized is None else {"preap_authorized": self.preap_authorized}
      output = self.card.update(self.cs, self.output, self.sm, self.toggles, **kwargs)
      assert output.alwaysOnLateralEnabled is expected
    return output

  def engage(self):
    self.cs.cruiseState.available = self.cs.cruiseState.enabled = True
    self.sm["selfdriveState"].active = True
    self.sm["carControl"].longActive = True
    self.cs.brakePressed = False
    self.cs.vEgo = 15.0
    self.cs.standstill = False
    self.cs.gearShifter = spc.GearShifter.drive

  def disengage(self):
    self.cs.cruiseState.enabled = False
    self.sm["selfdriveState"].active = False
    self.sm["carControl"].longActive = False


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
def test_fleet_aol_disabled_configuration(platform, isolated_settings):
  cp, fp, toggles = fleet_config(platform, "main", enabled=False)
  sequence = Sequence(cp, fp, toggles)
  sequence.step(False)
  sequence.engage()
  sequence.step(False, frames=20)
  sequence.disengage()
  sequence.cs.brakePressed = True
  sequence.step(False, frames=20)


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
@pytest.mark.parametrize("mode", ("main", "engage"))
def test_fleet_aol_state_sequence(platform, mode, isolated_settings, record_property):
  cp, fp, toggles = fleet_config(platform, mode)
  record_property("platform", platform)
  record_property("brand", cp.brand)
  record_property("mode", mode)
  record_property("fixture", "empty fingerprint/firmware; synthetic normalized state; no CAN/safety or selfdrived")
  if not spc.always_on_lateral_available(cp):
    # Even a stale feature bit must not grant a platform denied by current policy.
    fp.alternativeExperience |= spc.ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL
    denied = Sequence(cp, fp, toggles)
    denied.engage()
    denied.step(False, frames=20)
    denied.disengage()
    denied.step(False, frames=20)
    pytest.skip(f"AOL active coverage gap: current platform policy excludes {platform}; denial checked")
  if cp.dashcamOnly or cp.notCar:
    pytest.skip(f"AOL active coverage gap: empty-fingerprint configuration has dashcamOnly={cp.dashcamOnly}, notCar={cp.notCar}")
  if platform == "TESLA_MODEL_S_PREAP":
    denied = Sequence(cp, fp, toggles)
    denied.engage()
    denied.step(False, frames=20)
    denied.disengage()
    denied.step(False, frames=20)
    pytest.skip("AOL active coverage gap: Pre-AP requires external authorization; synthetic cruise state cannot supply it; denial checked")

  sequence = Sequence(cp, fp, toggles)
  sequence.step(False, frames=20)
  sequence.engage()
  sequence.step(True, frames=120)

  # Braking out of longitudinal at speed leaves a stable AOL-only state.
  sequence.disengage()
  sequence.cs.brakePressed = True
  sequence.step(True, frames=120)
  assert not sequence.sm["selfdriveState"].active
  assert not sequence.sm["carControl"].longActive

  # Both native and StarPilot immediate-disable sources suppress lateral.
  for source in ("selfdriveState", "starpilotSelfdriveState"):
    sequence.sm[source].alertType = f"controlsMismatch/{spc.ET.IMMEDIATE_DISABLE}"
    sequence.step(False, frames=20)
    sequence.sm[source].alertType = ""
    sequence.step(True, frames=20)
  sequence.sm["selfdriveState"].alertType = f"speedTooLow/{spc.ET.IMMEDIATE_DISABLE}"
  sequence.step(True, frames=20)  # Explicit existing longitudinal-only exception.
  sequence.sm["selfdriveState"].alertType = ""

  sequence.cs.vEgo = 2.0
  sequence.step(False, frames=20)
  sequence.cs.brakePressed = False
  sequence.step(True, frames=20)
  sequence.cs.vEgo = 0.0
  sequence.cs.brakePressed = sequence.cs.standstill = True
  sequence.step(True, frames=20)  # Existing standstill exception to brake pause.

  sequence.sm["liveCalibration"].calPerc = 0
  sequence.step(False, frames=20)
  sequence.sm["liveCalibration"].calPerc = 100
  sequence.step(True)
  sequence.sm["starpilotPlan"].lateralCheck = False
  sequence.step(False, frames=20)
  sequence.sm["starpilotPlan"].lateralCheck = True
  sequence.step(True)

  for gear in (spc.GearShifter.park, spc.GearShifter.reverse):
    sequence.cs.gearShifter = gear
    sequence.step(False, frames=20)
  sequence.engage()
  sequence.step(True, frames=20)
  sequence.disengage()

  # Explicit mode-off must remain off rather than repeatedly re-latching.
  if mode == "main":
    sequence.cs.cruiseState.available = False
    sequence.step(False)
  else:
    sequence.cs.buttonEvents = [SimpleNamespace(type=spc.ButtonType.lkas, pressed=True)]
    sequence.step(False)
    sequence.cs.buttonEvents = []
  sequence.step(False, frames=120)


def test_preap_aol_explicit_authorization_boundary(isolated_settings):
  cp, fp, toggles = fleet_config("TESLA_MODEL_S_PREAP", "main")
  if not spc.always_on_lateral_available(cp):
    pytest.skip("Pre-AP AOL unavailable by current policy")
  sequence = Sequence(cp, fp, toggles)
  sequence.engage()
  sequence.step(False, frames=20)
  sequence.preap_authorized = True
  sequence.step(True, frames=20)
  sequence.disengage()
  sequence.step(True, frames=20)
  sequence.sm["selfdriveState"].alertType = f"controlsMismatch/{spc.ET.IMMEDIATE_DISABLE}"
  sequence.step(False, frames=20)
  sequence.sm["selfdriveState"].alertType = ""
  sequence.step(True, frames=20)
  sequence.preap_authorized = False
  sequence.step(False, frames=120)
