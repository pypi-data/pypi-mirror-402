################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Scope
from skl2onnx.proto import onnx_proto


def add_node_to_replace_nan_and_inf(
    scope: Scope, container: ModelComponentContainer, input: str, initializer_type: int = onnx_proto.TensorProto.FLOAT
) -> str:
    """
    Adds ONNX nodes to replace NaN and Inf values in the input tensor with zero.

    Parameters:
        scope: Scope
            The scope object used to manage variable names in the ONNX graph.
        container: ModelComponentContainer
            The container that holds the model components being built.
        input: str
            The name of the input tensor to process.
        initializer_type: int
            The ONNX tensor data type (e.g., onnx_proto.TensorProto.FLOAT).

    Returns:
        str
            The name of the output tensor where NaN and Inf values are replaced with zero.
    """
    is_nan = scope.get_unique_variable_name("is_nan")
    is_inf = scope.get_unique_variable_name("is_inf")
    mask = scope.get_unique_variable_name("bad_mask")
    cleaned_output = scope.get_unique_variable_name("cleaned_col")
    zero_name = scope.get_unique_variable_name("zero_scalar")

    container.add_initializer(zero_name, initializer_type, [1], [0.0])
    container.add_node("IsNaN", [input], [is_nan], name=scope.get_unique_operator_name("IsNaN"))
    container.add_node("IsInf", [input], [is_inf], name=scope.get_unique_operator_name("IsInf"))
    container.add_node("Or", [is_nan, is_inf], [mask], name=scope.get_unique_operator_name("OrMask"))
    container.add_node(
        "Where",
        inputs=[mask, zero_name, input],
        outputs=[cleaned_output],
        name=scope.get_unique_operator_name("ReplaceNanInf"),
    )
    return cleaned_output
