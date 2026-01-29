################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.algebra.onnx_ops import OnnxConcat, OnnxGather
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import DoubleTensorType
from skl2onnx.operator_converters.common import concatenate_variables
from skl2onnx.proto import onnx_proto

from autoai_libs.cognito.transforms.transform_utils import NSFA
from autoai_libs.utils.exportable_utils import WML_raise_exception

inpt_type = DoubleTensorType


def nsfa_shape_calculator(operator: Operator) -> None:
    op: NSFA = operator.raw_operator
    if op.significant_columns is not None:
        if hasattr(op.analyzer, "explained_variance_ratio_"):
            best_components = [
                i for i in range(op.analyzer.n_components_) if np.sum(op.analyzer.explained_variance_ratio_[:i]) < 0.9
            ]
        else:
            best_components = [0]
        col_num = len(op.significant_columns) + len(best_components)
        operator.outputs[0].type = inpt_type([operator.inputs[0].get_first_dimension(), col_num])


def nsfa_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    opv = container.target_opset
    op: NSFA = operator.raw_operator

    feature_name = concatenate_variables(scope, operator.inputs, container, main_type=inpt_type)

    if op.significant_columns is not None and op.nonsignificant_columns is not None:
        if hasattr(op.analyzer, "explained_variance_ratio_"):
            best_components = [
                i for i in range(op.analyzer.n_components_) if np.sum(op.analyzer.explained_variance_ratio_[:i]) < 0.9
            ]
        else:
            best_components = [0]

        non_significant_columns_idxs = scope.get_unique_variable_name("non_significant_columns")
        container.add_initializer(
            non_significant_columns_idxs,
            onnx_proto.TensorProto.INT64,
            [len(op.nonsignificant_columns)],
            op.nonsignificant_columns,
        )

        gather_output = scope.declare_local_variable(
            "gathered_columns", type=inpt_type(shape=(None, len(op.nonsignificant_columns)))
        )
        non_significant_columns_output = OnnxGather(
            feature_name, non_significant_columns_idxs, axis=1, op_version=opv, output_names=[gather_output.full_name]
        )
        non_significant_columns_output.add_to(scope, container)

        analyzer = OnnxSubEstimator(op.analyzer, gather_output.full_name, op_version=opv)

        best_components_idxs = scope.get_unique_variable_name("best_components")
        container.add_initializer(
            best_components_idxs, onnx_proto.TensorProto.INT64, [len(best_components)], best_components
        )

        best_components_output = OnnxGather(analyzer, best_components_idxs, axis=1, op_version=opv)

        significant_columns_idxs = scope.get_unique_variable_name("significant_columns")
        container.add_initializer(
            significant_columns_idxs,
            onnx_proto.TensorProto.INT64,
            [len(op.significant_columns)],
            op.significant_columns,
        )

        significant_columns_output = OnnxGather(feature_name, significant_columns_idxs, axis=1, op_version=opv)

        output = OnnxConcat(
            significant_columns_output, best_components_output, axis=1, op_version=opv, output_names=operator.outputs
        )
        output.add_to(scope, container)
    else:
        WML_raise_exception(
            error_message="Missing column indices - transformer needs to be fitted before transformation."
        )


transformer = NSFA
update_registered_converter(
    model=transformer,
    alias=f"AutoAI{transformer.__name__}",
    shape_fct=nsfa_shape_calculator,
    convert_fct=nsfa_transformer_converter,
)
