"""Exercise protocol bounds, frame ownership and the real tool lifecycle without a browser installation."""

import array
import ast
import fcntl
import mmap
import os
import runpy
import socket
import sys
from types import SimpleNamespace as NS
from threading import Event, Thread
from unittest.mock import Mock

import pyray as rl
import pytest

from openpilot.selfdrive.ui.layouts.arabesque.tools import browser, browser_session as runtime
from openpilot.system.ui.lib.application import gui_app, MouseEvent, MousePos
from openpilot.system.ui.widgets import Widget


def test_sealed_frames_cannot_resize_and_roundtrip_fds():
  fd = runtime.sealed_slot(4096)
  left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
  try:
    assert fcntl.fcntl(fd, runtime.GET_SEALS) == runtime.SEALS
    with pytest.raises(OSError):
      os.ftruncate(fd, 0)
    with mmap.mmap(fd, 4096) as writer:
      writer[:4] = b'BGRX'
      runtime.packet(left, {'type': 'init'}, [fd])
      message, descriptors = runtime.receive(right, 1)
      try:
        assert message == {'type': 'init'}
        assert not os.get_inheritable(descriptors[0])
        with mmap.mmap(descriptors[0], 4096, access=mmap.ACCESS_READ) as reader:
          assert reader[:4] == b'BGRX'
      finally:
        os.close(descriptors[0])
  finally:
    os.close(fd)
    left.close()
    right.close()


@pytest.mark.parametrize('payload', [b'[]', b'{', b'{"type":7}', b'{"type":"x","pad":"' + b'x' * 4096 + b'"}'],
                         ids=['array', 'invalid-json', 'invalid-type', 'oversized'])
def test_malformed_or_truncated_packets_are_rejected(payload):
  left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
  try:
    left.send(payload)
    with pytest.raises(ValueError):
      runtime.receive(right)
  finally:
    left.close()
    right.close()


def test_unexpected_descriptor_is_closed():
  left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
  fd = runtime.sealed_slot(4096)
  before = len(os.listdir('/proc/self/fd'))
  try:
    left.sendmsg([b'{"type":"x"}'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [fd]))])
    with pytest.raises(ValueError):
      runtime.receive(right)
    assert len(os.listdir('/proc/self/fd')) == before
  finally:
    os.close(fd)
    left.close()
    right.close()


@pytest.mark.parametrize('values', [(True, 600, 20), (1601, 600, 20), (1440, -1, 20), (1440, 650, 31), (1440, 650, 0)])
def test_geometry_is_bounded(values):
  with pytest.raises(ValueError):
    runtime.geometry(*values)


def test_transient_launcher_has_no_host_data_or_display_privileges():
  command = runtime.launch_command('arabesque-firefox-test', 'test', 1440, 650, 20, 'shm')
  assert command[:6] == ['sudo', '-n', '/usr/bin/timeout', '--kill-after=1', '15', '/usr/bin/systemd-run']
  assert '--property=PrivateTmp=yes' in command
  assert '--property=ProtectSystem=strict' in command
  assert not any(part.startswith('--property=ProtectKernelTunables=') for part in command)
  binds = next(part for part in command if part.startswith('--property=BindReadOnlyPaths='))
  assert f'{runtime.RUNTIME}/isolation/devices:/dev' in binds
  assert all(f'{runtime.RUNTIME}/isolation/empty:{path}' in binds for path in ('/home', '/root', '/run/user'))
  assert '/sys /proc/sys ' in binds
  assert ('--property=TemporaryFileSystem=/data:ro /persist:ro /mnt:ro /media:ro /cache:ro /rwtmp:ro /var:ro '
          + '/dev/shm:rw,nosuid,nodev,noexec,mode=1777') in command
  assert '--property=CPUAffinity=0-5' in command
  assert '--property=KillMode=mixed' in command
  assert '--property=Restart=no' in command
  assert '--property=WatchdogSec=4' in command and '--property=LimitNPROC=1024' in command
  assert '--reuid=61234' in command and '--clear-groups' in command and '--no-new-privs' in command
  assert not any('NO_SANDBOX' in part or 'disable-sandbox' in part for part in command)


