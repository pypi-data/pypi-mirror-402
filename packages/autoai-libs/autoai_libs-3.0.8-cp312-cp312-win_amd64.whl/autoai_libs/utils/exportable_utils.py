################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2019-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import datetime
import hashlib
import logging
import numbers
import time
import traceback
from collections import Counter

import numpy as np
import pandas as pd
import six

import autoai_libs.utils.fc_methods as FC

global_missing_values_reference_list = ("?", "", "-", np.nan)

logger = logging.getLogger("autoai_libs")

AlphaNumeric = int | float | str


def numpy_select_columns(X, columns_indices_list):
    """
    Selects columns from numpy array (doesnt work with Pandas objects).
    """
    if columns_indices_list is not None and isinstance(columns_indices_list, list) and columns_indices_list:
        columns_selected_flag = True

        if isinstance(X, list):
            x_ndim = len(X)
            x_numelts = len(X)
        else:
            x_ndim = X.ndim
            x_numelts = X.shape[1]

        if x_ndim == 1:
            logger.warning("numpy_select_columns(): Input array has only one column. No column selection will occur.")
            columns_selected_flag = False
        else:  # Check if all provided indices are within range of the dataset at hand
            for i, index in enumerate(columns_indices_list):
                if not (-x_numelts <= index < x_numelts):
                    logger.warning(
                        f"numpy_select_columns(): train_sample_columns_index_list {i}th index is {index}: "
                        f"this is out of dataset column range [0,{x_numelts}-1]"
                    )
                    logger.warning("No column selection will occur.")
                    columns_selected_flag = False
                    break

        if columns_selected_flag:
            if isinstance(X, list):
                Y = list(np.array(X)[columns_indices_list])
            else:
                Y = X[:, columns_indices_list]
        else:
            Y = X
    else:
        columns_selected_flag = False
        Y = X

    return Y, columns_selected_flag


def numpy_flatten_column(X, remove_second_dim=True):
    """
    Returns flattened numpy array (doesnt work with Pandas objects).
    """
    if isinstance(X[0], np.ndarray) and X[0].shape[0] == 1:
        # this is a numpy array whose elements are numpy arrays (arises from string targets)
        # Y=np.ravel(X)
        # Y=X.flatten()
        Y = np.concatenate(X).ravel()
        if remove_second_dim:
            Y = numpy_remove_second_dim(Y)
    else:
        Y = X
    return Y


def numpy_replace_values(
    X: np.ndarray,
    filling_values: AlphaNumeric,
    reference_values_list: list[list[AlphaNumeric]] | list[AlphaNumeric],
    invert_flag: bool = False,
) -> np.ndarray:
    """
    Replaces values in the input matrix based on a reference list of known values for each column.

    :param X: Input matrix as a NumPy ndarray.
    :param filling_values: Value assigned to array entries that match (or do not match if invert_flag is True) the reference values.
    :param reference_values_list: A list of lists containing known values for each column. If a 1-dimensional list is provided,
                                  it is applied to each column.
    :param invert_flag: If True, replaces values NOT in the reference values list. Default is False.
    :return: Modified NumPy ndarray with replaced values.
    """
    if reference_values_list:
        nested_lists = isinstance(reference_values_list[0], list)
        original_shape = X.shape

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        Y = np.empty(X.shape, dtype=object)

        for j in range(X.shape[1]):
            # Replace pd.NA with np.nan to avoid TypeError
            x_col = np.where(pd.isna(X[:, j]), np.nan, X[:, j])

            if nested_lists:
                reference_values_list_col = reference_values_list[j]
            else:
                reference_values_list_col = reference_values_list

            mask = np.isin(x_col, reference_values_list_col, invert=invert_flag)

            if np.any(
                pd.isna(reference_values_list_col)
            ):  # np.any() instead of any() to ensure compatibility with ONNX constraints
                nan_mask = pd.isna(x_col)
                mask = np.logical_or(mask, nan_mask) if not invert_flag else np.logical_and(mask, ~nan_mask)

            Y[:, j] = np.where(mask, filling_values, X[:, j])

        return Y.reshape(original_shape)
    else:
        return X


def numpy_permute_array(X, permutation_indices=None, axis=None):
    """
    Performs a permutation on rows or columns of an nparray based on a list of permuted
    indices.
    :param X:
    :param permutation_indices: the list of permutation indices. If empty no permutation is performed. Default empty.
    :param axis: if 0 permute columns, if 1 permute columns. Default value is 0
    :return:
    """
    if permutation_indices is None:
        l_permutation_indices = []
    else:
        l_permutation_indices = permutation_indices

    if axis is None:
        l_axis = 0
    else:
        l_axis = axis

    if not l_permutation_indices:  # if permutation list is empty  or was not defined return original matrix
        Y = X.copy()
    else:
        i = np.argsort(l_permutation_indices)
        if l_axis == 0 or l_axis == 1:
            if l_axis == 0:
                Y = X[:, i].copy()
            else:
                Y = X[i, :].copy()
        else:
            Y = X.copy()
    return Y


def numpy_floatstr2float(X, missing_values_reference_list=None):
    """
    Converts a 1-D numpy array of strings that represent floats to floats
    and replaces missing values with np.nan. Also changes type of array from 'object' to 'float'
    :param X: 1-d numpy array of strings
    :param missing_values_reference_list: list of values that should be considered as missing
    :return: 1-D numpy array of floats and np.nan as missing values
    """

    if missing_values_reference_list is None:
        l_missing_values_reference_list = []
    else:
        l_missing_values_reference_list = missing_values_reference_list
    Y = X.copy()
    for i in range(X.shape[0]):
        if X[i] in l_missing_values_reference_list:
            Y[i] = np.nan
        else:
            if not isfloat(X[i]):
                try:
                    Y[i] = float(X[i])
                except Exception as e:
                    Y[i] = np.nan
    # Convert type from object to float
    Z = Y.astype(float)
    return Z


def setValueOrDefault(variable, def_value):
    if variable is None:
        return def_value
    else:
        return variable


