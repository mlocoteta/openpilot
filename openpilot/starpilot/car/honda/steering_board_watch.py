"""card.py side of the 9G steering boards (opendbc/car/honda/steering_board.py).

SteeringBoardWatch (TI drives only): when the TI never answers while the SSV3 reports
(CarState.ti_presence.missing), write TorqueInterceptorMissing=1 once, so the next start uses the SSV3. When the TI
does answer, clear a stale record once. Each param write happens at most once per drive.

BoardSeenRecorder (every 9G drive, also with openpilot disabled): the persistent "ever seen" record behind the
head unit's steering-board switch (galaxy POST /api/hud/steeringBoard refuses a board that is not fitted).
AccordSteeringBoardSeen = {"ti": epoch s | null, "ssv3": epoch s | null, "ssv3Firmware": int | null}, the last
time each board was heard on bus 0. A board's entry is only ever moved forward, never cleared: an SSV3-only drive
can't hear the TI (it only talks once openpilot commands it), so it must not erase the TI's record (lock-out).
  TI    TI_FEEDBACK 0x24A on bus 0 (raw scan) or CS.ti.feedback_seen on a TI drive
  SSV3  STEER_STATUS 0x190 (5 B) / SS_STATUS 0x208 (3 B) on bus 0; firmware = SS_STATUS byte 0 low nibble
The raw scan runs for SCAN_FRAMES card frames per drive (both boards report within the first second when they
talk at all), then only the cheap CS.ti check stays. One write per board per drive, once the wall clock is valid.
"""
import json
import time

from openpilot.common.swaglog import cloudlog

PARAM = "TorqueInterceptorMissing"
SEEN_PARAM = "AccordSteeringBoardSeen"

TI_FEEDBACK_ADDR = 0x24A
SSV3_STATUS = ((0x190, 5), (0x208, 3))
SSV3_VERSION_ADDR = 0x208
SCAN_FRAMES = 1000                        # 10 s of 100 Hz card frames
VALID_EPOCH = (1740096000, 2051222400)    # 2025-02-21 .. 2035-01-01 (common/time_helpers MIN_DATE / MAX_DATE)
PRESENT_DAYS = 30


class SteeringBoardWatch:
  def __init__(self, car_state, params):
    self.cs = car_state
    self.params = params
    self.recorded = False
    self.cleared = False

  def update(self) -> None:
    presence = self.cs.ti_presence
    if presence.missing and not self.recorded:
      self.recorded = True
      try:
        self.params.put_bool(PARAM, True)   # block=False = queued write (7.0 Params)
      except Exception:
        cloudlog.exception("steering_board_watch: could not record TorqueInterceptorMissing")
      cloudlog.event("accord_ti_missing", frames=presence.frames, status_frames=presence.status_frames)
    elif self.cs.ti.feedback_seen and not self.cleared:
      self.cleared = True
      try:
        if self.params.get_bool(PARAM):
          self.params.put_bool(PARAM, False)
          cloudlog.event("accord_ti_missing_cleared")
      except Exception:
        cloudlog.exception("steering_board_watch: could not clear TorqueInterceptorMissing")


def install(CI, params):
  cs = getattr(CI, "CS", None)
  if getattr(cs, "ti_presence", None) is None or getattr(cs, "ti", None) is None:
    return None
  return SteeringBoardWatch(cs, params)


# ---- persistent board record ------------------------------------------------------------------------------------

def valid_epoch(t) -> bool:
  return isinstance(t, (int, float)) and not isinstance(t, bool) and VALID_EPOCH[0] < t < VALID_EPOCH[1]


def parse_seen(raw) -> dict:
  """AccordSteeringBoardSeen -> {"ti": int|None, "ssv3": int|None, "ssv3Firmware": int|None}; garbage -> all None."""
  out = {"ti": None, "ssv3": None, "ssv3Firmware": None}
  try:
    if isinstance(raw, bytes):
      raw = raw.decode()
    data = json.loads(raw) if isinstance(raw, str) else raw
  except (ValueError, UnicodeDecodeError):
    return out
  if not isinstance(data, dict):
    return out
  for key in ("ti", "ssv3"):
    if valid_epoch(data.get(key)):
      out[key] = int(data[key])
  fw = data.get("ssv3Firmware")
  if isinstance(fw, int) and not isinstance(fw, bool) and 0 <= fw <= 15:
    out["ssv3Firmware"] = fw
  return out


def seen_recently(seen: dict, board: str, now: float, days: int = PRESENT_DAYS) -> bool:
  """Board heard within `days` of now. An invalid wall clock (no time sync yet) accepts any record."""
  t = (seen or {}).get(board)
  if t is None:
    return False
  if not valid_epoch(now):
    return True
  return now - t <= days * 86400


def raw_board_frames(can_list):
  """(TI_FEEDBACK seen, SSV3 frame seen, newest SS_STATUS.VERSION_NUM or None) over card's can_list on bus 0."""
  ti = ssv3 = False
  version = None
  for _, frames in can_list:
    for addr, dat, src in frames:
      if src != 0:
        continue
      if addr == TI_FEEDBACK_ADDR:
        ti = True
      elif (addr, len(dat)) in SSV3_STATUS:
        ssv3 = True
        if addr == SSV3_VERSION_ADDR:
          version = dat[0] & 0x0F
  return ti, ssv3, version


class BoardSeenRecorder:
  def __init__(self, car_state, params, clock=time.time):
    self.cs = car_state
    self.params = params
    self.clock = clock
    self.frames = 0
    self.heard = {"ti": False, "ssv3": False}
    self.version = None
    self.written = {"ti": False, "ssv3": False}
    self.written_version = None

  def update(self, can_list) -> None:
    self.frames += 1
    if self.frames <= SCAN_FRAMES and not (self.heard["ti"] and self.heard["ssv3"] and self.version is not None):
      ti, ssv3, version = raw_board_frames(can_list)
      self.heard["ti"] |= ti
      self.heard["ssv3"] |= ssv3
      if version is not None:
        self.version = version
    cs_ti = getattr(self.cs, "ti", None)
    if cs_ti is not None and getattr(cs_ti, "feedback_seen", False):
      self.heard["ti"] = True
    pending = [b for b in ("ti", "ssv3") if self.heard[b] and not self.written[b]]
    if self.heard["ssv3"] and self.version is not None and self.version != self.written_version and "ssv3" not in pending:
      pending.append("ssv3")
    if pending:
      self._write(pending)

  def _write(self, boards) -> None:
    now = self.clock()
    if not valid_epoch(now):
      return   # retried next frame; the wall clock syncs soon after start
    try:
      record = parse_seen(self.params.get(SEEN_PARAM))
      for board in boards:
        record[board] = max(int(now), record[board] or 0)
        self.written[board] = True
      if "ssv3" in boards and self.version is not None:
        record["ssv3Firmware"] = self.version
        self.written_version = self.version
      self.params.put(SEEN_PARAM, dict(record))   # queued write
      cloudlog.event("accord_steering_board_seen", boards=boards, record=record)
    except Exception:
      for board in boards:
        self.written[board] = True   # never retry every frame
      self.written_version = self.version
      cloudlog.exception("steering_board_watch: could not write AccordSteeringBoardSeen")


def install_seen(CP, CI, params):
  """Every 9G Accord drive (TI, SSV3 or openpilot disabled)."""
  if getattr(CP, "carFingerprint", None) != "HONDA_ACCORD_9G":
    return None
  return BoardSeenRecorder(getattr(CI, "CS", None), params)
