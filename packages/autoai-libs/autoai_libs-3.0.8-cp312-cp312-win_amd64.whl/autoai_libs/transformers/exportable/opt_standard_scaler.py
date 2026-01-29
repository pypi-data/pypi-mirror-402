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
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_array

from autoai_libs.transformers.exportable._debug import debug_timings, debug_transform_return, logger


class OptStandardScaler(BaseEstimator, TransformerMixin):
    """
    This transformer implements an optional StandardScaler.
    It acts as a StandardScaler() if use_scaler_flag is True.
    Otherwise it returns the input numpy array unchanged
    """

    def __init__(self, use_scaler_flag=True, **kwargs):
        """

        :param use_scaler_flag: Act as StandardScaler() if true, do nothing if false. Default is True
        StandardScaler parameters. See:
        http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html
        :param num_scaler_copy:
        :param num_scaler_with_mean:
        :param num_scaler_with_std:
        """

        self.use_scaler_flag = use_scaler_flag

        if self.use_scaler_flag:
            self.num_scaler_copy = kwargs.get("num_scaler_copy", True)
            self.num_scaler_with_mean = kwargs.get("num_scaler_with_mean", True)
            self.num_scaler_with_std = kwargs.get("num_scaler_with_std", True)

            self.scaler = StandardScaler(
                copy=self.num_scaler_copy, with_mean=self.num_scaler_with_mean, with_std=self.num_scaler_with_std
            )

    def fit(self, X, y=None):
        assert X.ndim == 2
        self._check_n_features(X, reset=True)

        if self.use_scaler_flag:
            self.scaler.fit(X, y)
        return self

    def transform(self, X):
        check_array(
            X, ensure_min_features=1, ensure_min_samples=1, dtype=None, force_all_finite="allow-nan", accept_sparse=True
        )

        if hasattr(self, "n_features_in_"):
            self._check_n_features(X, reset=False)

        logger.debug(
            "OptStandardScaler: Starting transform("
            + str(X.shape[0])
            + "x"
            + str(X.reshape(X.shape[0], -1).shape[1])
            + ")"
        )
        if debug_timings:
            start_time = time()

        if self.use_scaler_flag:
            Y = self.scaler.transform(X)
        else:
            Y = X

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "OptStandardScaler: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "OptStandardScaler: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + ")"
            )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
