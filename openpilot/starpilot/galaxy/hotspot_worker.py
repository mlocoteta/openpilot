"""Privileged, pipe-leased hotspot worker. Never reconfigures the station link.

The unprivileged manager child sends validated settings/heartbeats on stdin.
EOF, ten seconds without a heartbeat, or SIGTERM tears down only our AP.
"""
from __future__ import annotations

import ipaddress
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time

from openpilot.starpilot.galaxy.hotspot import ADDRESS, INTERFACE, NETWORK, HotspotSettings, validate_config
from openpilot.starpilot.galaxy.hotspot_netlink import WirelessInterfaces
from openpilot.starpilot.system.pipe_worker import claim, owned, stop_event

ALIAS = 'starpilot-galaxy-hotspot'
RUNTIME = Path('/run/starpilot-galaxy-hotspot')
STANDALONE_CHANNEL = ('g', 6)
HOLD = 'hold'
# wlan0 first; aa0 is Android Auto's own car link when it runs on a dedicated interface.
STATIONS = ('wlan0', 'aa0')
# Android Auto drops and rejoins the car between attempts; stay put through those gaps.
STANDALONE_SETTLE_S = 30.0
NEGOTIATING = ('AUTHENTICATING', 'ASSOCIATING', 'ASSOCIATED', '4WAY_HANDSHAKE', 'GROUP_HANDSHAKE')
ONROAD_PARAM = Path('/data/params/d/IsOnroad')
# qcacld panics when wpa_supplicant still holds galaxy0 while hostapd runs on it: a later supplicant mode
# change stops our AP from inside wlan0's join (route 00000070, 2026-10-29). NetworkManager hands every new
# Wi-Fi device to the supplicant before `managed no` lands, so keep galaxy0 out of NetworkManager from the start.
# A [device-*] managed=0 section beats netplan's type:wifi managed=1 (the last section wins, user-conf > udev);
# /run keeps it runtime-only.
NM_CONF = Path('/run/NetworkManager/conf.d/zz-starpilot-galaxy-hotspot.conf')
NM_CONF_TEXT = (f'# Written by the StarPilot Galaxy hotspot worker: never hand {INTERFACE} to wpa_supplicant.\n'
                f'[device-starpilot-galaxy-hotspot]\nmatch-device=interface-name:{INTERFACE}\nmanaged=0\n')
SUPPLICANT = ('fi.w1.wpa_supplicant1', '/fi/w1/wpa_supplicant1', 'fi.w1.wpa_supplicant1')
SUPPLICANT_SOCKETS = Path('/run/wpa_supplicant')
# The supplicant grabbed a fresh galaxy0 within 0.3 s on route 00000070; require it absent for longer before hostapd.
SUPPLICANT_QUIET_S = 1.5
SUPPLICANT_WAIT_S = 5.0
KEEP = 'keep'


def radio_channel(status):
  fields = dict(line.split('=', 1) for line in status.splitlines() if '=' in line)
  # A disconnected station remains available for AA/Wi-Fi association. Do not
  # depend on an Internet connection to offer local access. Association itself
  # gets priority: leave the AP untouched while the station negotiates its channel.
  if fields.get('wpa_state') in ('DISCONNECTED', 'INACTIVE', 'SCANNING'):
    return STANDALONE_CHANNEL
  if fields.get('wpa_state') in NEGOTIATING:
    return HOLD
  if fields.get('wpa_state') != 'COMPLETED':
    return None
  frequency = int(fields.get('freq', '0'))
  if 2412 <= frequency <= 2472 and (frequency - 2407) % 5 == 0:
    return 'g', (frequency - 2407) // 5
  if 5180 <= frequency <= 5825 and frequency % 5 == 0:
    return 'a', (frequency - 5000) // 5
  return None


def band_channel(number):
  return ('g' if number <= 14 else 'a'), number


def dfs(channel):
  return channel[0] == 'a' and 52 <= channel[1] <= 144


def choose_channel(results):
  """Pick the AP channel from each station's radio_channel result, wlan0 first."""
  if HOLD in results:
    return HOLD
  for result in results:
    if isinstance(result, tuple) and result != STANDALONE_CHANNEL:
      return result
  return results[0] if results else None


def steady_results(results):
  """(station, result) pairs, wlan0 first, when wlan0 must not move a running AP: its joins still hold
  the AP, its channel does not count."""
  first, others = results[0][1], [result for station, result in results[1:]]
  if first == HOLD:
    return [HOLD] + others
  return others if any(isinstance(result, tuple) and result != STANDALONE_CHANNEL for result in others) else [KEEP]


def nm_activating(state):
  """NetworkManager device states 40-90 are the steps between disconnected and activated."""
  try:
    return 40 <= int(state.strip().split(' ', 1)[0]) < 100
  except ValueError:
    return False


