#!/usr/bin/env python3
"""Record the Accord fork's own cereal additions as reviewed, so upstream's schema-policy tests pass.

The Accord port adds two things upstream's schema guards don't know about:
  * log.capnp      OnroadEvent.EventName `ssv3BlendProbe @105` (SSV3 developer blend-probe alert)
  * custom.capnp   StarPilotCarState `ssv3 @N :Ssv3Status` (N = the next ordinal after upstream's last field)

Upstream pins log.capnp by sha256 (tools/ci/schema-policy.json) and StarPilotCarState's compiled layout
(starpilot/car/tesla/tests/fixtures/custom_reviewed_schema_additions.json). This script re-derives the three
pinned values from the tree it runs in, so a rebase conflict in those files is resolved by taking upstream's
side and re-running it:

  ./dev python tools/accord_schema_review.py --root "$PWD"          # rewrite (idempotent)
  ./dev python tools/accord_schema_review.py --root "$PWD" --check  # exit 1 if anything would change

(./dev runs a mirror copy of the tree, so --root points the writes back at the real checkout.)

It only accepts the known Accord additions: any other unreviewed log.capnp line or StarPilotCarState field
still fails upstream's tests.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STARPILOT_CAR_STATE = '0xf35cc4560bbf6ec2'
ACCORD_LOG_LINES = (re.compile(r'^\s*ssv3BlendProbe @\d+;.*$'),)
ACCORD_CAR_STATE_FIELDS = ('ssv3',)


def normalized_log_sha(policy, log: str, custom: str) -> str:
  """sha256 exactly as tools/ci/schema_policy.validate() computes it (reserved aliases folded back)."""
  sys.path.insert(0, str(ROOT))
  from tools.ci.schema_policy import custom_structs
  definitions, _, _ = custom_structs(custom)
  for slot in policy['reserved']:
    name = definitions.get(slot['type_id'])
    if name is None:
      continue
    log = re.sub(rf'(?m)^(\s*)\w+ @{slot["ordinal"]} :Custom\.{re.escape(name)};',
                 rf'\g<1>{slot["field"]} @{slot["ordinal"]} :Custom.{slot["struct"]};', log)
  for ordinal, name in policy['raw_reserved'].items():
    log = re.sub(rf'(?m)^(\s*)\w+ @{ordinal} :Data;', rf'\g<1>{name} @{ordinal} :Data;', log)
  return hashlib.sha256(log.encode()).hexdigest()


def upstream_log(log: str) -> str:
  lines = [line for line in log.splitlines(keepends=True) if not any(p.match(line.rstrip('\n')) for p in ACCORD_LOG_LINES)]
  return ''.join(lines)


def review_car_state(review):
  from openpilot.cereal import custom
  from openpilot.starpilot.car.tesla.tests.schema_fixture import layout
  entry = review['types'][STARPILOT_CAR_STATE]
  current = layout(custom.StarPilotCarState.schema)
  fields = current.pop('fields')
  upstream_added = [f for f in entry['added_fields'] if f['name'] not in ACCORD_CAR_STATE_FIELDS]
  ours = [f for f in fields if f['name'] in ACCORD_CAR_STATE_FIELDS]
  tail = [f['name'] for f in fields[entry['old_field_count']:]]
  if sorted(tail) != sorted([f['name'] for f in upstream_added] + [f['name'] for f in ours]):
    raise SystemExit(f'StarPilotCarState fields beyond the reviewed ones: {tail}; review them first')
  entry['added_fields'] = upstream_added + sorted(ours, key=lambda f: f['ordinal']['explicit'])
  entry['new_storage'] = current
  return max(f['ordinal']['explicit'] for f in fields) + 1


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('--check', action='store_true')
  ap.add_argument('--root', type=Path, default=ROOT, help='checkout whose pinned files are read and rewritten')
  args = ap.parse_args()
  POLICY = args.root / 'tools/ci/schema-policy.json'
  REVIEW = args.root / 'openpilot/starpilot/car/tesla/tests/fixtures/custom_reviewed_schema_additions.json'
  EVOLUTION_TEST = args.root / 'openpilot/starpilot/car/tesla/tests/test_pedal_schema_evolution.py'

  changes = {}
  policy_text = POLICY.read_text()
  policy = json.loads(policy_text)
  log = (args.root / 'openpilot/cereal/log.capnp').read_text()
  custom_src = (args.root / 'openpilot/cereal/custom.capnp').read_text()
  full, base = normalized_log_sha(policy, log, custom_src), normalized_log_sha(policy, upstream_log(log), custom_src)
  # The pin must be upstream's (log.capnp without the Accord lines) or already ours; anything else is unreviewed.
  if policy['log_sha256'] not in (full, base):
    raise SystemExit('log.capnp differs from the pinned upstream schema beyond the Accord lines; review it first')
  if policy['log_sha256'] != full:
    changes[POLICY] = policy_text.replace(policy['log_sha256'], full)

  review_text = REVIEW.read_text()
  review = json.loads(review_text)
  next_ordinal = review_car_state(review)
  new_review = json.dumps(review, indent=2) + '\n'
  if new_review != review_text:
    changes[REVIEW] = new_review

  test_text = EVOLUTION_TEST.read_text()
  new_test = re.sub(r"(gmRegenGear @40 :Bool; unreviewed @)\d+( :Bool;)", rf'\g<1>{next_ordinal}\g<2>', test_text)
  if new_test != test_text:
    changes[EVOLUTION_TEST] = new_test

  for path in changes:
    print(('would update ' if args.check else 'updated ') + str(path.relative_to(args.root)))
  if args.check:
    return int(bool(changes))
  for path, text in changes.items():
    path.write_text(text)
  return 0


if __name__ == '__main__':
  raise SystemExit(main())
