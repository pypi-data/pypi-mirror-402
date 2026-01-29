################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2022-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import logging

from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier as XGBClassifierBase

logger = logging.getLogger("autoai_libs")


class XGBClassifier(XGBClassifierBase):
    """
    This is wrapper for XGBClassifier from xgboost package.
    Starting from version 1.6, pure XGBClassifier removes internal LabelEncoder.
    For reference:
    - xgboost 1.6 release notes: https://github.com/dmlc/xgboost/releases/tag/v1.6.0
    - PR with removal: https://github.com/dmlc/xgboost/pull/7357
    During fit(), it requires now to pass encoded target to estimator during the fit.
    During predict(), it outputs now encoded target.
    To be able to use XGBClassifier as in previous versions, we are wrapping XGBClassifier in autoai-libs.
    Inside this wrapper, we are placing back LabelEncoder transformer,
    so input data to fit() and output data from predict() can be still unencoded, as in xgboost version prior to 1.6.
    """

    def __init__(self, **kwargs):
        self._le_transformer = LabelEncoder()
        super().__init__(**kwargs)

    def fit(self, X, y, **fit_params):
        self._le_transformer.fit(y)
        super().fit(X, self._le_transformer.transform(y), **fit_params)
        return self

    def predict(self, X, **predict_params):
        encoded_result = super().predict(X, **predict_params)
        return self._le_transformer.inverse_transform(encoded_result)
