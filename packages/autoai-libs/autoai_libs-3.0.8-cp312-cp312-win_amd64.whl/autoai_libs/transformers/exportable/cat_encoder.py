################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import warnings
from time import time
from typing import Literal

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.utils import check_array

from autoai_libs.transformers.exportable._debug import (
    debug_timings,
    debug_transform_return,
    global_sklearn_version_family,
    logger,
    sklearn_version_list,
)


class CatEncoder(BaseEstimator, TransformerMixin):
    """
    This is a template for classes
    """

    def __init__(
        self,
        encoding: Literal["ordinal", "onehot", "onehot-dense"],
        categories,
        dtype,
        handle_unknown,
        sklearn_version_family=global_sklearn_version_family,
        activate_flag=True,
    ):
        self.encoding = encoding
        self.categories = categories
        self.dtype = dtype
        self.handle_unknown = handle_unknown
        # TODO: Remove it in the next RT (25.2 or 26.1) as it is not used
        self.sklearn_version_family = sklearn_version_family
        self.activate_flag = activate_flag

        if encoding == "onehot" or encoding == "onehot-dense":
            sparse_flag = encoding == "onehot"

            self.encoder = OneHotEncoder(
                categories=categories, sparse_output=sparse_flag, dtype=dtype, handle_unknown=handle_unknown
            )
        else:
            # use ordinal if not specified
            self.encoder = OrdinalEncoder(categories=categories, dtype=dtype)

    def fit(self, X, y=None):
        assert X.ndim == 2
        self._check_n_features(X, reset=True)

        logger.debug(
            "CatEncoder: Starting fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            Y = self.encoder.fit(X, y)
            self.categories_found = self.encoder.categories_

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "CatEncoder: Ending fit("
                + str(X.shape[0])
                + "x"
                + str(X.reshape(X.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "CatEncoder: Ending fit(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
            )

        return self

    def transform(self, X):
        check_array(
            X, ensure_min_features=1, ensure_min_samples=1, dtype=None, force_all_finite="allow-nan", accept_sparse=True
        )

        if hasattr(self, "n_features_in_"):
            self._check_n_features(X, reset=False)

        logger.debug(
            "CatEncoder: Starting transform(" + str(X.shape[0]) + "x" + str(X.reshape(X.shape[0], -1).shape[1]) + ")"
        )
        if debug_timings:
            start_time = time()

        if self.activate_flag:
            try:
                Y = self.encoder.transform(X)
            # TODO: Remove it in the next RT (25.2 or 26.1)
            except ValueError as e:
                # Handling unknown categories for different sklearn versions
                if str(e).startswith("Found unknown categories") and (
                    sklearn_version_list[0] == "1"
                    or (sklearn_version_list[0] == "0" and int(sklearn_version_list[1]) > 23)
                ):
                    stre = str(e)
                    error_msg = "".join([stre.split("[")[0], stre.split("[")[1].split("]")[1]])
                else:
                    raise e
                warnings.warn(error_msg, Warning)
                temp_handle_unknown = self.encoder.handle_unknown
                # note: set unknown values handling in sklearn
                self.encoder.handle_unknown = "ignore"
                Y = self.encoder.transform(X)
                # note: unknown values handling in sklearn back to default for fit compatibility for OrdinalEncoder
                self.encoder.handle_unknown = temp_handle_unknown
        else:
            Y = X

        if debug_timings:
            elapsed_time = time() - start_time
            logger.debug(
                "CatEncoder: Ending transform("
                + str(Y.shape[0])
                + "x"
                + str(Y.reshape(Y.shape[0], -1).shape[1])
                + "), elapsed_time (s): "
                + str(elapsed_time)
            )
        else:
            logger.debug(
                "CatEncoder: Ending transform(" + str(Y.shape[0]) + "x" + str(Y.reshape(Y.shape[0], -1).shape[1]) + ")"
            )

        if debug_transform_return:
            logger.debug(f"{self.__class__.__name__}.transform({X})->{Y}")
        return Y
