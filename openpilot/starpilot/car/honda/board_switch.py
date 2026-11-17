"""9G Accord: switch the steering board (TI <-> SSV3) while the car is on, without an ignition cycle.

The board decides CarParams (TI safety bit, TI tune vs SSV3 tune: torque_interceptor.apply_torque_interceptor),
the panda safety param, the car controller path and the torqued / lagd basis. All of them are fixed when card
starts (VehicleStartupPreferences.prepare), and none of them may change under a running card. So a switch is:

  1. card (this module) proves the car is safe to re-init: openpilot NOT engaged, NOT latActive and the car
     stopped (|vEgo| and |vEgoRaw| <= STOP_SPEED), all three continuously for DWELL_S;
  2. it writes the board params (hud_writes.write_board: TorqueInterceptorEnabled, AccordSteeringBoard=auto,
     AccordSteeringBoardPrevious), clears the requests, records the answer, and only then sets
     OnroadCycleRequested (upstream's settings path: hardwared drops `started` for ONROAD_CYCLE_TIME);
  3. from that frame until the processes stop, the published carState says cruise main off + steering
     temporarily unavailable (selfdrived: wrongCarMode / steerTempUnavailable NO_ENTRY; controlsd: no latActive),
     so nothing can engage between the decision and the restart;
  4. manager stops every onroad process; pandad leaves onroad (safety -> noOutput / ELM327, safety_configured_
     reset), then starts them again: card fingerprints, prepare() builds the NEW board's CarParams from the
     params, pandad sets the matching safety param from those CarParams, controlsd / torqued / lagd start on
     them. CarParamsPrevRoute = the other board's CarParams, so torqued's restore key and lagd's
     _tune_basis_changed see a different basis and start fresh: no learned value crosses boards.

Nothing is mutated live: there is never a moment where the panda, the tune and the board disagree inside one
card process. No option bits are involved (the TI path is the unchanged startup path).

Requests (both handled only by a running card, here):
  AccordSteeringBoardSwitch   {"board", "id"} from galaxy POST /api/hud/steeringBoard (head unit). Answered in
                              AccordSteeringBoardSwitchResult {"id", "board", "applied", "reason"} with
                              applied "now" or "refused". Refused at once while engaged / latActive / moving
                              (never queued behind an engagement); waits up to REQUEST_TIMEOUT_S for the dwell.
  AccordSteeringBoardPending  a staged value (older galaxy, or galaxy when card was not running). Applied at card
                              start before CarParams exist (consume_at_start), else at the next moment the gate
                              holds for DWELL_S (no time-out), else at offroad (galaxy PendingApplier).
"""
import time
import uuid

from openpilot.common.swaglog import cloudlog
from openpilot.starpilot.galaxy.hud_writes import (BOARDS, BOARD_PENDING, clear_pending, configured_board, pending_board,
                                                   write_board)

SWITCH_PARAM = 'AccordSteeringBoardSwitch'
RESULT_PARAM = 'AccordSteeringBoardSwitchResult'
CYCLE_PARAM = 'OnroadCycleRequested'

DWELL_S = 1.0              # disengaged + not latActive + stopped, continuously
STOP_SPEED = 0.1           # m/s
REQUEST_TIMEOUT_S = 2.5    # a head-unit request that never reaches the dwell is refused (galaxy waits SWITCH_WAIT_S)
POLL_FRAMES = 10           # params read at 10 Hz from the 100 Hz card loop
UNBLOCK_S = 15.0           # hardwared never cycled: stop blocking engagement (the running CarParams are unchanged)

APPLIED_NOW = 'now'
APPLIED_REFUSED = 'refused'
APPLIED_AFTER_DISENGAGE = 'after_disengage'

REFUSE_ENGAGED = 'Disengage first'
REFUSE_LAT = 'Turn steering off first'
REFUSE_MOVING = 'Stop the car first'
REFUSE_UNKNOWN = 'Still starting, try again'
REFUSE_DWELL = 'Wait a moment, try again'


