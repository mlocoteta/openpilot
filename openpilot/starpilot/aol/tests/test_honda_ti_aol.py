"""TI always-on lateral (F05), host side: the 9G Torque Interceptor car joins 7.0's Nidec pedal AOL.

Startup order on the car: vehicle_preferences.prepare() sets the TI bit (36 -> 36|4096), then
card.py applies the AOL policy addition (NIDEC_PEDAL_AOL 512, alternativeExperience 32) when the
AOL toggle is on, giving 548|4096. Every qualification on that final CP must still hold: stock
AOL (marked), the pedal interceptor, the TI itself, and the pandad/native profile for 4644.
"""
import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda import nidec_interceptor, stock_aol
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.torque_interceptor import TI_SAFETY_PARAM, apply_torque_interceptor, ti_qualified
from opendbc.car.honda.values import CAR
from openpilot.starpilot.aol.vehicle import native_matches_cp, native_profile_supported, policy_for

NIDEC = int(structs.CarParams.SafetyModel.hondaNidec)
TI_AOL_WORD = 548 | 4096


def startup(identity=CAR.HONDA_ACCORD_9G, *, pedal=True, ti=True, aol=True):
  fp = gen_empty_fingerprint()
  if pedal:
    fp[0][0x201] = 6
  cp = CarInterface.get_params(identity, fp, [], False, False, False)
  apply_torque_interceptor(cp, ti)  # vehicle_preferences.prepare()
  policy = policy_for(cp)
  if aol and policy.intent_supported:  # card.py AOL addition
    cp.safetyConfigs[0].safetyParam |= policy.safety_param_addition
    cp.alternativeExperience |= policy.alternative_experience_addition
  return cp, policy


def test_ti_pedal_car_gets_the_ti_aol_word():
  cp, policy = startup()
  assert TI_SAFETY_PARAM == 4096 and stock_aol.NIDEC_TI_AOL_WORD == TI_AOL_WORD
  assert policy.intent_supported and policy.runtime_supported and policy.explicit_latch
  assert (cp.safetyConfigs[0].safetyParam, cp.alternativeExperience) == (TI_AOL_WORD, 32)
  assert stock_aol.qualified(cp, marked_only=True)
  assert policy_for(cp).ordinary_axis_ack_required  # host steers only on the panda's lateralAllowed
  assert ti_qualified(cp)
  assert nidec_interceptor.qualified(cp)
  assert native_profile_supported(NIDEC, TI_AOL_WORD)
  assert native_matches_cp(cp, NIDEC, TI_AOL_WORD)
  assert not native_matches_cp(cp, NIDEC, 548)
  ci = CarInterface(cp)
  assert ci.CC.ti is not None and ci.CS.ti is not None and ci.CC.nidec_interceptor is not None


def test_aol_off_keeps_engaged_only_lateral():
  cp, _ = startup(aol=False)
  assert (cp.safetyConfigs[0].safetyParam, cp.alternativeExperience) == (36 | 4096, 0)
  assert not stock_aol.qualified(cp, marked_only=True)
  assert ti_qualified(cp)


def test_stock_9g_pedal_unchanged():
  cp, _ = startup(ti=False)
  assert (cp.safetyConfigs[0].safetyParam, cp.alternativeExperience) == (548, 32)
  assert stock_aol.qualified(cp, marked_only=True) and not ti_qualified(cp)


def test_no_pedal_ti_car_never_aol():
  cp, policy = startup(pedal=False)
  assert not policy.intent_supported
  assert cp.safetyConfigs[0].safetyParam == 4 | 4096 and cp.alternativeExperience == 0
  for experience in (0, 32):
    cp.alternativeExperience = experience
    assert not stock_aol.qualified(cp) and not stock_aol.qualified(cp, marked_only=True)


@pytest.mark.parametrize("identity", (CAR.ACURA_ILX, CAR.HONDA_CIVIC, CAR.HONDA_ODYSSEY_TWN, CAR.HONDA_CRV))
def test_ti_bit_on_other_pedal_hondas_never_qualifies(identity):
  cp, _ = startup(identity, ti=False)
  cp.safetyConfigs[0].safetyParam |= TI_SAFETY_PARAM
  assert not stock_aol.qualified(cp) and not stock_aol.qualified(cp, marked_only=True)
  assert not native_matches_cp(cp, NIDEC, int(cp.safetyConfigs[0].safetyParam))


@pytest.mark.parametrize("word", (36 | 4096, 4 | 4096, 544 | 4096, 804 | 4096, 4096, 548 | 4096 | 1))
def test_only_the_exact_ti_word_is_a_native_profile(word):
  assert not native_profile_supported(NIDEC, word)


def test_wrong_ti_word_with_experience_32_is_not_stock_aol():
  cp, _ = startup()
  cp.safetyConfigs[0].safetyParam = 36 | 4096  # TI bit but no NIDEC_PEDAL_AOL
  assert not stock_aol.qualified(cp, marked_only=True)
