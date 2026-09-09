from openpilot.system.hardware.base import LPABase
from openpilot.system.hardware.tici.hardware import Tici


def test_comma_profile_detection_without_lpa(mocker):
  hardware = Tici()
  modem = mocker.MagicMock()
  modem.Get.return_value = "Quectel"

  mocker.patch.object(hardware, "get_sim_info", return_value={"sim_id": "8985235000000000000"})
  mocker.patch.object(hardware, "get_modem", return_value=modem)
  mocker.patch.object(hardware, "get_device_type", return_value="mici")
  get_sim_lpa = mocker.patch.object(hardware, "get_sim_lpa")
  mocker.patch("openpilot.system.hardware.tici.hardware.os.path.exists", return_value=True)

  hardware.configure_modem()

  get_sim_lpa.assert_not_called()
  assert LPABase.is_comma_profile("8985235000000000000")
  assert not LPABase.is_comma_profile("8900000000000000000")
