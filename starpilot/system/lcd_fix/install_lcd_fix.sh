#!/usr/bin/env bash
# Reinstall the virtual-touchscreen workaround for a device whose digitizer has
# failed. Idempotent and cheap: a no-op when already correct.
#
# This lives in /data (which survives) and reinstalls into the rootfs (which an
# AGNOS flash wipes). Without it, the first boot after an AGNOS update loses the
# workaround and the device breaks in two ways at once:
#
#   * magic aborts on the missing /dev/input/event2 and the UI crash-loops
#   * hardwared's touch_thread dies on the missing by-path node, so manager
#     respawns the whole stack every ~2s and the device can never go onroad
#
# TO REMOVE once a working display is fitted: set LCD_FIX=0 in launch_env.sh,
# then run this script with --uninstall. The UI network stream is independent
# and keeps working either way.
set -e

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DST="/usr/comma/virtual_touch.py"
UNIT_DST="/usr/lib/systemd/system/virtual-touch.service"
DROPIN_DIR="/etc/systemd/system/magic.service.d"
DROPIN_DST="$DROPIN_DIR/10-wait-virtual-touch.conf"

remount_rw() { sudo mount -o remount,rw / 2>/dev/null || true; }
remount_ro() { sudo mount -o remount,ro / 2>/dev/null || true; }

if [ "${1:-}" = "--uninstall" ]; then
  remount_rw
  sudo systemctl disable --now virtual-touch.service 2>/dev/null || true
  sudo rm -f "$SCRIPT_DST" "$UNIT_DST" "$DROPIN_DST"
  sudo rmdir "$DROPIN_DIR" 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl restart magic.service 2>/dev/null || true
  remount_ro
  echo "lcd_fix: uninstalled"
  exit 0
fi

# Already correct? Then do nothing -- this runs on every boot.
if cmp -s "$SRC/virtual_touch.py" "$SCRIPT_DST" \
   && cmp -s "$SRC/virtual-touch.service" "$UNIT_DST" \
   && cmp -s "$SRC/10-wait-virtual-touch.conf" "$DROPIN_DST" \
   && systemctl is-active --quiet virtual-touch.service; then
  exit 0
fi

echo "lcd_fix: installing virtual touchscreen"
remount_rw
sudo install -m 0755 -D "$SRC/virtual_touch.py" "$SCRIPT_DST"
sudo install -m 0644 -D "$SRC/virtual-touch.service" "$UNIT_DST"
sudo install -m 0644 -D "$SRC/10-wait-virtual-touch.conf" "$DROPIN_DST"
sudo systemctl daemon-reload
sudo systemctl enable --now virtual-touch.service

# Wait for the uinput node before poking magic: magic treats a missing touch
# device as fatal, so restarting it too early just burns a failed start.
for _ in $(seq 1 100); do
  [ -e /dev/input/event2 ] && break
  sleep 0.1
done
sudo systemctl restart magic.service 2>/dev/null || true
remount_ro
echo "lcd_fix: installed"
