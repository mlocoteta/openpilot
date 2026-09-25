# Lateral characterization (2017 Accord 9G + Torque Interceptor)

A plan-driven mode of `lateral_maneuversd`. When `/data/lateral_characterization_plan.json`
exists and Lateral Maneuver Mode is on, the daemon runs the plan instead of the stock maneuvers.
It works through speed blocks (8/12/15/20/30 mph by default). For each block it switches the
controller settings under test, confirms that controlsd picked them up, runs the block's
maneuvers, then moves to the next block. When the plan finishes, aborts or exits, your own
settings are put back.

Settings under test (all switch live, no restart and no params-key/SCons change):

| variant | SteerDelay | FLM `standard` friction threshold @ 0/5/10/15/25 m/s | TISteerKp |
|---|---|---|---|
| A baseline | manual 0.01 | flat 0.30 | 0.5 |
| B | auto (lagd) | flat | 0.5 |
| C | manual 0.5 | flat | 0.5 |
| F | 0.01 | low-speed 2.0 / 1.2 / 0.45 / 0.35 / 0.30 | 0.5 |
| K | 0.01 | flat | 0.8 |

Maneuvers per block: a 10 s straight hold (noise / ping-pong), ±0.3 and ±0.6 m/s² steps
(+a, −a, +a, 0; held ~3 s, shortened automatically so the predicted offset stays ≤ 3 m), and
sines at 0.2/0.4/0.7 Hz.

Safety limits are enforced when the plan is loaded and again on every frame, so a bad plan
cannot exceed them:
- |lateral accel| ≤ 1.0 m/s², and ≤ 0.6 m/s² at or below 12 mph
- sine frequency ≤ 0.8 Hz
- settings are changed only between maneuvers, while driving straight with hands off and lateral
  engaged for 1 s
- each maneuver needs 2 s of on-speed, straight, flat road with hands off before it starts
- a maneuver is aborted and repeated (up to 4 attempts, then skipped) if you touch the wheel,
  lateral drops out, speed leaves ±0.7 m/s of the target, or the settings drift
- disengaging for 0.5 s puts your settings back and pauses the run. Re-engaging re-applies and
  re-checks the block's settings
- your settings are restored on completion, on abort, when the process exits (car off, mode
  toggled off) and at the next manager start if a snapshot was left behind (power loss)

## Plans

The plan file is only read in Lateral Maneuver Mode. Generate one on the device (or on a PC and
copy it over):

```sh
cd /data/openpilot
PYTHONPATH=/data/openpilot /usr/local/venv/bin/python tools/lateral_maneuvers/characterization/plan.py \
  generate --preset default -o /data/lateral_characterization_plan.json     # 25 blocks, ~40 min
#   --preset quick     8/15/30 mph, variants A,B,F,K, short maneuver set, ~11 min
#   --preset lowspeed  8/12/15 mph, variants A,F,K, ~15 min
#   --speeds 20,30 --variants A,K   any reduced plan (e.g. to finish a drive that was cut short)
PYTHONPATH=/data/openpilot /usr/local/venv/bin/python tools/lateral_maneuvers/characterization/plan.py check
```

`check` prints each block with its settings tag and the clamped maneuvers. **Manual SteerDelay
only works with Advanced Lateral Tune on.** Either turn it on in the StarPilot settings before
the drive, or add `"enable_advanced_lateral_tune": true` to the plan JSON. With that flag the
tool turns it on and restores it afterwards. If neither is done, blocks A/C/F/K cannot confirm
their delay and are skipped after about 40 s each.

**Friction-table blocks (variant F, `friction_table`) need the FLM double-parse fix** that ships
with this tool (`starpilot/common/json_param.py`). Without it StarPilot always broadcast
`flm_active_overrides = {}`, so no FLM table ever reached the controller and every
`friction_table` block was skipped with "settings not confirmed".

### Resume across drives

A plan can span several drives. After every block whose maneuvers **all** completed, the block
id is saved in `/data/lateral_characterization_progress.json` (keyed by a hash of the plan, written
atomically, survives process exit, car off and reboot). The next run skips those blocks and
starts at the first one that is not done; the alert shows `Resuming: block N/M (K done)` for 5 s.

