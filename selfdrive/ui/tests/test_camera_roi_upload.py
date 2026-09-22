from types import SimpleNamespace

import numpy as np
import pytest
import pyray as rl

from openpilot.selfdrive.ui.onroad.cameraview import CameraView


@pytest.fixture
def camera(monkeypatch):
  view = object.__new__(CameraView)
  stride, height, uv_offset = 32, 20, 800
  data = np.arange(uv_offset + stride * height // 2, dtype=np.uint8)
  view.frame = SimpleNamespace(width=24, height=height, stride=stride, uv_offset=uv_offset, data=data)
  view.texture_y = SimpleNamespace(id=1)
  view.texture_uv = SimpleNamespace(id=2)
  view._texture_needs_update = True
  view._texture_frame_data = None
  view._texture_upload_rect = None
  uploads = []

  def upload(texture, rect, pointer):
    bpp = 1 if texture.id == 1 else 2
    size = int(rect.width * rect.height * bpp)
    pixels = np.frombuffer(rl.ffi.buffer(pointer, size), dtype=np.uint8).copy()
    uploads.append((texture.id, (int(rect.x), int(rect.y), int(rect.width), int(rect.height)), pixels))

  monkeypatch.setattr(rl, 'update_texture_rec', upload)
  yield view, uploads
  view.texture_y = view.texture_uv = None
  view._closed = True


def test_upload_packs_padded_rows_and_preserves_uv_pairs(camera):
  view, uploads = camera
  frame = view.frame
  assert view._upload_texture_region(rl.Rectangle(0, 0, 24, 20), rl.Rectangle(-24, -20, 72, 60), rl.Rectangle(0, 0, 24, 20))

  assert len(uploads) == 2
  x0, y0, x1, y1 = view._texture_upload_rect
  assert all(value % 2 == 0 for value in (x0, y0, x1, y1))
  assert uploads[0][:2] == (1, (x0, y0, x1 - x0, y1 - y0))
  assert uploads[1][:2] == (2, (x0 // 2, y0 // 2, (x1 - x0) // 2, (y1 - y0) // 2))
  y_plane = frame.data[:frame.stride * frame.height].reshape(frame.height, frame.stride)
  uv_plane = frame.data[frame.uv_offset:].reshape(frame.height // 2, frame.stride // 2, 2)
  np.testing.assert_array_equal(uploads[0][2], y_plane[y0:y1, x0:x1].ravel())
  np.testing.assert_array_equal(uploads[1][2], uv_plane[y0 // 2:y1 // 2, x0 // 2:x1 // 2].ravel())
  assert not np.shares_memory(view._texture_frame_data, frame.data)


def test_unchanged_or_smaller_viewport_does_not_upload_again(camera):
  view, uploads = camera
  src, dst = rl.Rectangle(0, 0, 24, 20), rl.Rectangle(0, 0, 24, 20)
  assert view._upload_texture_region(src, dst, rl.Rectangle(5, 5, 10, 10))
  assert view._upload_texture_region(src, dst, rl.Rectangle(7, 7, 5, 5))
  assert len(uploads) == 2


def test_expanding_viewport_uses_owned_frame_after_camera_buffer_reuse(camera):
  view, uploads = camera
  src, dst = rl.Rectangle(0, 0, 24, 20), rl.Rectangle(0, 0, 24, 20)
  view._upload_texture_region(src, dst, rl.Rectangle(8, 8, 4, 4))
  expected = view.frame.data.copy()
  view.frame.data[:] = 255

  assert view._upload_texture_region(src, dst, rl.Rectangle(0, 0, 24, 20))

  x0, y0, x1, y1 = view._texture_upload_rect
  np.testing.assert_array_equal(uploads[-2][2], expected[:640].reshape(20, 32)[y0:y1, x0:x1].ravel())
  np.testing.assert_array_equal(uploads[-1][2], expected[800:].reshape(10, 16, 2)[y0 // 2:y1 // 2, x0 // 2:x1 // 2].ravel())


def test_new_camera_frame_invalidates_coverage_and_reuses_snapshot_storage(camera):
  view, uploads = camera
  src, dst = rl.Rectangle(0, 0, 24, 20), rl.Rectangle(0, 0, 24, 20)
  view._upload_texture_region(src, dst, rl.Rectangle(0, 0, 24, 20))
  storage = view._texture_frame_data
  view.frame.data[:] = 37
  view._texture_needs_update = True

  view._upload_texture_region(src, dst, rl.Rectangle(8, 8, 4, 4))

  assert view._texture_frame_data is storage
  assert view._texture_upload_rect == (6, 6, 14, 14)
  np.testing.assert_array_equal(uploads[-2][2], 37)
  np.testing.assert_array_equal(uploads[-1][2], 37)


def test_invisible_frame_is_owned_before_it_becomes_visible(camera):
  view, uploads = camera
  src, dst = rl.Rectangle(0, 0, 24, 20), rl.Rectangle(0, 0, 24, 20)
  assert not view._upload_texture_region(src, dst, rl.Rectangle(50, 50, 10, 10))
  assert not uploads
  expected = view._texture_frame_data.copy()
  view.frame.data[:] = 0

  assert view._upload_texture_region(src, dst, rl.Rectangle(0, 0, 24, 20))
  np.testing.assert_array_equal(view._texture_frame_data, expected)
  assert len(uploads) == 2


def test_disjoint_viewports_upload_the_bounding_region_without_holes(camera):
  view, uploads = camera
  src, dst = rl.Rectangle(0, 0, 24, 20), rl.Rectangle(0, 0, 24, 20)
  view._upload_texture_region(src, dst, rl.Rectangle(0, 0, 2, 2))
  view._upload_texture_region(src, dst, rl.Rectangle(22, 18, 2, 2))
  count = len(uploads)

  assert view._upload_texture_region(src, dst, rl.Rectangle(9, 9, 2, 2))
  assert len(uploads) == count
  assert view._texture_upload_rect == (0, 0, 26, 20)


@pytest.mark.parametrize(('enabled', 'stream', 'stride', 'height', 'region_expected'), [
  (False, 'VISION_STREAM_ROAD', 32, 20, False),
  (True, 'VISION_STREAM_ROAD', 32, 20, True),
  (True, 'VISION_STREAM_WIDE_ROAD', 32, 20, True),
  (True, 'VISION_STREAM_DRIVER', 32, 20, False),
  (True, 'VISION_STREAM_ROAD', 31, 20, False),
  (True, 'VISION_STREAM_ROAD', 32, 21, False),
])
def test_only_opted_in_even_road_frames_use_region_upload(camera, monkeypatch, enabled, stream, stride, height, region_expected):
  from msgq.visionipc import VisionStreamType

  view, _ = camera
  view._use_roi_upload = enabled
  view._use_egl = False
  view._stream_type = getattr(VisionStreamType, stream)
  view._switching = False
  view._onroad_reentry_pending = False
  view.frame.stride = stride
  view.frame.height = height
  view.client = SimpleNamespace(recv=lambda **_: None, is_connected=lambda: True)
  monkeypatch.setattr(view, '_calc_frame_matrix', lambda _: np.eye(3))
  calls = []
  monkeypatch.setattr(view, '_render_textures', lambda *args: calls.append(args))
  rect = rl.Rectangle(0, 0, 24, 20)

  view._render(rect)

  assert len(calls) == 1
  assert len(calls[0]) == (3 if region_expected else 2)
