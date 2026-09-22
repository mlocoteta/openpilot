# Offline fleet controller and safety checks

The runner in `selfdrive/car/tests/fleet_safety.py` enumerates every platform in
the current checkout and uses `opendbc.car.tests.routes`. It runs current
CarInterface/CarState/CarController code against recorded CAN and actuator
requests, then checks each newly generated CAN packet with freshly compiled
current safety hooks. It never connects to a Panda or starts vehicle processes.

Run from the repository root with the repository Python environment:

```sh
python -m selfdrive.car.tests.fleet_safety --inventory
python -m selfdrive.car.tests.fleet_safety --platform TESLA_MODEL_Y --release
python -m selfdrive.car.tests.fleet_safety --all --release
```

An isolated dependency set is in `selfdrive/car/tests/fleet_requirements.txt`.
The runner needs a C compiler. It does not use a previously staged libsafety.
Without `--release`, the safety library enables ALLOW_DEBUG, like the existing
safety unit tests. Release checks are needed as well: a debug-only hook must not
be mistaken for an available production configuration. Release host builds retain
unused-variable warnings without treating that specific diagnostic as an error.

For parallel runs, use separate output directories:

```sh
python -m selfdrive.car.tests.fleet_safety --all --release \
  --shard-count 8 --shard-index 0 --out selfdrive/car/tests/fleet_results/shard_0
```

Run indices 0 through 7. Each has its own library copies, worker processes,
parameter namespace, logs and results. `--local-log` allows a local rlog for one
explicitly selected platform. Route IDs and old fingerprint aliases must match;
the harness does not silently treat another vehicle's log as that platform.

## What is checked

- Recorded commands under the current default feature configuration.
- A separate AOL MAIN-availability controller/safety probe, using recorded
  actuator values with longitudinal requests and cruise button requests off.
- Actual per-Panda safety model, CP/FPCP safety-param OR, alternative-experience
  OR, and strict four-bus routing, matching production configuration assembly.
- Incoming CAN, current CarState validity and safety receive health.
- Every emitted TX, including inactive-state packets; unexpected rejection fails.
- Pre-hook normal/AOL/longitudinal permissions, so a rejection that revokes
  authorization cannot disappear from the failure accounting.
- Active requests, accepted active TX, engagement transitions, and AOL-only
  safety authorization coverage. Sparse commands and absent transitions cannot
  qualify as complete coverage.

There is a two-second unscored fixture startup interval. Controller and safety
history still receive messages during it. The harness does not force safety
authorization or clear a relay fault to manufacture a passing result.

## Results are deliberately strict

`pass` means the case satisfied these specific checks and coverage requirements.
`failed` means a hook/health check failed and needs investigation. `uncovered`
means the scenario was not demonstrated, including missing routes, dashcam-only
interfaces and segments without transitions. `error` means the case could not be
evaluated, such as download failure or mismatched fixture identity. Anything
other than pass makes the command exit nonzero. Existing `non_tested_cars`
exemptions remain visible coverage gaps.

Reports include frame counters, bounded rejected packet evidence, source hashes,
effective safety configurations and build provenance. Worker results carry a
unique execution ID; a crash, stale result or inconsistent exit code cannot be
reused as a pass. JSON and logs live under the ignored `fleet_results` directory.

The AOL probe is **not** a complete simulation of StarPilotCard, selfdrived,
controls mismatch handling or a vehicle ECU. Recorded commands may also reflect
historical settings different from current defaults. A blocked historical resume
request is not automatically a steering bug. Investigate each failure before
changing code. Do not widen safety permissions to make tests green.

## Continuous integration and remaining coverage

`starpilot/controls/tests/test_fleet_aol.py` separately exercises the actual
StarPilotCard state machine with isolated synthetic inputs for every platform.
It tests feature-off behavior, steady engagement, AOL-only operation, brake
pause, native/StarPilot immediate-disable alerts, calibration and gear gates.
It uses empty firmware/fingerprint fixtures, so optional vehicle configurations
are not covered by these sequences. Run it with a compatible built host runtime:

```sh
python -m pytest --noconftest -o addopts='' -q starpilot/controls/tests/test_fleet_aol.py
```

The first run passed 964 checks and explicitly skipped 72 active sequences:
309 platforms exercised both active modes; 36 platforms had two gaps each
(30 dashcam-only, one notCar, four Volvo policy exclusions, one Pre-AP external
authorization dependency). All 345 feature-off checks passed. A separate
Pre-AP authorization input boundary test is synthetic, not proof of actual
Panda authorization. These tests were run against the current working tree,
including concurrent Pre-AP changes; they do not certify an earlier commit.
The lightweight CI workflow below does not build the native runtime required
by this separate state-machine suite.

`.github/workflows/fleet_safety.yaml` adds harness tests and eight release-mode
recorded-route shards on relevant pull requests and manual runs. Missing coverage
is not converted to a skip or allowed failure. The current fleet is not green;
this workflow will expose that fact. It has not been executed on GitHub from this
local task. Requiring it for merge also needs repository branch protection; a
workflow file alone does not change repository settings.

As of the first September 21 inventory there are 345 platforms, 287 registered
routes across 237 platforms, and 108 platforms with no registered route. A route
entry does not guarantee valid, downloadable logs or all necessary maneuvers.
Every optional harness, longitudinal mode, safety parameter, firmware generation
and AOL configuration still needs explicit coverage. Offline checks reduce
blind spots; they do not certify every physical vehicle or reproduce an incident
whose CAN trace was not retained.
