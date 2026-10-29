import json
import stat
import struct
from pathlib import Path
from unittest.mock import Mock

import pytest

from openpilot.starpilot.galaxy.hotspot import DEFAULT, HotspotSettings, atomic_json, hotspot_name, validate_config
from openpilot.starpilot.galaxy.hotspot_netlink import WirelessInterfaces, attribute, attributes
from openpilot.starpilot.galaxy.hotspot_worker import (HOLD, KEEP, NM_CONF_TEXT, STANDALONE_SETTLE_S, SUPPLICANT_QUIET_S,
                                                       SUPPLICANT_WAIT_S, HotspotBackend, HotspotController, choose_channel,
                                                       hostapd_config, nm_activating, overlapping_routes, radio_channel, read_onroad,
                                                       steady_results)

CONFIG = {'enabled': True, 'ssid': 'TheGalaxy-6b86', 'password': '1234567890123456'}
DONGLE = 'b0c4a280b2f96b86'


def backend_mock(ready=True, ap_channel=None):
  backend = Mock()
  backend.alive.return_value = True
  backend.ap_status.return_value = {'ready': ready, 'channel': ap_channel}
  backend.activating.return_value = False
  backend.supplicant_holds.return_value = False
  backend.connected = set()
  return backend


def quiet_backend(tmp_path, **kwargs):
  """A backend whose NetworkManager rule, supplicant sockets and clock live in tmp_path."""
  now = [0.]
  def sleep(seconds):
    now[0] += seconds
  (tmp_path / 'sockets').mkdir(exist_ok=True)
  return HotspotBackend(tmp_path, nm_conf=tmp_path / 'conf.d' / 'zz.conf', sockets=tmp_path / 'sockets',
                        clock=lambda: now[0], sleep=sleep, **kwargs)


@pytest.mark.parametrize('change', [{'enabled': 1}, {'ssid': 'bad\nssid'}, {'password': 'short'},
                                  {'password': 'has spaces in it'}, {'extra': True}, {'password': 'é' * 12}])
def test_strict_settings(change):
  with pytest.raises(ValueError):
    validate_config({**CONFIG, **change})


def test_settings_revision_permissions_and_credentials(tmp_path):
  settings = HotspotSettings(tmp_path, tmp_path / 'status', clock=lambda: 100, dongle_id=lambda: DONGLE)
  assert settings.read() == {**DEFAULT, 'ssid': 'TheGalaxy-6b86'}
  initial = settings.snapshot(True)
  payload = {'revision': initial['revision'], 'config': {**initial['config'], 'enabled': True}}
  with pytest.raises(PermissionError):
    settings.save(payload, lambda: False)
  assert not settings.path.exists()
  saved = settings.save(payload, lambda: True)
  assert len(saved['config']['password']) == 24
  assert stat.S_IMODE(settings.path.stat().st_mode) == 0o600
  with pytest.raises(FileExistsError):
    settings.save(payload, lambda: True)
  unchanged = settings.save({'revision': saved['revision'], 'config': {**saved['config'], 'password': ''}}, lambda: True)
  assert unchanged['config'] == saved['config']
  runtime = {'revision': saved['revision'], 'updated': 99, 'active': True, 'state': 'active', 'reason': '', 'channel': 149}
  atomic_json(settings.status_path, runtime)
  assert settings.snapshot(False)['active']
  assert not settings.snapshot(False)['editable']
  for updates in ({'updated': 80}, {'updated': 101}, {'revision': 'wrong'}):
    atomic_json(settings.status_path, {**runtime, **updates})
    assert settings.snapshot(True)['state'] == 'unavailable'


def test_settings_reject_symlink_and_oversize(tmp_path):
  settings = HotspotSettings(tmp_path, tmp_path / 'status', dongle_id=lambda: DONGLE)
  target = tmp_path / 'elsewhere'
  target.write_text(json.dumps(CONFIG))
  settings.path.symlink_to(target)
  with pytest.raises(OSError):
    settings.read()
  settings.path.unlink()
  settings.path.write_text(' ' * 4097)
  with pytest.raises(ValueError):
    settings.read()


