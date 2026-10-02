import datetime
import json
import struct
import time

from openpilot.system.ubloxd import gnss_aiding as ga


def _now():
  return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def _checksum_ok(msg: bytes) -> bool:
  return ga.add_ubx_checksum(msg[:-2]) == msg


class TestParseQlts:
  def test_utc_response(self):
    # captured on the tici EG25 (EG25GGBR07A08M2G, Verizon), AT+QLTS=1
    resp = b'AT+QLTS=1\r\r\n+QLTS: "2026/10/02,19:22:32-16,1"\r\n\r\nOK\r\n'
    assert ga.parse_qlts(resp) == datetime.datetime(2026, 10, 2, 19, 22, 32)

  def test_positive_offset_and_str(self):
    assert ga.parse_qlts('+QLTS: "2027/01/31,23:59:59+32,0"\r\nOK') == datetime.datetime(2027, 1, 31, 23, 59, 59)

  def test_not_synced_yet(self):
    assert ga.parse_qlts(b'\r\n+QLTS: ""\r\n\r\nOK\r\n') is None

  def test_garbage(self):
    assert ga.parse_qlts(b"") is None
    assert ga.parse_qlts(b"\r\nERROR\r\n") is None
    assert ga.parse_qlts(b'+QLTS: "2026/13/45,99:00:00-16,1"') is None
    # CCLK is never used: on the EG25 it is not network synced
    assert ga.parse_qlts(b'+CCLK: "28/08/15,07:22:50-16"') is None


class TestLastPosition:
  def test_param(self):
    raw = json.dumps({"latitude": 40.9557078, "longitude": -72.8970942, "hasFix": True, "updatedAtSec": 1790894167.0})
    assert ga.last_gps_position(raw) == (40.9557078, -72.8970942, 1790894167.0)
    assert ga.last_gps_position(raw.encode()) == (40.9557078, -72.8970942, 1790894167.0)

  def test_invalid(self):
    assert ga.last_gps_position(None) is None
    assert ga.last_gps_position("") is None
    assert ga.last_gps_position("{}") is None
    assert ga.last_gps_position(json.dumps({"latitude": 0, "longitude": 0})) is None
    assert ga.last_gps_position(json.dumps({"latitude": 91, "longitude": 0})) is None
    assert ga.last_gps_position('{"latitude": NaN, "longitude": 1}') is None
    assert ga.last_gps_position(json.dumps({"latitude": 1, "longitude": 2})) == (1.0, 2.0, None)


class TestTimeValidation:
  def test_floor_uses_saved_position_time(self, mocker):
    stamp = datetime.datetime(2026, 7, 29, 15, 4)
    now = datetime.datetime(2026, 7, 28, 15, 5)
    mocker.patch.object(ga, "min_date", return_value=stamp)
    saved = datetime.datetime(2026, 10, 1, 12, 0, tzinfo=datetime.UTC).timestamp()
    assert ga.time_floor(None, now) == stamp
    assert ga.time_floor(saved, now) == datetime.datetime(2026, 10, 1, 12, 0)
    # an invalid wall time from a bad clock is ignored
    assert ga.time_floor(datetime.datetime(2026, 7, 28, tzinfo=datetime.UTC).timestamp(), now) == stamp
    assert ga.time_floor(1e20, now) == stamp
    # the system clock only moves forward from the stamp, so it is a floor too
    assert ga.time_floor(None, datetime.datetime(2026, 8, 1)) == datetime.datetime(2026, 8, 1)

  def test_plausible(self):
    floor = datetime.datetime(2026, 10, 1)
    assert ga.time_plausible(datetime.datetime(2026, 10, 2), floor)
    assert ga.time_plausible(floor - datetime.timedelta(minutes=1), floor)
    assert not ga.time_plausible(floor - datetime.timedelta(hours=1), floor)
    assert not ga.time_plausible(datetime.datetime(2017, 5, 28), floor)
    assert not ga.time_plausible(datetime.datetime(2036, 1, 1), floor)
    assert not ga.time_plausible(None, floor)


