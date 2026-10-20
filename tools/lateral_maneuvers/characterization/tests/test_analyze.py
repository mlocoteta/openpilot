import json
import math

import numpy as np
import pytest

from openpilot.tools.lateral_maneuvers.characterization import analyze as A
from openpilot.tools.lateral_maneuvers.characterization import plan as P

DT = 0.01
T_DELAY = 0.25  # 0x249 -> lat accel pure delay in the holds
SINE_DELAY = 0.2
SINE_GAIN = 0.8
SEC = 1e9


def second_order(u, zeta, wn, dt=DT):
  y, dy, out = 0.0, 0.0, np.zeros_like(u)
  for i, x in enumerate(u):
    ddy = wn * wn * (x - y) - 2 * zeta * wn * dy
    dy += ddy * dt
    y += dy * dt
    out[i] = y
  return out


def shift(x, s):
  n = int(round(s / DT))
  return np.concatenate([np.full(n, x[0]), x[:len(x) - n]]) if n else x.copy()


class Synth:
  """Builds rlog-like series + a sidecar for a plan, with known plant dynamics per Kp."""
  def __init__(self, seed=0):
    self.rng = np.random.default_rng(seed)
    self.t = 1000.0
    self.cols = {k: ([], []) for k in ("cmd", "req", "des", "act", "v", "roll", "pitch", "fric", "lsf")}
    self.events = []

  def _emit(self, des, act, cmd, v, roll=0.004, pitch=-0.01):
    t = self.t + np.arange(len(des)) * DT
    for k, x in (("des", des), ("act", act), ("cmd", cmd), ("req", cmd + 5.0), ("v", np.full(len(t), v)),
                 ("roll", np.full(len(t), roll)), ("pitch", np.full(len(t), pitch)), ("fric", np.full(len(t), 0.3)),
                 ("lsf", np.full(len(t), A.low_speed_factor(v)))):
      self.cols[k][0].extend(t)
      self.cols[k][1].extend(x)
    self.t = t[-1] + DT

  def idle(self, seconds, v):
    n = int(seconds / DT)
    self._emit(np.zeros(n), np.zeros(n), np.zeros(n), v)

  def maneuver(self, block, spec, dyn, aborted=False):
    v = block["speed_mps"]
    self.idle(2.0, v)
    t_prof, prof = P.maneuver_profile(spec)  # plan DT (20 Hz) -> 100 Hz log grid
    prof = np.interp(np.arange(0.0, len(prof) * P.DT, DT), t_prof, prof)
    kind = spec["type"]
    if kind == "hold":
      noise = np.convolve(self.rng.normal(0, 1, len(prof) + 50), np.ones(20) / 20, "same")[:len(prof)]
      cmd = np.round(noise * 150)
      des = np.zeros(len(prof))
      act = shift(cmd, T_DELAY) / 300.0 + self.rng.normal(0, 0.005, len(prof))
    elif kind == "step":
      des = prof.copy()
      act = second_order(des, dyn["zeta"], dyn["wn"])
      cmd = np.round(des * 300)
    else:
      des = prof.copy()
      act = SINE_GAIN * shift(des, dyn.get("sine_delay", SINE_DELAY))
      cmd = np.round(des * 300)
    start = {"type": "maneuver_start", "mono_ns": int(self.t * SEC), "block": block["id"], "maneuver": spec["id"],
             "maneuver_desc": spec["desc"], "spec": spec, "meta": P.maneuver_meta(spec), "settings": block["settings"],
             "tag": block["tag"], "speed_mph": block["speed_mph"], "roll": 0.004, "pitch": -0.01,
             "active_settings": {"ti_steer_kp": block["settings"]["ti_steer_kp"]}}
    self.events.append(start)
    self._emit(des, act, cmd, v)
    end = "maneuver_aborted" if aborted else "maneuver_end"
    self.events.append({"type": end, "mono_ns": int((self.t - DT) * SEC), "block": block["id"], "maneuver": spec["id"],
                        "reason": "steering touched" if aborted else None})

  def series(self):
    return {k: (np.asarray(t), np.asarray(v, float)) for k, (t, v) in self.cols.items()}


DYN = {0.5: {"zeta": 0.5, "wn": 2 * math.pi * 1.0}, 0.8: {"zeta": 0.8, "wn": 2 * math.pi * 1.5, "sine_delay": 0.1}}


