################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import onnx
from onnxconverter_common import apply_cast, apply_identity
from skl2onnx import update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import DoubleTensorType, FloatTensorType
from skl2onnx.operator_converters.common import concatenate_variables

from autoai_libs.transformers.exportable import float32_transform


def float32_transformer_shape_calculator(operator: Operator):
    op_features = sum(map(lambda x: x.type.shape[1] if x.type.shape else 0, operator.inputs))
    dims = [operator.inputs[0].get_first_dimension(), op_features if op_features else None]
    if operator.raw_operator.activate_flag and any(isinstance(inpt.type, DoubleTensorType) for inpt in operator.inputs):
        operator.outputs[0].type = FloatTensorType(dims)
    else:
        operator.outputs[0].type = operator.inputs[0].type.__class__(dims)


def float32_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer):
    op = operator.raw_operator
    feature_name = concatenate_variables(scope, operator.inputs, container)

    if op.activate_flag and any(isinstance(inpt.type, DoubleTensorType) for inpt in operator.inputs):
        apply_cast(scope, feature_name, operator.output_full_names, container, to=onnx.TensorProto.FLOAT)
    else:
        apply_identity(scope, feature_name, operator.output_full_names, container)


transformer = float32_transform
update_registered_converter(
    transformer, f"AutoAI{transformer.__name__}", float32_transformer_shape_calculator, float32_transformer_converter
)
