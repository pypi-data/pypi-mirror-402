################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
"""
Custom Converters for exportables.py

This module registers converters to transform the components in exportables.py into ONNX format.
It includes custom converters, shape calculators, and parsers to ensure compatibility
with ONNX export requirements.

Note:
Any converter with the `activate/use` flag won't work with arrays containing mixed types,
as ONNX can only define a single type for an output. As a result, every output will be cast
to the common type.
"""
from onnxconverter_common import apply_identity
from skl2onnx import get_model_alias
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.common.data_types import BooleanTensorType, StringTensorType

from autoai_libs.cognito.transforms.transform_utils import TNoOp
from autoai_libs.transformers.exportable import AllPassPreprocessingTransformer

non_numeric_types = (StringTensorType, BooleanTensorType)


def is_all_non_numeric(operator_list: Operator.OperatorList) -> bool:
    return all(type(inpt.type) in non_numeric_types for inpt in operator_list)


def is_all_numeric(operator_list: Operator.OperatorList) -> bool:
    return all(type(inpt.type) not in non_numeric_types for inpt in operator_list)


def identity_shape_calculator(operator: Operator):
    for i, inpt in enumerate(operator.inputs):
        operator.outputs[i].type = operator.inputs[i].type


def identity_converter(scope: Scope, operator: Operator, container: ModelComponentContainer):
    for i, inpt in enumerate(operator.inputs):
        apply_identity(scope, [inpt.full_name], [operator.outputs[i].full_name], container)


def identity_parser(
    scope: Scope, model: AllPassPreprocessingTransformer | TNoOp, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)

    # inputs
    this_operator.inputs.extend(inputs)

    # outputs
    for i, inpt in enumerate(this_operator.inputs):
        this_operator.outputs.append(
            scope.declare_local_variable(f"OUT_{inpt.full_name}", type=inpt.type.__class__(shape=inpt.type.shape))
        )
    # ends
    return list(this_operator.outputs)
