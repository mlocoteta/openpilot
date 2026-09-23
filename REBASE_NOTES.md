# Rebase / merge notes

Handoff notes for updating this fork onto a newer StarPilot base.
Car: **2017 Honda Accord (`HONDA_ACCORD_9G`, Nidec)** with a **Torque Interceptor (TI)**.
Device: **comma three (tici)** with a **failed digitizer** (touchscreen is dead).

## State of play (2026-09-10)

**The TI works.** Encoding, panda acceptance and board state are verified on car; the
remaining work is tuning, and **every tuning number predating `f27c9eaf` is worthless**
because it was measured through a broken encoding.

Where the work lives — check this first, it is easy to edit the wrong tree:

| where | branch | has the TI fix? |
| --- | --- | --- |
| **device** `/data/openpilot` | `starpilot-2017-accord-ti-c3-update` | **yes** — `f27c9eaf`, unpushed |
| dev box `~/openpilot` | `starpilot-honda-accord-ti` | **no** — still the broken 16-bit layout |

`f27c9eaf` exists only on the device and is not pushed to `origin`. Push it before doing
anything that could reset the tree. Do not "fix" the TI from the dev-box branch; it is behind.

Currently disabled on purpose, re-enable when wanted:
`SpeedLimitController=0`, `CurveSpeedController=0` (gates mapd off for memory).

## Upstream

| remote | url | role |
| --- | --- | --- |
| `starpilot` | `https://github.com/firestar5683/StarPilot` | the base we track. Default branch **`StarPilot`** |
| `origin` | `https://github.com/mlocoteta/openpilot` | our fork. Branch **`starpilot-2017-accord-ti-c3-update`** |
| `upstream` | `https://github.com/commaai/openpilot` | comma upstream. Not merged directly |

Ignore `starpilot/StarPilot-2017` — despite the name it is stale (last commit Feb 2026)
and is **not** the 2017-Accord branch. `StarPilot` is the live one.

**Always merge, never rebase.** Every past update is a merge commit
(`Merge remote-tracking branch 'firestar5683/StarPilot' into ...`). ~47 local commits and
118 tracked build artifacts make a rebase far more painful than a merge, for no benefit.

```bash
git fetch starpilot --no-tags StarPilot:refs/remotes/starpilot/StarPilot
git merge --no-edit starpilot/StarPilot
```

Push over SSH (`git@github.com:mlocoteta/openpilot.git`) — the HTTPS remote has no
credentials configured.

## Local changes that must survive

Roughly 47 source files diverge. The ones that matter:

**Torque Interceptor (the whole point of the fork)**
- `opendbc_repo/opendbc/car/honda/carstate.py` — registers `POWERTRAIN_DATA` for the 9G
  (read via `cp.vl_all`, so it must be explicit) and `TI_FEEDBACK` as **optional**
  (`freq 0`). TI_FEEDBACK is absent until openpilot commands the board; registering it as
  required trips `canError` before you can ever engage.
- `opendbc_repo/opendbc/car/honda/carcontroller.py` — when `has_ti`, stock
  `STEERING_CONTROL` carries **zero** torque and the real torque goes out on
  `TI_STEERING_CONTROL` (0x249).
- `opendbc_repo/opendbc/safety/modes/honda.h` — panda TX allow-list for 0x249.
- `opendbc_repo/opendbc/dbc/.../_ti_steering.dbc` — `TI_STEERING_CONTROL` 585,
  `TI_FEEDBACK` 586.
- `common/params_keys.h` — `TorqueInterceptorEnabled` + the `TISigmoid*` / `TISteerKp` block.

**Build**
- `SConstruct` — resolves Eigen from the managed venv package. AGNOS 19.6 stopped
  installing Eigen into `/usr/local/include`; without this the build fails.

**Streaming / dead digitizer** (see "Two independent subsystems" below)
- `system/ui/lib/ui_stream.py`, `system/ui/lib/application.py`
- `starpilot/system/lcd_fix/**`
- `launch_env.sh` — `STREAM*` and `LCD_FIX` blocks

## Two independent subsystems — keep them independent

1. **UI stream** (`STREAM=1`, port 8088). Reads the UI's own render texture and nothing
   else. Capture is gated on a connected viewer; with nobody watching it does zero work.
