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
from autoai_libs.utils.exportable_utils import numpy_permute_array


class NumpyPermuteArray(BaseEstimator, TransformerMixin):
    """
    Rearranges columns or rows of a numpy array based on a list of indices
    """

    def __init__(self, permutation_indices=None, axis=None):
        """
        :param permutation_indices: list of indexes based on which columns will be rearranged
        :param axis: 0 permute along columns, 1, permute along rows
        """
        if permutation_indices is None:
            self.permutation_indices = []
        else:
            self.permutation_indices = permutation_indices

        if axis is None:
            self.axis = 0
        else:
            self.axis = axis

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
            "NumpyPermuteArray: Starting transform("
            + str(X.shape[0])
            + "x"
            + str(X.reshape(X.shape[0], -1).shape[1])
            + ")"
        )
        if debug_timings:
            start_time = time()

        Y = numpy_permute_array(X, self.permutation_indices, self.axis)

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "NumpyPermuteArray: Ending transform("
                + str(X.shape[0])
                + "x"
                + str(X.reshape(X.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "NumpyPermuteArray: Ending transform("
                + str(X.shape[0])
                + "x"
                + str(X.reshape(X.shape[0], -1).shape[1])
                + ")\n"
            )

        Y = Y.reshape(Y.shape[0], -1)
        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
