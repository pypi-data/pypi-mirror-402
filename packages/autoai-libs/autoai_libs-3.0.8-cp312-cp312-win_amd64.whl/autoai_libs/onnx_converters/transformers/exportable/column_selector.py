################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from onnxconverter_common import apply_gather, apply_identity
from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.proto import onnx_proto

from autoai_libs.transformers.exportable import ColumnSelector

PREFIX = "SELECTED_"


def handle_multi_feature_single_input(op: ColumnSelector, operator: Operator):
    return (
        op.activate_flag
        and op.columns_indices_list
        and len(operator.inputs) == 1
        and operator.inputs[0].type.shape[1] != 1
    )


def column_selector_transformer_shape_calculator(operator: Operator):
    op: ColumnSelector = operator.raw_operator
    if handle_multi_feature_single_input(op, operator):
        operator.outputs[0].type = operator.inputs[0].type.__class__((None, len(op.columns_indices_list)))


def column_selector_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer):
    op: ColumnSelector = operator.raw_operator

    if handle_multi_feature_single_input(op, operator):
        columns_indices = scope.get_unique_variable_name(f"columns_indices")
        container.add_initializer(
            columns_indices, onnx_proto.TensorProto.INT64, [len(op.columns_indices_list)], op.columns_indices_list
        )
        apply_gather(
            scope,
            [operator.inputs[0].full_name, columns_indices],
            operator.output_full_names,
            axis=1,
            container=container,
        )
    else:
        inputs = {PREFIX + i.raw_name: i for i in operator.inputs}

        for output in operator.outputs:
            if inpt := inputs.get(output.raw_name):
                apply_identity(scope, [inpt.full_name], [output.full_name], container)


def column_selector_transformer_parser(
    scope: Scope, model: ColumnSelector, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)

    # inputs
    this_operator.inputs.extend(inputs)
    op: ColumnSelector = this_operator.raw_operator

    columns_selected_flag = False

    # outputs
    if op.activate_flag:
        columns_indices_list = op.columns_indices_list
        if columns_indices_list is not None and isinstance(columns_indices_list, list) and columns_indices_list:
            columns_selected_flag = True
            x_numelts = len(this_operator.inputs)

            if x_numelts == 1:
                columns_selected_flag = False
            else:
                for index in columns_indices_list:
                    if not (-x_numelts <= index < x_numelts):
                        columns_selected_flag = False
                        break

    if columns_selected_flag:
        for i in op.columns_indices_list:
            inpt = this_operator.inputs[i]
            this_operator.outputs.append(
                scope.declare_local_variable(PREFIX + inpt.raw_name, type=inpt.type.__class__(shape=inpt.type.shape))
            )
    else:
        for inpt in this_operator.inputs:
            this_operator.outputs.append(
                scope.declare_local_variable(PREFIX + inpt.raw_name, type=inpt.type.__class__(shape=inpt.type.shape))
            )

    # ends
    return list(this_operator.outputs)


transformer = ColumnSelector
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    column_selector_transformer_shape_calculator,
    column_selector_transformer_converter,
    parser=column_selector_transformer_parser,
)
