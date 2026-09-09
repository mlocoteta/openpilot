#!/usr/bin/env python3
import dataclasses
import json
import requests
import tempfile
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
  MAPS_STORAGE_CACHE_PARAM,
  estimate_file_eta_seconds,
  load_maps_storage_cache,
  nonnegative_int,
  selection_key,
  storage_bytes,
)
from openpilot.starpilot.common.theme_asset_names import find_matching_theme_asset_file
from openpilot.starpilot.common.starpilot_utilities import get_starpilot_api_info, is_url_pingable, run_cmd
from openpilot.starpilot.common.starpilot_variables import (
  ERROR_LOGS_PATH, STARPILOT_API, HD_LOGS_PATH, KONIK_LOGS_PATH, MAPS_PATH, THEME_SAVE_PATH,
  StarPilotVariables, get_starpilot_toggles
)

BOOT_LOGO_JPEG_PATH = Path("/usr/comma/bg.jpg")
BOOT_LOGO_PNG_PATH = Path("/usr/comma/bg.png")
BOOT_LOGO_MAGIC_PATH = Path("/usr/comma/magic.py")


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

  try:
    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="starpilot_boot_logo_") as staging_dir:
      staging_path = Path(staging_dir)
      staged_jpeg = staging_path / "bg.jpg"
      staged_png = staging_path / "bg.png"

      with Image.open(target_logo) as img:
        normalized_logo = img.convert("RGB")
        if normalized_logo.width >= normalized_logo.height:
          landscape_logo = normalized_logo
          weston_logo = normalized_logo.transpose(Image.Transpose.ROTATE_270)
        else:
          weston_logo = normalized_logo
          landscape_logo = normalized_logo.transpose(Image.Transpose.ROTATE_90)

        magic_uses_jpeg = False
        try:
          magic_uses_jpeg = BOOT_LOGO_JPEG_PATH.as_posix() in BOOT_LOGO_MAGIC_PATH.read_text()
        except OSError:
          pass

        (landscape_logo if magic_uses_jpeg else weston_logo).save(staged_jpeg, format="JPEG", quality=95)
        landscape_logo.save(staged_png, format="PNG")

      logo_variants = [(staged_jpeg, BOOT_LOGO_JPEG_PATH)]
      if BOOT_LOGO_PNG_PATH.is_file():
        logo_variants.append((staged_png, BOOT_LOGO_PNG_PATH))

      pending_updates = [
        (source, destination)
        for source, destination in logo_variants
        if not destination.is_file() or destination.read_bytes() != source.read_bytes()
      ]
      if not pending_updates:
        return

      mount_options = run_cmd(["findmnt", "-n", "-o", "OPTIONS", "/"], "Successfully retrieved mount options", "Failed to retrieve mount options")
      if mount_options is None:
        return
      if run_cmd(["sudo", "mount", "-o", "remount,rw", "/"], "Successfully remounted / as read-write", "Failed to remount /") is None:
        return

      try:
        for source, destination in pending_updates:
          run_cmd(["sudo", "cp", source, destination], f"Successfully replaced boot logo at {destination}", f"Failed to replace boot logo at {destination}")
      finally:
        run_cmd(["sudo", "mount", "-o", f"remount,{mount_options}", "/"], "Successfully restored / mount options", "Failed to restore / mount options")
  except Exception as error:
    print(f"Error normalizing boot logo {target_logo}: {error}")


MAPS_DOWNLOAD_PROGRESS_PARAM = "MapsDownloadProgress"
MAPS_DOWNLOAD_SIZE_CACHE_PARAM = MAPS_STORAGE_CACHE_PARAM


def _decode_map_param(value):
  return value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else value


def _get_maps_storage_cache(params):
  return load_maps_storage_cache(_decode_map_param(params.get(MAPS_DOWNLOAD_SIZE_CACHE_PARAM)))


def _save_maps_storage_cache(params, cache):
  params.put(MAPS_DOWNLOAD_SIZE_CACHE_PARAM, cache.to_json())


