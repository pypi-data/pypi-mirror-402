################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

from onnxconverter_common import apply_cast
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import DoubleTensorType, FloatTensorType, guess_numpy_type, guess_proto_type
from skl2onnx.proto import onnx_proto
from sklearn.preprocessing import KBinsDiscretizer

from autoai_libs.cognito.transforms.transform_extras import (
    NXOR,
    GroupByMax,
    GroupByMean,
    GroupByMedian,
    GroupByMin,
    GroupByStd,
)
from autoai_libs.cognito.transforms.transform_utils import TGen
from autoai_libs.onnx_converters.cognito.utils import add_node_to_replace_nan_and_inf


def tgen_shape_calculator(operator: Operator) -> None:
    op = operator.raw_operator
    n_cols_to_keep = operator.inputs[0].type.shape[1] + len(op.candidates_)
    dims = [operator.inputs[0].get_first_dimension(), n_cols_to_keep]
    if isinstance(operator.inputs[0].type, FloatTensorType):
        operator.outputs[0].type = FloatTensorType(dims)
    else:
        operator.outputs[0].type = DoubleTensorType(dims)


def tgen_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    inputs = operator.inputs
    outputs = operator.outputs
    target_type = outputs[0].type
    op = operator.raw_operator

    candidates = getattr(op, "candidates_", [])
    transform_objects = getattr(op, "tobjects_", [])
    tgen_fun = getattr(op, "fun", [])

    new_cols_all = []
    original_outputs = []

    for inpt in inputs:
        casted_name = scope.get_unique_variable_name("casted_input")
        apply_cast(scope, inpt.full_name, casted_name, container, to=guess_proto_type(target_type))
        original_outputs.append(casted_name)

    concat_output = scope.get_unique_variable_name("Concat")
    container.add_node(
        "Concat",
        inputs=original_outputs,
        outputs=[concat_output],
        axis=1,
    )

    for candidate, tr_obj in zip(candidates, transform_objects):
        gather_column_idx = scope.get_unique_variable_name(f"idx_{candidate}")
        container.add_initializer(gather_column_idx, onnx_proto.TensorProto.INT64, [len(candidate)], list(candidate))
        gather_var = scope.declare_local_variable(f"col_{candidate}", target_type.__class__([None, 1]))
        container.add_node(
            "Gather",
            inputs=[concat_output, gather_column_idx],
            outputs=[gather_var.full_name],
            name=scope.get_unique_operator_name("GatherColumn"),
            axis=1,
        )

        fun_output = scope.get_unique_variable_name(f"fun_output_{candidate}")

        if isinstance(tgen_fun, KBinsDiscretizer):
            kbins_output = scope.get_unique_variable_name(f"kbins_output_{candidate}")
            fun = OnnxSubEstimator(
                tr_obj, gather_var.full_name, op_version=container.target_opset, output_names=[kbins_output]
            )
            fun.add_to(scope, container)

            apply_cast(scope, kbins_output, fun_output, container, to=guess_proto_type(target_type))
        elif tgen_fun in (GroupByMedian, GroupByMax, GroupByMin, GroupByStd, GroupByMean):
            gather_column_1 = scope.get_unique_variable_name(f"idx_1_")
            container.add_initializer(gather_column_1, onnx_proto.TensorProto.INT64, [1], [0])
            gather_var_1 = scope.declare_local_variable(f"col_1_", target_type.__class__([None, 1]))
            container.add_node(
                "Gather",
                inputs=[gather_var.full_name, gather_column_1],
                outputs=[gather_var_1.full_name],
                name=scope.get_unique_operator_name("GatherCol1"),
                axis=1,
            )

            aggs = tr_obj.aggs.reset_index().to_numpy(dtype=guess_numpy_type(target_type))

            aggs_name = scope.get_unique_variable_name("aggs_")
            container.add_initializer(
                aggs_name,
                guess_proto_type(target_type),
                aggs.shape,
                aggs.ravel().tolist(),
            )
            custom_op_output = scope.get_unique_variable_name("co_output_")

            container.add_node(
                op_type=(
                    "CustomTGenGroupByMapping_float32"
                    if isinstance(target_type, FloatTensorType)
                    else "CustomTGenGroupByMapping_float64"
                ),
                inputs=[gather_var_1.full_name, aggs_name],
                outputs=[custom_op_output],
                name=scope.get_unique_operator_name("CustomMapping"),
                op_domain="ai.onnx.contrib",
                op_version=1,
            )
            fun_output = custom_op_output
        elif tgen_fun == NXOR:
            gather_column_1 = scope.get_unique_variable_name(f"idx_1_")
            container.add_initializer(gather_column_1, onnx_proto.TensorProto.INT64, [1], [0])
            gather_var_1 = scope.declare_local_variable(f"col_1_", target_type.__class__([None, 1]))
            container.add_node(
                "Gather",
                inputs=[gather_var.full_name, gather_column_1],
                outputs=[gather_var_1.full_name],
                name=scope.get_unique_operator_name("GatherCol1"),
                axis=1,
            )

            gather_column_2 = scope.get_unique_variable_name(f"idx_2_")
            container.add_initializer(gather_column_2, onnx_proto.TensorProto.INT64, [1], [1])
            gather_var_2 = scope.declare_local_variable(f"col_2_", target_type.__class__([None, 1]))
            container.add_node(
                "Gather",
                inputs=[gather_var.full_name, gather_column_2],
                outputs=[gather_var_2.full_name],
                name=scope.get_unique_operator_name("GatherCol2"),
                axis=1,
            )

            subtraction_name_1 = scope.get_unique_variable_name("sub_1")
            container.add_initializer(subtraction_name_1, guess_proto_type(target_type), [], [tr_obj.m1])
            sub_1_output = scope.get_unique_variable_name(f"sub_1_output_")
            container.add_node(
                "Sub",
                inputs=[gather_var_1.full_name, subtraction_name_1],
                outputs=[sub_1_output],
                name=scope.get_unique_operator_name("Sub_1"),
            )

            subtraction_name_2 = scope.get_unique_variable_name("sub_2")
            container.add_initializer(subtraction_name_2, guess_proto_type(target_type), [], [tr_obj.m2])
            sub_2_output = scope.get_unique_variable_name(f"sub_2_output_")
            container.add_node(
                "Sub",
                inputs=[gather_var_2.full_name, subtraction_name_2],
                outputs=[sub_2_output],
                name=scope.get_unique_operator_name("Sub_2"),
            )

            container.add_node(
                "Mul",
                inputs=[sub_1_output, sub_2_output],
                outputs=[fun_output],
                name=scope.get_unique_operator_name("Mul"),
            )

        cleaned_output = add_node_to_replace_nan_and_inf(
            scope=scope, container=container, input=fun_output, initializer_type=guess_proto_type(target_type)
        )
        new_cols_all.append(cleaned_output)

    container.add_node(
        "Concat",
        inputs=original_outputs + new_cols_all,
        outputs=[outputs[0].full_name],
        name=scope.get_unique_operator_name("ConcatOriginalPlusFun"),
        axis=1,
    )


transformer = TGen
update_registered_converter(
    model=transformer,
    alias=f"AutoAI{transformer.__name__}",
    shape_fct=tgen_shape_calculator,
    convert_fct=tgen_transformer_converter,
)