def running_board(CP):
  """Board of THIS card's CarParams ('ti' / 'ssv3'), None when not a 9G or passive (datalogger: nothing steers)."""
  try:
    if str(CP.carFingerprint) != 'HONDA_ACCORD_9G' or CP.passive:
      return None
    from opendbc.car.honda.torque_interceptor import ti_qualified
    return 'ti' if ti_qualified(CP) else 'ssv3'
  except Exception:
    return None


def new_request_id():
  return uuid.uuid4().hex[:12]


def _text(value):
  return value.decode('ascii', 'replace') if isinstance(value, bytes) else value


def read_request(params):
  """{'board', 'id'} or None. Garbage reads as None."""
  try:
    raw = params.get(SWITCH_PARAM)
  except Exception:
    return None
  if isinstance(raw, (bytes, str)):
    try:
      import json
      raw = json.loads(_text(raw))
    except ValueError:
      return None
  if not isinstance(raw, dict) or raw.get('board') not in BOARDS:
    return None
  rid = raw.get('id')
  return {'board': raw['board'], 'id': rid if isinstance(rid, str) else None}


def read_result(params):
  try:
    raw = params.get(RESULT_PARAM)
  except Exception:
    return None
  if isinstance(raw, (bytes, str)):
    try:
      import json
      raw = json.loads(_text(raw))
    except ValueError:
      return None
  return raw if isinstance(raw, dict) else None


def _remove(params, key):
  try:
    params.remove(key)
  except Exception:
    pass


def _result(params, rid, board, applied, reason):
  try:
    params.put(RESULT_PARAM, {'id': rid, 'board': board, 'applied': applied, 'reason': reason}, block=True)
  except Exception:
    cloudlog.exception('board_switch: could not write the result')


def consume_at_start(params):
  """card start, before VehicleStartupPreferences.read(): a staged board or an unanswered head-unit request becomes
  the live board for THIS start (nothing is running yet, so nothing can disagree). Returns the board or None."""
  board = None
  try:
    request = read_request(params)
    staged = pending_board(params)
    board = request['board'] if request is not None else staged
    if board is None:
      return None
    write_board(params, board, block=True)
    if staged is not None:
      clear_pending(params, BOARD_PENDING)
    if request is not None:
      _remove(params, SWITCH_PARAM)
      _result(params, request['id'], board, APPLIED_NOW, 'applied as openpilot started')
    cloudlog.event('accord_board_switch_at_start', board=board, request=request is not None, staged=staged)
  except Exception:
    cloudlog.exception('board_switch: could not apply the staged board at start')
  return board


