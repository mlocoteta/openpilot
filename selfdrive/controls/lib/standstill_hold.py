"""Standstill engage ("tap-to-hold") for openpilot-longitudinal cars that already allow engaging at 0 mph.

Engage at a standstill = press SET (or RES) while stopped with the foot on the brake. selfdrived goes to
preEnabled ("Release Brake to Engage"), then to enabled when the brake is released. Without this module the
stopping brake ramps in from 0 at stoppingDecelRate after that engage, and when the planner isn't asking to
stop (a red light with no lead) the car creeps. Mat's drives 313/319/357 crept in 11 of 22 such engages.

With StandstillEngageMode on, an engage that starts in preEnabled at a standstill with the brake pressed
latches a hold. LongControl then sits in `stopping` at the full stopAccel from the first frame, regardless of
the plan, until the driver presses the gas. The hold never lets go by itself:
  - gas: the hold ends. Resume mode keeps openpilot engaged and drives on at the set speed (like stock
    stop-and-go ACC). Hold-only mode disengages (lateral/AOL may continue).
  - brake: the usual rising-edge brake disengage (the driver's foot now holds the car).
  - door open, seatbelt off, gear out of D, or HOLD_TIMEOUT_S: the hold keeps braking and an alert + chime asks
    the driver to press the brake. The door/seatbelt/gear disengage events are held back while holding, since
    disengaging would release the brake with the car in gear.
Faults (soft/immediate disables) are untouched and still disengage.

controlsd and selfdrived each run a StandstillHold on the same carState and selfdriveState inputs: controlsd
uses it to hold the brake, selfdrived for the alerts and event handling. The brake is only ever commanded while
openpilot is engaged; panda safety and controls_allowed are unchanged.
"""
from cereal import car, log
from openpilot.common.params import Params, UnknownKeyName

GearShifter = car.CarState.GearShifter
OpenpilotState = log.SelfdriveState.OpenpilotState

PARAM = "StandstillEngageMode"
MODE_OFF = 0
MODE_RESUME = 1  # gas press resumes normal openpilot driving at the set speed
MODE_HOLD_ONLY = 2  # gas press ends the hold and disengages
MODES = (MODE_OFF, MODE_RESUME, MODE_HOLD_ONLY)

HOLD_TIMEOUT_S = 180.0  # longest engaged hold in 22 h of logs was 126 s, with no faults
MODE_REFRESH_S = 1.0
RESUME_DEFAULT_MPH = 25.0  # Resume mode set speed at a standstill engage with no earlier set speed this drive

REASON_NONE = ""
REASON_DOOR = "Door Open"
REASON_SEATBELT = "Seatbelt Unlatched"
REASON_GEAR = "Gear not D"
REASON_TIMEOUT = "Long Hold"

# disengage events held back while holding: each would release the brake with the car still able to roll
HELD_BACK_EVENTS = ("doorOpen", "seatbeltNotLatched", "wrongGear", "reverseGear")


def read_mode(params: Params) -> int:
  try:
    mode = params.get_int(PARAM)
  except (UnknownKeyName, TypeError, ValueError):
    return MODE_OFF
  return mode if mode in MODES else MODE_OFF


class ModeReader:
  """Reads the mode param about once a second (no restart needed after a settings change)."""
  def __init__(self, params: Params | None = None):
    self.params = params if params is not None else Params()
    self.mode = read_mode(self.params)
    self.last_read_t = 0.0

  def get(self, now: float) -> int:
    if now - self.last_read_t >= MODE_REFRESH_S:
      self.mode = read_mode(self.params)
      self.last_read_t = now
    return self.mode


def brake_request_reason(CS, held_s: float) -> str:
  """Why the driver should take over with the brake while holding, or '' if nothing is wrong."""
  if CS.doorOpen:
    return REASON_DOOR
  if CS.seatbeltUnlatched:
    return REASON_SEATBELT
  if CS.gearShifter not in (GearShifter.drive, GearShifter.sport):
    return REASON_GEAR
  if held_s >= HOLD_TIMEOUT_S:
    return REASON_TIMEOUT
  return REASON_NONE


class StandstillHold:
  def __init__(self):
    self.active = False
    self.mode = MODE_OFF  # mode latched when the hold started
    self.start_t = 0.0
    self.ended_by_gas = False  # True only on the frame the gas ended the hold

  def held_s(self, now: float) -> float:
    return now - self.start_t if self.active else 0.0

  def update(self, mode: int, ss_state, enabled: bool, CS, now: float) -> bool:
    """ss_state/enabled: selfdrived's state machine (previous frame in selfdrived, latest message in controlsd)."""
    self.ended_by_gas = False

    if not enabled:
      self.active = False
      return False

    if self.active:
      if CS.gasPressed:
        self.active = False
        self.ended_by_gas = True
    elif (mode != MODE_OFF and ss_state == OpenpilotState.preEnabled and CS.standstill and CS.brakePressed and
          not CS.gasPressed):
      self.active = True
      self.mode = mode
      self.start_t = now

    return self.active


def resume_set_speed_kph(previous_kph: float, floor_kph: float, is_metric: bool, max_kph: float,
                         imperial_increment: float) -> float:
  """Resume-mode set speed (cruise helper units) for a standstill engage: the last set speed this drive, else
  RESUME_DEFAULT_MPH (40 km/h metric). A plain SET at 0 mph would otherwise set the 7 mph engage floor and the gas
  press would "resume" to that.
  """
  if previous_kph > floor_kph:
    return min(previous_kph, max_kph)
  return 40.0 if is_metric else RESUME_DEFAULT_MPH * imperial_increment
