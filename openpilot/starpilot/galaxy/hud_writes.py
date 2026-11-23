"""Head-unit writes that only apply at the next car start: steering board (9G TI/SSV3) and openpilot on/off.

Both are params read once when card starts; the endpoints only decide whether a write is allowed now.
Answers (galaxy server.py): 400 bad value, 409 {"error": reason} when the board isn't fitted, 429 when the last
accepted write of the same kind is under WRITE_GAP_S old, else 200 {"applied": "next_start", ...}.
Offroad (IsOffroad == 1, not engaged): the live params are written. Onroad / engaged / IsOffroad unreadable (the comma
reports onroad whenever the car is in accessory): the value is STAGED instead (AccordSteeringBoardPending /
OpenpilotEnabledPending) and the answer carries "staged": true; nothing live changes mid-drive. apply_pending() moves
a staged value to the live params at the next provably-offroad moment (galaxy PendingApplier thread) and clears it.

No lock-out:
- steering board: a board is fitted when card heard it within PRESENT_DAYS (AccordSteeringBoardSeen, kept across
  TI-only and SSV3-only drives), or it is the configured board, the board of the last drive (CarParamsPersistent),
  or the board configured before the last head-unit switch (AccordSteeringBoardPrevious). So switching back is
  always possible.
- openpilot on/off: turning openpilot back ON only needs offroad (no engaged / presence check).
"""
import time

from openpilot.starpilot.car.honda.steering_board_watch import PRESENT_DAYS, SEEN_PARAM, parse_seen, seen_recently

WRITE_GAP_S = 5.0
BOARDS = ('ti', 'ssv3')
PREVIOUS_PARAM = 'AccordSteeringBoardPrevious'
BOARD_PENDING = 'AccordSteeringBoardPending'
ENABLED_PENDING = 'OpenpilotEnabledPending'


def _wall():
  return time.time()


def _is_true(value):
  return value is True or value in (b'1', '1', 1)


def parked_refusal(params, check_engaged=True):
  """None when params prove offroad (IsOffroad == 1) and not engaged, else the 409 reason. Unreadable = refuse."""
  try:
    offroad = params.get('IsOffroad')
  except Exception:
    return 'Could not read IsOffroad'
  if not _is_true(offroad):
    return 'Only while offroad'
  if check_engaged:
    try:
      engaged = params.get('IsEngaged')
    except Exception:
      return 'Could not read IsEngaged'
    if _is_true(engaged):
      return 'openpilot is engaged'
  return None


def configured_board(params):
  """'ti' / 'ssv3' for the next start (TI switch off = SSV3 only; AccordSteeringBoard 'ssv3' forces it), None unreadable."""
  try:
    ti_enabled = params.get_bool('TorqueInterceptorEnabled')
    override = params.get('AccordSteeringBoard')
  except Exception:
    return None
  override = override.decode('ascii', 'replace') if isinstance(override, bytes) else (override or '')
  return 'ti' if ti_enabled and override.strip().lower() != 'ssv3' else 'ssv3'


def last_drive_board(params):
  """Board of the last drive from CarParamsPersistent (TI safety bit), None when unknown / not a 9G / openpilot off."""
  try:
    from opendbc.car.structs import car
    from openpilot.starpilot.galaxy.hud import TI_SAVED_SAFETY_PARAMS, last_drive_car_params_bytes
    raw = last_drive_car_params_bytes(params)   # schema-cache envelope, not raw capnp
    if not raw:
      return None
    with car.CarParams.from_bytes(raw) as cp:
      if str(cp.carFingerprint) != 'HONDA_ACCORD_9G' or cp.passive:
        return None
      return 'ti' if any(str(c.safetyModel) == 'hondaNidec' and int(c.safetyParam) & TI_SAVED_SAFETY_PARAMS for c in cp.safetyConfigs) else 'ssv3'
  except Exception:
    return None


def previous_board(params):
  try:
    raw = params.get(PREVIOUS_PARAM)
  except Exception:
    return None
  raw = raw.decode('ascii', 'replace') if isinstance(raw, bytes) else raw
  return raw if raw in BOARDS else None


