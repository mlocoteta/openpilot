#!/usr/bin/env python3
import sys
import termios
import time
import signal
import struct
import threading
import requests
import urllib.parse
from datetime import datetime, UTC

from openpilot.cereal import log, messaging
from openpilot.common.api import Api
from openpilot.common.time_helpers import system_time_valid
from openpilot.common.params import Params
from openpilot.common.serial import Serial
from openpilot.common.swaglog import cloudlog
from openpilot.common.hardware import COMMA_HARDWARE
from openpilot.common.gpio import gpio_init, gpio_set
from openpilot.common.hardware.comma.pins import GPIO

UBLOX_TTY = "/dev/ttyHS0"

UBLOX_ACK = b"\xb5\x62\x05\x01\x02\x00"
UBLOX_NACK = b"\xb5\x62\x05\x00\x02\x00"
UBLOX_SOS_ACK = b"\xb5\x62\x09\x14\x08\x00\x02\x00\x00\x00\x01\x00\x00\x00"
UBLOX_SOS_NACK = b"\xb5\x62\x09\x14\x08\x00\x02\x00\x00\x00\x00\x00\x00\x00"
UBLOX_BACKUP_RESTORE_MSG = b"\xb5\x62\x09\x14\x08\x00\x03"
UBLOX_ASSIST_ACK = b"\xb5\x62\x13\x60\x08\x00"

# Accord port (2026-11-02): a failing AssistNow download retried every 10 s on Wi-Fi lined up with "received invalid
# data from ublox" -> init() -> a u-blox power cycle (117 of 118 multi-minute GPS outages). One stray 0x00 (a UART
# overrun/break byte, copied verbatim by the real-raw tty) no longer power-cycles the receiver: only a ublox that sent
# no valid UBX frame for UBLOX_DEAD_TIMEOUT s does. AssistNow skips while there is a fix and backs off after failures.
UBLOX_DEAD_TIMEOUT = 5.0  # s without a valid UBX frame before re-initing (it outputs several frames per second)
ASSIST_RETRY_MIN = 10.  # s, first retry after a failed AssistNow download (upstream retried every 10 s forever)
ASSIST_RETRY_MAX = 600.  # s, backoff cap
FIX_MAX_AGE = 2.  # s, a gpsLocationExternal fix this fresh means AssistNow has nothing to add

def set_power(enabled: bool) -> None:
  gpio_init(GPIO.UBLOX_SAFEBOOT_N, True)
  gpio_init(GPIO.GNSS_PWR_EN, True)
  gpio_init(GPIO.UBLOX_RST_N, True)

  gpio_set(GPIO.UBLOX_SAFEBOOT_N, True)
  gpio_set(GPIO.GNSS_PWR_EN, enabled)
  gpio_set(GPIO.UBLOX_RST_N, enabled)

def add_ubx_checksum(msg: bytes) -> bytes:
  A = B = 0
  for b in msg[2:]:
    A = (A + b) % 256
    B = (B + A) % 256
  return msg + bytes([A, B])

def get_assistnow_messages() -> list[bytes]:
  params = Params()
  if token := params.get('AssistNowToken'):
    cloudlog.warning("Downloading AssistNow data directly from u-blox")
    r = requests.get("https://online-live2.services.u-blox.com/GetOnlineData.ashx", params=urllib.parse.urlencode({
      'token': token,
      'gnss': 'gps,glo',
      'datatype': 'eph,alm,aux',
    }, safe=':,'), timeout=5)
  elif dongle_id := params.get('DongleId'):
    cloudlog.warning("Downloading AssistNow data from comma's AGPS proxy")
    api = Api(dongle_id)
    r = api.get(f"v1/{dongle_id}/assist", access_token=api.get_token(), timeout=5)
  else:
    raise RuntimeError("Neither AssistNowToken nor DongleId is configured")

  r.raise_for_status()
  dat = r.content

  # split up messages
  msgs = []
  while len(dat) > 0:
    assert dat[:2] == b"\xB5\x62"
    msg_len = 6 + (dat[5] << 8 | dat[4]) + 2
    # Skip MGA-INI messages; time from proxyserver is a stale cache
    if dat[2:4] != b"\x13\x40":
      msgs.append(dat[:msg_len])
    dat = dat[msg_len:]
  return msgs


