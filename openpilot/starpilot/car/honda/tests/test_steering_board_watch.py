from types import SimpleNamespace

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.starpilot.car.honda.steering_board_watch import install
from openpilot.starpilot.vehicle_preferences import VehicleStartupPreferences


class FakeParams:
  """Only the methods openpilot.common.params.Params really has (7.0: put/put_bool are queued unless block=True)."""
  def __init__(self, missing=False):
    self.values = {"TorqueInterceptorMissing": missing}
    self.writes = []

  def get(self, key):
    return self.values.get(key)

  def get_bool(self, key):
    return self.values.get(key, False)

  def put(self, key, value, block=False):
    self.values[key] = value
    self.writes.append((key, value))

  def put_bool(self, key, value, block=False):
    self.values[key] = value
    self.writes.append((key, value))


def test_fake_params_matches_real_params():
  from openpilot.common.params import Params
  for name in ("get", "get_bool", "put", "put_bool"):
    assert callable(getattr(Params, name))
  assert not hasattr(Params, "put_bool_nonblocking")   # the bug this fake now catches


def cp_9g():
  return CarInterface.get_params(CAR.HONDA_ACCORD_9G, gen_empty_fingerprint(), [], False, False, False)


def fp(ssv3: bool, ti: bool = False):
  f = gen_empty_fingerprint()
  if ssv3:
    f[0][0x190] = 5
  if ti:
    f[0][0x24A] = 8
  return f


def test_startup_selection_ti_unchanged_and_fallback():
  ti_bit = 4096
  for prefs, ssv3, ti, *rest in (
    (VehicleStartupPreferences(honda_torque_interceptor=True), True, True),        # today
    (VehicleStartupPreferences(honda_torque_interceptor=True, honda_ti_missing=True), True, False),
    (VehicleStartupPreferences(honda_torque_interceptor=True, honda_ti_missing=True), False, True),
    (VehicleStartupPreferences(honda_torque_interceptor=True, honda_board_override="ssv3"), True, False),
    (VehicleStartupPreferences(honda_torque_interceptor=False), True, False),
    # TI switch off = SSV3 only, even with a talking TI and the "ti" override
    (VehicleStartupPreferences(honda_torque_interceptor=False), True, False, True),
    (VehicleStartupPreferences(honda_torque_interceptor=False, honda_board_override="ti"), True, False, True),
    (VehicleStartupPreferences(honda_torque_interceptor=True), True, True, True),
  ):
    cp = cp_9g()
    base = int(cp.safetyConfigs[0].safetyParam)
    prefs.prepare(cp, fingerprints=fp(ssv3, *rest))
    assert bool(int(cp.safetyConfigs[0].safetyParam) & ti_bit) is ti
    if not ti:
      assert int(cp.safetyConfigs[0].safetyParam) == base


def test_watch_records_once_and_clears_once():
  cp = cp_9g()
  from opendbc.car.honda.torque_interceptor import apply_torque_interceptor
  apply_torque_interceptor(cp, True)
  ci = CarInterface(cp)
  params = FakeParams(missing=True)
  watch = install(ci, params)
  ci.CS.ti.feedback_seen = True
  watch.update()
  watch.update()
  assert params.writes == [("TorqueInterceptorMissing", False)]
  ci.CS.ti.feedback_seen = False
  ci.CS.ti_presence.missing = True
  watch.update()
  watch.update()
  assert params.writes[-1] == ("TorqueInterceptorMissing", True) and len(params.writes) == 2


def test_no_watch_off_the_ti_path():
  assert install(CarInterface(cp_9g()), FakeParams()) is None
  assert install(SimpleNamespace(CS=None), FakeParams()) is None


# ---- persistent board record (AccordSteeringBoardSeen) ----
import json  # noqa: E402

from openpilot.starpilot.car.honda.steering_board_watch import (BoardSeenRecorder, SEEN_PARAM, SCAN_FRAMES,  # noqa: E402
                                                                install_seen, parse_seen, seen_recently)

NOW = 1794000000   # 2026-11-08


def can(*frames):
  return [(0, [(addr, bytes(dat), src) for addr, dat, src in frames])]


SSV3_FW3 = (0x208, [0x43, 0x00, 0x16], 0)
SSV3_STATUS = (0x190, [0] * 5, 0)
TI_FB = (0x24A, [0] * 6, 0)


class Clock:
  def __init__(self, t):
    self.t = t

  def __call__(self):
    return self.t


def test_install_seen_every_9g_drive():
  cp = cp_9g()
  assert isinstance(install_seen(cp, CarInterface(cp), FakeParams()), BoardSeenRecorder)
  cp.passive = True   # openpilot disabled (datalogger): still recorded
  assert isinstance(install_seen(cp, SimpleNamespace(CS=None), FakeParams()), BoardSeenRecorder)
  assert install_seen(SimpleNamespace(carFingerprint="HONDA_CIVIC"), SimpleNamespace(CS=None), FakeParams()) is None


