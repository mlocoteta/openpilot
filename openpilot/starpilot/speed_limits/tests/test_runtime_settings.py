"""Persisted SLC corruption must not silently select a less restrictive default."""

from pathlib import Path
import tempfile
import unittest

from openpilot.common.params import Params
from openpilot.starpilot.speed_limits import acceptance as acc
from openpilot.starpilot.speed_limits.runtime_settings import MPH_TO_MPS, parse, read_params


class RuntimeSettingsTests(unittest.TestCase):
  def test_confirmation_master_controls_both_directions_regardless_of_legacy_flags(self):
    for enabled in (False, True):
      for legacy in ({}, {'SLCConfirmationLower': False, 'SLCConfirmationHigher': False},
                     {'SLCConfirmationLower': True, 'SLCConfirmationHigher': False},
                     {'SLCConfirmationLower': False, 'SLCConfirmationHigher': True}):
        with self.subTest(enabled=enabled, legacy=legacy):
          settings = parse({'SpeedLimitController': True, 'SLCConfirmation': enabled, **legacy})
          self.assertFalse(settings.errors)
          self.assertEqual((settings.acceptance.confirm_lower, settings.acceptance.confirm_higher), (enabled, enabled))

  def test_confirmation_on_never_autoaccepts_first_changed_or_disengaged_limits(self):
    active = acc.Authority(acc.Mode.COMBINED, acc.LongitudinalOwner.SYSTEM, True, True, False, False)
    stopped = acc.Authority(acc.Mode.COMBINED, acc.LongitudinalOwner.SYSTEM, False, False, False, True)
    policy = parse({'SpeedLimitController': True, 'SLCConfirmation': True}).acceptance
    for source in ('dashboard', 'map', 'vision', 'online'):
      previous = acc.Candidate(source, acc.ObservationIdentity(acc.IdentityKind.GEOGRAPHIC, value='accepted'), 20.)
      history = acc.AcceptedLimit(previous, 'drive', 0)
      for authority in (active, stopped):
        for accepted in (None, history):
          for speed in (15., 25.):
            with self.subTest(source=source, authority=authority, accepted=accepted, speed=speed):
              candidate = acc.Candidate(source, acc.ObservationIdentity(acc.IdentityKind.GEOGRAPHIC, value='new'), speed)
              result = acc.step(acc.new_session('drive', accepted), acc.Observation(acc.ObservationKind.VALID, candidate),
                                authority, policy, now_ns=1)
              self.assertEqual(result.state.accepted, accepted)
              self.assertIsNone(result.history_write)
              self.assertIsNotNone(result.state.pending)
              self.assertEqual(result.control_target_mps, 20. if accepted is not None and authority.can_control else None)

  def test_fresh_vision_display_default_preserves_explicit_saved_choices(self):
    from openpilot.starpilot.speed_limits.selection import Source
    with tempfile.TemporaryDirectory() as directory:
      params = Params(directory)
      settings = read_params(params)
      self.assertTrue(settings.display)
      self.assertFalse(settings.enabled)
      self.assertEqual(settings.selection.slots, (Source.VISION, Source.DASHBOARD))
      self.assertTrue(settings.acceptance.display_only)
      params.put_bool('ShowSpeedLimits', False, block=True)
      params.put('SLCPriority1', 'Dashboard', block=True)
      params.put('SLCPriority2', 'Map Data', block=True)
      saved = read_params(params)
      self.assertFalse(saved.display)
      self.assertFalse(saved.enabled)
      self.assertEqual(saved.selection.slots, (Source.DASHBOARD, Source.MAP))
      self.assertEqual(Path(params.get_param_path('ShowSpeedLimits')).read_bytes(), b'0')
      self.assertEqual(Path(params.get_param_path('SLCPriority1')).read_bytes(), b'Dashboard')
      self.assertEqual(Path(params.get_param_path('SLCPriority2')).read_bytes(), b'Map Data')

  def test_corrupt_saved_values_disable_control_without_rewriting(self):
    cases = {'SLCConfirmation': b'invalid',
             'Offset3': b'bad', 'IsMetric': b'2', 'SLCPriority1': b'\xff'}
    for key, raw in cases.items():
      with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
        params = Params(directory)
        params.put_bool('SpeedLimitController', True, block=True)
        path = Path(params.get_param_path(key))
        path.write_bytes(raw)
        settings = read_params(params)
        self.assertFalse(settings.enabled)
        self.assertTrue(settings.errors)
        self.assertEqual(path.read_bytes(), raw)
        self.assertTrue(params.get_bool('SpeedLimitController'))

  def test_absent_optional_values_keep_existing_defaults(self):
    with tempfile.TemporaryDirectory() as directory:
      params = Params(directory)
      params.put_bool('SpeedLimitController', True, block=True)
      settings = read_params(params)
      self.assertTrue(settings.enabled)
      self.assertFalse(settings.errors)
      self.assertTrue(all(band.offset_mps == 0 for band in settings.offsets.bands))

  def test_valid_native_values_preserve_explicit_zero_and_units(self):
    with tempfile.TemporaryDirectory() as directory:
      params = Params(directory)
      params.put_bool('SpeedLimitController', True, block=True)
      params.put_bool('SLCConfirmation', True, block=True)
      params.put_bool('SLCConfirmationLower', True, block=True)
      params.put('SLCFallback', 0, block=True)
      params.put('Offset3', -5.0, block=True)
      settings = read_params(params)
      self.assertTrue(settings.enabled)
      self.assertFalse(settings.errors)
      self.assertTrue(settings.acceptance.confirm_lower)
      self.assertAlmostEqual(settings.offsets.bands[2].offset_mps, -5 * MPH_TO_MPS)

  def test_retired_fallback_bytes_are_ignored_without_creating_or_rewriting_them(self):
    with tempfile.TemporaryDirectory() as directory:
      params = Params(directory)
      params.put_bool('SpeedLimitController', True, block=True)
      path = Path(params.get_param_path('SLCFallback'))
      baseline = read_params(params)
      self.assertTrue(baseline.enabled)
      self.assertFalse(path.exists())
      self.assertIsNone(params.get_default_value('SLCFallback'))
      for raw in (b'0', b'1', b'2', b'', b'broken', b'999', b'\xff'):
        with self.subTest(raw=raw):
          path.write_bytes(raw)
          self.assertEqual(read_params(params), baseline)
          self.assertEqual(path.read_bytes(), raw)
      for old in (0, 1, 2, None, 'broken'):
        self.assertEqual(parse({'SpeedLimitController': True, 'SLCFallback': old}), baseline)

  def test_nonfinite_or_unrepresentable_offset_disables_control(self):
    for value in (float('nan'), float('inf'), 10 ** 1000):
      with self.subTest(kind=type(value).__name__):
        settings = parse({'SpeedLimitController': True, 'Offset3': value})
        self.assertFalse(settings.enabled)
        self.assertTrue(settings.errors)


if __name__ == '__main__':
  unittest.main()
