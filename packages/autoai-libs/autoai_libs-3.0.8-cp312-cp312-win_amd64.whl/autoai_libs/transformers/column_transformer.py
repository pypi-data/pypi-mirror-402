################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import abc
from typing import Union

import numpy as np

from .general_transformer import AutoAITransformer


class ColumnTransformer(AutoAITransformer):
    """ColumnTransformer represents a transformer that acts on columns or tuples of columns.

    Args:
        :cols_to_be_transformed: list
            A list of column indices to be transformed,
            or tuples of indices to be transformed.
        :pass_x_and_col_ref_only: bool
            If True, perform_transformation will pass the x and the col_ref, not the entire column
        :delete_source_columns: boolean
            If True, delete the source columns of the transformation.

    Kwargs:
    """

    def __init__(
        self,
        cols_to_be_transformed: Union[list, int],
        pass_x_and_col_ref_only: bool = False,
        delete_source_columns: bool = False,
    ):
        if isinstance(cols_to_be_transformed, int):
            self.cols_to_be_transformed = [cols_to_be_transformed]
        else:
            self.cols_to_be_transformed = cols_to_be_transformed

        self.pass_x_and_col_ref_only = pass_x_and_col_ref_only
        self.delete_source_columns = delete_source_columns

    @abc.abstractmethod
    def perform_transformation(self, X: np.ndarray, column_ref: Union[tuple, int]) -> np.ndarray:
        raise NotImplementedError()

    @abc.abstractmethod
    def is_colref_valid(self, X: np.ndarray, column_ref: Union[tuple, int]) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def perform_delete(self, X: np.ndarray, column_ref: Union[tuple, int]) -> np.ndarray:
        raise NotImplementedError()

    def is_valid(self, X: np.ndarray) -> bool:
        for column_ref in self.cols_to_be_transformed:
            if not self.is_colref_valid(X, column_ref):
                return False
        return True

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> "ColumnTransformer":
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        for column_ref in self.cols_to_be_transformed:
            X = self.perform_transformation(X, column_ref)

        if self.delete_source_columns:
            X = self.perform_delete(X, self.cols_to_be_transformed)

        return X