def numpy_boolean2float(X: np.array, missing_values_reference_list: list = None):
    """
    Converts a NumPy boolean array to floats, replacing missing values with ones.
    :param X: Numpy array of booleans
    :param missing_values_reference_list: List of values that should be considered as missing
    :return: An unmodified NumPy array or a NumPy array of float values
    """

    if X.dtype == "bool":
        if missing_values_reference_list is not None:
            missing_values_mask = numpy_isin(X, missing_values_reference_list)
            X[missing_values_mask] = np.nan  # np.nan is converted to 1 when cast to float
        Y = X.astype(float)
    else:
        Y = X
    return Y


def compress_string(s, compress_type="string"):
    """
    Compresses a string to either a string without spaces or a int hash
    :param s: input string
    :param compress_type: 'string' or 'hash'
    :return: compressed string or int hash
    """
    # # Remove all special characters and spaces from the string
    # Xcol_copy[i] = ''.join(e for e in str_elt if e.isalnum())
    # Remove all white spaces from the string (including \t characters)

    if compress_type == "string":
        output = "".join(s.split())
    else:
        enc_val = s.encode()
        hash_object = hashlib.md5(enc_val, usedforsecurity=False)
        output = int(hash_object.hexdigest(), 16)
    return output


def compress_str_column(X, misslist, compress_type="string"):
    """
    Compresses a column of strings to a column of strings without whitespaces or a column of int hashes
    :param Xcol:
    :param compress_type: 'string' or 'hash'
    :return: Compressed column
    """
    if isinstance(X, list):
        Xcol = np.asarray(X)
    else:
        Xcol = X

    if Xcol.dtype.kind not in "OSUV":
        return Xcol  # Do not perform compression on data

    Xcol_str = Xcol.astype(str)
    num_rows = Xcol_str.shape[0]

    if compress_type == "string":
        Ycol = Xcol.copy()

        for i in range(num_rows):
            str_elt = Xcol_str[i]

            if not pd.isnull(str_elt) and str_elt not in misslist and not str_elt.isalnum():
                Ycol[i] = compress_string(str_elt, compress_type=compress_type)
    else:
        # using list for performance speed, cannot use indices in numpy due to implicit hash value cast
        hashes_list = []

        for i in range(num_rows):
            str_elt = Xcol_str[i]
            if pd.isnull(str_elt) or str_elt in misslist:
                hashes_list.append(np.nan)
            else:
                hashes_list.append(compress_string(str_elt, compress_type=compress_type))

        Ycol = np.array(hashes_list)

    return Ycol


def convert_float32(X, force_flag=False):
    if X.dtype == "float64" or force_flag:
        Y = X.astype("float32")
    else:  # this includes the case where X.dtype == 'float32'
        Y = X

    return Y


