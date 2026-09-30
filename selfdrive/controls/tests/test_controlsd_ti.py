from types import SimpleNamespace

from cereal import car
from opendbc.car import apply_ti_steer_torque_limits, ti_driver_limiter_binds
from opendbc.car.honda.values import TI_LIMITS
from opendbc.safety import ALTERNATIVE_EXPERIENCE
from openpilot.selfdrive.controls.controlsd import Controls, TI_PANDA_LOG_INTERVAL, TI_SUSTAINED_LIMIT_FRAMES, \
  honda_panda_lateral_allowed


class FakeParams:
  def __init__(self, **values):
    self.values = {"TISigmoidEnabled": True, "TISigmoidLive": False, **values}

  def get_bool(self, key):
    return bool(self.values.get(key, False))

  def get_float(self, key):
    value = self.values.get(key, 0.0)
    if isinstance(value, Exception):
      raise value
    return value


class FakeLaC:
  def __init__(self):
    self.damping = None

  def update_honda_accord_low_speed_damping(self, *args):
    self.damping = args


def make_controls(**params):
  controls = Controls.__new__(Controls)
  controls.params = FakeParams(**params)
  controls.LaC = FakeLaC()
  controls.starpilot_toggles = SimpleNamespace(steerKp=[[0], [0.6]])
  controls._ti_kp = None
  controls._ti_sigmoid_hash = None
  controls._ti_error_logged_time = 0.0
  return controls


def test_ti_kp_replaces_steer_kp_every_frame():
  controls = make_controls(TISteerKp=0.45)
  assert controls._lateral_kp() == [[0], [0.6]]
  controls._update_ti_live_params()
  for _ in range(250):
    assert controls._lateral_kp() == [[0], [0.45]]


def test_ti_kp_default_matches_param_default():
  controls = make_controls()
  controls._update_ti_live_params()
  assert controls._lateral_kp() == [[0], [0.3]]


def test_ti_live_update_failure_is_logged_and_keeps_last_values(mocker):
  log = mocker.patch("openpilot.selfdrive.controls.controlsd.cloudlog")
  controls = make_controls(TISteerKp=0.45)
  controls._update_ti_live_params()
  controls.params.values["TISteerKp"] = RuntimeError("boom")
  controls._update_ti_live_params()
  controls._update_ti_live_params()
  assert controls._lateral_kp() == [[0], [0.45]]
  assert log.exception.call_count == 1


def make_limit_controls(ti_output=0.0, driver_torque=0.0):
  from collections import deque
  from openpilot.selfdrive.controls.controlsd import TI_OUTPUT_PIPELINE_FRAMES
  controls = make_controls()
  controls.steer_limited_by_safety = True  # stale value from an earlier frame
  controls.ti_driver_override = True
  controls._ti_limited_frames = 0
  controls._ti_torque_requests = deque([0.0] * TI_OUTPUT_PIPELINE_FRAMES, maxlen=TI_OUTPUT_PIPELINE_FRAMES)
  controls._ti_driver_bound = deque([False] * TI_OUTPUT_PIPELINE_FRAMES, maxlen=TI_OUTPUT_PIPELINE_FRAMES)
  controls.sm = {'carOutput': SimpleNamespace(actuatorsOutput=SimpleNamespace(torque=ti_output)),
                 'carState': SimpleNamespace(steeringTorque=driver_torque)}
  return controls


def lat_cc(torque, lat_active=True):
  return SimpleNamespace(latActive=lat_active, actuators=SimpleNamespace(torque=torque))


def set_ti_output(controls, torque):
  controls.sm['carOutput'].actuatorsOutput.torque = torque


def test_ti_steer_limited_is_evaluated_without_selfdrive_active():
  # Always-on lateral: selfdriveState is inactive, but the lateral loop runs and must
  # not inherit a stale "limited" value that freezes the integrator for the whole drive.
  controls = make_limit_controls()
  controls._update_ti_steer_limited(lat_cc(0.0))
  assert not controls.steer_limited_by_safety
  assert not controls.ti_driver_override


def test_ti_steer_limited_matches_output_to_recent_requests():
  controls = make_limit_controls()
  requests = [0.02, 0.04, 0.06, 0.08, 0.10]
  for n, req in enumerate(requests):
    # carOutput answers the request from two frames earlier (the TI kept up)
    set_ti_output(controls, requests[n - 2] if n >= 2 else 0.0)
    controls._update_ti_steer_limited(lat_cc(req))
    assert not controls.steer_limited_by_safety


