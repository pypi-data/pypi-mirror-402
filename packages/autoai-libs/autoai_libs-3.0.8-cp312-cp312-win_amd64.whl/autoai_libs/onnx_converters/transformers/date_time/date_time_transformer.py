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
from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.common.data_types import DoubleTensorType
from skl2onnx.proto import onnx_proto

from autoai_libs.transformers.date_time.date_time_transformer import DateTransformer
from autoai_libs.transformers.date_time.date_time_utils import apply_date_aggregations


def date_transformer_shape_calculator(operator: Operator) -> None:
    pass


def date_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    inputs = operator.inputs
    outputs = operator.outputs
    op: DateTransformer = operator.raw_operator

    if op.activate_flag:
        date_index_correction = 0
        date_inputs = []
        for j, inpt in enumerate(inputs):
            if j in op.date_column_indices:
                if not op.delete_source_columns:
                    apply_identity(scope, [inpt.full_name], [outputs[j].full_name], container)
                else:
                    date_index_correction += 1
                date_inputs.append(inpt)
            else:
                apply_identity(scope, [inpt.full_name], [outputs[j - date_index_correction].full_name], container)

        if date_inputs:
            options = np.array(op.options)
            options_name = scope.get_unique_variable_name("options")
            container.add_initializer(options_name, onnx_proto.TensorProto.STRING, options.shape, options)

            concat_result_name = scope.get_unique_variable_name("concat_date")
            date_inputs_names = [inpt.full_name for inpt in date_inputs]
            apply_concat(scope, date_inputs_names, concat_result_name, container, axis=1)

            date_transformed = scope.get_unique_variable_name("date_transformed")

            container.add_node(
                "ApplyDateAggregations",
                inputs=[concat_result_name, options_name],
                outputs=[date_transformed],
                op_domain="ai.onnx.contrib",
                op_version=1,
                one_timestamp_type_flag="True",
                float32_processing_flag="True" if op.float32_processing_flag else "",
            )
            _, column_headers_list = apply_date_aggregations(
                X=None,
                date_column_indices=list(range(len(date_inputs))),
                options=op.options,
                delete_source_columns=True,
                column_headers_list=(
                    [op.column_headers_list[i] for i in op.date_column_indices]
                    if op.column_headers_list
                    else date_inputs_names
                ),
                float32_processing_flag=op.float32_processing_flag,
            )

            tmp_date_outputs = [scope.get_unique_variable_name(f"temp_{header}") for header in column_headers_list]
            container.add_node("Split", [date_transformed], tmp_date_outputs, axis=1)

            date_output_index = len(inputs)
            if op.delete_source_columns:
                date_output_index -= len(op.date_column_indices)
            elif not op.date_column_indices:
                date_output_index -= 1

            for output in outputs[date_output_index:]:
                index = column_headers_list.index(output.raw_name)
                apply_identity(scope, [tmp_date_outputs[index]], [output.full_name], container)
    else:
        for i, inpt in enumerate(operator.inputs):
            apply_identity(scope, [inpt.full_name], [outputs[i].full_name], container)


def date_transformer_parser(
    scope: Scope, model: DateTransformer, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)
    # inputs
    this_operator.inputs.extend(inputs)
    op: DateTransformer = this_operator.raw_operator

    # outputs
    if op.activate_flag:
        filtered_inputs = [
            inpt for i, inpt in enumerate(inputs) if not (i in op.date_column_indices and op.delete_source_columns)
        ]

        _, l_column_headers_list = apply_date_aggregations(
            X=None,
            date_column_indices=op.date_column_indices,
            options=op.options,
            delete_source_columns=op.delete_source_columns,
            column_headers_list=(op.column_headers_list if op.column_headers_list else this_operator.input_full_names),
            float32_processing_flag=op.float32_processing_flag,
        )
        selected_indices = [i for i in range(len(l_column_headers_list))]

        # Column selector part
        if op.column_headers_list and len(l_column_headers_list) != len(op.column_headers_list):
            selected_indices = op.column_selector.columns_indices_list
            new_column_headers_list = [l_column_headers_list[i] for i in selected_indices]

            if len(new_column_headers_list) != len(op.column_headers_list):
                op.new_column_headers_list = new_column_headers_list
                op.columns_added_flag = True
            else:
                op.new_column_headers_list = op.column_headers_list
                op.columns_added_flag = False

        else:
            op.new_column_headers_list = l_column_headers_list if l_column_headers_list else op.column_headers_list
            op.columns_added_flag = False

        end_of_basic_columns = len(this_operator.inputs)
        if op.delete_source_columns:
            end_of_basic_columns -= len(op.date_column_indices)

        for i, inpt in enumerate(filtered_inputs):
            if i in selected_indices:
                this_operator.outputs.append(scope.declare_local_variable(inpt.full_name, type=inpt.type))
        for i, header in enumerate(l_column_headers_list[end_of_basic_columns:], end_of_basic_columns):
            if i in selected_indices:
                this_operator.outputs.append(
                    scope.declare_local_variable(header, type=DoubleTensorType(shape=[None, 1]))
                )

    else:
        for i, inpt in enumerate(this_operator.inputs):
            this_operator.outputs.append(scope.declare_local_variable(inpt.full_name, type=inpt.type))

    # ends
    return list(this_operator.outputs)


transformer = DateTransformer
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    date_transformer_shape_calculator,
    date_transformer_converter,
    parser=date_transformer_parser,
)
