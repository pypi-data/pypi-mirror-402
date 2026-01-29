################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from snapml import BatchedTreeEnsembleRegressor


def bte_regressor_shape_calculator(operator: Operator) -> None:
    pass


# This converter covers only the portion of BatchedTreeEnsembleRegressor.predict()
# that executes when base_ensemble_fitted_ is present
def bte_regressor_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    input_tensor = operator.inputs[0]
    op: BatchedTreeEnsembleRegressor = operator.raw_operator
    base_ensemble = getattr(op, "base_ensemble_fitted_", None)

    sub = OnnxSubEstimator(
        base_ensemble, input_tensor, op_version=container.target_opset, output_names=[operator.outputs[0].full_name]
    )
    sub.add_to(scope, container)


update_registered_converter(
    BatchedTreeEnsembleRegressor,
    "AutoLibsBatchedTreeEnsembleRegressor",
    bte_regressor_shape_calculator,
    bte_regressor_converter,
)