def test_ti_steer_limited_clears_when_lateral_inactive():
  controls = make_limit_controls(ti_output=0.5)
  for _ in range(TI_SUSTAINED_LIMIT_FRAMES):
    controls._update_ti_steer_limited(lat_cc(0.0))
  assert controls.steer_limited_by_safety  # output 0.5 matches no recent request, for long enough
  controls._update_ti_steer_limited(lat_cc(0.0, lat_active=False))
  assert not controls.steer_limited_by_safety
  assert not controls.ti_driver_override
  assert controls._ti_limited_frames == 0
  assert list(controls._ti_torque_requests) == [0.0] * len(controls._ti_torque_requests)
  assert not any(controls._ti_driver_bound)


def run_ti_pipeline(frames, output_guard=False, near_lock=False):
  """frames: list of (request counts, TI driver torque). Runs the TI limiter as the carcontroller does
  (previous frame's request with this frame's carState) and controlsd on the result.
  Starts settled on the first request. Returns per-frame (sent, ti_driver_override, steer_limited_by_safety)."""
  controls = make_limit_controls()
  last_request = last_sent = 0 if near_lock else frames[0][0]
  controls._ti_torque_requests.extend([last_request / TI_LIMITS.TI_STEER_MAX] * len(controls._ti_torque_requests))
  out = []
  for request, driver_torque in frames:
    sent = apply_ti_steer_torque_limits(last_request, last_sent, driver_torque, TI_LIMITS,
                                        output_guard=output_guard, force_zero=near_lock)
    set_ti_output(controls, sent / TI_LIMITS.TI_STEER_MAX)
    controls.sm['carState'].steeringTorque = driver_torque
    controls._update_ti_steer_limited(lat_cc(request / TI_LIMITS.TI_STEER_MAX))
    out.append((sent, controls.ti_driver_override, controls.steer_limited_by_safety))
    last_request, last_sent = request, sent
  return out


def test_ti_rate_limit_with_light_same_side_hand_is_not_an_override():
  # 2026-09-30 turn exit (00000302 t=1416.8): the request drops faster than DELTA_DOWN for a few
  # frames while a light hand (+8) helps. The output lags, but it is not an override: no recapture
  # trigger and no integrator freeze.
  frames = [(400, 8)] * 30 + [(355, 8)] * 30 + [(400, 8)] * 30
  out = run_ti_pipeline(frames)
  assert any(sent not in (400, 355) for sent, _, _ in out[30:])  # the rate limit did bind
  assert not any(override for _, override, _ in out)
  assert not any(limited for _, _, limited in out)


def test_ti_output_guard_clamp_is_not_an_override():
  # aa7e4b70a headroom guard: a same-direction hand (+30) caps a 599 request at (40 - 30) * 12.
  # Not an override (no recapture), but a clamp that holds freezes the integrator after
  # TI_SUSTAINED_LIMIT_FRAMES so it cannot wind up behind it.
  frames = [(0, 0)] + [(599, 30)] * 80
  out = run_ti_pipeline(frames, output_guard=True)
  assert out[-1][0] == (TI_LIMITS.TI_OUTPUT_GUARD_POS - 30) * TI_LIMITS.TI_OUTPUT_TORQUE_DIV
  assert not any(override for _, override, _ in out)
  limited = [flag for _, _, flag in out]
  first = limited.index(True)
  assert first >= TI_SUSTAINED_LIMIT_FRAMES
  assert all(limited[first:])


def test_ti_near_lock_zero_freezes_integrator_once_sustained():
  frames = [(300, 0)] * 60
  out = run_ti_pipeline(frames, near_lock=True)
  assert all(sent == 0 for sent, _, _ in out)
  assert not any(override for _, override, _ in out)
  limited = [flag for _, _, flag in out]
  first = limited.index(True)
  # the first frames still match the settled 0 request; then the zeroed output is a limit that holds
  assert first <= TI_SUSTAINED_LIMIT_FRAMES + 3
  assert all(limited[first:])


def test_ti_opposing_hand_on_driver_limiter_is_an_override():
  # Driver holds against a +300 request (-20 counts): the driver allowance collapses to 0 and the
  # output ramps down. Recapture trigger and integrator freeze right away, and for as long as the hold lasts.
  frames = [(300, 0)] * 40 + [(300, -20)] * 40 + [(300, 0)] * 40
  out = run_ti_pipeline(frames)
  assert out[39][0] == 300
  assert not any(override or limited for _, override, limited in out[:40])
  hold = out[40:80]
  assert hold[-1][0] == 0
  assert all(override and limited for _, override, limited in hold[1:])
  # after release the output ramps back up (rate-limited, same request): no longer an override
  assert not any(override for _, override, _ in out[84:])