def board_refusal(params, board, now=None):
  """None when `board` may be configured now, else the 409 reason (onroad / engaged / not fitted)."""
  reason = parked_refusal(params)
  if reason:
    return reason
  return fitted_refusal(params, board, now)


def fitted_refusal(params, board, now=None):
  """None when `board` is fitted (or is always allowed: configured / last drive / previous), else the 409 reason."""
  if board in (configured_board(params), last_drive_board(params), previous_board(params)):
    return None
  try:
    seen = parse_seen(params.get(SEEN_PARAM))
  except Exception:
    seen = parse_seen(None)
  if seen_recently(seen, board, _wall() if now is None else now):
    return None
  name = 'TI' if board == 'ti' else 'SSV3'
  return f'{name} board not seen in the last {PRESENT_DAYS} days'


def write_board(params, board):
  """TorqueInterceptorEnabled (ssv3 = off = SSV3 only), AccordSteeringBoard=auto, remember the board switched away from."""
  current = configured_board(params)
  if current in BOARDS and current != board:
    params.put(PREVIOUS_PARAM, current)
  params.put_bool('TorqueInterceptorEnabled', board == 'ti')
  params.put('AccordSteeringBoard', 'auto')


def enabled_refusal(params, enabled):
  """openpilot on/off: off needs offroad + not engaged; on (back from datalogger) only needs offroad."""
  return parked_refusal(params, check_engaged=not enabled)


def stage_needed(params, check_engaged=True):
  """True when the write must be staged (not provably offroad / engaged)."""
  return parked_refusal(params, check_engaged=check_engaged) is not None


def _text(value):
  return value.decode('ascii', 'replace') if isinstance(value, bytes) else value


def pending_board(params):
  try:
    value = _text(params.get(BOARD_PENDING))
  except Exception:
    return None
  return value if value in BOARDS else None


def pending_enabled(params):
  try:
    value = _text(params.get(ENABLED_PENDING))
  except Exception:
    return None
  return True if value == '1' else False if value == '0' else None


def stage_board(params, board):
  params.put(BOARD_PENDING, board)


def stage_enabled(params, enabled):
  params.put(ENABLED_PENDING, '1' if enabled else '0')


def clear_pending(params, key):
  try:
    params.remove(key)
  except Exception:
    params.put(key, '')


def apply_pending(params):
  """Move staged values to the live params once provably offroad and not engaged. Returns the list of applied keys."""
  applied = []
  if parked_refusal(params) is not None:
    return applied
  board = pending_board(params)
  if board is not None:
    write_board(params, board)
    clear_pending(params, BOARD_PENDING)
    applied.append(BOARD_PENDING)
  enabled = pending_enabled(params)
  if enabled is not None:
    params.put_bool('OpenpilotEnabledToggle', enabled)
    clear_pending(params, ENABLED_PENDING)
    applied.append(ENABLED_PENDING)
  # anything else left in the keys (garbage) is cleared so it never reads as pending
  for key, valid in ((BOARD_PENDING, board), (ENABLED_PENDING, enabled)):
    if valid is None:
      try:
        if _text(params.get(key)):
          clear_pending(params, key)
      except Exception:
        pass
  return applied


class PendingApplier:
  """Polls apply_pending() so a staged value lands the moment the comma goes offroad (or at boot, if it is offroad)."""
  def __init__(self, params_factory, interval=1.0, log=None):
    self.params_factory = params_factory
    self.interval = interval
    self.log = log
    self.stop = False

  def step(self, lock=None):
    try:
      params = self.params_factory()
      if lock is not None:
        with lock:
          applied = apply_pending(params)
      else:
        applied = apply_pending(params)
      if applied and self.log:
        self.log(f'galaxy: hud staged values applied at offroad: {applied}')
    except Exception:
      pass

  def run(self, lock=None):
    while not self.stop:
      self.step(lock)
      time.sleep(self.interval)


class RateLimit:
  """At most one accepted write per WRITE_GAP_S; refused requests don't count."""
  def __init__(self, clock=time.monotonic, gap=None):
    self.clock = clock
    self.gap = WRITE_GAP_S if gap is None else gap
    self.last = None

  def blocked(self):
    return self.last is not None and self.clock() - self.last < self.gap

  def mark(self):
    self.last = self.clock()
