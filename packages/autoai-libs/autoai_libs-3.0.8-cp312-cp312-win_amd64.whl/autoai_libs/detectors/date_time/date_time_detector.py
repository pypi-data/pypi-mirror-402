################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import logging
from typing import List

import numpy as np
import pandas as pd

from autoai_libs.utils.exportable_utils import (
    FCplus,
    global_missing_values_reference_list,
    numpy_whatis,
    setValueOrDefault,
)

from ..small_data_detector import SmallDataDetector

logger = logging.getLogger("autoai_libs")


class DateDatasetDetector(SmallDataDetector):
    """DateDatasetDetector class for detecting columns with date.

    Parameters
    ----------
    X: np.ndarray, required

    y: np.ndarray, required

    column_headers_list: list, optional
        List with column names (strings).

    missing_values_reference_list: list, optional
        List with missing values.
    """

    def __init__(
        self, X: np.ndarray, y: np.ndarray = None, column_headers_list=None, missing_values_reference_list=None
    ):
        self.missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )

        if column_headers_list is None:
            self.column_headers_list = list(range(X.shape[1]))
        else:
            self.column_headers_list = column_headers_list

        self.X = X
        self.y = y

        # Output variables
        self.flag = False

        self.date_columns_indices = []

        if X.ndim == 1:
            self.num_columns = 1
        else:
            self.num_columns = X.shape[1]
        self.num_rows = X.shape[0]

    def get_date_columns_indices(self) -> List[int]:
        """Returns columns indices where date was found."""
        return self.date_columns_indices

    def get_date_columns(self) -> np.ndarray:
        """Returns columns where date was found."""
        if self.X.ndim == 1:
            if self.date_columns_indices:
                return self.X
        else:
            return self.X[:, self.date_columns_indices]

    def detect(self) -> bool:
        """Find out which columns are date columns. Returns True if date column is detected otherwise returns False."""
        logger.debug("DateDatasetDetector: Starting detection of columns with date values")

        for j in range(self.num_columns):
            if self.num_columns == 1:
                x_col = self.X
            else:
                x_col = self.X[:, j]

            misslist, dtype_str, stats = numpy_whatis(x_col, self.missing_values_reference_list, return_stats_flag=True)
            dfc = pd.DataFrame(x_col)
            if FCplus.is_column_string_in_datetime_format(dfc[0]) and stats["datetime_column_flag"]:
                self.flag = True
                self.date_columns_indices.append(j)

        logger.debug("DateDatasetDetector: Ending detection of columns with date values")

        return self.flag
