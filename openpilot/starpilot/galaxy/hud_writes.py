"""Head-unit writes: steering board (9G TI/SSV3, switched while the car is on) and openpilot on/off (next start).

Answers (galaxy server.py): 400 bad value, 409 {"error": reason} when the board isn't fitted, 429 when the last
accepted write of the same kind is under WRITE_GAP_S old.

Steering board (2026-11-17 on-the-fly switch, starpilot/car/honda/board_switch.py):
- provably offroad (IsOffroad == 1, not engaged): the live params are written, 200 {"applied": "now"} (used at start).
- otherwise the request goes to the running card (AccordSteeringBoardSwitch) and galaxy waits up to SWITCH_WAIT_S for
  its answer: 200 {"applied": "now"} = switched (card restarts openpilot, ~10 s, no ignition cycle), or
  409 {"applied": "refused", "reason", "error"} = engaged / latActive / moving / openpilot still starting.
  No answer (card not running yet) = STAGED (AccordSteeringBoardPending), 200 {"applied": "after_disengage",
  "staged": true}: card applies it when it starts, or at the next stop with openpilot off; galaxy's PendingApplier
  applies it at offroad.
openpilot on/off: params read once when card starts. Offroad: written live; onroad / engaged / unreadable: staged
(OpenpilotEnabledPending), applied at the next offroad; answer {"applied": "next_start"[, "staged": true]}.

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


def write_board(params, board, block=False):
  """TorqueInterceptorEnabled (ssv3 = off = SSV3 only), AccordSteeringBoard=auto, remember the board switched away from."""
  current = configured_board(params)
  if current in BOARDS and current != board:
    params.put(PREVIOUS_PARAM, current, block=block)
  params.put_bool('TorqueInterceptorEnabled', board == 'ti', block=block)
  params.put('AccordSteeringBoard', 'auto', block=block)


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


SWITCH_WAIT_S = 3.5        # card: REQUEST_TIMEOUT_S 2.5 + 10 Hz poll + margin; under the head unit's 5 s HTTP read timeout
SWITCH_POLL_S = 0.05


def request_switch(params, board, request_id):
  """Hand a live board switch to the running card (board_switch.BoardSwitch)."""
  from openpilot.starpilot.car.honda.board_switch import RESULT_PARAM, SWITCH_PARAM
  try:
    params.remove(RESULT_PARAM)
  except Exception:
    pass
  params.put(SWITCH_PARAM, {'board': board, 'id': request_id}, block=True)


def await_switch(params_factory, request_id, timeout=None, clock=time.monotonic, sleep=time.sleep):
  """card's answer {'applied', 'reason', ...} to request_id, or None when no card answered within timeout."""
  from openpilot.starpilot.car.honda.board_switch import read_result
  timeout = SWITCH_WAIT_S if timeout is None else timeout
  end = clock() + timeout
  while True:
    try:
      result = read_result(params_factory())
    except Exception:
      result = None
    if result is not None and result.get('id') == request_id and result.get('applied') in ('now', 'refused'):
      return result
    if clock() >= end:
      return None
    sleep(SWITCH_POLL_S)


def withdraw_switch(params, board, request_id):
  """No card answer: take the request back and stage it. Returns card's answer instead if it arrived meanwhile."""
  from openpilot.starpilot.car.honda.board_switch import SWITCH_PARAM, read_request, read_result
  result = read_result(params)
  if result is not None and result.get('id') == request_id and result.get('applied') in ('now', 'refused'):
    return result
  request = read_request(params)
  if request is not None and request.get('id') == request_id:
    try:
      params.remove(SWITCH_PARAM)
    except Exception:
      params.put(SWITCH_PARAM, '')
  stage_board(params, board)
  return None


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