def test_fixed_name_migration_password_and_restart(tmp_path):
  settings = HotspotSettings(tmp_path, dongle_id=lambda: DONGLE)
  atomic_json(settings.path, {**CONFIG, 'ssid': 'Old custom name'})
  assert settings.read() == CONFIG
  current = settings.snapshot(True)
  with pytest.raises(ValueError, match='fixed'):
    settings.save({'revision': current['revision'], 'config': {**CONFIG, 'ssid': 'Other name'}}, lambda: True)
  custom = {**CONFIG, 'password': 'my-new-password-123'}
  settings.save({'revision': current['revision'], 'config': custom}, lambda: True)
  restarted = HotspotSettings(tmp_path, dongle_id=lambda: DONGLE)
  assert restarted.read() == custom
  assert hotspot_name(DONGLE.upper()) == 'TheGalaxy-6b86'


@pytest.mark.parametrize('dongle', [None, '', 'UnregisteredDevice', '1234', 'x' * 16, b'0123456789abcdef'])
def test_unregistered_name_is_not_invented(dongle):
  with pytest.raises(ValueError, match='dongle ID'):
    hotspot_name(dongle)


@pytest.mark.parametrize('status,expected', [('wpa_state=COMPLETED\nfreq=5745', ('a', 149)),
  ('wpa_state=COMPLETED\nfreq=2412', ('g', 1)), ('wpa_state=DISCONNECTED\nfreq=5745', ('g', 6)),
  ('wpa_state=INACTIVE', ('g', 6)), ('wpa_state=SCANNING', ('g', 6)),
  ('wpa_state=ASSOCIATING', HOLD), ('wpa_state=4WAY_HANDSHAKE\nfreq=5745', HOLD),
  ('wpa_state=INTERFACE_DISABLED', None), ('FAIL', None),
  ('wpa_state=COMPLETED\nfreq=6000', None)])
def test_channel(status, expected):
  assert radio_channel(status) == expected


def test_automatic_standalone_connected_and_back():
  now = [100.]
  backend = backend_mock()
  controller = HotspotController(backend, clock=lambda: now[0])
  for status, expected in [('DISCONNECTED', ('g', 6)), ('COMPLETED\nfreq=5745', ('a', 149)), ('DISCONNECTED', ('g', 6))]:
    backend.channel.return_value = radio_channel('wpa_state=' + status)
    assert controller.tick(CONFIG)['state'] == 'starting'
    backend.start.assert_called_with(CONFIG, expected)
    assert controller.tick(CONFIG)['active']
    now[0] += STANDALONE_SETTLE_S + 1
  assert backend.start.call_count == 3
  assert controller.tick({**CONFIG, 'enabled': False})['state'] == 'disabled'


@pytest.mark.parametrize('results,expected', [
  ([('a', 149)], ('a', 149)), ([('g', 6)], ('g', 6)), ([None], None), ([HOLD, ('a', 149)], HOLD),
  ([('a', 149), HOLD], HOLD), ([('g', 1), ('a', 149)], ('g', 1)), ([('g', 6), ('a', 149)], ('a', 149)),
  ([None, ('a', 149)], ('a', 149)), ([('g', 6), None], ('g', 6))])
def test_choose_channel(results, expected):
  assert choose_channel(results) == expected


@pytest.mark.parametrize('state,expected', [('30 (disconnected)', False), ('50 (connecting (configuring))', True),
  ('60 (connecting (need authentication))', True), ('100 (connected)', False), ('', False), ('junk', False)])
def test_nm_activating(state, expected):
  assert nm_activating(state) == expected


