#pragma once

// 9G Accord SSV3 steering board (opendbc/car/honda/ssv3.py): it takes 0xE4 STEERING_CONTROL on bus 0 and reads byte 2
// bits 0-3 as board options (_steering_control_d_ssv3.dbc). Bits 2-3 are STEER_CONTROL_ARM on the Bosch Accord's
// angle-loop EPS, so the option ZERO_TORQUE_KEEPS_LKAS_ON alone (bit 3) reads as ARM 2, and the angle setpoint rule in
// honda_tx_hook would block every steering frame of the SSV3 car. That EPS exists only on classic Bosch: on the Nidec
// words an SSV3 9G can run (NIDEC_ALT, + GAS_INTERCEPTOR, + NIDEC_PEDAL_AOL) these bits are options and the angle rule
// is skipped; the Nidec torque rule (no torque without lateral permission) still applies. Every other word keeps the
// angle rule, the TI car included (0xE4 carries zero torque and no options there).
static bool honda_ssv3_options = false;

static void honda_ssv3_reset(uint16_t param, bool ti) {
  honda_ssv3_options = !ti && ((param == 4U) || (param == 36U) || (param == 548U));
}