def test_first_use_preparer_is_temporary_supervised_and_resource_limited():
  command = runtime.preparation_command('arabesque-firefox-test', 'test')
  assert '--collect' in command
  assert '--property=WatchdogSec=4' in command
  assert '--property=RuntimeMaxSec=900' in command
  assert '--property=CapabilityBoundingSet=CAP_CHOWN' in command
  assert f'--property=ExecStartPre=-+/usr/bin/mkdir -m 0755 {runtime.ROOT}' in command
  assert '--property=ProtectSystem=strict' in command
  assert '--property=ReadWritePaths=/data' in command
  assert '--property=CPUAffinity=0-5' in command
  assert '--property=Nice=10' in command and '--property=MemoryMax=1G' in command


@pytest.mark.parametrize('cancel', [False, True])
def test_first_use_prepares_without_frames_and_waits_before_launching(tmp_path, monkeypatch, cancel):
  root = tmp_path / 'firefox'
  monkeypatch.setattr(runtime, 'ROOT', root)
  monkeypatch.setattr(runtime, 'RUNTIME', root / 'runtime')
  monkeypatch.setattr(runtime, 'STATE', root / 'state')
  monkeypatch.setattr(runtime.BrowserSession, 'pending_stop', None)
  launch = Mock(return_value=['prepare'])
  monkeypatch.setattr(runtime, 'preparation_command', launch)
  monkeypatch.setattr(runtime.subprocess, 'Popen', Mock())
  monkeypatch.setattr(runtime, 'stop_unit', lambda *args: None)
  monkeypatch.setattr(runtime, 'credentials', lambda _: (os.getpid(), 0, 0))
  monkeypatch.setattr(runtime, 'sealed_slot', Mock(side_effect=AssertionError('Frames allocated before preparation')))
  session = runtime.BrowserSession(1440, 650, 20)
  client = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
  client.settimeout(2)
  try:
    assert not session.error and session._preparing and not session.buffers
    launch.assert_called_once()
    client.connect(session._listener.getsockname())
    session.poll()
    assert runtime.receive(client)[0] == {'type': 'prepare'}
    runtime.packet(client, {'type': 'status', 'message': 'Downloading Firefox… 50%'})
    session.poll()
    assert session.status == 'Downloading Firefox… 50%'
    runtime.packet(client, {'type': 'prepared'})
    session.poll()
    start = Mock()
    monkeypatch.setattr(session, '_start', start)
    session.poll()
    start.assert_not_called()
    if cancel:
      session.close()
    session.stopped.set()
    session.poll()
    assert start.call_count == (0 if cancel else 1)
  finally:
    client.close()
    session.close()


def test_prepared_runtime_does_not_start_preparation(tmp_path, monkeypatch):
  root = tmp_path / 'firefox'
  app = root / 'runtime/firefox/firefox'
  app.parent.mkdir(parents=True)
  app.write_bytes(b'firefox')
  (root / 'runtime/ready.json').write_text('{}')
  (root / 'state').mkdir()
  for path in (root, root / 'runtime', app, root / 'state'):
    path.chmod(0o700 if path == root / 'state' else 0o755)
  owners = {root: 0, root / 'runtime': 0, root / 'state': runtime.BROWSER_UID, app: 0}
  original_stat = runtime.Path.stat

  def stat(path, *args, **kwargs):
    info = original_stat(path, *args, **kwargs)
    if path in owners:
      values = list(info)
      values[4] = owners[path]
      return os.stat_result(values)
    return info

  monkeypatch.setattr(runtime.Path, 'stat', stat)
  monkeypatch.setattr(runtime, 'ROOT', root)
  monkeypatch.setattr(runtime, 'RUNTIME', root / 'runtime')
  monkeypatch.setattr(runtime, 'STATE', root / 'state')
  monkeypatch.setattr(runtime.BrowserSession, 'pending_stop', None)
  prepare, launch = Mock(), Mock(return_value=['browser'])
  monkeypatch.setattr(runtime, 'preparation_command', prepare)
  monkeypatch.setattr(runtime, 'launch_command', launch)
  monkeypatch.setattr(runtime.subprocess, 'Popen', Mock())
  monkeypatch.setattr(runtime, 'stop_unit', lambda *args: None)
  session = runtime.BrowserSession(1440, 650, 20)
  try:
    assert not session.error and not session._preparing and len(session.buffers) == 2
    prepare.assert_not_called()
    launch.assert_called_once()
  finally:
    session.close()


