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
from autoai_libs.utils.exportable_utils import numpy_select_columns


class ColumnSelector(BaseEstimator, TransformerMixin):
    """
    Selects a subset of columns for a given numpy array or subset of elements of a list
    """

    def __init__(self, columns_indices_list, activate_flag=True):
        """

        :param columns_indices_list: list of indices to select numpy columns or list elements
        :param activate_flag: determines whether transformer is active or not
        """
        self.activate_flag = activate_flag
        self.columns_indices_list = columns_indices_list
        self.columns_selected_flag = False

    def fit(self, X, y=None):
        assert X.ndim == 2
        self._check_n_features(X, reset=True)

        if isinstance(X, list):
            logger.debug("ColumnSelector: Starting fit(" + str(len(X)) + "x" + str(1) + ")")
        else:
            logger.debug(
                "ColumnSelector: Starting fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
            )
        if debug_timings:
            start_time = time()

        if debug_timings:
            elapsed_time = time() - start_time
            if isinstance(X, list):
                logger.debug(
                    "ColumnSelector: Ending fit("
                    + str(len(X))
                    + "x"
                    + str(1)
                    + "), elapsed_time (s): "
                    + str(elapsed_time)
                )
            else:
                logger.debug(
                    "ColumnSelector: Ending fit("
                    + str(X.shape[0])
                    + "x"
                    + str(X.reshape(X.shape[0], -1).shape[1])
                    + "), elapsed_time (s): "
                    + str(elapsed_time)
                )
        else:
            if isinstance(X, list):
                logger.debug("ColumnSelector: Ending fit(" + str(len(X)) + "x" + str(1) + ")")
            else:
                logger.debug(
                    "ColumnSelector: Ending fit("
                    + str(X.shape[0])
                    + "x"
                    + str(X.reshape(X.shape[0], -1).shape[1])
                    + ")"
                )

        return self

    def transform(self, X):
        check_array(
            X, ensure_min_features=1, ensure_min_samples=1, dtype=None, force_all_finite="allow-nan", accept_sparse=True
        )

        if hasattr(self, "n_features_in_") and self.activate_flag:
            self._check_n_features(X, reset=False)

        if isinstance(X, list):
            logger.debug("ColumnSelector: Starting transform(" + str(len(X)) + "x" + str(1) + ")")
        else:
            logger.debug(
                "ColumnSelector: Starting transform("
                + str(X.shape[0])
                + "x"
                + str(X.reshape(X.shape[0], -1).shape[1])
                + ")"
            )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            Y, self.columns_selected_flag = numpy_select_columns(X, columns_indices_list=self.columns_indices_list)
        else:
            self.columns_selected_flag = False
            Y = X

        if debug_timings:
            elapsed_time = time() - start_time
            if isinstance(X, list):
                logger.debug(
                    "ColumnSelector: Ending transform("
                    + str(len(X))
                    + "x"
                    + str(1)
                    + "), elapsed_time (s): "
                    + str(elapsed_time)
                )
            else:
                logger.debug(
                    "ColumnSelector: Ending transform("
                    + str(Y.shape[0])
                    + "x"
                    + str(Y.reshape(Y.shape[0], -1).shape[1])
                    + "), elapsed_time (s): "
                    + str(elapsed_time)
                )
        else:
            if isinstance(X, list):
                logger.debug("ColumnSelector: Ending transform(" + str(len(X)) + "x" + str(1) + ")")
            else:
                logger.debug(
                    "ColumnSelector: Ending transform("
                    + str(Y.shape[0])
                    + "x"
                    + str(Y.reshape(Y.shape[0], -1).shape[1])
                    + ")"
                )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
