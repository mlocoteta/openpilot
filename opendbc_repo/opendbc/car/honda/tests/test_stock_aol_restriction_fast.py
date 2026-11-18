"""card resolves qualified(CP, marked_only=True) once per drive and then uses qualified_temporary_restriction:
it must equal temporary_restriction for every qualified CP and state."""
import itertools

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.stock_aol import qualified, qualified_temporary_restriction, temporary_restriction
from opendbc.car.honda.torque_interceptor import apply_torque_interceptor
from opendbc.car.honda.values import CAR, HondaSafetyFlags

GEARS = structs.CarState.GearShifter


def accord_9g_aol_cp(ti: bool):
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x188] = 6
  fingerprint[0][0x201] = 6   # pedal
  cp = CarInterface.get_params(CAR.HONDA_ACCORD_9G, fingerprint, [], False, False, False)
  cp.fingerprintSource = structs.CarParams.FingerprintSource.fixed
  if ti:
    apply_torque_interceptor(cp, True)
  cp.alternativeExperience = 32
  cp.safetyConfigs[-1].safetyParam |= int(HondaSafetyFlags.NIDEC_PEDAL_AOL)
  return cp


def states():
  for can_valid, can_timeout, perm, temp, gear in itertools.product(
      (True, False), (False, True), (False, True), (False, True),
      (GEARS.drive, GEARS.sport, GEARS.low, GEARS.brake, GEARS.park, GEARS.reverse, GEARS.neutral, GEARS.unknown)):
    cs = structs.CarState()
    cs.canValid, cs.canTimeout, cs.steerFaultPermanent, cs.steerFaultTemporary, cs.gearShifter = (
      can_valid, can_timeout, perm, temp, gear)
    yield cs


def test_qualified_restriction_matches_full_check():
  for ti in (False, True):
    cp = accord_9g_aol_cp(ti)
    assert qualified(cp, marked_only=True), ti
    results = set()
    for cs in states():
      fast = qualified_temporary_restriction(cp, cs)
      assert fast is temporary_restriction(cp, cs)
      results.add(fast)
    assert results == {True, False}
    assert qualified_temporary_restriction(cp, None) is temporary_restriction(cp, None) is False
