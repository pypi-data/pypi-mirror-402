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
from skl2onnx.common.data_types import DoubleTensorType
from skl2onnx.proto import onnx_proto

from autoai_libs.transformers.exportable import CompressStrings


def compress_strings_shape_calculator(operator: Operator) -> None:
    pass


def compress_strings_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    inputs = operator.inputs
    outputs = operator.outputs
    op: CompressStrings = operator.raw_operator

    if op.activate_flag:
        for j, inpt in enumerate(inputs):
            dtype = op.dtypes_list[j]

            if dtype == "char_str":
                misslist = op.misslist_list[j]
                misslist_name = scope.get_unique_variable_name(f"misslist_{j}")
                container.add_initializer(misslist_name, onnx_proto.TensorProto.STRING, [len(misslist)], misslist)

                if op.compress_type == "string":
                    container.add_node(
                        "RemoveWhitespaces",
                        inputs=[inpt.full_name, misslist_name],
                        outputs=[outputs[j].full_name],
                        op_domain="ai.onnx.contrib",
                        op_version=1,
                    )
                else:
                    container.add_node(
                        "CompressToHash",
                        inputs=[inpt.full_name, misslist_name],
                        outputs=[outputs[j].full_name],
                        op_domain="ai.onnx.contrib",
                        op_version=1,
                    )
            else:
                apply_identity(scope, [inpt.full_name], [outputs[j].full_name], container)
    else:
        for i, inpt in enumerate(operator.inputs):
            apply_identity(scope, [inpt.full_name], [outputs[i].full_name], container)


def compress_strings_parser(
    scope: Scope, model: CompressStrings, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)
    # inputs
    this_operator.inputs.extend(inputs)
    op: CompressStrings = this_operator.raw_operator

    # outputs
    for i, inpt in enumerate(this_operator.inputs):
        if op.activate_flag and op.dtypes_list[i] == "char_str" and op.compress_type != "string":
            this_operator.outputs.append(
                scope.declare_local_variable(f"CS_{inpt.full_name}", type=DoubleTensorType(shape=inpt.type.shape))
            )
        else:
            this_operator.outputs.append(
                scope.declare_local_variable(f"CS_{inpt.full_name}", type=inpt.type.__class__(shape=inpt.type.shape))
            )
    # ends
    return list(this_operator.outputs)


transformer = CompressStrings
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    compress_strings_shape_calculator,
    compress_strings_converter,
    parser=compress_strings_parser,
)