def numpy_whatis(
    X: np.ndarray,
    missing_values_reference_list=None,
    stop_at_one_missing_value_flag=False,
    debug=False,
    use_dtype_str1_flag=True,
    return_stats_flag=False,
):
    """
    Classifies a 1-d numpy array as array of alphanumeric strings, int strings, float strings, ints or floats.
    In addition, for string arrays it discovers the characters representing missing values in the array.
    This is done either by matching a known reference list of missing values or, if such list is not available,
    it identifies missing values as single-character strings that are not alphanumeric.

    :param X: 1-d numpy array of floats, ints, or strings
    :param missing_values_reference_list: list containing the discovered missing values
    :return:
    """
    if debug:
        row_limit = min(X.shape[0], 50)
        logger.debug("numpy_whatis(): Starting. Column: " + str(X[list(range(row_limit))]) + "\n\n")
        start_time = time.time()

    X = numpy_flatten_column(X)
    if missing_values_reference_list is None:
        missing_values_list = []
    else:
        missing_values_list = missing_values_reference_list

    new_missing_values_list = []
    num_missing_values = 0

    nan_added_new_missing_values_flag = False
    nan_added_missing_values_flag = False

    found_nonmissing_flag = False
    found_float_str_flag = False
    found_int_str_flag = False
    found_string_flag = False

    dtype_str = "Unknown"
    dtype_str1 = "Unknown"

    if X.dtype == "float32" or X.dtype == "float16":  # to avoid float16/32 incompatibilities
        X = X.astype(float)

    start_missing_string_values_list = []
    missing_reference_values_exist_list = []

    if missing_values_list:
        # Find which of the missing values in reference list exist in X
        cum_missing_mask_arr, missing_masks_list, missing_reference_values_exist_list = numpy_compute_missing_indicator(
            X, missing_values_list, stop_at_one_missing_value_flag=stop_at_one_missing_value_flag, debug=debug
        )

        X_non_missing = X[~cum_missing_mask_arr]
        XX, xx_xounts = get_unique_values(X_non_missing, return_counts=True)
    else:
        cum_missing_mask_arr = np.zeros((X.shape[0],), dtype=bool)
        X_non_missing = X
        XX, xx_xounts = get_unique_values(X_non_missing, [np.nan], return_counts=True)

    if X_non_missing.shape[0] == 0:
        dtype_str = "missing"
        dtype_str1 = "missing"

    if XX.shape[0] == X_non_missing.shape[0]:
        unique_values_column_flag = True
    else:
        unique_values_column_flag = False

    if XX.shape[0] == 1 or dtype_str == "missing":  # XX.shape[0]=0 is when column is full of Nans
        constant_column_flag = True
    else:
        constant_column_flag = False

    dtypes_cnt_dict = {}
    dtypes_cnt_dict["missing"] = X.shape[0] - X_non_missing.shape[0]
    dtypes_cnt_dict["char_str"] = 0
    dtypes_cnt_dict["date_str"] = 0
    dtypes_cnt_dict["date_datetime"] = 0
    dtypes_cnt_dict["int_str"] = 0
    dtypes_cnt_dict["float_str"] = 0
    dtypes_cnt_dict["float_num"] = 0
    dtypes_cnt_dict["float_int_num"] = 0
    dtypes_cnt_dict["int_num"] = 0
    dtypes_cnt_dict["boolean"] = 0
    dtypes_cnt_dict["Unknown"] = 0

    dtypes_valueslist_dict = {}
    dtypes_valueslist_dict["missing"] = missing_reference_values_exist_list
    dtypes_valueslist_dict["char_str"] = []
    dtypes_valueslist_dict["date_str"] = []
    dtypes_valueslist_dict["date_datetime"] = []
    dtypes_valueslist_dict["int_str"] = []
    dtypes_valueslist_dict["float_str"] = []
    dtypes_valueslist_dict["float_num"] = []
    dtypes_valueslist_dict["float_int_num"] = []
    dtypes_valueslist_dict["int_num"] = []
    dtypes_valueslist_dict["boolean"] = []
    dtypes_valueslist_dict["Unknown"] = []

    dtypes_weighted_cnt_dict = {}
    dtypes_weighted_cnt_dict["missing"] = X.shape[0] - X_non_missing.shape[0]
    dtypes_weighted_cnt_dict["char_str"] = 0
    dtypes_weighted_cnt_dict["date_str"] = 0
    dtypes_weighted_cnt_dict["date_datetime"] = 0
    dtypes_weighted_cnt_dict["int_str"] = 0
    dtypes_weighted_cnt_dict["float_str"] = 0
    dtypes_weighted_cnt_dict["float_num"] = 0
    dtypes_weighted_cnt_dict["float_int_num"] = 0
    dtypes_weighted_cnt_dict["int_num"] = 0
    dtypes_weighted_cnt_dict["boolean"] = 0
    dtypes_weighted_cnt_dict["Unknown"] = 0

    start_missing_string_values_list = []
    weird_new_missing_values_list = []

    dtype_str3_stop_flag = False
    weird_new_missing_values_list3 = []
    start_missing_string_values_list3 = []
    dtype_str3_limit = 2
    dtype_str_found = "missing"  # initialize the value before checking the types

    if debug:
        dtype_start_time = time.time()
        logger.debug("numpy_whatis():" + "Start finding dtype on" + str(XX.shape[0]) + " rows")

    for i in range(XX.shape[0]):
        elt = XX[i]
        dtype_str3 = None
        # if elt not in missing_values_set: #missing_values_list:
        if isinstance(elt, six.string_types):  # this is a string
            if (
                found_nonmissing_flag
                and (elt == "" or (len(elt) == 1 and not elt.isalnum()))
                and elt not in weird_new_missing_values_list
            ):
                missing_values_list.append(elt)
                weird_new_missing_values_list.append(elt)

                break
            dtype_str = "char_str"  # by default a string of characters
            dtype_str_found = "char_str"

            if not dtype_str3_stop_flag:
                weird_new_missing_values_list3 = weird_new_missing_values_list

            if isint(elt) and "." not in elt:
                dtype_str = "int_str"
                dtype_str_found = "int_str"
                if not found_int_str_flag and not found_float_str_flag and found_string_flag:
                    start_missing_string_values_list = XX[0:i].tolist()
                found_int_str_flag = True
                found_nonmissing_flag = True

            if isfloat(elt) and "." in elt:
                dtype_str = "float_str"
                dtype_str_found = "float_str"
                if not found_int_str_flag and not found_float_str_flag and found_string_flag:
                    start_missing_string_values_list = XX[0:i].tolist()
                found_float_str_flag = True
                found_nonmissing_flag = True

            if dtype_str == "char_str":
                found_string_flag = True
                # a string in a float_str or int_str column can be treated as missing value
                if found_float_str_flag or found_int_str_flag:
                    if elt not in start_missing_string_values_list:  # new_missing_values_list:
                        start_missing_string_values_list.append(elt)

        else:
            if isinstance(elt, float):
                if elt.is_integer():
                    dtype_str_found = "float_int_num"
                    found_nonmissing_flag = True
                    if dtype_str != "float_num":  # if I found at least one float_num stick to it
                        dtype_str = "float_int_num"

                else:
                    dtype_str_found = "float_num"
                    dtype_str = "float_num"  # if I find at least one float that is not integer stick to this type
                    found_nonmissing_flag = True

            if type(elt) is int or isinstance(elt, np.integer) or isinstance(elt, numbers.Integral):
                dtype_str_found = "int_num"
                dtype_str = "int_num"
                found_nonmissing_flag = True

            if "bool" in str(type(elt)) or isinstance(elt, np.bool_):
                dtype_str_found = "boolean"
                dtype_str = "boolean"
                found_nonmissing_flag = True

            if (
                "date" in str(type(elt)).lower()
                or "time" in str(type(elt)).lower()
                or isinstance(elt, datetime.date)
                or isinstance(elt, pd.Timestamp)
            ):
                dtype_str_found = "date_datetime"
                dtype_str = "date_datetime"
                found_nonmissing_flag = True

        if not dtype_str3_stop_flag:
            dtype_str3 = dtype_str
        dtypes_cnt_dict[dtype_str_found] += 1
        dtypes_valueslist_dict[dtype_str_found].append(elt)
        dtypes_weighted_cnt_dict[dtype_str_found] += xx_xounts[i]

        if (
            dtype_str3 == "char_str"
            and dtypes_cnt_dict[dtype_str3] > dtype_str3_limit
            and (dtypes_cnt_dict["missing"] > 0 or weird_new_missing_values_list3)
        ):  # found at least one missing value
            dtype_str3_stop_flag = True
        elif (
            dtype_str3 == "float_str"
            and dtypes_cnt_dict[dtype_str3] > dtype_str3_limit
            and (dtypes_cnt_dict["missing"] > 0 or weird_new_missing_values_list3)
        ):  # found at least one missing value
            dtype_str3_stop_flag = True

    if debug:
        logger.debug(
            "numpy_whatis():"
            + "Ending finding dtype on"
            + str(XX.shape[0])
            + " rows"
            + "\nelapsed_time: numpy_isin_elapsed_end(s): "
            + str(time.time() - dtype_start_time)
        )

    # if the column consists of both floats and integers strings treat all as floats strings
    if found_float_str_flag and found_int_str_flag:
        dtype_str = "float_str"

    # type priorities: char_str > float_str > int_str
    dtypes_found_list = []
    start_missing_string_values_list_flag = False
    for dtype_str_found in dtypes_cnt_dict.keys():
        if dtypes_cnt_dict[dtype_str_found] > 0 and dtype_str_found != "missing":
            dtypes_found_list.append(dtype_str_found)
    if len(dtypes_found_list) == 0:
        if dtypes_cnt_dict["missing"] > 0:  # check if there are only missing values
            dtype_str1 = "missing"
        else:
            dtype_str1 = "Unknown"
    elif len(dtypes_found_list) == 1:  # only one type was found excluding missing values
        dtype_str1 = dtypes_found_list[0]
    else:  # more than one types were found in column
        if "char_str" in dtypes_found_list:
            # if a string was found along with string numbers then it can either be a missing value
            # or entire column is strings
            dtype_str1 = "char_str"
            if dtypes_cnt_dict["char_str"] == 1 or weird_new_missing_values_list:
                if "float_str" in dtypes_found_list:
                    dtype_str1 = "float_str"
                    start_missing_string_values_list_flag = True
                elif "int_str" in dtypes_found_list:
                    dtype_str1 = "int_str"
                    start_missing_string_values_list_flag = True
        elif "float_str" in dtypes_found_list:
            dtype_str1 = "float_str"
        if "float_num" in dtypes_found_list:
            dtype_str1 = "float_num"

    if use_dtype_str1_flag:
        dtype_str_final = dtype_str1
    else:
        start_missing_string_values_list_flag = True
        dtype_str_final = dtype_str

    if start_missing_string_values_list_flag:
        new_missing_values_list = (
            missing_reference_values_exist_list + start_missing_string_values_list + weird_new_missing_values_list
        )
    else:
        new_missing_values_list = missing_reference_values_exist_list + weird_new_missing_values_list

    check_limit = min(XX.shape[0], 50)

    if debug:
        logger.debug("numpy_whatis():" + "Starting checking datetime property  on" + str(check_limit) + " rows")
        datetime_start_time = time.time()

    datetime_column_flag = FCplus.is_column_string_in_datetime_format(XX[list(range(check_limit))]) and (
        dtype_str == "char_str" or dtype_str == "date_datetime"
    )

    if debug:
        logger.debug(
            "numpy_whatis():"
            + "Ending checking datetime property  on"
            + str(check_limit)
            + " rows"
            + "\nelapsed_time(s): "
            + str(time.time() - datetime_start_time)
        )

    check_limit = min(X_non_missing.shape[0], 50)
    if debug:
        logger.debug("numpy_whatis():" + "Starting checking monotonic property  on " + str(check_limit) + " rows")
        monotonic_start_time = time.time()

    monotonic_column_flag = False
    if False:  # do not check monotonic property for the time being
        monotonic_column_flag = numpy_is_column_monotonic_increasing(
            X_non_missing[list(range(check_limit))]
        ) or numpy_is_column_monotonic_decreasing(X_non_missing[list(range(check_limit))])

    if debug:
        logger.debug(
            "numpy_whatis():"
            + "Ending checking monotonic property on "
            + str(check_limit)
            + " rows"
            + "\nelapsed_time(s): "
            + str(time.time() - monotonic_start_time)
        )

    if debug:
        logger.debug("numpy_whatis():" + "Starting checking contiguous property  on " + str(check_limit) + " rows")
        contiguous_start_time = time.time()

    contiguous_column_flag = False
    if False:  # do not check contiguous property for the time being
        if dtype_str == "int_num" and unique_values_column_flag:
            # check if these integers are contiguous
            X_non_missing_sorted = np.sort(X_non_missing)
            X_non_missing_sorted_diff = np.diff(X_non_missing_sorted)
            if np.all(X_non_missing_sorted_diff == X_non_missing_sorted_diff[0]):
                contiguous_column_flag = True

        # max_elt = np.max(X_non_missing)
        # min_elt = np.min(X_non_missing)
        # diff=max_elt-min_elt
        # if diff == X_non_missing.shape[0]-1: #this is a consecutive set of integers
        #     contiguous_column_flag=True

    if debug:
        logger.debug(
            "numpy_whatis():"
            + "Ending checking contiguous property on "
            + str(check_limit)
            + " rows"
            + "\nelapsed_time(s): "
            + str(time.time() - contiguous_start_time)
        )

    if debug:
        logger.debug("numpy_whatis():Ending_" + "\nelapsed_time(s): " + str(time.time() - start_time))

    if return_stats_flag:
        stats_dict = {}
        stats_dict["dtype_str"] = dtype_str_final
        stats_dict["missing_values"] = new_missing_values_list
        stats_dict["unique_values"] = XX
        stats_dict["unique_values_counts"] = xx_xounts
        stats_dict["missing_mask"] = cum_missing_mask_arr
        stats_dict["dtypes_cnt"] = dtypes_cnt_dict
        stats_dict["dtypes_weighted_cnt_dict"] = dtypes_weighted_cnt_dict
        stats_dict["weird_new_missing_values_list"] = weird_new_missing_values_list
        stats_dict["unique_values_column_flag"] = unique_values_column_flag
        stats_dict["constant_column_flag"] = constant_column_flag
        stats_dict["datetime_column_flag"] = datetime_column_flag
        stats_dict["monotonic_column_flag"] = monotonic_column_flag
        stats_dict["contiguous_column_flag"] = contiguous_column_flag

        return new_missing_values_list, dtype_str_final, stats_dict
    else:
        return new_missing_values_list, dtype_str_final