class BoardSwitch:
  def __init__(self, CP, params, clock=time.monotonic):
    self.params = params
    self.clock = clock
    self.board = running_board(CP)
    self.passive = bool(getattr(CP, 'passive', False))
    self.frame = 0
    self.quiet_since = None
    self.request_since = {}
    self.committed_at = None
    self.committed_board = None

  # ---- gate ------------------------------------------------------------------------------------------------------
  def _state(self, CS, CC, cc_alive):
    """(hard refusal reason or None, gate open now). Unknown openpilot state is not a hard refusal (startup)."""
    moving = max(abs(float(getattr(CS, 'vEgo', 0.0) or 0.0)), abs(float(getattr(CS, 'vEgoRaw', 0.0) or 0.0))) > STOP_SPEED
    if self.passive:
      return (REFUSE_MOVING if moving else None), not moving
    if CC is not None and bool(getattr(CC, 'enabled', False)):
      return REFUSE_ENGAGED, False
    if CC is not None and bool(getattr(CC, 'latActive', False)):
      return REFUSE_LAT, False
    if moving:
      return REFUSE_MOVING, False
    return None, bool(cc_alive and CC is not None)

  @property
  def blocking(self):
    return self.committed_at is not None and self.clock() - self.committed_at < UNBLOCK_S

  def update(self, CS, CC, cc_alive=True) -> bool:
    """Every card frame (100 Hz). True = a switch is committed: block engagement until the processes stop."""
    now = self.clock()
    if self.committed_at is not None:
      if not self.blocking and self.committed_board is not None:
        cloudlog.error('board_switch: no onroad cycle after the switch; engagement unblocked on the old board')
        self.committed_board = None
      return self.blocking
    hard, open_now = self._state(CS, CC, cc_alive)
    if open_now:
      if self.quiet_since is None:
        self.quiet_since = now
    else:
      self.quiet_since = None
    self.frame += 1
    if self.frame % POLL_FRAMES:
      return False
    dwell = self.quiet_since is not None and now - self.quiet_since >= DWELL_S
    self._handle_request(now, hard, dwell)
    if self.committed_at is None:
      self._handle_pending(dwell)
    return self.blocking

  # ---- requests --------------------------------------------------------------------------------------------------
  def _no_cycle_needed(self, board):
    """Same board running, or nothing steers (passive / not a 9G): params only, no restart."""
    return self.board is None or board == self.board

  def _write_only(self, board):
    if configured_board(self.params) != board:
      write_board(self.params, board, block=True)

  def _handle_request(self, now, hard, dwell):
    request = read_request(self.params)
    if request is None:
      self.request_since.clear()
      try:
        if _text(self.params.get(SWITCH_PARAM)):
          _remove(self.params, SWITCH_PARAM)    # garbage
      except Exception:
        pass
      return
    board, rid = request['board'], request['id']
    if self._no_cycle_needed(board):
      self._write_only(board)
      if pending_board(self.params) is not None:
        clear_pending(self.params, BOARD_PENDING)
      _remove(self.params, SWITCH_PARAM)
      reason = 'already active' if self.board == board else 'Used when openpilot starts'
      _result(self.params, rid, board, APPLIED_NOW, reason)
      cloudlog.event('accord_board_switch', board=board, applied=APPLIED_NOW, reason=reason)
      return
    if hard is not None:
      _remove(self.params, SWITCH_PARAM)
      _result(self.params, rid, board, APPLIED_REFUSED, hard)
      cloudlog.event('accord_board_switch', board=board, applied=APPLIED_REFUSED, reason=hard)
      return
    if dwell:
      self._commit(board, rid)
      return
    first = self.request_since.setdefault(rid, now)
    if now - first > REQUEST_TIMEOUT_S:
      reason = REFUSE_UNKNOWN if self.quiet_since is None else REFUSE_DWELL
      self.request_since.pop(rid, None)
      _remove(self.params, SWITCH_PARAM)
      _result(self.params, rid, board, APPLIED_REFUSED, reason)
      cloudlog.event('accord_board_switch', board=board, applied=APPLIED_REFUSED, reason=reason)

  def _handle_pending(self, dwell):
    board = pending_board(self.params)
    if board is None:
      return
    if self._no_cycle_needed(board):
      self._write_only(board)
      clear_pending(self.params, BOARD_PENDING)
      cloudlog.event('accord_board_switch_staged', board=board, cycle=False)
    elif dwell:
      self._commit(board, None)

  def _commit(self, board, rid):
    # order matters: board params durable first, then the answer, then the restart request
    write_board(self.params, board, block=True)
    if pending_board(self.params) is not None:
      clear_pending(self.params, BOARD_PENDING)
    _remove(self.params, SWITCH_PARAM)
    self.committed_at = self.clock()
    self.committed_board = board
    _result(self.params, rid, board, APPLIED_NOW, 'Switching, about 10 s')
    self.params.put_bool(CYCLE_PARAM, True, block=True)
    cloudlog.event('accord_board_switch', board=board, applied=APPLIED_NOW, previous=self.board, staged=rid is None)


def block_engagement(CS) -> None:
  """Published carState between the commit and the restart: nothing can engage (CS is the card's structs.CarState)."""
  CS.cruiseState.available = False
  CS.steerFaultTemporary = True


def install(CP, params):
  """Every 9G Accord card (also passive), except replays."""
  import os
  if 'REPLAY' in os.environ or getattr(CP, 'carFingerprint', None) != 'HONDA_ACCORD_9G':
    return None
  return BoardSwitch(CP, params)
