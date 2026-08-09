#!/usr/bin/env python3
import dataclasses
import json
import requests
import threading
import time

from pathlib import Path
from types import SimpleNamespace

from cereal import messaging
from openpilot.common.basedir import BASEDIR
from openpilot.common.params import Params
from openpilot.common.time_helpers import system_time_valid
from openpilot.system.hardware import HARDWARE
from openpilot.system.version import get_build_metadata

from openpilot.starpilot.assets.theme_manager import ThemeManager
from openpilot.starpilot.common.starpilot_backups import backup_starpilot
from openpilot.starpilot.common.connect_server import sync_konik_dongle_id
from openpilot.starpilot.common.maps_catalog import normalize_schedule_value, sanitize_selected_locations_csv
from openpilot.starpilot.common.maps_download_progress import (
  estimate_download_bytes,
  estimate_eta_seconds,
  load_size_cache,
  nonnegative_int,
  selection_key,
  storage_bytes,
)
from openpilot.starpilot.common.theme_asset_names import find_matching_theme_asset_file
from openpilot.starpilot.common.starpilot_utilities import get_starpilot_api_info, is_FrogsGoMoo, is_url_pingable, run_cmd
from openpilot.starpilot.common.starpilot_variables import (
  ERROR_LOGS_PATH, STARPILOT_API, FROGS_GO_MOO_PATH, HD_LOGS_PATH, KONIK_LOGS_PATH, MAPS_PATH, THEME_SAVE_PATH,
  StarPilotVariables, get_starpilot_toggles
)


def seed_desktop_theme_assets():
  params = Params()
  params_memory = Params(memory=True)
  params_defaults = Params(return_defaults=True)
  theme_manager = ThemeManager(params, params_memory, boot_run=True)

  custom_themes = params_defaults.get_bool("CustomThemes")
  random_themes = custom_themes and params_defaults.get_bool("RandomThemes")

  starpilot_toggles = SimpleNamespace(
    boot_logo=params_defaults.get("BootLogo", encoding="utf-8", default="starpilot"),
    holiday_themes=params_defaults.get_bool("HolidayThemes"),
    random_themes=random_themes,
    random_themes_holidays=random_themes and params_defaults.get_bool("RandomThemesHolidays"),
    color_scheme=params_defaults.get("ColorScheme", encoding="utf-8", default="stock") if custom_themes else "stock",
    distance_icons=params_defaults.get("DistanceIconPack", encoding="utf-8", default="stock") if custom_themes else "stock",
    icon_pack=params_defaults.get("IconPack", encoding="utf-8", default="stock") if custom_themes else "stock",
    sound_pack=params_defaults.get("SoundPack", encoding="utf-8", default="stock") if custom_themes else "stock",
    signal_icons=params_defaults.get("SignalAnimation", encoding="utf-8", default="stock") if custom_themes else "stock",
    wheel_image=params_defaults.get("WheelIcon", encoding="utf-8", default="stock") if custom_themes else "stock",
  )

  theme_manager.update_active_theme(
    time_validated=system_time_valid(),
    starpilot_toggles=starpilot_toggles,
    boot_run=True,
  )
  theme_manager.update_theme_asset("distance_icons", starpilot_toggles.distance_icons, boot_run=True)
  theme_manager.update_wheel_image(starpilot_toggles.wheel_image, boot_run=True)


def starpilot_boot_functions(build_metadata, params):
  params_memory = Params(memory=True)

  maps_selected_raw = params.get("MapsSelected")
  maps_selected = sanitize_selected_locations_csv(maps_selected_raw)
  if isinstance(maps_selected_raw, bytes):
    maps_selected_raw = maps_selected_raw.decode("utf-8", errors="ignore")
  if maps_selected != (maps_selected_raw or ""):
    params.put("MapsSelected", maps_selected)

  params.put("BuildMetadata", json.dumps(dataclasses.asdict(build_metadata)))

  StarPilotVariables()
  ThemeManager(params, params_memory, boot_run=True).update_active_theme(time_validated=system_time_valid(), starpilot_toggles=get_starpilot_toggles(), boot_run=True)

  sync_konik_dongle_id(params)

  def boot_thread():
    while not system_time_valid():
      print("Waiting for system time to become valid...")
      time.sleep(1)

    backup_starpilot(build_metadata, params)

  threading.Thread(target=boot_thread, daemon=True).start()


