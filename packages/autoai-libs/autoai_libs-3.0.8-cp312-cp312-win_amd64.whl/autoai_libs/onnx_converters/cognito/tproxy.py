################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope

from autoai_libs.cognito.transforms.transform_utils import Tproxy


def tproxy_shape_calculator(operator: Operator) -> None:
    pass


def tproxy_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    input_tensor = operator.inputs[0]
    outputs_tensor = operator.outputs[0]
    op = operator.raw_operator

    sub = OnnxSubEstimator(
        op.trobj, input_tensor, op_version=container.target_opset, output_names=[outputs_tensor.full_name]
    )
    sub.add_to(scope, container)


transformer = Tproxy
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    tproxy_shape_calculator,
    tproxy_transformer_converter,
)