2. **LCD fix** (`LCD_FIX=1`). Virtual uinput touchscreen for the dead digitizer. Provides
   `/dev/input/event2` (or `magic` aborts fatally) **and** the by-path symlink
   `/dev/input/by-path/platform-894000.i2c-event` (or `hardwared`'s `touch_thread` dies,
   manager respawns everything every ~2s, and the device can never go onroad).

**When a working display is fitted:** set `LCD_FIX=0` and run
`starpilot/system/lcd_fix/install_lcd_fix.sh --uninstall`. The stream is unaffected.
Do not let these two get coupled.

## Torque Interceptor: board generation decides the message layout

**Read this before touching anything TI.** This cost a full day and produced a car that
yanked the wheel at full scale.

There are two incompatible TI generations, and MoreTore's opendbc carries both:

| gen | reference DBC | steering cmd | feedback |
| --- | --- | --- | --- |
| **gen1 (this car)** | `opendbc/dbc/mazda_2017.dbc` | 585, **12-bit, `(1,-2048)` offset** | **586** `TI_FEEDBACK` |
| gen2/gen3 | `mazda_2019.dbc` / `mazda_2023.dbc` | 585 `EPS_LKAS`, 16-bit signed | 587, different layout |

```
# gen1 -- what 0x249 must look like
SG_ LKAS_REQUEST : 3|12@0+ (1,-2048) [0|2048] "" XXX
SG_ CHKSUM       : 19|12@0+ (1,-2048) [0|2048] "" XXX
SG_ KEY          : 39|32@0+ (1,0)               ""  XXX   # value 3294744160 (0xC461CE60)
```

**Identify the board from the bus, never from the branch name.** Ours reports
`VERSION_NUMBER=6` in `TI_FEEDBACK` (586). Presence of 586 at all == gen1.

The `4_2026_ti` port brought the **gen2** 16-bit layout onto this gen1 car. Symptom: a
**zero** command encodes as `0x0000`, the board reads `raw 0 - 2048 = -2048`, i.e. full-scale
deflection with the sign effectively inverted. On car it pulls hard immediately, then the
board latches `STATE=OFF` with `VIOL=17`. Fixed in `f27c9eaf`.

Neutral on the wire is **`0800`**, not `0000`. If you see `0000` going out, the layout is wrong.

**The panda safety hook must decode the offset too.** `honda.h`'s 0x249 `tx_hook` does
`((data[0] & 0x0F) << 8) | data[1] - 2048` *before* its zero check; otherwise neutral (`0x800`)
reads as non-zero and is blocked whenever controls are not allowed.

**Sign: do not negate.** The TI drives the EPS motor in its own convention, matching
`opendbc/car/mazda/carcontroller.py` (`torque * STEER_MAX`, no minus). A negation also puts
the command and the TI torque sensor in opposite conventions, which makes
`apply_ti_steer_torque_limits` fight the command instead of the driver.

**State machine** (`TI_STATE` in `honda/values.py`): `DISCOVER=0 OFF=1 DRIVER_OVER=2 RUN=3`.
`ti_lkas_allowed` requires `RUN`. The board recovers on its own -- once it receives
well-formed frames it goes `OFF -> RUN` and clears `VIOL` to 0. No arming sequence needed.

## Diagnosing "the TI gets no command"

The panda echoes every TX back on `can` with `src` offset, which tells you *who* dropped it:

| `src` | meaning |
| --- | --- |
| bus (0/1/2) | normal received frame |
| **128** = `0x80 + bus` | TX **accepted** by panda |
| **192** = `0xC0 + bus` | TX **rejected** by panda |

Tally *all* TX addresses, not just 0x249. If `0xE4`/`0x1FA`/`0x30C`/`0x33D` come back `128`
and only `0x249` comes back `192`, the panda is fine and the problem is specific to the TI
message -- allow-list or `tx_hook`. If a **zero-torque** 0x249 is rejected while
`controlsAllowed` is true, no safety rule can explain it and the running firmware is stale.

## Pain points

**Build artifacts are committed.** 118 tracked binaries (`panda/board/obj/**`,
`common/*.so`, `common/libcommon.a`, `selfdrive/locationd/models/generated/**`,
`system/loggerd/{loggerd,encoderd,bootlog}`, `selfdrive/pandad/pandad`,
`system/camerad/camerad`). They conflict on every merge — 83 of 98 conflicts last time.
Resolve in bulk, then rebuild:

