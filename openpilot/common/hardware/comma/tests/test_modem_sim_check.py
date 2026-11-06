"""Accord: Home sidebar tap -> modem daemon re-checks the SIM and always republishes with the request id."""
from unittest import mock

import pytest

from openpilot.common.hardware.comma import modem as modem_mod
from openpilot.common.hardware.comma.modem import Modem, State

NO_SIM = {"imei": "861234567890123", "iccid": "", "mcc_mnc": "", "modem_version": "EG25"}
SIM = {"imei": "861234567890123", "iccid": "8901260", "mcc_mnc": "310260", "modem_version": "EG25"}


class FakeAT:
  """AT+CPIN? answers from `cpin` ("READY" or a +CME ERROR); everything else OK."""
  def __init__(self, m, cpin):
    self.m, self.cpin, self.sent = m, cpin, []

  def __call__(self, cmd):
    self.sent.append(cmd)
    self.m._last_at_error = ""
    if cmd == "AT+CPIN?":
      if self.cpin == "READY":
        return ["+CPIN: READY"]
      self.m._last_at_error = self.cpin
      return []
    return []


@pytest.fixture
def env(tmp_path, monkeypatch):
  path = tmp_path / "modem_sim_check"
  monkeypatch.setattr(modem_mod, "SIM_CHECK_PATH", str(path))
  monkeypatch.setattr(modem_mod, "SIM_CHECK_READY_WAIT", 0.0)
  monkeypatch.setattr(modem_mod.time, "sleep", lambda s: None)
  return path


def _modem(identity, cpin="+CME ERROR: 10", onroad=""):
  m = Modem()
  published = []
  m._publish_state = lambda **kw: (published.append(kw), m.S.update(kw))  # ty: ignore[invalid-assignment]  # test double
  m._read_identity = lambda: dict(identity)  # ty: ignore[invalid-assignment]  # test double
  m._read_param = lambda key: onroad if key == "IsOnroad" else ""  # ty: ignore[invalid-assignment]  # test double
  m._ppp = mock.MagicMock()
  at = FakeAT(m, cpin)
  m._at = at  # ty: ignore[invalid-assignment]  # test double
  return m, published, at


def test_no_request_does_nothing(env):
  m, published, at = _modem(NO_SIM)
  m._handle_sim_check(State.INITIALIZING)
  assert published == [] and at.sent == []


def test_no_sim_power_cycles_and_republishes_unchanged_result(env):
  m, published, at = _modem(NO_SIM)
  m.S["sim"] = "absent"
  env.write_text("123.456")
  m._handle_sim_check(State.INITIALIZING)
  assert not env.exists()  # request consumed
  assert at.sent[:2] == ["AT+CFUN=0", "AT+CFUN=1"]
  assert len(published) == 1
  p = published[0]
  assert p["sim_check_id"] == "123.456" and p["sim"] == "absent" and p["sim_check_t"] > 0
  assert m._sim_checks == 1


def test_counter_bumps_and_survives_reconnect_reset(env, monkeypatch):
  m, published, _ = _modem(NO_SIM)
  m._publish_state = Modem._publish_state.__get__(m)  # ty: ignore[invalid-assignment]  # real publish into tmp
  monkeypatch.setattr(modem_mod, "STATE_PATH", str(env.parent / "modem"))
  monkeypatch.setattr(modem_mod.tempfile, "NamedTemporaryFile",
                      lambda **kw: open(env.parent / "modem.tmp", "w"))
  env.write_text("a")
  m._handle_sim_check(State.INITIALIZING)
  assert m.S["sim_check"] == 1 and m.S["sim_check_id"] == "a"
  m._publish_state(**modem_mod.INITIAL_STATE)
  assert m.S["sim_check"] == 1


def test_sim_appears_after_power_cycle(env):
  m, published, _ = _modem(SIM, cpin="READY")
  m.S["sim"] = "absent"
  env.write_text("x")
  m._handle_sim_check(State.INITIALIZING)
  assert published[-1]["sim"] == "ready" and published[-1]["sim_check_id"] == "x"


def test_working_sim_is_not_power_cycled(env):
  m, published, at = _modem(SIM, cpin="READY")
  m.S["sim"] = "ready"
  env.write_text("y")
  m._handle_sim_check(State.CONNECTED)
  assert "AT+CFUN=0" not in at.sent
  assert published[-1]["sim"] == "ready" and published[-1]["sim_check_id"] == "y"


def test_cfun1_retried_until_ok(env):
  m, published, at = _modem(NO_SIM)
  fails = {"n": 2}

  def flaky(cmd):
    at.sent.append(cmd)
    m._last_at_error = ""
    if cmd == "AT+CFUN=1" and fails["n"]:
      fails["n"] -= 1
      m._last_at_error = "AT timeout"
    return []
  m._at = flaky  # ty: ignore[invalid-assignment]  # test double
  env.write_text("z")
  m._handle_sim_check(State.INITIALIZING)
  assert at.sent.count("AT+CFUN=1") == 3


def test_onroad_ignored(env):
  m, published, at = _modem(NO_SIM, onroad="1")
  env.write_text("r")
  m._handle_sim_check(State.INITIALIZING)
  assert not env.exists() and published == [] and at.sent == []
  assert m._sim_check_t is None  # an onroad tap doesn't start the rate limit


def test_rate_limit(env, monkeypatch):
  m, published, at = _modem(NO_SIM)
  t = {"now": 100.0}
  monkeypatch.setattr(modem_mod.time, "monotonic", lambda: t["now"])
  env.write_text("1")
  m._handle_sim_check(State.INITIALIZING)
  t["now"] += 5
  env.write_text("2")
  m._handle_sim_check(State.INITIALIZING)
  assert [p["sim_check_id"] for p in published] == ["1"] and not env.exists()
  t["now"] += 6
  env.write_text("3")
  m._handle_sim_check(State.INITIALIZING)
  assert [p["sim_check_id"] for p in published] == ["1", "3"]


def test_run_loop_handles_request(env, monkeypatch):
  m, published, _ = _modem(NO_SIM)
  m.S["sim"] = "absent"
  env.write_text("loop")
  m._has_modem_manager = lambda: False  # ty: ignore[invalid-assignment]  # test double

  def init_once():
    m.running = False
    return State.INITIALIZING
  m._do_initializing = init_once  # ty: ignore[invalid-assignment]  # test double
  m.run()
  assert any(p.get("sim_check_id") == "loop" for p in published)
