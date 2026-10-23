"""Honda 9G Accord Torque Interceptor lateral controller (F03), ported from the 6.x
test_latcontrol.py (TI parts) and test_controlsd_ti.py (F03 parts)."""
import math

import pytest

from openpilot.cereal import log
from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.torque_interceptor import TI_LIMITS, apply_ti_steer_torque_limits, apply_torque_interceptor
from opendbc.car.honda.values import CAR
from opendbc.car.structs import car
from opendbc.car.vehicle_model import VehicleModel
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.controls.lib import latcontrol_torque_ti as ti
from openpilot.selfdrive.controls.lib.latcontrol_torque import LatControlTorque
from openpilot.selfdrive.controls.lib.latcontrol_torque_ti import (
  TI_LIVE_PARAMS_INTERVAL, TI_OUTPUT_PIPELINE_FRAMES, TI_SIGMOID_DEFAULT, TI_SUSTAINED_LIMIT_FRAMES, LatControlTorqueTI,
  build_sigmoid_tables, get_honda_accord_continuous_center_damped_output, get_honda_accord_low_speed_damped_output,
  get_ti_9g_low_speed_gain_scale, ti_driver_limiter_binds, ti_driver_torque_limits, ti_lateral_qualified,
)
from openpilot.selfdrive.controls.lib.lateral_controller_factory import create_lateral_controller


class FakeParams:
  def __init__(self, **values):
    self.values = {"TISigmoidEnabled": True, "TISigmoidLive": False, **values}

  def get_value(self, key):
    value = self.values.get(key)
    if isinstance(value, Exception):
      raise value
    return value


def ti_cp(identity=CAR.HONDA_ACCORD_9G, *, ti_on=True, pedal=True):
  fp = gen_empty_fingerprint()
  if pedal:
    fp[0][0x201] = 6
  cp = CarInterface.get_params(identity, fp, [], False, False, False)
  apply_torque_interceptor(cp, ti_on)
  return cp


def build(params=None, **values):
  cp = ti_cp()
  ci = CarInterface(cp)
  controller = LatControlTorqueTI(cp.as_reader(), ci, DT_CTRL, params=params or FakeParams(**values))
  VM = VehicleModel(cp)
  CS = car.CarState.new_message()
  CS.vEgo = 20.0
  lp = log.VehicleParameters.new_message()
  lp.steerRatio = cp.steerRatio
  lp.stiffnessFactor = 1.0
  return controller, VM, CS, lp


# ---- selection and learning exclusion ----

class TestSelection:
  def test_factory_picks_ti_controller_only_on_the_ti_car(self):
    cp = ti_cp()
    assert ti_lateral_qualified(cp)
    controller = create_lateral_controller(cp.as_reader(), CarInterface(cp), DT_CTRL, mode='stock')
    assert isinstance(controller, LatControlTorqueTI)

  def test_plain_9g_keeps_the_stock_controller(self):
    cp = ti_cp(ti_on=False)
    assert not ti_lateral_qualified(cp)
    try:
      controller = create_lateral_controller(cp.as_reader(), CarInterface(cp), DT_CTRL, mode='stock')
    except ValueError:
      return  # 7.0 refuses a mode it has no policy for; either way it is not the TI controller
    assert not isinstance(controller, LatControlTorqueTI)

  def test_other_hondas_never_qualify(self):
    for identity in (CAR.HONDA_ACCORD, CAR.HONDA_CIVIC):
      assert not ti_lateral_qualified(ti_cp(identity, ti_on=True, pedal=False))

  def test_flm_and_torqued_are_excluded(self):
    # Not a LatControlTorque: 7.0's FLM Auto Learn stages, native refinement, gain owner and
    # torqued live parameters are all gated on isinstance(LaC, LatControlTorque) or on the
    # update_torque_parameters API, which this controller deliberately does not have.
    controller, *_ = build()
    assert not isinstance(controller, LatControlTorque)
    for name in ('update_torque_parameters', 'starpilot_extension', 'flm_source', 'flm_surface', 'native_learning_baseline'):
      assert not hasattr(controller, name)

  def test_controlsd_skips_learning_hosts_on_the_ti_car(self):
    import inspect
    from openpilot.selfdrive.controls import controlsd
    src = inspect.getsource(controlsd.Controls.__init__)
    assert "self.ti_lateral = ti_lateral_qualified(self.CP)" in src
    assert "if not getattr(self, 'ti_lateral', False) and torque_runtime_enabled(self.CP, self.params) else None" in src
    assert "self.global_learning = None if getattr(self, 'ti_lateral', False) else GlobalRuntime(" in src
    assert "self.LaC.controls_steer_limited(CC, CS, self.sm['carOutput'])" in inspect.getsource(controlsd.Controls.publish)


