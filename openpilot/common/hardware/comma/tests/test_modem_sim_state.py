from unittest import mock

from openpilot.common.hardware.comma.modem import Modem, State


def _modem(identity):
  m = Modem()
  published = []
  m._publish_state = lambda **kw: (published.append(kw), m.S.update(kw))  # ty: ignore[invalid-assignment]  # test double
  m._init_at_channel = lambda: True  # ty: ignore[invalid-assignment]  # test double
  m._read_identity = lambda: dict(identity)  # ty: ignore[invalid-assignment]  # test double
  m._configure_modem = lambda v: None  # ty: ignore[invalid-assignment]  # test double
  m._at = lambda cmd: []  # ty: ignore[invalid-assignment]  # test double
  m._read_param = lambda key: ""  # ty: ignore[invalid-assignment]  # test double
  m._ppp = mock.MagicMock()
  return m, published


def _init(m):
  with mock.patch("os.path.exists", return_value=True):
    return m._do_initializing()


def test_no_sim_published_once():
  m, published = _modem({"imei": "861234567890123", "iccid": "", "mcc_mnc": "", "modem_version": "EG25"})
  assert _init(m) == State.INITIALIZING
  assert _init(m) == State.INITIALIZING
  assert m.S["sim"] == "absent"
  assert [p for p in published if "sim" in p] == [{"sim": "absent", "imei": "861234567890123"}]


def test_modem_silent_is_not_no_sim():
  m, published = _modem({"imei": "", "iccid": "", "mcc_mnc": "", "modem_version": ""})
  assert _init(m) == State.INITIALIZING
  assert m.S["sim"] == "unknown"
  assert published == []


def test_sim_ready_after_identity():
  m, _ = _modem({"imei": "861234567890123", "iccid": "8901260", "mcc_mnc": "310260", "modem_version": "EG25"})
  m.S["sim"] = "absent"
  assert _init(m) == State.SEARCHING
  assert m.S["sim"] == "ready"