- A block with a skipped maneuver (4 aborted attempts) or settings that could not be confirmed is
  **not** complete. The run moves on and that block is retried on the next drive. A pass that
  leaves such blocks ends with `Pass done: K/M blocks complete`.
- A block interrupted by car off / mode off is not complete and restarts from its first maneuver.
- Once every block is done the screen shows `Characterization finished` and nothing runs (no
  restart from block 1). Reset the progress to run the plan again.
- Editing the plan (any setting, speed, maneuver or limit) changes its hash, so the edited plan
  starts fresh. Progress of other plans stays in the file, so swapping plan files back and forth
  resumes each one.
- Reset: the on-device **Reset Characterization Progress** button, the Galaxy **Reset
  Characterization Progress** button, or
  `PYTHONPATH=/data/openpilot /usr/local/venv/bin/python tools/lateral_maneuvers/characterization/plan.py reset-progress`.
  `plan.py progress` prints which blocks are done.

## Driver procedure

Where to drive:
- **Turn off StarPilot's Curve Speed Controller (CSC) for the test drive.** The tool never
  changes ACC set speed or anything longitudinal, but CSC can slow the car below the block speed
  (especially in the 8–15 mph blocks), and then maneuvers wait at `Set speed to X mph` or abort
  with `speed out of range`. Other speed-limit / map controllers can do the same.
- 8–12 mph blocks: a big, empty parking lot, or a flat, empty, uncrowned service road.
- 15–30 mph blocks: a long, straight, flat road with little crown and no traffic close behind.
  Crown and bank show up as roll and pollute the noise and step data. The tool waits
  ("Waiting: road not flat") when |roll| > 0.08 rad, and the report shows the roll and pitch
  for each block.
- Every maneuver moves the car up to ~3 m sideways. Leave that much clear space on both sides.

Steps:
1. Write the plan (above), then arm the test with one of:
   - on the comma: **Settings → StarPilot → Steering → Advanced Lateral Tuning → Lateral
     Characterization Test** (the section shows with Advanced Lateral Tuning on). Its subtitle
     shows the plan and progress, e.g. `Plan 'default': 7/25 blocks done — resumes at block 8 next
     drive`. It can only be armed when a valid plan file exists; otherwise it is greyed out and
     says why. Below it is **Reset Characterization Progress** (asks for confirmation).
   - the Galaxy lateral maneuvers page (**Start / Arm**; it also shows the progress and has a
     reset button), or `echo -n 1 > /data/params/d/LateralManeuverMode`.

   Arming (either way) sets Lateral Maneuver Mode and turns Longitudinal Maneuver Mode off.
   Arming while onroad works too: the manager starts `lateral_maneuversd` right away.
2. Start the car. The screen shows "Lateral Maneuver Mode". If the plan file is invalid, the
   screen shows "Characterization plan invalid" and the reason on the second line, and nothing
   is sent.
3. Engage openpilot and set ACC to the speed on the second line. The alert's second line always
   reads
   `Block N/M mK/J, <maneuver>, set X mph · <settings tag>`,
   for example `Block 3/25 m2/6, step ±0.3 3.0s, set 8 mph · d0.50 fflat kp0.50`.
4. **Hands off, go straight.** The first line shows the current phase:
   - `Hold straight: applying settings`, then `Verifying: steer_delay, ti_steer_kp…`: the new
     settings are being written and checked (the check usually takes a few seconds).
   - `Set speed to X mph`: wrong speed, or lateral not active.
   - `Waiting: road not straight / road not flat / hands off`
   - `Starting: 2`, `Starting: 1`, then `Active …` (`Active +0.3m/s² 2.1s`, `Active sine 0.4Hz 5.0s`,
     `Active hold 7.5s`): the maneuver is running. Keep hands off.
   - `Complete`: the next maneuver starts by itself.
   - A short flash of `LC settings …` with JSON on the second line is the block's settings,
     logged so they can be read back from the rlog.
5. Moving on happens automatically. There is no button to press. Change the ACC set speed when
   the second line shows a new `set X mph`.
6. **Pause:** disengage (brake or cancel). After 0.5 s your settings are restored and the
   screen shows `Paused: engage to continue`. When you re-engage, the block's settings are
   re-applied and re-checked, and the interrupted maneuver runs again.
   **Abort one maneuver:** touch the wheel. It shows `Aborted: steering touched` and repeats.
