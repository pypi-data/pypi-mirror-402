################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from onnxconverter_common import apply_identity
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.operator_converters.common import concatenate_variables

from autoai_libs.transformers.exportable.opt_standard_scaler import OptStandardScaler


def opt_standard_scaler_shape_calculator(operator: Operator) -> None:
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    dims = [operator.inputs[0].get_first_dimension(), op_features]
    operator.outputs[0].type = operator.inputs[0].type.__class__(dims)


def opt_standard_scaler_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    op: OptStandardScaler = operator.raw_operator

    if op.use_scaler_flag:
        scaler = OnnxSubEstimator(
            op.scaler, *operator.inputs, op_version=container.target_opset, output_names=operator.outputs
        )
        scaler.add_to(scope, container)
    else:
        feature_name = concatenate_variables(scope, operator.inputs, container)
        apply_identity(scope, feature_name, operator.output_full_names, container)


transformer = OptStandardScaler
update_registered_converter(
    transformer, f"AutoAI{transformer.__name__}", opt_standard_scaler_shape_calculator, opt_standard_scaler_converter
)
