#!/usr/bin/env python3
"""Replay real rlog segments through the /api/perf projection (host tool, never on the device).

Feeds the newest CAN batch per tick into perf.CanLatest (every CAN_EVERY-th, as
live) and takes the newest carState every 20 ms of log time (the live worker's 50 Hz), with the live
worker's age limits. Several consecutive segments can be given; they are joined
in order. Output is JSONL: one {"t", "row"} per sample (t = seconds since the
first event), plus "slow" (gear, 12 V, isMetric, onroad) once a second.

  ./dev python openpilot/starpilot/galaxy/tools/perf_replay_dump.py SEG_DIR [SEG_DIR...] -o out.jsonl
  ./dev python openpilot/starpilot/galaxy/tools/perf_replay_dump.py --check SEG_DIR [...]   # decode sanity stats
"""

import argparse
import json
import math
import sys
from pathlib import Path

from openpilot.cereal import log
from openpilot.starpilot.galaxy.perf import CAN_EVERY, FIELDS, MAX_AGE_S, SAMPLE_INTERVAL_S, SOURCE_MAX_AGE_S, CanLatest, accord_9g, \
                                           sample_row, slow_values

WANTED = {'carState', 'can', 'deviceState', 'peripheralState', 'carParams', 'initData'}


def log_path(path: Path) -> Path:
  if path.is_dir():
    for name in ('rlog.zst', 'rlog', 'rlog.bz2'):
      if (path / name).exists():
        return path / name
    raise FileNotFoundError(f'no rlog in {path} (qlogs have no CAN)')
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


def is_metric_from(events, default):
  for _, which, event in events:
    if which == 'initData':
      for entry in event.initData.params.entries:
        if entry.key == 'IsMetric':
          return bytes(entry.value) in (b'1', b'True', b'true')
  return default


def replay(events, is_metric):
  car_params = next((event.carParams for _, which, event in events if which == 'carParams'), None)
  decodes = accord_9g(car_params)
  can = CanLatest()
  latest, latest_ns = {}, {}
  last_can_ns, can_batches, latest_can = 0, 0, None
  start_ns = next(mono for mono, which, _ in events if which == 'carState')
  step_ns = int(SAMPLE_INTERVAL_S * 1e9)
  next_ns = start_ns
  last_row_ns = 0
  index = 0
  out = []
  end_ns = events[-1][0]
  while next_ns <= end_ns:
    while index < len(events) and events[index][0] <= next_ns:
      mono, which, event = events[index]
      if which == 'can':
        latest_can = (mono, event.can)
      elif which != 'initData':
        latest[which], latest_ns[which] = getattr(event, which), mono
      index += 1
    # Like the live conflated subscriber: only the newest CAN batch per tick, every CAN_EVERY-th one decoded.
    if decodes and latest_can is not None and latest_can[0] != last_can_ns and next_ns - latest_can[0] <= 300_000_000:
      last_can_ns = latest_can[0]
      can_batches += 1
      if can_batches % CAN_EVERY == 1 or CAN_EVERY == 1:
        can.update(latest_can[1], last_can_ns)
    fresh = {}
    for key in ('carState', 'deviceState', 'peripheralState'):
      age = (next_ns - latest_ns.get(key, -10**18)) / 1e9
      fresh[key] = key in latest and 0 <= age <= MAX_AGE_S.get(key, SOURCE_MAX_AGE_S)
    car_ns = latest_ns.get('carState', 0)
    if fresh['carState'] and car_ns != last_row_ns:
      last_row_ns = car_ns
      row = sample_row(latest['carState'], car_ns, can.decode(car_ns))
      row[0] = round((car_ns - start_ns) / 1e9, 3)
      item = {'t': row[0], 'row': row}
      if len(out) % 50 == 0 or len(out) == 5:
        item['slow'] = slow_values(latest, fresh, is_metric)
        item['decodes'] = decodes
      out.append(item)
    next_ns += step_ns
  return out


def check(rows):
  """Sign/scale sanity: VSA lat accel vs v*yaw, VSA long accel vs aEgo, ranges."""
  idx = {name: i for i, name in enumerate(FIELDS)}
  pairs_lat, pairs_long = [], []
  for item in rows:
    r = item['row']
    if r[idx['ay']] is not None and r[idx['yaw']] is not None and r[idx['v']] is not None and r[idx['v']] > 3:
      pairs_lat.append((r[idx['ay']], r[idx['v']] * r[idx['yaw']]))
    if r[idx['ax']] is not None and r[idx['a']] is not None:
      pairs_long.append((r[idx['ax']], r[idx['a']]))

  def corr(pairs):
    if len(pairs) < 10:
      return None
    xs, ys = zip(*pairs)
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return round(sxy / math.sqrt(sxx * syy), 3) if sxx and syy else None, round(sxy / syy, 3) if syy else None

  stats = {'samples': len(rows), 'lat_vs_vyaw(corr,slope)': corr(pairs_lat), 'long_vs_aEgo(corr,slope)': corr(pairs_long)}
  for name in ('v', 'a', 'ax', 'ay', 'yaw', 'steer', 'gas', 'brake', 'rpm'):
    values = [item['row'][idx[name]] for item in rows if item['row'][idx[name]] is not None]
    stats[name] = (min(values), max(values), len(values)) if values else None
  return stats


def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('segments', nargs='+', type=Path)
  parser.add_argument('-o', '--output', type=Path)
  parser.add_argument('--is-metric', choices=('true', 'false'), default='false')
  parser.add_argument('--check', action='store_true')
  args = parser.parse_args(argv)
  events = []
  for segment in args.segments:
    events.extend(read_events(log_path(segment)))
  events.sort(key=lambda item: item[0])
  if not events:
    print('no events', file=sys.stderr)
    return 1
  rows = replay(events, is_metric_from(events, args.is_metric == 'true'))
  if args.check:
    print(json.dumps(check(rows), indent=1))
  if args.output:
    with args.output.open('w') as handle:
      for item in rows:
        handle.write(json.dumps(item, separators=(',', ':')) + '\n')
    print(f'wrote {len(rows)} samples to {args.output}', file=sys.stderr)
  return 0


if __name__ == '__main__':
  sys.exit(main())