def ubx_frame_ends(dat: bytes) -> tuple[int, int]:
  """Scan dat for UBX frames with a valid checksum. Returns (valid frame count, offset where unscanned data starts):
  the start of a trailing frame that isn't complete yet, else len(dat)."""
  count = 0
  i = dat.find(b"\xB5\x62")
  while i >= 0:
    if len(dat) < i + 6:
      return count, i
    end = i + 6 + (dat[i + 4] | dat[i + 5] << 8) + 2
    if end > len(dat):
      return count, i
    if add_ubx_checksum(dat[i:end - 2]) == dat[i:end]:
      count += 1
      i = dat.find(b"\xB5\x62", end)
    else:
      i = dat.find(b"\xB5\x62", i + 1)
  return count, len(dat)


class UbxWatchdog:
  """Tracks the last valid UBX frame; the receiver counts as dead only after `timeout` s without one."""
  def __init__(self, now: float, timeout: float = UBLOX_DEAD_TIMEOUT):
    self.timeout = timeout
    self.tail = b''
    self.last_valid = now

  def reset(self, now: float) -> None:
    self.tail = b''
    self.last_valid = now

  def feed(self, dat: bytes, now: float) -> None:
    buf = self.tail + dat
    count, rest = ubx_frame_ends(buf)
    if count:
      self.last_valid = now
    self.tail = buf[rest:][-0x2000:]

  def dead(self, now: float) -> bool:
    return now - self.last_valid > self.timeout


class AssistBackoff:
  """When the next AssistNow download may run: right away at first, then exponential backoff after failures."""
  def __init__(self, base: float = ASSIST_RETRY_MIN, cap: float = ASSIST_RETRY_MAX):
    self.base, self.cap = base, cap
    self.failures = 0
    self.next_at = 0.

  def due(self, now: float) -> bool:
    return now >= self.next_at

  def failed(self, now: float) -> float:
    delay = min(self.cap, self.base * 2 ** self.failures)
    self.failures += 1
    self.next_at = now + delay
    return delay


def has_recent_fix(sm, now: float) -> bool:
  return bool(sm.seen['gpsLocationExternal'] and now - sm.recv_time['gpsLocationExternal'] < FIX_MAX_AGE and
              sm['gpsLocationExternal'].hasFix)


def ignore_line_errors(tty: Serial) -> None:
  # IGNBRK|IGNPAR: drop break and parity/framing-error bytes instead of reading them as 0x00. Serial reconfigures
  # iflag to 0 on every baud change, so this is re-applied after each one. On drivers whose tty runs real-raw
  # (serial core) the line discipline copies flagged bytes anyway; UbxWatchdog is the protection that matters.
  try:
    attrs = termios.tcgetattr(tty.fd)
    attrs[0] |= termios.IGNBRK | termios.IGNPAR
    termios.tcsetattr(tty.fd, termios.TCSANOW, attrs)
  except (termios.error, OSError):
    cloudlog.exception("pigeond: could not set IGNBRK|IGNPAR")


