#!/usr/bin/env python3

import logging
import math
import os
import platform
import shutil
import signal
import sys
import time
from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Sequence
from pathlib import Path
from random import randint
from subprocess import PIPE, Popen, TimeoutExpired
from typing import Literal

from openpilot.common.basedir import BASEDIR
from openpilot.common.utils import managed_proc
from openpilot.tools.lib.route import Route
from openpilot.tools.lib.logreader import LogReader

# cereal.messaging, common.params and common.prefix load native extensions that the raybig path
# builds at runtime (prepare_raybig_runtime), so they're imported at point of use instead - at
# module scope they'd fail before that build ever runs.

DEFAULT_OUTPUT = 'output.mp4'
DEMO_START = 90
DEMO_END = 105
DEMO_ROUTE = 'a2a0ccea32023010/2023-07-27--13-01-19'
FRAMERATE = 20
PIXEL_DEPTH = '24'
RESOLUTION = '2160x1080'
SECONDS_TO_WARM = 2
PROC_WAIT_SECONDS = 30*10
RECORD_TAIL_MARGIN = 5  # extra seconds recorded past the requested end, see record_raybig
MAX_CACHED_SEGMENTS = 5  # replay's own default, see tools/replay/main.cc
MAX_PLAYBACK = 10  # upper bound for --playback, see record_raybig
PROGRESS_INTERVAL = 30  # seconds between progress lines while recording
STALL_WARN_SECONDS = 60  # warn if the output file stops growing for this long

OPENPILOT_FONT = str(Path(BASEDIR, 'selfdrive/assets/fonts/Inter-Regular.ttf').resolve())
REPLAY = str(Path(BASEDIR, 'tools/replay/replay').resolve())
UI = str(Path(BASEDIR, 'selfdrive/ui/ui').resolve())
RAYBIG_UI = str(Path(BASEDIR, 'selfdrive/ui/ui.py').resolve())
RAYBIG_PREPARE_SCRIPT = str(Path(BASEDIR, 'scripts/launch_ui_raybig_desktop.sh').resolve())
WSLG_X11_DIR = '/mnt/wslg/.X11-unix'

logger = logging.getLogger('clip.py')


def proc_output(proc: Popen, tail: int = 4000) -> str:
  log_file = getattr(proc, 'log_file', None)
  if log_file is None:
    return ''
  pos = log_file.tell()
  log_file.seek(0)
  try:
    return log_file.read().decode(errors='replace')[-tail:]
  finally:
    log_file.seek(pos)


def check_for_failure(procs: list[Popen]):
  for proc in procs:
    exit_code = proc.poll()
    if exit_code is not None and exit_code != 0:
      cmd = str(proc.args)
      if isinstance(proc.args, str):
        cmd = proc.args
      elif isinstance(proc.args, Sequence):
        cmd = str(proc.args[0])
      msg = f'{cmd} failed, exit code {exit_code}'
      logger.error(msg)
      output = proc_output(proc)
      if output:
        logger.error(output)
      raise ChildProcessError(msg)


def escape_ffmpeg_text(value: str):
  special_chars = {',': '\\,', ':': '\\:', '=': '\\=', '[': '\\[', ']': '\\]'}
  value = value.replace('\\', '\\\\\\\\\\\\\\\\')
  for char, escaped in special_chars.items():
    value = value.replace(char, escaped)
  return value


def get_logreader(route: Route):
  return LogReader(route.qlog_paths()[0] if len(route.qlog_paths()) else route.name.canonical_name)


def get_meta_text(lr: LogReader, route: Route):
  init_data = lr.first('initData')
  car_params = lr.first('carParams')
  origin_parts = init_data.gitRemote.split('/')
  origin = origin_parts[3] if len(origin_parts) > 3 else 'unknown'
  return ', '.join([
    f"openpilot v{init_data.version}",
    f"route: {route.name.canonical_name}",
    f"car: {car_params.carFingerprint}",
    f"origin: {origin}",
    f"branch: {init_data.gitBranch}",
    f"commit: {init_data.gitCommit[:7]}",
    f"modified: {str(init_data.dirty).lower()}",
  ])


