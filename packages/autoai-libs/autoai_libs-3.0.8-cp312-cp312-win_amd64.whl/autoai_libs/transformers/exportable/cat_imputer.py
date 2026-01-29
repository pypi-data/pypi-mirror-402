################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from time import time

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.utils import check_array

from autoai_libs.transformers.exportable._debug import (
    debug_timings,
    debug_transform_return,
    global_sklearn_version_family,
    logger,
)


class CatImputer(BaseEstimator, TransformerMixin):
    """
    This is a wrapper for categorical imputer
    """

    def __init__(
        self,
        strategy,
        missing_values,
        sklearn_version_family=global_sklearn_version_family,
        activate_flag=True,
        **kwargs,
    ):
        # TODO: Remove it in the next RT (25.2 or 26.1) as it is not used
        self.sklearn_version_family = sklearn_version_family
        self.strategy = strategy
        self.missing_values = missing_values
        self.activate_flag = activate_flag

        self.imputer = SimpleImputer(strategy=strategy, missing_values=missing_values, **kwargs)

    def fit(self, X, y=None):
        assert X.ndim == 2
        self._check_n_features(X, reset=True)

        logger.debug(
            "CatImputer: Starting fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            self.imputer.fit(X, y)

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "CatImputer: Ending fit("
                + str(X.shape[0])
                + "x"
                + str(X.reshape(X.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "CatImputer: Ending fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
            )

        return self

    def transform(self, X):
        check_array(
            X, ensure_min_features=1, ensure_min_samples=1, dtype=None, force_all_finite="allow-nan", accept_sparse=True
        )

        if hasattr(self, "n_features_in_"):
            self._check_n_features(X, reset=False)

        logger.debug(
            "CatImputer: Starting transform(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            Y = self.imputer.transform(X)
        else:
            Y = X

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "CatImputer: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "CatImputer: Ending transform(" + str(Y.shape[0]) + "x" + str(Y.reshape(Y.shape[0], -1).shape[1]) + ")"
            )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