def numpy_get_categories(X, cat_indices, missing_values_list, categories_list2=None):
    if categories_list2 is None:
        categories_list2 = []
    if X.ndim == 1:
        num_cols = 1
    else:
        num_cols = X.shape[1]
    for j in range(num_cols):
        if j in cat_indices:
            if num_cols == 1:
                CC = X
            else:
                CC = X[:, j]
            misslist, dtype_str, column_stats_dict = numpy_whatis(CC, missing_values_list, return_stats_flag=True)
            column_train_labels = column_stats_dict["unique_values"]
            if dtype_str == "char_str":
                for i, str_elt in enumerate(column_train_labels):
                    if not pd.isnull(str_elt) and str_elt not in misslist and not str_elt.isalnum():
                        column_train_labels[i] = compress_string(column_train_labels[i])
            column_train_labels_list = column_train_labels.tolist()
            categories_list2.append(column_train_labels_list)
    return categories_list2


def numpy_remove_second_dim(X):
    Y = X
    if Y.ndim > 1 and Y.shape[1] == 1:
        Y = Y.reshape(
            -1,
        )
    return Y


def isint(value):
    """
    Returns true if argument is integer/float or a string representing an integer/float

    :param value: value to be tested
    :return: true or false
    """
    try:
        int(value)
        return True
    except ValueError:
        return False


def numpy_is_column_monotonic_increasing(column):
    try:
        dt = pd.to_datetime(column)
        result = dt.is_monotonic_increasing
        return result
    except Exception as e:
        return False


