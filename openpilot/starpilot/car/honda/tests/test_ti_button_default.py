from types import SimpleNamespace

from opendbc.car.honda.values import CAR
from openpilot.starpilot.aol.tests.test_honda_ti_aol import startup
from openpilot.starpilot.car.honda.ti_button_default import AOL_TOGGLE, enroll_lkas_default


class Saved:
  def __init__(self, action):
    self.values = {} if action is None else {'LKASButtonControl': action}
  def get(self, key, **kwargs):
    return self.values.get(key)
  def get_param_path(self, key):
    return '/path-that-does-not-exist-for-test/' + key
  def put(self, key, value, **kwargs):
    self.values[key] = value


def cp_for(fingerprint=CAR.HONDA_ACCORD_9G, param=4644, brand='honda'):
  if brand != 'honda' or fingerprint != CAR.HONDA_ACCORD_9G:
    return SimpleNamespace(brand=brand, carFingerprint=fingerprint, safetyConfigs=[SimpleNamespace(safetyParam=param)])
  cp, _ = startup(ti=bool(param & 4096), aol=(param & 512) != 0)
  return cp


def test_real_startup_carparams():
  # TI on, with or without the AOL toggle or the pedal (no-pedal TI has no AOL policy, so 9 stays inert there)
  for kw in ({'aol': True}, {'aol': False}, {'pedal': False}):
    cp, _ = startup(**kw)
    saved = Saved(None)
    assert enroll_lkas_default(cp, saved) and saved.get('LKASButtonControl') == AOL_TOGGLE
  for kw in ({'ti': False}, {'identity': CAR.HONDA_CIVIC}):
    cp, _ = startup(**kw)
    saved = Saved(None)
    assert not enroll_lkas_default(cp, saved) and saved.get('LKASButtonControl') is None


def test_ti_accord_gets_toggle_aol_once():
  saved = Saved(None)
  assert enroll_lkas_default(cp_for(), saved)
  assert saved.get('LKASButtonControl') == AOL_TOGGLE
  saved.put('LKASButtonControl', 0)
  assert not enroll_lkas_default(cp_for(), saved)
  assert saved.get('LKASButtonControl') == 0


def test_ti_word_without_aol_also_enrolls():
  saved = Saved(None)
  assert enroll_lkas_default(cp_for(param=36 | 4096), saved)
  assert saved.get('LKASButtonControl') == AOL_TOGGLE


def test_saved_choice_is_kept():
  for action in (0, 3, 5, 9, b'garbage'):
    saved = Saved(action)
    assert not enroll_lkas_default(cp_for(), saved)
    assert saved.get('LKASButtonControl') == action


def test_non_ti_cars_untouched():
  class Unused:
    def get(self, *_args, **_kw):
      raise AssertionError('must not read settings')
    put = get_param_path = get
  for cp in (cp_for(param=548), cp_for(fingerprint=CAR.HONDA_CIVIC), cp_for(brand='toyota'), None, object(),
             SimpleNamespace(brand='honda', carFingerprint=CAR.HONDA_ACCORD_9G, safetyConfigs=[])):
    assert not enroll_lkas_default(cp, Unused())