class TTYPigeon:
  def __init__(self):
    self.tty = Serial(UBLOX_TTY, baudrate=9600, timeout=0)
    ignore_line_errors(self.tty)

  def send(self, dat: bytes) -> None:
    self.tty.write(dat)

  def receive(self) -> bytes:
    dat = b''
    while len(dat) < 0x1000:
      d = self.tty.read(0x40)
      dat += d
      if len(d) == 0:
        break
    return dat

  def set_baud(self, baud: int) -> None:
    self.tty.baudrate = baud
    ignore_line_errors(self.tty)

  def wait_for_ack(self, ack: bytes = UBLOX_ACK, nack: bytes = UBLOX_NACK, timeout: float = 0.5) -> bool:
    dat = b''
    st = time.monotonic()
    while True:
      dat += self.receive()
      if ack in dat:
        cloudlog.debug("Received ACK from ublox")
        return True
      elif nack in dat:
        cloudlog.error("Received NACK from ublox")
        return False
      elif time.monotonic() - st > timeout:
        cloudlog.error("No response from ublox")
        raise TimeoutError('No response from ublox')
      time.sleep(0.001)

  def send_with_ack(self, dat: bytes, ack: bytes = UBLOX_ACK, nack: bytes = UBLOX_NACK) -> None:
    self.send(dat)
    self.wait_for_ack(ack, nack)

  def wait_for_backup_restore_status(self, timeout: float = 1.) -> int:
    dat = b''
    st = time.monotonic()
    while True:
      dat += self.receive()
      position = dat.find(UBLOX_BACKUP_RESTORE_MSG)
      if position >= 0 and len(dat) >= position + 11:
        return dat[position + 10]
      elif time.monotonic() - st > timeout:
        cloudlog.error("No backup restore response from ublox")
        raise TimeoutError('No response from ublox')
      time.sleep(0.001)

  def reset_device(self) -> bool:
    # deleting the backup does not always work on first try (mostly on second try)
    for _ in range(5):
      # device cold start
      self.send(b"\xb5\x62\x06\x04\x04\x00\xff\xff\x00\x00\x0c\x5d")
      time.sleep(1) # wait for cold start
      init_baudrate(self)

      # clear configuration
      self.send_with_ack(b"\xb5\x62\x06\x09\x0d\x00\x1f\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x17\x71\xd7")

      # clear flash memory (almanac backup)
      self.send_with_ack(b"\xB5\x62\x09\x14\x04\x00\x01\x00\x00\x00\x22\xf0")

      # try restoring backup to verify it got deleted
      self.send(b"\xB5\x62\x09\x14\x00\x00\x1D\x60")
      # 1: failed to restore, 2: could restore, 3: no backup
      status = self.wait_for_backup_restore_status()
      if status == 1 or status == 3:
        return True
    return False

def send_time(pigeon: TTYPigeon) -> None:
  if not system_time_valid():
    return

  cloudlog.warning("Sending current time to ublox")

  # UBX-MGA-INI-TIME_UTC
  t_now = datetime.now(UTC).replace(tzinfo=None)
  msg = add_ubx_checksum(b"\xB5\x62\x13\x40\x18\x00" + struct.pack("<BBBBHBBBBBxIHxxI",
    0x10,
    0x00,
    0x00,
    0x80,
    t_now.year,
    t_now.month,
    t_now.day,
    t_now.hour,
    t_now.minute,
    t_now.second,
    t_now.microsecond * 1000,
    30,
    0
  ))
  pigeon.send_with_ack(msg, ack=UBLOX_ASSIST_ACK)

def save_almanac(pigeon: TTYPigeon) -> None:
  # store almanac in flash
  pigeon.send(b"\xB5\x62\x09\x14\x04\x00\x00\x00\x00\x00\x21\xEC")
  try:
    if pigeon.wait_for_ack(ack=UBLOX_SOS_ACK, nack=UBLOX_SOS_NACK):
      cloudlog.info("Done storing almanac")
    else:
      cloudlog.error("Error storing almanac")
  except TimeoutError:
    pass

def init_baudrate(pigeon: TTYPigeon):
  # ublox default setting on startup is 9600 baudrate
  pigeon.set_baud(9600)

  # $PUBX,41,1,0007,0003,460800,0*15\r\n
  pigeon.send(b"\x24\x50\x55\x42\x58\x2C\x34\x31\x2C\x31\x2C\x30\x30\x30\x37\x2C\x30\x30\x30\x33\x2C\x34\x36\x30\x38\x30\x30\x2C\x30\x2A\x31\x35\x0D\x0A")
  time.sleep(0.1)
  pigeon.set_baud(460800)