@pytest.mark.parametrize('finish', ['success', 'close', 'eof', 'lease'])
def test_preparation_progress_completion_and_owner_cleanup(monkeypatch, finish):
  client, worker = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
  client.settimeout(3)
  connection = Mock(wraps=worker)
  connection.connect = Mock()
  setup, complete, installer_finished = Mock(), Event(), Event()

  def prepare():
    try:
      setup.report('Downloading Firefox… 50%')
      complete.wait(3)
      setup.report('Prepared')
    finally:
      installer_finished.set()

  setup.prepare.side_effect = prepare
  monkeypatch.setattr(runtime.socket, 'socket', Mock(return_value=connection))
  monkeypatch.setattr(runtime.signal, 'signal', Mock())
  monkeypatch.setattr(runtime, 'credentials', lambda _: (os.getpid(), os.getuid(), os.getgid()))
  monkeypatch.setattr(runtime, 'notify', Mock())
  monkeypatch.setattr(runtime, 'LEASE_SECONDS', 0.15)
  monkeypatch.setattr(runtime.sys, 'argv', ['prepare', 'address', str(os.getuid()), str(os.getpid())])
  monkeypatch.setattr(runtime.importlib.util, 'spec_from_file_location', Mock(return_value=Mock(loader=Mock())))
  monkeypatch.setattr(runtime.importlib.util, 'module_from_spec', Mock(return_value=setup))
  runtime.packet(client, {'type': 'prepare'})
  thread = Thread(target=runtime.preparation_main, daemon=True)
  try:
    thread.start()
    message, _ = runtime.receive(client)
    assert message['type'] == 'status'
    if finish == 'success':
      complete.set()
      while message['type'] == 'status':
        message, _ = runtime.receive(client)
      assert message == {'type': 'prepared'}
    elif finish == 'close':
      runtime.packet(client, {'type': 'close'})
    elif finish == 'eof':
      client.close()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert setup.ROOT == runtime.ROOT
    runtime.notify.assert_any_call('READY=1\nWATCHDOG=1')
  finally:
    complete.set()
    thread.join(timeout=3)
    assert installer_finished.wait(1)
    client.close()
    worker.close()


def test_take_latest_frame_releases_old_slot_after_bounded_handoff():
  session = runtime.BrowserSession.__new__(runtime.BrowserSession)
  session._frames, session.buffers, session.release = [0, 1], [b'old', b'new'], Mock()
  session.ready = True
  assert session.take_frame() == (1, b'new')
  session.release.assert_called_once_with(0)
  assert session.take_frame() is None


def test_input_is_bounded_and_modifiers_are_explicit():
  x, held = Mock(), set()
  runtime.inject(x, {'type': 'input', 'event': 'motion', 'a': 3, 'b': 9}, held, 1440, 650)
  x.motion.assert_called_once_with(3, 9)
  runtime.inject(x, {'type': 'input', 'event': 'key', 'a': 0x61, 'b': 1}, held, 1440, 650)
  x.key.assert_called_once_with(0x61, ctrl=True, alt=False, shift=False)
  runtime.inject(x, {'type': 'input', 'event': 'button', 'a': 1, 'b': True}, held, 1440, 650)
  assert held == {1}
  for event, a, b in (('motion', 1440, 0), ('motion', -1, 0), ('button', 7, True), ('button', 1, 1), ('key', 0x61, 8)):
    with pytest.raises(ValueError):
      runtime.inject(x, {'type': 'input', 'event': event, 'a': a, 'b': b}, held, 1440, 650)


