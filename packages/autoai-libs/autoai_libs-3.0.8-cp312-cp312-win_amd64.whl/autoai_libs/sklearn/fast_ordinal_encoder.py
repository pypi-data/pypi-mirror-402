################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import numpy as np
from sklearn.preprocessing import OrdinalEncoder
from sklearn.utils import validation


def _original_encode_check_unknown(values, uniques, return_mask=False):
    if values.dtype == object:
        uniques_set = set(uniques)
        diff = list(set(values) - uniques_set)
        if return_mask:
            if diff:
                valid_mask = np.array([val in uniques_set for val in values])
            else:
                valid_mask = np.ones(len(values), dtype=bool)
            return diff, valid_mask
        else:
            return diff
    else:
        unique_values = np.unique(values)
        diff = list(np.setdiff1d(unique_values, uniques, assume_unique=True))
        if return_mask:
            if diff:
                valid_mask = np.in1d(values, uniques)
            else:
                valid_mask = np.ones(len(values), dtype=bool)
            return diff, valid_mask
        else:
            return diff


def _original_encode_numpy(values, uniques=None, encode=False, check_unknown=True):
    if uniques is None:
        if encode:
            uniques, encoded = np.unique(values, return_inverse=True)
            return uniques, encoded
        else:
            # unique sorts
            return np.unique(values)
    if encode:
        if check_unknown:
            diff = _original_encode_check_unknown(values, uniques)
            if diff:
                raise ValueError("y contains previously unseen labels: %s" % str(diff))
        encoded = np.searchsorted(uniques, values)
        return uniques, encoded
    else:
        return uniques


def _fast_encode_python(values, uniques=None, encode=False, table=None):
    if uniques is None:
        uniques = sorted(set(values))
        uniques = np.array(uniques, dtype=values.dtype)

    if encode:
        table = {val: i for i, val in enumerate(uniques)} if not table else table
        try:
            encoded = np.array([table[v] for v in values])
        except KeyError as e:
            raise ValueError("y contains previously unseen labels: %s" % str(e))
        return uniques, encoded
    else:
        return uniques


def _fast_encode(values, uniques=None, encode=False, check_unknown=True, table=None):
    if values.dtype == object:
        try:
            res = _fast_encode_python(values, uniques, encode, table=table)
        except TypeError:
            raise TypeError("argument must be a string or number")
        return res
    else:
        return _original_encode_numpy(values, uniques, encode, check_unknown=check_unknown)


class FastOrdinalEncoder(OrdinalEncoder):
    def __init__(self, categories="auto", dtype=np.float64, handle_unknown="error"):
        self.categories = categories
        self.dtype = dtype
        self.handle_unknown = handle_unknown
        if self.handle_unknown == "error":
            self.unknown_value = None

    def fit(self, X, y=None):
        validation._check_n_features(estimator=self, X=X, reset=True)
        OrdinalEncoder.fit(self, X)

        self.ordinalEncodingTables_ = {}
        for i in range(len(self.categories_)):
            tmpTable = {val: k for k, val in enumerate(self.categories_[i])}
            self.ordinalEncodingTables_[i] = tmpTable

        return self

    def _transform(
        self,
        X,
        handle_unknown="error",
        ensure_all_finite=True,
        warn_on_unknown=False,
        ignore_category_indices=None,
    ):
        if hasattr(self, "n_features_in_"):
            validation._check_n_features(estimator=self, X=X, reset=False)

        X_list, n_samples, n_features = self._check_X(X)

        X_int = np.zeros((n_samples, n_features), dtype=int)
        X_mask = np.ones((n_samples, n_features), dtype=bool)

        if n_features != len(self.categories_):
            raise ValueError(
                "The number of features in X is different to the number of "
                "features of the fitted data. The fitted data had {} features "
                "and the X has {} features.".format(
                    len(
                        self.categories_,
                    ),
                    n_features,
                )
            )

        for i in range(n_features):
            Xi = X_list[i]
            diff, valid_mask = _original_encode_check_unknown(Xi, self.categories_[i], return_mask=True)

            if not np.all(valid_mask):
                if self.handle_unknown == "error":
                    msg = "Found unknown categories {0} in column {1}" " during transform".format(diff, i)
                    raise ValueError(msg)
                else:
                    # Set the problematic rows to an acceptable value and
                    # continue `The rows are marked `X_mask` and will be
                    # removed later.
                    X_mask[:, i] = valid_mask
                    # cast Xi into the largest string type necessary
                    # to handle different lengths of numpy strings
                    if self.categories_[i].dtype.kind in ("U", "S") and self.categories_[i].itemsize > Xi.itemsize:
                        Xi = Xi.astype(self.categories_[i].dtype)
                    else:
                        Xi = Xi.copy()

                    Xi[~valid_mask] = self.categories_[i][0]
            # We use check_unknown=False, since _encode_check_unknown was
            # already called above.

            if self.ordinalEncodingTables_ is None:
                _, encoded = _fast_encode(Xi, self.categories_[i], encode=True, check_unknown=False)
            else:
                _, encoded = _fast_encode(
                    Xi, self.categories_[i], encode=True, check_unknown=False, table=self.ordinalEncodingTables_[i]
                )

            X_int[:, i] = encoded

        return X_int, X_mask
