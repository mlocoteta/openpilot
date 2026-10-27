"""F27: the route turn slowdown needs the driver's matching turn signal.

Route 0000004c--06d77f2ceb seg 5 (2026-10-27): a guided "turn left" 560 m ahead pulled
cruise from 52 to 36 mph on a straight road with no blinker; the driver never turned.
"""
from types import SimpleNamespace as NS

import pytest

from openpilot.common.constants import CV
from openpilot.starpilot.navigation.intent import cruise_ceiling, turn_signalled

NOW = 20_000_000_000
SET = 53 * CV.MPH_TO_MS


def make_sm(modifier='left', kind='turn', distance=488., left=False, right=False):
  class SM(dict):
    valid = dict.fromkeys(('starpilotNavigation', 'deviceState', 'carState', 'carControl'), True)
    alive = dict(valid)
    logMonoTime = dict.fromkeys(valid, NOW)
  instruction = NS(maneuverType=kind, maneuverModifier=modifier, distanceMeters=distance)
  later = NS(maneuverType='turn', maneuverModifier='right', distanceMeters=13_772.)
  nav = NS(enabled=True, controlValid=True, status='guiding', sessionId='producer', revision='one', frameMonoTime=NOW,
           startedMonoTime=10_000_000_000, locationMonoTime=NOW, instruction=instruction, nextManeuver=later, version=2)
  return SM(starpilotNavigation=NS(navigation=nav), deviceState=NS(started=True, startedMonoTime=10_000_000_000),
            carState=NS(canValid=True, canTimeout=False, gearShifter='drive', vEgo=23.2, standstill=False,
                        leftBlinker=left, rightBlinker=right, leftBlindspot=False, rightBlindspot=False,
                        gasPressed=False, brakePressed=False),
            carControl=NS(latActive=True, longActive=True))


CP = NS(openpilotLongitudinalControl=True, passive=False, dashcamOnly=False, minSteerSpeed=0.)


def test_route_4c_unsignalled_turn_does_not_slow():
  assert cruise_ceiling(make_sm(), CP, NOW, SET) is None


def test_matching_signal_restores_upstream_ceiling():
  expected = ((14 * CV.MPH_TO_MS) ** 2 + 2 * .45 * (488. - 8)) ** .5
  assert cruise_ceiling(make_sm(left=True), CP, NOW, SET) == pytest.approx(expected)
  assert cruise_ceiling(make_sm('right', right=True), CP, NOW, SET) == pytest.approx(expected)


@pytest.mark.parametrize('modifier,left,right', [('left', False, True), ('sharpLeft', False, True),
                                                 ('right', True, False), ('sharpRight', True, False),
                                                 ('left', True, True), ('uturn', True, True), ('uturn', False, False)])
def test_wrong_side_or_hazards_do_not_slow(modifier, left, right):
  assert cruise_ceiling(make_sm(modifier, left=left, right=right), CP, NOW, SET) is None


@pytest.mark.parametrize('kind,modifier', [('turn', 'uturn'), ('roundabout', 'right'), ('rotary', 'straight')])
def test_sideless_maneuvers_take_either_single_signal(kind, modifier):
  assert cruise_ceiling(make_sm(modifier, kind, distance=60.), CP, NOW, SET) is None
  assert cruise_ceiling(make_sm(modifier, kind, distance=60., left=True), CP, NOW, SET) is not None
  assert cruise_ceiling(make_sm(modifier, kind, distance=60., right=True), CP, NOW, SET) is not None


def test_next_maneuver_needs_its_own_signal():
  sm = make_sm('straight', kind='fork', distance=50.)
  sm['starpilotNavigation'].navigation.nextManeuver = NS(maneuverType='turn', maneuverModifier='right', distanceMeters=80.)
  assert cruise_ceiling(sm, CP, NOW, SET) is None
  sm['carState'].rightBlinker = True
  assert cruise_ceiling(sm, CP, NOW, SET) is not None


def test_turn_signalled_reads_stalk_state_only():
  cs = NS(leftBlinker=True, rightBlinker=False)
  assert turn_signalled(cs, NS(maneuverType='turn', maneuverModifier='left'))
  assert not turn_signalled(cs, NS(maneuverType='turn', maneuverModifier='right'))


def test_planner_ignores_unsignalled_guided_turn():
  import numpy as np
  from unittest.mock import patch
  from opendbc.car.hyundai.interface import CarInterface
  from opendbc.car.hyundai.values import CAR
  from openpilot.cereal import messaging
  from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
  from openpilot.starpilot.longitudinal.tests.test_conditional_handoff import Frame, NOW as FRAME_NOW, DRIVE
  from openpilot.starpilot.navigation.wire import navigation_envelope

  cp = CarInterface.get_non_essential_params(CAR.HYUNDAI_IONIQ_6)
  cp.openpilotLongitudinalControl = True
  baseline, guided = LongitudinalPlanner(cp, init_v=20.), LongitudinalPlanner(cp, init_v=20.)
  for tick in range(40):
    frame = Frame()
    now = FRAME_NOW + tick * 50_000_000
    frame['carState'].vEgo = 20.
    frame['carState'].gearShifter = 'drive'
    frame.logMonoTime = dict.fromkeys(frame, now)
    with patch('openpilot.selfdrive.controls.lib.longitudinal_planner.navigation_ceiling', return_value=None):
      baseline.update(frame, now_ns=now)
    nav = messaging.new_message('starpilotNavigation')
    nav.starpilotNavigation = navigation_envelope({'enabled': True, 'controlValid': True, 'status': 'guiding', 'sessionId': 'test',
                              'revision': 'one', 'frameMonoTime': now, 'startedMonoTime': DRIVE, 'locationMonoTime': now,
                              'instruction': {'maneuverType': 'turn', 'maneuverModifier': 'left', 'distanceMeters': 20.}})
    frame['starpilotNavigation'] = nav.starpilotNavigation
    frame.logMonoTime['starpilotNavigation'] = now
    frame.valid['starpilotNavigation'] = frame.alive['starpilotNavigation'] = True
    guided.update(frame, now_ns=now)
    assert guided.output_a_target == baseline.output_a_target
    np.testing.assert_array_equal(guided.mpc.params, baseline.mpc.params)
