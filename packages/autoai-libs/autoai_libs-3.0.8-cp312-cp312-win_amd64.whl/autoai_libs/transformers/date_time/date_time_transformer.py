################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

from autoai_libs.detectors.date_time.date_time_detector import DateDatasetDetector
from autoai_libs.transformers.date_time.date_time_utils import apply_date_aggregations
from autoai_libs.transformers.exportable import ColumnSelector
from autoai_libs.utils.exportable_utils import (
    get_constant_column_indices_missingvalues,
    global_missing_values_reference_list,
    transform_row,
)


class DateTransformer(BaseEstimator, TransformerMixin):
    """
    Detects date columns on an input array and adds new feature columns for each detected date column
    """

    def __init__(
        self,
        date_column_indices=None,
        options=None,
        delete_source_columns=True,
        column_headers_list=None,
        missing_values_reference_list=None,
        activate_flag=True,
        float32_processing_flag=True,
    ):
        """

        :praram date_column_indices: upfront known list of date columns indices
        :param options: List containing the types of new feature columns to add for each detected datetime column.
                        List can contain one or more of ['all,'Datetime','DateToFloatTimestamp','DateToTimestamp',
                        'Timestamp','FloatTimestamp', 'DayOfWeek','DayOfMonth', 'Hour','DayOfYear','Week','Month',
                        'Year','Second','Minute']. Default is None, in this case all the above options are applied
        :param delete_source_columns: Flag determining whether the original date columns will be deleted or not
        :param column_headers_list: List containing the column names of the input array
        :param missing_values_reference_list: List containing missing values of the input array
        :param activate_flag: Flag that determines whether the transformer will be applied or not
        :param float32_processing_flag: Flag that determines whether timestamps will be float32-compatible. Default True.
        """

        self.float32_processing_flag = float32_processing_flag
        self.missing_values_reference_list = (
            global_missing_values_reference_list
            if missing_values_reference_list is None
            else missing_values_reference_list
        )
        self.column_headers_list = [] if column_headers_list is None else column_headers_list
        self.columns_added_flag = False

        if options is None:
            self.options = ["all"]
        else:
            self.options = options

        self.delete_source_columns = delete_source_columns

        self.activate_flag = activate_flag

        self.date_column_indices = date_column_indices
        self.new_column_headers_list = []  # this is the column_headers_list + what will be added

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray = None,
        column_headers_list: list = None,
        missing_values_reference_list: list = None,
    ) -> "DateTransformer":
        """Detect which columns are date ones, save the results.
        In addition save number of X rows and columns.
        """
        if column_headers_list is not None:
            self.column_headers_list = column_headers_list
        if missing_values_reference_list is not None:
            self.missing_values_reference_list = missing_values_reference_list

        self.num_rows = X.shape[0]
        self.num_columns = X.shape[1]
        if self.activate_flag:
            # do fit here
            if self.date_column_indices is None:
                date_detector = DateDatasetDetector(
                    X, y, missing_values_reference_list=self.missing_values_reference_list
                )
                date_detector.detect()
                self.date_column_indices = date_detector.get_date_columns_indices()

            Y, l_column_headers_list = apply_date_aggregations(
                X=X,
                date_column_indices=self.date_column_indices,
                options=self.options,
                delete_source_columns=self.delete_source_columns,
                column_headers_list=self.column_headers_list,
                float32_processing_flag=self.float32_processing_flag,
            )

            if len(l_column_headers_list) != len(self.column_headers_list):
                new_index_list = []
                new_headers_list = []
                for i, elt in enumerate(l_column_headers_list):
                    if elt not in self.column_headers_list:
                        new_index_list.append(i)
                        new_headers_list.append(elt)

                XY_diff = Y[:, new_index_list]
                non_const_indices_diff = get_constant_column_indices_missingvalues(
                    X=XY_diff, missing_values_reference_list=self.missing_values_reference_list, reverse_flag=True
                )
                non_const_indices_Y = []
                for i, elt in enumerate(non_const_indices_diff):
                    non_const_indices_Y.append(new_index_list[elt])

                final_indices = []
                if X.ndim == 1:
                    ncols_x = 1
                else:
                    ncols_x = X.shape[1]
                if Y.ndim == 1:
                    ncols_y = 1
                else:
                    ncols_y = Y.shape[1]

                indices_x = list(range(ncols_x))
                for i, elt in enumerate(list(range(ncols_y))):
                    if i in indices_x or i in non_const_indices_Y:
                        final_indices.append(i)

                self.column_selector = ColumnSelector(columns_indices_list=final_indices)

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Do transformation, apply date aggregations and return transformed data."""
        assert X.ndim == 2, f"X should be 2 dimensional but given: {X.ndim} dimensions."

        if self.activate_flag:
            Y, l_column_headers_list = apply_date_aggregations(
                X=X,
                date_column_indices=self.date_column_indices,
                options=self.options,
                delete_source_columns=self.delete_source_columns,
                column_headers_list=self.column_headers_list,
                float32_processing_flag=self.float32_processing_flag,
            )

            # self.new_column_headers_list should always be set to l_column_headers_list.
            # If self.column_headers_list is empty, l_column_headers_list will also be empty.
            # Additionally, comparing lengths (len(l_column_headers_list) != len(self.column_headers_list))
            # is not a reliable way to detect added columns, as the lists could differ in content
            # even if their lengths are the same.
            if len(l_column_headers_list) != len(self.column_headers_list):
                # Now keep only the non-constant columns
                Y = self.column_selector.fit_transform(Y)
                l_column_headers_list = list(transform_row(self.column_selector, l_column_headers_list))

                if len(l_column_headers_list) != len(self.column_headers_list):
                    self.new_column_headers_list = l_column_headers_list
                    self.columns_added_flag = True
                else:
                    self.new_column_headers_list = self.column_headers_list
                    self.columns_added_flag = False

            else:
                self.new_column_headers_list = self.column_headers_list
                self.columns_added_flag = False

        else:
            return X

        return Y