def test_join_leaves_running_ap_alone():
  now = [100.]
  backend = backend_mock(ap_channel=1)
  controller = HotspotController(backend, clock=lambda: now[0])
  backend.channel.return_value = ('g', 1)
  controller.tick(CONFIG)
  assert controller.tick(CONFIG)['active']
  backend.start.reset_mock()
  backend.stop.reset_mock()
  # Android Auto drops home Wi-Fi, scans, associates and joins the car on channel 149.
  for channel in (('g', 6), HOLD, ('g', 6), HOLD):
    backend.channel.return_value = channel
    now[0] += 2
    assert controller.tick(CONFIG)['active']
  backend.stop.assert_not_called()
  backend.start.assert_not_called()
  backend.ap_status.return_value = {'ready': True, 'channel': 149}
  backend.channel.return_value = ('a', 149)
  assert controller.tick(CONFIG)['channel'] == 149
  backend.stop.assert_not_called()
  backend.start.assert_not_called()
  # Only a station gone for good moves the AP to its standalone channel.
  backend.channel.return_value = ('g', 6)
  now[0] += STANDALONE_SETTLE_S - 1
  assert controller.tick(CONFIG)['active']
  backend.start.assert_not_called()
  now[0] += 2
  assert controller.tick(CONFIG)['state'] == 'starting'
  backend.start.assert_called_once_with(CONFIG, ('g', 6))


def test_read_onroad(tmp_path):
  param = tmp_path / 'IsOnroad'
  assert not read_onroad(param)
  param.write_bytes(b'1')
  assert read_onroad(param)
  param.write_bytes(b'0')
  assert not read_onroad(param)


def test_hold_does_not_start_ap():
  backend = backend_mock()
  backend.channel.return_value = HOLD
  controller = HotspotController(backend, clock=lambda: 100)
  assert controller.tick(CONFIG)['state'] == 'waiting'
  backend.start.assert_not_called()
  backend.stop.assert_not_called()


def test_backend_channel_reports_idle_stations_and_asks_networkmanager_only_for_them(tmp_path):
  def command(args, **kwargs):
    if args[0] == 'nmcli':
      return Mock(returncode=0, stdout='50 (connecting (configuring))\n')
    return Mock(returncode=0, stdout='wpa_state=DISCONNECTED\n')
  run = Mock(side_effect=command)
  backend = HotspotBackend(tmp_path, run=run, interfaces=Mock())
  assert backend.channel() == ('g', 6) and backend.idle == ['wlan0']
  assert all(call.args[0][0] != 'nmcli' for call in run.call_args_list)
  assert backend.activating()
  run.side_effect = lambda args, **kwargs: Mock(returncode=0, stdout='wpa_state=COMPLETED\nfreq=5745')
  assert backend.channel() == ('a', 149) and backend.connected == {149}
  assert not backend.activating()
  assert all(call.args[0][-1] in ('status', 'wlan0') for call in run.call_args_list)


def test_backend_skips_car_station_without_status(tmp_path, monkeypatch):
  monkeypatch.setattr(Path, 'exists', lambda self: True)
  def command(args, **kwargs):
    if args[2] == 'aa0':
      assert kwargs['check'] is False
      return Mock(returncode=255, stdout='Failed to connect to non-global ctrl_ifname: aa0')
    return Mock(returncode=0, stdout='wpa_state=COMPLETED\nfreq=2412')
  backend = HotspotBackend(tmp_path, run=Mock(side_effect=command), interfaces=Mock())
  assert backend.channel() == ('g', 1)


def test_networkmanager_join_holds_the_running_ap():
  now = [100.]
  backend = backend_mock(ap_channel=1)
  controller = HotspotController(backend, clock=lambda: now[0])
  backend.channel.return_value = ('g', 1)
  controller.tick(CONFIG)
  backend.start.reset_mock()
  backend.channel.return_value = ('g', 6)
  now[0] += STANDALONE_SETTLE_S + 1
  backend.activating.return_value = True
  assert controller.tick(CONFIG)['active']
  backend.start.assert_not_called()
  backend.activating.reset_mock()
  backend.channel.return_value = ('g', 1)
  backend.activating.return_value = False
  controller.tick(CONFIG)
  backend.activating.assert_not_called()  # nothing to change, so nothing to ask


def test_ap_moved_by_the_driver_to_another_station_stays_there():
  backend = backend_mock(ap_channel=36)
  controller = HotspotController(backend, clock=lambda: 100)
  backend.channel.return_value = ('a', 36)
  controller.tick(CONFIG)
  backend.start.reset_mock()
  backend.stop.reset_mock()
  backend.connected = {36, 149}
  backend.ap_status.return_value = {'ready': True, 'channel': 149}
  for _ in range(3):
    assert controller.tick(CONFIG) == {'active': True, 'state': 'active', 'reason': '', 'channel': 149}
  backend.start.assert_not_called()
  backend.stop.assert_not_called()


