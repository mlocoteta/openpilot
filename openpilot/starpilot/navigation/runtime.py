from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import math
import time
import uuid

from openpilot.starpilot.navigation.owner import ConflictError, NavigationOwner, ValidationError, ROUTE_AVOIDANCES
from openpilot.starpilot.navigation.route_engine import MapboxRouteEngine

from openpilot.starpilot.gps.phone import read_phone_gps
from openpilot.starpilot.gps.source import GPS_MAX_AGE_NS, GPS_SERVICES, bearing, select_source

# Only the comma's own (or the car's) GPS may authorize route advice to modeld/plannerd. A phone or head-unit fix
# (phoneGps, e.g. the Accord head unit filling the comma's u-blox outages) still guides, but only for display.
CONTROL_SOURCES = ("comma", "car")
ARRIVED_NS = 5_000_000_000      # stopped at the destination this long shows "You have arrived"
END_ROUTE_NS = 10_000_000_000   # ...and this long ends navigation, like tapping End navigation
# 10-31 (Mat #car: "auto-rerouting has problems"; HU black box 12:27:56 + 12:28:07 = two reroutes 11 s apart):
OFF_ROUTE_NS = 4_000_000_000        # off the route this long (fresh fixes only) asks for a new route
REROUTE_GRACE_NS = 10_000_000_000   # a just-fetched route is not judged off-route for this long
REROUTE_GAP_NS = 20_000_000_000     # at most one reroute per this long; meanwhile the old route keeps guiding
KEY_END_M = 60.                     # a drive that ended this close to the route's end does not resume it next drive


def located(sm, now_ns: int, phone_fix=None):
  """(source, position): source is comma|car|phone, or (None, None) without a usable fix."""
  selected = select_source(sm, now_ns, phone_fix=phone_fix)
  if selected is None:
    return None, None
  source, (stamp, gps) = selected
  speed = max(0., gps.speed) if math.isfinite(gps.speed) else None
  return source, (stamp, (gps.longitude, gps.latitude), speed, bearing(gps))


def location(sm, now_ns: int, phone_fix=None):
  return located(sm, now_ns, phone_fix)[1]


