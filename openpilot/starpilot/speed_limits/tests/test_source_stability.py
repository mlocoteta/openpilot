"""Map/Vision flaps are debounced before selection (Accord route 4c, 2026-10-26)."""

import unittest
from dataclasses import replace

from openpilot.starpilot.speed_limits import acceptance as acc
from openpilot.starpilot.speed_limits import composition as comp
from openpilot.starpilot.speed_limits import selection as sel
from openpilot.starpilot.speed_limits import source_stability as stab
from openpilot.starpilot.speed_limits import speed_domain as sd
from openpilot.starpilot.speed_limits.runtime import Runtime
from openpilot.starpilot.speed_limits.runtime_settings import parse

NS = 1_000_000_000
MS = 1_000_000
MPH = 0.44704
SESSION = "flap-drive"
ORDERED = sel.SelectionPolicy(sel.SelectionMode.ORDERED, (sel.Source.MAP, sel.Source.VISION), False)
UNKNOWN = acc.Observation(acc.ObservationKind.UNKNOWN)
STALE = acc.Observation(acc.ObservationKind.STALE)
ABSENT = acc.Observation(acc.ObservationKind.ABSENT)
ACTIVE = acc.Authority(acc.Mode.LONGITUDINAL_ONLY, acc.LongitudinalOwner.SYSTEM, False, True, False, False)
HOST = comp.HostState(True, True, True, False, False, 100.0, 100.0)
OFFSET = sd.OffsetSchedule((sd.OffsetBand(0.0, None, 0.0),))


def reading(source: sel.Source, mph: float, road: str = "road") -> acc.Observation:
  return acc.Observation(acc.ObservationKind.VALID, acc.Candidate(
    source.value, acc.ObservationIdentity(acc.IdentityKind.GEOGRAPHIC, value=f"{source.value}-{road}"), mph * MPH))


def frame_obs(map_obs: acc.Observation = UNKNOWN, vision_obs: acc.Observation = UNKNOWN,
              dashboard: acc.Observation = UNKNOWN) -> dict[sel.Source, acc.Observation]:
  return {sel.Source.DASHBOARD: dashboard, sel.Source.MAP: map_obs, sel.Source.VISION: vision_obs,
          sel.Source.ONLINE: ABSENT}


def speed(observation: acc.Observation) -> float | None:
  return round(observation.candidate.speed_mps / MPH) if observation.kind is acc.ObservationKind.VALID else None


def flap(seconds: float, *, map_mph: float = 55, vision_mph: float = 45, start_ns: int = 0):
  """Route 4c pattern: Map valid ~1/5 of frames, Vision ~1/2, disagreeing; 20 Hz."""
  for i in range(int(seconds * 20)):
    now = start_ns + i * 50 * MS
    phase = i % 40
    map_obs = reading(sel.Source.MAP, map_mph) if phase < 8 else UNKNOWN
    vision_obs = reading(sel.Source.VISION, vision_mph) if 4 <= phase < 24 else STALE
    yield now, frame_obs(map_obs, vision_obs)


