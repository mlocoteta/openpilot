from openpilot.selfdrive.modeld import egpu_recovery as R
from openpilot.selfdrive.modeld.egpu_recovery import CarInputs, EgpuRecovery
from openpilot.selfdrive.selfdrived.egpu_alert import GpuBackupAlert, alert_text

MOVING_ENGAGED = CarInputs(v_ego=20.0, enabled=True, lat_active=True, long_active=True, valid=True)
MOVING_AOL_ONLY = CarInputs(v_ego=20.0, enabled=False, lat_active=True, long_active=False, valid=True)
MOVING_DISENGAGED = CarInputs(v_ego=20.0, valid=True)
STOPPED_OP_HOLDING = CarInputs(standstill=True, enabled=True, lat_active=True, long_active=True, valid=True)
STOPPED_BRAKE_AOL = CarInputs(standstill=True, brake_pressed=True, lat_active=True, valid=True)
STOPPED_NO_BRAKE = CarInputs(standstill=True, valid=True)


def run(rec, t0, t1, car, supply_mv=14000, usb=True, big=False, dt=0.05, until_request=True):
  """Feed the monitor at 20 Hz; return the times at which it requested an onroad cycle.
  By default stop at the first request, as the real onroad cycle ends this modeld process."""
  requests = []
  t = t0
  while t < t1:
    if rec.update(t, big, supply_mv, usb, car):
      requests.append(round(t, 2))
      if until_request:
        break
    t += dt
  return requests


def new(tmp_path, big=False, now=0.0, enabled=True):
  return EgpuRecovery(big, now, state_path=tmp_path / "s.json", enabled=enabled)


def test_safe_moment_gates():
  assert EgpuRecovery.safe_moment(MOVING_ENGAGED) is None
  assert EgpuRecovery.safe_moment(MOVING_AOL_ONLY) is None
  assert EgpuRecovery.safe_moment(STOPPED_OP_HOLDING) is None    # openpilot holds the car: never
  assert EgpuRecovery.safe_moment(STOPPED_NO_BRAKE) == "disengaged"
  assert EgpuRecovery.safe_moment(STOPPED_BRAKE_AOL) == "standstill"
  assert EgpuRecovery.safe_moment(MOVING_DISENGAGED) == "disengaged"
  assert EgpuRecovery.safe_moment(CarInputs(standstill=True, brake_pressed=True)) is None  # stale/invalid inputs


def test_route_319_power_returns_then_switches_at_brake_held_stop(tmp_path):
  rec = new(tmp_path)
  # 0-242 s: Chestnut 12 V missing while driving engaged.
  assert run(rec, 0, 242, MOVING_ENGAGED, supply_mv=10) == []
  assert rec.state.stage == R.WAIT_POWER and rec.state.power_loss_seen and rec.state.detail == "no 12 V"
  # Power back but still engaged at speed: wait.
  assert run(rec, 242, 400, MOVING_ENGAGED) == []
  assert rec.state.stage == R.WAIT_SAFE
  # Brake-held stop with AOL lateral: request after the 1 s hold.
  req = run(rec, 400, 410, STOPPED_BRAKE_AOL)
  assert len(req) == 1 and 401.0 <= req[0] <= 402.1
  assert rec.state.stage == R.SWITCHING and rec.state.pending and rec.state.attempts == 1


def test_power_must_be_stable_for_10s(tmp_path):
  rec = new(tmp_path)
  run(rec, 0, 5, STOPPED_BRAKE_AOL, supply_mv=0)
  req = run(rec, 5, 30, STOPPED_BRAKE_AOL)
  assert len(req) == 1 and 15.0 <= req[0] <= 16.1
  # A dip resets the stability timer.
  (tmp_path / "b").mkdir()
  rec2 = new(tmp_path / "b")
  run(rec2, 0, 2, STOPPED_BRAKE_AOL, supply_mv=0)
  run(rec2, 2, 9, STOPPED_BRAKE_AOL)
  run(rec2, 9, 10, STOPPED_BRAKE_AOL, supply_mv=9000)
  req = run(rec2, 10, 30, STOPPED_BRAKE_AOL)
  assert len(req) == 1 and req[0] >= 20.0


def test_usb_product_required(tmp_path):
  rec = new(tmp_path)
  assert run(rec, 0, 60, STOPPED_BRAKE_AOL, usb=False) == []
  assert rec.state.stage == R.WAIT_POWER


