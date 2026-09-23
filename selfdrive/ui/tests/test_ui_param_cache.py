import threading

import pytest

from openpilot.selfdrive.ui.lib import ui_param_cache
from openpilot.selfdrive.ui.lib.ui_param_cache import UIParamCache


class FakeParams:
  def __init__(self):
    self.values = {"enabled": False, "count": 1}
    self.calls = []

  def get(self, key, **_kwargs):
    self.calls.append(("get", key))
    return self.values.get(key)

  def get_bool(self, key, **_kwargs):
    self.calls.append(("get_bool", key))
    return bool(self.values.get(key, False))

  def get_int(self, key, **_kwargs):
    self.calls.append(("get_int", key))
    return int(self.values.get(key, 0))

  def get_float(self, key, **_kwargs):
    self.calls.append(("get_float", key))
    return float(self.values.get(key, 0.0))

  def put(self, key, value, **_kwargs):
    self.values[key] = value

  def put_bool(self, key, value, **_kwargs):
    self.values[key] = value

  def put_int(self, key, value, **_kwargs):
    self.values[key] = value

  def put_float(self, key, value, **_kwargs):
    self.values[key] = value

  def put_nonblocking(self, key, value):
    self.values[key] = value

  def put_bool_nonblocking(self, key, value):
    self.values[key] = value

  def remove(self, key):
    self.values.pop(key, None)

  def clear_all(self, marker=None):
    self.calls.append(("clear_all", marker))
    self.values.clear()


def test_reads_are_shared_until_ttl():
  now = [0.0]
  params = FakeParams()
  cached = UIParamCache(params, ttl=0.1, clock=lambda: now[0])

  assert not cached.get_bool("enabled")
  assert not cached.get_bool("enabled")
  assert params.calls == [("get_bool", "enabled")]

  now[0] = 0.11
  params.values["enabled"] = True
  assert cached.get_bool("enabled")
  assert params.calls.count(("get_bool", "enabled")) == 2


def test_writes_invalidate_immediately():
  params = FakeParams()
  cached = UIParamCache(params, ttl=10.0)

  assert not cached.get_bool("enabled")
  cached.put_bool("enabled", True)
  assert cached.get_bool("enabled")
  assert params.calls.count(("get_bool", "enabled")) == 2


@pytest.mark.parametrize("background", [False, True])
def test_zero_ttl_disables_caching(background):
  params = FakeParams()
  cached = UIParamCache(params, ttl=0.0)
  if background:
    cached.start()
  try:
    assert not cached.get_bool("enabled")
    params.values["enabled"] = True
    assert cached.get_bool("enabled")
    assert params.calls.count(("get_bool", "enabled")) == 2
  finally:
    cached.stop()


@pytest.mark.parametrize("method", ["put", "put_bool", "put_int", "put_float", "put_nonblocking", "put_bool_nonblocking"])
def test_all_write_paths_invalidate(method):
  params = FakeParams()
  cached = UIParamCache(params, ttl=10.0)
  assert not cached.get_bool("enabled")
  getattr(cached, method)("enabled", True)
  assert cached.get_bool("enabled")
  assert params.calls.count(("get_bool", "enabled")) == 2


def test_remove_and_clear_all_invalidate():
  params = FakeParams()
  cached = UIParamCache(params, ttl=10.0)

  assert cached.get_int("count") == 1
  cached.remove("count")
  assert cached.get_int("count") == 0

  assert not cached.get_bool("enabled")
  params.values["enabled"] = True
  cached.clear_all("flag")
  params.values["enabled"] = True
  assert cached.get_bool("enabled")
  assert ("clear_all", "flag") in params.calls


class ControlledParams(FakeParams):
  def __init__(self):
    super().__init__()
    self.block_next = False
    self.fail_next = False
    self.read_started = threading.Event()
    self.release_read = threading.Event()
    self.reader_threads = []

  def get_int(self, key, *args, **kwargs):
    self.reader_threads.append(threading.current_thread())
    value = super().get_int(key, **kwargs)
    if self.block_next:
      self.block_next = False
      self.read_started.set()
      if not self.release_read.wait(3):
        raise TimeoutError("Blocked parameter test read was not released")
    if self.fail_next:
      self.fail_next = False
      raise OSError("Parameter temporarily unavailable")
    return value


@pytest.fixture
def async_cache():
  params = ControlledParams()
  now = [0.0]
  cache = UIParamCache(params, ttl=0.1, clock=lambda: now[0])
  cache.start()
  try:
    yield params, cache, now
  finally:
    params.release_read.set()
    cache.stop()


def test_background_cache_keeps_cold_reads_synchronous(async_cache):
  params, cache, _ = async_cache
  assert cache.get_int("count") == 1
  assert params.reader_threads == [threading.current_thread()]


def test_stale_read_returns_while_refresh_is_blocked_and_deduplicates(async_cache):
  params, cache, now = async_cache
  assert cache.get_int("count") == 1
  params.values["count"] = 2
  params.block_next = True
  now[0] = 0.2

  assert cache.get_int("count") == 1
  assert params.read_started.wait(1)
  for _ in range(100):
    assert cache.get_int("count") == 1
  assert len(params.calls) == 2
  assert len(cache._pending) == 1

  now[0] = 0.5
  params.release_read.set()
  cache._refresh_queue.join()
  assert cache.get_int("count") == 2
  assert len(params.calls) == 2
  assert not cache._pending


