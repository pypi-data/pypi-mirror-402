################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################


__all__ = ["make_holdout_split", "numpy_remove_missing_target_rows"]

from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from numpy import array
from sklearn.model_selection import train_test_split

from autoai_libs.utils.exportable_utils import global_missing_values_reference_list, numpy_compute_missing_indicator


def make_holdout_split(
    *,
    x: array,
    y: array,
    learning_type: str,
    test_size: float,
    random_state: int = 33,
    fairness_info: Dict[str, list] = None,
    return_only_holdout: bool = True,
    time_ordered_data: bool = False,
) -> Union[Tuple[array, array, array], Tuple[array, array, array, array, array, array]]:
    """
        This function is dedicated to have a backward compatibility for previous internal holdout split.
        It uses all old methods to retrieve a holdout dataset. The new approach is to have a houldout dataset
        defined and passed by the user.

    Parameters
    ----------
    x: array, required
        A numpy array (training one)

    y: array, required
        A numpy array (target column)

    learning_type: str, required
        One of: ['classification', 'binary', 'multiclass' , 'regression']

    test_size: float: required
        Float between 0 and 1. Indicates how big should be a houldout dataset.

    random_state: int, optional
        Default 33.

    fairness_info: dict, optional
        Dictionary with fairness metrics configuration parameters:
                fairness_info = {
                    "protected_attributes": [
                        {"feature": "Age", "reference_group": [[20, 40]]}
                    ],
                    "favorable_labels": ["No Risk"]}

    return_only_holdout: bool, optional
        Default True. If set to False it will return also training dataet and train indices.

    time_ordered_data: bool, optional
        Default False. Should be passed if data is a time series and its ordering has to be preserved.
        Passing the argument results in splittlin the dataset into training and testing one without shuffling.

    Returns
    -------
    Numpy arrays:
        x_train, x_holdout, y_train, y_holdout, train_indices, holdout_indices

        if return_only_holdout:
            x_holdout, y_holdout, holdout_indices
    """

    if learning_type == "classification" or learning_type == "binary" or learning_type == "multiclass":
        while True:
            try:
                # Note: Split for fairness
                if fairness_info is not None:
                    from lale.lib.aif360.util import fair_stratified_train_test_split

                    (
                        x_train,
                        x_holdout,
                        y_train,
                        y_holdout,
                        train_indices,
                        holdout_indices,
                    ) = fair_stratified_train_test_split(
                        x,
                        y,
                        range(len(x)),
                        favorable_labels=fairness_info["favorable_labels"],
                        protected_attributes=fairness_info["protected_attributes"],
                        test_size=test_size,
                        random_state=random_state,
                    )

                # Note: normal classification split
                else:
                    (x_train, x_holdout, y_train, y_holdout, train_indices, holdout_indices) = train_test_split(
                        x, y, range(len(x)), test_size=test_size, random_state=random_state, stratify=y, shuffle=True
                    )

            except ValueError as e:
                if ("test_size" in str(e)) and ("should be greater or equal to the number of classes" in str(e)):
                    raise ValueError(
                        "The number of classes is greater than the number of rows reserved "
                        "as holdout data. To resolve this, either increase the proportion of "
                        "the holdout data, or increase the size of the data set."
                    ) from e

                # Note: try to do shuffled split one more time
                elif "The least populated class in y has only" in str(e):
                    # 'ValueError: The least populated class in y has only 1 member, which is too few.
                    # The minimum number of groups for any class cannot be less than 2.'
                    (x_train, x_holdout, y_train, y_holdout, train_indices, holdout_indices) = train_test_split(
                        x, y, range(len(x)), test_size=test_size, random_state=random_state, stratify=None, shuffle=True
                    )

                else:
                    raise e

            # Note: when we have at least 2 classes in train and holdout target column, finish split
            if len(np.unique(y_train)) >= 2 and len(np.unique(y_holdout)) >= 2:
                break

            if test_size >= 0.5:
                raise ValueError("Label distribution is too imbalanced to generate a holdout set")

            test_size *= 2

    # Note: Split for regression problems. Time series experiment are currently only allowed for regression tasks
    else:
        shuffle = False if time_ordered_data else True

        (x_train, x_holdout, y_train, y_holdout, train_indices, holdout_indices) = train_test_split(
            x, y, range(len(x)), test_size=test_size, random_state=random_state, shuffle=shuffle
        )

    if return_only_holdout:
        return x_holdout, y_holdout, holdout_indices

    else:
        return x_train, x_holdout, y_train, y_holdout, train_indices, holdout_indices


