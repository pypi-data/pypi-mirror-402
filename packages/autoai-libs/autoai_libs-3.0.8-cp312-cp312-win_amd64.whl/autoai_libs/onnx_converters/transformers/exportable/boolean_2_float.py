################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import onnx
from onnxconverter_common import apply_cast, apply_concat, apply_identity
from skl2onnx import update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import BooleanTensorType, DoubleTensorType

from autoai_libs.transformers.exportable import boolean2float


def boolean2float_shape_calculator(operator: Operator) -> None:
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    dims = [operator.inputs[0].get_first_dimension(), op_features]
    if operator.raw_operator.activate_flag and all(
        isinstance(inpt.type, BooleanTensorType) for inpt in operator.inputs
    ):
        operator.outputs[0].type = DoubleTensorType(dims)
    else:
        operator.outputs[0].type = operator.inputs[0].type.__class__(dims)


def boolean2float_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    op: boolean2float = operator.raw_operator

    concat_result_name = scope.get_unique_variable_name("concat")
    apply_concat(scope, operator.input_full_names, "concat", container, axis=1)

    if op.activate_flag and all(isinstance(inpt.type, BooleanTensorType) for inpt in operator.inputs):
        apply_cast(scope, concat_result_name, operator.output_full_names, container, to=onnx.TensorProto.DOUBLE)
    else:
        apply_identity(scope, concat_result_name, operator.output_full_names, container)


transformer = boolean2float
update_registered_converter(
    transformer, f"AutoAI{transformer.__name__}", boolean2float_shape_calculator, boolean2float_converter
)
