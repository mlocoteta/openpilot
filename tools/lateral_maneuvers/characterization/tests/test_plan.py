import json

import numpy as np
import pytest

from openpilot.tools.lateral_maneuvers.characterization import plan as P


def _plan(blocks, **extra):
  return P.normalize_plan({"version": 1, "blocks": blocks, **extra})


def test_default_plan_is_valid_and_drivable_in_40_min():
  plan = P.normalize_plan(P.build_plan("default"))
  assert len(plan["blocks"]) == 25
  assert {b["speed_mph"] for b in plan["blocks"]} == {8, 12, 15, 20, 30}
  assert 25 <= plan["estimated_minutes"] <= 40
  quick = P.normalize_plan(P.build_plan("quick"))
  assert quick["estimated_minutes"] < plan["estimated_minutes"] / 2


def test_default_variants_cover_requested_settings():
  plan = P.normalize_plan(P.build_plan("default"))
  settings = [b["settings"] for b in plan["blocks"] if b["speed_mph"] == 8]
  assert {s["steer_delay"] for s in settings} == {0.01, "auto", 0.5}
  tables = {tuple(s["friction_table"]) for s in settings}
  assert tables == {(0.3,) * 5, (2.0, 1.2, 0.45, 0.35, 0.30)}
  assert {s["ti_steer_kp"] for s in settings} == {0.5, 0.8}


def test_reduced_plan_from_cli(tmp_path, capsys):
  out = tmp_path / "plan.json"
  assert P.main(["generate", "--speeds", "8,12", "--variants", "A,F", "--maneuvers", "quick", "-o", str(out)]) == 0
  plan = P.load_plan(str(out))
  assert [b["id"] for b in plan["blocks"]] == ["s08A", "s08F", "s12A", "s12F"]
  assert P.main(["check", str(out)]) == 0


def test_missing_plan_file_means_stock_behaviour(tmp_path):
  assert P.load_plan(str(tmp_path / "absent.json")) is None


def test_invalid_json_raises(tmp_path):
  path = tmp_path / "bad.json"
  path.write_text("{nope")
  with pytest.raises(P.PlanError):
    P.load_plan(str(path))


@pytest.mark.parametrize("speed,limit", [(8, 0.6), (12, 0.6), (15, 1.0), (30, 1.0)])
def test_amplitude_clamped_by_speed(speed, limit):
  plan = _plan([{"speed_mph": speed, "settings": {"ti_steer_kp": 0.5}, "maneuvers": [
    {"type": "step", "amplitude": 2.5, "hold_s": 0.5},
    {"type": "sine", "freq_hz": 0.7, "amplitude": -3.0, "cycles": 2},
  ]}], max_displacement_m=6.0)
  for m in plan["blocks"][0]["maneuvers"]:
    assert m["amplitude"] <= limit + 1e-9
    _, accel = P.maneuver_profile(m)
    assert np.max(np.abs(accel)) <= limit + 1e-9
    assert m["notes"]


def test_sine_frequency_and_cycles_clamped():
  m = _plan([{"speed_mph": 20, "settings": {"ti_steer_kp": 0.5}, "maneuvers": [
    {"type": "sine", "freq_hz": 3.0, "amplitude": 0.3, "cycles": 50}]}])["blocks"][0]["maneuvers"][0]
  assert m["freq_hz"] == P.SINE_FREQ_MAX
  assert m["cycles"] == P.SINE_CYCLES_MAX


def test_step_hold_shortened_to_displacement_limit():
  m = _plan([{"speed_mph": 20, "settings": {"ti_steer_kp": 0.5}, "maneuvers": [
    {"type": "step", "amplitude": 0.6, "hold_s": 3.0}]}])["blocks"][0]["maneuvers"][0]
  assert m["hold_s"] < 3.0
  assert m["displacement_m"] <= P.DEFAULT_MAX_DISPLACEMENT_M + 0.05
  assert any("shortened" in n for n in m["notes"])


