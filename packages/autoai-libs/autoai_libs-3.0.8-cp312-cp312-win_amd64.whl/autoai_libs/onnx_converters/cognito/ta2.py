################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
from onnxconverter_common import apply_identity
from skl2onnx import update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import DoubleTensorType, FloatTensorType, guess_proto_type
from skl2onnx.operator_converters.common import concatenate_variables
from skl2onnx.proto import onnx_proto

from autoai_libs.cognito.transforms.transform_utils import TA2
from autoai_libs.onnx_converters.cognito.utils import add_node_to_replace_nan_and_inf


def ta2_shape_calculator(operator: Operator) -> None:
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    n_new_cols = len(operator.raw_operator.colid_pairs_)
    operator.outputs[0].type = operator.inputs[0].type.__class__(
        [operator.inputs[0].get_first_dimension(), op_features + n_new_cols]
    )


def ta2_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    outputs_tensor = operator.outputs[0]
    op: TA2 = operator.raw_operator
    selected_colid_pairs = op.colid_pairs_

    fun_map = {
        np.true_divide: "Div",
        np.fmax: "Max",
        np.fmin: "Min",
        np.subtract: "Sub",
        np.add: "Add",
        np.multiply: "Mul",
    }
    onnx_op = fun_map.get(op.fun)
    if onnx_op is None:
        raise ValueError(f"Unsupported function: {op.fun}")

    new_log_outputs = []

    casted_input = concatenate_variables(scope, operator.inputs, container, main_type=outputs_tensor.type.__class__)
    original_outputs = [casted_input]

    for col_pair_index in selected_colid_pairs:
        col_index_initializer_1 = scope.get_unique_variable_name(f"col_idx_{col_pair_index[0]}")
        col_index_initializer_2 = scope.get_unique_variable_name(f"col_idx_{col_pair_index[1]}")

        container.add_initializer(col_index_initializer_1, onnx_proto.TensorProto.INT64, [1], [col_pair_index[0]])
        container.add_initializer(col_index_initializer_2, onnx_proto.TensorProto.INT64, [1], [col_pair_index[1]])

        col_output_1 = scope.get_unique_variable_name(f"col_{col_pair_index[0]}")
        col_output_2 = scope.get_unique_variable_name(f"col_{col_pair_index[1]}")

        container.add_node(
            "Gather",
            inputs=[casted_input, col_index_initializer_1],
            outputs=[col_output_1],
            name=scope.get_unique_operator_name("GatherColumn"),
            axis=1,
        )
        container.add_node(
            "Gather",
            inputs=[casted_input, col_index_initializer_2],
            outputs=[col_output_2],
            name=scope.get_unique_operator_name("GatherColumn"),
            axis=1,
        )
        fun_output = scope.get_unique_variable_name("fun_output")
        container.add_node(
            onnx_op,
            inputs=[col_output_1, col_output_2],
            outputs=[fun_output],
            name=scope.get_unique_operator_name("Fun"),
        )
        cleaned_output = add_node_to_replace_nan_and_inf(
            scope=scope, container=container, input=fun_output, initializer_type=guess_proto_type(outputs_tensor.type)
        )
        new_log_outputs.append(cleaned_output)
    if selected_colid_pairs:
        container.add_node(
            "Concat",
            inputs=original_outputs + new_log_outputs,
            outputs=[outputs_tensor.full_name],
            name=scope.get_unique_operator_name("ConcatTA"),
            axis=1,
        )
    else:
        apply_identity(scope, original_outputs, outputs_tensor.full_name, container)


transformer = TA2
update_registered_converter(
    model=transformer,
    alias=f"AutoAI{transformer.__name__}",
    shape_fct=ta2_shape_calculator,
    convert_fct=ta2_transformer_converter,
)
