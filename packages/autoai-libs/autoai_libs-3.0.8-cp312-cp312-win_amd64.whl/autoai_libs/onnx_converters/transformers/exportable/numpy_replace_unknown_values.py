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
from skl2onnx.common.data_types import FloatTensorType
from skl2onnx.operator_converters.common import concatenate_variables
from skl2onnx.proto import onnx_proto

from autoai_libs.transformers.exportable import NumpyReplaceUnknownValues


def numpy_replace_unknown_values_transformer_shape_calculator(operator: Operator) -> None:
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    dims = [operator.inputs[0].get_first_dimension(), op_features]
    operator.outputs[0].type = FloatTensorType(dims)


def numpy_replace_unknown_values_transformer_converter(
    scope: Scope, operator: Operator, container: ModelComponentContainer
) -> None:
    op: NumpyReplaceUnknownValues = operator.raw_operator

    if isinstance(op.filling_values, int):
        op.filling_values = float(op.filling_values)

    feature_name = concatenate_variables(scope, operator.inputs, container, main_type=FloatTensorType)
    if known_values_list := op.known_values_list:
        if isinstance(known_values_list[0], list):
            # Padding list with the last element
            max_len = max(map(len, known_values_list))
            known_values_list = [lst + [lst[-1]] * (max_len - len(lst)) for lst in known_values_list]

        known_values = np.array(known_values_list)
        known_values_list_name = scope.get_unique_variable_name(f"known_values_list")
        container.add_initializer(
            known_values_list_name, onnx_proto.TensorProto.FLOAT, known_values.shape, known_values
        )

        container.add_node(
            "ReplaceFloatValues",
            inputs=[feature_name, known_values_list_name],
            outputs=operator.output_full_names,
            op_domain="ai.onnx.contrib",
            op_version=1,
            invert_flag="True",
            filling_values=op.filling_values,
        )
    else:
        apply_identity(scope, feature_name, operator.output_full_names, container)


transformer = NumpyReplaceUnknownValues
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    numpy_replace_unknown_values_transformer_shape_calculator,
    numpy_replace_unknown_values_transformer_converter,
)