def overlapping_routes(rows):
  subnet = ipaddress.ip_network(NETWORK)
  for row in rows:
    destination = row.get('dst', 'default')
    if destination == 'default' or row.get('dev') == INTERFACE:
      continue
    if subnet.overlaps(ipaddress.ip_network(destination, strict=False)):
      return True
  return False


def hostapd_config(config, channel):
  validate_config(config)
  band, number = channel
  if band not in ('a', 'g') or type(number) is not int or not 1 <= number <= 165:
    raise ValueError('Invalid channel')
  return (f'interface={INTERFACE}\ndriver=nl80211\nssid={config["ssid"]}\nhw_mode={band}\nchannel={number}\n' +
          f'wmm_enabled=1\nauth_algs=1\nwpa=2\nwpa_passphrase={config["password"]}\n' +
          'wpa_key_mgmt=WPA-PSK\nrsn_pairwise=CCMP\nmax_num_sta=4\n')


class HotspotBackend:
  def __init__(self, root=RUNTIME, run=subprocess.run, interfaces=WirelessInterfaces, popen=subprocess.Popen,
               nm_conf=NM_CONF, sockets=SUPPLICANT_SOCKETS, clock=time.monotonic, sleep=time.sleep):
    self.root, self.run, self.interfaces, self.popen = root, run, interfaces, popen
    self.nm_conf, self.sockets, self.clock, self.sleep = nm_conf, sockets, clock, sleep
    self.children = []
    self.owned = False
    self.firewall = shutil.which('iptables-legacy') or shutil.which('iptables')
    self.connected = set()  # channel numbers of the stations that are connected
    self.idle = []  # stations that reported no connection; NetworkManager may be about to join one

  def command(self, args, check=True):
    return self.run(args, check=check, text=True, capture_output=True, timeout=5)

  def channel(self, steady=False):
    """steady: wlan0 carries the car's Internet; its joins and channel changes must not restart the AP."""
    results, self.connected, self.idle = [], set(), []
    for station in STATIONS:
      if station == STATIONS[0]:
        result = radio_channel(self.command(['/usr/sbin/wpa_cli', '-i', station, 'status']).stdout)
      else:
        if not Path(f'/sys/class/net/{station}').exists():
          continue
        # Between creation and wpa_supplicant taking it, aa0 has no status yet; that is no reason to drop the AP.
        reply = self.command(['/usr/sbin/wpa_cli', '-i', station, 'status'], check=False)
        if reply.returncode != 0:
          continue
        result = radio_channel(reply.stdout)
      if result == STANDALONE_CHANNEL:
        self.idle.append(station)
      elif isinstance(result, tuple):
        self.connected.add(result[1])
      results.append((station, result))
    if steady and results and results[0][0] == STATIONS[0]:
      return choose_channel(steady_results(results))
    return choose_channel([result for station, result in results])

  def activating(self):
    for station in self.idle:
      reply = self.command(['nmcli', '-t', '-g', 'GENERAL.STATE', 'device', 'show', station], check=False)
      if reply.returncode == 0 and nm_activating(reply.stdout):
        return True
    return False

  def alive(self):
    return self.owned and len(self.children) == 2 and all(child.poll() is None for child in self.children)

  def ap_status(self):
    """Whether the AP is up, and its current channel: the driver moves it by itself to follow a station."""
    reply = self.command(['/usr/sbin/hostapd_cli', '-p', str(self.root / 'control'), '-i', INTERFACE, 'status'], check=False)
    lines = reply.stdout.splitlines() if reply.returncode == 0 else []
    channel = next((line.split('=', 1)[1] for line in lines if line.startswith('channel=')), '')
    return {'ready': 'state=ENABLED' in lines, 'channel': int(channel) if channel.isdigit() else None}

  def _wireless(self, method):
    client = self.interfaces()
    try:
      getattr(client, method)(INTERFACE)
    finally:
      client.close()

  def keep_unmanaged(self):
    """Install the NetworkManager rule once per boot; the reload only re-reads configuration. Best effort:
    wait_supplicant_free still keeps hostapd off a supplicant-held galaxy0 without it."""
    try:
      if self.nm_conf.read_text() == NM_CONF_TEXT:
        return
    except OSError:
      pass
    try:
      self.nm_conf.parent.mkdir(parents=True, exist_ok=True)
      temporary = self.nm_conf.with_name('.' + self.nm_conf.name)
      temporary.write_text(NM_CONF_TEXT)
      os.replace(temporary, self.nm_conf)
    except OSError:
      return
    self.command(['nmcli', 'general', 'reload', 'conf'], check=False)

  def supplicant_path(self):
    reply = self.command(['busctl', 'call', *SUPPLICANT, 'GetInterface', 's', INTERFACE], check=False)
    if reply.returncode == 0 and reply.stdout.startswith('o '):
      return reply.stdout.split(None, 1)[1].strip().strip('"')
    return None

  def supplicant_holds(self):
    return (self.sockets / INTERFACE).exists() or self.supplicant_path() is not None

  def wait_supplicant_free(self):
    """Before hostapd: galaxy0 must stay out of wpa_supplicant for SUPPLICANT_QUIET_S. No AP runs yet, so
    removing a supplicant interface here only changes the mode of an idle interface."""
    start = last_held = self.clock()
    released = False
    while self.clock() - last_held < SUPPLICANT_QUIET_S:
      if self.supplicant_holds():
        last_held = self.clock()
        if last_held - start >= SUPPLICANT_WAIT_S:
          raise RuntimeError('wpa_supplicant holds the hotspot interface')
        path = None if released else self.supplicant_path()
        if path is not None and last_held - start >= SUPPLICANT_QUIET_S:
          self.command(['busctl', 'call', *SUPPLICANT, 'RemoveInterface', 'o', path], check=False)
          released = True
      self.sleep(0.1)

  def stale_owned(self):
    return owned(INTERFACE, ALIAS)

  def stop(self):
    for child in self.children:
      if child.poll() is None:
        child.terminate()
    for child in self.children:
      try:
        child.wait(timeout=2)
      except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=2)
    self.children.clear()
    owned = self.owned or self.stale_owned()
    if owned:
      # Drop a supplicant hold before the netdev goes, or the supplicant re-grabs the next galaxy0 by name.
      path = self.supplicant_path()
      if path is not None:
        self.command(['busctl', 'call', *SUPPLICANT, 'RemoveInterface', 'o', path], check=False)
      self._wireless('delete')
      self.owned = False
    if self.firewall:
      # The comment distinguishes our rules even if the kernel already removed
      # the AP after a worker crash. Never flush the shared forwarding chain.
      for direction in ('-i', '-o'):
        self.command(self.firewall_rule('-D', direction), check=False)

  def firewall_rule(self, operation, direction):
    return [self.firewall, '-w', '2', operation, 'FORWARD', direction, INTERFACE,
            '-m', 'comment', '--comment', ALIAS, '-j', 'DROP']

  def start(self, config, channel):
    if not self.firewall:
      raise RuntimeError('Firewall helper unavailable')
    if overlapping_routes(json.loads(self.command(['ip', '-j', '-4', 'route', 'show', 'table', 'all']).stdout)):
      raise RuntimeError('Hotspot subnet conflicts with an existing network')
    self.keep_unmanaged()
    self._wireless('create')
    self.owned = True
    try:
      self.command(['ip', 'link', 'set', 'dev', INTERFACE, 'alias', ALIAS])
      self.command(['nmcli', 'device', 'set', INTERFACE, 'managed', 'no'])
      self.command(['sysctl', '-w', f'net.ipv6.conf.{INTERFACE}.disable_ipv6=1'])
      # Local access only, even if the phone supplies its own default route.
      for direction in ('-i', '-o'):
        self.command(self.firewall_rule('-I', direction))
      self.command(['ip', 'address', 'add', f'{ADDRESS}/24', 'dev', INTERFACE])
      self.command(['ip', 'link', 'set', 'dev', INTERFACE, 'up'])
      self.wait_supplicant_free()
      ap = self.root / 'hostapd.conf'
      ap.write_text(hostapd_config(config, channel) + f'ctrl_interface={self.root / "control"}\n')
      ap.chmod(0o600)
      dhcp = self.root / 'dnsmasq.conf'
      dhcp.write_text(f'interface={INTERFACE}\nbind-interfaces\nport=0\nno-resolv\nno-hosts\n' +
                      'dhcp-range=172.31.254.10,172.31.254.30,255.255.255.0,10m\n' +
                      'dhcp-option=3\ndhcp-option=6\nleasefile-ro\n')
      for command in (['/usr/sbin/hostapd', str(ap)],
                      ['/usr/sbin/dnsmasq', '--keep-in-foreground', '--conf-file=' + str(dhcp)]):
        self.children.append(self.popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, close_fds=True))
    except BaseException:
      self.stop()
      raise


