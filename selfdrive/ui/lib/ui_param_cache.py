"""Small, shared cache for read-mostly UI parameters.

Parameter reads are file-backed.  The raylib UIs ask for the same values from
multiple widgets during a frame, so a short cache avoids repeated open/read/
close cycles. Writes invalidate immediately; opt-in background refresh keeps
expired reads off the render thread while retaining the latest cached value.
"""

from __future__ import annotations

import os
import queue
import threading
import time
from collections.abc import Callable
from typing import Any, NamedTuple

from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware import PC


class _RefreshRequest(NamedTuple):
  cache_key: tuple[Any, ...]
  cached: tuple[float, Any]
  args: tuple[Any, ...]
  kwargs: dict[str, Any]


class UIParamCache:
  def __init__(self, params: Params | Any | None = None, ttl: float = 0.1,
               clock: Callable[[], float] = time.monotonic):
    self._params = params if params is not None else Params()
    self._ttl = max(0.0, ttl)
    self._clock = clock
    self._cache: dict[tuple[Any, ...], tuple[float, Any]] = {}
    self._lock = threading.Lock()
    self._worker: threading.Thread | None = None
    self._refresh_queue: queue.Queue[_RefreshRequest | None] = queue.Queue()
    self._pending: set[tuple[Any, ...]] = set()
    self._stop_event = threading.Event()

  def start(self) -> None:
    with self._lock:
      if self._worker is not None:
        return
      self._refresh_queue = queue.Queue()
      self._pending = set()
      self._stop_event = threading.Event()
      self._worker = threading.Thread(target=self._refresh_worker, name="ui-param-cache", daemon=True,
                                      args=(self._refresh_queue, self._pending, self._stop_event))
      self._worker.start()

  def stop(self, timeout: float = 1.0) -> None:
    with self._lock:
      worker = self._worker
      if worker is None:
        return
      self._worker = None
      self._stop_event.set()
      self._refresh_queue.put(None)
    worker.join(timeout)

  def _refresh_worker(self, requests: queue.Queue[_RefreshRequest | None], pending: set[tuple[Any, ...]],
                      stop_event: threading.Event) -> None:
    if not PC:
      try:
        os.sched_setscheduler(0, os.SCHED_OTHER, os.sched_param(0))
      except OSError:
        cloudlog.exception("Unable to lower UI parameter worker priority")
        with self._lock:
          if self._stop_event is stop_event:
            self._worker = None
        return

    while True:
      request = requests.get()
      try:
        if request is None:
          return
        with self._lock:
          current = not stop_event.is_set() and self._cache.get(request.cache_key) is request.cached
        if not current:
          continue

        method, key = request.cache_key[:2]
        try:
          value = getattr(self._params, method)(key, *request.args, **request.kwargs)
        except Exception:
          value = request.cached[1]
        refreshed_at = self._clock()
        with self._lock:
          if not stop_event.is_set() and self._cache.get(request.cache_key) is request.cached:
            self._cache[request.cache_key] = (refreshed_at, value)
      finally:
        if request is not None:
          with self._lock:
            pending.discard(request.cache_key)
        requests.task_done()

  def _queue_refresh(self, cache_key: tuple[Any, ...], cached: tuple[float, Any],
                     args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
    if cache_key in self._pending:
      return
    with self._lock:
      if self._worker is not None and cache_key not in self._pending and self._cache.get(cache_key) is cached:
        self._pending.add(cache_key)
        self._refresh_queue.put(_RefreshRequest(cache_key, cached, args, kwargs))

  @staticmethod
  def _cache_key(method: str, key: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, ...]:
    if not args and not kwargs:
      return method, key
    # Params arguments are primitive values in UI call sites. repr keeps this
    # robust for an occasional list/dict default without requiring hashability.
    return (method, key, repr(args), repr(sorted(kwargs.items())))

  def _read(self, method: str, key: str, *args: Any, **kwargs: Any) -> Any:
    cache_key = self._cache_key(method, key, args, kwargs)
    now = self._clock()
    cached = self._cache.get(cache_key)
    if cached is not None and now - cached[0] < self._ttl:
      return cached[1]

    blocking = kwargs.get("block", args[0] if args else False)
    if cached is not None and self._worker is not None and self._ttl > 0 and not blocking:
      self._queue_refresh(cache_key, cached, args, kwargs)
      return cached[1]

    value = getattr(self._params, method)(key, *args, **kwargs)
    with self._lock:
      self._cache[cache_key] = (now, value)
    return value

  def get(self, key: str, *args: Any, **kwargs: Any) -> Any:
    return self._read("get", key, *args, **kwargs)

  def get_bool(self, key: str, *args: Any, **kwargs: Any) -> bool:
    return self._read("get_bool", key, *args, **kwargs)

  def get_int(self, key: str, *args: Any, **kwargs: Any) -> int:
    return self._read("get_int", key, *args, **kwargs)

  def get_float(self, key: str, *args: Any, **kwargs: Any) -> float:
    return self._read("get_float", key, *args, **kwargs)

  def invalidate(self, key: str | None = None) -> None:
    with self._lock:
      if key is None:
        self._cache.clear()
        return
      self._cache = {cache_key: value for cache_key, value in self._cache.items()
                     if cache_key[1] != key}

  def put(self, key: str, value: Any, *args: Any, **kwargs: Any) -> None:
    self._params.put(key, value, *args, **kwargs)
    self.invalidate(key)

  def put_bool(self, key: str, value: bool, *args: Any, **kwargs: Any) -> None:
    self._params.put_bool(key, value, *args, **kwargs)
    self.invalidate(key)

  def put_int(self, key: str, value: int, *args: Any, **kwargs: Any) -> None:
    self._params.put_int(key, value, *args, **kwargs)
    self.invalidate(key)

  def put_float(self, key: str, value: float, *args: Any, **kwargs: Any) -> None:
    self._params.put_float(key, value, *args, **kwargs)
    self.invalidate(key)

  def put_nonblocking(self, key: str, value: Any) -> None:
    self._params.put_nonblocking(key, value)
    self.invalidate(key)

  def put_bool_nonblocking(self, key: str, value: bool) -> None:
    self._params.put_bool_nonblocking(key, value)
    self.invalidate(key)

  def remove(self, key: str) -> None:
    self._params.remove(key)
    self.invalidate(key)

  def clear_all(self, *args: Any, **kwargs: Any) -> None:
    self._params.clear_all(*args, **kwargs)
    self.invalidate()

  def __getattr__(self, name: str) -> Any:
    return getattr(self._params, name)


_SHARED_UI_PARAMS: UIParamCache | None = None


def shared_ui_params() -> UIParamCache:
  """Return the cache shared by raylib UI views and settings panels."""
  global _SHARED_UI_PARAMS
  if _SHARED_UI_PARAMS is None:
    _SHARED_UI_PARAMS = UIParamCache()
  return _SHARED_UI_PARAMS