@pytest.fixture(scope="module")
def run():
  plan = P.normalize_plan({"version": 1, "name": "synthetic", "blocks": [
    {"id": f"k{kp}", "speed_mph": 15, "settings": {"steer_delay": 0.01, "friction_table": "flat", "ti_steer_kp": kp},
     "maneuvers": [{"type": "hold", "duration_s": 10.0}, {"type": "step", "amplitude": 0.3, "hold_s": 3.0},
                   {"type": "sine", "freq_hz": 0.4, "amplitude": 0.3, "cycles": 3}]}
    for kp in (0.5, 0.8)]})
  s = Synth()
  for block in plan["blocks"]:
    kp = block["settings"]["ti_steer_kp"]
    s.maneuver(block, block["maneuvers"][1], DYN[kp], aborted=True)  # repeated attempt below; must be ignored
    for spec in block["maneuvers"]:
      s.maneuver(block, spec, DYN[kp])
  s.idle(2.0, plan["blocks"][-1]["speed_mps"])
  sidecar = {"route": "0000abcd--synthetic", "plan": plan, "gitCommit": "x", "gitBranch": "y",
             "events": s.events + [{"type": "run_end", "mono_ns": int(s.t * SEC), "reason": "completed", "restored": {}}]}
  return A.analyze_run(s.series(), sidecar), plan


def _by(report, block, kind):
  return [r for r in report["maneuvers"] if r["block"] == block and r["type"] == kind]


def test_decode_ti():
  assert A.decode_ti(bytes([0x08, 0x00])) == 0
  assert A.decode_ti(bytes([0x0A, 0x57])) == 599
  assert A.decode_ti(bytes([0xF5, 0xA9])) == -599  # upper nibble (counter/state) ignored


def test_xcorr_recovers_known_delay_and_sign():
  rng = np.random.default_rng(1)
  x = np.convolve(rng.normal(0, 1, 800), np.ones(15) / 15, "same")
  lags, corr = A.xcorr_curve(x, -2.0 * shift(x, 0.33))
  d, c = A.delay_from_curve(lags, corr)
  assert d == pytest.approx(0.33, abs=0.015) and c < -0.9
  assert A.delay_from_curve(lags, corr, sign=+1)[0] is None


def test_completed_attempts_only(run):
  report, _ = run
  assert len(report["maneuvers"]) == 6
  assert sum(e["type"] == "maneuver_aborted" for e in report["incidents"]) == 2


def test_hold_delay_ping_pong_and_noise(run):
  report, _ = run
  assert report["cmd_accel_sign"] == 1
  for kp in (0.5, 0.8):
    h = _by(report, f"k{kp}", "hold")[0]
    assert h["cmd_delay_s"] == pytest.approx(T_DELAY, abs=0.02)
    assert h["cmd_flips_per_s"] > 0.5 and h["err_flips_per_s"] > 0.5
    assert h["amplified_noise_sigma"] == pytest.approx(h["noise_sigma"] * (1 + h["lsf"] / kp))
    assert h["lsf"] == pytest.approx(A.low_speed_factor(15 * P.MPH_TO_MS), rel=1e-3)
    assert h["friction_threshold"] == pytest.approx(0.3)
    assert h["req_gap_mean_abs"] == pytest.approx(5.0, abs=0.01)
    assert h["pitch_mean"] == pytest.approx(-0.01) and h["road_start"]["roll"] == 0.004


def test_step_overshoot_matches_second_order(run):
  report, _ = run
  expected = 100 * math.exp(-math.pi * 0.5 / math.sqrt(1 - 0.5 ** 2))  # 16.3 %
  step = _by(report, "k0.5", "step")[0]
  assert len(step["steps"]) == 4
  first = step["steps"][0]
  assert first["overshoot_pct"] == pytest.approx(expected, abs=2.0)
  assert first["rise_s"] == pytest.approx(0.26, abs=0.05)  # 10-90 % rise of zeta 0.5, wn 1 Hz
  assert first["settling_s"] is not None and first["settling_s"] < 1.5
  assert _by(report, "k0.8", "step")[0]["overshoot_pct"] < 3.0


