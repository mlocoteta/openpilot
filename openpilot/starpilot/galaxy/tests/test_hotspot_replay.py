"""Replay of the route 00000070 Wi-Fi panic (2026-10-29 13:54:40-13:58:00 UTC) against a model of the radio.

The model follows the kernel and NetworkManager logs: NetworkManager hands every new galaxy0 to wpa_supplicant
and lets go when told `managed no`, unless its [device-*] rule is loaded; on the third AP restart (13:55:52) the
supplicant kept galaxy0 itself; a wlan0 join while hostapd runs on a supplicant-held galaxy0 panics (13:56:36).
"""
import json
from unittest.mock import Mock

import pytest

from openpilot.starpilot.galaxy import hotspot_worker
from openpilot.starpilot.galaxy.hotspot_worker import NEGOTIATING

CONFIG = {'enabled': True, 'ssid': 'TheGalaxy-6b86', 'password': '1234567890123456'}
START = 13 * 3600 + 54 * 60 + 40

# (from, wpa_cli status) for wlan0, seconds after 13:54:40
WLAN0 = [
  (0, 'wpa_state=SCANNING'),
  (12, 'wpa_state=ASSOCIATING'),               # 13:54:52 "Deco1" de:e7:75:2e:8b:e7 ch11 (Mat's phone hotspot)
  (13, 'wpa_state=COMPLETED\nfreq=2462'),
  (41, 'wpa_state=DISCONNECTED'),              # 13:55:21 disassociated
  (45, 'wpa_state=ASSOCIATING'),               # 13:55:25 rejoin, fails
  (47, 'wpa_state=SCANNING'),
  (116, 'wpa_state=ASSOCIATING'),              # 13:56:36 "Deco1" 42:fc:a0:70:25:7f ch1
  (117, 'wpa_state=COMPLETED\nfreq=2412'),
]


def clock_text(t):
  t = int(START + t)
  return f'{t // 3600:02d}:{t // 60 % 60:02d}:{t % 60:02d}'


class Radio:
  def __init__(self, tmp_path, rogue_creates=(3,), rule_works=True):
    self.t = 0.
    self.tmp_path = tmp_path
    self.rogue_creates, self.rule_works = set(rogue_creates), rule_works
    self.rule_loaded = False
    self.creates = 0
    self.held = False         # wpa_supplicant has galaxy0
    self.rogue = False        # ...and keeps it regardless of NetworkManager
    self.ap = None            # channel hostapd runs on
    self.hazards, self.events = [], []
    self.last_wlan0 = None

  def wlan0(self):
    return [status for start, status in WLAN0 if start <= self.t][-1]

  def note(self, text):
    self.events.append(f'{clock_text(self.t)} {text}')

  def observe(self):
    status = self.wlan0()
    state = status.split('\n')[0].split('=')[1]
    if state != self.last_wlan0 and state in NEGOTIATING and self.ap is not None and self.held:
      self.hazards.append(f'{clock_text(self.t)} PANIC: wlan0 joins while wpa_supplicant holds the running AP')
    self.last_wlan0 = state
    return status

  # subprocess.run
  def run(self, args, **kwargs):
    reply = Mock(returncode=0, stdout='')
    if args[0] == '/usr/sbin/wpa_cli':
      reply.stdout = self.observe() if args[2] == 'wlan0' else ''
      reply.returncode = 0 if args[2] == 'wlan0' else 255
    elif args[0] == '/usr/sbin/hostapd_cli':
      reply.returncode, reply.stdout = (0, f'state=ENABLED\nchannel={self.ap}\n') if self.ap else (255, '')
    elif args[:3] == ['ip', '-j', '-4']:
      reply.stdout = '[]'
    elif args[:3] == ['nmcli', 'general', 'reload']:
      self.rule_loaded = self.rule_works
    elif args[:5] == ['nmcli', 'device', 'set', 'galaxy0', 'managed'] and not self.rogue:
      if self.held:
        self.note('NetworkManager releases galaxy0 from wpa_supplicant')
      self.held = False
    elif args[:2] == ['nmcli', 'device'] and args[2:3] != ['set'] and 'wlan0' in args:
      self.hazards.append(f'{clock_text(self.t)} wlan0 touched: {args}')
    elif args[0] == 'busctl':
      if args[5] == 'GetInterface':
        reply.returncode, reply.stdout = (0, 'o "/fi/w1/wpa_supplicant1/Interfaces/3"\n') if self.held else (1, '')
      elif args[5] == 'RemoveInterface' and self.held:
        self.note('worker removes galaxy0 from wpa_supplicant')
        self.held = self.rogue = False
    return reply

  # WirelessInterfaces
  def interfaces(self):
    radio = self
    class Client:
      def create(self, name):
        radio.creates += 1
        radio.note(f'galaxy0 created (#{radio.creates})')
        if radio.creates in radio.rogue_creates:
          radio.held = radio.rogue = True
          radio.note('wpa_supplicant grabs galaxy0 by itself')
        elif not radio.rule_loaded:
          radio.held = True
          radio.note('NetworkManager hands galaxy0 to wpa_supplicant')
      def delete(self, name):
        radio.ap = None
        radio.note('galaxy0 deleted')
      def close(self):
        pass
    return Client()

  # subprocess.Popen
  def popen(self, command, **kwargs):
    child = Mock()
    child.poll.return_value = None
    if command[0] == '/usr/sbin/hostapd':
      conf = open(command[1]).read()
      self.ap = int(conf.split('channel=')[1].split('\n')[0])
      if self.held:
        self.hazards.append(f'{clock_text(self.t)} hostapd started on a supplicant-held galaxy0')
      if self.last_wlan0 in NEGOTIATING:
        self.hazards.append(f'{clock_text(self.t)} AP started while wlan0 joins')
      self.note(f'hostapd up on ch{self.ap}')
    return child

  def sleep(self, seconds):
    self.t += seconds


