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
from autoai_libs.utils.exportable_utils import compress_str_column, global_missing_values_reference_list, numpy_whatis


class CompressStrings(BaseEstimator, TransformerMixin):
    """
    Removes spaces and special characters from string columns of a numpy array
    """

    def __init__(
        self,
        compress_type="string",
        dtypes_list=None,
        misslist_list=None,
        missing_values_reference_list=None,
        activate_flag=True,
    ):
        self.compress_type = compress_type

        if dtypes_list is None:
            self.dtypes_list = []
        else:
            self.dtypes_list = dtypes_list

        if misslist_list is None:
            self.misslist_list = []
        else:
            self.misslist_list = misslist_list

        self.activate_flag = activate_flag

        # TODO: Remove missing_values_reference_list in new RT (26.1 or 25.2) as it wasn't even used
        if missing_values_reference_list is None:
            self.missing_values_reference_list = global_missing_values_reference_list
        else:
            self.missing_values_reference_list = missing_values_reference_list

    def fit(self, X, y=None):
        self._check_n_features(X, reset=True)

        logger.debug(
            "CompressStrings: Starting fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            # do fit here
            pass

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "CompressStrings: Ending fit("
                + str(X.shape[0])
                + "x"
                + str(X.reshape(X.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "CompressStrings: Ending fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
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
            "CompressStrings: Starting transform("
            + str(X.shape[0])
            + "x"
            + str(X.reshape(X.shape[0], -1).shape[1])
            + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            Y = X.copy().astype(object)
            num_columns = X.shape[1]

            for j in range(num_columns):
                Xcol = X[:, j]
                dtype_str = self.dtypes_list[j]
                misslist = self.misslist_list[j]

                if dtype_str == "char_str":
                    Y[:, j] = compress_str_column(Xcol, misslist, self.compress_type)
        else:
            Y = X

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "CompressStrings: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "CompressStrings: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + ")"
            )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
