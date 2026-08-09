import numpy as np


HONDA_HRV_3G_FAR_FOLLOW_BRAKE_SLEW_RATE = 3.0
HONDA_HRV_3G_FAR_FOLLOW_RELEASE_SLEW_RATE = 2.0
HONDA_HRV_3G_UNTRACKED_SLOW_LEAD_DECEL_SCALE = 1.35
GM_SILVERADO_EARLY_FOLLOW_MIN_EGO_SPEED = 18.0
GM_SILVERADO_EARLY_FOLLOW_MAX_DISTANCE = 130.0
GM_SILVERADO_EARLY_FOLLOW_MIN_MODEL_PROB = 0.85
GM_SILVERADO_EARLY_FOLLOW_MAX_LATERAL_OFFSET = 1.2
TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_EGO_SPEED = 2.0
TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_LEAD_SPEED = 0.45
TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_LEAD_DELTA = 0.35
TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_LEAD_ACCEL = 0.35
TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MIN_MODEL_PROB = 0.95
TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_LATERAL_OFFSET = 1.75
TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MIN_BRAKE = 0.18
TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_BRAKE = 0.32


def get_far_follow_output_slew_rates(CP):
  if CP.brand == "honda" and str(CP.carFingerprint) == "HONDA_HRV_3G":
    return (
      HONDA_HRV_3G_FAR_FOLLOW_BRAKE_SLEW_RATE,
      HONDA_HRV_3G_FAR_FOLLOW_RELEASE_SLEW_RATE,
    )
  return 0.0, 0.0


def get_untracked_slow_lead_decel_scale(CP):
  if CP.brand == "honda" and str(CP.carFingerprint) == "HONDA_HRV_3G":
    return HONDA_HRV_3G_UNTRACKED_SLOW_LEAD_DECEL_SCALE
  return 1.0


def is_gm_silverado_early_follow_lead(CP, lead, v_ego):
  """Admit a credible centered vision lead before it becomes a close lead."""
  if (
    CP.brand != "gm" or str(CP.carFingerprint) not in ("CHEVROLET_SILVERADO", "CHEVROLET_SILVERADO_CC") or
    lead is None or not bool(getattr(lead, "status", False)) or bool(getattr(lead, "radar", False)) or
    float(v_ego) < GM_SILVERADO_EARLY_FOLLOW_MIN_EGO_SPEED or
    float(getattr(lead, "dRel", float("inf"))) > GM_SILVERADO_EARLY_FOLLOW_MAX_DISTANCE or
    float(getattr(lead, "modelProb", 0.0)) < GM_SILVERADO_EARLY_FOLLOW_MIN_MODEL_PROB or
    abs(float(getattr(lead, "yRel", 0.0))) > GM_SILVERADO_EARLY_FOLLOW_MAX_LATERAL_OFFSET
  ):
    return False
  return True


def get_toyota_sienna_post_departure_restop_cap(CP, lead, v_ego, accel_min,
                                                stop_distance, now_t, departure_latch_until):
  """Re-arm a stop if a Sienna's lead twitches forward and stops again."""
  if (
    CP.brand != "toyota" or str(CP.carFingerprint) != "TOYOTA_SIENNA_4TH_GEN" or
    now_t >= departure_latch_until or lead is None or not lead.status or
    float(v_ego) > TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_EGO_SPEED
  ):
    return None

  lead_radar = bool(getattr(lead, "radar", False))
  lead_prob = float(getattr(lead, "modelProb", 1.0 if lead_radar else 0.0))
  if not lead_radar and lead_prob < TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MIN_MODEL_PROB:
    return None
  if abs(float(getattr(lead, "yRel", 0.0))) > TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_LATERAL_OFFSET:
    return None

  lead_speed = max(float(getattr(lead, "vLead", 0.0)), 0.0)
  lead_delta = lead_speed - float(v_ego)
  lead_accel = float(getattr(lead, "aLeadK", 0.0))
  max_distance = max(float(stop_distance) + 3.0, 4.5)
  if (
    float(getattr(lead, "dRel", float("inf"))) > max_distance or
    lead_speed > TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_LEAD_SPEED or
    lead_delta > TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_LEAD_DELTA or
    lead_accel > TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_LEAD_ACCEL
  ):
    return None

  speed_factor = float(np.clip(float(v_ego) / TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_EGO_SPEED, 0.0, 1.0))
  closing_factor = float(np.clip((float(v_ego) - lead_speed) / 1.5, 0.0, 1.0))
  hold_brake = TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MIN_BRAKE + 0.08 * speed_factor + 0.06 * closing_factor
  brake_floor = -float(np.clip(
    hold_brake,
    TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MIN_BRAKE,
    TOYOTA_SIENNA_POST_DEPARTURE_RESTOP_MAX_BRAKE,
  ))
  return brake_floor if accel_min >= 0.0 else max(float(accel_min), brake_floor)
