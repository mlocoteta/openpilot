#pragma once

#include "opendbc/safety/declarations.h"

#define TESLA_LEGACY_FLAG_HW1 8U

static bool tesla_external_panda = false;
static bool tesla_hw1 = false;
static bool tesla_hw2 = false;
static bool tesla_hw3 = false;
static bool tesla_legacy_longitudinal = false;

static int chassis_bus = 0U;
static int das_control_msg = 0x2bfU;
static int di_torque1_msg = 0x106U;

static bool tesla_legacy_stock_aeb = false;
static bool tesla_legacy_stock_lkas = false;
static bool tesla_legacy_stock_lkas_prev = false;

static void tesla_legacy_rx_hook(const CANPacket_t *msg) {
  // EPAS_sysStatus: steering angle, driver hands, and EAC status.
  if (!tesla_external_panda && (msg->bus == 0U) && (msg->addr == 0x370U)) {
    const int angle_meas_new = (((msg->data[4] & 0x3FU) << 8) | msg->data[5]) - 8192U;
    update_sample(&angle_meas, angle_meas_new);

    const int hands_on_level = msg->data[4] >> 6;
    const int eac_status = msg->data[6] >> 5;
    const int eac_error_code = msg->data[2] >> 4;
    steering_disengage = (hands_on_level >= 3) || ((eac_status == 0) && (eac_error_code == 9));
  }

  // ESP_B: ESP_vehicleSpeed.
  if (!tesla_external_panda && (msg->bus == (unsigned)chassis_bus) && (msg->addr == 0x155U)) {
    const float speed = ((msg->data[6] | (msg->data[5] << 8)) * 0.01) * KPH_TO_MS;
    UPDATE_VEHICLE_SPEED(speed);
  }

  // DI_torque1: pedal position. HW1 uses the 0x108 message variant.
  if ((tesla_external_panda || tesla_hw1) && (msg->bus == 0U) && (msg->addr == di_torque1_msg)) {
    gas_pressed = msg->data[6] != 0U;
  }

  if (((tesla_external_panda) && (msg->bus == 0U) && (msg->addr == 0x1f8U)) ||
      ((!tesla_external_panda) && (msg->bus == (unsigned)chassis_bus) && (msg->addr == 0x20aU))) {
    brake_pressed = (((msg->data[0] & 0x0CU) >> 2) != 1U);
  }

  // DI_state: cruise state.
  if (((tesla_external_panda) && (msg->bus == 0U) && (msg->addr == 0x256U)) ||
      ((!tesla_external_panda) && (msg->bus == (unsigned)chassis_bus) && (msg->addr == 0x368U))) {
    const int cruise_state = (msg->data[1] >> 4) & 0x07U;
    const bool cruise_engaged = (cruise_state == 2) || (cruise_state == 3) || (cruise_state == 4) ||
                                (cruise_state == 6) || (cruise_state == 7);
    vehicle_moving = cruise_state != 3;
    pcm_cruise_check(cruise_engaged);
  }

  if (msg->bus == 2U) {
    if ((tesla_external_panda || tesla_hw1) && msg->addr == das_control_msg) {
      tesla_legacy_stock_aeb = (msg->data[2] & 0x03U) == 1U;
    }

    if (!tesla_external_panda && msg->addr == 0x488U) {
      const int steering_control_type = msg->data[2] >> 6;
      const bool stock_lkas_now = steering_control_type == 2;
      if (stock_lkas_now && !tesla_legacy_stock_lkas_prev && !controls_allowed) {
        tesla_legacy_stock_lkas = true;
      }
      if (!stock_lkas_now) {
        tesla_legacy_stock_lkas = false;
      }
      tesla_legacy_stock_lkas_prev = stock_lkas_now;
    }
  }
}

static bool tesla_legacy_tx_hook(const CANPacket_t *msg) {
  const AngleSteeringLimits TESLA_STEERING_LIMITS = {
    .max_angle = 3600,
    .angle_deg_to_can = 10,
    .frequency = 50U,
  };

  const AngleSteeringParams TESLA_LEGACY_STEERING_PARAMS = {
    .slip_factor = -0.0005666493436310427,
    .steer_ratio = 15.,
    .wheelbase = 2.96,
  };

  const LongitudinalLimits TESLA_LONG_LIMITS = {
    .max_accel = 425,
    .min_accel = 288,
    .inactive_accel = 375,
  };

  bool violation = false;

  // DAS_steeringControl: angle is encoded in 0.1 degree units with a 1638.35 offset.
  if (!tesla_external_panda && (msg->addr == 0x488U)) {
    const int raw_angle_can = ((msg->data[0] & 0x7FU) << 8) | msg->data[1];
    const int desired_angle = raw_angle_can - 16384;
    const int steer_control_type = msg->data[2] >> 6;
    const bool steer_control_enabled = steer_control_type == 1;

    violation |= steer_angle_cmd_checks_vm(desired_angle, steer_control_enabled,
                                           TESLA_STEERING_LIMITS, TESLA_LEGACY_STEERING_PARAMS);

    const bool valid_steer_control_type = (steer_control_type == 0) || (steer_control_type == 1);
    violation |= !valid_steer_control_type;
    violation |= tesla_legacy_stock_lkas;
  }

  // DAS_control: HW1 longitudinal control is sent to the powertrain bus (bus 0).
  if ((tesla_external_panda || tesla_hw1) && (msg->addr == das_control_msg)) {
    const int aeb_event = msg->data[2] & 0x03U;
    violation |= aeb_event != 0;
    violation |= tesla_legacy_stock_aeb;

    const int raw_accel_max = ((msg->data[6] & 0x1FU) << 4) | (msg->data[5] >> 4);
    const int raw_accel_min = ((msg->data[5] & 0x0FU) << 5) | (msg->data[4] >> 3);
    if (tesla_legacy_longitudinal) {
      violation |= (raw_accel_max < TESLA_LONG_LIMITS.inactive_accel) &&
                   (raw_accel_min < TESLA_LONG_LIMITS.inactive_accel);
      violation |= longitudinal_accel_checks(raw_accel_max, TESLA_LONG_LIMITS);
      violation |= longitudinal_accel_checks(raw_accel_min, TESLA_LONG_LIMITS);
    } else {
      // Stock ACC may only be cancelled, never spoofed or accelerated.
      const int acc_state = msg->data[1] >> 4;
      violation |= acc_state != 13;
      violation |= (raw_accel_max != TESLA_LONG_LIMITS.inactive_accel) ||
                   (raw_accel_min != TESLA_LONG_LIMITS.inactive_accel);
    }
  }

  return !violation;
}

