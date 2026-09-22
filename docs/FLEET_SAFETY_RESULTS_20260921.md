# Fleet offline audit — September 21, 2026

This is a first-pass fault and coverage inventory, not fleet driving clearance.
No hardware was accessed and no controller or safety policy was changed by this
audit. Other work was concurrently modifying the checkout; per-case source and
library hashes identify the tested implementations.

The full debug-library run visited all 345 platforms. It evaluated both recorded
and AOL-main scenarios for 287 registered routes, plus 108 missing-route entries:

| Result | Cases |
|---|---:|
| Pass within the stated scope | 103 |
| Failed checks, requiring triage | 123 |
| Missing coverage | 288 |
| Could not evaluate | 168 |
| Total | 682 |

These are case counts, not numbers of unsafe cars. Missing coverage includes all
108 platforms without routes and segments without active transitions. Evaluation
errors include unavailable recordings and identities that do not match the
registered platform after the existing fingerprint migration. Old logs must be
normalized explicitly, not quietly substituted for another car.

Full local evidence is under
`selfdrive/car/tests/fleet_results/full_fleet/results.json`, with per-shard build,
case and worker logs. Generated evidence is ignored by Git.

The follow-up full release-library run also completed 682 cases: **102 pass,
153 failed, 289 uncovered, 138 evaluation errors**. Evidence is under
`selfdrive/car/tests/fleet_results/release_fleet_checked/results.json`.
The two batches had different download availability and ran against a changing
working tree; their count difference is not an isolated debug-versus-release
experiment. Both correctly exit nonzero. The release batch is not fleet clearance.

## Confirmed distinctions from failure triage

**Hyundai Custin — controller/safety capability mismatch.** The registered
segment `0bbe367c98fa1538/2023-09-16--00-16-49/2` contains 600 camera-bus
messages at 0x53e, all eight bytes, none six. `CarInterfaceBase.get_starpilot_params`
in `opendbc_repo/opendbc/car/interfaces.py` enables HAS_LKAS12 by address alone.
Hyundai `CarState.update` and `CarController.update` then produce six-byte LKAS12
replacements. In `opendbc_repo/opendbc/safety/modes/hyundai.h`,
`hyundai_rx_all_hook` only enables replacement after receiving a six-byte camera
message, and `hyundai_tx_hook` correctly rejects the unsolicited replacement.
Both scenarios reject 5,799 such packets. A fresh-library probe also reproduced
the six-byte/eight-byte distinction. Repair requires a controller capability and
parser regression test; do not broaden the safety allowlist to hide the mismatch.

**Honda Civic Bosch — incompatible historical control requests.** All 5,997
recorded requests in the inspected 2020 fixture have enabled/latActive/longActive
false but resume true; all 6,000 cruise-state CAN messages are disabled. Current
controller output is RES_ACCEL at 0x296, which current safety correctly blocks.
The AOL probe suppresses resume and passes. Investigate historical command/schema
semantics before calling this a current steering defect.

**Ford Escape — mid-segment initialization artifact.** The first cruise-enabled
0x165 enables controls, but the immediately following 0x202 reaches
`speed_mismatch_check` before safety has nonzero speed history. Controls are
revoked; cruise stays enabled for the entire segment so `pcm_cruise_check` sees
no new rising edge. Relay health remains good. This reproduces with both recorded
and default alternative experience. A two-second scoring warmup does not repair
the latch. This needs recorded preroll/initialization coverage, not force-setting
`controls_allowed` or changing vehicle safety.

## Tesla and AOL scope

In the full debug-library run, the Model 3 route and the second Model Y route
passed both scenarios. The first Model Y route lacked a lateral transition;
its AOL case also lacked requested steering under AOL-only safety permission.
Model X was uncovered as a current dashcam-only configuration. The Model S HW1
and Pre-AP entries have no registered routes. None of these findings reproduces
or disproves the exact hackathon oscillation without its trace.

The separate actual StarPilotCard synthetic-input suite passed 964 checks with
72 explicit active-sequence gaps. All 345 disabled configurations were checked;
309 platforms completed both active modes. These tests check state-machine gates
and stable sequences, not the entire selfdrived-to-Panda feedback loop.

The test-harness regressions pass 34 tests. They cover pre-hook AOL authorization,
strict configuration/bus routing, rejected active packets, expected negative
checks, empty activity, worker crashes, stale reports and build failures.

See `FLEET_SAFETY_TESTING.md` for commands, CI scope and limitations. The workflow
has been added locally but not published or run on GitHub, and branch protection
has not been changed. The full fleet is not green.