def test_dfs_channel_that_will_not_start_falls_back_to_standalone():
  now = [100.]
  backend = backend_mock(ready=False)
  controller = HotspotController(backend, clock=lambda: now[0])
  backend.channel.return_value = ('a', 100)
  assert controller.tick(CONFIG)['state'] == 'starting'
  now[0] += 16
  assert controller.tick(CONFIG)['state'] == 'error'
  now[0] += 16
  backend.ap_status.return_value = {'ready': True, 'channel': 6}
  assert controller.tick(CONFIG)['state'] == 'starting'
  backend.start.assert_called_with(CONFIG, ('g', 6))


def test_backend_ap_status(tmp_path):
  run = Mock(return_value=Mock(returncode=0, stdout='state=ENABLED\nchannel=149\n'))
  backend = HotspotBackend(tmp_path, run=run, interfaces=Mock())
  assert backend.ap_status() == {'ready': True, 'channel': 149}
  assert run.call_count == 1
  run.return_value = Mock(returncode=255, stdout='')
  assert backend.ap_status() == {'ready': False, 'channel': None}


def test_routes_and_config():
  assert not overlapping_routes([{'dst': 'default'}, {'dst': '192.168.180.0/24'}, {'dst': '172.31.254.0/24', 'dev': 'galaxy0'}])
  assert overlapping_routes([{'dst': '172.31.0.0/16', 'dev': 'wlan0'}])
  assert overlapping_routes([{'dst': '172.31.254.1', 'dev': 'eth0'}])
  config = hostapd_config(CONFIG, ('a', 149))
  assert 'interface=galaxy0\n' in config and 'channel=149\n' in config and 'wpa=2\n' in config
  assert 'country_code' not in config
  with pytest.raises(ValueError):
    hostapd_config({**CONFIG, 'ssid': 'Galaxy\ninterface=wlan0'}, ('a', 149))


def test_controller_lifecycle_and_channel_recovery():
  backend = backend_mock()
  backend.channel.return_value = ('a', 149)
  now = [100.]
  controller = HotspotController(backend, clock=lambda: now[0])
  assert controller.tick(CONFIG)['state'] == 'starting'
  assert controller.tick(CONFIG)['active']
  backend.start.assert_called_once_with(CONFIG, ('a', 149))
  backend.channel.return_value = ('a', 36)
  assert controller.tick(CONFIG)['state'] == 'error'  # rate limit restarts
  now[0] += 16
  assert controller.tick(CONFIG)['state'] == 'starting'
  backend.start.assert_called_with(CONFIG, ('a', 36))
  backend.channel.return_value = None
  assert controller.tick(CONFIG)['state'] == 'waiting'
  assert controller.applied is None
  assert controller.tick({**CONFIG, 'enabled': False})['state'] == 'disabled'
  backend.stop.assert_called()


def test_controller_readiness_and_failed_child():
  backend = backend_mock(ready=False)
  backend.channel.return_value = ('a', 149)
  now = [0]
  controller = HotspotController(backend, clock=lambda: now[0])
  assert controller.tick(CONFIG)['state'] == 'starting'
  assert controller.tick(CONFIG)['state'] == 'starting'
  now[0] = 16
  assert controller.tick(CONFIG)['state'] == 'error'
  assert controller.applied is None
  now[0] = 32
  backend.start.side_effect = OSError('failed')
  assert controller.tick(CONFIG)['state'] == 'error'
  backend.stop.assert_called()


