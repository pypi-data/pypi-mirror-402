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
from autoai_libs.utils.exportable_utils import global_missing_values_reference_list, numpy_replace_values


# TODO: Suggestion to change filling_values -> filling_value in the next RT (25.2 or 26.1)
class NumpyReplaceUnknownValues(BaseEstimator, TransformerMixin):
    """
    Given a numpy array and a reference list of known values for each column,
    replaces values that are not part of a reference list with a special value
    (typically np.nan). This is typically used to remove labels for columns in a test dataset
    that have not been seen in the corresponding columns of the training dataset.
    """

    def __init__(
        self, known_values_list=None, filling_values=None, missing_values_reference_list=None, filling_values_list=None
    ):
        """

        :param known_values_list: reference list of lists of known values for each column
        :param filling_values: special value assigned to unknown values
        """

        if missing_values_reference_list is None:
            self.missing_values_reference_list = global_missing_values_reference_list
        else:
            self.missing_values_reference_list = missing_values_reference_list

        if known_values_list is None:
            self.known_values_list = []
        else:
            self.known_values_list = known_values_list  # list of known values to the transformer

        if filling_values is None:
            self.filling_values = np.nan
        else:
            self.filling_values = filling_values  # filling value for the unknown values

        # TODO: Remove it in the next RT (25.2 or 26.1) as it is not used
        if filling_values_list is None:
            self.filling_values_list = []
        else:
            self.filling_values_list = filling_values_list

    def fit(self, X, y=None):
        self._check_n_features(X, reset=True)

        if type(self.known_values_list) is list:
            if len(self.known_values_list) == 0:
                from autoai_libs.utils.exportable_utils import numpy_get_categories

                numpy_get_categories(
                    X, range(X.shape[0]), self.missing_values_reference_list, categories_list2=self.known_values_list
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
            "NumpyReplaceUnknownValues: Starting transform("
            + str(X.shape[0])
            + "x"
            + str(X.reshape(X.shape[0], -1).shape[1])
            + ")"
        )
        if debug_timings:
            start_time = time()

        Y = numpy_replace_values(
            X, filling_values=self.filling_values, reference_values_list=self.known_values_list, invert_flag=True
        )

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "NumpyReplaceUnknownValues: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "NumpyReplaceUnknownValues: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + ")"
                + "\n"
            )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