@pytest.fixture
def tool(monkeypatch):
  monkeypatch.setattr(browser, 'device', NS(awake=True))
  monkeypatch.setattr('openpilot.system.ui.widgets.device', NS(awake=True))
  monkeypatch.setattr(gui_app, '_mouse_events', [])
  for key in ('get_key_pressed', 'get_char_pressed'):
    monkeypatch.setattr(rl, key, lambda: 0)
  monkeypatch.setattr(rl, 'set_exit_key', Mock())
  monkeypatch.setattr(browser, 'gui_label', Mock())
  for key in ('draw_rectangle_rec', 'draw_rectangle_rounded', 'draw_circle_lines'):
    monkeypatch.setattr(rl, key, Mock())
  sessions = []

  def create(width, height, fps):
    session = Mock(width=width, height=height, fps=fps, ready=True, error='', status='shm')
    session.stopped = Event()
    session.stopped.set()
    sessions.append(session)
    return session

  create.pending_stop = None
  monkeypatch.setattr(browser, 'BrowserSession', create)
  permitted = Mock(return_value=True)
  view = browser.Browser(permitted)
  view.set_rect(rl.Rectangle(0, 104, 2160, 976))
  yield NS(view=view, sessions=sessions, permitted=permitted)
  view.hide_event()


def touch(view, x, y, *, pressed=False, released=False):
  gui_app._mouse_events = [MouseEvent(MousePos(x, y), 0, pressed, released, pressed, 0)]
  Widget.render(view)


def test_loading_status_and_pan_controls_have_readable_labels(tool):
  view = tool.view
  view.show_event()
  tool.sessions[0].status = 'Downloading Firefox… 50%'
  view._keyboard = True
  view._update_layout_rects()
  view._render(view.rect)
  labels = [call.args[1] for call in browser.gui_label.call_args_list]
  assert labels[0] == 'Downloading Firefox... 50%'
  assert 'Up' in labels and 'Down' in labels


def test_no_runtime_until_open_and_none_after_close_or_sleep(tool):
  view, sessions = tool.view, tool.sessions
  assert sessions == []
  view.show_event()
  first = sessions[0]
  view.poll_runtime(True)
  first.poll.assert_called_once_with()
  view.poll_runtime(False)
  first.close.assert_called_once()
  assert view._session is None and view._texture is None and view._shader is None
  view.poll_runtime(False)
  assert len(sessions) == 1
  view.poll_runtime(True)
  assert len(sessions) == 2
  view.hide_event()
  sessions[1].close.assert_called_once()
  view.hide_event()
  sessions[1].close.assert_called_once()
  assert view._prepare not in gui_app._render_prepare


def test_scroll_is_not_a_click_and_pointer_disable_releases(tool):
  view = tool.view
  view.show_event()
  session = tool.sessions[0]
  touch(view, 600, 400, pressed=True)
  assert not any(c.args[0].get('event') == 'button' for c in session.send.call_args_list)
  touch(view, 600, 250)
  touch(view, 600, 250, released=True)
  buttons = [c.args[0] for c in session.send.call_args_list if c.args[0].get('event') == 'button']
  assert buttons and all(p['a'] in (4, 5) for p in buttons)
  session.send.reset_mock()
  view._pointer = True
  touch(view, 600, 400, pressed=True)
  assert any(c.args[0] == {'type': 'input', 'event': 'button', 'a': 1, 'b': True} for c in session.send.call_args_list)
  view.set_enabled(False)
  session.reset_input.assert_called_once()
  touch(view, 600, 400, released=True)
  assert view._gesture is None


