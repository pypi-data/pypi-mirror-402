################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
import onnx
from onnxconverter_common import apply_cast
from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.common.data_types import FloatTensorType
from skl2onnx.proto import onnx_proto

from autoai_libs.transformers.exportable import NumpyReplaceMissingValues


def numpy_replace_missing_values_transformer_shape_calculator(operator: Operator) -> None:
    pass


def numpy_replace_missing_values_transformer_converter(
    scope: Scope, operator: Operator, container: ModelComponentContainer
) -> None:
    inputs = operator.inputs
    outputs = operator.outputs
    op: NumpyReplaceMissingValues = operator.raw_operator

    for inpt, outpt in zip(inputs, outputs):
        if missing_values := op.missing_values:
            if not isinstance(missing_values, list):
                missing_values = [missing_values]
            missing_values_array = np.array(missing_values)
            missing_values_name = scope.get_unique_variable_name("missing_values")
            if missing_values_array.dtype.type == np.str_:
                apply_cast(scope, inpt.full_name, outpt.full_name, container, to=onnx.TensorProto.FLOAT)
            else:
                cast_name = scope.get_unique_variable_name("cast")
                apply_cast(scope, inpt.full_name, cast_name, container, to=onnx.TensorProto.FLOAT)
                container.add_initializer(
                    missing_values_name,
                    onnx_proto.TensorProto.FLOAT,
                    np.array(missing_values, dtype=np.float32).shape,
                    missing_values,
                )
                container.add_node(
                    op_type="ReplaceFloatValues",
                    inputs=[cast_name, missing_values_name],
                    outputs=[outpt.full_name],
                    op_domain="ai.onnx.contrib",
                    op_version=1,
                    invert_flag="",
                    filling_values=op.filling_values,
                )
        else:
            apply_cast(scope, inpt.full_name, outpt.full_name, container, to=onnx.TensorProto.FLOAT)


def numpy_replace_missing_values_parser(
    scope: Scope, model: NumpyReplaceMissingValues, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)
    this_operator.inputs.extend(inputs)

    for inpt in inputs:
        this_operator.outputs.append(
            scope.declare_local_variable(f"OUT_{inpt.full_name}", FloatTensorType(shape=inpt.type.shape))
        )
    return list(this_operator.outputs)


transformer = NumpyReplaceMissingValues
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    numpy_replace_missing_values_transformer_shape_calculator,
    numpy_replace_missing_values_transformer_converter,
    parser=numpy_replace_missing_values_parser,
)
