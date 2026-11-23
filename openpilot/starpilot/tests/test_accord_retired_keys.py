"""Accord 9G settings removed 2026-11-23 must never block startup (openpilot/starpilot/state_migration.py)."""
import tempfile
import unittest
from pathlib import Path

from openpilot.common.params import Params
from openpilot.starpilot.state_migration import ACCORD_RETIRED_KEYS, RETIRED_KEYS, load_snapshot, prepare_manager_start

# Values as saved on the car before the removal (manager writes PERSISTENT defaults; the probe is cleared to 0).
SAVED = {'SSV3BlendProbe': b'0', 'SSV3DeadbandComp': b'0', 'SSV3TxAllLkasData': b'0', 'SLCSourceStability': b'0'}


class TestAccordRetiredKeys(unittest.TestCase):
  def setUp(self):
    self.temporary = tempfile.TemporaryDirectory()
    self.addCleanup(self.temporary.cleanup)
    self.root = Path(self.temporary.name)
    self.params = Params(str(self.root / 'params'))
    self.namespace = Path(self.params.get_param_path())
    self.storage = self.root / 'recovery'

  def test_keys_are_unregistered_and_retired(self):
    registered = {key.decode() if isinstance(key, bytes) else key for key in self.params.all_keys()}
    self.assertEqual(set(SAVED), set(ACCORD_RETIRED_KEYS))
    self.assertFalse(registered & ACCORD_RETIRED_KEYS)
    self.assertTrue(ACCORD_RETIRED_KEYS <= RETIRED_KEYS)

  def test_saved_values_are_archived_and_startup_proceeds(self):
    prepare_manager_start(self.params, self.storage)
    self.params.put('AlwaysOnLateral', True, block=True)
    for key, raw in SAVED.items():
      (self.namespace / key).write_bytes(raw)
    prepare_manager_start(self.params, self.storage, auto_migrate=True)
    remaining = {entry.name for entry in self.namespace.iterdir()}
    self.assertFalse(remaining & set(SAVED))
    self.assertIn('AlwaysOnLateral', remaining)
    archived = [load_snapshot(s) for s in (self.storage / 'snapshots').iterdir()]
    self.assertTrue(any(set(SAVED) <= set(snapshot) for snapshot in archived))
    # a second start is a no-op
    prepare_manager_start(self.params, self.storage, auto_migrate=True)
    prepare_manager_start(self.params, self.storage, dry_run=True)


if __name__ == '__main__':
  unittest.main()
