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
from sklearn.utils import check_array

from autoai_libs.transformers.exportable._debug import debug_timings, debug_transform_return, logger
from autoai_libs.utils.exportable_utils import (
    global_missing_values_reference_list,
    numpy_floatstr2float,
    setValueOrDefault,
)


class FloatStr2Float(BaseEstimator, TransformerMixin):
    def __init__(self, dtypes_list, missing_values_reference_list=None, activate_flag=True):
        self.dtypes_list = dtypes_list
        self.missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )

        self.activate_flag = activate_flag

    def fit(self, X, y=None):
        assert X.ndim == 2
        self._check_n_features(X, reset=True)

        logger.debug(
            "FloatStr2Float: Starting fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            # do fit here
            pass

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "FloatStr2Float: Ending fit("
                + str(X.shape[0])
                + "x"
                + str(X.reshape(X.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "FloatStr2Float: Ending fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
            )

        return self

    def transform(self, X):
        check_array(
            X, ensure_min_features=1, ensure_min_samples=1, dtype=None, force_all_finite="allow-nan", accept_sparse=True
        )

        if hasattr(self, "n_features_in_"):
            self._check_n_features(X, reset=False)

        logger.debug(
            "FloatStr2Float: Starting transform("
            + str(X.shape[0])
            + "x"
            + str(X.reshape(X.shape[0], -1).shape[1])
            + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            # do transform here
            Y = X.copy().astype(object)

            for j, dtype in enumerate(self.dtypes_list):
                if dtype == "float_str":
                    Y[:, j] = numpy_floatstr2float(X[:, j], self.missing_values_reference_list)
        else:
            Y = X

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "FloatStr2Float: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "FloatStr2Float: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + ")"
            )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