def test_backend_failure_rolls_back_only_owned_interface(tmp_path):
  run = Mock(return_value=Mock(stdout='[]'))
  interfaces = Mock()
  backend = quiet_backend(tmp_path, run=run, interfaces=interfaces)
  backend.firewall = '/sbin/iptables-legacy'
  def command(args, **kwargs):
    if args[:3] == ['ip', 'address', 'add']:
      raise OSError('failed')
    return Mock(stdout='[]')
  run.side_effect = command
  with pytest.raises(OSError):
    backend.start(CONFIG, ('a', 149))
  interfaces.return_value.create.assert_called_once_with('galaxy0')
  interfaces.return_value.delete.assert_called_once_with('galaxy0')
  commands = [call.args[0] for call in run.call_args_list]
  assert ['nmcli', 'device', 'set', 'galaxy0', 'managed', 'no'] in commands
  assert all('wlan0' not in command and 'p2p0' not in command for command in commands)
  assert not backend.owned


def test_backend_conflict_does_not_create(tmp_path):
  interfaces = Mock()
  backend = HotspotBackend(tmp_path, run=Mock(return_value=Mock(stdout='[{"dst":"172.31.0.0/16"}]')), interfaces=interfaces)
  backend.firewall = '/sbin/iptables-legacy'
  with pytest.raises(RuntimeError):
    backend.start(CONFIG, ('a', 149))
  interfaces.assert_not_called()


def test_netlink_encoding_and_refusal():
  assert attributes(attribute(4, b'galaxy0\0')) == {4: b'galaxy0\0'}
  with pytest.raises(ValueError):
    attributes(b'\x03\x00\x01\x00')
  wireless = WirelessInterfaces.__new__(WirelessInterfaces)
  wireless.interfaces = Mock(return_value={'wlan0': {'type': 2, 'phy': 0, 'index': 1}, 'galaxy0': {'index': 7}})
  wireless.query = Mock()
  wireless.family = 22
  with pytest.raises(RuntimeError):
    wireless.create('galaxy0')
  wireless.query.assert_not_called()
  wireless.delete('galaxy0')
  wireless.query.assert_called_once_with(22, 8, attribute(3, b'\x07\0\0\0'), ack=True)


def test_netlink_new_interface_payloads():
  wireless = WirelessInterfaces.__new__(WirelessInterfaces)
  wireless.interfaces = Mock(return_value={'wlan0': {'type': 2, 'phy': 0, 'index': 1}})
  wireless.query = Mock()
  wireless.family = 22
  wireless.create('galaxy0')
  ap = attribute(1, struct.pack('I', 0)) + attribute(4, b'galaxy0\0') + attribute(5, struct.pack('I', 3))
  wireless.query.assert_called_with(22, 7, ap, ack=True)
  wireless.create('aa0', iftype=2)
  station = attribute(1, struct.pack('I', 0)) + attribute(4, b'aa0\0') + attribute(5, struct.pack('I', 2))
  wireless.query.assert_called_with(22, 7, station, ack=True)


def supplicant_run(holds):
  """Fake commands; holds[0] says whether wpa_supplicant has galaxy0 (busctl GetInterface)."""
  def command(args, **kwargs):
    if args[:2] == ['busctl', 'call'] and args[5] == 'GetInterface':
      if holds[0]:
        return Mock(returncode=0, stdout='o "/fi/w1/wpa_supplicant1/Interfaces/7"\n')
      return Mock(returncode=1, stdout='')
    if args[:2] == ['busctl', 'call'] and args[5] == 'RemoveInterface':
      holds[0] = False
    return Mock(returncode=0, stdout='[]')
  return Mock(side_effect=command)


def commands(run):
  return [call.args[0] for call in run.call_args_list]


def test_networkmanager_rule_is_written_once_and_reloaded(tmp_path):
  run = supplicant_run([False])
  backend = quiet_backend(tmp_path, run=run, interfaces=Mock(), popen=Mock())
  backend.firewall = '/sbin/iptables-legacy'
  backend.start(CONFIG, ('g', 6))
  assert backend.nm_conf.read_text() == NM_CONF_TEXT
  assert 'match-device=interface-name:galaxy0\nmanaged=0\n' in NM_CONF_TEXT
  assert commands(run).count(['nmcli', 'general', 'reload', 'conf']) == 1
  ordered = commands(run)
  assert ordered.index(['nmcli', 'general', 'reload', 'conf']) < ordered.index(['nmcli', 'device', 'set', 'galaxy0', 'managed', 'no'])
  backend.stop()
  backend.start(CONFIG, ('g', 6))
  assert commands(run).count(['nmcli', 'general', 'reload', 'conf']) == 1  # unchanged rule, no second reload
  assert all('wlan0' not in command for command in commands(run))


