#pragma once

// Honda 9G Accord gen1 Torque Interceptor (TI): an aftermarket steering board on bus 0.
// openpilot steers it with 0x249 TI_STEERING_CONTROL. 0x249 is only in the TX table, and only
// passes this hook, when the Nidec safety param carries HONDA_PARAM_TORQUE_INTERCEPTOR
// (HondaSafetyFlags.TORQUE_INTERCEPTOR in opendbc/car/honda/values.py). Every other Nidec
// profile check sees the param with this bit removed (honda_ti_reset). Stock AOL sees the raw
// word, except for the one TI AOL word below (honda_ti_stock_aol_param).
//
// TI always-on lateral (F05): the TI car reuses 7.0's Nidec pedal AOL policy (honda_stock_aol.h)
// instead of a TI-specific rule. Its word is NIDEC_ALT|GAS_INTERCEPTOR|NIDEC_PEDAL_AOL|TI
// (548|4096 = 4644) with alternativeExperience 32, set by the host AOL policy on top of the TI
// bit. The 9G sends the sources that policy validates (0x190 EPS status, 0x191 gear, 0x1A6 MAIN
// with checksums/counters). lateral_controls_allowed() then follows the policy's permission:
// fresh MAIN on (<=300 ms), drive gear, known EPS status, healthy RX, a physical grant (MAIN or
// LKAS edge, or engagement) and a current host lateral request. Any other TI word (4|TI, 36|TI,
// any extra bit) keeps the TI bit in what stock AOL sees, which no stock AOL word matches.

#define HONDA_TI_STEERING_CONTROL 0x249U
#define HONDA_TI_MAX_STEER 599  // TI_LIMITS.TI_STEER_MAX in opendbc/car/honda/torque_interceptor.py
#define HONDA_PARAM_TORQUE_INTERCEPTOR 4096U

static bool honda_ti = false;

static const CanMsg HONDA_TI_N_TX_MSGS[] = {
  {0xE4, 0, 5, .check_relay = true},
  {0x194, 0, 4, .check_relay = true},
  {0x1FA, 0, 8, .check_relay = false},
  {0x30C, 0, 8, .check_relay = true},
  {0x33D, 0, 5, .check_relay = true},
  {HONDA_TI_STEERING_CONTROL, 0, 8, .check_relay = false},
};

static const CanMsg HONDA_TI_N_INTERCEPTOR_TX_MSGS[] = {
  {0xE4, 0, 5, .check_relay = true},
  {0x194, 0, 4, .check_relay = true},
  {0x1FA, 0, 8, .check_relay = false},
  {0x30C, 0, 8, .check_relay = true},
  {0x33D, 0, 5, .check_relay = true},
  {0x200, 0, 6, .check_relay = false},
  {HONDA_TI_STEERING_CONTROL, 0, 8, .check_relay = false},
};

// Returns the Nidec param without the TI bit.
static uint16_t honda_ti_reset(uint16_t param) {
  honda_ti = GET_FLAG(param, HONDA_PARAM_TORQUE_INTERCEPTOR);
  return (uint16_t)(param & (uint16_t)(~HONDA_PARAM_TORQUE_INTERCEPTOR));
}

// The Nidec word stock AOL may see for this init: the TI bit is removed only from the exact 9G
// pedal AOL word (NIDEC_ALT|GAS_INTERCEPTOR|NIDEC_PEDAL_AOL = 548). Call after honda_ti_reset.
static uint16_t honda_ti_stock_aol_param(uint16_t raw_param) {
  const uint16_t base = (uint16_t)(raw_param & (uint16_t)(~HONDA_PARAM_TORQUE_INTERCEPTOR));
  return (honda_ti && (base == 548U)) ? base : raw_param;
}

static bool honda_ti_tx(const CANPacket_t *msg) {
  bool allowed = honda_ti && msg_matches(msg, HONDA_TI_STEERING_CONTROL, 0U, 8U);
  if (allowed) {
    // LKAS_REQUEST is a 12-bit unsigned field with a +2048 offset (see _ti_steering.dbc), so
    // neutral is 0x800 on the wire, not 0x000. Decode the offset before the zero check, or
    // neutral reads as non-zero and is blocked whenever lateral is off. Rate and driver
    // limits are applied upstream; this is the hard magnitude cap.
    const uint32_t ti_raw = (((uint32_t)msg->data[0] & 0x0FU) << 8) | (uint32_t)msg->data[1];
    const int ti_steer = (int)ti_raw - 2048;
    if (!lateral_controls_allowed()) {
      allowed = ti_steer == 0;
    } else {
      allowed = (ti_steer <= HONDA_TI_MAX_STEER) && (ti_steer >= -HONDA_TI_MAX_STEER);
    }
  }
  return allowed;
}
