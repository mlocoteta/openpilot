"""9G Accord Torque Interceptor: LKAS button defaults to Toggle AOL.

6.x ran the TI car with LKASButtonControl=9, so the steering-wheel LKAS button turned
always-on lateral on and off. 7.0 skips the LKASButtonControl default at manager start
(card enrolls it per vehicle) and only the Sonata Hybrid enrolls one, so on the TI car
the key stays absent and the button does nothing. Write 9 once when the key is absent;
any saved choice (including Off) is kept. No marker key: a present file is the marker.
"""

import os

from opendbc.car.honda.torque_interceptor import ti_qualified

AOL_TOGGLE = 9


def ti_car(cp):
  try:
    return cp.brand == 'honda' and ti_qualified(cp)
  except (AttributeError, TypeError, ValueError, IndexError):
    return False


def enroll_lkas_default(cp, params):
  if not ti_car(cp):
    return False
  if params.get('LKASButtonControl') is not None or os.path.lexists(params.get_param_path('LKASButtonControl')):
    return False
  params.put('LKASButtonControl', AOL_TOGGLE, block=True)
  return True