def numpy_is_column_monotonic_decreasing(column):
    try:
        dt = pd.to_datetime(column)
        result = dt.is_monotonic_decreasing
        return result
    except Exception as e:
        return False


def numpy_isintstr(X, missing_values_reference_list=None):
    """
    Returns true if a 1-d numpy array consists of ints/floats or
    strings that represent ints/floats, excluding the missing values

    :param X: 1-d numpy array of strings or ints/floats
    :param missing_values_reference_list: list of missing values
    :return: true or false
    """
    if missing_values_reference_list is None:
        l_missing_values_reference_list = []
    else:
        l_missing_values_reference_list = missing_values_reference_list

    flag = True
    for i in range(X.shape[0]):
        if X[i] not in l_missing_values_reference_list:
            if isint(X[i]):  # if we find at least one entry that does not look like int return false
                flag = False
    return flag


def numpy_compute_missing_indicator(X, missing_values_list, stop_at_one_missing_value_flag=False, debug=False):
    missing_masks_list = []
    missing_reference_values_exist_list = []

    if debug:
        row_limit = min(X.shape[0], 50)
        logger.debug("numpy_compute_missing_indicator(): Column: " + str(X[list(range(row_limit))]) + "\n\n")

    for i, missing_value in enumerate(missing_values_list):
        if debug:
            numpy_isin_start = time.time()
            logger.debug("\n\nnumpy_compute_missing_indicator():Checking for missing_value=" + str(missing_value))

        missing_mask = numpy_isin(X, [missing_value])

        missing_value_found = False
        if np.any(missing_mask):
            missing_value_found = True
            missing_reference_values_exist_list.append(missing_value)
            missing_masks_list.append(missing_mask)
            if stop_at_one_missing_value_flag:
                break

        if debug:
            logger.debug(
                "numpy_compute_missing_indicator():"
                + "missing_value="
                + str(missing_value)
                + " found: "
                + str(missing_value_found)
                + "\nelapsed_time: numpy_isin_elapsed_end(s): "
                + str(time.time() - numpy_isin_start)
            )

    if missing_masks_list:
        for i, missing_mask_arr in enumerate(missing_masks_list):
            if i == 0:
                cum_missing_mask_arr = missing_mask_arr
            else:
                cum_missing_mask_arr = cum_missing_mask_arr | missing_mask_arr
    else:
        cum_missing_mask_arr = np.zeros((X.shape[0],), dtype=bool)
        missing_masks_list = list(cum_missing_mask_arr)
        missing_reference_values_exist_list = []

    return cum_missing_mask_arr, missing_masks_list, missing_reference_values_exist_list


def numpy_isin(X, values_reference_list, debug=False):
    """
    Returns a boolean mask indicating where X values match the values of the reference list
    :param X:
    :param values_reference_list:
    :return:
    """

    if debug:
        limit = min(X.shape[0], 50)
        logger.debug("Starting numpy_isin(): Starting\n X column: " + str(X[list(range(limit))]) + "\n")
        start_time = time.time()

    l_X = numpy_flatten_column(X)
    l_values_reference_list = values_reference_list

    nan_missing_mask = pd.isnull(l_values_reference_list)
    if np.any(nan_missing_mask):  # if nan is in the values reference list
        non_nan_values_reference_list = list(np.asarray(l_values_reference_list)[~nan_missing_mask])
        if not non_nan_values_reference_list:  # nan was the only reference value
            result = pd.isnull(l_X)
        else:
            nan_cond = pd.isnull(l_X)
            set_non_nan_values_reference_list = set(non_nan_values_reference_list)

            if debug:
                logger.debug(l_X[list(range(limit))])
                logger.debug(set_non_nan_values_reference_list)

            non_nan_cond = indicator_mask(set_non_nan_values_reference_list, l_X)
            result = nan_cond | non_nan_cond
    else:
        set_reference_values_list_col = set(l_values_reference_list)
        result = indicator_mask(set_reference_values_list_col, l_X)

    if debug:
        np_isin_time = time.time()
        logger.debug("Ending numpy_isin(): Ending, elapsed time (s)" + str(np_isin_time - start_time))

    return result


def indicator_mask(reference_set: set, l):
    is_in_reference = np.vectorize(lambda value: value in reference_set, otypes=[bool])
    return is_in_reference(l)


def get_unique_values(
    y: np.ndarray,
    exclusion_list=None,
    return_index=False,
    return_inverse=False,
    return_counts=False,
    fast_str_conversion_flag=True,
):
    """
    Gets unique values of a numpy array excluding values in a list (this was implemented
    to address the case where np.unique() crashes on arrays containing np.Nan values)
    :param y: input numpy array
    :param exclusion_list: list of excluded values
    :return: list of unique values
    """

    if exclusion_list is None or not exclusion_list:
        # result = np.unique(y, return_index,return_inverse,return_counts)
        y_to_process = y
    else:
        included_mask = ~numpy_isin(y, exclusion_list)
        # included_indices = list(np.where(included_mask)[0])
        # y1=y[included_mask]
        # y2=y[included_indices]
        # result=np.unique(y[included_mask],return_index,return_inverse,return_counts)
        y_to_process = y[included_mask]
    try:
        result = np.unique(y_to_process, return_index, return_inverse, return_counts)
    except Exception as e:
        if "not supported between instances of" in str(e) and "'str'" in str(e):
            logger.warning(str(e) + ", Converting to string column")
            y_to_process = numpy_column_float2str(X=y_to_process, fast_conversion_flag=fast_str_conversion_flag)
            result = np.unique(y_to_process, return_index, return_inverse, return_counts)
        else:
            WML_raise_exception(exception_obj=e, exception_trace_flag=True)
    # except Exception as e:
    #     if 'not supported between instances of' in str(e) and '\'str\'' in str(e):
    #         logger.warning(str(e) + ', Converting to string column')
    #         result=np.unique(y_to_process.astype(str), return_counts=True)
    #     else:
    #         WML_raise_exception(exception_obj=e, exception_trace_flag=True)

    # # unique_array = np.unique(y)
    # # if exclusion_list is not None and exclusion_list:
    # #     unique_list = []
    # #     exclusion_mask = np.isin(unique_array, exclusion_list)
    # # #     indices=np.where(exclusion_mask)
    # # #     result=unique_array[indices]
    # #     for i in range(unique_array.shape[0]):
    # #         if not exclusion_mask[i]:
    # #             unique_list.append(unique_array[i])
    # #     result=np.asarray(unique_list)
    # # else:
    # #     result=unique_array
    #
    # if exclusion_list is None or not exclusion_list:
    #     result=np.unique(y)
    # else:
    #     unique_list=[]
    #     for i in range(y.shape[0]):
    #         if y[i] not in exclusion_list and y[i] not in unique_list:
    #            unique_list.append(y[i])
    #     result = np.asarray(unique_list)

    return result


