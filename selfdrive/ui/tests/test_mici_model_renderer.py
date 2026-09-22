from types import SimpleNamespace

import numpy as np
import pytest

from openpilot.selfdrive.ui.mici.onroad.model_renderer import ModelRenderer


@pytest.fixture
def renderer():
  renderer = object.__new__(ModelRenderer)
  renderer._car_space_transform = np.array([[580, -480, 0], [400, 0, -480], [1, 0, 0]], dtype=np.float32)
  renderer._transform_dirty = False
  renderer._clip_region = SimpleNamespace(x=-500, y=-500, width=2160, height=1800)
  return renderer


def reference_polygon(renderer, line, y_off, z_off, max_idx, allow_invert):
  left, right = [], []
  clip = renderer._clip_region
  previous_y = float('inf')
  for point in line[:max_idx + 1]:
    if not point[0] >= 0:
      continue
    edges = [renderer._car_space_transform @ (point + np.array([0, offset, z_off], dtype=np.float32))
             for offset in (-y_off, y_off)]
    if not all(abs(edge[2]) >= 1e-6 for edge in edges):
      continue
    edges = [edge[:2] / edge[2] for edge in edges]
    if not all(clip.x <= edge[0] <= clip.x + clip.width and clip.y <= edge[1] <= clip.y + clip.height for edge in edges):
      continue
    if not allow_invert and edges[0][1] > previous_y:
      continue
    previous_y = edges[0][1]
    left.append(edges[0])
    right.append(edges[1])
  return np.array(left + right[::-1], dtype=np.float32).reshape(-1, 2)


@pytest.mark.parametrize('allow_invert', [False, True])
@pytest.mark.parametrize('length', [0, 1, 33, 100])
@pytest.mark.parametrize('max_idx', [0, 15, 100])
@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_projection_preserves_clipping_and_hill_geometry(renderer, allow_invert, length, max_idx, dtype):
  rng = np.random.default_rng(42)
  line = np.column_stack((np.linspace(-5, 110, length), rng.normal(0, 6, length), rng.normal(0, 1, length))).astype(dtype)
  expected = reference_polygon(renderer, line, 0.9, 1.22, max_idx, allow_invert)
  actual = renderer._map_line_to_polygon(line, 0.9, 1.22, max_idx, allow_invert)

  assert actual.dtype == np.float32
  assert actual.flags.c_contiguous
  np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-3)


@pytest.mark.parametrize('allow_invert', [False, True])
def test_projection_discards_zero_depth_and_out_of_view_points(renderer, allow_invert):
  line = np.array([[0, 0, 0], [1e-7, 0, 0], [-5, 0, 0], [1, 100, 0]], dtype=np.float32)
  with np.errstate(divide='raise', invalid='raise'):
    actual = renderer._map_line_to_polygon(line, 0.9, 1.22, len(line), allow_invert)
  assert actual.shape == (0, 2)


def test_projection_requires_both_polygon_edges_inside_clip(renderer):
  renderer._clip_region = SimpleNamespace(x=0, y=0, width=100, height=100)
  renderer._car_space_transform = np.eye(3, dtype=np.float32)
  line = np.array([[10, 10, 1], [20, 99, 1], [30, 15, 1]], dtype=np.float32)

  actual = renderer._map_line_to_polygon(line, 2, 0, len(line))

  np.testing.assert_array_equal(actual, [[10, 8], [30, 13], [30, 17], [10, 12]])


def test_projection_removes_hill_inversions_after_clipping(renderer):
  renderer._car_space_transform = np.eye(3, dtype=np.float32)
  line = np.array([[10, 50, 1], [20, 40, 1], [30, 45, 1], [40, 30, 1], [50, 30, 1]], dtype=np.float32)

  actual = renderer._map_line_to_polygon(line, 2, 0, len(line), allow_invert=False)

  np.testing.assert_array_equal(actual[:len(actual) // 2], [[10, 48], [20, 38], [40, 28], [50, 28]])


def test_unchanged_transform_keeps_geometry_cached(renderer):
  original = renderer._car_space_transform
  renderer.set_transform(original.astype(np.float64))

  assert renderer._car_space_transform is original
  assert not renderer._transform_dirty

  renderer._transform_dirty = True
  renderer.set_transform(original)
  assert renderer._transform_dirty


def test_changed_transform_invalidates_geometry_and_copies_input(renderer):
  transform = renderer._car_space_transform.astype(np.float64)
  transform[0, 0] += 1
  renderer.set_transform(transform)

  assert renderer._transform_dirty
  assert renderer._car_space_transform.dtype == np.float32
  np.testing.assert_array_equal(renderer._car_space_transform, transform)
  transform[0, 0] += 1
  assert renderer._car_space_transform[0, 0] != transform[0, 0]
