################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################


__all__ = ["sample", "numpy_sample_rows"]

import numbers
from typing import Optional, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def sample(
    X: Union[pd.DataFrame, np.array],
    y: Optional[Union[pd.DataFrame, np.array]] = None,
    test_size: Optional[Union[int, float]] = None,
    random_state: Optional[int] = 33,
    shuffle: Optional[bool] = True,
    stratify_flag: Optional[bool] = True,
):
    """
        Performs sampling of data matrix X based on labels y using stratified sampling and shuffling options

    Parameters
    ----------
    X: pd.DataFrame or np.array, required
        Data matrix to sample from.

    y: pd.DataFrame or np.array, optional
        Labels vector. If None, no stratification takes place.

    test_size: int or float, optional
        Either integer between 0 and number of rows of 'X' or float between 0 and 1.

    random_state: int, optional
        Random seed, default 33.

    shuffle: bool, optional
        Determine whether sampled data will be shuffled with respect to 'X' (default True).
        Cannot be False while 'stratify_flag' is True.

    stratify_flag: bool, optional
        If True, perform stratified sampling based on labels vector 'y'. Only in effect if 'y' is not None.

    Returns
    -------
    Sampled version of 'X' and sampled indices of 'X'. If 'y' is not None, sampled version of 'X', 'y'
    and sampled indices of 'X'
    """
    num_rows = X.shape[0]
    indices = np.arange(num_rows)

    # Note: check if 'test_size' parameter is correct, it should be between 0 and 1 (float)
    # or between 0 and max num of 'X' rows (int)
    if test_size is not None:
        if isinstance(test_size, float):
            if not (0 < test_size < 1):
                raise ValueError(
                    f"Parameter 'test_size' is of type: {type(test_size)}."
                    f"It should be between 0 and 1. Its current value is: {test_size}"
                )

        if isinstance(test_size, int) or isinstance(test_size, np.integer) or isinstance(test_size, numbers.Integral):
            if not (0 < test_size < num_rows):
                raise ValueError(
                    f"Parameter 'test_size' is of type: {type(test_size)}."
                    f"It should be between 0 and maximum number of 'X' rows. "
                    f"Its current value is: {test_size}. Maximum number of rows is: {num_rows}"
                )
        # --- end note

        # Perform sampling
        if y is None:  # not stratified as 'y' is not defined
            _, X, _, indices = train_test_split(
                X, indices, test_size=test_size, random_state=random_state, shuffle=shuffle
            )

        else:  # try to perform stratify sampling
            try:
                _, X, _, y, _, indices = train_test_split(
                    X,
                    y,
                    indices,
                    test_size=test_size,
                    random_state=random_state,
                    shuffle=True,
                    stratify=y if stratify_flag else None,
                )

            except Exception as e:
                if (y if stratify_flag else None) is not None:
                    if "member" in str(e) or "infinity" in str(e):
                        _, X, _, y, _, ind_test = train_test_split(
                            X, y, indices, test_size=test_size, random_state=random_state, shuffle=True, stratify=None
                        )

                else:
                    raise e

    if y is not None:
        return X, y, indices
    else:
        return X, indices


def numpy_sample_rows(
    X: Union[pd.DataFrame, np.array],
    y: Optional[Union[pd.DataFrame, np.array]],
    train_sample_rows_test_size: Optional[Union[int, float]],
    learning_type: str,
    random_state: Optional[int] = 33,
    return_sampled_indices: bool = True,
):
    """
        Performs sampling of data matrix X based on labels y.

    Parameters
    ----------
    X: pd.DataFrame or np.array, required
        Data matrix to sample from.

    y: pd.DataFrame or np.array, optional
        Labels vector. If None, no stratification takes place.

    train_sample_rows_test_size: int or float, optional
        Either integer between 0 and number of rows of 'X' or float between 0 and 1.

    learning_type: str, required
        One of ['classification', 'regression']

    random_state: int, optional
        Random seed, default 33.

    return_sampled_indices: bool, optional
        If True, returns sampled indices. Default True.

    Returns
    -------
    Sampled version of 'X', 'y' and sampled indices of 'X' if 'return_sampled_indices' is True.
    """
    if train_sample_rows_test_size is not None and train_sample_rows_test_size > 0:
        X, y, sampled_indices = sample(
            X=X,
            y=y,
            test_size=train_sample_rows_test_size,
            random_state=random_state,
            stratify_flag=True if learning_type == "classification" else False,
        )
    else:
        sampled_indices = list(range(y.shape[0]))

    if return_sampled_indices:
        return X, y, sampled_indices

    else:
        return X, y
