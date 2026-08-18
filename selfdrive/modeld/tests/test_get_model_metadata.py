import base64
import pickle

import onnx

from openpilot.selfdrive.modeld.get_model_metadata import make_metadata_dict


def test_make_metadata_dict_uses_disk_backed_parser(tmp_path):
  model_input = onnx.helper.make_tensor_value_info("input", onnx.TensorProto.FLOAT, (1, 3))
  model_output = onnx.helper.make_tensor_value_info("output", onnx.TensorProto.FLOAT, (1, 4))
  graph = onnx.helper.make_graph(
    [onnx.helper.make_node("Identity", ["input"], ["output"])],
    "metadata-test",
    [model_input],
    [model_output],
  )
  model = onnx.helper.make_model(graph)
  output_slices = {"path": slice(0, 4)}
  model.metadata_props.append(onnx.StringStringEntryProto(
    key="output_slices",
    value=base64.b64encode(pickle.dumps(output_slices)).decode(),
  ))
  model.metadata_props.append(onnx.StringStringEntryProto(key="model_checkpoint", value="test-checkpoint"))
  model_path = tmp_path / "model.onnx"
  onnx.save(model, model_path)

  metadata = make_metadata_dict(model_path)

  assert metadata == {
    "model_checkpoint": "test-checkpoint",
    "output_slices": output_slices,
    "input_shapes": {"input": (1, 3)},
    "output_shapes": {"output": (1, 4)},
  }
