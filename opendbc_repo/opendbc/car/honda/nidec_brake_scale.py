"""Nidec brake scale: m/s^2 of decel per unit (0..1) of the Nidec friction brake command (0x1FA COMPUTER_BRAKE / 256).

Stock openpilot maps both gas and brake at 4.8. Fitting brake command against measured decel on the 2017 Accord 9G
(2026-09-25/26 rlogs, 0-35 m/s) gave 2.8-3.8 m/s^2 per unit, so 4.8 delivered about 70 % of the requested braking.
6.x ran 3.6 on the 9G from 2026-09-26 (8d1f75031, F06 brake half) and got 0.94 of the request. The 7.0 port dropped
it (reports/2026-11-19-brake-shortfall.md: 0.69 of the request, -4.0 requests capped near -2.9 m/s^2).

Brake side only. The gas side, the pedal interceptor command, the PCM speed target and the wind/creep brake tables
(already in brake units) keep the stock 4.8 / stock values. Every other Honda keeps 4.8 on both sides.
No panda safety change: the command is still clipped to NIDEC_BRAKE_MAX - 1 = 255.

Kept in its own module so carcontroller and cruise_brake_deadband share one value without a circular import.
"""
NIDEC_ACCEL_PER_UNIT = 4.8  # stock: gas side for every Nidec, brake side for every Nidec but the 9G
ACCORD_9G_BRAKE_ACCEL_PER_UNIT = 3.6


def nidec_brake_accel_per_unit(car_fingerprint) -> float:
  from opendbc.car.honda.values import CAR
  return ACCORD_9G_BRAKE_ACCEL_PER_UNIT if car_fingerprint == CAR.HONDA_ACCORD_9G else NIDEC_ACCEL_PER_UNIT