def test_keyboard_geometry_pans_without_distorting_or_mapping_chrome(tool):
  view = tool.view
  view.show_event()
  assert view._point(MousePos(100, 120)) is None
  factor = view._factor
  view._keyboard = True
  view._update_layout_rects()
  assert view._factor == factor
  assert view._point(MousePos(100, 1000)) is None
  view._scroll_y = 10000
  view._update_layout_rects()
  assert 0 < view._scroll_y < view._session.height


def test_fast_wake_waits_for_old_process_group_and_keeps_geometry(tool):
  view = tool.view
  view.show_event()
  old = tool.sessions[0]
  height = old.height
  view._keyboard = True
  view._update_layout_rects()
  old.stopped.clear()
  view.poll_runtime(False)
  view.poll_runtime(True)
  assert len(tool.sessions) == 1 and view._session is None
  old.stopped.set()
  view.poll_runtime(True)
  assert len(tool.sessions) == 2 and tool.sessions[-1].height == height


def test_new_browser_waits_for_previous_widget_cleanup(tool):
  tool.view.show_event()
  old = tool.sessions[0]
  old.stopped.clear()
  old.close.side_effect = lambda: setattr(browser.BrowserSession, 'pending_stop', old.stopped)
  tool.view.hide_event()
  view = browser.Browser(tool.permitted)
  view.set_rect(rl.Rectangle(0, 104, 2160, 976))
  try:
    view.show_event()
    view.poll_runtime(True)
    assert len(tool.sessions) == 1 and view._session is None
    old.stopped.set()
    view.poll_runtime(True)
    assert len(tool.sessions) == 2 and view._session is tool.sessions[-1]
  finally:
    view.hide_event()


def test_failed_frame_release_does_not_return_a_closed_mapping():
  session = runtime.BrowserSession.__new__(runtime.BrowserSession)
  session._frames, session.buffers, session.ready = [0, 1], [b'old', b'new'], True

  def disconnect(slot):
    session.ready = False
    session.buffers = []

  session.release = Mock(side_effect=disconnect)
  assert session.take_frame() is None


def test_stop_command_and_launcher_are_reaped_even_on_failure(monkeypatch):
  stopped, launcher = Event(), Mock()
  monkeypatch.setattr(runtime.subprocess, 'run', Mock(side_effect=OSError('supervisor unavailable')))
  runtime.stop_unit('arabesque-firefox-test', launcher, stopped)
  launcher.wait.assert_called_once_with(timeout=12)
  assert stopped.is_set()


def test_firefox_quits_cleanly_before_using_signals(monkeypatch):
  process, x = Mock(), Mock()
  process.poll.side_effect = [None, None, 0, 0]
  monkeypatch.setattr(runtime.time, 'sleep', Mock())
  runtime.stop_firefox(process, x)
  x.key.assert_called_once_with(ord('q'), ctrl=True)
  process.terminate.assert_not_called()


@pytest.mark.parametrize('broken_display', [True, False])
def test_firefox_stop_still_forces_exit_on_display_error_or_hang(monkeypatch, broken_display):
  process, x = Mock(), Mock()
  process.poll.return_value = None
  if broken_display:
    x.key.side_effect = RuntimeError('X display closed')
  monkeypatch.setattr(runtime.time, 'monotonic', Mock(side_effect=[0, 2]))
  runtime.stop_firefox(process, x)
  process.terminate.assert_called_once()
  process.wait.assert_called_once_with(timeout=1)


