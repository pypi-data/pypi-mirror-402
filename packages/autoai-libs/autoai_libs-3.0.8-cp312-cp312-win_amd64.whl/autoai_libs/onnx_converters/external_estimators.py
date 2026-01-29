################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numbers
import warnings

import numpy as np
import packaging.version as pv
from lightgbm import LGBMClassifier, LGBMRegressor
from onnxmltools import __version__ as oml_version
from onnxmltools.convert.lightgbm.operator_converters.LightGbm import convert_lightgbm
from onnxmltools.convert.xgboost.operator_converters.XGBoost import convert_xgboost
from skl2onnx import update_registered_converter
from skl2onnx.common._apply_operation import apply_cast
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import BooleanTensorType, guess_numpy_type
from skl2onnx.common.shape_calculator import (
    calculate_linear_classifier_output_shapes,
    calculate_linear_regressor_output_shapes,
)
from skl2onnx.common.tree_ensemble import (
    add_tree_to_attribute_pairs,
    get_default_tree_classifier_attribute_pairs,
)
from skl2onnx.proto import onnx_proto
from sklearn.ensemble import GradientBoostingClassifier
from xgboost import XGBRegressor


def skl2onnx_convert_lightgbm(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    options = scope.get_options(operator.raw_operator)
    operator.split = options.get("split")
    if operator.split is not None and pv.Version(oml_version) < pv.Version("1.9.2"):
        warnings.warn(
            f"Option split was released in version 1.9.2 but {oml_version} is installed. It will be ignored.",
            stacklevel=0,
        )
    convert_lightgbm(scope, operator, container)


update_registered_converter(
    LGBMRegressor,
    "LightGbmLGBMRegressor",
    calculate_linear_regressor_output_shapes,
    skl2onnx_convert_lightgbm,
    options={"split": None},
)

update_registered_converter(
    LGBMClassifier,
    "LightGbmLGBMClassifier",
    calculate_linear_classifier_output_shapes,
    convert_lightgbm,
    options={"nocl": [True, False], "zipmap": [True, False, "columns"]},
)


update_registered_converter(
    XGBRegressor,
    "XGBoostXGBRegressor",
    calculate_linear_regressor_output_shapes,
    convert_xgboost,
)


def convert_sklearn_gradient_boosting_classifier(
    scope,
    operator,
    container,
    op_type="TreeEnsembleClassifier",
    op_domain="ai.onnx.ml",
    op_version=1,
) -> None:  # pragma: no cover
    dtype = guess_numpy_type(operator.inputs[0].type)
    if dtype != np.float64:
        dtype = np.float32
    op = operator.raw_operator
    if op.loss not in ("deviance", "log_loss", "exponential"):
        raise NotImplementedError(
            f"Loss '{op.loss}' is not supported yet. You "
            "may raise an issue at "
            "https://github.com/onnx/sklearn-onnx/issues."
        )

    attrs = get_default_tree_classifier_attribute_pairs()
    attrs["name"] = scope.get_unique_operator_name(op_type)

    transform = "LOGISTIC" if op.n_classes_ == 2 else "SOFTMAX"
    options = container.get_options(op, dict(raw_scores=False))

    if op.init == "zero":
        loss = getattr(op, "_loss", getattr(op, "loss_", None))
        base_values = np.zeros(getattr(loss, "K", 1))
    elif op.init is None:
        n_features = getattr(op.estimators_[0, 0], "n_features_in_", getattr(op.estimators_[0, 0], "n_features_", None))
        x0 = np.zeros((1, n_features))

        func = getattr(
            op,
            "_raw_predict_init",  # sklearn >= 0.21
            getattr(op, "_init_decision_function", None),  # sklearn >= 0.20 and sklearn < 0.21
        )
        try:
            base_values = func(x0).ravel()
        except:
            raise RuntimeError("scikit-learn < 0.19 is not supported.")
    else:
        raise NotImplementedError(
            "Setting init to an estimator is not supported, you may raise an "
            "issue at https://github.com/onnx/sklearn-onnx/issues."
        )

    if not options.get("raw_scores") and op.loss != "exponential":
        attrs["post_transform"] = transform

    attrs["base_values"] = [float(v) for v in base_values]

    classes = op.classes_
    if all(isinstance(i, (numbers.Real, bool, np.bool_)) for i in classes):
        attrs["classlabels_int64s"] = [int(i) for i in classes]
    elif all(isinstance(i, str) for i in classes):
        attrs["classlabels_strings"] = [str(i) for i in classes]
    else:
        raise ValueError("Labels must be all integer or all strings.")

    tree_weight = op.learning_rate
    n_est = getattr(op, "n_estimators_", getattr(op, "n_estimators", None))
    if op.n_classes_ == 2:
        for tree_id in range(n_est):
            tree = op.estimators_[tree_id][0].tree_
            add_tree_to_attribute_pairs(attrs, True, tree, tree_id, tree_weight, 0, False, True, dtype=dtype)
    else:
        for estimator_idx in range(n_est):
            for class_idx in range(op.n_classes_):
                tree_id = estimator_idx * op.n_classes_ + class_idx
                tree = op.estimators_[estimator_idx][class_idx].tree_
                add_tree_to_attribute_pairs(
                    attrs, True, tree, tree_id, tree_weight, class_idx, False, True, dtype=dtype
                )

    if dtype is not None:
        for k in attrs:
            if k in (
                "nodes_values",
                "class_weights",
                "target_weights",
                "nodes_hitrates",
                "base_values",
            ):
                attrs[k] = np.array(attrs[k], dtype=dtype)

    input_name = operator.input_full_names
    if isinstance(operator.inputs[0].type, BooleanTensorType):
        cast_input_name = scope.get_unique_variable_name("cast_input")

        apply_cast(
            scope,
            input_name,
            cast_input_name,
            container,
            to=onnx_proto.TensorProto.FLOAT,
        )
        input_name = cast_input_name

    proba_output = scope.get_unique_variable_name("proba_output")

    container.add_node(
        op_type,
        input_name,
        [operator.outputs[0].full_name, proba_output],
        op_domain=op_domain,
        op_version=op_version,
        **attrs,
    )

    if op.loss == "exponential":
        scale_name = scope.get_unique_variable_name("scale2")
        scaled_logits = scope.get_unique_variable_name("scaled_logits")

        container.add_initializer(scale_name, onnx_proto.TensorProto.FLOAT, [], [2.0])
        container.add_node(
            "Mul",
            [proba_output, scale_name],
            scaled_logits,
            name=scope.get_unique_operator_name("Mul_Exp2"),
        )

        proba_output = scope.get_unique_variable_name("routput")
        container.add_node(
            "Sigmoid",
            [scaled_logits],
            proba_output,
            name=scope.get_unique_operator_name("Sigmoid_Exp2"),
        )

    container.add_node("Identity", proba_output, operator.outputs[1].full_name)


update_registered_converter(
    GradientBoostingClassifier,
    "SklearnGradientBoostingClassifier",
    calculate_linear_classifier_output_shapes,
    convert_sklearn_gradient_boosting_classifier,
    options={
        "zipmap": [True, False, "columns"],
        "raw_scores": [True, False],
        "output_class_labels": [False, True],
        "nocl": [True, False],
    },
)