def isfloat(value):
    """
    Returns true if argument is float or a string representing an float

    :param value: value to be tested
    :return: true or false
    """
    try:
        float(value)
        return True
    # handle strings and None types
    except (ValueError, TypeError):
        return False


def numpy_column_float2str(X, fast_conversion_flag=True):
    if fast_conversion_flag:
        Y = X.astype(str)
    else:
        Y = X
        for i in range(X.shape[0]):
            elt = Y[i]
            if not isinstance(elt, str):
                if pd.isnull(elt):
                    elt_i = "?"
                else:
                    if isinstance(elt, float):
                        if elt.is_integer():
                            elt_i = str(int(elt))
                        else:
                            elt_i = str(elt)
                    else:
                        elt_i = str(elt)
                Y[i] = elt_i
    return Y


def WML_raise_exception(
    error_message=None,
    exception_type="Exception",
    exception_obj=None,
    exception_trace_flag=False,
    logger_error_flag=True,
):
    if error_message is None:
        error_message = "Exception raised!\n"
    if exception_obj is not None and exception_trace_flag:
        trace_error_message = "".join(traceback.format_exception(exception_obj))
        error_message = error_message + trace_error_message + "\nExiting ..."

    if logger_error_flag:
        logger.error(error_message)

    # sys.exit(error_message)

    if exception_type == "FileNotFoundError":
        raise FileNotFoundError(error_message)
    elif exception_type == "ValueError":
        raise ValueError(error_message)
    elif exception_type == "TypeError":
        raise TypeError(error_message)
    else:  # exception_type is None or exception_type == 'Exception':
        raise Exception(error_message)


