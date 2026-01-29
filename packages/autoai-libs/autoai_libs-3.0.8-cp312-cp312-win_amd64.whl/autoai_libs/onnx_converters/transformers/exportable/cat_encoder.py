################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
from onnxconverter_common import apply_concat, apply_identity
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import FloatTensorType, Int64TensorType
from skl2onnx.operator_converters.common import concatenate_variables

from autoai_libs.onnx_converters.utils import is_all_non_numeric, is_all_numeric
from autoai_libs.transformers.exportable import CatEncoder


def cat_encoder_shape_calculator(operator: Operator) -> None:
    op: CatEncoder = operator.raw_operator
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    dims = [operator.inputs[0].get_first_dimension(), op_features]
    if op.activate_flag:
        if np.issubdtype(op.dtype, np.floating):
            operator.outputs[0].type = FloatTensorType(dims)
        else:
            operator.outputs[0].type = Int64TensorType(dims)
    else:
        operator.outputs[0].type = operator.inputs[0].type.__class__(dims)


def cat_encoder_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    op: CatEncoder = operator.raw_operator

    if op.activate_flag:
        scaler = OnnxSubEstimator(
            op.encoder, *operator.inputs, op_version=container.target_opset, output_names=operator.outputs
        )
        scaler.add_to(scope, container)
    else:
        if is_all_non_numeric(operator.inputs):
            apply_concat(scope, operator.input_full_names, operator.output_full_names, container, axis=1)
        elif is_all_numeric(operator.inputs):
            feature_name = concatenate_variables(scope, operator.inputs, container)
            apply_identity(scope, feature_name, operator.output_full_names, container)
        else:
            raise RuntimeError("Numerical tensor(s) and string tensor(s) cannot be concatenated.")


transformer = CatEncoder
update_registered_converter(
    transformer, f"AutoAI{transformer.__name__}", cat_encoder_shape_calculator, cat_encoder_converter
)
