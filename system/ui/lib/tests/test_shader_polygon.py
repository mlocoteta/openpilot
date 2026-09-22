import numpy as np
import pyray as rl
import pytest
from types import SimpleNamespace

from openpilot.system.ui.lib import shader_polygon
from openpilot.system.ui.lib.shader_polygon import Gradient, draw_polygon, triangulate


def test_triangulate_interleaves_polygon_chains():
  points = np.array([
    [1.0, 10.0],
    [2.0, 20.0],
    [3.0, 30.0],
    [30.0, 300.0],
    [20.0, 200.0],
    [10.0, 100.0],
  ], dtype=np.float32)

  np.testing.assert_array_equal(triangulate(points), [
    [1.0, 10.0], [10.0, 100.0],
    [2.0, 20.0], [20.0, 200.0],
    [3.0, 30.0], [30.0, 300.0],
  ])


def test_triangulate_drops_unpaired_last_point():
  points = np.array([
    [1.0, 10.0],
    [2.0, 20.0],
    [20.0, 200.0],
    [10.0, 100.0],
    [99.0, 99.0],
  ], dtype=np.float32)

  np.testing.assert_array_equal(triangulate(points), [
    [1.0, 10.0], [10.0, 100.0],
    [2.0, 20.0], [20.0, 200.0],
  ])


@pytest.mark.parametrize("points", [
  np.arange(132, dtype=np.float32).reshape(-1, 2),
  np.arange(132, dtype=np.float64).reshape(-1, 2),
  np.arange(264, dtype=np.float64).reshape(-1, 2)[::2, ::-1],
  np.asfortranarray(np.arange(132, dtype=np.float32).reshape(-1, 2)),
])
def test_triangulate_preserves_coordinates_in_contiguous_float_buffer(points):
  original = points.copy()
  points.flags.writeable = False
  strip = triangulate(points)
  expected = [point for pair in zip(points[:len(points) // 2], points[len(points) // 2:][::-1], strict=True) for point in pair]

  assert strip.dtype == np.float32
  assert strip.flags.c_contiguous
  np.testing.assert_array_equal(strip, np.asarray(expected, dtype=np.float32))
  np.testing.assert_array_equal(points, original)


@pytest.mark.parametrize("use_gradient", [False, True])
@pytest.mark.parametrize("point_count", [4, 5, 66])
def test_draw_polygon_passes_native_vertices(monkeypatch, use_gradient, point_count):
  points = np.arange(point_count * 4, dtype=np.float64).reshape(-1, 2)[::2]
  rect = rl.Rectangle(0, 0, 100, 100)
  color = rl.Color(10, 20, 30, 40)
  gradient = Gradient((0, 0), (1, 1), [color, rl.Color(*rl.WHITE)], [0, 1]) if use_gradient else None
  calls = []
  state = SimpleNamespace(initialize=lambda: calls.append("initialize"), shader="shader")

  def draw_strip(vertices, count, fill):
    assert rl.ffi.typeof(vertices) == rl.ffi.typeof("Vector2 *")
    coordinates = [[vertices[i].x, vertices[i].y] for i in range(count)]
    np.testing.assert_array_equal(coordinates, triangulate(points))
    assert fill == (rl.WHITE if use_gradient else color)
    calls.append("draw")

  monkeypatch.setattr(shader_polygon.ShaderState, "get_instance", lambda: state)
  monkeypatch.setattr(shader_polygon, "_configure_shader_color", lambda *args: calls.append(("configure", args)))
  monkeypatch.setattr(rl, "begin_shader_mode", lambda shader: calls.append(("begin", shader)))
  monkeypatch.setattr(rl, "end_shader_mode", lambda: calls.append("end"))
  monkeypatch.setattr(rl, "draw_triangle_strip", draw_strip)

  draw_polygon(rect, points, gradient=gradient, color=None if use_gradient else color)

  assert calls == (["initialize", ("configure", (state, None, gradient, rect)), ("begin", "shader"), "draw", "end"]
                   if use_gradient else ["draw"])