def _reconcile_maps_storage(params, cache, *, selected_key=None, baseline_storage_bytes=None, total_files=0, updated_at=""):
  total_storage_bytes = storage_bytes(MAPS_PATH)
  cache.reconcile(
    total_storage_bytes,
    selection_key=selected_key,
    baseline_storage_bytes=baseline_storage_bytes,
    total_files=total_files,
    updated_at=updated_at,
  )
  _save_maps_storage_cache(params, cache)
  return total_storage_bytes


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
  current_storage_bytes=None,
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

  fraction = min(max(downloaded_files / float(total_files), 0.0), 1.0) if total_files > 0 else (1.0 if completed else 0.0)

  if completed:
    percent = 100
  elif total_files > 0:
    percent = min(99, int(fraction * 100))
  else:
    percent = 0

  estimated_bytes = nonnegative_int(cached_estimate_bytes)
  storage_known = current_storage_bytes is not None or baseline_storage_bytes is not None
  effective_storage_bytes = current_storage_bytes if current_storage_bytes is not None else baseline_storage_bytes
  storage_delta_bytes = (
    max(nonnegative_int(current_storage_bytes) - nonnegative_int(baseline_storage_bytes), 0)
    if current_storage_bytes is not None and baseline_storage_bytes is not None else 0
  )

  payload = {
    "active": bool(active),
    "cancelled": cancelled,
    "completed": bool(completed),
    "downloadedBytes": storage_delta_bytes,
    "downloadedFiles": downloaded_files,
    "estimatedDownloadBytes": estimated_bytes,
    "estimateSource": "previous_additional_storage" if estimated_bytes > 0 else "",
    "etaSeconds": estimate_file_eta_seconds(elapsed_seconds, total_files, downloaded_files) if not completed else 0,
    "percent": percent,
    "phase": phase,
    "primaryLocation": primary_location,
    "selectedKey": selection_key(maps_selected),
    "selectedLocations": [location for location in maps_selected.split(",") if location],
    "storageBytes": nonnegative_int(effective_storage_bytes) if storage_known else 0,
    "storageKnown": storage_known,
    "totalFiles": total_files,
    "updatedAt": time.time(),
    "bytesPerSecond": 0,
  }
  params_memory.put(MAPS_DOWNLOAD_PROGRESS_PARAM, json.dumps(payload, separators=(",", ":")))
  return payload


def _wait_for_map_download_to_stop(sm, last_progress, timeout_seconds=5.0):
  deadline = time.monotonic() + timeout_seconds
  while time.monotonic() < deadline:
    sm.update(1000)
    if not sm.updated["mapdExtendedOut"]:
      continue

    last_progress = sm["mapdExtendedOut"].downloadProgress
    if not last_progress.active:
      return last_progress, True
  return last_progress, False


def update_maps(now, params, params_memory, manual_update=False):
  size_cache = _get_maps_storage_cache(params)
  if not size_cache.storage_known:
    _reconcile_maps_storage(params, size_cache)
  baseline_storage_bytes = size_cache.storage_bytes
  maps_downloaded = bool(size_cache.maps_present)

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

  if maps_downloaded and (schedule == 0 or (schedule == 1 and not is_sunday) or (schedule == 2 and not is_first)) and not manual_update:
    return

  suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
  todays_date = now.strftime(f"%B {day}{suffix}, %Y")

  if maps_downloaded and params.get("LastMapsUpdate") == todays_date and not manual_update:
    return

  params_memory.put_bool("DownloadMaps", True)

  pm = messaging.PubMaster(["mapdIn"])
  sm = messaging.SubMaster(["mapdExtendedOut"])

  selected_key = selection_key(maps_selected)
  cached_estimate_bytes = size_cache.selection_estimate_bytes(selected_key)
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

      last_progress, stopped = _wait_for_map_download_to_stop(sm, last_progress)
      final_storage = None
      if stopped:
        final_storage = _reconcile_maps_storage(params, size_cache)
      else:
        size_cache.mark_unknown()
        _save_maps_storage_cache(params, size_cache)

      _publish_maps_progress(
        params_memory,
        maps_selected,
        baseline_storage_bytes if stopped else None,
        started_at,
        progress=last_progress,
        active=False,
        cancelled=True,
        phase="cancelled",
        cached_estimate_bytes=cached_estimate_bytes,
        current_storage_bytes=final_storage,
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

  final_storage = _reconcile_maps_storage(
    params,
    size_cache,
    selected_key=selected_key,
    baseline_storage_bytes=baseline_storage_bytes,
    total_files=int(last_progress.totalFiles) if last_progress is not None else 0,
    updated_at=now.isoformat(),
  )
  _publish_maps_progress(
    params_memory,
    maps_selected,
    baseline_storage_bytes,
    started_at,
    progress=last_progress,
    active=False,
    completed=True,
    phase="complete",
    cached_estimate_bytes=cached_estimate_bytes,
    current_storage_bytes=final_storage,
  )

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