# ---- torque curve, Kp, live params ----

class TestLiveParams:
  def test_startup_sigmoid_defaults_when_unset(self):
    controller, *_ = build()
    assert controller.sigmoid_params == TI_SIGMOID_DEFAULT
    torque, lataccel = build_sigmoid_tables(*TI_SIGMOID_DEFAULT)
    assert controller.torque_from_lateral_accel(1.0, controller.torque_params) == pytest.approx(
      float(__import__('numpy').interp(1.0, lataccel, torque)))

  def test_startup_uses_the_params(self):
    controller, *_ = build(TISigmoidA=2.42, TISigmoidB=1.12, TISigmoidC=0.1)
    assert controller.sigmoid_params == (2.42, 1.12, 0.1)
    # the PID limits follow the curve's +-1 torque points
    assert controller.pid.pos_limit == pytest.approx(controller.lateral_accel_from_torque(1.0, controller.torque_params))

  def test_sigmoid_off_is_linear(self):
    controller, *_ = build(TISigmoidEnabled=False)
    assert controller.sigmoid_params is None
    lf = controller.torque_params.latAccelFactor
    assert controller.torque_from_lateral_accel(1.0, controller.torque_params) == pytest.approx(1.0 / lf)

  def test_live_sigmoid_update_and_disable(self):
    params = FakeParams(TISigmoidLive=True, TISigmoidA=2.42, TISigmoidB=1.12, TISigmoidC=0.1)
    controller, VM, CS, lp = build(params)
    params.values.update(TISigmoidA=3.0)
    for _ in range(TI_LIVE_PARAMS_INTERVAL - 1):
      controller.update(False, CS, VM, lp, False, 0.0, False, 0.4)
    assert controller.sigmoid_params == (2.42, 1.12, 0.1)
    controller.update(False, CS, VM, lp, False, 0.0, False, 0.4)
    assert controller.sigmoid_params == (3.0, 1.12, 0.1)
    params.values["TISigmoidEnabled"] = False
    controller.refresh_live_params()
    assert controller.sigmoid_params is None

  def test_live_sigmoid_ignored_without_live_flag(self):
    params = FakeParams(TISigmoidA=2.42, TISigmoidB=1.12, TISigmoidC=0.1)
    controller, *_ = build(params)
    params.values.update(TISigmoidA=3.0)
    controller.refresh_live_params()
    assert controller.sigmoid_params == (2.42, 1.12, 0.1)

  def test_ti_kp_replaces_the_gain_table_every_frame(self):
    controller, VM, CS, lp = build(TISteerKp=0.45)
    for _ in range(250):
      controller.update(True, CS, VM, lp, False, 0.001, False, 0.4)
      assert controller.pid._k_p == [[0], [0.45]]

  def test_ti_kp_default_matches_param_default(self):
    controller, VM, CS, lp = build()
    controller.update(True, CS, VM, lp, False, 0.0, False, 0.4)
    assert controller.pid._k_p == [[0], [0.3]]

  def test_live_update_failure_is_logged_and_keeps_last_values(self, mocker):
    log_mock = mocker.patch.object(ti, "cloudlog")
    params = FakeParams(TISteerKp=0.45)
    controller, *_ = build(params)
    params.values["TISteerKp"] = RuntimeError("boom")
    controller.refresh_live_params()
    controller.refresh_live_params()
    assert controller.lateral_kp() == [[0], [0.45]]
    assert log_mock.exception.call_count == 1

  def test_damping_toggles_apply(self):
    controller, *_ = build(TILowSpeedDampingEnabled=True)
    assert controller.honda_accord_low_speed_damping_enabled
    assert controller.honda_accord_low_speed_damping_max == pytest.approx(0.12)
    controller.update_low_speed_damping(False, 0.12, continuous_center_enabled=True)
    assert controller.honda_accord_continuous_center_damping_enabled
    # the two policies never stack
    controller.update_low_speed_damping(True, 0.12, continuous_center_enabled=True)
    assert not controller.honda_accord_low_speed_damping_enabled
    controller.update_low_speed_damping(False, 0.12)
    assert not controller.honda_accord_low_speed_damping_enabled
    assert not controller.honda_accord_continuous_center_damping_enabled

  def test_damping_defaults_off(self):
    controller, *_ = build()
    assert not controller.honda_accord_low_speed_damping_enabled
    assert not controller.honda_accord_continuous_center_damping_enabled
    assert controller.honda_accord_continuous_center_damping_max_reduction == pytest.approx(0.62)

  def test_user_friction_override(self):
    controller, *_ = build(SteerFriction=0.19, SteerFrictionStock=0.31)
    assert controller.torque_params.friction == pytest.approx(0.19)
    stock, *_ = build(SteerFriction=0.31, SteerFrictionStock=0.31)
    assert stock.torque_params.friction == pytest.approx(ti_cp().lateralTuning.torque.friction)
    unset, *_ = build()
    assert unset.torque_params.friction == pytest.approx(ti_cp().lateralTuning.torque.friction)