def parse_args(parser: ArgumentParser):
  args = parser.parse_args()
  if args.demo:
    args.route = DEMO_ROUTE
    if args.start is None or args.end is None:
      args.start = DEMO_START
      args.end = DEMO_END
  elif args.route.count('/') == 1:
    if args.start is None or args.end is None:
      parser.error('must provide both start and end if timing is not in the route ID')
  elif args.route.count('/') == 3:
    if args.start is not None or args.end is not None:
      parser.error('don\'t provide timing when including it in the route ID')
    parts = args.route.split('/')
    args.route = '/'.join(parts[:2])
    args.start = int(parts[2])
    args.end = int(parts[3])
  if args.end <= args.start:
    parser.error(f'end ({args.end}) must be greater than start ({args.start})')
  if args.start < SECONDS_TO_WARM:
    parser.error(f'start must be greater than {SECONDS_TO_WARM}s to allow the UI time to warm up')

  try:
    args.route = Route(args.route, data_dir=args.data_dir)
  except Exception as e:
    parser.error(f'failed to get route: {e}')

  # FIXME: length isn't exactly max segment seconds, simplify to replay exiting at end of data
  # max_seg_number is a 0-based index, so the route has max_seg_number + 1 segments
  length = round((args.route.max_seg_number + 1) * 60)
  if args.start >= length:
    parser.error(f'start ({args.start}s) cannot be after end of route ({length}s)')
  if args.end > length:
    parser.error(f'end ({args.end}s) cannot be after end of route ({length}s)')

  return args


def populate_car_params(lr: LogReader):
  from openpilot.common.params import Params, UnknownKeyName

  init_data = lr.first('initData')
  assert init_data is not None

  params = Params()
  entries = init_data.params.entries
  for cp in entries:
    key, value = cp.key, cp.value
    try:
      params.put(key, params.cpp2python(key, value))
    except UnknownKeyName:
      # forks of openpilot may have other Params keys configured. ignore these
      logger.warning(f"unknown Params key '{key}', skipping")
    except (TypeError, ValueError) as e:
      # logged value doesn't cast to the param's type, e.g. an empty JSON param. ignore these
      logger.warning(f"could not restore Params key '{key}', skipping: {e}")
  logger.debug('persisted CarParams')


def wslg_available() -> bool:
  return os.path.isdir(WSLG_X11_DIR)


def validate_env(parser: ArgumentParser, ui: Literal['c3', 'raybig']):
  if platform.system() not in ['Linux']:
    parser.exit(1, f'clip.py: error: {platform.system()} is not a supported operating system\n')

  use_wslg = ui == 'raybig' and wslg_available()

  required_bins = ['ffmpeg']
  if ui == 'raybig':
    required_bins.append('ffprobe')  # used to retime the export, see retime_to_wall_clock
  if not use_wslg:
    # Under WSLg, raybig renders against the existing live :0 display instead of a virtual Xvfb one.
    required_bins.append('Xvfb')
  for proc in required_bins:
    if shutil.which(proc) is None:
      parser.exit(1, f'clip.py: error: missing {proc} command, is it installed?\n')

  # REPLAY is not checked here; prepare_replay() builds it on demand

  if ui == 'c3':
    if shutil.which(UI) is None:
      parser.exit(1, f'clip.py: error: missing {UI} command, did you build openpilot yet?\n')
  elif ui == 'raybig':
    if not os.path.isfile(RAYBIG_UI):
      parser.exit(1, f'clip.py: error: missing {RAYBIG_UI}\n')
    if not os.access(RAYBIG_PREPARE_SCRIPT, os.X_OK):
      parser.exit(1, f'clip.py: error: missing or non-executable {RAYBIG_PREPARE_SCRIPT}\n')