@pytest.mark.parametrize("clear_all", [False, True])
def test_invalidating_an_inflight_refresh_preserves_new_reads(async_cache, clear_all):
  params, cache, now = async_cache
  assert cache.get_int("count") == 1
  params.block_next = True
  now[0] = 0.2
  assert cache.get_int("count") == 1
  assert params.read_started.wait(1)

  if clear_all:
    cache.clear_all()
    params.values["count"] = 3
  else:
    cache.put_int("count", 3)
  assert cache.get_int("count") == 3
  params.release_read.set()
  cache._refresh_queue.join()
  assert cache.get_int("count") == 3


def test_background_errors_keep_value_and_allow_later_refresh(async_cache):
  params, cache, now = async_cache
  assert cache.get_int("count") == 1
  params.fail_next = True
  params.values["count"] = 2
  now[0] = 0.2
  assert cache.get_int("count") == 1
  cache._refresh_queue.join()
  assert cache.get_int("count") == 1
  assert cache._worker.is_alive()
  assert len(params.calls) == 2

  now[0] = 0.4
  assert cache.get_int("count") == 1
  cache._refresh_queue.join()
  assert cache.get_int("count") == 2


def test_blocking_reads_remain_synchronous(async_cache):
  params, cache, now = async_cache
  assert cache.get_int("count", block=True) == 1
  params.values["count"] = 2
  now[0] = 0.2
  assert cache.get_int("count", block=True) == 2
  assert params.reader_threads == [threading.current_thread()] * 2
  assert not cache._pending


def test_background_cache_does_not_refresh_unused_settings(async_cache):
  params, cache, now = async_cache
  assert cache.get_bool("enabled") is False
  assert cache.get_int("count") == 1
  now[0] = 0.2
  cache.get_int("count")
  cache._refresh_queue.join()
  assert params.calls.count(("get_bool", "enabled")) == 1
  assert params.calls.count(("get_int", "count")) == 2


def test_stop_releases_worker_and_restores_synchronous_refresh(async_cache):
  params, cache, now = async_cache
  assert cache.get_int("count") == 1
  worker = cache._worker
  cache.start()
  assert cache._worker is worker
  cache.stop()
  assert not worker.is_alive()
  params.values["count"] = 2
  now[0] = 0.2
  assert cache.get_int("count") == 2
  assert params.reader_threads == [threading.current_thread()] * 2


def test_timed_out_worker_cannot_publish_after_restart(async_cache):
  params, cache, now = async_cache
  assert cache.get_int("count") == 1
  params.values["count"] = 2
  params.block_next = True
  now[0] = 0.2
  assert cache.get_int("count") == 1
  assert params.read_started.wait(1)
  old_worker, old_queue = cache._worker, cache._refresh_queue
  cache.stop(timeout=0.01)
  assert old_worker.is_alive()

  params.values["count"] = 3
  cache.start()
  assert cache.get_int("count") == 1
  cache._refresh_queue.join()
  assert cache.get_int("count") == 3
  params.release_read.set()
  old_queue.join()
  old_worker.join(1)
  assert not old_worker.is_alive()
  assert cache.get_int("count") == 3


def test_worker_lowers_its_own_realtime_priority(monkeypatch):
  calls = []
  configured = threading.Event()

  def set_scheduler(pid, policy, priority):
    calls.append((pid, policy, priority, threading.current_thread()))
    configured.set()

  monkeypatch.setattr(ui_param_cache, "PC", False)
  monkeypatch.setattr(ui_param_cache.os, "SCHED_OTHER", 0, raising=False)
  monkeypatch.setattr(ui_param_cache.os, "sched_param", lambda priority: priority, raising=False)
  monkeypatch.setattr(ui_param_cache.os, "sched_setscheduler", set_scheduler, raising=False)
  cache = UIParamCache(FakeParams())
  cache.start()
  try:
    assert configured.wait(1)
    assert calls == [(0, 0, 0, cache._worker)]
  finally:
    cache.stop()


def test_worker_priority_failure_restores_synchronous_reads(monkeypatch):
  def set_scheduler(*_):
    raise PermissionError("Unable to change scheduler")

  monkeypatch.setattr(ui_param_cache, "PC", False)
  monkeypatch.setattr(ui_param_cache.os, "SCHED_OTHER", 0, raising=False)
  monkeypatch.setattr(ui_param_cache.os, "sched_param", lambda priority: priority, raising=False)
  monkeypatch.setattr(ui_param_cache.os, "sched_setscheduler", set_scheduler, raising=False)
  monkeypatch.setattr(ui_param_cache.cloudlog, "exception", lambda *_: None)
  params = FakeParams()
  now = [0.0]
  cache = UIParamCache(params, clock=lambda: now[0])
  assert cache.get_int("count") == 1
  cache.start()
  worker = cache._worker
  if worker is not None:
    worker.join(1)
    assert not worker.is_alive()
  params.values["count"] = 2
  now[0] = 0.2
  assert cache.get_int("count") == 2
  assert cache._worker is None