class RouteRuntime:
  def __init__(self, owner: NavigationOwner, engine=None, executor=None):
    self.owner = owner
    if engine is None:
      from openpilot.starpilot.navigation.mapbox_budget import MonthlyBudget
      engine = MapboxRouteEngine(owner.session, MonthlyBudget('directions', owner.root / 'mapbox-usage'))
    self.engine = engine
    self.executor = executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix='route')
    self.key = None
    self.route = None
    self.routes = []
    self.future = None
    self.fetch_key = None
    self.preview_only = False
    self.retry_after = 0
    self.off_route_since = 0
    self.arrived_since = 0
    self.ended_revision = None
    self.hud_route = None
    self.route_since = 0          # when the current route started guiding (reroute grace)
    self.rerouted_at = 0          # last off-route refetch
    self.last_end_m = float('inf')  # last fresh fix's distance to the route end, for the key-cycle check
    self.session = uuid.uuid4().hex

  def update(self, now_ns: int, position, drive_id: int, control_source: bool = True) -> dict:
    if position is not None:
      stamp, coordinates, _, bearing = position
      if 0 < stamp <= now_ns <= stamp + GPS_MAX_AGE_NS:
        self.owner.position_store.record({'longitude': coordinates[0], 'latitude': coordinates[1], 'bearing': bearing})
    if position is None:
      self.owner.position_store.flush()
    # 10-31: a deviceState blip (drive_id 0 for a moment) or key-off is not a new drive; only a new start is.
    # Before, each 0 <-> id flip dropped the route and fetched it again mid-drive ("Rerouting" with no reason).
    drive = drive_id or (self.key[3] if self.key is not None else 0)
    settings, key, exclusions = self._routing(drive)
    if key != self.key:
      # 10-31: a drive that ended parked at the destination (arrival missed in a GPS gap, or key-off before
      # END_ROUTE_NS) must not resume guiding to the same place on the next drive.
      if (self.key is not None and self.key[:3] == key[:3] and self.key[4:] == key[4:] and self.key[3] != drive
          and key[2] is not None and self.last_end_m < KEY_END_M):
        self._end_route(settings['revision'])
        settings, key, exclusions = self._routing(drive)
      self.last_end_m = float('inf')
      self.rerouted_at = 0
      self.key, self.route = key, None
      self.routes = []
      self.preview_only = False
      self.retry_after = self.off_route_since = self.arrived_since = 0
    # A saved origin can draw a preview, but a fresh fix must calculate its own route.
    if position is not None and self.preview_only:
      self.route, self.routes = None, []
      self.retry_after = 0
      self.fetch_key = None  # reject an in-flight request from the saved origin
      self.preview_only = False
    base_status = ('disabled' if not settings['enabled'] else 'needsKey' if not settings['token'] else
                   'noDestination' if settings['destination'] is None else 'waitingForLocation')
    result = {'sessionId': self.session, 'frameMonoTime': now_ns, 'startedMonoTime': drive_id,
                  'revision': settings['revision'], 'enabled': settings['enabled'], 'status': base_status,
                  'destinationName': (settings['destination'] or {}).get('name', ''), 'instruction': {}, 'nextManeuver': {},
                  'route': [], 'locationMonoTime': 0, 'controlValid': False}
    if self.future is not None and self.future.done():
      try:
        route = self.future.result()
      except (ValidationError, OSError, ValueError):
        route = None
      if self.fetch_key == self.key:
        self.routes = getattr(route, 'alternatives', [route]) if route is not None else []
        self.route = route
        if self.routes:
          self.owner.record_routes(settings['revision'], self.routes)
        self.retry_after = now_ns + 30_000_000_000 if route is None else 0
      self.future = None
    if self.routes:
      if getattr(self, 'routes_revision', None) != settings['revision']:
        self.owner.record_routes(settings['revision'], self.routes)
        self.routes_revision = settings['revision']
      index = settings.get('routeChoice', 0)
      selected_route = self.routes[index] if type(index) is int and 0 <= index < len(self.routes) else self.routes[0]
      if selected_route is not self.route:
        self.off_route_since = self.arrived_since = 0
        self.route_since = now_ns
      self.route = selected_route
    if base_status != 'waitingForLocation':
      return result
    if position is None:
      if self.route is not None:
        result['route'] = self.route.preview()
        # 10-31: the fix dropped while stopped at the destination (u-blox outages at the door): arrival still ends.
        if self.arrived_since and now_ns - self.arrived_since >= ARRIVED_NS:
          result['status'] = 'arrived'
          if now_ns - self.arrived_since >= END_ROUTE_NS:
            self._end_route(settings['revision'])
      else:
        saved = self.owner.position_store.read()
        if saved is not None:
          result['status'] = 'routeUnavailable' if self.retry_after > now_ns else 'routing'
          if self.future is None and now_ns >= self.retry_after:
            self.preview_only = True
            self.fetch_key = self.key
            self.future = self.executor.submit(self.engine.fetch, settings['token'],
                                               (saved['longitude'], saved['latitude']), settings['destination'], saved.get('bearing'), exclusions)
      return result
    stamp, coordinates, speed, bearing = position
    result['locationMonoTime'] = stamp
    if self.route is None:
      result['status'] = 'routeUnavailable' if self.retry_after > now_ns else 'routing'
      if self.future is None and now_ns >= self.retry_after:
        self.fetch_key = self.key
        self.future = self.executor.submit(self.engine.fetch, settings['token'], coordinates, settings['destination'], bearing, exclusions)
      return result
    progress = self.route.progress(coordinates, speed, bearing)
    fresh = now_ns <= stamp + GPS_MAX_AGE_NS
    graced = self.route_since and now_ns - self.route_since < REROUTE_GRACE_NS
    self.off_route_since = (self.off_route_since or now_ns) if fresh and progress.off_route and not graced else 0
    # A stale fix (u-blox outage) neither starts nor cancels arrival: stopped at the door, the clock keeps running.
    if fresh:
      self.arrived_since = (self.arrived_since or now_ns) if progress.arrived else 0
      self.last_end_m = progress.end_m
    if (self.off_route_since and now_ns - self.off_route_since >= OFF_ROUTE_NS and not self.arrived_since
        and (not self.rerouted_at or now_ns - self.rerouted_at >= REROUTE_GAP_NS)):
      self.rerouted_at = now_ns
      self.route = None
      self.routes = []
      result['status'] = 'routing'
      return result
    arrived = self.arrived_since and now_ns - self.arrived_since >= ARRIVED_NS
    if self.arrived_since and now_ns - self.arrived_since >= END_ROUTE_NS:
      self._end_route(settings['revision'])
    if self.hud_route is not self.route:
      # Galaxy HUD v3: once per guided route, before the first status that guides along it.
      try:
        self.owner.record_hud_route(self.route.hud_route())
        self.hud_route = self.route
      except (OSError, ValueError, AttributeError):
        pass
    result.update(status='arrived' if arrived else 'guiding', instruction=progress.instruction,
                  nextManeuver=progress.next_maneuver, route=self.route.preview(),
                  controlValid=bool(control_source and speed is not None and fresh and drive_id > 0 and not progress.off_route and not progress.arrived and stamp >= drive_id))
    return result

  def _routing(self, drive: int):
    settings = self.owner.read_routing()
    selected = settings['destination']
    destination_key = None if selected is None else (selected['id'], selected['longitude'], selected['latitude'])
    exclusions = tuple(value for key, value in ROUTE_AVOIDANCES.items() if settings[key])
    return settings, (settings['enabled'], hashlib.sha256(settings['token'].encode()).digest(), destination_key, drive, exclusions), exclusions

  def _end_route(self, revision: str) -> None:
    # Once per destination; a concurrent change (new destination, Galaxy edit) wins over arrival.
    if self.ended_revision == revision:
      return
    try:
      self.owner.clear(revision, True)
    except ConflictError:
      self.ended_revision = revision
    except (ValidationError, OSError):
      return
    else:
      self.ended_revision = revision


