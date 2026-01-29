################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from onnxconverter_common import apply_cast, apply_concat, apply_identity, apply_reshape
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import FloatTensorType, guess_proto_type
from skl2onnx.operator_converters.common import concatenate_variables
from sklearn.decomposition import PCA

from autoai_libs.cognito.transforms.transform_extras import ClusterDBSCAN, IsolationForestAnomaly
from autoai_libs.cognito.transforms.transform_utils import TAM
from autoai_libs.onnx_converters.cognito.utils import add_node_to_replace_nan_and_inf


def tam_shape_calculator(operator: Operator) -> None:
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    transformer = operator.raw_operator.trans_class_obj_
    if isinstance(transformer, PCA):
        dims = [operator.inputs[0].get_first_dimension(), transformer.components_.shape[1] + op_features]
    elif isinstance(transformer, (ClusterDBSCAN, IsolationForestAnomaly)):
        dims = [operator.inputs[0].get_first_dimension(), 1 + op_features]
    else:
        dims = [operator.inputs[0].get_first_dimension(), op_features * 2]

    if isinstance(transformer, IsolationForestAnomaly):
        operator.outputs[0].type = FloatTensorType(dims)
    else:
        operator.outputs[0].type = operator.inputs[0].type.__class__(dims)


def tam_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    op: TAM = operator.raw_operator
    opv = container.target_opset
    outputs_tensor = operator.outputs[0]

    transformer = op.trans_class_obj_
    output_type = outputs_tensor.type.__class__

    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    float64_input = scope.declare_local_variable("float64_input", type=output_type(shape=[None, op_features]))
    concatenated = concatenate_variables(scope, operator.inputs, container, main_type=output_type)
    apply_identity(scope, concatenated, float64_input.full_name, container)

    onnx_transformer = scope.get_unique_variable_name("onnx_transformer")

    if isinstance(transformer, ClusterDBSCAN):
        scaler = OnnxSubEstimator(transformer.scaler, float64_input.full_name, op_version=opv)

        knn_proba = scope.get_unique_variable_name("knn_proba")
        knn_label = scope.get_unique_variable_name("knn_label")

        knn = OnnxSubEstimator(transformer.knn, scaler, op_version=opv, output_names=[knn_label, knn_proba])
        knn.add_to(scope, container)

        casted_label = scope.get_unique_variable_name("casted_label")
        apply_cast(scope, knn_label, casted_label, container, to=guess_proto_type(output_type()))

        apply_reshape(scope, casted_label, onnx_transformer, container, desired_shape=[-1, 1])

    elif isinstance(transformer, IsolationForestAnomaly):
        isoforest_proba = scope.get_unique_variable_name("isoforest_proba")
        isoforest_label = scope.get_unique_variable_name("isoforest_label")
        isoforest = OnnxSubEstimator(
            transformer.isoforest,
            float64_input.full_name,
            op_version=opv,
            output_names=[isoforest_label, isoforest_proba],
        )
        isoforest.add_to(scope, container)

        casted_label = scope.get_unique_variable_name("casted_label")
        apply_cast(scope, isoforest_label, casted_label, container, to=guess_proto_type(output_type()))

        apply_reshape(scope, casted_label, onnx_transformer, container, desired_shape=[-1, 1])
    else:
        sub_estimator = OnnxSubEstimator(
            transformer, float64_input.full_name, op_version=opv, output_names=[onnx_transformer]
        )
        sub_estimator.add_to(scope, container)

    cleaned_output = add_node_to_replace_nan_and_inf(
        scope=scope, container=container, input=onnx_transformer, initializer_type=guess_proto_type(output_type())
    )
    apply_concat(scope, [float64_input.full_name, cleaned_output], operator.output_full_names, container, axis=1)


transformer = TAM
update_registered_converter(
    model=transformer,
    alias=f"AutoAI{transformer.__name__}",
    shape_fct=tam_shape_calculator,
    convert_fct=tam_transformer_converter,
)