7. **Stop:** turn off the toggle / Lateral Maneuver Mode, or turn the car off. Either one ends
   the process, which restores your settings. Completed blocks are kept, so the next drive
   resumes. To stop using characterization altogether, delete
   `/data/lateral_characterization_plan.json`, and the mode goes back to the stock maneuvers.
8. When every block is done, the screen shows `Characterization finished` / `all N blocks done`.
   Pull over, turn the car off, and turn the test toggle off.

## Logs and report

- Sidecar: `/data/media/0/lateral_characterization/<route>.json` (`<route>.<n>.json` if the
  daemon restarted within a route). It holds the plan, the snapshot, and events on the rlog
  clock (`mono_ns`), for example: `run_start`, `block_start` (settings, roll/pitch),
  `settings_applied`, `settings_verified` (observed values), `maneuver_start` (spec, active
  settings, roll/pitch), `maneuver_end`, `maneuver_aborted` (reason), `paused`/`resumed`,
  `block_end` (`complete`), `block_complete`, `run_end`, `restore_verified`. `run_start` records
  `completed_blocks` / `resumed_done` when a run resumes. One sidecar per drive.
- Report (on a PC; this reads from the device and never writes to it):

```sh
cd <openpilot checkout>
PYTHONPATH=$PWD python tools/lateral_maneuvers/characterization/analyze.py \
  --route 0000012a--abcdef0123 --pull --out /tmp/lc_report       # ssh comma@100.64.90.15
# or with local files:
PYTHONPATH=$PWD python tools/lateral_maneuvers/characterization/analyze.py \
  --rlogs /path/with/<route>--N/rlog.zst --sidecar <route>.json --out /tmp/lc_report
# a plan driven over several drives: repeat --route (or --sidecar); one --rlogs dir can hold all routes
PYTHONPATH=$PWD python tools/lateral_maneuvers/characterization/analyze.py \
  --route 0000012a--abcdef0123 --route 0000012c--0123abcdef --pull --out /tmp/lc_report
```

With several sidecars the results are merged per block id: a block's data comes from the newest
drive that completed it (or, if none did, the newest drive with any completed maneuver of it).
Sidecars from a different plan than the newest one are ignored and listed in the report.

`report.md` and `report.json` include:
- the 0x249→lat-accel delay (cross-correlation over 0–800 ms, sign checked) and the des→act delay
- step rise, overshoot and settling
- sine gain and phase
- ping-pong (0x249 sign flips/s and error flips/s in holds)
- the slew-cap fraction and the command-vs-request gap
- tracking RMS
- amplified noise σ(des−act)·(1+lsf/Kp) compared with the friction threshold
- roll and pitch

Each report ends with recommendations for SteerDelay, the threshold table and TISteerKp, with
the evidence behind each one.

## Install (parked, offroad)

Branch `char-resume-ui` adds only Python, docs and one Galaxy JS file on top of `521ccdd5e`
(`lateral-characterization`, itself Python-only on `8170040cb`). No params key was added, so the
compiled aarch64 artifacts are unchanged and no build is needed.

```sh
ssh -i ~/.ssh/openclaw_comma_ed25519 comma@100.64.90.15
cat /data/params/d/IsOnroad                       # must be 0
cd /data/openpilot
git fetch origin char-resume-ui
git checkout --force -B char-resume-ui FETCH_HEAD
git log -1 --oneline
git diff --stat 8170040cb HEAD -- '*.so' '*.a' '*.o' panda/board/obj common/params_pyx.cpp common/params_keys.h   # must be empty
PYTHONPATH=/data/openpilot /usr/local/venv/bin/python system/manager/prebuilt_guard.py --check
sudo reboot                                       # NOT `systemctl restart comma`
```

The branch is on origin, so `updated` cannot reset it away. To go back, use the same steps
with `starpilot-2017-accord-ti-dom-next` / `8170040cb`.

What applies when: the plan file is read each time `lateral_maneuversd` starts, which happens
when you go onroad with the mode on. Settings changes during the run are live. The manager's
stale-snapshot restore runs at manager start, i.e. on the next boot.
