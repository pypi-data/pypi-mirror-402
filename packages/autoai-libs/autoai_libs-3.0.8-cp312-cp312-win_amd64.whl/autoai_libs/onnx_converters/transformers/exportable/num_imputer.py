################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
from onnx import onnx_pb as onnx_proto
from onnxconverter_common import apply_identity
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.algebra.onnx_ops import OnnxCast
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import DoubleTensorType
from skl2onnx.operator_converters.common import concatenate_variables
from sklearn.impute import SimpleImputer

from autoai_libs.transformers.exportable import NumImputer


def num_imputer_shape_calculator(operator: Operator) -> None:
    op = operator.raw_operator
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    dims = [operator.inputs[0].get_first_dimension(), op_features]
    if op.activate_flag:
        operator.outputs[0].type = DoubleTensorType(dims)
    else:
        operator.outputs[0].type = operator.inputs[0].type.__class__(dims)


def num_imputer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    op: NumImputer = operator.raw_operator
    opv = container.target_opset
    out = operator.outputs

    if op.activate_flag:
        # The order of casting is reversed because the Imputer converter cannot handle float64. This may lead to different results.
        imputer = OnnxSubEstimator(op.imputer, *operator.inputs, op_version=opv)
        if op.strategy != "constant" and op.bad_columns:
            simple = SimpleImputer(missing_values=float("nan"), strategy="constant", fill_value=0)
            setattr(simple, "statistics_", np.zeros(op.imputer.statistics_.shape))
            setattr(simple, "indicator_", op.imputer.indicator_)
            setattr(simple, "n_features_in_", op.imputer.n_features_in_)
            imputer = OnnxSubEstimator(simple, imputer, op_version=opv)

        X_float64 = OnnxCast(imputer, to=onnx_proto.TensorProto.DOUBLE, op_version=opv, output_names=out)
        X_float64.add_to(scope, container)
    else:
        feature_name = concatenate_variables(scope, operator.inputs, container)
        apply_identity(scope, feature_name, operator.output_full_names, container)


transformer = NumImputer
update_registered_converter(
    transformer, f"AutoAI{transformer.__name__}", num_imputer_shape_calculator, num_imputer_converter
)