def install_starpilot(build_metadata, params):
  paths = [
    ERROR_LOGS_PATH,
    HD_LOGS_PATH,
    KONIK_LOGS_PATH,
    MAPS_PATH,
    THEME_SAVE_PATH
  ]
  for path in paths:
    path.mkdir(parents=True, exist_ok=True)

  register_device(build_metadata, params)

  update_boot_logo(starpilot=True, selected_logo=params.get("BootLogo"))

  if is_FrogsGoMoo():
    mount_options = run_cmd(["findmnt", "-n", "-o", "OPTIONS", "/persist"], "Successfully retrieved mount options", "Failed to retrieve mount options")
    run_cmd(["sudo", "mount", "-o", "remount,rw", "/persist"], "Successfully remounted /persist as read-write", "Failed to remount /persist")
    run_cmd(["sudo", "python3", FROGS_GO_MOO_PATH], "Successfully ran frogsgomoo.py", "Failed to run frogsgomoo.py")
    run_cmd(["sudo", "mount", "-o", f"remount,{mount_options}", "/persist"], "Successfully restored /persist mount options", "Failed to restore /persist mount options")


def register_device(build_metadata, params):
  def register_thread():
    dongle_id = params.get("DongleId")
    if isinstance(dongle_id, bytes):
      dongle_id = dongle_id.decode("utf-8", errors="ignore")
    starpilot_dongle_id = params.get("StarPilotDongleId")
    if isinstance(starpilot_dongle_id, bytes):
      starpilot_dongle_id = starpilot_dongle_id.decode("utf-8", errors="ignore")

    # Keep a stable local identifier even if the remote registration endpoint
    # is unavailable or slow to respond.
    if dongle_id and not starpilot_dongle_id:
      params.put("StarPilotDongleId", dongle_id)

    while not is_url_pingable(STARPILOT_API):
      time.sleep(60)

    payload = {
      "api_token": params.get("StarPilotApiToken"),
      "build_metadata": dataclasses.asdict(build_metadata),
      "device": HARDWARE.get_device_type(),
      "dongle_id": dongle_id,
      "starpilot_dongle_id": params.get("StarPilotDongleId"),
    }

    try:
      response = requests.post(f"{STARPILOT_API}/register", json=payload, headers={"Content-Type": "application/json", "User-Agent": "starpilot-api/1.0"}, timeout=10)
      response.raise_for_status()

      data = response.json()
      params.put("StarPilotApiToken", data.get("api_token", ""))
      params.put("StarPilotDongleId", data.get("starpilot_dongle_id"))
    except Exception:
      pass

  threading.Thread(target=register_thread, daemon=True).start()


def uninstall_starpilot():
  update_boot_logo(stock=True)

  HARDWARE.uninstall()


def update_boot_logo(starpilot=False, stock=False, selected_logo=None):
  if HARDWARE.get_device_type() == "pc":
    return

  boot_logo_location = Path("/usr/comma/bg.jpg")

  if starpilot:
    target_logo = Path(BASEDIR) / "starpilot/assets/other_images/starpilot_boot_logo.jpg"
    if selected_logo:
      selected = selected_logo.decode("utf-8", "ignore") if isinstance(selected_logo, (bytes, bytearray)) else str(selected_logo)
      selected = selected.strip()
      if selected.lower() not in {"", "stock", "default"}:
        matched_logo = find_matching_theme_asset_file(THEME_SAVE_PATH / "bootlogos", selected)
        if matched_logo is not None:
          target_logo = matched_logo
  elif stock:
    target_logo = Path(BASEDIR) / "starpilot/assets/other_images/stock_bg.jpg"
  else:
    print(f'Error: Must specify either "starpilot=True" or "stock=True"')
    return

  if not target_logo.is_file():
    print(f"Error: Target logo file not found at {target_logo}")
    return

  source_logo = target_logo
  staged_logo = Path("/tmp/starpilot_boot_logo.jpg")
  try:
    from PIL import Image

    with Image.open(target_logo) as img:
      # weston.service always writes a JPEG copy of /usr/comma/bg.jpg; make sure
      # the source image is already RGB JPEG to avoid startup failure on RGBA assets.
      if img.format != "JPEG" or img.mode != "RGB":
        img.convert("RGB").save(staged_logo, format="JPEG", quality=95)
        source_logo = staged_logo
  except Exception as error:
    print(f"Error normalizing boot logo {target_logo}: {error}")
    if target_logo.suffix.lower() not in {".jpg", ".jpeg"}:
      print("Skipping boot logo update to keep weston startup stable.")
      return

  current_logo = boot_logo_location.read_bytes() if boot_logo_location.is_file() else b""
  desired_logo = source_logo.read_bytes()
  if current_logo != desired_logo:
    mount_options = run_cmd(["findmnt", "-n", "-o", "OPTIONS", "/"], "Successfully retrieved mount options", "Failed to retrieve mount options")
    run_cmd(["sudo", "mount", "-o", "remount,rw", "/"], "Successfully remounted / as read-write", "Failed to remount /")
    run_cmd(["sudo", "cp", source_logo, boot_logo_location], "Successfully replaced boot logo", "Failed to replace boot logo")
    run_cmd(["sudo", "mount", "-o", f"remount,{mount_options}", "/"], "Successfully restored / mount options", "Failed to restore / mount options")


