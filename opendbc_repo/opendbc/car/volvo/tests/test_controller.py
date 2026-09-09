from collections import defaultdict
from types import SimpleNamespace

from opendbc.car.volvo.carcontroller import CarController
from opendbc.car.volvo.helpers import checksum_lca_5_message
from opendbc.car.volvo.interface import CarInterface
from opendbc.car.volvo.values import DBC


def _zero_message():
  return defaultdict(int)


def _state():
  return SimpleNamespace(
    out=SimpleNamespace(steeringAngleDeg=0.0, vEgoRaw=12.0, steeringTorque=0.0),
    msg_lca=_zero_message(),
    msg_pscm=_zero_message(),
    msg_pscm_related=_zero_message(),
    msg_lca_3=_zero_message(),
    msg_lca_2=_zero_message(),
    msg_lca_5=_zero_message(),
    msg_lca_4=_zero_message(),
    msg_lca_6=_zero_message(),
    msg_lca_7=_zero_message(),
    pilot_assist_engaged=False,
  )


class _Actuators:
  steeringAngleDeg = 30.0

  def as_builder(self):
    return SimpleNamespace(steeringAngleDeg=self.steeringAngleDeg)


def test_controller_emits_valid_eight_byte_messages_and_lca5_checksum():
  cp = CarInterface.get_non_essential_params("POLESTAR_2")
  controller = CarController(DBC[cp.carFingerprint], cp)
  cs = _state()
  cc = SimpleNamespace(latActive=True, actuators=_Actuators())

  actuators, can_sends = controller.update(cc, cs, 0, None)

  assert can_sends
  assert {msg[2] for msg in can_sends} == {0, 2}
  assert all(len(msg[1]) == 8 for msg in can_sends)
  assert 0.0 < actuators.steeringAngleDeg < 540.0

  lca5 = next(msg for msg in can_sends if msg[0] == 0x67)
  data = lca5[1]
  assert data[2] == checksum_lca_5_message(data[0], data[1], data[3], data[4], data[5])


def test_controller_relays_stock_lca5_angle_when_inactive():
  cp = CarInterface.get_non_essential_params("VOLVO_XC40_RECHARGE")
  controller = CarController(DBC[cp.carFingerprint], cp)
  cs = _state()
  cs.msg_lca_5["LCA_5_STEER"] = 12.0
  cc = SimpleNamespace(latActive=False, actuators=_Actuators())

  _, can_sends = controller.update(cc, cs, 0, None)
  lca5 = next(msg for msg in can_sends if msg[0] == 0x67)

  # The inactive path must not manufacture a new angle command.
  raw = ((lca5[1][6] & 0x7F) << 8) | lca5[1][7]
  if raw & (1 << 14):
    raw -= 1 << 15
  assert abs(raw * 0.05596 - 12.0) < 0.1