static bool tesla_legacy_fwd_hook(int bus_num, int addr) {
  bool block_msg = false;

  if (bus_num == 2) {
    if (!tesla_external_panda && !tesla_hw1 && (addr == 0x27dU)) {
      block_msg = true;
    }
    if (!tesla_external_panda && (addr == 0x488U) && !tesla_legacy_stock_lkas) {
      block_msg = true;
    }
    if ((tesla_external_panda || tesla_hw1) && (addr == das_control_msg) && !tesla_legacy_stock_aeb) {
      block_msg = true;
    }
  }

  return block_msg;
}

static safety_config tesla_legacy_init(uint16_t param) {
  const int TESLA_FLAG_EXTERNAL_PANDA = 4;
  const int TESLA_FLAG_HW2 = 16;
  const int TESLA_FLAG_HW3 = 32;

  tesla_external_panda = GET_FLAG(param, TESLA_FLAG_EXTERNAL_PANDA);
  tesla_hw1 = GET_FLAG(param, TESLA_LEGACY_FLAG_HW1);
  tesla_hw2 = GET_FLAG(param, TESLA_FLAG_HW2);
  tesla_hw3 = GET_FLAG(param, TESLA_FLAG_HW3);
  tesla_legacy_longitudinal = GET_FLAG(param, 1);

  tesla_legacy_stock_aeb = false;
  tesla_legacy_stock_lkas = false;
  tesla_legacy_stock_lkas_prev = false;
  chassis_bus = 0U;
  di_torque1_msg = 0x106U;
  das_control_msg = tesla_external_panda ? 0x2bfU : 0x2b9U;

  static const CanMsg TESLA_TX_LEGACY_MSGS[] = {
    {0x488, 0, 4, .check_relay = true, .disable_static_blocking = true},
    {0x27D, 0, 3, .check_relay = true, .disable_static_blocking = true},
  };

  static const CanMsg TESLA_LEGACY_PT_MSGS[] = {
    {0x2bf, 0, 8, .check_relay = true, .disable_static_blocking = true},
  };

  static const CanMsg TESLA_TX_LEGACY_HW1_MSGS[] = {
    {0x488, 0, 4, .check_relay = true, .disable_static_blocking = true},
    {0x2b9, 0, 8, .check_relay = true, .disable_static_blocking = true},
  };

  static RxCheck tesla_legacy_pt_rx_checks[] = {
    {.msg = {{0x106, 0, 8, 100U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x1f8, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x2bf, 2, 8, 25U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x256, 0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
  };

  static RxCheck tesla_legacy_hw1_rx_checks[] = {
    {.msg = {{0x108, 0, 8, 100U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x2b9, 2, 8, 25U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x370, 0, 8, 25U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x155, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x20a, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x368, 0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x488, 2, 4, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
  };

  static RxCheck tesla_legacy_hw2_rx_checks[] = {
    {.msg = {{0x370, 0, 8, 25U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x155, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x20a, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x368, 0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x488, 2, 4, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
  };

  static RxCheck tesla_legacy_hw3_rx_checks[] = {
    {.msg = {{0x370, 0, 8, 100U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x155, 1, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x20a, 1, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x368, 1, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
    {.msg = {{0x488, 2, 4, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, {0}, {0}}},
  };

  if (tesla_external_panda && (tesla_hw3 || tesla_hw2)) {
    return BUILD_SAFETY_CFG(tesla_legacy_pt_rx_checks, TESLA_LEGACY_PT_MSGS);
  }
  if (tesla_hw3) {
    chassis_bus = 1U;
    return BUILD_SAFETY_CFG(tesla_legacy_hw3_rx_checks, TESLA_TX_LEGACY_MSGS);
  }
  if (tesla_hw1) {
    di_torque1_msg = 0x108U;
    return BUILD_SAFETY_CFG(tesla_legacy_hw1_rx_checks, TESLA_TX_LEGACY_HW1_MSGS);
  }
  return BUILD_SAFETY_CFG(tesla_legacy_hw2_rx_checks, TESLA_TX_LEGACY_MSGS);
}

const safety_hooks tesla_legacy_hooks = {
  .init = tesla_legacy_init,
  .rx = tesla_legacy_rx_hook,
  .tx = tesla_legacy_tx_hook,
  .fwd = tesla_legacy_fwd_hook,
};
