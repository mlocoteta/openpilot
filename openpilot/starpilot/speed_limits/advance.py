"""One mapped boundary offered through the existing SLC decision owner."""
import math
from dataclasses import dataclass

from openpilot.starpilot.speed_limits import acceptance as acc, selection as sel
from openpilot.starpilot.speed_limits.map_observation import Upcoming


@dataclass
class Encounter:
  boundary_id: str
  from_mps: float
  speed_mps: float
  way_id: int
  started_ns: int
  crossed: bool = False
  declined: bool = False
  withdrawn: bool = False
  disabled: bool = False
  accepted_ns: int | None = None


class Advance:
  def __init__(self):
    self.encounter: Encounter | None = None
    self.boundary_id = ''
    self.started_ns: int | None = None

  def disable(self):
    if self.encounter is not None and not self.encounter.crossed:
      self.encounter.disabled = True

  def use_current(self, candidate):
    self.boundary_id, self.started_ns = '', None
    if self.encounter is not None:
      self.encounter.disabled = True
      self.encounter.withdrawn = False
      if candidate.speed_mps == self.encounter.speed_mps:
        self.encounter.declined = False
        self.encounter.accepted_ns = None

  def propose(self, observations, policy, upcoming: Upcoming | None, *, current_way_id: int,
              seconds: int, speed_mps: float | None, standstill: bool, can_offer: bool, now_ns: int):
    self.boundary_id, self.started_ns = '', None
    current = observations[sel.Source.MAP].candidate
    encounter = self.encounter
    if current is None:
      if encounter is not None and not encounter.crossed:
        return {source: acc.Observation(acc.ObservationKind.UNKNOWN)
                if observation.candidate is not None and observation.candidate.speed_mps == encounter.from_mps
                else observation for source, observation in observations.items()}
      return None
    if encounter is not None:
      if current.speed_mps == encounter.speed_mps and (encounter.crossed or current_way_id == encounter.way_id):
        encounter.crossed = True
      elif current.speed_mps not in (encounter.from_mps, encounter.speed_mps):
        self.encounter = encounter = None

    # shortcut: use fresh GPS distance without propagation; revisit only if replay shows material timing error.
    eligible = (can_offer and type(seconds) is int and 0 < seconds <= 10 and not standstill and
                type(speed_mps) in (int, float) and math.isfinite(speed_mps) and speed_mps > 0 and
                upcoming is not None and upcoming.distance_m <= speed_mps * seconds)
    if eligible and (encounter is None or upcoming.boundary_id != encounter.boundary_id):
      proposed = dict(observations)
      proposed[sel.Source.MAP] = upcoming.observation
      if sel.select_limit(proposed, policy).selected_source is sel.Source.MAP:
        assert upcoming.observation.candidate is not None
        encounter = self.encounter = Encounter(upcoming.boundary_id, current.speed_mps,
          upcoming.observation.candidate.speed_mps, upcoming.way_id, now_ns)
    if encounter is None:
      return None

    proposed = dict(observations)
    blocked = encounter.declined or encounter.withdrawn
    if encounter.crossed:
      if blocked:
        proposed = {source: acc.Observation(acc.ObservationKind.UNKNOWN)
                    if observation.candidate is not None and observation.candidate.speed_mps == encounter.speed_mps
                    else observation for source, observation in proposed.items()}
      else:
        if not encounter.disabled and sel.select_limit(observations, policy).selected_source is sel.Source.MAP:
          self.started_ns = encounter.started_ns
        return None
    elif (seconds > 0 and not blocked and not encounter.disabled and upcoming is not None and
          upcoming.boundary_id == encounter.boundary_id and
          upcoming.observation.candidate.speed_mps == encounter.speed_mps):
      proposed[sel.Source.MAP] = upcoming.observation
      if sel.select_limit(proposed, policy).selected_source is sel.Source.MAP:
        self.boundary_id, self.started_ns = encounter.boundary_id, encounter.started_ns
    else:
      # Losing a preview must not offer the still-current approach limit again.
      proposed[sel.Source.MAP] = acc.Observation(acc.ObservationKind.UNKNOWN)
    chosen = sel.select_limit(proposed, policy).observation.candidate
    if not encounter.crossed and chosen is not None and chosen.speed_mps == encounter.from_mps:
      encounter.withdrawn = True
      proposed = {source: acc.Observation(acc.ObservationKind.UNKNOWN)
                  if source is sel.Source.MAP or observation.candidate is not None and observation.candidate.speed_mps == encounter.from_mps
                  else observation for source, observation in proposed.items()}
      self.boundary_id, self.started_ns = '', None
    return proposed

  def observe(self, result):
    encounter = self.encounter
    if encounter is None or result.acceptance is None:
      return
    decision = result.acceptance
    selected = result.selection.observation.candidate if result.selection is not None else None
    if selected is not None and selected.speed_mps == encounter.speed_mps and selected.source == 'map':
      if decision.basis in ('driver_reject', 'timeout_reject', 'rejected'):
        encounter.declined = True
      accepted = decision.state.accepted
      if accepted is not None and accepted.candidate.speed_mps == encounter.speed_mps and decision.state.pending is None:
        if encounter.accepted_ns is None:
          encounter.accepted_ns = accepted.accepted_at_ns
    elif selected is not None and not encounter.crossed and not encounter.disabled:
      encounter.withdrawn = True
    if encounter.accepted_ns is not None and result.state.override.persistent_selected_mps is not None:
      encounter.withdrawn = True
    accepted = decision.state.accepted
    if not encounter.disabled and encounter.accepted_ns is not None and accepted is not None and accepted.accepted_at_ns != encounter.accepted_ns:
      encounter.withdrawn = True