def send_position(pigeon: TTYPigeon) -> None:
  if not (position := Params().get("LastGPSPosition")):
    return

  if not isinstance(position, bytes):
    return  # Older STRING cache is not a serialized GPS Event.
  with log.Event.from_bytes(position) as evt:
    gps = evt.gpsLocationExternal
    if datetime.now(UTC).timestamp() - gps.unixTimestampMillis / 1000 > 7 * 24 * 3600:
      return
    cloudlog.warning("Sending last position to ublox")

    # UBX-MGA-INI-POS_LLH
    msg = add_ubx_checksum(b"\xB5\x62\x13\x40\x14\x00" + struct.pack("<BB2xiiiI",
      0x01, 0x00,
      round(gps.latitude * 1e7),
      round(gps.longitude * 1e7),
      round(gps.altitude * 100),
      100_000 * 100,
    ))
  pigeon.send_with_ack(msg, ack=UBLOX_ASSIST_ACK)


def init_pigeon(pigeon: TTYPigeon) -> bool:
  # try initializing a few times
  for _ in range(10):
    try:

      # setup port config
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x14\x00\x03\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x1E\x7F")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x14\x00\x00\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x19\x35")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x14\x00\x01\x00\x00\x00\xC0\x08\x00\x00\x00\x08\x07\x00\x01\x00\x01\x00\x00\x00\x00\x00\xF4\x80")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x14\x00\x04\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1D\x85")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x00\x00\x06\x18")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x01\x00\x01\x08\x22")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x01\x00\x03\x0A\x24")

      # UBX-CFG-RATE (0x06 0x08)
      pigeon.send_with_ack(b"\xB5\x62\x06\x08\x06\x00\x64\x00\x01\x00\x00\x00\x79\x10")

      # UBX-CFG-NAV5 (0x06 0x24)
      pigeon.send_with_ack(b"\xB5\x62\x06\x24\x24\x00\x07\x00\x04\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x5C\xAB")

      # UBX-CFG-ODO (0x06 0x1E)
      pigeon.send_with_ack(b"\xB5\x62\x06\x1E\x14\x00\x00\x00\x00\x00\x01\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3C\x37")
      pigeon.send_with_ack(b"\xB5\x62\x06\x39\x08\x00\xFF\xAD\x62\xAD\x1E\x63\x00\x00\x83\x0C")
      pigeon.send_with_ack(b"\xB5\x62\x06\x23\x28\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x24")

      # UBX-CFG-NAV5 (0x06 0x24)
      pigeon.send_with_ack(b"\xB5\x62\x06\x24\x00\x00\x2A\x84")
      pigeon.send_with_ack(b"\xB5\x62\x06\x23\x00\x00\x29\x81")
      pigeon.send_with_ack(b"\xB5\x62\x06\x1E\x00\x00\x24\x72")
      pigeon.send_with_ack(b"\xB5\x62\x06\x39\x00\x00\x3F\xC3")

      # UBX-CFG-MSG (set message rate)
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x01\x07\x01\x13\x51")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x02\x15\x01\x22\x70")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x02\x13\x01\x20\x6C")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x0A\x09\x01\x1E\x70")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x0A\x0B\x01\x20\x74")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x01\x35\x01\x41\xAD")
      cloudlog.debug("pigeon configured")

      # try restoring almanac backup
      pigeon.send(b"\xB5\x62\x09\x14\x00\x00\x1D\x60")
      restore_status = pigeon.wait_for_backup_restore_status()
      if restore_status == 2:
        cloudlog.warning("almanac backup restored")
      elif restore_status == 3:
        cloudlog.warning("no almanac backup found")
      else:
        cloudlog.error(f"failed to restore almanac backup, status: {restore_status}")

      cloudlog.warning("Pigeon GPS on!")
      break
    except TimeoutError:
      cloudlog.warning("Initialization failed, trying again!")
  else:
    cloudlog.warning("Failed to initialize pigeon")
    return False
  return True

