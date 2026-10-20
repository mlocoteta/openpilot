"""
Time and position aiding for the u-blox when the system clock is not valid yet.

The tici RTC can be dead, so the clock boots at the systemd build stamp and
pigeond used to skip UBX-MGA-INI-TIME_UTC entirely (cold start every drive).
NTP over LTE only fixes the clock ~15-20 s after pigeond has initialized.

Time sources, best first:
- the system clock once NTP has synced (systemd-timesyncd marker file)
- the LTE modem's NITZ time (Quectel AT+QLTS=1, UTC) on the AT port that
  ModemManager ignores. AT+CCLK? is not used: on the EG25 it is not network
  synced and reads years off.
- the system clock when it is valid for any other reason (GPS via timed)

Coarse position comes from the LastGPSPosition param.
"""
import datetime
import json
import os
import struct
import threading
import time
from collections.abc import Callable
from pathlib import Path

from openpilot.common.swaglog import cloudlog
from openpilot.common.time_helpers import MAX_DATE, min_date, system_time_valid

MODEM_AT_PORTS = ("/dev/modem_at1", "/dev/modem_at0")
TIMESYNCD_SYNCED = Path("/run/systemd/timesync/synchronized")

# NITZ is truncated to whole seconds and measured ~0.5 s behind NTP on the EG25
NITZ_OFFSET_S = 0.5
NITZ_ACC_S = 2
NTP_ACC_S = 1
SYSTEM_ACC_S = 30  # unknown source (GPS/car clock via timed), same as the stock path

LAST_POSITION_ACC_CM = 10_000 * 100  # 10 km: the car may have moved while off

UBX_HEADER = b"\xb5\x62"
UBX_NAV_PVT = b"\xb5\x62\x01\x07\x5c\x00"


def add_ubx_checksum(msg: bytes) -> bytes:
  A = B = 0
  for b in msg[2:]:
    A = (A + b) % 256
    B = (B + A) % 256
  return msg + bytes([A, B])


def ubx_mga_ini_time_utc(t: datetime.datetime, acc_s: int, acc_ns: int = 0) -> bytes:
  # UBX-MGA-INI-TIME_UTC (0x13 0x40), type 0x10, UTC reference, leap seconds unknown (0x80)
  return add_ubx_checksum(UBX_HEADER + b"\x13\x40\x18\x00" + struct.pack("<BBBBHBBBBBxIHxxI",
    0x10,
    0x00,
    0x00,
    0x80,
    t.year,
    t.month,
    t.day,
    t.hour,
    t.minute,
    t.second,
    t.microsecond * 1000,
    acc_s,
    acc_ns,
  ))


def ubx_mga_ini_pos_llh(lat: float, lon: float, alt_cm: int, acc_cm: int) -> bytes:
  # UBX-MGA-INI-POS_LLH (0x13 0x40), type 0x01: lat/lon 1e-7 deg, alt cm, posAcc cm (stddev)
  return add_ubx_checksum(UBX_HEADER + b"\x13\x40\x14\x00" + struct.pack("<BBxxiiiI",
    0x01,
    0x00,
    round(lat * 1e7),
    round(lon * 1e7),
    alt_cm,
    acc_cm,
  ))


def parse_qlts(resp: bytes | str) -> datetime.datetime | None:
  """Parse a Quectel `+QLTS: "yyyy/MM/dd,hh:mm:ss±zz,d"` response, naive datetime.

  With AT+QLTS=1 the date/time is UTC; zz (quarter hours) is the local offset and is ignored.
  Returns None when the modem has no network time yet (`+QLTS: ""`) or on garbage.
  """
  if isinstance(resp, bytes):
    resp = resp.decode("ascii", errors="replace")
  for line in resp.splitlines():
    line = line.strip()
    if not line.startswith("+QLTS:"):
      continue
    parts = line.split('"')
    if len(parts) < 3 or len(parts[1]) < 19:
      return None
    try:
      return datetime.datetime.strptime(parts[1][:19], "%Y/%m/%d,%H:%M:%S")
    except ValueError:
      return None
  return None


def last_gps_position(raw) -> tuple[float, float, float | None] | None:
  """(lat, lon, updatedAtSec) from the LastGPSPosition param, or None if unusable."""
  try:
    if isinstance(raw, bytes):
      raw = raw.decode("utf-8")
    pos = json.loads(raw) if isinstance(raw, str) else raw
    lat, lon = float(pos["latitude"]), float(pos["longitude"])
  except Exception:
    return None
  if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0) or lat != lat or lon != lon:
    return None
  updated = pos.get("updatedAtSec")
  return lat, lon, float(updated) if isinstance(updated, (int, float)) else None


