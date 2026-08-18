import pytest

from opendbc.car.nissan import nissancan


@pytest.mark.parametrize(
  ("raw_command", "frame", "active", "expected"),
  [
    (5320, 0, False, "dc53a2ac1b000e03"),
    (6144, 0, True, "ff6090ac5b000e03"),
    (8191, 15, True, "007f8fac5b00fe0c"),
    (4096, 0, True, "ff40b0ac5b000e03"),
    (2518, 0, True, "a827d5ac5b000e09"),
  ],
)
def test_leaf_accel_command_vectors(raw_command, frame, active, expected):
  addr, dat, bus = nissancan.create_accel_command(raw_command, frame, active)

  assert addr == 0x2B0
  assert bus == 1
  assert dat.hex() == expected


@pytest.mark.parametrize(
  ("pressure", "frame", "active", "brake_mode", "expected"),
  [
    (0, 0, False, False, "000000006400ff27"),
    (8, 3, True, False, "008000006483ff2a"),
    (142, 2, True, True, "08e000006486ff95"),
  ],
)
def test_leaf_brake_command_vectors(pressure, frame, active, brake_mode, expected):
  addr, dat, bus = nissancan.create_brake_command(pressure, frame, active, brake_mode)

  assert addr == 0x1C3
  assert bus == 1
  assert dat.hex() == expected
  assert dat[7] == (0x01 + 0xC3 + sum(dat[:7])) & 0xFF