def test_sine_gain_and_phase(run):
  report, _ = run
  s = _by(report, "k0.5", "sine")[0]
  assert s["gain"] == pytest.approx(SINE_GAIN, abs=0.02)
  assert s["phase_deg"] == pytest.approx(-360 * 0.4 * SINE_DELAY, abs=2.0)
  assert s["phase_delay_s"] == pytest.approx(SINE_DELAY, abs=0.015)


def test_recommendation_and_outputs(run, tmp_path):
  report, _ = run
  rec = report["recommendation"]
  assert rec["ti_steer_kp"]["value"] == 0.8
  assert rec["steer_delay"]["measured_cmd_to_accel_delay_s"] is not None
  table = rec["friction_table"]["value"]
  assert len(table) == len(P.FRICTION_SPEED_KNOTS) and all(0.3 <= x <= 2.0 for x in table)
  path = A.write_report(report, str(tmp_path))
  with open(path) as f:
    md = f.read()
  assert "TISteerKp:** 0.8" in md and "| k0.5 | 15 |" in md
  with open(tmp_path / "report.json") as f:
    doc = json.load(f)
  assert doc["recommendation"]["ti_steer_kp"]["value"] == 0.8


def test_extract_series_from_cereal():
  from cereal import messaging
  msgs = []
  sc = messaging.new_message("sendcan", 2)
  sc.logMonoTime = int(5 * SEC)
  sc.sendcan[0].address, sc.sendcan[0].src, sc.sendcan[0].dat = 0x249, 0, bytes([0x08, 0x64, 0, 0])
  sc.sendcan[1].address, sc.sendcan[1].src, sc.sendcan[1].dat = 0xE4, 0, bytes(5)
  msgs.append(sc)
  cc = messaging.new_message("carControl")
  cc.logMonoTime = int(5 * SEC)
  cc.carControl.actuators.torque = 0.5
  cc.carControl.orientationNED = [0.02, -0.03, 0.0]
  msgs.append(cc)
  cs = messaging.new_message("controlsState")
  cs.logMonoTime = int(5.01 * SEC)
  ts = cs.controlsState.lateralControlState.init("torqueState")
  ts.desiredLateralAccel, ts.actualLateralAccel = 0.4, 0.3
  msgs.append(cs)
  sp = messaging.new_message("starpilotLateralState")
  sp.starpilotLateralState.active = True
  sp.starpilotLateralState.frictionThreshold = 1.2
  msgs.append(sp)
  s = A.extract_series([messaging.log_from_bytes(m.to_bytes()) for m in msgs])
  assert list(s["cmd"][1]) == [100]
  assert s["req"][1][0] == pytest.approx(299.5)
  assert s["roll"][1][0] == pytest.approx(0.02) and s["pitch"][1][0] == pytest.approx(-0.03)
  assert (s["des"][1][0], s["act"][1][0]) == (pytest.approx(0.4), pytest.approx(0.3))
  assert s["fric"][1][0] == pytest.approx(1.2)


def _synth_run(plan, blocks, route, started, dyn=None, partial=None, seed=0):
  """One drive: completes `blocks`; `partial` block only gets its first maneuver."""
  s = Synth(seed)
  for block in plan["blocks"]:
    if block["id"] in blocks or block["id"] == partial:
      kp = block["settings"]["ti_steer_kp"]
      specs = block["maneuvers"][:1] if block["id"] == partial else block["maneuvers"]
      for spec in specs:
        s.maneuver(block, spec, (dyn or DYN)[kp])
  s.idle(2.0, 6.7)
  return s.series(), {"route": route, "plan": plan, "startedWall": started, "gitCommit": "x", "gitBranch": "y",
                      "events": s.events + [{"type": "run_end", "mono_ns": int(s.t * SEC), "reason": "process_exit"}]}


