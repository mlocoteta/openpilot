from types import SimpleNamespace

import pytest

from opendbc.car import structs
from opendbc.car.tesla.carcontroller import CarController
from opendbc.car.tesla.interface import CarInterface
from opendbc.car.tesla.values import CAR, DBC


@pytest.mark.parametrize('direction', [-1., 1.])
def test_preap_stalled_rack_request_stays_within_legacy_tracking_envelope(direction):
  cp = CarInterface.get_non_essential_params(CAR.TESLA_MODEL_S_PREAP)
  controller = CarController(DBC[cp.carFingerprint], cp)
  controller.stock_cc = None
  cs = SimpleNamespace(out=SimpleNamespace(vEgoRaw=3., steeringAngleDeg=0.),
                       hands_on_level=0, preap_lateral_authorized=True, cruiseEnabled=False)
  cc = structs.CarControl.new_message()
  cc.latActive = True
  cc.actuators.steeringAngleDeg = direction * 100.
  previous = 0.
  for frame in range(100):
    output, _ = controller.update(cc.as_reader(), cs, frame * 10000000, None)
    assert abs(output.steeringAngleDeg) <= 20.
    assert abs(output.steeringAngleDeg - previous) <= 5.
    previous = output.steeringAngleDeg
  assert previous == direction * 20.

  cs.out.steeringAngleDeg = -direction * 50.
  output, _ = controller.update(cc.as_reader(), cs, 1000000000, None)
  assert abs(output.steeringAngleDeg - previous) <= 5.

  cc.latActive = False
  controller.frame = 102
  output, _ = controller.update(cc.as_reader(), cs, 1020000000, None)
  assert output.steeringAngleDeg == cs.out.steeringAngleDeg