```bash
git diff --name-only --diff-filter=U \
  | grep -E 'panda/board/obj/|\.(a|so|o)$|locationd/models/generated/' \
  | while read -r f; do git checkout --theirs -- "$f"; git add -- "$f"; done
```

**SCons caching silently serves stale objects.** The single worst trap. `params_keys.h`
was correct in source but `TorqueInterceptorEnabled` was **absent from the compiled
key table**, so every `Params().get_bool("TorqueInterceptorEnabled")` raised
`UnknownKeyName` and TI was unreachable — with no error pointing anywhere near the cause.
SCons hashes content, so `touch` will not force a rebuild. The keys live in `params.cc`
→ `libcommon.a`, so rebuilding `params_pyx.so` alone just relinks the stale archive.

```bash
# Verify after any merge that touches params_keys.h -- and after any AGNOS flash.
# Ask the library; do NOT grep the binary. `strings` on params_pyx.so gives
# FALSE NEGATIVES (observed reporting 0 for keys that resolve fine).
PYTHONPATH=/data/openpilot /usr/local/venv/bin/python -c "
from openpilot.common.params import Params
Params().get('TorqueInterceptorEnabled')"      # UnknownKeyName == stale build

# if it raises:
rm -f common/libcommon.a common/params.o common/params_pyx.so common/params_pyx.cpp
PATH=/usr/local/venv/bin:$PATH python -m SCons --cache-disable -j4
```

Compiling `params.cc` takes minutes. A short SSH timeout kills it and the output
reads "Build interrupted", which looks like a build failure but is not. Run detached.

**Honda conflicts are usually complementary, not competing.** StarPilot is adding
`HONDA_ACCORD_11G` (Bosch CAN-FD) support; ours is `HONDA_ACCORD_9G` (Nidec). Both sides
are fingerprint-gated, so keep both rather than picking one. 11G code is inert on this car.

**AGNOS pins conflict.** `launch_env.sh`, `system/hardware/tici/agnos.json`,
`system/webrtc/**`, `tools/agnos/**` all conflict when versions differ. Take StarPilot's
unless there is a specific reason not to — but see the warning below.

## Commands

```bash
# build (device). PATH matters: cythonize/scons live in the venv
cd /data/openpilot && PATH=/usr/local/venv/bin:$PATH \
  /usr/local/venv/bin/python -m SCons -j4

# deploy to device
git fetch origin <branch> && git checkout -f -B <branch> origin/<branch>

# rebuild + flash panda firmware (REQUIRED after any opendbc/safety change)
cd /data/openpilot/panda && PATH=/usr/local/venv/bin:$PATH \
  PYTHONPATH=/data/openpilot:/data/openpilot/opendbc_repo \
  /usr/local/venv/bin/scons -u -j1        # -j1: no swap, -j2+ thrashes to load 40+
printf 1 > /data/params/d/FlashPanda && sudo systemctl restart comma

# device state
cat /VERSION                              # AGNOS version
sudo abctl --boot_slot                    # A/B slot
systemctl is-active virtual-touch magic comma
cat /data/params/d/IsOnroad
```

Python deps live in `/usr/local/venv`; plain `python3` on the device lacks `cereal`.
Use `PYTHONPATH=/data/openpilot /usr/local/venv/bin/python`.

## Don't touch

- **`panda/board/obj/**`** — signed panda firmware. Never hand-edit; rebuild it. The 0x249
  TX allow-list and `tx_hook` live in the compiled binary, so a stale build silently blocks TI.
  **Rebuilding is not enough — pandad will not reflash on its own.** Arm it explicitly:
  `printf 1 > /data/params/d/FlashPanda`, then restart `comma`. It flashed when the param
  reads back `0`. A whole day was lost to a correct source tree and a stale flashed binary.
- **`common/params_keys.h` ordering** — append new keys; existing entries are referenced by
  the compiled key table.
- **`/data/media`, `/data/backups`** (device) — user drive footage and backups. openpilot
  prunes media itself when space is low.
- **`system/hardware/tici/agnos.json` hashes** — must match `AGNOS_VERSION` in
  `launch_env.sh`. A mismatch means a failed or endless flash.

## Gotchas worth knowing

