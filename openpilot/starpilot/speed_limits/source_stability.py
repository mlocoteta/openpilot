"""Debounce source observations before selection so map/vision gaps cannot flap SLC.

Map evidence is valid only on an unambiguous current-way match with a fresh GPS
fix, and Vision only while a sign read is current. On a real drive (2026-10-26,
Accord) Map was valid for ~19 % of frames and Vision for ~54 %, and the two
disagreed at zone boundaries. ORDERED selection then alternated between them
every second or two, so every flip restarted the confirmation prompt (new
decision, 10 s timeout never reached) and, without confirmation, would have
adopted each flip immediately.

Three rules, all per drive session and without I/O:

* hold: a source's last adopted limit stays VALID for HOLD_NS after its raw
  observation turns UNKNOWN or STALE (ABSENT passes through and clears it);
* dwell: a source's new limit replaces its held one only after the same value
  was read for DWELL_NS, with gaps no longer than GAP_NS; a different reading
  restarts the dwell;
* sticky: once Map or Vision supplies the selected limit it stays selected
  while its held limit is current; priority only decides when neither is held.

Dashboard and Online readings come from the car or a provider, not from a
per-frame match or sign read, so they pass through untouched and are never
masked.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from openpilot.starpilot.speed_limits import acceptance as acc
from openpilot.starpilot.speed_limits import selection as sel

HOLD_NS = 10_000_000_000
DWELL_NS = 2_000_000_000
GAP_NS = 1_500_000_000
UNKNOWN = acc.Observation(acc.ObservationKind.UNKNOWN)
DEBOUNCED = (sel.Source.MAP, sel.Source.VISION)


@dataclass(frozen=True)
class Track:
  held: acc.Observation | None = None  # always VALID when present
  held_ns: int = 0  # last frame whose raw reading matched the held limit
  challenger: acc.Observation | None = None
  challenger_since_ns: int = 0
  challenger_last_ns: int = 0


@dataclass(frozen=True)
class State:
  tracks: tuple[tuple[sel.Source, Track], ...] = tuple((source, Track()) for source in DEBOUNCED)
  sticky: sel.Source | None = None
  last_ns: int | None = None


EMPTY = State()


def state_is_valid(state: object) -> bool:
  return (isinstance(state, State) and type(state.tracks) is tuple and
          tuple(source for source, _ in state.tracks) == DEBOUNCED and
          all(isinstance(track, Track) for _, track in state.tracks) and
          (state.sticky is None or isinstance(state.sticky, sel.Source)) and
          (state.last_ns is None or (type(state.last_ns) is int and state.last_ns >= 0)))


def _step_track(track: Track, raw: acc.Observation, now_ns: int) -> tuple[Track, acc.Observation]:
  if raw.kind is acc.ObservationKind.ABSENT:
    return Track(), raw
  if raw.kind is acc.ObservationKind.VALID:
    assert raw.candidate is not None
    speed = raw.candidate.speed_mps
    if track.held is not None and track.held.candidate.speed_mps == speed and now_ns - track.held_ns <= HOLD_NS:
      # Same limit: keep the adopted candidate so its presentation stays put.
      return replace(track, held_ns=now_ns, challenger=None), track.held
    challenger = track.challenger
    if (challenger is None or challenger.candidate.speed_mps != speed or
        now_ns - track.challenger_last_ns > GAP_NS):
      track = replace(track, challenger=raw, challenger_since_ns=now_ns)
    track = replace(track, challenger_last_ns=now_ns)
    if now_ns - track.challenger_since_ns >= DWELL_NS:
      track = Track(held=track.challenger, held_ns=now_ns)
  if track.held is not None and now_ns - track.held_ns <= HOLD_NS:
    return track, track.held
  if track.held is not None:
    track = replace(track, held=None)
  # Not yet adopted (dwelling) or expired: never pass an undebounced value on.
  return track, UNKNOWN if raw.kind is acc.ObservationKind.VALID else raw


def stabilize(state: State, observations: Mapping[sel.Source, acc.Observation], policy: sel.SelectionPolicy,
              now_ns: int) -> tuple[State, dict[sel.Source, acc.Observation]]:
  """Return debounced per-source observations; the caller still runs select_limit on them."""
  if state.last_ns is not None and now_ns < state.last_ns:
    state = EMPTY  # reversed clock: start over rather than extend a hold
  tracks = []
  stable = dict(observations)
  for source, track in state.tracks:
    raw = observations.get(source, UNKNOWN)
    if not acc.observation_is_valid(raw):
      track, out = Track(), raw  # selection reports the malformed input itself
    else:
      track, out = _step_track(track, raw, now_ns)
    tracks.append((source, track))
    stable[source] = out
  sticky = state.sticky
  if sticky is not None and (stable[sticky].kind is not acc.ObservationKind.VALID or
                             (policy.mode is sel.SelectionMode.ORDERED and sticky not in policy.slots)):
    sticky = None
  if sticky is None:
    selected = sel.select_limit(stable, policy)
    sticky = selected.selected_source if not selected.errors and selected.selected_source in DEBOUNCED else None
  if sticky is not None:
    # The other debounced source cannot displace a held, current limit from the sticky one.
    stable = {source: (UNKNOWN if source in DEBOUNCED and source is not sticky and
                       observation.kind is acc.ObservationKind.VALID else observation)
              for source, observation in stable.items()}
  return State(tuple(tracks), sticky, now_ns), stable
