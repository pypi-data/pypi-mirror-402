################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

from onnxconverter_common import apply_gather, apply_identity
from onnxmltools.convert.xgboost.operator_converters.XGBoost import convert_xgboost
from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.common.data_types import FloatTensorType, Int64TensorType, guess_data_type, guess_proto_type

from autoai_libs.estimators.xgboost import XGBClassifier as XGBClassifier_autoai_libs


def autoai_libs_xgb_converter_shape_calculator(operator: Operator) -> None:
    outputs = operator.outputs  # outputs in ONNX graph

    classes = operator.raw_operator._le_transformer.classes_
    num_observations = operator.inputs[0].type.shape[0]
    num_classes = len(classes)

    outputs[0].type = outputs[0].type.__class__([num_observations])  # labels
    outputs[1].type = outputs[1].type.__class__([num_observations, num_classes])  # probabilities


def autoai_libs_xgb_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    op: XGBClassifier_autoai_libs = operator.raw_operator

    # Save original output variable names
    original_outputs = operator.outputs

    # Re-assign temporary outputs to intercept them
    operator.outputs = [
        scope.declare_local_variable(
            "intermediate_label", Int64TensorType(original_outputs[0].type.shape)
        ),  # original_outputs[0].type),
        (
            scope.declare_local_variable("intermediate_proba", original_outputs[1].type)
            if len(original_outputs) > 1
            else None
        ),
    ]

    # Call original XGBoost converter
    convert_xgboost(scope, operator, container)
    inputs = operator.outputs
    operator.outputs = original_outputs

    classes = op._le_transformer.classes_
    classes_name = scope.get_unique_variable_name("classes")
    new_output_type = guess_data_type(classes)[0][1]

    container.add_initializer(classes_name, guess_proto_type(new_output_type), classes.shape, classes)

    apply_gather(scope, [classes_name, inputs[0].full_name], operator.outputs[0].full_name, container)  # decoded labels

    apply_identity(scope, inputs[1].full_name, operator.outputs[1].full_name, container)  # probabilities


def autoai_libs_xgb_parser(
    scope: Scope, model: XGBClassifier_autoai_libs, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)
    op: XGBClassifier_autoai_libs = this_operator.raw_operator

    this_operator.inputs.append(inputs[0])

    classes = op._le_transformer.classes_
    label_type = guess_data_type(classes)[0][1].__class__

    val_label = scope.declare_local_variable("val_label", label_type())
    val_prob = scope.declare_local_variable("val_prob", FloatTensorType())
    this_operator.outputs.append(val_label)
    this_operator.outputs.append(val_prob)

    return list(this_operator.outputs)


update_registered_converter(
    XGBClassifier_autoai_libs,
    "AutoLibsXGBClassifier",
    autoai_libs_xgb_converter_shape_calculator,
    autoai_libs_xgb_converter,
    parser=autoai_libs_xgb_parser,
    options={"nocl": [True, False], "zipmap": [True, False, "columns"]},
)