def read_onroad(path=ONROAD_PARAM):
  try:
    return path.read_bytes().strip() == b'1'
  except OSError:
    return False  # 7.0 removes IsOnroad while offroad


class HotspotController:
  def __init__(self, backend, clock=time.monotonic, onroad=read_onroad):
    self.backend, self.clock, self.onroad = backend, clock, onroad
    self.applied, self.retry_at, self.ready_deadline = None, 0.0, 0.0
    self.station_seen = float('-inf')
    self.attempted = None
    self.refused = set()  # DFS channels hostapd would not start on; use the standalone channel instead

  def tick(self, config):
    if not config['enabled']:
      self.backend.stop()
      self.applied = None
      return {'active': False, 'state': 'disabled', 'reason': ''}
    try:
      running = self.applied is not None and self.backend.alive()
      # Onroad a 2.4 GHz AP stays put: the HU needs it, and wlan0 (the phone hotspot) works beside it in MCC.
      # Every AP restart is a fresh galaxy0 that NetworkManager and wpa_supplicant may race for.
      steady = running and self.applied[1][0] == 'g' and self.onroad()
      channel = self.backend.channel(steady=steady)
      status = self.backend.ap_status() if running else {'ready': False, 'channel': None}
      if running and (isinstance(channel, tuple) or channel == KEEP) and self.applied[0] == config:
        current = status['channel']
        # The driver moves the AP onto a station's channel by itself; restarting it there would only move it back.
        if current is not None and (channel == KEEP or current == channel[1] or current in self.backend.connected):
          channel = band_channel(current)
          self.applied = (self.applied[0], channel)
      if channel == KEEP:
        channel = self.applied[1]
      if running and channel != HOLD and self.backend.supplicant_holds():
        # Not expected with the NetworkManager rule. A supplicant-held AP is what panicked: stop it while no
        # station is joining, and start clean after the retry delay.
        raise RuntimeError('wpa_supplicant holds the running hotspot interface')
      if channel == STANDALONE_CHANNEL:
        if self.clock() - self.station_seen < STANDALONE_SETTLE_S:
          channel = HOLD
      elif channel is not None:
        self.station_seen = self.clock()
      if isinstance(channel, tuple) and channel[1] in self.refused:
        channel = STANDALONE_CHANNEL
      if channel != HOLD and (not running or (dict(config), channel) != self.applied) and self.backend.activating():
        self.station_seen = self.clock()
        channel = HOLD
      if channel is None:
        self.backend.stop()
        self.applied = None
        return {'active': False, 'state': 'waiting', 'reason': 'Waiting for Wi-Fi radio readiness or a supported connection channel.'}
      desired = (dict(config), channel)
      if channel == HOLD:
        # Starting, stopping or moving the AP while a station joins makes the join fail.
        if not running or self.applied is None:
          return {'active': False, 'state': 'waiting', 'reason': 'Waiting for Wi-Fi to finish connecting.'}
        desired = self.applied
        channel = desired[1]
      if desired != self.applied or not running:
        self.backend.stop()
        self.applied = None
        if self.clock() < self.retry_at:
          return {'active': False, 'state': 'error', 'reason': 'Hotspot unavailable; retrying shortly.'}
        self.retry_at = self.clock() + 15
        self.attempted = channel
        self.backend.start(config, channel)
        self.applied = desired
        self.ready_deadline = self.clock() + 15
        return {'active': False, 'state': 'starting', 'reason': 'Starting the local Wi-Fi network.', 'channel': channel[1]}
      if not status['ready']:
        if self.clock() >= self.ready_deadline:
          raise RuntimeError('Hotspot did not become ready')
        return {'active': False, 'state': 'starting', 'reason': 'Waiting for the Wi-Fi access point.', 'channel': channel[1]}
      self.attempted = None
      return {'active': True, 'state': 'active', 'reason': '', 'channel': channel[1]}
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError):
      if self.attempted is not None and dfs(self.attempted):
        self.refused.add(self.attempted[1])
      self.attempted = None
      self.backend.stop()
      self.applied = None
      self.retry_at = self.clock() + 15
      return {'active': False, 'state': 'error', 'reason': 'Hotspot could not start on this channel. Projection Wi-Fi was not reconfigured.'}


def main():
  fd = claim(RUNTIME, 'Hotspot worker')
  backend = HotspotBackend()
  controller = HotspotController(backend)
  stop = stop_event()
  config, buffer, last = None, b'', time.monotonic()
  try:
    backend.stop()  # clean an interface explicitly marked as ours after a crash
    while not stop.is_set() and time.monotonic() - last < 10:
      if select.select([sys.stdin], [], [], 2)[0]:
        data = os.read(sys.stdin.fileno(), 4097)
        if not data:
          break
        buffer += data
        if len(buffer) > 4096:
          raise ValueError('Oversized settings input')
        while b'\n' in buffer:
          line, buffer = buffer.split(b'\n', 1)
          config = validate_config(json.loads(line))
          last = time.monotonic()
      if config is not None:
        print(json.dumps({**controller.tick(config), 'revision': HotspotSettings.revision(config)}), flush=True)
  finally:
    backend.stop()
    os.close(fd)


if __name__ == '__main__':
  main()
