#!/usr/bin/env bash

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

# On AGNOS, prefer the managed venv runtime (has required Python deps like pyzmq).
if [ -x /usr/local/venv/bin/python3 ]; then
  export PATH="/usr/local/venv/bin:${PATH}"
fi

# models get lower priority than ui
# - ui is ~5ms
# - modeld is 20ms
# - DM is 10ms
# in order to run ui at 60fps (16.67ms), we need to allow
# it to preempt the model workloads. we have enough
# headroom for this until ui is moved to the CPU.
export QCOM_PRIORITY=12

if [ -z "$AGNOS_VERSION" ]; then
  export AGNOS_VERSION="19.6.20"
fi

if [ -z "$AGNOS_ACCEPTED_VERSIONS" ]; then
  export AGNOS_ACCEPTED_VERSIONS="$AGNOS_VERSION"
fi

export STAGING_ROOT="/data/safe_staging"

# StarPilot variables (only available after StarPilot is installed to /data/openpilot)
if [ -x /data/openpilot/starpilot/system/environment_variables ]; then
  eval "$(/data/openpilot/starpilot/system/environment_variables)"
fi

# UI network stream (http://<device>:8088/). Self-contained -- it reads the UI's
# own render texture and does not depend on the virtual-touchscreen workaround
# used on devices with a dead digitizer, so either can be removed independently.
# Capture only runs while a viewer is connected, so this is free when unused.
export STREAM="1"
export STREAM_PORT="8088"
export STREAM_SCALE="2"
export STREAM_QUALITY="50"
export STREAM_FPS="20"

# Virtual touchscreen for a device with a failed digitizer. Lives in /data and
# reinstalls into the rootfs, which an AGNOS flash wipes. Idempotent, so this is
# a no-op once installed. Set to 0 (or delete this block) once a working display
# is fitted -- the UI stream above is independent and keeps working either way.
export LCD_FIX="1"
if [ "$LCD_FIX" = "1" ] && [ -x /data/openpilot/starpilot/system/lcd_fix/install_lcd_fix.sh ]; then
  /data/openpilot/starpilot/system/lcd_fix/install_lcd_fix.sh || true
fi