def test_never_requests_while_openpilot_controls(tmp_path):
  rec = new(tmp_path)
  run(rec, 0, 5, MOVING_ENGAGED, supply_mv=0)
  assert run(rec, 5, 600, MOVING_ENGAGED) == []
  assert run(rec, 600, 900, MOVING_AOL_ONLY) == []
  assert run(rec, 900, 1200, STOPPED_OP_HOLDING) == []


def test_moving_disengaged_needs_10s(tmp_path):
  rec = new(tmp_path)
  run(rec, 0, 5, MOVING_ENGAGED, supply_mv=0)
  run(rec, 5, 30, MOVING_ENGAGED)
  req = run(rec, 30, 60, MOVING_DISENGAGED)
  assert len(req) == 1 and 40.0 <= req[0] <= 41.1
  # A brief disengagement does not count.
  (tmp_path / "b").mkdir()
  rec2 = new(tmp_path / "b")
  run(rec2, 0, 5, MOVING_ENGAGED, supply_mv=0)
  run(rec2, 5, 30, MOVING_ENGAGED)
  for k in range(10):
    assert run(rec2, 30 + 10 * k, 35 + 10 * k, MOVING_DISENGAGED) == []
    assert run(rec2, 35 + 10 * k, 40 + 10 * k, MOVING_ENGAGED) == []


def test_failed_attempts_backoff_and_give_up(tmp_path):
  t = 0.0
  rec = new(tmp_path, now=t)
  run(rec, 0, 5, STOPPED_BRAKE_AOL, supply_mv=0)
  assert len(run(rec, 5, 20, STOPPED_BRAKE_AOL)) == 1
  attempts = []
  for _ in range(2, 6):
    # modeld restarts after the cycle; the big model fails again.
    t = rec.state.last_attempt_t + 35.0
    rec = new(tmp_path, big=False, now=t)
    assert rec.state.stage in (R.BACKOFF, R.GAVE_UP)
    if rec.state.stage == R.GAVE_UP:
      break
    req = run(rec, t, t + 1000, STOPPED_BRAKE_AOL)
    assert len(req) == 1
    attempts.append(req[0] - t)
  assert rec.state.stage == R.GAVE_UP and rec.state.attempts == R.MAX_ATTEMPTS
  # Backoff: 120 s after the first failure, 300 s after the second (+10 s power stability on restart).
  assert 119.0 <= attempts[0] <= 121.0
  assert 299.0 <= attempts[1] <= 301.0
  assert run(rec, t, t + 3000, STOPPED_BRAKE_AOL) == []


def test_success_resets_and_reports_recovered(tmp_path):
  rec = new(tmp_path)
  run(rec, 0, 5, STOPPED_BRAKE_AOL, supply_mv=0)
  assert len(run(rec, 5, 20, STOPPED_BRAKE_AOL)) == 1
  rec = new(tmp_path, big=True, now=50.0)
  assert rec.state.stage == R.RECOVERED and not rec.state.pending
  assert run(rec, 50, 100, MOVING_ENGAGED, big=True) == []
  assert rec.state.stage == R.RECOVERED
  run(rec, 100, 120, MOVING_ENGAGED, big=True)
  assert rec.state.stage == R.IDLE


def test_fresh_start_resets_budget(tmp_path):
  rec = new(tmp_path)
  rec.state.attempts, rec.state.stage = 3, R.GAVE_UP
  rec._save(0.0)
  rec = new(tmp_path, now=10.0)   # not pending: ignition or manual cycle
  assert rec.state.attempts == 0 and rec.state.stage == R.WAIT_POWER


def test_no_power_loss_seen_means_one_late_attempt(tmp_path):
  rec = new(tmp_path)
  req = run(rec, 0, 300, STOPPED_BRAKE_AOL)
  assert len(req) == 1 and 59.9 <= req[0] <= 61.1
  rec = new(tmp_path, now=req[0] + 35)
  assert rec.state.stage == R.GAVE_UP


def test_cycle_not_honoured_counts_as_failure(tmp_path):
  rec = new(tmp_path)
  run(rec, 0, 5, STOPPED_BRAKE_AOL, supply_mv=0)
  req = run(rec, 5, 20, STOPPED_BRAKE_AOL)
  assert len(req) == 1
  run(rec, req[0], req[0] + R.CYCLE_TIMEOUT_SECONDS + 2, STOPPED_BRAKE_AOL, until_request=False)
  assert rec.state.stage == R.BACKOFF and not rec.state.pending