MAPS_DOWNLOAD_PROGRESS_PARAM = "MapsDownloadProgress"
MAPS_DOWNLOAD_SIZE_CACHE_PARAM = "MapsDownloadSizeCache"


def _decode_map_param(value):
  return value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else value


def _get_map_size_cache(params):
  return load_size_cache(_decode_map_param(params.get(MAPS_DOWNLOAD_SIZE_CACHE_PARAM)))


def _publish_maps_progress(
  params_memory,
  maps_selected,
  baseline_storage_bytes,
  started_at,
  progress=None,
  *,
  active=None,
  cancelled=False,
  completed=False,
  phase="starting",
  cached_estimate_bytes=0,
):
  total_files = 0
  downloaded_files = 0
  progress_cancelled = False
  primary_location = ""
  if progress is not None:
    total_files = int(progress.totalFiles)
    downloaded_files = int(progress.downloadedFiles)
    progress_cancelled = bool(progress.cancelled)
    try:
      if len(progress.locationDetails) > 0:
        primary_location = str(progress.locationDetails[0].location)
      elif len(progress.locations) > 0:
        primary_location = str(progress.locations[0])
    except (AttributeError, IndexError, TypeError):
      pass

  if active is None:
    active = bool(progress.active) if progress is not None else False
  cancelled = bool(cancelled or progress_cancelled)
  elapsed_seconds = max(time.monotonic() - started_at, 0.0)
  current_storage_bytes = storage_bytes(MAPS_PATH)
  storage_delta_bytes = max(current_storage_bytes - baseline_storage_bytes, 0)
  bytes_per_second = storage_delta_bytes / elapsed_seconds if elapsed_seconds > 0 else 0.0
  estimated_bytes = estimate_download_bytes(storage_delta_bytes, total_files, downloaded_files)
  estimate_source = "live_file_rate" if estimated_bytes else ""
  if not estimated_bytes and cached_estimate_bytes:
    estimated_bytes = int(cached_estimate_bytes)
    estimate_source = "previous_download"

  if completed:
    percent = 100
  elif estimated_bytes > 0:
    percent = min(99, int(storage_delta_bytes * 100 / estimated_bytes))
  elif total_files > 0:
    percent = min(99, int(downloaded_files * 100 / total_files))
  else:
    percent = 0

  payload = {
    "active": bool(active),
    "cancelled": cancelled,
    "completed": bool(completed),
    "downloadedBytes": storage_delta_bytes,
    "downloadedFiles": downloaded_files,
    "estimatedDownloadBytes": estimated_bytes,
    "estimateSource": estimate_source,
    "etaSeconds": estimate_eta_seconds(estimated_bytes, storage_delta_bytes, bytes_per_second) if not completed else 0,
    "percent": percent,
    "phase": phase,
    "primaryLocation": primary_location,
    "selectedKey": selection_key(maps_selected),
    "selectedLocations": [location for location in maps_selected.split(",") if location],
    "storageBytes": current_storage_bytes,
    "totalFiles": total_files,
    "updatedAt": time.time(),
    "bytesPerSecond": round(bytes_per_second, 2),
  }
  params_memory.put(MAPS_DOWNLOAD_PROGRESS_PARAM, json.dumps(payload, separators=(",", ":")))
  return payload


