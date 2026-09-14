#include "fake_stm.h"
#include "config.h"
#include "can.h"

bool can_init(uint8_t can_number) { return true; }
void process_can(uint8_t can_number) { }
//int safety_tx_hook(CANPacket_t *to_send) { return 1; }

typedef struct harness_configuration harness_configuration;
void refresh_can_tx_slots_available(void);
void can_tx_comms_resume_usb(void) { };
void can_tx_comms_resume_spi(void) { };

#include "health.h"
#include "faults.h"
#include "libc.h"
#include "boards/board_declarations.h"
#include "opendbc/safety/safety.h"
#include "main_definitions.h"
#include "drivers/can_common.h"

can_ring *rx_q = &can_rx_q;
can_ring *tx1_q = &can_tx1_q;
can_ring *tx2_q = &can_tx2_q;
can_ring *tx3_q = &can_tx3_q;

void set_ignition_can_for_test(bool enabled) {
  ignition_can = enabled;
}

bool get_ignition_can_for_test(void) {
  return ignition_can;
}

void set_ignition_can_cnt_for_test(uint32_t cnt) {
  ignition_can_cnt = cnt;
}

uint32_t get_ignition_can_cnt_for_test(void) {
  return ignition_can_cnt;
}

#include "comms_definitions.h"
#include "can_comms.h"
