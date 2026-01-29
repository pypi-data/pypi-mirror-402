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
from sklearn.utils import check_array

from autoai_libs.transformers.exportable._debug import debug_timings, debug_transform_return, logger
from autoai_libs.utils.exportable_utils import numpy_replace_values


# TODO: Suggestion to change filling_values -> filling_value in the next RT (25.2 or 26.1)
class NumpyReplaceMissingValues(BaseEstimator, TransformerMixin):
    """
    Given a numpy array and a reference list of missing values for it,
    replaces missing values with a special value (typically a special missing value such as np.nan).
    """

    def __init__(self, missing_values, filling_values=np.nan):
        """

        :param missing_values: list of values considered as "missing" for the array
        :param filling_values: value to replace the missing values
        """
        if missing_values is None:
            self.missing_values = []
        else:
            self.missing_values = missing_values  # list of missing values to be replaced

        if filling_values is None:
            self.filling_values = np.nan
        else:
            self.filling_values = filling_values  # filling value for the missing values

    def fit(self, X, y=None):
        self._check_n_features(X, reset=True)
        return self

    def transform(self, X):
        assert X.ndim == 2
        check_array(
            X, ensure_min_features=1, ensure_min_samples=1, dtype=None, force_all_finite="allow-nan", accept_sparse=True
        )

        if hasattr(self, "n_features_in_"):
            self._check_n_features(X, reset=False)

        logger.debug(
            "NumpyReplaceMissingValues: Starting transform("
            + str(X.shape[0])
            + "x"
            + str(X.reshape(X.shape[0], -1).shape[1])
            + ")"
        )
        if debug_timings:
            start_time = time()

        Y = numpy_replace_values(
            X, filling_values=self.filling_values, reference_values_list=self.missing_values, invert_flag=False
        )

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "NumpyReplaceMissingValues: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "NumpyReplaceMissingValues: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + ")"
            )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
