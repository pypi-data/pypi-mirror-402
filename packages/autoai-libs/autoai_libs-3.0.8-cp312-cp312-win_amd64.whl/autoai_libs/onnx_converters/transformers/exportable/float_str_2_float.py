################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from onnxconverter_common import apply_identity
from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.common.data_types import FloatTensorType
from skl2onnx.proto import onnx_proto

from autoai_libs.transformers.exportable import FloatStr2Float


def float_str_2_float_shape_calculator(operator: Operator) -> None:
    pass


def float_str_2_float_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    inputs = operator.inputs
    outputs = operator.outputs
    op: FloatStr2Float = operator.raw_operator

    if op.activate_flag:
        missing_values_reference_list_name = None

        for j, inpt in enumerate(inputs):
            dtype = op.dtypes_list[j]

            if dtype == "float_str":
                if missing_values_reference_list_name is None:
                    # Lazily initialize only once
                    missing_values_reference_list = op.missing_values_reference_list
                    missing_values_reference_list_name = scope.get_unique_variable_name("missing_values_reference_list")
                    container.add_initializer(
                        missing_values_reference_list_name,
                        onnx_proto.TensorProto.STRING,
                        [len(missing_values_reference_list)],
                        missing_values_reference_list,
                    )
                container.add_node(
                    "FloatStr2Float",
                    inputs=[inpt.full_name, missing_values_reference_list_name],
                    outputs=[outputs[j].full_name],
                    op_domain="ai.onnx.contrib",
                    op_version=1,
                )
            else:
                apply_identity(scope, [inpt.full_name], [outputs[j].full_name], container)
    else:
        for i, inpt in enumerate(operator.inputs):
            apply_identity(scope, [inpt.full_name], [outputs[i].full_name], container)


def float_str_2_float_parser(
    scope: Scope, model: FloatStr2Float, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)
    # inputs
    this_operator.inputs.extend(inputs)
    op: FloatStr2Float = this_operator.raw_operator

    # outputs
    for i, inpt in enumerate(this_operator.inputs):
        if op.activate_flag and op.dtypes_list[i] == "float_str":
            this_operator.outputs.append(
                scope.declare_local_variable(f"FS_{inpt.full_name}", type=FloatTensorType(shape=inpt.type.shape))
            )
        else:
            this_operator.outputs.append(
                scope.declare_local_variable(f"FS_{inpt.full_name}", type=inpt.type.__class__(shape=inpt.type.shape))
            )
    # ends
    return list(this_operator.outputs)


transformer = FloatStr2Float
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    float_str_2_float_shape_calculator,
    float_str_2_float_converter,
    parser=float_str_2_float_parser,
)