def test_hostapd_waits_until_supplicant_lets_go(tmp_path):
  holds = [True]
  run = supplicant_run(holds)
  popen = Mock()
  backend = quiet_backend(tmp_path, run=run, interfaces=Mock(), popen=popen)
  backend.firewall = '/sbin/iptables-legacy'
  clock_at_start = backend.clock()
  real_sleep = backend.sleep
  def sleep(seconds):
    real_sleep(seconds)
    if backend.clock() - clock_at_start > 0.5:
      holds[0] = False  # NetworkManager's `managed no` removed it on its own
  backend.sleep = sleep
  backend.start(CONFIG, ('g', 6))
  assert popen.call_count == 2
  assert not any(command[5:6] == ['RemoveInterface'] for command in commands(run) if command[0] == 'busctl')
  assert backend.clock() - clock_at_start >= 0.5 + SUPPLICANT_QUIET_S


def test_lingering_supplicant_interface_is_removed_before_hostapd(tmp_path):
  holds = [True]
  run = supplicant_run(holds)
  popen = Mock(side_effect=lambda *args, **kwargs: (assert_free(holds), Mock())[1])
  backend = quiet_backend(tmp_path, run=run, interfaces=Mock(), popen=popen)
  backend.firewall = '/sbin/iptables-legacy'
  backend.start(CONFIG, ('g', 6))
  removes = [command for command in commands(run) if command[:2] == ['busctl', 'call'] and command[5] == 'RemoveInterface']
  assert removes == [['busctl', 'call', 'fi.w1.wpa_supplicant1', '/fi/w1/wpa_supplicant1', 'fi.w1.wpa_supplicant1',
                      'RemoveInterface', 'o', '/fi/w1/wpa_supplicant1/Interfaces/7']]
  assert popen.call_count == 2


def assert_free(holds):
  assert not holds[0], 'hostapd started while wpa_supplicant held galaxy0'


def test_supplicant_that_keeps_galaxy0_blocks_the_ap(tmp_path):
  run = Mock(side_effect=lambda args, **kwargs: Mock(returncode=0, stdout='o "/x"\n' if args[0] == 'busctl' else '[]'))
  popen, interfaces = Mock(), Mock()
  backend = quiet_backend(tmp_path, run=run, interfaces=interfaces, popen=popen)
  backend.firewall = '/sbin/iptables-legacy'
  with pytest.raises(RuntimeError, match='wpa_supplicant'):
    backend.start(CONFIG, ('g', 6))
  popen.assert_not_called()
  interfaces.return_value.delete.assert_called_once_with('galaxy0')
  assert backend.clock() <= SUPPLICANT_WAIT_S + 0.2


def test_socket_alone_counts_as_held(tmp_path):
  backend = quiet_backend(tmp_path, run=supplicant_run([False]), interfaces=Mock())
  assert not backend.supplicant_holds()
  (backend.sockets / 'galaxy0').touch()
  assert backend.supplicant_holds()


def test_stop_drops_supplicant_hold_before_deleting_the_interface(tmp_path):
  holds = [True]
  run = supplicant_run(holds)
  interfaces = Mock()
  order = []
  interfaces.return_value.delete.side_effect = lambda name: order.append(('delete', holds[0]))
  backend = quiet_backend(tmp_path, run=run, interfaces=interfaces)
  backend.owned = True
  backend.stop()
  assert order == [('delete', False)]


@pytest.mark.parametrize('results,expected', [
  ([('wlan0', ('g', 11))], [KEEP]), ([('wlan0', ('g', 6))], [KEEP]), ([('wlan0', HOLD)], [HOLD]),
  ([('wlan0', None)], [KEEP]), ([('wlan0', ('g', 11)), ('aa0', ('a', 149))], [('a', 149)]),
  ([('wlan0', ('g', 11)), ('aa0', ('g', 6))], [KEEP]), ([('wlan0', HOLD), ('aa0', ('a', 149))], [HOLD, ('a', 149)])])