def test_tab_probe_uses_cgroup_without_proc_children_and_matches_parent(tmp_path, monkeypatch):
  proc = tmp_path / 'proc'
  roles = {10: ('firefox', b'firefox\0'), 20: ('forkserver', b'firefox -contentproc forkserver\0'),
           30: ('file:// Content', b'firefox -contentproc -isForBrowser -parentPid 10 5 tab\0')}
  for pid, (name, command) in roles.items():
    base = proc / str(pid)
    base.mkdir(parents=True)
    (base / 'cmdline').write_bytes(command)
    (base / 'status').write_text(f'Name:\t{name}\nUid:\t{os.getuid()}\nSeccomp:\t2\nNoNewPrivs:\t1\nCapEff:\t0000\n')
  (proc / '10/cgroup').write_text('0::/test.service\n')
  cgroup = tmp_path / 'cgroup'
  (cgroup / 'test.service').mkdir(parents=True)
  (cgroup / 'test.service/cgroup.procs').write_text('10\n20\n30\n')
  real_path = runtime.Path

  def fake_path(path):
    if str(path).startswith('/proc/'):
      return proc / str(path)[6:]
    return cgroup if str(path) == '/sys/fs/cgroup' else real_path(path)

  monkeypatch.setattr(runtime, 'Path', fake_path)
  assert runtime.content_sandboxed(10)
  (proc / '30/status').write_text(f'Name:\tfile:// Content\nUid:\t{os.getuid()}\nSeccomp:\t2\nCapEff:\t0000\n')
  monkeypatch.setattr(runtime, 'no_new_privileges', lambda: 0)
  assert not runtime.content_sandboxed(10)
  monkeypatch.setattr(runtime, 'no_new_privileges', lambda: 1)
  assert runtime.content_sandboxed(10)
  (proc / '30/cmdline').write_bytes(b'firefox -contentproc -isForBrowser -parentPid 11 5 tab\0')
  assert not runtime.content_sandboxed(10)
  (proc / '30/cmdline').write_bytes(b'firefox -contentproc -parentPid 10 5 utility\0')
  assert not runtime.content_sandboxed(10)


def test_browser_poll_follows_fresh_state_before_any_render():
  path = browser.__file__
  from pathlib import Path
  path = Path(path).parents[3] / 'ui.py'
  tree = ast.parse(path.read_text())
  tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'update_frame']
  events = []
  namespace: dict = {'gui_app': NS(measure_frame_phase=lambda _, callback: callback()), 'ui_state': NS(update=lambda: events.append('state'))}
  exec(compile(ast.fix_missing_locations(tree), str(path), 'exec'), namespace)
  namespace['update_frame'](arabesque=lambda: events.append('browser'))
  assert events == ['state', 'browser']


def test_diagnostic_entry_cannot_start_without_fresh_offroad(monkeypatch):
  authority = Mock()
  authority.offroad.return_value = False
  monkeypatch.setitem(sys.modules, 'openpilot.common.params', NS(Params=Mock()))
  monkeypatch.setitem(sys.modules, 'openpilot.starpilot.galaxy.settings', NS(LiveContextSource=Mock(return_value=authority)))
  monkeypatch.setattr(sys, 'argv', [runtime.__file__, '--seconds', '1'])
  monkeypatch.setattr(sys, 'path', list(sys.path))
  launch = Mock()
  monkeypatch.setattr(runtime.subprocess, 'Popen', launch)
  with pytest.raises(SystemExit, match='fresh off-road authority'):
    runpy.run_path(runtime.__file__, run_name='__main__')
  launch.assert_not_called()
  authority.close.assert_called_once()


def test_wake_touch_and_revoked_authority_never_inject(tool):
  view = tool.view
  view.show_event()
  view.poll_runtime(False)
  view.poll_runtime(True)
  touch(view, 600, 400, pressed=True)
  assert view._gesture is None
  assert not tool.sessions[-1].send.called
  tool.permitted.return_value = False
  view.poll_runtime(True)
  assert view._session is None
  tool.sessions[-1].close.assert_called_once()


def test_commit_exact_unicode_without_terminal_normalization(tool):
  view = tool.view
  view.show_event()
  view._text('é€\u0301😀')
  assert [c.args[0]['a'] for c in tool.sessions[0].send.call_args_list] == [0xe9, 0x010020ac, 0x01000301, 0x0101f600]