class StabilizerTests(unittest.TestCase):
  def run_frames(self, frames, state=None):
    state = state or stab.State()
    out = []
    for now, observations in frames:
      state, stable = stab.stabilize(state, observations, ORDERED, now)
      out.append((now, sel.select_limit(stable, ORDERED)))
    return state, out

  def test_raw_selection_flaps_but_stabilized_selection_holds_one_limit(self):
    frames = list(flap(60))
    raw = [speed(sel.select_limit(o, ORDERED).observation) for _, o in frames]
    raw_changes = sum(1 for a, b in zip(raw, raw[1:], strict=False) if a is not None and b is not None and a != b)
    self.assertGreater(raw_changes, 20)
    _, out = self.run_frames(frames)
    values = [speed(s.observation) for _, s in out if speed(s.observation) is not None]
    self.assertEqual(len(set(values)), 1)  # whichever source dwelled first stays sticky
    self.assertEqual(len({s.selected_source for _, s in out if s.selected_source is not None}), 1)

  def test_new_limit_needs_dwell_and_single_misread_never_passes(self):
    frames = [(i * 50 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 45))) for i in range(60)]
    state, out = self.run_frames(frames)
    first_valid = next(now for now, s in out if s.observation.kind is acc.ObservationKind.VALID)
    self.assertEqual(first_valid, stab.DWELL_NS)
    misread = [(3 * NS + i * 50 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 70 if i == 3 else 45)))
               for i in range(40)]
    _, out = self.run_frames(misread, state)
    self.assertEqual({speed(s.observation) for _, s in out}, {45})

  def test_changed_limit_adopts_after_dwell_and_a_different_reading_restarts_it(self):
    state, _ = self.run_frames([(i * 100 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 45))) for i in range(30)])
    start = 3 * NS
    seq = [(start + i * 100 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 55))) for i in range(15)]
    seq += [(start + 1500 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 45)))]
    seq += [(start + 1600 * MS + i * 100 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 55))) for i in range(25)]
    _, out = self.run_frames(seq, state)
    switched = next(now for now, s in out if speed(s.observation) == 55)
    self.assertEqual(switched, start + 1600 * MS + stab.DWELL_NS)

  def test_held_limit_survives_gaps_up_to_hold_then_expires(self):
    state, _ = self.run_frames([(i * 100 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 45))) for i in range(30)])
    last = 29 * 100 * MS
    for gap in (STALE, UNKNOWN):
      _, stable = stab.stabilize(state, frame_obs(vision_obs=gap), ORDERED, last + stab.HOLD_NS)
      self.assertEqual(speed(stable[sel.Source.VISION]), 45)
      _, stable = stab.stabilize(state, frame_obs(vision_obs=gap), ORDERED, last + stab.HOLD_NS + 1)
      self.assertIs(stable[sel.Source.VISION], gap)

  def test_absent_passes_through_and_clears_the_hold(self):
    state, _ = self.run_frames([(i * 100 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 45))) for i in range(30)])
    state, stable = stab.stabilize(state, frame_obs(vision_obs=ABSENT), ORDERED, 3 * NS)
    self.assertIs(stable[sel.Source.VISION], ABSENT)
    state, stable = stab.stabilize(state, frame_obs(), ORDERED, 3 * NS + 100 * MS)
    self.assertIs(stable[sel.Source.VISION], UNKNOWN)

  def test_sticky_source_keeps_control_until_its_hold_expires(self):
    state, _ = self.run_frames([(i * 100 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 45))) for i in range(30)])
    self.assertIs(state.sticky, sel.Source.VISION)
    start = 3 * NS
    # Higher-priority Map now reads 55 continuously while Vision stays current.
    both = [(start + i * 100 * MS, frame_obs(reading(sel.Source.MAP, 55), reading(sel.Source.VISION, 45))) for i in range(50)]
    state, out = self.run_frames(both, state)
    self.assertEqual({speed(s.observation) for _, s in out}, {45})
    # Vision goes quiet: its held 45 lasts HOLD_NS, then the dwelled Map 55 takes over.
    quiet_start = start + 50 * 100 * MS
    quiet = [(quiet_start + i * 100 * MS, frame_obs(reading(sel.Source.MAP, 55), STALE)) for i in range(120)]
    state, out = self.run_frames(quiet, state)
    takeover = next(now for now, s in out if speed(s.observation) == 55)
    self.assertGreater(takeover, quiet_start + stab.HOLD_NS - 200 * MS)
    self.assertLessEqual(takeover, quiet_start + stab.HOLD_NS + 200 * MS)
    self.assertIs(state.sticky, sel.Source.MAP)

  def test_dashboard_is_never_debounced_or_masked(self):
    policy = sel.SelectionPolicy(sel.SelectionMode.ORDERED, (sel.Source.DASHBOARD, sel.Source.VISION), False)
    state = stab.State()
    for i in range(30):
      state, _ = stab.stabilize(state, frame_obs(vision_obs=reading(sel.Source.VISION, 45)), policy, i * 100 * MS)
    dash = reading(sel.Source.DASHBOARD, 35)
    state, stable = stab.stabilize(state, frame_obs(vision_obs=reading(sel.Source.VISION, 45), dashboard=dash), policy, 3 * NS)
    self.assertIs(stable[sel.Source.DASHBOARD], dash)
    self.assertEqual(sel.select_limit(stable, policy).selected_source, sel.Source.DASHBOARD)

  def test_reversed_clock_restarts_and_state_validation(self):
    state, _ = self.run_frames([(10 * NS + i * 100 * MS, frame_obs(vision_obs=reading(sel.Source.VISION, 45))) for i in range(30)])
    state, stable = stab.stabilize(state, frame_obs(vision_obs=reading(sel.Source.VISION, 45)), ORDERED, NS)
    self.assertEqual(stable[sel.Source.VISION].kind, acc.ObservationKind.UNKNOWN)
    self.assertTrue(stab.state_is_valid(state))
    self.assertFalse(stab.state_is_valid(replace(state, tracks=())))


