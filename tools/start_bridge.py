#!/usr/bin/env python3
"""Start cereal bridge for live PlotJuggler, but only if every service it will
subscribe to has msgq reader headroom.

msgq allows NUM_READERS=15 readers per queue and NEVER decrements the counter when
a subscriber exits -- it only resets to 0 by evicting *all* subscribers (and SIGUSR2-ing
them), which crashes live openpilot processes. Each `systemctl restart comma` therefore
permanently consumes a slot on every queue until the next reboot. So check before adding
one more reader.
"""
import os, struct, subprocess, sys

NUM_READERS = 15
MIN_HEADROOM = 3          # refuse to subscribe unless this many slots are free
BASEDIR = "/data/openpilot"

# Deliberately excludes carState / carControl / selfdriveState: those sit at 12-14/15
# on this fork and are what crashed the device on 2026-09-10.
SERVICES = ["can", "sendcan", "carParams", "pandaStates", "carOutput", "controlsState"]


def num_readers(service):
    path = "/dev/shm/msgq_" + service
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        hdr = f.read(8 * (3 + 3 * NUM_READERS))
    return struct.unpack("<%dQ" % (len(hdr) // 8), hdr)[0]


def main():
    print("checking msgq reader headroom (need >=%d free of %d)" % (MIN_HEADROOM, NUM_READERS))
    blocked = []
    for svc in SERVICES:
        n = num_readers(svc)
        if n is None:
            print("  %-15s no segment yet (ok, will be created)" % svc)
            continue
        head = NUM_READERS - n
        state = "ok" if head >= MIN_HEADROOM else "TOO TIGHT"
        print("  %-15s %2d/%d used, %2d free   %s" % (svc, n, NUM_READERS, head, state))
        if head < MIN_HEADROOM:
            blocked.append((svc, n))

    if blocked:
        print("\nREFUSING TO START. These queues would risk an eviction storm:")
        for svc, n in blocked:
            print("  %s at %d/%d" % (svc, n, NUM_READERS))
        print("\nReboot the device to reset the counters, then retry.")
        return 1

    print("\nheadroom ok -- starting bridge")
    os.chdir(BASEDIR)
    subprocess.Popen(["./cereal/messaging/bridge", ",".join(SERVICES)],
                     stdout=open("/tmp/bridge.log", "w"), stderr=subprocess.STDOUT,
                     stdin=subprocess.DEVNULL, start_new_session=True)
    print("bridge started: %s" % ",".join(SERVICES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