def phone_gps_dict(phone_fix) -> dict | None:
  if phone_fix is None:
    return None
  gps = dict(vars(phone_fix[1]))
  gps["vNED"] = list(gps.get("vNED", ()))
  return gps


def publish_status(pm, value: dict, phone_fix=None) -> None:
  from openpilot.cereal import messaging
  message = messaging.new_message('starpilotNavigation', valid=True)
  from openpilot.starpilot.navigation.wire import navigation_envelope
  message.starpilotNavigation = {**navigation_envelope(value), **({'phoneGps': gps} if (gps := phone_gps_dict(phone_fix)) else {})}
  pm.send('starpilotNavigation', message)


def main():
  from openpilot.cereal import messaging
  from openpilot.common.realtime import Ratekeeper
  from openpilot.common.swaglog import cloudlog
  owner = NavigationOwner()
  runtime = RouteRuntime(owner)
  sm = messaging.SubMaster(['deviceState', *(service for service in GPS_SERVICES if service != 'starpilotNavigation')])
  pm = messaging.PubMaster(['starpilotNavigation'])
  # Forward new phone measurements promptly; held fixes still need only a 1 Hz heartbeat.
  rate = Ratekeeper(5.)
  next_update_ns = 0
  last_phone_stamp = 0
  try:
    while True:
      sm.update(0)
      now = time.monotonic_ns()
      device = sm['deviceState']
      device_stamp = sm.logMonoTime['deviceState']
      drive_id = (device.startedMonoTime if sm.valid['deviceState'] and device.started and
                  0 < device.startedMonoTime <= device_stamp <= now <= device_stamp + 2_000_000_000 else 0)
      try:
        phone_fix = read_phone_gps(now)
        phone_stamp = phone_fix[0] if phone_fix is not None else 0
        if now >= next_update_ns or phone_stamp != last_phone_stamp:
          next_update_ns = now + 1_000_000_000
          last_phone_stamp = phone_stamp
          source, position = located(sm, now, phone_fix)
          value = runtime.update(now, position, drive_id, source in CONTROL_SOURCES)
          publish_status(pm, value, phone_fix)
      except (ValidationError, OSError, ValueError):
        cloudlog.warning('navigation settings or route unavailable')
      rate.keep_time()
  finally:
    owner.position_store.flush(force=True)


if __name__ == '__main__':
  main()