def deinitialize_and_exit(pigeon: TTYPigeon | None):
  if pigeon is not None:
    # controlled GNSS stop
    pigeon.send(b"\xB5\x62\x06\x04\x04\x00\x00\x00\x08\x00\x16\x74")

  # turn off power and exit cleanly
  set_power(False)
  sys.exit(0)

def init(pigeon: TTYPigeon) -> None:
  # register exit handler
  signal.signal(signal.SIGINT, lambda sig, frame: deinitialize_and_exit(pigeon))

  # power cycle ublox
  set_power(False)
  time.sleep(0.1)
  set_power(True)
  time.sleep(0.5)

  init_baudrate(pigeon)
  init_pigeon(pigeon)

  if system_time_valid():
    try:
      send_time(pigeon)
      send_position(pigeon)
    except Exception:
      cloudlog.exception("failed to send time and position to ublox")

def run_receiving(duration: int = 0):
  pm = messaging.PubMaster(['ubloxRaw'])

  pigeon = TTYPigeon()
  init(pigeon)

  start_time = time.monotonic()
  last_almanac_save = time.monotonic()
  watchdog = UbxWatchdog(time.monotonic())
  assist_attempted = False
  assist_messages = None

  def download_assistnow() -> None:
    nonlocal assist_messages
    sm = messaging.SubMaster(['deviceState', 'gpsLocationExternal'])
    backoff = AssistBackoff()
    while assist_messages is None:
      sm.update(1000)
      now = time.monotonic()
      if not backoff.due(now) or has_recent_fix(sm, now):
        continue
      if system_time_valid() and sm['deviceState'].networkType != log.DeviceState.NetworkType.none:
        try:
          assist_messages = get_assistnow_messages()
        except Exception:
          delay = backoff.failed(now)
          cloudlog.warning(f"failed to get AssistNow messages, next try in {delay:.0f} s")
  threading.Thread(target=download_assistnow, daemon=True).start()

  while (duration == 0) or (time.monotonic() - start_time < duration):
    if assist_messages is not None and not assist_attempted:
      assist_attempted = True
      try:
        for msg in assist_messages:
          pigeon.send_with_ack(msg, ack=UBLOX_ASSIST_ACK)
        send_time(pigeon)
        cloudlog.warning("AssistNow messages sent")
      except Exception:
        cloudlog.warning("failed to send AssistNow messages")
      watchdog.reset(time.monotonic())  # the ACK waits consumed the receiver's output

    dat = pigeon.receive()
    now = time.monotonic()
    watchdog.feed(dat, now)
    if watchdog.dead(now):
      cloudlog.warning(f"no valid data from ublox for {UBLOX_DEAD_TIMEOUT:.0f} s, re-initing!")
      init(pigeon)
      watchdog.reset(time.monotonic())
      assist_attempted = False
      continue

    dat = dat.lstrip(b"\x00")  # stray overrun/break bytes; ubloxd resyncs on the UBX header
    if len(dat) > 0:
      # send out to socket
      msg = messaging.new_message('ubloxRaw', len(dat), valid=True)
      msg.ubloxRaw = dat[:]
      pm.send('ubloxRaw', msg)

      # save almanac every 5 minutes
      if (time.monotonic() - last_almanac_save) > 60*5:
        save_almanac(pigeon)
        last_almanac_save = time.monotonic()
        watchdog.reset(time.monotonic())
    else:
      # prevent locking up a CPU core if ublox disconnects
      time.sleep(0.001)


def main():
  assert COMMA_HARDWARE, "unsupported hardware for pigeond"
  run_receiving()

if __name__ == "__main__":
  main()