# ---- low-speed gain schedule ----

def test_ti_9g_low_speed_gain_schedule_curve():
  assert get_ti_9g_low_speed_gain_scale(0.0) == pytest.approx(0.5)
  assert get_ti_9g_low_speed_gain_scale(7.0) == pytest.approx(0.5)
  assert get_ti_9g_low_speed_gain_scale(8.5) == pytest.approx(0.75)
  assert get_ti_9g_low_speed_gain_scale(10.0) == pytest.approx(1.0)
  assert get_ti_9g_low_speed_gain_scale(30.0) == pytest.approx(1.0)
  scales = [get_ti_9g_low_speed_gain_scale(0.5 * i) for i in range(60)]
  assert all(b >= a for a, b in zip(scales, scales[1:], strict=False))


@pytest.mark.parametrize("v_ego,expected_scale", [(4.5, 0.5), (8.5, 0.75), (12.0, 1.0), (25.0, 1.0)])
def test_ti_9g_low_speed_gain_schedule_scales_feedback_only(v_ego, expected_scale):
  outputs = {}
  for enabled in (False, True):
    controller, VM, CS, lp = build()
    controller.ti_low_speed_gain_schedule_enabled = enabled
    CS.vEgo = v_ego
    CS.steeringAngleDeg = -3.0
    for _ in range(5):
      torque, _, lac_log = controller.update(True, CS, VM, lp, False, 0.004, False, 0.4)
    outputs[enabled] = (torque, lac_log.error, lac_log.p, lac_log.f, controller.low_speed_factor, controller.friction_scale,
                        controller.feedforward)
  off, on = outputs[False], outputs[True]
  assert on[4] == pytest.approx(off[4] * expected_scale)
  assert on[5] == pytest.approx(off[5] * expected_scale)
  if expected_scale == 1.0:
    assert on == pytest.approx(off)
  else:
    assert abs(on[1]) < abs(off[1])
    assert abs(on[2]) < abs(off[2])
    assert on[0] * off[0] > 0.0
    assert abs(on[0]) < abs(off[0])


# ---- soft recapture and integrator freeze ----

# 6.x used 0.012 with its stock Kp table; with TISteerKp 0.3 and the sigmoid default that saturates at
# 1.0, which hides the recapture ramp, so the curve here is gentler.
RECAPTURE_CURVATURE = 0.004


def recapture_run(enabled, schedule):
  """schedule: (frames, steeringPressed, steeringTorque, limited); limited is a bool or (override, steer_limited)."""
  controller, VM, CS, lp = build()
  controller.ti_recapture_enabled = enabled
  CS.vEgo = 14.0
  CS.steeringAngleDeg = -2.0  # wide of a left curve: large positive error
  out = []
  for frames, pressed, drv, limited in schedule:
    override, steer_limited = limited if isinstance(limited, tuple) else (limited, limited)
    for _ in range(frames):
      CS.steeringPressed = pressed
      CS.steeringTorque = drv
      controller.set_ti_driver_override(override)
      torque, _, lac_log = controller.update(True, CS, VM, lp, steer_limited, RECAPTURE_CURVATURE, False, 0.4)
      out.append((torque, lac_log.p, lac_log.f, lac_log.i, controller.ti_recapture_gain, controller.feedforward))
  return out