class FCplus:
    @staticmethod
    def is_column_datetime(column):
        result = numpy_is_column_datetime(column)
        return result

    @staticmethod
    def is_num_column_categorical(dfc, uni_max=100, uni_ratio=0.1):
        try:
            uni = np.unique(dfc)
        except Exception as e:
            logger.error("exception ", exc_info=e)
            logger.debug(type(dfc))
            logger.debug(dfc)
            logger.debug(dfc.isnull().any())
            raise e
        r = float(len(uni)) / float(len(dfc))
        return (len(uni) < uni_max and r < uni_ratio) or len(uni) == 2 or (len(uni) < 5) and len(dfc) < 30

    @staticmethod
    def is_column_categorical(y: np.ndarray, missing_values_reference_list=None) -> bool:
        # if isinstance(y, (list, pd.core.series.Series, np.ndarray, pd.DataFrame)):
        #         pass
        flag = False
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )

        misslist, dtype_str = numpy_whatis(y, l_missing_values_reference_list)
        if dtype_str == "int_str" or dtype_str == "char_str":
            flag = True
        if dtype_str == "int_num" or dtype_str == "float_int_num":
            if misslist:
                ylist = []
                for i in range(y.shape[0]):
                    if y[i] not in misslist:
                        ylist.append(y[i])
                y1 = np.asarray(ylist)
                # flag = FC.is_categorical(y1)
                flag = FCplus.is_num_column_categorical(y1, uni_max=100, uni_ratio=0.1)
            else:
                # flag=FC.is_categorical(y)
                flag = FCplus.is_num_column_categorical(y, uni_max=100, uni_ratio=0.1)
        return flag

    @staticmethod
    def find_categorical_columns(X: np.ndarray, missing_values_reference_list=None):
        output_index_list = []
        if X.ndim == 1:
            if FCplus.is_column_categorical(
                X.reshape(-1, 1), missing_values_reference_list=missing_values_reference_list
            ):
                output_index_list.append(0)
        else:
            for j in range(X.shape[1]):
                if FCplus.is_column_categorical(X[:, j], missing_values_reference_list=missing_values_reference_list):
                    output_index_list.append(j)
        return output_index_list

    @staticmethod
    def is_numerical(y: np.ndarray, missing_values_reference_list=None) -> bool:
        return not FCplus.is_column_categorical(y, missing_values_reference_list=missing_values_reference_list)

    @staticmethod
    def find_numerical_columns(X: np.ndarray, missing_values_reference_list=None):
        output_index_list = []
        if X.ndim == 1:
            if FCplus.is_numerical(X.reshape(-1, 1), missing_values_reference_list=missing_values_reference_list):
                output_index_list.append(0)
        else:
            for j in range(X.shape[1]):
                if FCplus.is_numerical(X[:, j], missing_values_reference_list=missing_values_reference_list):
                    output_index_list.append(j)
        return output_index_list

    @staticmethod
    def is_dataset_for_classification(y: np.ndarray, X: np.ndarray = None, missing_values_reference_list=None) -> bool:
        return FCplus.is_column_categorical(y, missing_values_reference_list=missing_values_reference_list)

    @staticmethod
    def is_dataset_preprocessed(X: np.ndarray, missing_values_reference_list=None) -> bool:
        flag = True
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )
        if X.ndim == 1:
            misslist, dtype_str = numpy_whatis(X, l_missing_values_reference_list)
            # if there are either missing values or non-numeric values
            # consider the dataset non-preprocessed
            if misslist or dtype_str == "char_str" or dtype_str == "int_str" or dtype_str == "float_str":
                flag = False
        else:
            for j in range(X.shape[1]):
                misslist, dtype_str = numpy_whatis(X[:, j], l_missing_values_reference_list)
                # if there are either missing values or non-numeric values on at least one column
                # consider the dataset non-preprocessed
                if misslist or dtype_str == "char_str" or dtype_str == "int_str" or dtype_str == "float_str":
                    flag = False
                    break
        return flag

    @staticmethod
    def is_dataset_missing(X: np.ndarray, missing_values_reference_list=None) -> bool:
        flag = True

        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )

        if X.ndim == 1:
            # if at least one column has missing values consider the dataset "missing"
            misslist, dtype_str = numpy_whatis(X, l_missing_values_reference_list)
            if misslist:
                flag = False
        else:
            for j in range(X.shape[1]):
                # if at least one column has missing values consider the dataset "missing"
                misslist, dtype_str = numpy_whatis(X[:, j], l_missing_values_reference_list)
                if misslist:
                    flag = False
                    break
        return flag

    @staticmethod
    def get_dataset_missing_columns(X: np.ndarray, missing_values_reference_list=None):
        flag = True
        missing_columns = []
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )
        if X.ndim == 1:
            misslist, dtype_str = numpy_whatis(X, l_missing_values_reference_list)
            if misslist:
                missing_columns.append(0)
        else:
            for j in range(X.shape[1]):
                # if at least one column has missing values consider the dataset "missing"
                misslist, dtype_str = numpy_whatis(X[:, j], l_missing_values_reference_list)
                if misslist:
                    missing_columns.append(j)
        return missing_columns

    @staticmethod
    def is_dataset_numeric(X: np.ndarray, missing_values_reference_list=None) -> bool:
        flag = True
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )
        if X.ndim == 1:
            misslist, dtype_str = numpy_whatis(X, l_missing_values_reference_list)
            if dtype_str == "char_str" or dtype_str == "int_str" or dtype_str == "float_str":
                flag = False
        else:
            for j in range(X.shape[1]):
                misslist, dtype_str = numpy_whatis(X[:, j], l_missing_values_reference_list)
                if dtype_str == "char_str" or dtype_str == "int_str" or dtype_str == "float_str":
                    flag = False
                    break
        return flag

    @staticmethod
    def get_dataset_non_numeric_columns(X: np.ndarray, missing_values_reference_list=None):
        string_columns = []
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )
        if X.ndim == 1:
            misslist, dtype_str = numpy_whatis(X, l_missing_values_reference_list)
            if dtype_str == "char_str" or dtype_str == "int_str" or dtype_str == "float_str":
                string_columns.append(0)
        else:
            for j in range(X.shape[1]):
                misslist, dtype_str = numpy_whatis(X[:, j], l_missing_values_reference_list)
                if dtype_str == "char_str" or dtype_str == "int_str" or dtype_str == "float_str":
                    string_columns.append(j)
        return string_columns

    @staticmethod
    def check_statistics(dfc, mean_value, std_value, min_value, max_value, num_stds, unit_factors_list):
        X = dfc.values
        for k in unit_factors_list:
            flag = True
            if X.ndim == 1:
                for i in range(X.shape[0]):
                    elt = k * X[i]
                    if abs((elt - mean_value)) > num_stds * std_value or elt > max_value or elt < min_value:
                        flag = False
                        break
            else:
                for i in range(X.shape[0]):
                    if not flag:  # if at least one column was found not to satisfy distribution try the next unit
                        break
                    for j in range(X.shape[1]):
                        elt = k * X[i, j]
                        if abs((elt - mean_value)) > num_stds * std_value or elt > max_value or elt < min_value:
                            flag = False
                            break
            if flag:
                break
        return flag

    @staticmethod
    def is_column_missing(column, missing_values_reference_list=None) -> bool:
        flag = True
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )
        misslist, dtype_str = numpy_whatis(column, l_missing_values_reference_list)
        if not misslist:  # no missing value found
            flag = False
        return flag

    # @staticmethod
    # def is_column_increasing(column) -> bool:
    #     if FCplus.is_column_not_categorical(pd.DataFrame(column)):
    #         return is_sorted_increasing(column)
    #     else:
    #         return False
    #
    # @staticmethod
    # def is_column_decreasing(column) -> bool:
    #     if FCplus.is_column_not_categorical(pd.DataFrame(column)):
    #         return is_sorted_decreasing(column)
    #     else:
    #         return False

    @staticmethod
    def is_column_sex(dfc):
        flag = False

        # if str(dfc[0].dtype) == 'object':
        if isinstance(dfc.values[0, 0], str):
            values = dfc[0].unique()
            if len(values) == 2 and (
                (values[0].lower() == "male" and values[1].lower() == "female")
                or (values[1].lower() == "male" and values[0].lower() == "female")
                or (values[0].lower() == "m" and values[1].lower() == "f")
                or (values[1].lower() == "m" and values[0].lower() == "f")
            ):
                flag = True
        return flag

    # @staticmethod
    # def is_column_timestamp(series):
    #     flag = pd.core.dtypes.common.is_datetime64_ns_dtype(series) | pd.core.dtypes.common.is_timedelta64_ns_dtype(series)
    #     return flag

    @staticmethod
    def is_column_height(dfc):
        """
        Infers whether column represents height based on US statistics
        Men: 69.1 inches mean and 2.9 inches std
        Women: 63.7 inches and 2.7 inches std
        :param dfc:
        :return:
        """
        # Men
        if isinstance(dfc.values[0, 0], str):
            return False

        men_mean_height = 69.1
        men_std_height = 2.9

        women_mean_height = 63.7
        women_std_height = 2.7

        human_mean_height = (men_mean_height + women_mean_height) / 2
        human_std_height = (1 / 4) * (men_std_height * men_std_height + women_std_height * women_std_height)
        human_min_height = 21.49
        human_max_height = 107.08

        unit_factors_list = [1, 2.54]  # check for both inches and cm
        num_deviations = 3

        flag = FCplus.check_statistics(
            dfc,
            human_mean_height,
            human_std_height,
            human_min_height,
            human_max_height,
            num_deviations,
            unit_factors_list,
        )

        return flag

    @staticmethod
    def is_column_weight(dfc):
        """
        Infers whether column represents weight based on US statistics
        :param dfc:
        :return:
        """
        # Men

        # if not str(dfc[0].dtype) in DataUtils.FloatDataTypes():
        #     return False

        if isinstance(dfc.values[0, 0], str):
            return False

        human_mean_weight = 177.9
        human_std_weight = 40.9
        human_min_weight = 102
        human_max_weight = 300

        unit_factors_list = [1, 0.453592]  # check for both lbs and kg
        num_deviations = 3

        flag = FCplus.check_statistics(
            dfc,
            human_mean_weight,
            human_std_weight,
            human_min_weight,
            human_max_weight,
            num_deviations,
            unit_factors_list,
        )

        return flag

    @staticmethod
    def is_column_age(dfc, missing_values_reference_list=None):
        """
        Infers whether column represents weight based on US statistics
        :param dfc:
        :return:
        """
        # Men

        # if not str(dfc[0].dtype) in DataUtils.FloatDataTypes():
        #     return False
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )

        miss_values, dtype_str = numpy_whatis(dfc.values[0], l_missing_values_reference_list)
        # or not "int" in dtype_str: #dtype_str can be int_num, float_int_num or int_str
        if isinstance(dfc.values[0, 0], str) or not dtype_str == "int_num":
            return False
        # if str(dfc.values[0].dtype) == 'object':
        #     if not dfc.values[0].isinteger():
        #         return False
        # flag = isint(dfc.values[0,0])
        #
        # if not str(dfc[0].dtype) == 'int64' and not dtype_str == "int_str":
        #     return False

        human_mean_age = 40
        human_std_age = 20
        human_min_age = 0
        human_max_age = 100

        unit_factors_list = [1]
        num_deviations = 2

        flag = FCplus.check_statistics(
            dfc, human_mean_age, human_std_age, human_min_age, human_max_age, num_deviations, unit_factors_list
        )

        return flag

    @staticmethod
    def is_column_timestamp(series):
        if isinstance(series.values[0, 0], str):
            return False

        flag = pd.core.dtypes.common.is_datetime64_ns_dtype(series) | pd.core.dtypes.common.is_timedelta64_ns_dtype(
            series
        )
        return flag

    @staticmethod
    def is_column_positive(dfc) -> bool:
        if isinstance(dfc.values[0, 0], str):
            return False

        return FC.is_positive(dfc)

    @staticmethod
    def is_column_non_negative(dfc):
        if isinstance(dfc.values[0, 0], str):
            return False

        return FC.is_non_negative(dfc)

    @staticmethod
    def is_column_not_all_non_negative(dfc):
        if isinstance(dfc.values[0, 0], str):
            return False

        return FC.is_not_all_non_negative(dfc)

    @staticmethod
    def is_column_lt80pc_unique_int(dfc):
        if isinstance(dfc.values[0, 0], str):
            return False

        return FC.is_lt80pc_unique_int(dfc)

    @staticmethod
    def is_column_constant(dfc):
        return FC.is_constant(dfc)

    @staticmethod
    def is_column_categorical_mult_cats(dfc, missing_values_reference_list=None):
        return (
            FCplus.is_column_categorical(dfc, missing_values_reference_list=missing_values_reference_list)
            and len(np.unique(dfc)) > 2
        )

    @staticmethod
    def is_column_not_categorical(dfc, missing_values_reference_list=None):
        return not FCplus.is_column_categorical(dfc, missing_values_reference_list=missing_values_reference_list)

    @staticmethod
    def is_column_string(column, missing_values_reference_list=None):
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )

        misslist, dtype_str = numpy_whatis(column, l_missing_values_reference_list)
        if dtype_str == "char_str":
            flag = True
        else:
            flag = False
        return flag

    @staticmethod
    def is_column_string_in_datetime_format(column):
        return FC.is_string_in_datetime_format(column)

    @staticmethod
    def is_column_epoch(column):
        return FC.is_epoch(column)

    @staticmethod
    def is_column_longitude(column, name=None):
        return FC.is_longitude(column, name)

    @staticmethod
    def is_column_latitude(column, name=None):
        return FC.is_latitude(column, name)

    @staticmethod
    def is_column_distance(column):
        return FC.is_distance(column)

    @staticmethod
    def getClasses(y: np.ndarray, exclude_missing_class_flag=True, missing_values_reference_list=None):
        l_missing_values_reference_list = setValueOrDefault(
            missing_values_reference_list, global_missing_values_reference_list
        )

        misslist, dtype_str = numpy_whatis(y, l_missing_values_reference_list)
        seq = []
        if misslist and exclude_missing_class_flag:
            for i in range(y.shape[0]):
                if y[i] not in misslist:
                    seq.append(y[i])
        else:
            for i in range(y.shape[0]):
                seq.append(y[i])

        n = len(seq)
        classes_list = [(clas, float(count)) for clas, count in Counter(seq).items()]

        return classes_list