class CompositionFlapTests(unittest.TestCase):
  def drive(self, policy: acc.Policy, stability: bool, seconds: float = 60, actions=None):
    state = comp.new_session(SESSION)
    decisions, adoptions, bases = set(), [], []
    for now, observations in flap(seconds):
      action = actions(now, state) if actions else None
      ego = sd.SpeedPair(sd.DomainStatus.VALID, 22.0, 22.0, SESSION, now)
      f = comp.Frame(now, observations, ORDERED, ACTIVE, policy, OFFSET, sd.DomainStatus.VALID, ego, False, HOST,
                     action=action, source_stability=stability)
      result = comp.step(state, f)
      self.assertFalse(result.errors)
      state = result.state
      if state.acceptance.pending is not None:
        decisions.add(state.acceptance.pending.decision_id)
      if result.acceptance.history_write is not None:
        adoptions.append(round(result.acceptance.history_write.candidate.speed_mps / MPH))
      bases.append(result.acceptance.basis)
    return state, decisions, adoptions, bases

  def test_automatic_adoption_flaps_without_stability_and_adopts_once_with_it(self):
    automatic = acc.Policy(confirm_lower=False, confirm_higher=False, fallback_previous=True)
    _, _, adoptions, _ = self.drive(automatic, False)
    self.assertGreater(len(adoptions), 20)
    self.assertEqual(set(adoptions), {45, 55})
    _, _, adoptions, _ = self.drive(automatic, True)
    self.assertEqual(len(adoptions), 1)

  def test_confirmation_prompt_keeps_one_decision_and_reaches_its_timeout(self):
    confirm = acc.Policy(confirm_lower=True, confirm_higher=True, fallback_previous=True)
    _, decisions, _, _ = self.drive(confirm, False)
    self.assertGreater(len(decisions), 20)
    state, decisions, adoptions, bases = self.drive(confirm, True)
    self.assertEqual(len(decisions), 1)
    self.assertIn("timeout_reject", bases)
    self.assertEqual(adoptions, [])

  def test_driver_accept_matches_the_single_presented_decision(self):
    confirm = acc.Policy(confirm_lower=True, confirm_higher=True, fallback_previous=True)
    sent = []

    def press(now, state):
      pending = state.acceptance.pending
      if pending is not None and not sent and now >= 3 * NS:
        sent.append(now)
        return acc.DriverAction(SESSION, 1, pending.decision_id, acc.ActionKind.ACCEPT)
      return None
    state, decisions, adoptions, _ = self.drive(confirm, True, seconds=20, actions=press)
    self.assertEqual(len(adoptions), 1)
    self.assertEqual(len(decisions), 1)
    self.assertEqual(round(state.acceptance.accepted.candidate.speed_mps / MPH), adoptions[0])


class RuntimeGateTests(unittest.TestCase):
  def test_runtime_debounce_is_opt_in(self):
    settings = parse({'SpeedLimitController': True, 'SLCPriority1': 'Map Data', 'SLCPriority2': 'Vision'})
    self.assertFalse(Runtime(settings, session_id='a').source_stability)
    self.assertTrue(Runtime(settings, session_id='b', source_stability=True).source_stability)

  def test_plannerd_enables_it_only_on_the_accord_9g_with_the_toggle(self):
    import tempfile
    from opendbc.car.honda.interface import CarInterface
    from opendbc.car.honda.values import CAR
    from openpilot.common.params import Params
    from openpilot.selfdrive.controls.plannerd import SavedSlcLifecycle
    for car, toggle, expected in ((CAR.HONDA_ACCORD_9G, True, True), (CAR.HONDA_ACCORD_9G, None, False),
                                  (CAR.HONDA_ACCORD_9G, False, False), (CAR.HONDA_CIVIC, True, False)):
      with self.subTest(car=car, toggle=toggle), tempfile.TemporaryDirectory() as directory:
        params = Params(directory)
        try:
          for key, value in {'SpeedLimitController': True, 'SLCPriority1': 'Map Data', 'SLCPriority2': 'Vision'}.items():
            params.put(key, value, block=True)
          if toggle is not None:
            params.put_bool('SLCSourceStability', toggle, block=True)
          cp = CarInterface.get_non_essential_params(car)
          cp.openpilotLongitudinalControl = True
          runtime, _ = SavedSlcLifecycle(params, cp, {'SLC_REPLAY_RUNTIME': '1'}).refresh(NS)
          self.assertIsNotNone(runtime)
          self.assertIs(runtime.source_stability, expected)
        finally:
          params._finalizer()


  def test_plannerd_toggle_rebuilds_the_runtime(self):
    import tempfile
    from opendbc.car.honda.interface import CarInterface
    from opendbc.car.honda.values import CAR
    from openpilot.common.params import Params
    from openpilot.selfdrive.controls.plannerd import SavedSlcLifecycle
    with tempfile.TemporaryDirectory() as directory:
      params = Params(directory)
      try:
        for key, value in {'SpeedLimitController': True, 'SLCPriority1': 'Map Data', 'SLCPriority2': 'Vision'}.items():
          params.put(key, value, block=True)
        cp = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_9G)
        cp.openpilotLongitudinalControl = True
        life = SavedSlcLifecycle(params, cp, {'SLC_REPLAY_RUNTIME': '1'})
        runtime, changed = life.refresh(NS)
        self.assertTrue(changed)
        self.assertFalse(runtime.source_stability)
        self.assertEqual(life.refresh(NS + 2_000_000_000), (runtime, False))
        params.put_bool('SLCSourceStability', True, block=True)
        on, changed = life.refresh(NS + 4_000_000_000)
        self.assertTrue(changed)
        self.assertIsNot(on, runtime)
        self.assertTrue(on.source_stability)
      finally:
        params._finalizer()


if __name__ == "__main__":
  unittest.main()