class TestAidingTime:
  def test_invalid_clock_uses_modem(self, mocker):
    modem_t = _now()
    mocker.patch.object(ga, "system_time_valid", return_value=False)
    t, acc, src = ga.get_aiding_time(lambda: modem_t)
    assert (t, acc, src) == (modem_t, ga.NITZ_ACC_S, "modem")

  def test_invalid_clock_rejects_stale_modem(self, mocker):
    mocker.patch.object(ga, "system_time_valid", return_value=False)
    assert ga.get_aiding_time(lambda: datetime.datetime(2017, 5, 28, 10, 42)) is None
    assert ga.get_aiding_time(lambda: None) is None

  def test_valid_clock_skips_modem(self, mocker):
    modem = mocker.Mock()
    mocker.patch.object(ga, "system_time_valid", return_value=True)
    mocker.patch.object(ga, "ntp_synced", return_value=True)
    _, acc, src = ga.get_aiding_time(modem)
    assert (acc, src) == (ga.NTP_ACC_S, "ntp")
    modem.assert_not_called()
    mocker.patch.object(ga, "system_time_valid", return_value=True)
    mocker.patch.object(ga, "ntp_synced", return_value=False)
    assert ga.get_aiding_time(modem)[1:] == (ga.SYSTEM_ACC_S, "system")

  def test_query_modem_time_missing_port(self):
    assert ga.query_modem_time(ports=("/nonexistent/modem_at",)) is None


class TestUbx:
  def test_time_utc_matches_stock_layout(self):
    t = datetime.datetime(2026, 10, 2, 19, 22, 32)
    # the exact bytes pigeond built before this change (tAccS=30, ns=0)
    stock = ga.add_ubx_checksum(b"\xB5\x62\x13\x40\x18\x00" + struct.pack("<BBBBHBBBBBxIHxxI",
      0x10, 0x00, 0x00, 0x80, t.year, t.month, t.day, t.hour, t.minute, t.second, 0, 30, 0))
    assert ga.ubx_mga_ini_time_utc(t, 30) == stock

  def test_time_utc_fields(self):
    t = datetime.datetime(2026, 10, 2, 19, 22, 32, 500000)
    msg = ga.ubx_mga_ini_time_utc(t, 2)
    assert len(msg) == 6 + 24 + 2
    assert msg[:6] == b"\xb5\x62\x13\x40\x18\x00"
    p = msg[6:-2]
    # UBX-MGA-INI-TIME_UTC: type, version, ref, leapSecs, year, month, day, hour, minute, second, res, ns, tAccS, res, tAccNs
    assert p[0] == 0x10 and p[1] == 0 and p[2] == 0 and p[3] == 0x80
    assert struct.unpack_from("<H", p, 4)[0] == 2026
    assert tuple(p[6:11]) == (10, 2, 19, 22, 32)
    assert struct.unpack_from("<I", p, 12)[0] == 500_000_000
    assert struct.unpack_from("<H", p, 16)[0] == 2
    assert struct.unpack_from("<I", p, 20)[0] == 0
    assert _checksum_ok(msg)

  def test_pos_llh(self):
    msg = ga.ubx_mga_ini_pos_llh(40.9557078, -72.8970942, 0, ga.LAST_POSITION_ACC_CM)
    assert len(msg) == 6 + 20 + 2
    assert msg[:6] == b"\xb5\x62\x13\x40\x14\x00"
    p = msg[6:-2]
    # UBX-MGA-INI-POS_LLH: type 0x01, version 0, reserved[2], lat, lon (1e-7 deg), alt (cm), posAcc (cm)
    assert p[0] == 0x01 and p[1] == 0 and p[2:4] == b"\x00\x00"
    assert struct.unpack("<iiiI", p[4:]) == (409557078, -728970942, 0, 1_000_000)
    assert _checksum_ok(msg)

  def test_checksum_known_message(self):
    # UBX-CFG-RATE from pigeond with its known checksum
    assert ga.add_ubx_checksum(b"\xB5\x62\x06\x08\x06\x00\x64\x00\x01\x00\x00\x00") == \
      b"\xB5\x62\x06\x08\x06\x00\x64\x00\x01\x00\x00\x00\x79\x10"

  def test_has_gnss_fix(self):
    def pvt(flags):
      payload = bytearray(92)
      payload[21] = flags
      return ga.add_ubx_checksum(ga.UBX_NAV_PVT + bytes(payload))
    assert ga.has_gnss_fix(b"\x00junk" + pvt(0x01))
    assert ga.has_gnss_fix(pvt(0x00) + pvt(0x03))
    assert not ga.has_gnss_fix(pvt(0x00))
    assert not ga.has_gnss_fix(pvt(0x01)[:20])  # truncated
    assert not ga.has_gnss_fix(b"")