def test_ti_9g_recapture_holds_feedback_during_override_and_ramps_after():
  schedule = [(50, False, 0, False), (50, False, 10, True), (100, False, 0, False)]
  off = recapture_run(False, schedule)
  on = recapture_run(True, schedule)
  assert on[:50] == pytest.approx(off[:50])
  assert all(abs(x[1]) < 1e-9 for x in on[60:100])
  assert abs(off[99][1]) > 0.1
  assert on[99][5] == pytest.approx(RECAPTURE_CURVATURE * 14.0 ** 2, abs=0.05)
  assert off[99][5] > on[99][5]
  gains = [x[4] for x in on]
  assert gains[100 + 15] == 0.0
  assert 0.0 < gains[100 + 20 + 30] < 1.0
  assert gains[100 + 20 + 61] == pytest.approx(1.0)
  assert all(b >= a for a, b in zip(gains[100:], gains[101:], strict=False))
  # the recaptured command approaches the baseline gradually instead of stepping
  steps_on = max(abs(on[k + 1][0] - on[k][0]) for k in range(100, 199))
  assert steps_on < 0.1 * abs(on[199][0] - on[100][0])
  assert on[199][0] == pytest.approx(off[199][0], abs=0.05)


def test_ti_9g_recapture_pressed_zeroes_feedback_immediately():
  on = recapture_run(True, [(20, False, 0, False), (1, True, 20, False), (1, False, 0, False)])
  assert on[20][4] == 0.0 and abs(on[20][1]) < 1e-9


def test_ti_9g_recapture_ignores_hands_resting_without_limit():
  off = recapture_run(False, [(80, False, 8, False)])
  on = recapture_run(True, [(80, False, 8, False)])
  assert on == pytest.approx(off)
  on2 = recapture_run(True, [(80, False, 2, True)])
  assert all(x[4] == 1.0 for x in on2)


def test_ti_9g_recapture_ignores_rate_and_guard_limits():
  for steer_limited in (False, True):
    on = recapture_run(True, [(20, False, 0, False), (60, False, 10, (False, steer_limited))])
    assert all(x[4] == 1.0 for x in on)
    assert abs(on[-1][1]) > 0.1


def test_ti_9g_integrator_freezes_on_override_only():
  def run(drv, override, steer_limited):
    controller, VM, CS, lp = build()
    CS.vEgo = 14.0
    CS.steeringAngleDeg = 0.0
    out = []
    for k in range(100):
      CS.steeringTorque = drv if k >= 50 else 0
      controller.set_ti_driver_override(override and k >= 50)
      _, _, lac_log = controller.update(True, CS, VM, lp, steer_limited and k >= 50, 0.001, False, 0.4)
      out.append((lac_log.i, controller.ti_recapture_gain))
    return out

  free = run(10, False, False)
  held = run(-20, True, True)
  i_at_hold = held[49][0]
  assert free[49][0] == pytest.approx(i_at_hold)
  assert abs(free[-1][0] - i_at_hold) > 1e-3
  assert all(x[0] == pytest.approx(i_at_hold) for x in held[50:])
  assert all(x[1] == 1.0 for x in free) and all(x[1] == 0.0 for x in held[50:])


def test_inactive_resets_and_outputs_zero():
  controller, VM, CS, lp = build()
  for _ in range(20):
    controller.update(True, CS, VM, lp, False, 0.003, False, 0.4)
  torque, _, lac_log = controller.update(False, CS, VM, lp, False, 0.003, False, 0.4)
  assert torque == 0.0 and not lac_log.active and controller.pid.i == 0.0
  assert all(math.isfinite(x) for x in (controller.prev_output_torque, controller.prev_desired_lateral_accel))


# ---- low-speed damping functions ----