def test_records_ssv3_with_firmware_once_per_drive():
  params = FakeParams()
  rec = BoardSeenRecorder(None, params, clock=Clock(NOW))
  for _ in range(5):
    rec.update(can(SSV3_STATUS, SSV3_FW3, (0x208, [0x43, 0, 0], 2)))
  assert params.writes == [(SEEN_PARAM, {"ti": None, "ssv3": NOW, "ssv3Firmware": 3})]


def test_ssv3_only_drive_keeps_the_ti_record():
  params = FakeParams()
  params.values[SEEN_PARAM] = {"ti": NOW - 86400 * 3, "ssv3": NOW - 86400 * 3, "ssv3Firmware": 2}
  rec = BoardSeenRecorder(SimpleNamespace(ti=None), params, clock=Clock(NOW))
  for _ in range(SCAN_FRAMES + 50):
    rec.update(can(SSV3_FW3))
  assert params.values[SEEN_PARAM] == {"ti": NOW - 86400 * 3, "ssv3": NOW, "ssv3Firmware": 3}
  assert len(params.writes) == 1


def test_ti_drive_records_both_boards():
  params = FakeParams()
  cs = SimpleNamespace(ti=SimpleNamespace(feedback_seen=False))
  rec = BoardSeenRecorder(cs, params, clock=Clock(NOW))
  rec.update(can(SSV3_STATUS))                 # SSV3 first, TI silent until commanded
  cs.ti.feedback_seen = True
  rec.update(can())
  assert params.values[SEEN_PARAM] == {"ti": NOW, "ssv3": NOW, "ssv3Firmware": None}
  rec2 = BoardSeenRecorder(None, FakeParams(), clock=Clock(NOW))
  rec2.update(can(TI_FB))
  assert rec2.params.values[SEEN_PARAM]["ti"] == NOW


def test_raw_scan_stops_and_bus_filter():
  params = FakeParams()
  rec = BoardSeenRecorder(None, params, clock=Clock(NOW))
  for _ in range(SCAN_FRAMES):
    rec.update(can((0x24A, [0] * 6, 2), (0x190, [0] * 4, 0)))   # wrong bus / wrong length
  rec.update(can(TI_FB, SSV3_FW3))                                # after the scan window
  assert params.writes == []


def test_waits_for_a_valid_wall_clock_and_never_moves_back():
  params = FakeParams()
  clock = Clock(1600000000)   # 2020: no time sync yet
  rec = BoardSeenRecorder(None, params, clock=clock)
  rec.update(can(SSV3_STATUS))
  assert params.writes == []
  clock.t = NOW
  rec.update(can())
  assert params.values[SEEN_PARAM]["ssv3"] == NOW
  params.values[SEEN_PARAM] = {"ti": None, "ssv3": NOW + 100, "ssv3Firmware": None}
  rec = BoardSeenRecorder(None, params, clock=Clock(NOW))
  rec.update(can(SSV3_STATUS))
  assert params.values[SEEN_PARAM]["ssv3"] == NOW + 100


def test_parse_and_recent():
  assert parse_seen(None) == {"ti": None, "ssv3": None, "ssv3Firmware": None}
  assert parse_seen(b"{bad") == parse_seen("[]") == parse_seen(None)
  assert parse_seen(json.dumps({"ti": NOW, "ssv3": "x", "ssv3Firmware": True})) == {"ti": NOW, "ssv3": None, "ssv3Firmware": None}
  seen = {"ti": NOW - 31 * 86400, "ssv3": NOW - 29 * 86400}
  assert not seen_recently(seen, "ti", NOW) and seen_recently(seen, "ssv3", NOW)
  assert seen_recently(seen, "ti", 1600000000)   # clock not synced: any record counts
  assert not seen_recently({"ti": None}, "ti", NOW)


def test_real_params_round_trip(tmp_path):
  from openpilot.common.params import Params
  params = Params(str(tmp_path))
  rec = BoardSeenRecorder(None, params, clock=Clock(NOW))
  rec.update(can(SSV3_FW3, TI_FB))
  ok = False
  for _ in range(200):
    if params.get(SEEN_PARAM) is not None:
      ok = True
      break
    import time
    time.sleep(0.01)
  assert ok and parse_seen(params.get(SEEN_PARAM)) == {"ti": NOW, "ssv3": NOW, "ssv3Firmware": 3}
  params.put_bool("TorqueInterceptorMissing", True, block=True)
  assert params.get_bool("TorqueInterceptorMissing")
