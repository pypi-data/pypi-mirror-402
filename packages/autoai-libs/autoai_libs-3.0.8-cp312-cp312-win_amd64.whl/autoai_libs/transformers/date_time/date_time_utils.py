################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
__all__ = ["apply_date_aggregations"]

import logging
from typing import List, Tuple

import numpy as np

from autoai_libs.transformers.date_time.small_time_transformers import (
    DatetimeExtractTransformer,
    DateToFloatTimestampTransformer,
    DateToTimestampTransformer,
    DayExtractTransformer,
    DayOfWeekExtractTransformer,
    DayOfYearExtractTransformer,
    FloatTimestampExtractTransformer,
    FloatTimestampExtractTransformer32,
    HourExtractTransformer,
    MinuteExtractTransformer,
    MonthExtractTransformer,
    SecondExtractTransformer,
    TimestampExtractTransformer,
    WeekExtractTransformer,
    YearExtractTransformer,
)

logger = logging.getLogger("autoai_libs")


def apply_date_aggregations(
    X: np.ndarray | None,
    date_column_indices: List[int],
    options: List[str],
    delete_source_columns: bool = True,
    column_headers_list: List[str] = None,
    one_timestamp_type_flag: bool = True,
    float32_processing_flag: bool = True,
) -> Tuple[np.ndarray, list]:
    """Transform date columns from X based on date_column_indices.
    Transformations that could be applied (options):
    - 'Datetime'
    - 'DateToFloatTimestamp'
    - 'DateToTimestamp'
    - 'Timestamp'
    - 'FloatTimestamp'
    - 'Year'
    - 'Month'
    - 'Week'
    - 'DayOfYear'
    - 'DayOfMonth'
    - 'DayOfWeek'
    - 'Hour'
    - 'Minute'
    - 'Second'

    or:
    - 'all' that indicates that all transformations should be applied.
    """
    all_supported_options = [
        "Datetime",
        "DateToFloatTimestamp",
        "DateToTimestamp",
        "Timestamp",
        "FloatTimestamp",
        "Year",
        "Month",
        "Week",
        "DayOfYear",
        "DayOfMonth",
        "DayOfWeek",
        "Hour",
        "Minute",
        "Second",
    ]

    if "all" in options and one_timestamp_type_flag:
        supported_options = [
            "FloatTimestamp",
            "Year",
            "Month",
            "Week",
            "DayOfYear",
            "DayOfMonth",
            "DayOfWeek",
            "Hour",
            "Minute",
            "Second",
        ]
    else:
        supported_options = all_supported_options

    if column_headers_list is not None and column_headers_list:
        column_headers_list_copy = column_headers_list.copy()
    else:
        column_headers_list_copy = []

    if date_column_indices is not None and date_column_indices:
        if delete_source_columns:
            l_delete_source_columns = False
            # l_delete_source_columns will become True right before the addition of the last aggregation column
            # agg_counter holds the number of additions
            if "all" in options:  # date_column_indices: #exclude 'all' keyword
                agg_counter = len(supported_options)
                # if one_timestamp_type_flag:
                #     agg_counter=agg_counter-4
            else:  # Find the aggregations that are valid
                agg_counter = 0
                for elt in options:
                    if elt in supported_options:
                        agg_counter = agg_counter + 1
                    else:
                        logger.warning("\n" + elt + ": Invalid aggregation")
                if agg_counter == 0:
                    logger.warning("Valid date aggregations:")
                    logger.warning(supported_options)
                    logger.warning("No valid date aggregations were found in options. No transforms are applied")
                    return X, column_headers_list_copy
        else:
            l_delete_source_columns = False
            agg_counter = -1  # agg_counter has no effect in this case

        supported_functions_dict = {}
        supported_functions_dict["Datetime"] = DatetimeExtractTransformer
        supported_functions_dict["DateToFloatTimestamp"] = DateToFloatTimestampTransformer
        supported_functions_dict["DateToTimestamp"] = DateToTimestampTransformer
        supported_functions_dict["Timestamp"] = TimestampExtractTransformer
        supported_functions_dict["DayOfWeek"] = DayOfWeekExtractTransformer
        supported_functions_dict["DayOfMonth"] = DayExtractTransformer
        supported_functions_dict["Hour"] = HourExtractTransformer
        supported_functions_dict["DayOfYear"] = DayOfYearExtractTransformer
        supported_functions_dict["Week"] = WeekExtractTransformer
        supported_functions_dict["Month"] = MonthExtractTransformer
        supported_functions_dict["Year"] = YearExtractTransformer
        supported_functions_dict["Second"] = SecondExtractTransformer
        supported_functions_dict["Minute"] = MinuteExtractTransformer

        if float32_processing_flag:
            supported_functions_dict["FloatTimestamp"] = FloatTimestampExtractTransformer32
        else:
            supported_functions_dict["FloatTimestamp"] = FloatTimestampExtractTransformer

        added_options = []
        for tried_opt in supported_options:
            if "all" in options or tried_opt in options:
                agg_counter = agg_counter - 1
                if delete_source_columns and agg_counter == 0:
                    l_delete_source_columns = True

                if X is not None:
                    time_t_datetime = supported_functions_dict[tried_opt](
                        cols_to_be_transformed=date_column_indices, delete_source_columns=l_delete_source_columns
                    )
                    X = time_t_datetime.fit_transform(X)

                added_options.append(tried_opt)

        if column_headers_list is not None and column_headers_list:
            for idx_options, time_agg_opt in enumerate(added_options):
                for idx_indices, dt_col_index in enumerate(date_column_indices):
                    new_column_name = (
                        f"NewDateFeature_{(idx_options*len(date_column_indices))+idx_indices}"
                        f"_{time_agg_opt}({column_headers_list_copy[dt_col_index]})"
                    )
                    column_headers_list_copy.append(new_column_name)

            if delete_source_columns:
                column_headers_list_copy = [
                    elt for k, elt in enumerate(column_headers_list_copy) if k not in date_column_indices
                ]

    return X, column_headers_list_copy
