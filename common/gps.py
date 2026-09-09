from openpilot.common.params import Params


def get_gps_location_service(params: Params) -> str:
  if params.get_bool("UbloxAvailable") or params.get_bool("CarGpsAvailable"):
    return "gpsLocationExternal"
  else:
    return "gpsLocation"
