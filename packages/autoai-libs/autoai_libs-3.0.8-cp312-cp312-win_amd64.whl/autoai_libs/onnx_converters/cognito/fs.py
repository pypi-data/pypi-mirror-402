################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

from onnxconverter_common import apply_cast
from skl2onnx import update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import DoubleTensorType, FloatTensorType, guess_proto_type
from skl2onnx.proto import onnx_proto

from autoai_libs.cognito.transforms.transform_utils import FS1, FS2, FS3


def fs_shape_calculator(operator: Operator) -> None:
    op = operator.raw_operator

    if hasattr(op, "cols_to_keep_final_"):
        n_cols_to_keep = len(op.cols_to_keep_final_)
    elif hasattr(op, "colids_to_remove"):
        n_cols_to_keep = len(operator.inputs) - len(op.colids_to_remove)
    else:
        raise ValueError(f"Missing required attribute in transformer {op.__class__}")

    dims = [operator.inputs[0].get_first_dimension(), n_cols_to_keep]

    if isinstance(operator.inputs[0].type, FloatTensorType):
        operator.outputs[0].type = FloatTensorType(dims)
    else:
        operator.outputs[0].type = DoubleTensorType(dims)


def fs_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    inputs = operator.inputs
    outputs = operator.outputs
    op = operator.raw_operator

    if hasattr(op, "cols_to_keep_final_"):
        colids_to_keep = getattr(op, "cols_to_keep_final_", [])
    elif hasattr(op, "colids_to_remove"):
        if len(inputs) > 1:
            colids_to_keep = [
                col_index for col_index in range(len(inputs)) if col_index not in getattr(op, "colids_to_remove", [])
            ]
        else:
            colids_to_keep = [
                col_index
                for col_index in range(inputs[0].type.shape[1])
                if col_index not in getattr(op, "colids_to_remove", [])
            ]
    else:
        raise ValueError(f"Missing required attribute in transformer {op.__class__}")

    concat_inputs = []

    for inpt in operator.inputs:
        target_type = guess_proto_type(operator.outputs[0].type)
        casted_name = scope.get_unique_variable_name("casted_input")
        apply_cast(scope, inpt.full_name, casted_name, container, to=target_type)
        concat_inputs.append(casted_name)

    concat_output = scope.get_unique_variable_name("Concat")
    container.add_node(
        "Concat",
        inputs=concat_inputs,
        outputs=[concat_output],
        axis=1,
    )

    col_index_initializer = scope.get_unique_variable_name(f"col_idx")
    container.add_initializer(
        col_index_initializer, onnx_proto.TensorProto.INT64, [len(colids_to_keep)], colids_to_keep
    )

    container.add_node(
        "Gather",
        inputs=[concat_output, col_index_initializer],
        outputs=[outputs[0].full_name],
        name=scope.get_unique_operator_name("GatherColumn"),
        axis=1,
    )


for fs_transformer in [FS1, FS2, FS3]:
    update_registered_converter(
        model=fs_transformer,
        alias=f"AutoAI{fs_transformer.__name__}",
        shape_fct=fs_shape_calculator,
        convert_fct=fs_transformer_converter,
    )