def numpy_split_on_target_values(
    y: Union[pd.DataFrame, np.array],
    X: Union[pd.DataFrame, np.array] = None,
    ref_values: Union[list, set] = None,
    return_indices: bool = False,
):
    X_ref_values_target_rows = None
    X_non_ref_values_target_rows = None
    if ref_values is None or not ref_values:
        if X is not None:
            return X
        else:
            return y

    ref_values_target_indices = ref_values_indicator(y=y, ref_values=ref_values, output_type="list")

    if ref_values_target_indices:
        non_ref_values_target_indices = filter_list(
            full_list=list(range(y.shape[0])), exclude_list=ref_values_target_indices
        )

        y_non_ref_values_target_rows = y[non_ref_values_target_indices]
        y_ref_values_target_rows = y[ref_values_target_indices]

        if X is not None:
            if isinstance(X, pd.DataFrame):
                X_non_ref_values_target_rows = X.iloc[non_ref_values_target_indices].values
                X_ref_values_target_rows = X.iloc[ref_values_target_indices].values

            else:
                X_non_ref_values_target_rows = X[non_ref_values_target_indices, :]
                X_ref_values_target_rows = X[ref_values_target_indices, :]

    else:
        non_ref_values_target_indices = list(range(y.shape[0]))
        y_non_ref_values_target_rows = y
        y_ref_values_target_rows = None
        if X is not None:
            X_non_ref_values_target_rows = X
            X_ref_values_target_rows = None

    if X is not None:
        if return_indices:
            return (
                X_ref_values_target_rows,
                y_ref_values_target_rows,
                X_non_ref_values_target_rows,
                y_non_ref_values_target_rows,
                ref_values_target_indices,
                non_ref_values_target_indices,
            )

        else:
            return (
                X_ref_values_target_rows,
                y_ref_values_target_rows,
                X_non_ref_values_target_rows,
                y_non_ref_values_target_rows,
            )

    else:
        if return_indices:
            return (
                y_ref_values_target_rows,
                y_non_ref_values_target_rows,
                ref_values_target_indices,
                non_ref_values_target_indices,
            )

        else:
            return y_ref_values_target_rows, y_non_ref_values_target_rows


def ref_values_indicator(
    y: Union[pd.DataFrame, np.array],
    ref_values: Union[list, set] = None,
    output_non_reference_indicator_flag: bool = False,
    output_type: str = "list",
) -> np.array:
    """
        Returns indices of rows with reference values (or non-reference values) of a pandas dataframe or numpy array

    Parameters
    ----------
    y: pd.DataFrame or np.array, required

    ref_values: list or set, optional
        Vector containing the reference values.

    output_non_reference_indicator_flag: bool, optional
        Outputs the non-reference values of target.

    output_type: str, optional
        Type of the returned indicator variable: list of indices ('list'), binary vector ('int')
        or boolean vector ('bool'). Default is 'list'

    Returns
    -------
    List of indices or binary vector or boolean vector.

    Example
    -------
    >>> y = ['one', 'two', 'three', 'four']
    >>> ref_values = ['two', 'one']
    >>> ref_values_indicator(y, ref_values)
    ... [0, 1]
    >>> ref_values_indicator(y, ref_values, output_type='int')
    ... [1, 1, 0, 0]
    >>> ref_values_indicator(y, ref_values, output_type='bool')
    ... [True,  True, False, False]
    >>> ref_values_indicator(y, ref_values, output_type='bool', output_non_reference_indicator_flag=True)
    ... [False, False,  True,  True]
    """
    if not (isinstance(y, pd.DataFrame) or isinstance(y, np.ndarray) or isinstance(y, pd.Series)):
        raise ValueError(f"y is not of type: pd.DataFrame or np.array. y type: {type(y)}")

    if ref_values is None or not list(ref_values):
        return []

    if output_type == "int":
        ref_values_indicator = np.zeros(y.shape[0], dtype=int)
        ref_values_indicator[np.isin(y, ref_values, invert=output_non_reference_indicator_flag)] = 1

    elif output_type == "bool":
        ref_values_indicator = np.isin(y, ref_values, invert=output_non_reference_indicator_flag)

    else:
        ref_values_indicator = np.where(np.isin(y, ref_values, invert=output_non_reference_indicator_flag))[0]

    return ref_values_indicator.tolist()