def test_honda_accord_low_speed_damping_is_bounded_and_local():
  damped, scale, envelope = get_honda_accord_low_speed_damped_output(1.0, -1.0, 0.35, 4.0, 0.12)
  highway, highway_scale, highway_envelope = get_honda_accord_low_speed_damped_output(1.0, -1.0, 0.35, 12.0, 0.12)
  strong_turn, strong_turn_scale, strong_turn_envelope = get_honda_accord_low_speed_damped_output(1.0, -1.0, 2.0, 4.0, 0.12)
  assert 0.88 <= scale < 1.0
  assert 0.0 < envelope <= 1.0
  assert damped < 1.0
  assert highway == pytest.approx(1.0, abs=0.005)
  assert highway_scale == pytest.approx(1.0, abs=0.001)
  assert highway_envelope == pytest.approx(0.0, abs=0.005)
  assert strong_turn_scale > scale
  assert strong_turn_envelope < envelope
  assert strong_turn > damped


def test_honda_accord_low_speed_damping_requires_reversal_activation():
  untouched, scale, envelope = get_honda_accord_low_speed_damped_output(1.0, -1.0, 0.35, 4.0, 0.12, activation=0.0)
  active, active_scale, active_envelope = get_honda_accord_low_speed_damped_output(1.0, -1.0, 0.35, 4.0, 0.12, activation=1.0)
  assert untouched == pytest.approx(1.0)
  assert scale == pytest.approx(1.0)
  assert envelope == pytest.approx(0.0)
  assert active < untouched
  assert active_scale < 1.0
  assert active_envelope > 0.0


def test_honda_accord_low_speed_damping_has_gentle_crawl_tail():
  _, scale, envelope = get_honda_accord_low_speed_damped_output(1.0, -1.0, 0.35, 1.0 * 0.44704, 0.12, activation=1.0)
  assert 0.0 < envelope < 0.10
  assert 0.98 < scale < 1.0


def test_honda_accord_continuous_center_damping_matches_reference_envelope():
  damped, scale, envelope = get_honda_accord_continuous_center_damped_output(1.0, -1.0, 0.05, 4.0)
  outside, outside_scale, outside_envelope = get_honda_accord_continuous_center_damped_output(1.0, -1.0, 0.8, 4.0)
  highway, highway_scale, highway_envelope = get_honda_accord_continuous_center_damped_output(1.0, -1.0, 0.05, 12.0)
  lighter_cap, _, _ = get_honda_accord_continuous_center_damped_output(1.0, -1.0, 0.05, 4.0, max_reduction=0.20)
  assert 0.62 <= scale < 1.0
  assert 0.0 < envelope <= 1.0
  assert damped < 1.0
  assert outside > damped
  assert outside_scale > scale
  assert outside_envelope < envelope
  assert highway == pytest.approx(1.0, abs=0.005)
  assert highway_scale == pytest.approx(1.0, abs=0.001)
  assert highway_envelope == pytest.approx(0.0, abs=0.005)
  assert lighter_cap > damped