def test_steady_results(results, expected):
  assert steady_results(results) == expected


def test_backend_steady_channel_ignores_wlan0_but_not_its_joins(tmp_path):
  statuses = {'wlan0': 'wpa_state=COMPLETED\nfreq=2462'}
  backend = HotspotBackend(tmp_path, run=Mock(side_effect=lambda args, **kwargs: Mock(returncode=0, stdout=statuses[args[2]])),
                           interfaces=Mock())
  assert backend.channel() == ('g', 11)
  assert backend.channel(steady=True) == KEEP and backend.connected == {11}
  statuses['wlan0'] = 'wpa_state=ASSOCIATING'
  assert backend.channel(steady=True) == HOLD


def onroad_controller(ap_channel=6, start=('g', 6)):
  now = [100.]
  backend = backend_mock(ap_channel=ap_channel)
  controller = HotspotController(backend, clock=lambda: now[0], onroad=lambda: True)
  backend.channel.return_value = start
  controller.tick(CONFIG)
  assert controller.tick(CONFIG)['active']
  backend.start.reset_mock()
  backend.stop.reset_mock()
  return controller, backend, now


def test_onroad_phone_hotspot_joins_never_move_the_ap():
  controller, backend, now = onroad_controller()
  # 13:54:52 joins "Deco1" on ch11, 13:55:21 drops, 13:55:25 fails, 13:56:36 joins on ch1 (route 00000070).
  for channel in (HOLD, KEEP, KEEP, HOLD, KEEP, KEEP, HOLD, KEEP):
    backend.channel.return_value = channel
    now[0] += 20
    assert controller.tick(CONFIG) == {'active': True, 'state': 'active', 'reason': '', 'channel': 6}
    assert backend.channel.call_args.kwargs == {'steady': True}
  backend.start.assert_not_called()
  backend.stop.assert_not_called()


def test_onroad_ap_moved_by_the_driver_is_adopted():
  controller, backend, now = onroad_controller()
  backend.connected = {11}
  backend.ap_status.return_value = {'ready': True, 'channel': 11}
  backend.channel.return_value = KEEP
  assert controller.tick(CONFIG)['channel'] == 11
  assert controller.applied[1] == ('g', 11)
  backend.start.assert_not_called()


def test_offroad_and_5ghz_ap_keep_following_stations():
  now = [100.]
  backend = backend_mock(ap_channel=149)
  onroad = [False]
  controller = HotspotController(backend, clock=lambda: now[0], onroad=lambda: onroad[0])
  backend.channel.return_value = ('a', 149)
  controller.tick(CONFIG)
  controller.tick(CONFIG)
  assert backend.channel.call_args.kwargs == {'steady': False}
  onroad[0] = True
  controller.tick(CONFIG)
  assert backend.channel.call_args.kwargs == {'steady': False}  # the HU cannot use 5 GHz; let it come back to 2.4


def test_running_ap_held_by_supplicant_is_stopped_unless_a_station_joins():
  controller, backend, now = onroad_controller()
  backend.supplicant_holds.return_value = True
  backend.channel.return_value = HOLD
  assert controller.tick(CONFIG)['active']  # stopping the AP mid-join is the hazard itself
  backend.stop.assert_not_called()
  backend.channel.return_value = KEEP
  assert controller.tick(CONFIG)['state'] == 'error'
  backend.stop.assert_called_once()
  assert controller.applied is None


def test_unwritable_networkmanager_rule_does_not_block_the_ap(tmp_path):
  run = supplicant_run([False])
  popen = Mock()
  blocker = tmp_path / 'not-a-dir'
  blocker.write_text('')
  backend = quiet_backend(tmp_path, run=run, interfaces=Mock(), popen=popen)
  backend.nm_conf = blocker / 'zz.conf'
  backend.firewall = '/sbin/iptables-legacy'
  backend.start(CONFIG, ('g', 6))
  assert popen.call_count == 2
  assert ['nmcli', 'general', 'reload', 'conf'] not in commands(run)