def filter_list(full_list: list, exclude_list: list) -> list:
    """
        Return a list that results from remove elements from a full list that are in exclude_list

    Parameters
    ----------
    full_list: list, required
        Original list of objects.

    exclude_list: list, required
        List with objects to exclude from original list.

    Returns
    -------
    List created from original one but without excluded objects.
    """
    s = set(exclude_list)
    return list((x for x in full_list if x not in s))


def missing_values_indicator(
    y: Union[pd.DataFrame, np.ndarray],
    missing_values_reference_list: Optional[Sequence[str]] = None,
    output_non_missing_indicator_flag: Optional[bool] = False,
    output_type: Optional[str] = "list",
) -> np.ndarray | list:
    """
    Returns indices of rows with missing values or non-missing values of a pandas dataframe or array

    Parameters
    ----------
    y: pd.DataFrame or np.ndarray

    missing_values_reference_list: list, optional
        List containing the values considered as missing. Default 'global_missing_values_reference_list'.

    output_non_missing_indicator_flag: bool, optional
        Indicator if outputs the non-missing values of target. Default False.

    output_type: str, optional
        Type of the returned indicator variable: list of indices ('list'), binary vector ('int')
        or boolean vector ('bool'). Default is 'list'

    Returns
    -------
    Numpy ndarray or list with missing values indicator
    """
    if missing_values_reference_list is None:
        missing_values_reference_list = global_missing_values_reference_list

    if isinstance(y, pd.DataFrame):
        y_arr = y.values
    else:
        y_arr = y

    (missing_indicator_mask, missing_indicator_mask_list, missing_values_list) = numpy_compute_missing_indicator(
        y_arr, missing_values_reference_list, stop_at_one_missing_value_flag=False
    )

    if output_non_missing_indicator_flag:
        indicator_mask = np.invert(missing_indicator_mask)

    else:
        indicator_mask = missing_indicator_mask

    if output_type == "bool":
        missing_values_indicator = indicator_mask

    elif output_type == "int":
        missing_values_indicator = indicator_mask.astype(np.int64)

    else:
        missing_values_indicator = np.where(indicator_mask)[0].tolist()

    return missing_values_indicator


def numpy_remove_missing_target_rows(
    y: Union[pd.DataFrame, np.ndarray],
    X: Union[pd.DataFrame, np.ndarray] = None,
    missing_values_reference_list: Optional[Sequence[str]] = None,
):
    """
    Removes missing target rows.

    Parameters
    ----------
    y: np.ndarray

    X: np.ndarray

    missing_values_reference_list: list, optional
        List containing the values considered as missing. Default 'global_missing_values_reference_list'.

    Returns
    -------
    Tuple of np.ndarrays.
    y_non_missing_target_rows, non_missing_target_rows, y_missing_target_rows, missing_target_rows

    or

    (X_non_missing_target_rows, y_non_missing_target_rows, non_missing_target_rows,
                X_missing_target_rows, y_missing_target_rows, missing_target_rows)
    """
    X_non_missing_target_rows = []
    X_missing_target_rows = []

    missing_target_rows = missing_values_indicator(
        y=y,
        missing_values_reference_list=missing_values_reference_list,
        output_non_missing_indicator_flag=False,
        output_type="list",
    )
    if missing_target_rows:
        non_missing_target_rows = filter_list(list(range(y.shape[0])), missing_target_rows)

        y_non_missing_target_rows = y[non_missing_target_rows]
        y_missing_target_rows = y[missing_target_rows]

        if X is not None:
            X_non_missing_target_rows = X[non_missing_target_rows, :]
            X_missing_target_rows = X[missing_target_rows, :]

    else:
        non_missing_target_rows = list(range(y.shape[0]))
        y_non_missing_target_rows = y
        y_missing_target_rows = None
        X_non_missing_target_rows = X
        X_missing_target_rows = None

    if X is not None:
        return (
            X_non_missing_target_rows,
            y_non_missing_target_rows,
            non_missing_target_rows,
            X_missing_target_rows,
            y_missing_target_rows,
            missing_target_rows,
        )
    else:
        return y_non_missing_target_rows, non_missing_target_rows, y_missing_target_rows, missing_target_rows
