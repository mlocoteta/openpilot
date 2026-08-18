from openpilot.selfdrive.ui.onroad.starpilot.pip_sidecam import (
  IMAGE_TO_VEHICLE_SIDE,
  PIP_FRAGMENT_SHADER,
  PipSideCamera,
)


def test_pip_maps_raw_driver_image_sides_to_vehicle_sides():
  assert IMAGE_TO_VEHICLE_SIDE == {"left": "right", "right": "left"}

  camera = PipSideCamera.__new__(PipSideCamera)
  camera._closed = True
  camera._mask = {
    "center_left": [100, 200],
    "center_right": [900, 200],
    "crop_size": 100,
  }

  left_vehicle_crop = camera._crop_rect("left")
  right_vehicle_crop = camera._crop_rect("right")

  assert (left_vehicle_crop.x, left_vehicle_crop.y) == (850, 150)
  assert (right_vehicle_crop.x, right_vehicle_crop.y) == (50, 150)


def test_pip_driver_camera_shader_mirrors_the_crop():
  assert "uniform int uFlipX" in PIP_FRAGMENT_SHADER
  assert "cropCoord.x = 1.0 - cropCoord.x" in PIP_FRAGMENT_SHADER


def test_pip_driver_camera_shader_masks_before_sampling_and_keeps_two_texture_reads():
  assert "fwidth(radius)" in PIP_FRAGMENT_SHADER
  assert "if (radius > 1.0 + aa)" in PIP_FRAGMENT_SHADER
  assert PIP_FRAGMENT_SHADER.index("if (radius > 1.0 + aa)") < PIP_FRAGMENT_SHADER.index("texture(texture0")
  assert PIP_FRAGMENT_SHADER.count("texture(texture0") == 1
  assert PIP_FRAGMENT_SHADER.count("texture(texture1") == 1


def test_pip_driver_camera_shader_uses_analytic_bubble_shading_without_new_uniforms():
  assert "float z = sqrt(max(0.0, 1.0 - dot(p, p)))" in PIP_FRAGMENT_SHADER
  assert "BUBBLE_REFRACTION" in PIP_FRAGMENT_SHADER
  assert "BUBBLE_EDGE_DARKEN" in PIP_FRAGMENT_SHADER
  assert "BUBBLE_HIGHLIGHT" in PIP_FRAGMENT_SHADER
  assert "BUBBLE_RIM" in PIP_FRAGMENT_SHADER
  assert "BUBBLE_EDGE_TRANSPARENCY" in PIP_FRAGMENT_SHADER
  assert "BUBBLE_BORDER_WIDTH" not in PIP_FRAGMENT_SHADER
  assert "rgb = mix(rgb, vec3(1.0)" not in PIP_FRAGMENT_SHADER
  assert "uniform sampler2D texture2" not in PIP_FRAGMENT_SHADER
  assert "uRefraction" not in PIP_FRAGMENT_SHADER