def test_runtime_fallback_after_big_model_was_active(tmp_path):
  rec = new(tmp_path, big=True)
  assert run(rec, 0, 30, MOVING_ENGAGED, big=True) == []
  assert rec.state.stage == R.IDLE
  run(rec, 30, 40, MOVING_ENGAGED, supply_mv=0)   # big model died with the power
  assert rec.state.stage == R.WAIT_POWER
  assert len(run(rec, 40, 80, STOPPED_BRAKE_AOL)) == 1


def test_disabled_never_requests(tmp_path):
  rec = new(tmp_path, enabled=False)
  run(rec, 0, 5, STOPPED_BRAKE_AOL, supply_mv=0)
  assert run(rec, 5, 600, STOPPED_BRAKE_AOL) == []
  assert rec.state.stage == R.DISABLED


def test_corrupt_state_file_is_ignored(tmp_path):
  (tmp_path / "s.json").write_text("{not json")
  rec = new(tmp_path)
  assert rec.state.stage == R.WAIT_POWER
  (tmp_path / "s.json").write_text('{"stage": 5, "bogus": 1}')
  assert R.load_state(tmp_path / "s.json").stage == 5


def test_status_staleness(tmp_path):
  rec = new(tmp_path, now=100.0)
  assert R.read_status(tmp_path / "s.json", now=101.0) is not None
  assert R.read_status(tmp_path / "s.json", now=100.0 + R.STALE_SECONDS + 0.1) is None
  assert R.read_status(tmp_path / "missing.json", now=1.0) is None
  del rec


def test_alert_shows_on_stage_change_then_reminds():
  a = GpuBackupAlert()
  s = R.RecoveryState(stage=R.WAIT_POWER, detail="no 12 V")
  assert a.update(0.0, s) == ("Backup driving model", "GPU reconnecting: no 12 V power")
  assert a.update(11.0, s) is not None
  assert a.update(13.0, s) is None
  assert a.update(299.0, s) is None
  assert a.update(300.5, s) is not None   # reminder
  s2 = R.RecoveryState(stage=R.WAIT_SAFE)
  assert a.update(320.0, s2)[1].startswith("GPU ready")
  assert a.update(400.0, s2) is None
  sw = R.RecoveryState(stage=R.SWITCHING)
  assert a.update(500.0, sw)[0] == "Switching to GPU model"
  assert a.update(560.0, sw) is not None   # stays up until the cycle
  assert a.update(600.0, R.RecoveryState(stage=R.IDLE)) is None
  assert a.update(600.0, None) is None
  rec = R.RecoveryState(stage=R.RECOVERED)
  assert a.update(700.0, rec) == ("GPU model restored", "")
  assert a.update(707.0, rec) is None


def test_alert_text_covers_every_stage():
  for stage in (R.WAIT_POWER, R.WAIT_SAFE, R.BACKOFF, R.SWITCHING, R.GAVE_UP, R.DISABLED, R.RECOVERED):
    t1, _ = alert_text(R.RecoveryState(stage=stage, attempts=1))
    assert t1
  assert alert_text(R.RecoveryState(stage=R.IDLE)) == ("", "")


def test_alert_text_fits_mid_alert():
  import os
  from PIL import Image, ImageDraw, ImageFont
  from openpilot.common.basedir import BASEDIR
  fonts = os.path.join(BASEDIR, "selfdrive/assets/fonts")
  bold, regular = ImageFont.truetype(os.path.join(fonts, "Inter-Bold.ttf"), 88), ImageFont.truetype(os.path.join(fonts, "Inter-SemiBold.ttf"), 66)
  draw = ImageDraw.Draw(Image.new('RGB', (0, 0)))
  for stage in (R.WAIT_POWER, R.WAIT_SAFE, R.BACKOFF, R.SWITCHING, R.GAVE_UP, R.DISABLED, R.RECOVERED):
    for detail in ("", "no 12 V"):
      t1, t2 = alert_text(R.RecoveryState(stage=stage, attempts=3, detail=detail))
      for txt, font in ((t1, bold), (t2, regular)):
        left, _, right, _ = draw.textbbox((0, 0), txt, font)
        assert right - left <= 2160 - 300, txt
