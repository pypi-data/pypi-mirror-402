################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from time import time

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.utils import check_array

from autoai_libs.transformers.exportable._debug import debug_timings, debug_transform_return, logger


class NumImputer(BaseEstimator, TransformerMixin):
    """
    This is a wrapper for numerical imputer
    """

    def __init__(self, strategy, missing_values, activate_flag=True, **kwargs):
        self.strategy = strategy
        self.missing_values = missing_values
        self.activate_flag = activate_flag
        self.imputer = SimpleImputer(strategy=strategy, missing_values=missing_values)

    def fit(self, X, y=None):
        self._check_n_features(X, reset=True)

        logger.debug(
            "NumImputer: Starting fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            # We need to record which columns are made up of only missing values
            # if the strategy is not 'constant' since these columns will be DISCARDED
            # when we call transform afterwards.
            if self.strategy != "constant":
                self.bad_columns = sorted(
                    [c for c in range(X.shape[1]) if is_all_missing(X[:, c], self.missing_values)]
                )
            self.imputer.fit(X, y)

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "NumImputer: Ending fit("
                + str(X.shape[0])
                + "x"
                + str(X.reshape(X.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "NumImputer: Ending fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
            )

        return self

    def transform(self, X):
        assert X.ndim == 2
        check_array(
            X, ensure_min_features=1, ensure_min_samples=1, dtype=None, force_all_finite="allow-nan", accept_sparse=True
        )

        if hasattr(self, "n_features_in_"):
            self._check_n_features(X, reset=False)

        logger.debug(
            "NumImputer: Starting transform(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            Y = X.astype(np.float64)
            Y = self.imputer.transform(Y)
            if self.strategy != "constant":
                insertion_indices = [bi - i for i, bi in enumerate(self.bad_columns)]
                Y = np.insert(Y, insertion_indices, 0, axis=1)
        else:
            Y = X

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "NumImputer: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "NumImputer: Ending transform(" + str(Y.shape[0]) + "x" + str(Y.reshape(Y.shape[0], -1).shape[1]) + ")"
            )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        assert X.shape == Y.shape
        return Y


from collections.abc import Iterable


def is_all_missing(x, bad_vals):
    if not isinstance(bad_vals, Iterable):
        bad_vals = [bad_vals]

    std_bad = [v for v in bad_vals if not np.isnan(v)]

    assert len(std_bad) + 1 >= len(bad_vals)
    test_nan = len(std_bad) < len(bad_vals)
    if not test_nan:
        return np.isin(x, std_bad).all()
    else:  # All nans or mixed
        it = (np.isnan(float(cell)) or np.isin(cell, std_bad) for cell in x)
        return np.fromiter(it, float).all()
