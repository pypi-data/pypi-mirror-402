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

from autoai_libs.transformers.exportable import NumpyPermuteArray


def numpy_permute_array_transformer_shape_calculator(operator: Operator) -> None:
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    dims = [operator.inputs[0].get_first_dimension(), op_features]
    operator.outputs[0].type = operator.inputs[0].type.__class__(dims)


def numpy_permute_array_transformer_converter(
    scope: Scope, operator: Operator, container: ModelComponentContainer
) -> None:
    op: NumpyPermuteArray = operator.raw_operator

    feature_name = concatenate_variables(scope, operator.inputs, container, main_type=FloatTensorType)
    if permutation_indices := op.permutation_indices:
        permutation_indices_name = scope.get_unique_variable_name(f"permutation_indices")
        container.add_initializer(
            permutation_indices_name,
            onnx_proto.TensorProto.INT64,
            np.array(permutation_indices).shape,
            permutation_indices,
        )

        container.add_node(
            "PermuteNumericArrays",
            inputs=[feature_name, permutation_indices_name],
            outputs=operator.output_full_names,
            op_domain="ai.onnx.contrib",
            op_version=1,
            axis=op.axis,
        )
    else:
        apply_identity(scope, feature_name, operator.output_full_names, container)


transformer = NumpyPermuteArray
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    numpy_permute_array_transformer_shape_calculator,
    numpy_permute_array_transformer_converter,
)
