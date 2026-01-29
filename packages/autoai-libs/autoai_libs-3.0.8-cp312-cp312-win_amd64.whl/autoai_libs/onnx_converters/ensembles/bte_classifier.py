################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.common.data_types import FloatTensorType, guess_data_type
from snapml import BatchedTreeEnsembleClassifier


def bte_classifier_shape_calculator(operator: Operator) -> None:
    input_shape = operator.inputs[0].type.shape
    op: BatchedTreeEnsembleClassifier = operator.raw_operator
    classes = getattr(op, "classes_", None)
    num_classes = len(classes)

    operator.outputs[0].type = operator.outputs[0].type.__class__([input_shape[0]])
    operator.outputs[1].type = operator.outputs[1].type.__class__([input_shape[0], num_classes])


# This converter covers only the portion of BatchedTreeEnsembleClassifier.predict()
# that executes when base_ensemble_fitted_ is present
def bte_classifier_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    input_tensor = operator.inputs[0]
    op: BatchedTreeEnsembleClassifier = operator.raw_operator
    base_ensemble = getattr(op, "base_ensemble_fitted_", None)

    sub = OnnxSubEstimator(
        base_ensemble,
        input_tensor,
        op_version=container.target_opset,
        output_names=[operator.outputs[0].full_name, operator.outputs[1].full_name],
    )
    sub.add_to(scope, container)


def bte_classifier_parser(
    scope: Scope, model: BatchedTreeEnsembleClassifier, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)
    op: BatchedTreeEnsembleClassifier = this_operator.raw_operator

    this_operator.inputs.append(inputs[0])

    classes = getattr(op, "classes_", None)
    label_type = guess_data_type(classes)[0][1].__class__

    val_label = scope.declare_local_variable("val_label", label_type())
    val_prob = scope.declare_local_variable("val_prob", FloatTensorType())
    this_operator.outputs.append(val_label)
    this_operator.outputs.append(val_prob)

    return list(this_operator.outputs)


update_registered_converter(
    BatchedTreeEnsembleClassifier,
    "AutoLibsBatchedTreeEnsembleClassifier",
    bte_classifier_shape_calculator,
    bte_classifier_converter,
    parser=bte_classifier_parser,
    options={"zipmap": [True, False, "columns"]},
)