@pytest.mark.skipif(os.environ.get('ARABESQUE_GPU_TEST') != '1', reason='Needs a disposable Xvfb with GLX')
def test_browser_status_and_pan_labels_have_actual_font_glyphs(monkeypatch):
  from openpilot.system.ui.lib import text_measure
  from openpilot.system.ui.lib.application import font_fallback, multilang

  monkeypatch.setattr(text_measure, '_cache', text_measure.LRUCache(1024))
  monkeypatch.setattr(gui_app, '_fonts', {})
  monkeypatch.setattr(gui_app, '_fallback_fonts', {})
  monkeypatch.setattr(rl, '_orig_draw_text_ex', rl.draw_text_ex, raising=False)
  monkeypatch.setattr(rl, 'draw_text_ex', rl.draw_text_ex)
  rl.init_window(1080, 488, 'Firefox status font check')
  try:
    gui_app._load_fonts()
    gui_app._patch_text_functions()
    view = browser.Browser(lambda: True)
    view.set_rect(rl.Rectangle(0, 0, 1080, 488))
    view._session = Mock(width=1440, height=650, error='', status='Downloading Firefox… 50%')
    view._keyboard = True
    view._update_layout_rects()
    draw_label = browser.gui_label
    labels = []

    def record_label(rect, text, *args, **kwargs):
      labels.append(text)
      draw_label(rect, text, *args, **kwargs)

    monkeypatch.setattr(browser, 'gui_label', record_label)
    for language in ('en', 'ja', 'ko', 'th', 'zh-CHS', 'zh-CHT'):
      monkeypatch.setattr(multilang, '_language', language)
      labels.clear()
      rl.begin_drawing()
      try:
        view._render(view.rect)
      finally:
        rl.end_drawing()
      font = font_fallback(gui_app.font(browser.DEFAULT_THEME.font_weight))
      for text in labels:
        for character in set(text):
          index = rl.get_glyph_index(font, ord(character))
          assert font.glyphs[index].value == ord(character), f'{language}: missing {character!r} in {text!r}'
      for bounds, text, key in view._buttons:
        if key in ('pan-up', 'pan-down'):
          assert text_measure.measure_text_cached(font, text, round(28 * view._scale)).x <= bounds.width
  finally:
    for font in (*gui_app._fonts.values(), *gui_app._fallback_fonts.values()):
      rl.unload_font(font)
    rl.close_window()


@pytest.mark.skipif(os.environ.get('ARABESQUE_GPU_TEST') != '1', reason='Needs a disposable Xvfb with GLX')
def test_real_texture_swizzle_alpha_and_reuse():
  rl.init_window(320, 240, 'Arabesque frame check')
  view = browser.Browser(lambda: True)
  fd = runtime.sealed_slot(320 * 240 * 4)
  buffer = mmap.mmap(fd, 320 * 240 * 4)
  session = Mock(ready=True, width=320, height=240, error='')
  session.take_frame.return_value = (0, buffer)
  view._session = session
  try:
    texture_id = None
    for colors in ((0xff0000, 0x00ff00, 0x0000ff, 0xffffff), (0xffffff, 0x0000ff, 0x00ff00, 0xff0000)):
      row = b''.join(color.to_bytes(4, 'little') * 80 for color in colors)
      buffer[:] = row * 240
      view._prepare()
      assert not session.fail.called
      assert view._texture is not None
      if texture_id is not None:
        assert view._texture.id == texture_id
      texture_id = view._texture.id
      rl.begin_drawing()
      rl.clear_background(rl.BLACK)
      rl.begin_shader_mode(view._shader)
      bounds = rl.Rectangle(0, 0, 320, 240)
      rl.draw_texture_pro(view._texture, bounds, bounds, rl.Vector2(0, 0), 0, rl.WHITE)
      rl.end_shader_mode()
      image = rl.load_image_from_screen()
      try:
        for i, expected in enumerate(colors):
          actual = rl.get_image_color(image, i * 80 + 40, 120)
          assert (actual.r, actual.g, actual.b, actual.a) == (expected >> 16, expected >> 8 & 255, expected & 255, 255)
      finally:
        rl.unload_image(image)
        rl.end_drawing()
    assert session.release.call_count == 2
  finally:
    view.hide_event()
    buffer.close()
    os.close(fd)
    rl.close_window()