def update_maps(now, params, params_memory, manual_update=False):
  maps_selected_raw = params.get("MapsSelected")
  maps_selected = sanitize_selected_locations_csv(maps_selected_raw)
  if not maps_selected:
    return
  if isinstance(maps_selected_raw, bytes):
    maps_selected_raw = maps_selected_raw.decode("utf-8", errors="ignore")
  if maps_selected != (maps_selected_raw or ""):
    params.put("MapsSelected", maps_selected)

  day = now.day
  is_first = day == 1
  is_sunday = now.weekday() == 6
  schedule = normalize_schedule_value(params.get("PreferredSchedule"))

  maps_downloaded = MAPS_PATH.exists() and any(path.is_file() for path in MAPS_PATH.rglob("*"))
  if maps_downloaded and (schedule == 0 or (schedule == 1 and not is_sunday) or (schedule == 2 and not is_first)) and not manual_update:
    return

  suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
  todays_date = now.strftime(f"%B {day}{suffix}, %Y")

  if maps_downloaded and params.get("LastMapsUpdate") == todays_date and not manual_update:
    return

  pm = messaging.PubMaster(["mapdIn"])
  sm = messaging.SubMaster(["mapdExtendedOut"])

  size_cache = _get_map_size_cache(params)
  cached_entry = size_cache.get(selection_key(maps_selected), {})
  cached_estimate_bytes = nonnegative_int(cached_entry.get("downloadBytes", 0)) if isinstance(cached_entry, dict) else 0
  baseline_storage_bytes = storage_bytes(MAPS_PATH)
  started_at = time.monotonic()
  _publish_maps_progress(
    params_memory,
    maps_selected,
    baseline_storage_bytes,
    started_at,
    active=True,
    phase="starting",
    cached_estimate_bytes=cached_estimate_bytes,
  )

  time.sleep(1)

  msg = messaging.new_message("mapdIn")
  msg.mapdIn.type = 0
  msg.mapdIn.str = maps_selected
  pm.send("mapdIn", msg)

  started = False
  last_progress = None
  while True:
    sm.update(1000)

    if params_memory.get_bool("CancelDownloadMaps"):
      msg = messaging.new_message("mapdIn")
      msg.mapdIn.type = 27
      pm.send("mapdIn", msg)

      _publish_maps_progress(
        params_memory,
        maps_selected,
        baseline_storage_bytes,
        started_at,
        progress=last_progress,
        active=False,
        cancelled=True,
        phase="cancelled",
        cached_estimate_bytes=cached_estimate_bytes,
      )
      params_memory.remove("CancelDownloadMaps")
      params_memory.remove("DownloadMaps")
      return

    if sm.updated["mapdExtendedOut"]:
      progress = sm["mapdExtendedOut"].downloadProgress
      last_progress = progress

      if progress.active:
        started = True

      _publish_maps_progress(
        params_memory,
        maps_selected,
        baseline_storage_bytes,
        started_at,
        progress=progress,
        phase="downloading" if progress.active else "finishing",
        cached_estimate_bytes=cached_estimate_bytes,
      )

      if not progress.active and started:
        break

  final_progress = _publish_maps_progress(
    params_memory,
    maps_selected,
    baseline_storage_bytes,
    started_at,
    progress=last_progress,
    active=False,
    completed=True,
    phase="complete",
    cached_estimate_bytes=cached_estimate_bytes,
  )
  if final_progress["downloadedBytes"] > 0:
    size_cache[selection_key(maps_selected)] = {
      "downloadBytes": final_progress["downloadedBytes"],
      "totalFiles": final_progress["totalFiles"],
      "updatedAt": now.isoformat(),
    }
    params.put(MAPS_DOWNLOAD_SIZE_CACHE_PARAM, json.dumps(size_cache, separators=(",", ":")))

  params.put("LastMapsUpdate", todays_date)
  params_memory.remove("DownloadMaps")


def update_openpilot(thread_manager, params):
  def update_available():
    run_cmd(["pkill", "-SIGUSR1", "-f", "system.updated.updated"], "Checking for updates...", "Failed to check for update...", report=False)

    while params.get("UpdaterState") != "checking...":
      time.sleep(1)

    while params.get("UpdaterState") == "checking...":
      time.sleep(1)

    if not params.get_bool("UpdaterFetchAvailable"):
      return False

    while params.get_bool("IsOnroad") or thread_manager.is_thread_alive("lock_doors"):
      time.sleep(60)

    run_cmd(["pkill", "-SIGHUP", "-f", "system.updated.updated"], "Update available, downloading...", "Failed to download update...", report=False)

    while not params.get_bool("UpdateAvailable"):
      time.sleep(60)

    return True

  if params.get("UpdaterState") != "idle":
    return

  while params.get_bool("IsOnroad") or thread_manager.is_thread_alive("lock_doors"):
    time.sleep(60)

  if not update_available():
    return

  while True:
    if not update_available():
      break

  while params.get_bool("IsOnroad") or thread_manager.is_thread_alive("lock_doors"):
    time.sleep(60)

  # Manager owns the final reboot so a stale offroad read here cannot reboot
  # the device while ignition is still on.
  params.put_bool("DoReboot", True)
