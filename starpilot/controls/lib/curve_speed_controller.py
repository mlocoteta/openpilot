#!/usr/bin/env python3
import numpy as np

from openpilot.common.constants import CV
from openpilot.common.realtime import DT_MDL

from openpilot.starpilot.common.starpilot_variables import CITY_SPEED_LIMIT, CRUISING_SPEED, DEFAULT_LATERAL_ACCELERATION, PLANNER_TIME

CALIBRATION_PROGRESS_THRESHOLD = 10 / DT_MDL
CSC_MIN_SPEED = CITY_SPEED_LIMIT * CV.MPH_TO_MS
CSC_MAX_DECEL_RATE = 1.5
MAX_CURVATURE = 0.1
MIN_CURVATURE = 0.001
PERCENTILE = 90
ROUNDING_PRECISION = 5
STEP = 0.001


def is_user_overriding_longitudinal(sm):
  try:
    if any(getattr(event, "overrideLongitudinal", False) for event in sm["onroadEvents"]):
      return True
  except (KeyError, TypeError):
    pass

  car_state = sm["carState"]
  starpilot_car_state = sm["starpilotCarState"]
  return bool(
    getattr(car_state, "gasPressed", False) or
    getattr(car_state, "brakePressed", False) or
    getattr(starpilot_car_state, "accelPressed", False)
  )


def is_manual_speed_control(sm):
  """Return whether the driver, rather than longitudinal control, owns speed."""
  return not bool(sm["carControl"].longActive) or is_user_overriding_longitudinal(sm)


class CurveSpeedController:
  def __init__(self, StarPilotVCruise):
    self.starpilot_planner = StarPilotVCruise.starpilot_planner

    self.enable_training = False
    self.target_set = False

    self.training_timer = 0.0
    self.persistence_timer = 0.0
    self.data_dirty = False

    curvature_data = self.starpilot_planner.params.get("CurvatureData")
    self.curvature_data = self._normalize_curvature_data(curvature_data)

    self.required_curvatures = [str(round(road_curvature, ROUNDING_PRECISION)) for road_curvature in np.arange(MIN_CURVATURE, MAX_CURVATURE + STEP, STEP)]

    self.update_lateral_acceleration()

  @staticmethod
  def _bucket_curvature(road_curvature):
    clipped_curvature = float(np.clip(road_curvature, MIN_CURVATURE, MAX_CURVATURE))
    bucket_index = round((clipped_curvature - MIN_CURVATURE) / STEP)
    bucketed_curvature = MIN_CURVATURE + (bucket_index * STEP)
    return str(round(bucketed_curvature, ROUNDING_PRECISION))

  @classmethod
  def _normalize_curvature_data(cls, curvature_data):
    if not isinstance(curvature_data, dict):
      return {}

    normalized = {}
    for key, value in curvature_data.items():
      if not isinstance(value, dict):
        continue

      try:
        raw_curvature = abs(float(key))
        average = float(value["average"])
        count = int(value["count"])
      except (KeyError, TypeError, ValueError):
        continue

      if count <= 0:
        continue

      bucket = cls._bucket_curvature(raw_curvature)
      if bucket in normalized:
        existing = normalized[bucket]
        total_count = existing["count"] + count
        normalized[bucket] = {
          "average": ((existing["average"] * existing["count"]) + (average * count)) / total_count,
          "count": total_count,
        }
      else:
        normalized[bucket] = {
          "average": average,
          "count": count,
        }

    return normalized

  def _persist_data(self):
    if not self.data_dirty:
      return

    progress = 0.0
    for key in self.required_curvatures:
      if key in self.curvature_data:
        progress += min(self.curvature_data[key]["count"] / CALIBRATION_PROGRESS_THRESHOLD, 1.0)

    self.starpilot_planner.params.put_nonblocking("CalibrationProgress", (progress / len(self.required_curvatures)) * 100)
    self.starpilot_planner.params.put_nonblocking("CurvatureData", self.curvature_data)
    self.data_dirty = False
    self.persistence_timer = 0.0

  def flush_data(self):
    self._persist_data()

  def log_data(self, v_ego, sm):
    eligible = (
      v_ego > CRUISING_SPEED and
      not self.starpilot_planner.tracking_lead and
      is_manual_speed_control(sm)
    )
    self.enable_training = False

    if not eligible:
      self.flush_data()
      self.training_timer = 0.0
      self.persistence_timer = 0.0
      return

    self.training_timer += DT_MDL
    if self.data_dirty:
      self.persistence_timer += DT_MDL

    in_curve = (
      self.training_timer >= PLANNER_TIME and
      self.starpilot_planner.driving_in_curve and
      not (sm["carState"].leftBlinker or sm["carState"].rightBlinker)
    )
    if in_curve:
      lateral_acceleration = abs(self.starpilot_planner.lateral_acceleration)
      road_curvature = self._bucket_curvature(abs(self.starpilot_planner.road_curvature))

      if road_curvature in self.curvature_data:
        data = self.curvature_data[road_curvature]
        average = data["average"]
        count = data["count"]
        self.curvature_data[road_curvature] = {
          "average": ((average * count) + lateral_acceleration) / (count + 1),
          "count": count + 1
        }
      else:
        self.curvature_data[road_curvature] = {
          "average": lateral_acceleration,
          "count": 1
        }

      self.data_dirty = True
      self.update_lateral_acceleration()
      self.enable_training = True

      if self.persistence_timer >= PLANNER_TIME:
        self.flush_data()
    elif self.data_dirty:
      self.flush_data()

  def update_lateral_acceleration(self):
    if self.curvature_data:
      all_samples = [data["average"] for data in self.curvature_data.values()]
      self.lateral_acceleration = float(np.percentile(all_samples, PERCENTILE))
    else:
      self.lateral_acceleration = DEFAULT_LATERAL_ACCELERATION

    self.starpilot_planner.params.put_nonblocking("CalibratedLateralAcceleration", self.lateral_acceleration)

  def update_target(self, v_ego):
    lateral_acceleration = self.lateral_acceleration
    if self.starpilot_planner.starpilot_weather.weather_id != 0:
      lateral_acceleration -= self.lateral_acceleration * self.starpilot_planner.starpilot_weather.reduce_lateral_acceleration

    if self.target_set:
      csc_speed = (lateral_acceleration / abs(self.starpilot_planner.road_curvature))**0.5
      csc_speed = max(float(csc_speed), CSC_MIN_SPEED)
      if csc_speed >= v_ego:
        self.target = v_ego
      else:
        time_to_curve = max(float(self.starpilot_planner.time_to_curve), DT_MDL)
        decel_rate = float(np.clip((v_ego - csc_speed) / time_to_curve, 0.0, CSC_MAX_DECEL_RATE))
        self.target = float(np.clip(self.target - decel_rate * DT_MDL, csc_speed, v_ego))
    else:
      self.target_set = True
      self.target = v_ego