**An AGNOS bump wipes `/usr`.** That deletes the LCD fix, which breaks `magic` *and*
`hardwared` at once and the device cannot go onroad. This is why the fix lives in `/data`
and reinstalls from `launch_env.sh` on every boot. **Verify after any AGNOS change:**

```bash
ls /usr/comma/virtual_touch.py /dev/input/by-path/platform-894000.i2c-event
systemctl is-active virtual-touch magic
```

**The AGNOS updater can block on an invisible prompt.** With no working display it will
sit forever — updater running, zero download, zero disk write, ~15% CPU, holding
`/dev/dri/card0` and `/dev/input/event2`. Dismiss it through the virtual touchscreen; the
confirm button was at **(1700, 900)**:

```bash
curl -X POST 'http://<device>:8089/tap?x=1700&y=900'
```

Note the stream (8088) is **down** during an AGNOS update — `updater_magic` owns the
display, not the openpilot UI — but touch injection (8089) still works.

**An AGNOS flash re-breaks the param key table.** Confirmed: after 19.6.10 -> 19.6.20,
`TorqueInterceptorEnabled`, `HomeScreenName` and `TISigmoidEnabled` were all missing from
the compiled table again, and the UI crash-looped on `UnknownKeyName: HomeScreenName`
raised by `home_screen_name()` in the render path. That also kills the stream, because the
streamer runs inside the UI process. The `TorqueInterceptorEnabled` **param file itself**
was wiped too, so re-check the value, not just the key. Verify both after every AGNOS change.

**AGNOS downloads do not consume `/data`.** It streams straight to the raw inactive
partition. Free space stays flat during the download; don't chase it.

**Memory: 3.6 GB and no swap/zram at all.** Idle was 3360/3606 MB used with 245 MB free,
and `scons -j2` thrashed the box to load 48 with SSH timing out. `run_mapd` in
`system/manager/process_config.py` is gated on `SpeedLimitController or CurveSpeedController`
so mapd (~150 MB) stays down when neither feature is on -- that alone freed ~1.7 GB.
Re-enabling either param brings mapd back automatically; no code change needed.

**`/data/backups` fills the disk.** StarPilot writes a ~4.2 GB auto-backup on *every* branch
change and never prunes. Two of them plus the tree already left <5 GB free. Check before any
branch switch; deleting superseded ones is safe (ask first -- they are the user's).

**Beware self-matching `pgrep`.** `pgrep -f mapd` inside a shell one-liner matches its own
command string and reports the process as running when it is not. Bit us twice. Use
`ps -C <name>` or `pgrep -f <pat> | grep -v $$`.

**`du` on this device lies.** Sparse files/hardlinks make `/data/media` report ~194 GB on a
30 GB partition. Trust `df` only.

**External hardware is currently absent.** No AMD eGPU (Chestnut) and no external SSD —
both USB 3.0 buses are empty; only the internal hub, LTE modem, and panda enumerate.
Models run from internal storage and `modeld` does inference on-device. Don't debug the
"GPU not detected" path in software; check the cable first.

## Verifying a merge on the car

Needs the engine actually running — key-on is not enough.

1. `TorqueInterceptorEnabled` is `True` **and** compiled into `params_pyx.so`
2. Car fingerprints as `HONDA_ACCORD_9G`; `CarParams` set
3. `TI_FEEDBACK` (586) appears once openpilot sends `TI_STEERING_CONTROL` (585), and
   reports `STATE=3` (RUN) with `VIOL=0 ERROR=0`. `STATE=1` (OFF) with a non-zero `VIOL`
   means the board is rejecting what you send -- check the 585 layout first.
4. 0x249 comes back `src=128` (accepted). Neutral encodes as `0800`, and decodes to 0.
5. No `steerFaultPermanent` — a latched EPS fault needs an ignition cycle to clear
6. `modelV2` publishing ~20 Hz (the external-GPU gate needs ≥10.0 V; it is an
   **unbounded** wait, so a low rail hangs model load behind a "big model loading" spinner
   with nothing pointing at the cause)
7. `commIssue` frequency — `starpilotPlan`/`liveParameters`/`radarState` late means CPU
   contention. `alertDebug` and `lateralManeuverPlan` appear in every `commIssue` log but
   are in selfdrived's ignore list; **they are never the cause.**