@pytest.mark.parametrize("spec", [
  {"type": "step", "amplitude": 0.3, "hold_s": 3.0},
  {"type": "sine", "freq_hz": 0.2, "amplitude": 0.3, "cycles": 2},
  {"type": "sine", "freq_hz": 0.7, "amplitude": 0.3, "cycles": 4},
])
def test_profiles_return_heading_and_offset_to_zero(spec):
  m = P.normalize_maneuver(spec, 20, P.DEFAULT_MAX_DISPLACEMENT_M)
  t, accel = P.maneuver_profile(m)
  assert accel[0] == 0.0 or m["type"] == "step"
  assert accel[-1] == 0.0
  heading_rate_integral = np.sum(accel) * P.DT  # lateral velocity at the end
  assert abs(heading_rate_integral) < 0.02
  if m["type"] == "step":
    pos = np.cumsum(np.cumsum(accel) * P.DT) * P.DT
    assert abs(pos[-1]) < 0.1  # doublet returns to the start line


def test_sine_fit_window_is_full_amplitude_integer_cycles():
  m = P.normalize_maneuver({"type": "sine", "freq_hz": 0.4, "amplitude": 0.3, "cycles": 3}, 20, 3.0)
  meta = P.maneuver_meta(m)
  t0, t1 = meta["fit_window"]
  assert (t1 - t0) * m["freq_hz"] == pytest.approx(2.0)
  t, accel = P.maneuver_profile(m)
  sel = (t >= t0) & (t <= t1)
  assert np.max(np.abs(accel[sel])) == pytest.approx(0.3, abs=1e-3)


def test_step_meta_transitions_match_profile():
  m = P.normalize_maneuver({"type": "step", "amplitude": 0.3, "hold_s": 2.0}, 20, 3.0)
  t, accel = P.maneuver_profile(m)
  for tr in P.maneuver_meta(m)["transitions"]:
    i = int(round(tr["t"] / P.DT))
    assert accel[i] == pytest.approx(tr["to"])


@pytest.mark.parametrize("settings,error", [
  ({"steer_friction": 0.1}, "cannot be switched live"),
  ({"bogus": 1}, "unknown setting"),
  ({"friction_table": "nope"}, "unknown friction_table"),
  ({"friction_table": [0.3, 0.3]}, "needs 5 values"),
  ({"steer_delay": "fast"}, "finite number"),
])
def test_bad_settings_rejected(settings, error):
  with pytest.raises(P.PlanError, match=error):
    _plan([{"speed_mph": 20, "settings": settings}])


def test_settings_clamped_and_tagged():
  notes = []
  s = P.normalize_settings({"steer_delay": 5.0, "ti_steer_kp": 0.01, "friction_table": [9, 1, 1, 1, 1]}, notes)
  assert s["steer_delay"] == 1.0
  assert s["ti_steer_kp"] == P.TI_STEER_KP_RANGE[0]
  assert s["friction_table"][0] == P.FRICTION_VALUE_RANGE[1]
  assert s["friction_table_name"] == "custom"
  assert len(notes) == 3
  assert P.settings_tag({"steer_delay": "auto", "friction_table": [0.3] * 5, "friction_table_name": "flat",
                         "ti_steer_kp": 0.5}) == "dauto fflat kp0.50"


@pytest.mark.parametrize("block", [
  {"speed_mph": 2, "settings": {"ti_steer_kp": 0.5}},
  {"speed_mph": 80, "settings": {"ti_steer_kp": 0.5}},
  {"speed_mph": 20},
  {"speed_mph": 20, "variant": "Z"},
  {"speed_mph": 20, "settings": {"ti_steer_kp": 0.5}, "maneuvers": [{"type": "spin"}]},
])
def test_bad_blocks_rejected(block):
  with pytest.raises(P.PlanError):
    _plan([block])


def test_block_settings_override_variant():
  plan = _plan([{"speed_mph": 20, "variant": "A", "settings": {"ti_steer_kp": 0.9}}],
               variants={"A": {"steer_delay": 0.01, "friction_table": "flat", "ti_steer_kp": 0.5}})
  assert plan["blocks"][0]["settings"]["ti_steer_kp"] == 0.9
  assert plan["blocks"][0]["settings"]["steer_delay"] == 0.01


def test_plan_json_round_trip(tmp_path):
  raw = P.build_plan("lowspeed")
  path = tmp_path / "p.json"
  path.write_text(json.dumps(raw))
  assert P.load_plan(str(path)) == P.normalize_plan(raw)