def time_floor(last_position_sec: float | None = None, now: datetime.datetime | None = None) -> datetime.datetime:
  """Earliest plausible current time: the systemd stamp, the (monotonic since stamp) system clock,
  and the wall time the last GPS position was saved at, if that was valid."""
  if now is None:
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
  floor = max(min_date(), now)
  if last_position_sec is not None:
    try:
      saved = datetime.datetime.fromtimestamp(last_position_sec, datetime.UTC).replace(tzinfo=None)
    except (OverflowError, OSError, ValueError):
      saved = None
    if saved is not None and min_date() < saved < MAX_DATE:
      floor = max(floor, saved)
  return floor


def time_plausible(t: datetime.datetime | None, floor: datetime.datetime) -> bool:
  # small slack for floor sources that are rounded or slightly ahead
  return t is not None and floor - datetime.timedelta(minutes=5) <= t < MAX_DATE


def query_modem_time(ports=MODEM_AT_PORTS, timeout: float = 1.0) -> datetime.datetime | None:
  """NITZ UTC from the modem AT port, None if unavailable. Never blocks longer than ~timeout per port."""
  import serial
  for port in ports:
    if not os.path.exists(port):
      continue
    try:
      with serial.Serial(port, 115200, timeout=0.05, write_timeout=timeout, exclusive=True) as s:
        s.reset_input_buffer()
        s.write(b"AT+QLTS=1\r")
        buf = b""
        st = time.monotonic()
        while time.monotonic() - st < timeout:
          buf += s.read(128)
          if b"OK\r" in buf or b"ERROR" in buf:
            break
      t = parse_qlts(buf)
      if t is not None:
        return t + datetime.timedelta(seconds=NITZ_OFFSET_S)
      if b"OK\r" in buf:
        # port works, the modem just has no network time yet
        return None
    except Exception as e:
      cloudlog.debug(f"gnss aiding: modem time query on {port} failed: {e}")
  return None


def ntp_synced() -> bool:
  try:
    return TIMESYNCD_SYNCED.exists()
  except OSError:
    return False


def get_aiding_time(modem_query: Callable[[], datetime.datetime | None] = query_modem_time,
                    last_position_sec: float | None = None) -> tuple[datetime.datetime, int, str] | None:
  """(utc_time, accuracy_s, source) or None. The modem query is only used while the system clock is invalid."""
  if system_time_valid():
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    return (now, NTP_ACC_S, "ntp") if ntp_synced() else (now, SYSTEM_ACC_S, "system")

  floor = time_floor(last_position_sec)
  t = modem_query()
  if t is None:
    return None
  if not time_plausible(t, floor):
    cloudlog.warning(f"gnss aiding: ignoring implausible modem time {t} (floor {floor})")
    return None
  # the modem time was read just now, take it as of this instant
  return t, NITZ_ACC_S, "modem"


def has_gnss_fix(dat: bytes) -> bool:
  """True if a complete UBX-NAV-PVT in dat has gnssFixOK set."""
  pos = dat.find(UBX_NAV_PVT)
  while pos >= 0:
    flags_idx = pos + 6 + 21
    if flags_idx < len(dat) and dat[flags_idx] & 0x01:
      return True
    pos = dat.find(UBX_NAV_PVT, pos + 1)
  return False


class LateAiding:
  """Background poll for a time source while pigeond streams; the result is injected by the main loop.

  Only started when init could not inject time. Stops after the first result, a GNSS fix, or the deadline.
  """
  POLL_S = 2.0
  DEADLINE_S = 300.0

  def __init__(self, last_position_sec: float | None, modem_query=query_modem_time):
    self.last_position_sec = last_position_sec
    self.modem_query = modem_query
    self.result: tuple[datetime.datetime, float, int, str] | None = None  # (time, monotonic at read, acc, source)
    self.done = threading.Event()
    self.thread = threading.Thread(target=self._run, name="gnss-late-aiding", daemon=True)

  def start(self) -> None:
    self.thread.start()

  def stop(self) -> None:
    self.done.set()

  def _run(self) -> None:
    st = time.monotonic()
    try:
      while not self.done.is_set() and time.monotonic() - st < self.DEADLINE_S:
        try:
          res = get_aiding_time(self.modem_query, self.last_position_sec)
        except Exception:
          cloudlog.exception("gnss aiding: late time query failed")
          res = None
        if res is not None:
          self.result = (res[0], time.monotonic(), res[1], res[2])
          return
        self.done.wait(self.POLL_S)
    finally:
      # result (if any) is set before done, so take() never misses it
      self.done.set()

  def take(self) -> tuple[datetime.datetime, int, str] | None:
    """Pop the result, with the time advanced to now."""
    res = self.result
    if res is None:
      return None
    self.result = None
    t, mono, acc, source = res
    return t + datetime.timedelta(seconds=time.monotonic() - mono), acc, source
