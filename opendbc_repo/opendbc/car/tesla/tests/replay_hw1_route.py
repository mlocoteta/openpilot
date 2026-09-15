#!/usr/bin/env python3
"""Offline AP1/HW1 CAN, radar, controller, and panda-safety replay.

Usage: PYTHONPATH=. python -m opendbc.car.tesla.tests.replay_hw1_route PATH_TO_RLOGS

The supplied Pre-AP recording contains stock AP commands copied to bus 0 while
ELM327/old firmware forwarded traffic. The counterfactual run skips those copies:
the HW1 safety mode blocks stock 0x488/0x2b9 forwarding on bus 2. This is NOT a
physical HW1 drive; it cannot validate engagement or steering actuation on-car.
"""

import argparse
from collections import Counter
from pathlib import Path

from cereal import custom
from openpilot.tools.lib.logreader import LogReader
from opendbc.car import Bus, structs
from opendbc.car.tesla.carcontroller import CarController
from opendbc.car.tesla.carstate import CarState
from opendbc.car.tesla.interface import CarInterface
from opendbc.car.tesla.radar_interface import RadarInterface
from opendbc.car.tesla.values import CAR, DBC, TeslaSafetyFlags
from opendbc.safety.tests.libsafety import libsafety_py


def replay(paths: list[Path], simulate_active: bool = False):
  fp = {0: {0x201: 5}, 1: {}, 2: {}}
  cp = CarInterface.get_params(CAR.TESLA_MODEL_S_HW1, fp, [], True, False, False, None)
  assert cp.safetyConfigs[0].safetyModel == structs.CarParams.SafetyModel.tesla
  assert cp.safetyConfigs[0].safetyParam == TeslaSafetyFlags.FLAG_HW1.value | TeslaSafetyFlags.LONG_CONTROL.value
  safety = libsafety_py.libsafety
  assert safety.set_safety_hooks(int(structs.CarParams.SafetyModel.tesla), cp.safetyConfigs[0].safetyParam) == 0
  safety.init_tests()

  parsers = CarState.get_can_parsers(cp)
  cs = CarState(cp, custom.StarPilotCarParams.new_message())
  controller = CarController(DBC[CAR.TESLA_MODEL_S_HW1], cp)
  active_controller = CarController(DBC[CAR.TESLA_MODEL_S_HW1], cp) if simulate_active else None
  radar = RadarInterface(cp)
  stats = Counter()
  first_rejected = []
  active_rejected = []
  last_ap_command: dict[tuple[int, bytes], int] = {}
  suppressed_examples = []

  for path in paths:
    for event in LogReader(str(path)):
      if event.which() != "can":
        continue
      t = event.logMonoTime
      frames = [(x.address, bytes(x.dat), x.src) for x in event.can]
      stock_in_event = {(a, d) for a, d, b in frames if b == 2 and a in (0x488, 0x2b9)}
      for a, d, b in frames:
        if b == 2 and a in (0x488, 0x2b9):
          last_ap_command[(a, d)] = t
        if b == 0 and a in (0x488, 0x2b9):
          seen = last_ap_command.get((a, d), -1)
          if (a, d) in stock_in_event or (0 <= t - seen < 250_000_000):
            stats["suppressed_bus0_stock_copies"] += 1
            continue
          stats["unmatched_bus0_stock_commands"] += 1
          if len(suppressed_examples) < 5:
            suppressed_examples.append((path.name, t, hex(a), d.hex()))
        if b < 128:
          stats["physical_rx"] += 1
          if not safety.safety_rx_hook(libsafety_py.make_CANPacket(a, b, d)):
            stats["rx_rejected"] += 1
          if b == 2 and a in (0x488, 0x2b9):
            stats["stock_forward_blocked"] += safety.safety_fwd_hook(b, a) == -1

      safety.set_timer((t // 1000) & 0xffffffff)
      safety.safety_tick_current_safety_config()
      stats["safety_invalid_ticks"] += not safety.safety_config_valid()
      stats["relay_malfunction_ticks"] += safety.get_relay_malfunction()
      stats["controls_allowed_ticks"] += safety.get_controls_allowed()

      batch = [(t, frames)]
      for parser in parsers.values():
        parser.update(batch)
        stats["invalid_car_parser_ticks"] += not parser.can_valid
      out, _ = cs.update(parsers, None)
      cs.out = out
      stats["carstate_faulted_ticks"] += out.accFaulted
      stats["seatbelt_unlatched_ticks"] += out.seatbeltUnlatched
      stats["steering_inhibited_ticks"] += out.steerFaultTemporary
      stats["cruise_engaged_ticks"] += out.cruiseState.enabled

      radar_data = radar.update(batch)
      if radar_data is not None:
        stats["radar_updates"] += 1
        stats["radar_points"] += len(radar_data.points)
        stats["radar_error_updates"] += radar_data.errors.canError or radar_data.errors.radarFault

      cc = structs.CarControl.new_message()
      cc.actuators.steeringAngleDeg = out.steeringAngleDeg
      cc.actuators.accel = 0.
      # Do not fabricate engagement on the actual faulted/standby route.
      _, sends = controller.update(cc.as_reader(), cs, t, None)
      for a, d, b in sends:
        stats["generated_tx"] += 1
        stats[f"generated_{hex(a)}"] += 1
        if not safety.safety_tx_hook(libsafety_py.make_CANPacket(a, b, d)):
          stats["tx_rejected"] += 1
          if len(first_rejected) < 5:
            first_rejected.append((path.name, t, hex(a), d.hex(), out.steeringAngleDeg, safety.get_relay_malfunction()))

      if active_controller is not None:
        # A synthetic gate test only. This recording never engaged cruise, so
        # enabling controls here does NOT represent an actual car-state transition.
        eligible = (not (out.steerFaultTemporary or out.steerFaultPermanent or out.steeringDisengage or out.accFaulted or
                         out.gasPressed or out.brakePressed or out.stockAeb or out.stockLkas) and out.vEgoRaw > 2.)
        simulated = structs.CarControl.new_message()
        simulated.latActive = eligible
        simulated.longActive = eligible
        simulated.actuators.steeringAngleDeg = out.steeringAngleDeg
        simulated.actuators.accel = 0.5 if eligible else 0.
        _, active_sends = active_controller.update(simulated.as_reader(), cs, t, None)
        if eligible:
          stats["simulated_eligible_ticks"] += 1
          safety.set_controls_allowed(True)
          for a, d, b in active_sends:
            stats["simulated_tx"] += 1
            stats[f"simulated_{hex(a)}"] += 1
            if not safety.safety_tx_hook(libsafety_py.make_CANPacket(a, b, d)):
              stats["simulated_tx_rejected"] += 1
              if len(active_rejected) < 5:
                active_rejected.append((path.name, t, hex(a), d.hex(), out.steeringAngleDeg, out.vEgoRaw))
          safety.set_controls_allowed(False)
      stats["can_events"] += 1
    print(f"{path.name}: {dict(stats)}", flush=True)

  print(f"unmatched bus-0 command examples: {suppressed_examples}")
  print(f"rejected TX examples: {first_rejected}")
  print(f"rejected synthetic-active TX examples: {active_rejected}")
  print(f"final: {dict(stats)}")
  return stats


if __name__ == "__main__":
  argp = argparse.ArgumentParser(description=__doc__)
  argp.add_argument("rlogs", type=Path, help="directory containing segment rlog.zst files")
  argp.add_argument("--simulate-active", action="store_true", help="force safety engagement only on healthy standby samples")
  args = argp.parse_args()
  files = sorted(args.rlogs.glob("*.rlog.zst"))
  if not files:
    argp.error("no *.rlog.zst files found")
  replay(files, args.simulate_active)