def numpy_is_column_datetime(column):
    try:
        # pd.to_datetime(column).astype(np.int64)
        pd.to_datetime(column)
        return True
    except Exception as e:
        return False


class DatasetS:
    def __init__(self, dataframe):
        self.df = dataframe

    # Returns a new dataset
    def AddNewColumns(self, fun):
        colnames = list(self.df.columns)
        # if 'label' in colnames:
        # todo
        #    colnames.remove('label')
        for i in range(0, len(colnames)):
            # todo
            self.df = self.df.withColumn("log" + colnames[i], fun(self.df[colnames[i]]))

    @staticmethod
    def GetTargetType(y):
        if FC.is_not_categorical(y):
            return "regression"
        else:
            return "classification"


def get_constant_column_indices_missingvalues(X, missing_values_reference_list=None, reverse_flag=False):
    """
    Returns the constant column indices of a numpy array and the non-constant ones if reverse_flag=True
    :param X: input array
    :param missing_values_reference_list: missing values in input array
    :param reverse_flag: if True, the non-constant column indices are returned
    :return:
    """
    const_indices = []
    if X.ndim == 1:
        num_cols = 1
    else:
        num_cols = X.shape[1]

    for j in range(num_cols):
        if num_cols == 1:
            Xcol = X
        else:
            Xcol = X[:, j]
        Xcol_unique = get_unique_values(Xcol, exclusion_list=missing_values_reference_list)
        if len(Xcol_unique) == 1:
            const_indices.append(j)

    if reverse_flag:
        all_indices = list(range(num_cols))
        non_const_indices = []
        for elt in all_indices:
            if elt not in const_indices:
                non_const_indices.append(elt)
        return non_const_indices
    else:
        return const_indices


def transform_row(transformer, row):
    if len(row) == 0:
        r = row
    else:
        array = np.array([row])
        # case of an empty row
        if 0 in array.shape:
            r = row
        else:
            r = transformer.transform(array)[0]
    return r
