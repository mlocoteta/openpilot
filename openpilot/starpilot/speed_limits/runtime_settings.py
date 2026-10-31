"""Reviewed saved-setting mapping for the opt-in system-longitudinal SLC runtime."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from openpilot.starpilot.speed_limits import acceptance as acc
from openpilot.starpilot.speed_limits import offset_document as od
from openpilot.starpilot.speed_limits import selection as sel
from openpilot.starpilot.speed_limits import speed_domain as sd

MPH_TO_MPS = od.MPH_TO_MPS
KPH_TO_MPS = od.KPH_TO_MPS
IMPERIAL_BOUNDS = od.IMPERIAL_BOUNDS
METRIC_BOUNDS = od.METRIC_BOUNDS
LABELS = {"Dashboard": sel.Source.DASHBOARD, "Map Data": sel.Source.MAP, "Maps": sel.Source.MAP, "Vision": sel.Source.VISION}


@dataclass(frozen=True)
class Settings:
  enabled: bool
  display: bool
  selection: sel.SelectionPolicy
  acceptance: acc.Policy
  offsets: sd.OffsetSchedule
  errors: tuple[str, ...] = ()
  # Saved intent must still retire pending work when vehicle capabilities disable control.
  requested: bool = False
  advance_seconds: int = 0


def _bool(values: Mapping[str, object], key: str, default: bool = False) -> bool:
  value = values.get(key, default)
  if type(value) is not bool:
    raise ValueError(f"{key} must be Boolean")
  return value


def _disabled(reason: str) -> Settings:
  selection = sel.SelectionPolicy(sel.SelectionMode.ORDERED, (sel.Source.DASHBOARD, sel.Source.MAP), False)
  return Settings(False, False, selection, acc.Policy(display_only=True),
                  sd.OffsetSchedule((sd.OffsetBand(0.0, None, 0.0),)), (reason,))


def parse(values: Mapping[str, object]) -> Settings:
  """Translate saved labels without changing their meaning or enabling unsupported output."""
  try:
    control = _bool(values, "SpeedLimitController")
    display = control or _bool(values, "ShowSpeedLimits", True)
    document = (od.validate(values['SLCOffsetSchedule']) if 'SLCOffsetSchedule' in values else
                od.default_document(_bool(values, 'IsMetric')))
    if not isinstance(document, od.OffsetDocument):
      raise ValueError('saved SLC offsets need review')
    first = values.get("SLCPriority1", "Vision")
    second = values.get("SLCPriority2", "Dashboard")
    if type(first) is not str or type(second) is not str:
      raise ValueError("invalid saved SLC source priority")
    mode = {"Highest": sel.SelectionMode.HIGHEST, "Lowest": sel.SelectionMode.LOWEST}.get(first, sel.SelectionMode.ORDERED)
    if first not in (*LABELS, "Highest", "Lowest") or second not in LABELS:
      raise ValueError("invalid saved SLC source priority")
    slots = (LABELS.get(first), LABELS[second])
    override = values.get("SLCOverride", 1)
    if type(override) is not int or override not in (0, 1, 2):
      raise ValueError("invalid saved SLC override")
    confirmation = _bool(values, "SLCConfirmation")
    advance = values.get('SLCAdvanceSeconds', 0)
    if type(advance) is not int or not 0 <= advance <= 10:
      advance = 0  # An invalid optional timer cannot enable early adoption.
    policy = acc.Policy(confirm_lower=confirmation, confirm_higher=confirmation,
                        display_only=not control)
    offsets = document.schedule()
    # SLCOverride remains a validated legacy preference; only set-speed changes override SLC.
    return Settings(control, display, sel.SelectionPolicy(mode, slots, False), policy, offsets,
                    requested=control, advance_seconds=advance)
  except (ValueError, OverflowError) as error:
    return _disabled(str(error))


SAVED_KEYS = ("SpeedLimitController", "ShowSpeedLimits", "IsMetric", "SLCPriority1", "SLCPriority2",
              "SLCOverride", "SLCConfirmation", "SLCAdvanceSeconds")


def read_params(params) -> Settings:
  values = {}
  try:
    with Path(params.get_param_path('SLCOffsetSchedule')).open('rb') as stream:
      raw_document = stream.read(od.MAX_DOCUMENT_BYTES + 1)
  except FileNotFoundError:
    raw_document = None
  except OSError:
    return _disabled('Invalid saved SLCOffsetSchedule')
  if raw_document is not None:
    try:
      values['SLCOffsetSchedule'] = od.decode(raw_document)
    except (ValueError, OverflowError):
      return _disabled('Invalid saved SLCOffsetSchedule')
  for key in SAVED_KEYS:
    if raw_document is not None and key == 'IsMetric':
      continue
    # Typed Params reads turn malformed numbers/strings into absence and accept
    # any non-"1" Boolean as false. Neither may silently alter confirmation or
    # units. Decode the saved bytes explicitly; only an absent file uses defaults.
    try:
      with Path(params.get_param_path(key)).open('rb') as stream:
        raw = stream.read(8 if key == 'SLCAdvanceSeconds' else -1)
      if key == 'SLCAdvanceSeconds':
        if raw not in tuple(str(seconds).encode() for seconds in range(11)):
          raise ValueError('invalid advance time')
        value = int(raw)
      elif key == 'SLCOverride':
        value = int(raw)
      elif key in ('SLCPriority1', 'SLCPriority2'):
        value = raw.decode('utf-8')
      else:
        if raw not in (b'0', b'1'):
          raise ValueError('invalid Boolean')
        value = raw == b'1'
      values[key] = value
    except FileNotFoundError:
      continue
    except (OSError, ValueError, OverflowError):
      if key == 'SLCAdvanceSeconds':
        values[key] = 0
        continue
      return _disabled(f'Invalid saved {key}')
  return parse(values)
