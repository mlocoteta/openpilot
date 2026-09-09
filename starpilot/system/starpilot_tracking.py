#!/usr/bin/env python3
from openpilot.common.constants import CV
from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.car.cruise import V_CRUISE_MAX
from openpilot.selfdrive.selfdrived.events import STARPILOT_EVENT_NAME
from openpilot.selfdrive.selfdrived.selfdrived import LONGITUDINAL_PERSONALITY_MAP, State
from openpilot.selfdrive.selfdrived.state import ACTIVE_STATES
from openpilot.selfdrive.ui.soundd import StarPilotAudibleAlert

from openpilot.starpilot.common.starpilot_utilities import clean_model_name
from openpilot.starpilot.controls.lib.starpilot_events import RANDOM_EVENT_END, RANDOM_EVENT_START
from openpilot.starpilot.controls.lib.weather_checker import WEATHER_CATEGORIES

class StarPilotTracking:
  def __init__(self, starpilot_planner, starpilot_toggles):
    self.params = starpilot_planner.params

    self.starpilot_events = starpilot_planner.starpilot_events
    self.starpilot_weather = starpilot_planner.starpilot_weather

    self.starpilot_stats = self.params.get("StarPilotStats")
    self.starpilot_stats.pop("CurrentMonthsKilometers", None)
    self.starpilot_stats.pop("ResetStats", None)

    self.drive_added = False
    self.previously_enabled = False

    self.distance_since_override = 0
    self.tracked_time = 0

    self.previous_random_events = set()

    self.previous_alert = None
    self.previous_sound = StarPilotAudibleAlert.none
    self.previous_state = State.disabled

    self.model_name = clean_model_name(starpilot_toggles.model_name)

  def _commit_tracked_time(self, now=None, time_validated=False):
    if not self.previously_enabled or self.tracked_time <= 0:
      return

    if time_validated and now is not None:
      current_month = now.month
      if current_month != self.starpilot_stats.get("Month"):
        self.starpilot_stats.update({
          "CurrentMonthsMeters": 0,
          "Month": current_month
        })

    self.starpilot_stats["StarPilotSeconds"] = self.starpilot_stats.get("StarPilotSeconds", 0) + self.tracked_time

    total_model_times = self.starpilot_stats.get("ModelTimes", {})
    total_model_times[self.model_name] = total_model_times.get(self.model_name, 0) + self.tracked_time
    self.starpilot_stats["ModelTimes"] = total_model_times

    self.starpilot_stats["TrackedTime"] = self.starpilot_stats.get("TrackedTime", 0) + self.tracked_time
    self.tracked_time = 0

    if not self.drive_added:
      self.starpilot_stats["StarPilotDrives"] = self.starpilot_stats.get("StarPilotDrives", 0) + 1
      self.drive_added = True

  def flush(self, now=None, time_validated=False):
    """Persist the current drive, including time since the last stop checkpoint."""
    if not self.previously_enabled:
      return

    self._commit_tracked_time(now, time_validated)
    self.params.put("StarPilotStats", dict(sorted(self.starpilot_stats.items())))

  def update(self, now, time_validated, sm, starpilot_toggles):
    v_cruise = min(sm["carState"].vCruiseCluster, V_CRUISE_MAX) * CV.KPH_TO_MS
    v_ego = max(sm["carState"].vEgo, 0)

    distance_driven = v_ego * DT_MDL
    self.previously_enabled |= sm["selfdriveState"].enabled or sm["starpilotCarState"].alwaysOnLateralEnabled
    self.tracked_time += DT_MDL

    if sm["selfdriveState"].alertType not in (self.previous_alert, ""):
      alert_name = sm["selfdriveState"].alertType.split('/')[0]
      total_events = self.starpilot_stats.get("TotalEvents", {})
      total_events[alert_name] = total_events.get(alert_name, 0) + 1
      self.starpilot_stats["TotalEvents"] = total_events
    self.previous_alert = sm["selfdriveState"].alertType

    if sm["selfdriveState"].enabled:
      key = str(round(v_cruise, 2))
      total_cruise_speed_times = self.starpilot_stats.get("CruiseSpeedTimes", {})
      total_cruise_speed_times[key] = total_cruise_speed_times.get(key, 0) + DT_MDL
      self.starpilot_stats["CruiseSpeedTimes"] = total_cruise_speed_times

    self.starpilot_stats["CurrentMonthsMeters"] = self.starpilot_stats.get("CurrentMonthsMeters", 0) + distance_driven

    if self.starpilot_weather.sunrise != 0 and self.starpilot_weather.sunset != 0:
      if self.starpilot_weather.is_daytime:
        self.starpilot_stats["DayTime"] = self.starpilot_stats.get("DayTime", 0) + DT_MDL
      else:
        self.starpilot_stats["NightTime"] = self.starpilot_stats.get("NightTime", 0) + DT_MDL

    if sm["selfdriveState"].state != self.previous_state:
      if sm["selfdriveState"].state in ACTIVE_STATES and self.previous_state not in ACTIVE_STATES:
        self.starpilot_stats["Engages"] = self.starpilot_stats.get("Engages", 0) + 1
        if starpilot_toggles.sound_pack == "frog":
          self.starpilot_stats["FrogChirps"] = self.starpilot_stats.get("FrogChirps", 0) + 1

      elif sm["selfdriveState"].state == State.disabled and self.previous_state in ACTIVE_STATES:
        self.starpilot_stats["Disengages"] = self.starpilot_stats.get("Disengages", 0) + 1
        if starpilot_toggles.sound_pack == "frog":
          self.starpilot_stats["FrogSqueaks"] = self.starpilot_stats.get("FrogSqueaks", 0) + 1

      if sm["selfdriveState"].state == State.overriding and self.previous_state != State.overriding:
        self.starpilot_stats["Overrides"] = self.starpilot_stats.get("Overrides", 0) + 1

      self.previous_state = sm["selfdriveState"].state

    if sm["selfdriveState"].experimentalMode:
      self.starpilot_stats["ExperimentalModeTime"] = self.starpilot_stats.get("ExperimentalModeTime", 0) + DT_MDL

    self.starpilot_stats["StarPilotMeters"] = self.starpilot_stats.get("StarPilotMeters", 0) + distance_driven

    if sm["starpilotSelfdriveState"].alertSound != self.previous_sound:
      if sm["starpilotSelfdriveState"].alertSound == StarPilotAudibleAlert.goat:
        self.starpilot_stats["GoatScreams"] = self.starpilot_stats.get("GoatScreams", 0) + 1

      self.previous_sound = sm["starpilotSelfdriveState"].alertSound

    self.starpilot_stats["MaxAcceleration"] = max(self.starpilot_events.max_acceleration, self.starpilot_stats.get("MaxAcceleration", 0))

    if sm["carControl"].latActive:
      self.starpilot_stats["LateralTime"] = self.starpilot_stats.get("LateralTime", 0) + DT_MDL
    if sm["carControl"].longActive:
      self.starpilot_stats["LongitudinalTime"] = self.starpilot_stats.get("LongitudinalTime", 0) + DT_MDL

      personality_name = LONGITUDINAL_PERSONALITY_MAP.get(sm["selfdriveState"].personality, "Unknown").capitalize()
      total_personality_times = self.starpilot_stats.get("PersonalityTimes", {})
      total_personality_times[personality_name] = total_personality_times.get(personality_name, 0) + DT_MDL
      self.starpilot_stats["PersonalityTimes"] = total_personality_times
    elif sm["starpilotCarState"].alwaysOnLateralEnabled:
      self.starpilot_stats["AOLTime"] = self.starpilot_stats.get("AOLTime", 0) + DT_MDL

    if sm["selfdriveState"].state in (State.disabled, State.overriding):
      self.distance_since_override = 0
      self.starpilot_stats["OverrideTime"] = self.starpilot_stats.get("OverrideTime", 0) + DT_MDL
    else:
      self.distance_since_override += distance_driven
      self.starpilot_stats["LongestDistanceWithoutOverride"] = max(self.distance_since_override, self.starpilot_stats.get("LongestDistanceWithoutOverride", 0))

    current_random_events = {event for event in self.starpilot_events.events.names if RANDOM_EVENT_START <= event <= RANDOM_EVENT_END}
    if len(current_random_events) > 0:
      new_events = current_random_events - self.previous_random_events
      if new_events:
        total_random_events = self.starpilot_stats.get("RandomEvents", {})
        for event in new_events:
          event_name = STARPILOT_EVENT_NAME[event]
          total_random_events[event_name] = total_random_events.get(event_name, 0) + 1
        self.starpilot_stats["RandomEvents"] = total_random_events

    self.previous_random_events = current_random_events

    if sm["carState"].standstill:
      self.starpilot_stats["StandstillTime"] = self.starpilot_stats.get("StandstillTime", 0) + DT_MDL
      if self.starpilot_events.stopped_for_light:
        self.starpilot_stats["StopLightTime"] = self.starpilot_stats.get("StopLightTime", 0) + DT_MDL

    suffix = "unknown"
    for category in WEATHER_CATEGORIES.values():
      if any(start <= self.starpilot_weather.weather_id <= end for start, end in category["ranges"]):
        suffix = category["suffix"]
        break

    weather_times = self.starpilot_stats.get("WeatherTimes", {})
    weather_times[suffix] = weather_times.get(suffix, 0) + DT_MDL
    self.starpilot_stats["WeatherTimes"] = weather_times

    if self.tracked_time >= 60 and sm["carState"].standstill and self.previously_enabled:
      self._commit_tracked_time(now, time_validated)
      self.params.put_nonblocking("StarPilotStats", dict(sorted(self.starpilot_stats.items())))
