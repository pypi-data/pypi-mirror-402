################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import abc
import logging

import numpy as np

from .column_transformer import ColumnTransformer
from .small_data_transformer import SmallDataTransformer

logger = logging.getLogger("autoai_libs")


class SmallDataColumnTransformer(ColumnTransformer, SmallDataTransformer):
    @abc.abstractmethod
    def __init__(self, func, *args, **kwargs):
        self.func = func
        super().__init__(*args, **kwargs)

    def is_colref_valid(self, X, column_ref):
        try:
            self.perform_transformation(X, column_ref)
            return True
        except Exception as e:
            logger.warning(
                "Error accessing column reference {0}, X has type: {1}, error='{2}'".format(
                    column_ref, type(X).__name__, e
                ),
                exc_info=e,
            )
            return False

    def perform_transformation(self, X, column_ref):
        if self.pass_x_and_col_ref_only:
            transformed = self.func(X, column_ref)
        else:
            if isinstance(column_ref, tuple):
                transformed = self.func(*self.slice_into_tuple(X, column_ref))
            else:
                transformed = self.func(X[:, column_ref])

        X = np.column_stack((X, transformed))
        return X

    def perform_delete(self, X, column_ref):
        X = np.delete(X, column_ref, 1)
        return X

    def slice_into_tuple(self, X, column_ref_tuple):
        output_list = []
        for column in column_ref_tuple:
            if 0 <= column < X.shape[1]:
                output_list.append(X[:, column])

            else:
                raise AssertionError(f"Column out of range: {column}, X has {X.shape[1]} columns.")

        return tuple(output_list)