def validate_output_file(output_file: str):
  if not output_file.endswith('.mp4'):
    raise ArgumentTypeError('output must be an mp4')
  return output_file


def validate_route(route: str):
  if route.count('/') not in (1, 3):
    raise ArgumentTypeError(f'route must include or exclude timing, example: {DEMO_ROUTE}')
  return route


def validate_title(title: str):
  if len(title) > 80:
    raise ArgumentTypeError('title must be no longer than 80 chars')
  return title


def validate_scale(scale: str):
  value = float(scale)
  if not 0 < value <= 1:
    raise ArgumentTypeError('scale must be greater than 0 and at most 1')
  return value


def validate_playback(playback: str):
  value = float(playback)
  if not 1 <= value <= MAX_PLAYBACK:
    raise ArgumentTypeError(f'playback must be between 1 and {MAX_PLAYBACK}')
  return value


def wait_for_frames(procs: list[Popen]):
  from cereal.messaging import SubMaster

  sm = SubMaster(['uiDebug'])
  no_frames_drawn = True
  while no_frames_drawn:
    sm.update()
    no_frames_drawn = sm['uiDebug'].drawTimeMillis == 0.
    check_for_failure(procs)


def wait_for_xvfb(display_num: int, xvfb_proc: Popen, timeout: float = 10.0):
  # the UI and replay start immediately after, so wait for the display to actually exist
  socket_path = f'/tmp/.X11-unix/X{display_num}'
  deadline = time.monotonic() + timeout
  while time.monotonic() < deadline:
    check_for_failure([xvfb_proc])
    if os.path.exists(socket_path):
      return
    time.sleep(0.05)
  raise TimeoutError(f'Xvfb did not create {socket_path} within {timeout}s')


def prepare_replay(jobs: int | None = None):
  if shutil.which(REPLAY) is not None:
    return

  logger.info('building replay (this can take a while the first time)...')
  env = os.environ.copy()
  env['SP_DISABLE_AUTO_DEVICE_SCONS'] = '1'
  scons = Path(BASEDIR, '.venv/bin/scons')
  cmd = [str(scons)] if os.access(scons, os.X_OK) else [sys.executable, '-m', 'SCons']
  cmd += ['--extras', '-j', str(jobs or os.cpu_count() or 8), 'tools/replay/replay']
  if Popen(cmd, cwd=BASEDIR, env=env).wait() != 0:
    raise ChildProcessError('failed to build replay, see output above')


def prepare_raybig_runtime():
  logger.info('preparing raybig host runtime (this can take a while the first time)...')
  env = os.environ.copy()
  env['SP_RAYBIG_COMPILE_ONLY'] = '1'
  # Without this, the script's own cleanup trap restores/deletes the .so files it just built.
  env['SP_KEEP_DESKTOP_RUNTIME_ARTIFACTS'] = '1'
  result = Popen([RAYBIG_PREPARE_SCRIPT], env=env)
  if result.wait() != 0:
    raise ChildProcessError('failed to prepare raybig host runtime, see output above')


def make_ffmpeg_cmd(display: str, out: str, duration: int, bit_rate_kbps: int, overlays: list[str]):
  return [
    'ffmpeg', '-y',
    '-video_size', RESOLUTION,
    '-framerate', str(FRAMERATE),
    '-f', 'x11grab',
    '-rtbufsize', '100M',
    '-draw_mouse', '0',
    '-i', display,
    '-c:v', 'libx264',
    '-maxrate', f'{bit_rate_kbps}k',
    '-bufsize', f'{bit_rate_kbps*2}k',
    '-crf', '23',
    '-filter:v', ','.join(overlays),
    '-preset', 'ultrafast',
    '-tune', 'zerolatency',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-f', 'mp4',
    '-t', str(duration),
    out,
  ]