def replay(module, tmp_path, onroad=True, **radio):
  model = Radio(tmp_path, **radio)
  kwargs = {'run': model.run, 'interfaces': model.interfaces, 'popen': model.popen}
  if hasattr(module, 'NM_CONF'):
    (tmp_path / 'sockets').mkdir(exist_ok=True)
    kwargs.update(nm_conf=tmp_path / 'nm.conf', sockets=tmp_path / 'sockets', clock=lambda: model.t, sleep=model.sleep)
  backend = module.HotspotBackend(tmp_path, **kwargs)
  backend.firewall = '/sbin/iptables-legacy'
  backend.stale_owned = lambda: False
  controller_kwargs = {'onroad': lambda: onroad} if 'onroad' in module.HotspotController.__init__.__code__.co_varnames else {}
  controller = module.HotspotController(backend, clock=lambda: model.t, **controller_kwargs)
  states = []
  while model.t < 200:
    reply = controller.tick(CONFIG)
    states.append((clock_text(model.t), reply['state'], reply.get('channel')))
    model.t = int(model.t) + 2
  return model, states


@pytest.mark.parametrize('radio', [{}, {'rogue_creates': ()}, {'rule_works': False},
                                   {'rule_works': False, 'rogue_creates': (1, 2, 3, 4, 5)}])
def test_replay_route_70_no_hazard_and_phone_hotspot_untouched(tmp_path, radio):
  model, states = replay(hotspot_worker, tmp_path, **radio)
  assert model.hazards == [], json.dumps(model.events, indent=1)
  assert model.creates == 1  # the AP starts once and rides out every phone-hotspot join on ch6
  assert model.ap == 6
  assert states[-1][1:] == ('active', 6)
  assert model.wlan0() == 'wpa_state=COMPLETED\nfreq=2412'  # wlan0 is left on the phone hotspot


@pytest.mark.parametrize('rule_works', [True, False])
def test_replay_offroad_restarts_stay_clean_even_when_the_supplicant_grabs_every_galaxy0(tmp_path, rule_works):
  # Offroad the AP still follows wlan0, so the replay restarts it at 13:54:53 and 13:55:5x like the panic drive.
  model, states = replay(hotspot_worker, tmp_path, onroad=False, rule_works=rule_works, rogue_creates=range(1, 10))
  assert model.hazards == [], json.dumps(model.events, indent=1)
  assert model.creates >= 3
  assert states[-1][1] == 'active'
