import time


NORMAL_BUS_LAYOUT = {(2, 0x110): 32, (2, 0x362): 32, (1, 0x35): 32,
                     (1, 0xEA): 24, (1, 0xA0): 24, (1, 0x1A0): 32,
                     (1, 0x1CF): 8, (0, 0x3A5): 24}


# Classic HKG steering, chassis and stock SCC are already visible on normal
# harness wiring. This selects a diagnostic query family, never a vehicle or
# control profile. Fresh firmware and CAN fingerprinting still own identity.
CLASSIC_NORMAL_BUS_LAYOUT = {(0, 0x251): 8, (0, 0x386): 8, (0, 0x394): 8,
                            (0, 0x4F1): 4, (2, 0x340): 8, (0, 0x420): 8, (0, 0x421): 8}


HDA1_NORMAL_BUS_LAYOUT = {(0, 0x120): 32, (2, 0x120): 32, (0, 0x35): 32, (0, 0xEA): 24,
                         (0, 0xA0): 24, (0, 0x1A0): 32, (0, 0x1CF): 8, (0, 0x130): 16}


def normal_bus_topology(can_recv, *, clock=time.monotonic):
  deadline = clock() + .12
  layouts = (NORMAL_BUS_LAYOUT, CLASSIC_NORMAL_BUS_LAYOUT)
  observed = [{} for _ in layouts]
  hda1_observed = {}
  hda1_invalid = False
  for _ in range(24):
    if clock() >= deadline:
      break
    for packet in can_recv(wait_for_one=True):
      for frame in packet:
        key = (frame.src, frame.address)
        for layout, received in zip(layouts, observed, strict=True):
          if key in layout:
            length = len(frame.dat)
            if length != layout[key]:
              return False
            received[key] = length
        if key in HDA1_NORMAL_BUS_LAYOUT:
          if len(frame.dat) != HDA1_NORMAL_BUS_LAYOUT[key]:
            hda1_invalid = True
          else:
            hda1_observed[key] = len(frame.dat)
    if (any(received == layout for layout, received in zip(layouts, observed, strict=True)) or
        not hda1_invalid and hda1_observed == HDA1_NORMAL_BUS_LAYOUT):
      return True
  return False
