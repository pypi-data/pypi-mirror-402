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

import autoai_libs.cognito.transforms.textras_methods as TExtras
from autoai_libs.cognito.transforms.transform_utils import TA1
from autoai_libs.onnx_converters.cognito.utils import add_node_to_replace_nan_and_inf


def ta1_shape_calculator(operator: Operator) -> None:
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    n_new_cols = len(operator.raw_operator.colids_)
    dims = [operator.inputs[0].get_first_dimension(), op_features + n_new_cols]

    output_type = DoubleTensorType

    #  Tan and cos don't support float64
    if operator.raw_operator.fun in (np.tan, np.cos):
        output_type = FloatTensorType

    operator.outputs[0].type = output_type(dims)


def ta1_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    outputs_tensor = operator.outputs[0]
    op = operator.raw_operator
    selected_cols = op.colids_

    fun_map = {
        np.absolute: "Abs",
        np.log: "Log",
        np.sin: "Sin",
        np.cos: "Cos",
        np.tan: "Tan",
        np.tanh: "Tanh",
        np.cbrt: "Pow",
        np.square: "Pow",
        np.rint: "Round",
        np.exp: "Exp",
        np.sqrt: "Sqrt",
        TExtras.cube: "Pow",
        TExtras.sigmoid: "Sigmoid",
    }
    onnx_op = fun_map.get(op.fun)
    if onnx_op is None:
        raise ValueError(f"Unsupported function: {op.fun}")

    new_log_outputs = []

    initializer_type = guess_proto_type(outputs_tensor.type)
    casted_input = concatenate_variables(scope, operator.inputs, container, main_type=outputs_tensor.type.__class__)

    for col_index in selected_cols:
        col_index_initializer = scope.get_unique_variable_name(f"col_idx_{col_index}")
        container.add_initializer(col_index_initializer, onnx_proto.TensorProto.INT64, [1], [col_index])
        col_output = scope.get_unique_variable_name(f"col_{col_index}")
        container.add_node(
            "Gather",
            inputs=[casted_input, col_index_initializer],
            outputs=[col_output],
            name=scope.get_unique_operator_name("GatherColumn"),
            axis=1,
        )
        fun_output = scope.get_unique_variable_name("fun_output")
        if op.fun in [np.square, np.cbrt, TExtras.cube]:
            exponent = {
                np.square: 2.0,
                np.cbrt: 1.0 / 3.0,
                TExtras.cube: 3.0,
            }.get(op.fun)
            exponent_name = scope.get_unique_variable_name("exponent")
            container.add_initializer(exponent_name, initializer_type, [], [exponent])
            container.add_node(
                "Pow",
                inputs=[col_output, exponent_name],
                outputs=[fun_output],
                name=scope.get_unique_operator_name("Pow"),
            )
        else:
            container.add_node(
                onnx_op, inputs=[col_output], outputs=[fun_output], name=scope.get_unique_operator_name("Fun")
            )

        cleaned_output = add_node_to_replace_nan_and_inf(
            scope=scope, container=container, input=fun_output, initializer_type=initializer_type
        )
        new_log_outputs.append(cleaned_output)

    if selected_cols:
        container.add_node(
            "Concat",
            inputs=[casted_input] + new_log_outputs,
            outputs=[outputs_tensor.full_name],
            name=scope.get_unique_operator_name("ConcatTA"),
            axis=1,
        )
    else:
        apply_identity(scope, [casted_input], outputs_tensor.full_name, container)


transformer = TA1
update_registered_converter(
    model=transformer,
    alias=f"AutoAI{transformer.__name__}",
    shape_fct=ta1_shape_calculator,
    convert_fct=ta1_transformer_converter,
)