def test_multi_route_merge_newest_completed_wins(run):
  _, plan = run
  slow = {0.5: DYN[0.5], 0.8: {"zeta": 0.8, "wn": 2 * math.pi * 1.5, "sine_delay": 0.4}}
  older = _synth_run(plan, {"k0.5", "k0.8"}, "00000001--a", 100.0)
  newer = _synth_run(plan, {"k0.8"}, "00000002--b", 200.0, dyn=slow, seed=1)
  newest_partial = _synth_run(plan, set(), "00000003--c", 300.0, partial="k0.5", seed=2)
  report = A.analyze_runs([newer, newest_partial, older])  # input order does not matter
  assert report["block_sources"] == {"k0.5": "00000001--a", "k0.8": "00000002--b"}
  assert report["routes"] == ["00000001--a", "00000002--b", "00000003--c"]
  assert len(report["maneuvers"]) == 6
  sine08 = _by(report, "k0.8", "sine")[0]
  assert sine08["route"] == "00000002--b" and sine08["phase_delay_s"] == pytest.approx(0.4, abs=0.05)
  assert {r["route"] for r in _by(report, "k0.5", "hold")} == {"00000001--a"}
  assert "Runs merged" in A.render_markdown(report)


def test_multi_route_newest_partial_used_when_never_completed(run):
  _, plan = run
  a = _synth_run(plan, {"k0.8"}, "00000001--a", 100.0)
  b = _synth_run(plan, set(), "00000002--b", 200.0, partial="k0.5")
  report = A.analyze_runs([a, b])
  assert report["block_sources"] == {"k0.5": "00000002--b", "k0.8": "00000001--a"}
  assert len(_by(report, "k0.5", "hold")) == 1


def test_multi_route_ignores_same_id_with_different_content(run):
  _, plan = run
  other = P.normalize_plan({"version": 1, "name": "other", "blocks": [
    {"id": "k0.5", "speed_mph": 20, "settings": {"ti_steer_kp": 0.5}, "maneuvers": "quick"}]})
  a = _synth_run(other, {"k0.5"}, "00000001--a", 100.0)
  b = _synth_run(plan, {"k0.8"}, "00000002--b", 200.0)
  report = A.analyze_runs([a, b])
  assert report["routes"] == ["00000002--b"]
  assert [(i["route"], i["block"]) for i in report["ignored_blocks"]] == [("00000001--a", "k0.5")]
  assert set(report["block_sources"]) == {"k0.8"}


def test_multi_route_merges_identical_blocks_across_plan_files(run):
  # e.g. a reduced plan driven first, then the full plan: identical blocks (same id + content) merge
  _, plan = run
  reduced = P.normalize_plan({"version": 1, "name": "reduced", "blocks": [
    {"id": "k0.5", "speed_mph": 15, "settings": {"steer_delay": 0.01, "friction_table": "flat", "ti_steer_kp": 0.5},
     "maneuvers": [{"type": "hold", "duration_s": 10.0}, {"type": "step", "amplitude": 0.3, "hold_s": 3.0},
                   {"type": "sine", "freq_hz": 0.4, "amplitude": 0.3, "cycles": 3}]}]})
  a = _synth_run(reduced, {"k0.5"}, "00000001--a", 100.0)
  b = _synth_run(plan, {"k0.8"}, "00000002--b", 200.0)
  report = A.analyze_runs([a, b])
  assert report["block_sources"] == {"k0.5": "00000001--a", "k0.8": "00000002--b"}
  assert report["ignored_blocks"] == [] and report["plan"] == "synthetic"


def test_cli_accepts_multiple_sidecars_one_rlog_dir(run, tmp_path, monkeypatch, capsys):
  _, plan = run
  a = _synth_run(plan, {"k0.5"}, "00000001--a", 100.0)
  b = _synth_run(plan, {"k0.8"}, "00000002--b", 200.0)
  series = {"00000001--a": a[0], "00000002--b": b[0]}
  loaded = []

  def fake_load(directory, route=None):
    loaded.append((directory, route))
    return series[route]
  monkeypatch.setattr(A, "load_rlogs", fake_load)
  paths = []
  for _, sc in (a, b):
    p = tmp_path / f"{sc['route']}.json"
    p.write_text(json.dumps(sc, default=lambda o: o.tolist()))
    paths += ["--sidecar", str(p)]
  A.main(paths + ["--rlogs", str(tmp_path / "rlogs"), "--out", str(tmp_path / "out")])
  assert loaded == [(str(tmp_path / "rlogs"), "00000001--a"), (str(tmp_path / "rlogs"), "00000002--b")]
  report = json.loads((tmp_path / "out" / "report.json").read_text())
  assert report["block_sources"] == {"k0.5": "00000001--a", "k0.8": "00000002--b"}
  assert "00000001--a, 00000002--b" in capsys.readouterr().out
