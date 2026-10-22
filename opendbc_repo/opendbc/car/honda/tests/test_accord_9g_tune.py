"""accord_9g_tune: the TI car's longitudinal numbers are opt-in; the default is stock Dom behaviour."""
import dataclasses
import json

import pytest

from opendbc.car.honda import accord_9g_tune as tune_mod, carcontroller
from opendbc.car.honda.accord_9g_tune import STOCK, TI_CAR, load_tune, parse_tune, use_tune
from opendbc.car.honda.tests.test_honda_9g_pedal import pedal_interface
from opendbc.car.honda.values import CAR


@pytest.fixture(autouse=True)
def stock_tune():
  with use_tune(STOCK):
    yield


class TestStockDefault:
  def test_defaults_are_stock(self):
    assert STOCK.brake_accel_per_unit == carcontroller.NIDEC_BRAKE_ACCEL_PER_UNIT
    assert not (STOCK.aero_wind_brake or STOCK.gas_guard or STOCK.cruise_brake_deadband or STOCK.brake_onset_hold)

  def test_9g_brake_and_wind_match_other_nidec_cars(self):
    for v in (0.0, 2.3, 13.4, 22.4, 35.0):
      assert carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_ACCORD_9G) == \
        pytest.approx(carcontroller.get_honda_nidec_wind_brake(v, CAR.HONDA_CIVIC))
    for accel in (-3.0, -1.2, 0.0, 0.96):
      assert carcontroller.compute_gas_brake(accel, 20.0, CAR.HONDA_ACCORD_9G) == \
        carcontroller.compute_gas_brake(accel, 20.0, CAR.HONDA_CIVIC)

  def test_9g_pedal_runs_the_stock_learner_without_deadband(self, monkeypatch):
    cc = pedal_interface(monkeypatch, True)[0].CC
    assert cc.pedal_guard is None and cc.cruise_brake_deadband is None
    assert cc.bosch_gas_factor == 1.13  # stored value used as-is, no band clamp
    assert cc.log_pedal_learner  # logging only, stays on

  def test_ti_preset_restores_the_ti_car(self, monkeypatch):
    with use_tune(TI_CAR):
      cc = pedal_interface(monkeypatch, True)[0].CC
      assert cc.pedal_guard is not None and cc.cruise_brake_deadband is not None
      assert carcontroller.compute_gas_brake(-1.2, 20.0, CAR.HONDA_ACCORD_9G)[1] == pytest.approx(1.2 / 3.6)

  def test_custom_band_reaches_the_guard(self, monkeypatch):
    with use_tune(dataclasses.replace(STOCK, gas_guard=True, gas_factor_min=0.8, gas_factor_max=1.1, gas_factor_default=1.0)):
      cc = pedal_interface(monkeypatch, True)[0].CC
    assert (cc.pedal_guard.lo, cc.pedal_guard.hi) == (0.8, 1.1)
    assert cc.bosch_gas_factor == 1.1  # stored 1.13 clamped into the new band
    assert cc.pedal_guard.applied(1.1, 0.0) == pytest.approx(1.0)  # launch cap still applies


class TestParse:
  def test_presets_and_overrides(self):
    assert parse_tune({}) == STOCK
    assert parse_tune({"preset": "ti_car"}) == TI_CAR
    t = parse_tune({"preset": "ti_car", "brake_accel_per_unit": 4})
    assert t.brake_accel_per_unit == 4.0 and t.gas_guard
    assert parse_tune({"aero_wind_brake": True, "cruise_brake_deadband": True}).cruise_brake_deadband

  @pytest.mark.parametrize("data", [
    [], {"preset": "nope"}, {"preset": ["ti_car"]}, {"typo": 1}, {"gas_guard": 1}, {"brake_accel_per_unit": True},
    {"brake_accel_per_unit": "3.6"}, {"brake_accel_per_unit": 9.0}, {"brake_accel_per_unit": float("nan")},
    {"gas_factor_min": 1.5, "gas_factor_default": 1.4}, {"cruise_brake_deadband": True},
  ])
  def test_rejects_bad_input(self, data):
    with pytest.raises(ValueError):
      parse_tune(data)


class TestLoad:
  def test_missing_file_is_stock(self, tmp_path):
    assert load_tune(str(tmp_path / "none.json")) == STOCK

  def test_reads_file(self, tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"preset": "ti_car"}))
    assert load_tune(str(p)) == TI_CAR

  @pytest.mark.parametrize("text", ["{not json", json.dumps({"brake_accel_per_unit": 99})])
  def test_bad_file_falls_back_to_stock_and_logs(self, tmp_path, monkeypatch, text):
    p = tmp_path / "t.json"
    p.write_text(text)
    errors = []
    monkeypatch.setattr(tune_mod.carlog, "error", lambda msg, *a: errors.append(msg))
    assert load_tune(str(p)) == STOCK
    assert errors and "using stock values" in errors[0]

  def test_get_tune_reads_the_file_once(self, tmp_path, monkeypatch):
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"preset": "ti_car"}))
    monkeypatch.setattr(tune_mod, "TUNE_FILE", str(p))
    monkeypatch.setattr(tune_mod, "_cache", None)
    with use_tune(None):
      assert tune_mod.get_tune() == TI_CAR
      p.write_text("{}")
      assert tune_mod.get_tune() == TI_CAR
