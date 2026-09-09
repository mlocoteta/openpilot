# Rebase / merge notes

Handoff notes for updating this fork onto a newer StarPilot base.
Car: **2017 Honda Accord (`HONDA_ACCORD_9G`, Nidec)** with a **Torque Interceptor (TI)**.
Device: **comma three (tici)** with a **failed digitizer** (touchscreen is dead).

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
  TX allow-list for TI lives in the compiled binary, so a stale build silently blocks TI.
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
3. `TI_FEEDBACK` (586) appears once openpilot sends `TI_STEERING_CONTROL` (585)
4. No `steerFaultPermanent` — a latched EPS fault needs an ignition cycle to clear
5. `modelV2` publishing ~20 Hz (the external-GPU gate needs ≥10.0 V; it is an
   **unbounded** wait, so a low rail hangs model load behind a "big model loading" spinner
   with nothing pointing at the cause)
6. `commIssue` frequency — `starpilotPlan`/`liveParameters`/`radarState` late means CPU
   contention. `alertDebug` and `lateralManeuverPlan` appear in every `commIssue` log but
   are in selfdrived's ignore list; **they are never the cause.**