def test_ti_driver_limiter_flag_matches_limiter():
  for s in range(-60, 61, 3):
    for request in (-599, -300, -40, 0, 40, 300, 599):
      clipped = apply_ti_steer_torque_limits(request, request, s, TI_LIMITS) != request
      assert ti_driver_limiter_binds(request, s, TI_LIMITS) == clipped
      if clipped:
        assert s * request < 0 and abs(s) > TI_LIMITS.TI_STEER_DRIVER_ALLOWANCE


# --- Honda 9G TI: lateral only while the panda would pass 0x249 (drives 305/310/313) ---

AOL = ALTERNATIVE_EXPERIENCE.ALWAYS_ON_LATERAL
NIDEC = car.CarParams.SafetyModel.hondaNidec


def panda(controls_allowed=False, alt=AOL, model=NIDEC, tx_blocked=0):
  return SimpleNamespace(controlsAllowed=controls_allowed, alternativeExperience=alt, safetyModel=model,
                         safetyTxBlocked=tx_blocked)


def test_honda_panda_lateral_allowed_needs_cruise_main():
  # honda.h: !acc_main_on clears controls_allowed, and aol_allowed = acc_main_on && ALT_EXP bit
  for engaged in (False, True):
    for ps in ([panda()], [panda(controls_allowed=True)], []):
      assert not honda_panda_lateral_allowed(False, engaged, ps)


def test_honda_panda_lateral_allowed_with_cruise_main():
  assert honda_panda_lateral_allowed(True, False, [panda()])                           # AOL bit
  assert honda_panda_lateral_allowed(True, False, [panda(controls_allowed=True, alt=0)])
  assert not honda_panda_lateral_allowed(True, False, [panda(alt=0)])                  # no AOL, not engaged
  # engaged: a 10 Hz pandaStates that has not caught up yet must not drop lateral (controlsMismatch covers it)
  assert honda_panda_lateral_allowed(True, True, [panda(alt=0)])
  # no panda health yet, or only a silent/noOutput panda: nothing contradicts cruise main
  assert honda_panda_lateral_allowed(True, False, [])
  assert honda_panda_lateral_allowed(True, False, [panda(alt=0, model=car.CarParams.SafetyModel.noOutput)])


def make_gate_controls(panda_states):
  controls = make_controls()
  controls.sm = {'pandaStates': panda_states}
  controls._ti_panda_blocking = False
  controls._ti_panda_block_log_time = -TI_PANDA_LOG_INTERVAL
  controls._ti_tx_blocked_last = None
  controls._ti_tx_blocked_log_time = -TI_PANDA_LOG_INTERVAL
  return controls


def cs(available):
  return SimpleNamespace(cruiseState=SimpleNamespace(available=available))


def test_ti_panda_gate_holds_lateral_off_while_main_off_and_logs_once(mocker):
  log = mocker.patch("openpilot.selfdrive.controls.controlsd.cloudlog")
  controls = make_gate_controls([panda()])
  # AOL with ACC main on: untouched
  assert all(controls._ti_panda_lateral_gate(True, cs(True), False) for _ in range(50))
  # MAIN pressed off: held off every frame, one log line for the episode
  assert not any(controls._ti_panda_lateral_gate(True, cs(False), False) for _ in range(960))
  assert log.warning.call_count == 1
  # MAIN back on: lateral resumes on the same frame
  assert controls._ti_panda_lateral_gate(True, cs(True), False)
  # a second episode right after is not logged again (rate limit)
  assert not controls._ti_panda_lateral_gate(True, cs(False), False)
  assert log.warning.call_count == 1


def test_ti_panda_gate_never_turns_lateral_on():
  controls = make_gate_controls([panda(controls_allowed=True)])
  assert not controls._ti_panda_lateral_gate(False, cs(True), True)
  assert not controls._ti_panda_blocking


def test_ti_panda_tx_blocked_diagnostics(mocker):
  log = mocker.patch("openpilot.selfdrive.controls.controlsd.cloudlog")
  controls = make_gate_controls([panda(tx_blocked=40)])
  controls._log_ti_panda_tx_blocked(True)            # first sample only sets the baseline
  controls.sm['pandaStates'] = [panda(tx_blocked=61)]
  controls._log_ti_panda_tx_blocked(False)           # blocks while lateral is off are not reported
  assert log.warning.call_count == 0
  controls.sm['pandaStates'] = [panda(tx_blocked=70)]
  controls._log_ti_panda_tx_blocked(True)
  assert log.warning.call_count == 1 and "blocked 9 TX" in log.warning.call_args[0][0]
  controls.sm['pandaStates'] = [panda(tx_blocked=3)]  # panda reboot resets the counter
  controls._log_ti_panda_tx_blocked(True)
  assert log.warning.call_count == 1