def record(procs: list[Popen], env: dict[str, str], display: str, out: str, duration: int,
           bit_rate_kbps: int, overlays: list[str]):
  # c3 has no frame export of its own, so screen capture its Xvfb display. raybig uses
  # record_raybig instead.
  logger.info('waiting for replay to begin (loading segments, may take a while)...')
  wait_for_frames(procs)
  logger.debug(f'letting UI warm up ({SECONDS_TO_WARM}s)...')
  time.sleep(SECONDS_TO_WARM)
  check_for_failure(procs)

  ffmpeg_cmd = make_ffmpeg_cmd(display, out, duration, bit_rate_kbps, overlays)
  with managed_proc(ffmpeg_cmd, env) as ffmpeg_proc:
    all_procs = procs + [ffmpeg_proc]
    logger.info(f'recording in progress ({duration}s)...')
    ffmpeg_proc.wait(duration + PROC_WAIT_SECONDS)
    check_for_failure(all_procs)
    logger.info(f'recording complete: {Path(out).resolve()}')


def probe_video(path: str) -> tuple[float, float]:
  """Return (duration_seconds, frame_rate) of a video file's first video stream."""
  proc = Popen(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=r_frame_rate:format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', path], stdout=PIPE, stderr=PIPE)
  stdout, stderr = proc.communicate()
  if proc.returncode != 0:
    raise ChildProcessError(f'ffprobe failed on {path}: {stderr.decode().strip()}')

  values = stdout.decode().split()
  rate_str = next(v for v in values if '/' in v)
  numerator, denominator = rate_str.split('/')
  frame_rate = float(numerator) / float(denominator)
  duration = float(next(v for v in values if '/' not in v))
  return duration, frame_rate


def retime_to_wall_clock(out: str, recorded_seconds: float, tolerance: float = 0.10):
  # the UI tags the export with the fps it targeted, but the real rate depends on how fast this
  # machine reads frames back from the GPU. frames are produced in lockstep with real-time
  # replay, so re-tag to match wall clock. remuxing through raw h264 avoids a re-encode.
  # tolerance is loose because recorded_seconds starts at the first onroad frame, a few seconds
  # after the UI starts recording; this only needs to catch gross mismatches.
  duration, frame_rate = probe_video(out)
  if abs(duration - recorded_seconds) <= tolerance * recorded_seconds:
    return

  actual_frame_rate = frame_rate * duration / recorded_seconds
  logger.info(f'retiming: {duration:.1f}s at {frame_rate:.2f}fps -> {recorded_seconds:.1f}s at {actual_frame_rate:.2f}fps')

  out_path = Path(out)
  raw = out_path.with_suffix('.retime.h264')
  retimed = out_path.with_suffix('.retime.mp4')
  try:
    for cmd in (['ffmpeg', '-y', '-v', 'error', '-i', out, '-c', 'copy', '-f', 'h264', str(raw)],
                ['ffmpeg', '-y', '-v', 'error', '-r', f'{actual_frame_rate:.6f}', '-i', str(raw),
                 '-c', 'copy', '-movflags', '+faststart', str(retimed)]):
      proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
      _, stderr = proc.communicate()
      if proc.returncode != 0:
        raise ChildProcessError(f'retime step failed: {stderr.decode().strip()}')
    retimed.replace(out_path)
  finally:
    raw.unlink(missing_ok=True)
    retimed.unlink(missing_ok=True)


def record_raybig(ui_proc: Popen, replay_proc: Popen, duration: int, out: str, playback: float = 1.0):
  # the UI records from the moment its window opens, so the export leads with some offroad
  # frames. tail margin covers replay not being exactly at `start` on the first onroad frame.
  # at playback > 1 the route advances faster than the clock, so we wait proportionally less.
  procs = [ui_proc, replay_proc]
  logger.info('waiting for replay to begin (loading segments, may take a while)...')
  wait_for_frames(procs)
  record_for = (SECONDS_TO_WARM + duration + RECORD_TAIL_MARGIN) / playback
  if playback > 1:
    logger.info(f'recording in progress ({duration}s of route at {playback}x, ~{record_for:.0f}s wall clock)...')
  else:
    logger.info(f'recording in progress ({duration}s)...')
  started_at = time.monotonic()
  out_path = Path(out)
  last_size, grew_at, logged_at = -1, started_at, started_at

  # poll rather than sleeping straight through, so a replay or UI that dies partway is caught
  # now instead of after the full duration has elapsed
  while (elapsed := time.monotonic() - started_at) < record_for:
    check_for_failure(procs)
    now = time.monotonic()
    size = out_path.stat().st_size if out_path.exists() else 0

    if size > last_size:
      last_size, grew_at = size, now
    elif now - grew_at > STALL_WARN_SECONDS:
      logger.warning(f'{out} has not grown in {now - grew_at:.0f}s; recording may have stalled')
      # the source is the usual suspect, so show what it last reported
      output = proc_output(replay_proc, tail=1500)
      if output:
        logger.warning(f'last replay output:\n{output}')
      grew_at = now

    if now - logged_at >= PROGRESS_INTERVAL:
      logger.info(f'recording {elapsed:.0f}/{record_for:.0f}s, {size / 1e6:.0f}MB')
      logged_at = now

    time.sleep(1)

  check_for_failure(procs)

  logger.info('stopping recording...')
  # SIGINT closes the window gracefully, flushing the UI's own ffmpeg pipe (close_ffmpeg() in
  # system/ui/lib/application.py). SIGTERM, which managed_proc uses, has no handler and would
  # skip that. close_ffmpeg() can take up to 60s, so wait longer than that before killing.
  ui_proc.send_signal(signal.SIGINT)
  # the clip should run for the stretch of route it covers, not the wall clock time it took,
  # so at playback > 1 scale back up. this also self-corrects a machine that couldn't render
  # fast enough to keep up: the result is fewer frames, not a wrongly sped up clip.
  recorded_seconds = (time.monotonic() - started_at) * playback
  try:
    ui_proc.wait(timeout=90)
  except TimeoutExpired:
    logger.warning('UI did not exit cleanly after SIGINT; the recording may be truncated or corrupt')
    ui_proc.kill()
    ui_proc.wait()

  if ui_proc.returncode not in (0, -signal.SIGINT):
    logger.warning(f'UI exited with code {ui_proc.returncode} after SIGINT; the recording may be incomplete')

  retime_to_wall_clock(out, recorded_seconds)
  logger.info(f'recording complete: {Path(out).resolve()}')


def clip(
  data_dir: str | None,
  quality: Literal['low', 'high'],
  prefix: str,
  route: Route,
  out: str,
  start: int,
  end: int,
  speed: int,
  target_mb: int,
  title: str | None,
  ui: Literal['c3', 'raybig'],
  scale: float | None,
  playback: float,
):
  logger.info(f'clipping route {route.name.canonical_name}, start={start} end={end} quality={quality} target_filesize={target_mb}MB')
  Path(out).resolve().parent.mkdir(parents=True, exist_ok=True)
  lr = get_logreader(route)

  begin_at = max(start - SECONDS_TO_WARM, 0)
  duration = end - start
  bit_rate_kbps = int(round(target_mb * 8 * 1024 * 1024 / duration / 1000))

  # raybig exports its own frames (RECORD, below) rather than being screen captured, so under
  # WSLg it can just render against the live desktop instead of needing its own Xvfb.
  use_wslg = ui == 'raybig' and wslg_available()
  if use_wslg:
    display = os.environ.get('DISPLAY', ':0')
  else:
    # TODO: evaluate creating fn that inspects /tmp/.X11-unix and creates unused display to avoid possibility of collision
    display_num = randint(99, 999)
    display = f':{display_num}'
    xvfb_cmd = ['Xvfb', display, '-terminate', '-screen', '0', f'{RESOLUTION}x{PIXEL_DEPTH}']

  box_style = 'box=1:boxcolor=black@0.33:boxborderw=7'
  meta_text = get_meta_text(lr, route)
  overlays = [
    # metadata overlay
    f"drawtext=text='{escape_ffmpeg_text(meta_text)}':fontfile={OPENPILOT_FONT}:fontcolor=white:fontsize=15:{box_style}:x=(w-text_w)/2:y=5.5:enable='between(t,1,5)'",
    # route time overlay
    f"drawtext=text='%{{eif\\:floor(({start}+t)/60)\\:d\\:2}}\\:%{{eif\\:mod({start}+t\\,60)\\:d\\:2}}':fontfile={OPENPILOT_FONT}:fontcolor=white:fontsize=24:{box_style}:x=w-text_w-38:y=38"
  ]
  if title:
    overlays.append(f"drawtext=text='{escape_ffmpeg_text(title)}':fontfile={OPENPILOT_FONT}:fontcolor=white:fontsize=32:{box_style}:x=(w-text_w)/2:y=53")

  if speed > 1:
    overlays += [
      f"setpts=PTS/{speed}",
      "fps=60",
    ]

  # read far enough ahead that replay doesn't run dry partway through and loop back on itself,
  # repeating earlier footage. capped because each cached ~60s segment holds its logs and camera
  # video in memory, and a long clip would otherwise try to hold the whole route at once.
  segments_to_cache = min(math.ceil((end - begin_at) / 60) + 1, MAX_CACHED_SEGMENTS)
  replay_cmd = [REPLAY, '--ecam', '-c', str(segments_to_cache), '-s', str(begin_at), '--prefix', prefix]
  if playback > 1:
    replay_cmd.extend(['-x', str(playback)])
  if data_dir:
    replay_cmd.extend(['--data_dir', data_dir])
  if quality == 'low':
    replay_cmd.append('--qcam')
  replay_cmd.append(route.name.canonical_name)

  prepare_replay()

  if ui == 'raybig':
    prepare_raybig_runtime()
    ui_cmd = [sys.executable, RAYBIG_UI]
  else:
    ui_cmd = [UI, '-platform', 'xcb']

  # imported here, after prepare_raybig_runtime() has built the native extensions it needs
  from openpilot.common.prefix import OpenpilotPrefix

  with OpenpilotPrefix(prefix, shared_download_cache=True):
    populate_car_params(lr)
    env = os.environ.copy()
    env['DISPLAY'] = display
    if ui == 'raybig':
      env['BIG'] = '1'
      env.setdefault('PRIME_TYPE', '0')
      # use the real replayed drive stats instead of raybig's desktop fake-data demo
      env['SP_RAYBIG_FAKE_DRIVE_STATS'] = '0'
      pythonpath_extra = f"{BASEDIR}{os.pathsep}{Path(BASEDIR, 'starpilot/third_party')}"
      env['PYTHONPATH'] = f"{pythonpath_extra}{os.pathsep}{env['PYTHONPATH']}" if env.get('PYTHONPATH') else pythonpath_extra
      # the raylib UI pipes its own frames to ffmpeg (system/ui/lib/application.py). no drawtext
      # overlays on this path, unlike c3.
      env['RECORD'] = '1'
      env['RECORD_OUTPUT'] = out
      env['RECORD_BITRATE'] = f'{bit_rate_kbps}k'
      if speed > 1:
        env['RECORD_SPEED'] = str(speed)
      # the UI defaults to 60fps and tags the export as such, but the per-frame GPU readback
      # can't sustain that and the clip plays fast. ask for a rate it can actually hit. at
      # playback > 1 it has to render proportionally faster to still cover FRAMERATE frames
      # per second of route.
      env['FPS'] = str(int(round(FRAMERATE * playback)))
      # sets the render texture size, which is what gets piped to ffmpeg. left unset, the UI
      # picks a scale that fits the screen.
      if scale is not None:
        env['SCALE'] = str(scale)

      if use_wslg:
        logger.info('WSLg detected: rendering against the live desktop display.')
        with managed_proc(ui_cmd, env) as ui_proc, managed_proc(replay_cmd, env) as replay_proc:
          record_raybig(ui_proc, replay_proc, duration, out, playback)
      else:
        with managed_proc(xvfb_cmd, env) as xvfb_proc:
          wait_for_xvfb(display_num, xvfb_proc)
          with managed_proc(ui_cmd, env) as ui_proc, managed_proc(replay_cmd, env) as replay_proc:
            record_raybig(ui_proc, replay_proc, duration, out, playback)
    else:
      with managed_proc(xvfb_cmd, env) as xvfb_proc:
        wait_for_xvfb(display_num, xvfb_proc)
        with managed_proc(ui_cmd, env) as ui_proc, managed_proc(replay_cmd, env) as replay_proc:
          record([xvfb_proc, ui_proc, replay_proc], env, display, out, duration, bit_rate_kbps, overlays)


def main():
  p = ArgumentParser(prog='clip.py', description='clip your openpilot route.', epilog='comma.ai')
  route_group = p.add_mutually_exclusive_group(required=True)
  route_group.add_argument('route', nargs='?', type=validate_route, help=f'The route (e.g. {DEMO_ROUTE} or {DEMO_ROUTE}/{DEMO_START}/{DEMO_END})')
  route_group.add_argument('--demo', help='use the demo route', action='store_true')
  p.add_argument('-d', '--data-dir', help='local directory where route data is stored')
  p.add_argument('-e', '--end', help='stop clipping at <end> seconds', type=int)
  p.add_argument('-f', '--file-size', help='target file size (Discord/GitHub support max 10MB, default is 9MB)', type=float, default=9.)
  p.add_argument('-o', '--output', help='output clip to (.mp4)', type=validate_output_file, default=DEFAULT_OUTPUT)
  p.add_argument('-p', '--prefix', help='openpilot prefix', default=f'clip_{randint(100, 99999)}')
  p.add_argument('-q', '--quality', help='quality of camera (low = qcam, high = hevc)', choices=['low', 'high'], default='high')
  p.add_argument('-x', '--speed', help='record the clip at this speed multiple', type=int, default=1)
  p.add_argument('-s', '--start', help='start clipping at <start> seconds', type=int)
  p.add_argument('-t', '--title', help='overlay this title on the video (e.g. "Chill driving across the Golden Gate Bridge")', type=validate_title)
  p.add_argument('-u', '--ui', help='desktop UI to record. raybig exports its own frames, so it also works where screen capture '
                                    'cannot see the window (e.g. WSLg), but gets no title/metadata overlays',
                 choices=['c3', 'raybig'], default='c3')
  p.add_argument('--scale', help='scale the recorded resolution, e.g. 0.5 for half size (raybig only, default is to fit the screen)',
                 type=validate_scale)
  p.add_argument('--playback', help='replay faster than real time to finish sooner, e.g. 2 for twice as fast (raybig only). '
                                    'the clip still plays at normal speed, but drops frames if the UI cannot keep up',
                 type=validate_playback, default=1.0)
  args = parse_args(p)
  validate_env(p, args.ui)
  exit_code = 1
  try:
    clip(
      data_dir=args.data_dir,
      quality=args.quality,
      prefix=args.prefix,
      route=args.route,
      out=args.output,
      start=args.start,
      end=args.end,
      speed=args.speed,
      target_mb=args.file_size,
      title=args.title,
      ui=args.ui,
      scale=args.scale,
      playback=args.playback,
    )
    exit_code = 0
  except KeyboardInterrupt as e:
    logger.exception('interrupted by user', exc_info=e)
  except Exception as e:
    logger.exception('encountered error', exc_info=e)
  sys.exit(exit_code)


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s\t%(message)s')
  main()