def test_low_speed_damping_runs_in_the_controller():
  # A wheel ping-ponging +-40 deg every 5 frames in a gentle low-speed left turn: the reversal-gated
  # policy engages and the command varies less; off, the two runs are identical.
  def total_variation(seq):
    return sum(abs(b - a) for a, b in zip(seq, seq[1:], strict=False))
  outs = {}
  for enabled in (False, True):
    controller, VM, CS, lp = build(TILowSpeedDampingEnabled=enabled)
    CS.vEgo = 4.0
    seq = []
    for k in range(200):
      CS.steeringAngleDeg = 40.0 if (k // 5) % 2 else -40.0
      torque, _, _ = controller.update(True, CS, VM, lp, False, 0.01, False, 0.4)
      seq.append(torque)
    outs[enabled] = seq
  assert max(abs(a - b) for a, b in zip(outs[True], outs[False], strict=True)) > 0.05
  assert total_variation(outs[True]) < total_variation(outs[False])


# ---- steer_limited_by_safety and driver override (6.x controlsd _update_ti_steer_limited) ----

def limiter():
  controller, *_ = build()
  controller.steer_limited_by_safety = True  # stale value from an earlier frame
  controller.ti_driver_override = True
  return controller


def test_steer_limited_is_evaluated_without_selfdrive_active():
  controller = limiter()
  controller.update_steer_limited(True, 0.0, 0.0, 0.0)
  assert not controller.steer_limited_by_safety
  assert not controller.ti_driver_override


def test_steer_limited_matches_output_to_recent_requests():
  controller = limiter()
  requests = [0.02, 0.04, 0.06, 0.08, 0.10]
  for n, req in enumerate(requests):
    assert not controller.update_steer_limited(True, req, requests[n - 2] if n >= 2 else 0.0, 0.0)


def test_steer_limited_clears_when_lateral_inactive():
  controller = limiter()
  for _ in range(TI_SUSTAINED_LIMIT_FRAMES):
    controller.update_steer_limited(True, 0.0, 0.5, 0.0)
  assert controller.steer_limited_by_safety
  controller.update_steer_limited(False, 0.0, 0.5, 0.0)
  assert not controller.steer_limited_by_safety
  assert not controller.ti_driver_override
  assert controller._ti_limited_frames == 0
  assert list(controller._ti_torque_requests) == [0.0] * TI_OUTPUT_PIPELINE_FRAMES
  assert not any(controller._ti_driver_bound)


def run_ti_pipeline(frames):
  """frames: (request counts, TI driver torque). Runs the phase-1 TI limiter as the carcontroller does
  (previous frame's request with this frame's carState) and the steer-limited logic on the result."""
  controller = limiter()
  last_request = last_sent = frames[0][0]
  controller._ti_torque_requests.extend([last_request / TI_LIMITS.TI_STEER_MAX] * TI_OUTPUT_PIPELINE_FRAMES)
  out = []
  for request, driver_torque in frames:
    sent = apply_ti_steer_torque_limits(last_request, last_sent, driver_torque, TI_LIMITS)
    controller.update_steer_limited(True, request / TI_LIMITS.TI_STEER_MAX, sent / TI_LIMITS.TI_STEER_MAX, driver_torque)
    out.append((sent, controller.ti_driver_override, controller.steer_limited_by_safety))
    last_request, last_sent = request, sent
  return out


def test_rate_limit_with_light_same_side_hand_is_not_an_override():
  frames = [(400, 8)] * 30 + [(355, 8)] * 30 + [(400, 8)] * 30
  out = run_ti_pipeline(frames)
  assert any(sent not in (400, 355) for sent, _, _ in out[30:])
  assert not any(override for _, override, _ in out)
  assert not any(limited for _, _, limited in out)


def test_opposing_hand_on_driver_limiter_is_an_override():
  frames = [(300, 0)] * 40 + [(300, -20)] * 40 + [(300, 0)] * 40
  out = run_ti_pipeline(frames)
  assert out[39][0] == 300
  assert not any(override or limited for _, override, limited in out[:40])
  hold = out[40:80]
  assert hold[-1][0] == 0
  assert all(override and limited for _, override, limited in hold[1:])
  assert not any(override for _, override, _ in out[84:])


def test_sustained_non_driver_limit_freezes_after_the_threshold():
  controller = limiter()
  controller.update_steer_limited(True, 0.5, 0.0, 0.0)  # output still matches the settled zero request
  flags = [controller.update_steer_limited(True, 0.5, 0.2, 0.0) for _ in range(TI_SUSTAINED_LIMIT_FRAMES + 5)]
  assert not any(flags[:TI_SUSTAINED_LIMIT_FRAMES - 1])
  assert all(flags[TI_SUSTAINED_LIMIT_FRAMES - 1:])
  assert not controller.ti_driver_override


def test_driver_limiter_flag_matches_limiter():
  for s in range(-60, 61, 3):
    lo, hi = ti_driver_torque_limits(s, TI_LIMITS)
    for request in (-599, -300, -40, 0, 40, 300, 599):
      clipped = apply_ti_steer_torque_limits(request, request, s, TI_LIMITS) != request
      assert ti_driver_limiter_binds(request, s, TI_LIMITS) == clipped == (not lo <= request <= hi)
      if clipped:
        assert s * request < 0 and abs(s) > TI_LIMITS.TI_STEER_DRIVER_ALLOWANCE


def test_controls_hook_reads_carcontrol_carstate_and_caroutput():
  controller = limiter()
  CC = car.CarControl.new_message()
  CC.latActive = True
  CC.actuators.torque = 0.3
  CS = car.CarState.new_message()
  CO = car.CarOutput.new_message()
  CO.actuatorsOutput.torque = 0.0
  assert not controller.controls_steer_limited(CC, CS, CO)
  assert list(controller._ti_torque_requests)[-1] == pytest.approx(0.3)
