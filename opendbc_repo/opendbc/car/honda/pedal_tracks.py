"""Which way round the pedal interceptor's two sensor tracks are wired, seen from GAS_SENSOR.

Honda's accelerator sensor has two tracks and track 2 reads about twice track 1 (9G Accord rlogs: 236/531 at rest,
2.2x while pressed). With the harness wired the other way round INTERCEPTOR_GAS is the larger one. The
HondaPedalSwapped param (HondaFlags.PEDAL_SIGNALS_SWAPPED) has to match: otherwise every gas command puts the two
tracks out of step at the engine ECU. On a mismatch the controller sends no gas for the rest of the drive.
"""
from opendbc.car.carlog import carlog

MIN_RAW = 100      # both tracks read at least this with the sensor powered (rest ~236 / ~531)
TRACK_RATIO = 1.5  # one track must read at least this much more than the other to count
CONFIRM_FRAMES = 100  # 1 s of carstate updates with the same answer


class PedalTrackCheck:
  def __init__(self, swapped_setting: bool):
    self.swapped_setting = swapped_setting
    self.observed: bool | None = None  # True = tracks swapped, latched once confirmed
    self._candidate: bool | None = None
    self._count = 0

  @property
  def mismatch(self) -> bool:
    return self.observed is not None and self.observed != self.swapped_setting

  def update(self, track1: float, track2: float) -> None:
    if self.observed is not None or min(track1, track2) < MIN_RAW:
      return
    if track2 >= TRACK_RATIO * track1:
      seen = False
    elif track1 >= TRACK_RATIO * track2:
      seen = True
    else:
      return

    if seen != self._candidate:
      self._candidate, self._count = seen, 0
    self._count += 1
    if self._count >= CONFIRM_FRAMES:
      self.observed = seen
      wiring = "swapped" if seen else "normal"
      seen_tracks = f"track1={track1:.0f} track2={track2:.0f}"
      setting = f"HondaPedalSwapped={int(self.swapped_setting)}"
      if self.mismatch:
        carlog.error(f"pedal interceptor tracks look {wiring} ({seen_tracks}) but {setting}: no gas this drive, fix the toggle")
      else:
        carlog.warning(f"pedal interceptor tracks {wiring} ({seen_tracks}), matches {setting}")
