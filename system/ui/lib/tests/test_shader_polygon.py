import numpy as np

from openpilot.system.ui.lib.shader_polygon import triangulate


def test_triangulate_interleaves_polygon_chains():
  points = np.array([
    [1.0, 10.0],
    [2.0, 20.0],
    [3.0, 30.0],
    [30.0, 300.0],
    [20.0, 200.0],
    [10.0, 100.0],
  ], dtype=np.float32)

  assert triangulate(points) == [
    [1.0, 10.0], [10.0, 100.0],
    [2.0, 20.0], [20.0, 200.0],
    [3.0, 30.0], [30.0, 300.0],
  ]


def test_triangulate_drops_unpaired_last_point():
  points = np.array([
    [1.0, 10.0],
    [2.0, 20.0],
    [20.0, 200.0],
    [10.0, 100.0],
    [99.0, 99.0],
  ], dtype=np.float32)

  assert triangulate(points) == [
    [1.0, 10.0], [10.0, 100.0],
    [2.0, 20.0], [20.0, 200.0],
  ]
