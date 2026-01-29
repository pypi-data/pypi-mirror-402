################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2022-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import warnings
from typing import TYPE_CHECKING

import lale.docstrings
import lale.operators

import autoai_libs.estimators.xgboost

try:
    from lale.lib.xgboost.xgb_classifier import XGBClassifier as XGBClassifier_lale
except ImportError:
    warnings.warn(
        "autoai_libs.lale.XGBClassifier will be unavailable. To install, run:\npip install 'autoai-libs[xgboost-wrapper]'"
    )

try:
    import xgboost  # type: ignore

    xgboost_installed = True
except ImportError:
    xgboost_installed = False
    if TYPE_CHECKING:
        import xgboost  # type: ignore


class _XGBClassifierImpl:
    _wrapped_model: autoai_libs.estimators.xgboost.XGBClassifier

    @classmethod
    def validate_hyperparams(cls, **hyperparams):
        assert xgboost_installed, """Your Python environment does not have xgboost installed. You can install it with
            pip install xgboost
        or with
            pip install 'lale[full]'"""

    def __init__(self, **hyperparams):
        self.validate_hyperparams(**hyperparams)
        self._hyperparams = hyperparams
        self._wrapped_model = autoai_libs.estimators.xgboost.XGBClassifier(**self._hyperparams)

    def get_params(self, deep=True):
        out = self._wrapped_model.get_params(deep=deep)
        return out

    def fit(self, X, y, **fit_params):
        self._wrapped_model.fit(X, y, **fit_params)
        return self

    def predict(self, X, **predict_params):
        return self._wrapped_model.predict(X, **predict_params)

    def predict_proba(self, X):
        return self._wrapped_model.predict_proba(X)

    def score(self, X, y):
        return self._wrapped_model.score(X, y)


_combined_schemas = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": """`XGBClassifier`_ gradient boosted decision trees.
.. _`XGBClassifier`: https://xgboost.readthedocs.io/en/latest/python/python_api.html#xgboost.XGBClassifier
""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.xgboost.xgb_classifier.html",
    "import_from": "autoai_libs.estimators.xgboost",
    "tags": {"pre": [], "op": ["estimator", "classifier"], "post": []},
    "properties": {
        "hyperparams": XGBClassifier_lale.hyperparam_schema(),
        "input_fit": XGBClassifier_lale.input_schema_fit(),
        "input_predict": XGBClassifier_lale.input_schema_predict(),
        "output_predict": XGBClassifier_lale.output_schema_predict(),
        "input_predict_proba": XGBClassifier_lale.input_schema_predict_proba(),
        "output_predict_proba": XGBClassifier_lale.output_schema_predict_proba(),
    },
}


XGBClassifier: lale.operators.PlannedIndividualOp
XGBClassifier = lale.operators.make_operator(_XGBClassifierImpl, _combined_schemas)
