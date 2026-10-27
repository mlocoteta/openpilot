#!/usr/bin/env python3
"""Replay real rlog/qlog segments through the /api/hud projection (host tool, never on the device).

Runs galaxy.hud.extract() at 4 Hz of log time on the latest message of each
service, with the same per-service age limits as the live worker, and writes one
/api/hud response per line (JSONL) plus "t" = seconds since the segment's first
event. CarParams are taken from the segment's first carParams event, like the
live worker's Params read; IsMetric comes from initData params when logged,
else from --is-metric.

  ./dev python openpilot/starpilot/galaxy/tools/hud_replay_dump.py SEGMENT_DIR_OR_LOG [...] -o out.jsonl
  ./dev python openpilot/starpilot/galaxy/tools/hud_replay_dump.py --scan SEGMENT_DIR [...]
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from openpilot.cereal import log
from openpilot.starpilot.galaxy.hud import MAX_AGE_S, SAMPLE_INTERVAL_S, SERVICES, SOURCE_MAX_AGE_S, STALE_AFTER_S, STATIC_SERVICES, \
                                          core_fresh, extract

WANTED = set(SERVICES) | {'initData'}


def log_path(path: Path) -> Path:
  if path.is_dir():
    for name in ('rlog.zst', 'rlog', 'rlog.bz2', 'qlog.zst', 'qlog', 'qlog.bz2'):
      if (path / name).exists():
        return path / name
    raise FileNotFoundError(f'no rlog/qlog in {path}')
  return path


def read_events(path: Path):
  data = path.read_bytes()
  if path.suffix == '.zst' or data[:4] == b'\x28\xB5\x2F\xFD':
    import zstandard
    data = zstandard.ZstdDecompressor().stream_reader(data).read()
  elif path.suffix == '.bz2':
    import bz2
    data = bz2.decompress(data)
  events = []
  for event in log.Event.read_multiple_bytes(data):
    try:
      which = event.which()
    except Exception:
      continue
    if which in WANTED:
      events.append((event.logMonoTime, which, event))
  events.sort(key=lambda item: item[0])
  return events


def is_metric_from(events):
  for _, which, event in events:
    if which != 'initData':
      continue
    try:
      for entry in event.initData.params.entries:
        if entry.key == 'IsMetric':
          return bytes(entry.value) in (b'1', b'true')
    except Exception:
      return None
    return None
  return None


def replay(path: Path, interval=SAMPLE_INTERVAL_S, is_metric=None):
  """Yield (t, response) at `interval` seconds of log time."""
  events = read_events(path)
  if not events:
    return
  logged = is_metric_from(events)
  is_metric = logged if logged is not None else is_metric
  car_params = next((event.carParams for _, which, event in events if which == 'carParams'), None)
  # initData of a later segment carries the route's start time; the clock starts at the first service event.
  times = [mono for mono, which, _ in events if which != 'initData']
  if not times:
    return
  start_ns, end_ns = times[0], times[-1]
  latest = {}
  index = 0
  seq = 0
  signature = None
  tick_ns = start_ns + int(interval * 1e9)
  while tick_ns <= end_ns:
    while index < len(events) and events[index][0] <= tick_ns:
      mono, which, event = events[index]
      if which != 'initData':
        latest[which] = (mono, event.valid, getattr(event, which))
      index += 1
    fresh, msgs, ages = {}, {}, {}
    for service in SERVICES:
      item = latest.get(service)
      if service in STATIC_SERVICES:
        fresh[service] = bool(item and item[1]) or car_params is not None
        msgs[service] = item[2] if item and item[1] else car_params
        continue
      age = (tick_ns - item[0]) / 1e9 if item else None
      ok = bool(item and item[1] and 0 <= age <= MAX_AGE_S.get(service, SOURCE_MAX_AGE_S))
      fresh[service] = ok
      msgs[service] = item[2] if ok else None
      if ok:
        ages[service] = age
    values = extract(msgs, fresh, is_metric)
    current = core_fresh(values, fresh)
    core = ('selfdriveState', 'carState') if values['onroad'] else ('deviceState',)
    age = max(ages[key] for key in core) if current else None
    new_signature = tuple(latest[s][0] if s in ages else 0 for s in SERVICES)
    if new_signature != signature:
      seq += 1
    signature = new_signature
    state = 'current' if current and age is not None and age <= STALE_AFTER_S else 'stale'
    response = {'schemaVersion': 1, 'state': state, 'sessionId': 'replay', 'seq': seq,
                'ageSeconds': round(age, 3) if age is not None else None, **values, 'error': ''}
    yield round((tick_ns - start_ns) / 1e9, 3), response
    tick_ns += int(interval * 1e9)


def summarize(path: Path):
  stats = Counter()
  alerts = Counter()
  egpu = Counter()
  slc_sources = Counter()
  for _, row in replay(path, interval=1.0):
    stats['samples'] += 1
    stats['current'] += row['state'] == 'current'
    stats['onroad'] += row['onroad'] is True
    stats['offroad'] += row['onroad'] is False
    stats['engaged'] += row['engaged'] is True
    stats['latActive'] += row['steering']['latActive'] is True
    stats['lead'] += row['lead'] is not None
    stats['standstill'] += row['vEgo'] is not None and row['vEgo'] < 0.2
    stats['highway'] += row['vEgo'] is not None and row['vEgo'] > 25
    stats['slcLimit'] += bool(row['slc'] and row['slc']['limit'])
    stats['fault'] += row['steering']['fault'] is True
    if row['slc'] and row['slc']['source']:
      slc_sources[row['slc']['source']] += 1
    if row['alert']:
      alerts[row['alert']['text1'] + ' / ' + row['alert']['text2']] += 1
    if row['egpu']:
      egpu[row['egpu']['state']] += 1
  return {'segment': str(path), **stats, 'alerts': dict(alerts), 'egpu': dict(egpu), 'slcSources': dict(slc_sources)}


def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('logs', nargs='+', type=Path, help='segment directories or rlog/qlog files')
  parser.add_argument('-o', '--output', type=Path, help='JSONL output (default stdout)')
  parser.add_argument('--scan', action='store_true', help='print one JSON summary per segment instead')
  parser.add_argument('--is-metric', choices=('true', 'false'), help='IsMetric when initData does not log it (it usually does not)')
  args = parser.parse_args(argv)

  if args.scan:
    for path in args.logs:
      try:
        print(json.dumps(summarize(log_path(path))), flush=True)
      except Exception as error:
        print(json.dumps({'segment': str(path), 'error': f'{type(error).__name__}: {error}'}), flush=True)
    return 0

  out = args.output.open('w') if args.output else sys.stdout
  try:
    for path in args.logs:
      for t, response in replay(log_path(path), is_metric=None if args.is_metric is None else args.is_metric == 'true'):
        out.write(json.dumps({'t': t, **response}, separators=(',', ':')) + '\n')
  finally:
    if args.output:
      out.close()
  return 0


if __name__ == '__main__':
  sys.exit(main())