class TestLateAiding:
  def _wait(self, late, timeout=2.0):
    st = time.monotonic()
    while late.result is None and not late.done.is_set() and time.monotonic() - st < timeout:
      time.sleep(0.01)

  def test_retries_until_modem_has_time(self, mocker):
    t = _now()
    answers = iter([None, None, t])
    late = ga.LateAiding(None, modem_query=lambda: next(answers))
    late.POLL_S = 0.01
    mocker.patch.object(ga, "system_time_valid", return_value=False)
    late.start()
    self._wait(late)
    res = late.take()
    assert res is not None and res[1:] == (ga.NITZ_ACC_S, "modem")
    assert res[0] >= t
    assert late.take() is None

  def test_gives_up_at_deadline(self, mocker):
    late = ga.LateAiding(None, modem_query=lambda: None)
    late.POLL_S = 0.01
    late.DEADLINE_S = 0.05
    mocker.patch.object(ga, "system_time_valid", return_value=False)
    late.start()
    late.thread.join(1.0)
    assert late.done.is_set() and late.take() is None

  def test_stop(self, mocker):
    late = ga.LateAiding(None, modem_query=lambda: None)
    mocker.patch.object(ga, "system_time_valid", return_value=False)
    late.start()
    late.stop()
    late.thread.join(1.0)
    assert not late.thread.is_alive()


class FakePigeon:
  def __init__(self, ack=True):
    self.sent: list[bytes] = []
    self.ack = ack
    self.time_aided = False

  def send(self, dat: bytes) -> None:
    self.sent.append(dat)

  def send_with_ack(self, dat: bytes, ack=None, nack=None) -> None:
    self.sent.append(dat)
    if not self.ack:
      raise TimeoutError


class TestPigeondAiding:
  POS = (40.9557078, -72.8970942, None)

  def test_init_sends_modem_time_and_position(self, mocker):
    from openpilot.system.ubloxd import pigeond
    p = FakePigeon()
    t = _now()
    mocker.patch.object(pigeond, "last_position_from_params", return_value=self.POS)
    mocker.patch.object(pigeond, "get_aiding_time", return_value=(t, ga.NITZ_ACC_S, "modem"))
    assert pigeond.send_aiding_without_valid_time(p)
    assert p.sent == [ga.ubx_mga_ini_time_utc(t, ga.NITZ_ACC_S),
                      ga.ubx_mga_ini_pos_llh(self.POS[0], self.POS[1], 0, ga.LAST_POSITION_ACC_CM)]

  def test_init_without_time_or_ack_never_raises(self, mocker):
    from openpilot.system.ubloxd import pigeond
    p = FakePigeon()
    mocker.patch.object(pigeond, "last_position_from_params", return_value=self.POS)
    mocker.patch.object(pigeond, "get_aiding_time", return_value=None)
    assert not pigeond.send_aiding_without_valid_time(p)
    assert len(p.sent) == 1  # position only
    p = FakePigeon(ack=False)
    mocker.patch.object(pigeond, "last_position_from_params", return_value=None)
    mocker.patch.object(pigeond, "get_aiding_time", return_value=(_now(), 2, "modem"))
    assert not pigeond.send_aiding_without_valid_time(p)
    mocker.patch.object(pigeond, "last_position_from_params", return_value=None)
    mocker.patch.object(pigeond, "get_aiding_time", side_effect=RuntimeError)
    assert not pigeond.send_aiding_without_valid_time(FakePigeon())

  def test_late_aiding_injects_once(self, mocker):
    from openpilot.system.ubloxd import pigeond
    p = FakePigeon()
    late = ga.LateAiding(None)
    assert pigeond.update_late_aiding(p, late, b"") is late  # nothing yet
    late.result = (_now(), time.monotonic(), ga.NTP_ACC_S, "ntp")
    mocker.patch.object(pigeond, "last_position_from_params", return_value=self.POS)
    assert pigeond.update_late_aiding(p, late, b"") is None
    assert [m[:6] for m in p.sent] == [b"\xb5\x62\x13\x40\x18\x00", b"\xb5\x62\x13\x40\x14\x00"]
    assert p.time_aided

  def test_late_aiding_stops_on_fix_or_give_up(self):
    from openpilot.system.ubloxd import pigeond
    payload = bytearray(92)
    payload[21] = 0x01
    fix = ga.add_ubx_checksum(ga.UBX_NAV_PVT + bytes(payload))
    late = ga.LateAiding(None)
    assert pigeond.update_late_aiding(FakePigeon(), late, fix) is None
    assert late.done.is_set()
    late = ga.LateAiding(None)
    late.done.set()
    p = FakePigeon()
    assert pigeond.update_late_aiding(p, late, b"") is None
    assert p.sent == []

  def test_no_late_aiding_when_time_was_sent(self):
    from openpilot.system.ubloxd import pigeond
    p = FakePigeon()
    p.time_aided = True
    assert pigeond.start_late_aiding(p) is None
