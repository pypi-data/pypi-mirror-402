################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2022-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################


import numpy as np
import pandas as pd


def calculate_IQR(data: pd.DataFrame, lower_q=0.25, upper_q=0.75) -> tuple:
    """
    Calculates the interquartile-range (IQR).

    Parameters
    ----------
    data: Pandas DataFrame, required.
    lower_q: lower quantile level. Default value 0.25, optional.
    upper_q: upper quantile level. Default value 0.75, optional.

    Returns
    -------
    (Q1, Q3, IQR): tuple of quartiles and IQR.
    """
    q3 = data.quantile(upper_q)
    q1 = data.quantile(lower_q)
    iqr = q3 - q1

    return q1, q3, iqr


def calculate_boundaries(data: pd.DataFrame, lower_q=0.25, upper_q=0.75, IQR_adjusted=True) -> tuple:
    """
    Calculates the boundaries for outliers detection using either IQR or adjusted IQR (skewness adjustment).
    The mean of quartile skewness, and octile skewness is used for medcouple (MC) approximation.
    MC is not used directly due to computation complexity (O(N**2)).

    Parameters
    ----------
    data: Pandas DataFrame, required.
    lower_q: lower quantile level. Default value 0.25, optional.
    upper_q: upper quantile level. Default value 0.75, optional.
    IQR_adjusted: bool, use adjusted for skewness IQR definition (based on medcouple approximation). Default value True, optional

    Returns
    -------
    (lower_limit, upper_limit): tuple of bounds (lower and upper)
    """

    q1, q3, iqr = calculate_IQR(data, lower_q, upper_q)

    if IQR_adjusted:
        # https://wis.kuleuven.be/stat/robust/papers/2008/adjboxplot-revision.pdf
        q2 = data.quantile(0.5)
        q875 = data.quantile(0.875)
        q125 = data.quantile(0.125)
        q_s = ((q3 - q2) - (q2 - q1)) / (q3 - q1)
        o_s = ((q875 - q2) - (q2 - q125)) / (q875 - q125)
        mc_approximation = (q_s + o_s) / 2
        a_positive = -3.5
        a_negative = -4
        b_positive = 4
        b_negative = 3.5

        if isinstance(mc_approximation, pd.Series):
            a = pd.Series(
                data=[a_positive if mc >= 0 else a_negative for mc in mc_approximation], index=mc_approximation.index
            )
            b = pd.Series(
                data=[b_positive if mc >= 0 else b_negative for mc in mc_approximation], index=mc_approximation.index
            )
        else:
            a = a_positive if mc_approximation >= 0 else a_negative
            b = b_positive if mc_approximation >= 0 else b_negative

        return q1 - 1.5 * np.exp(a * mc_approximation) * iqr, q3 + 1.5 * np.exp(b * mc_approximation) * iqr
    else:
        return q1 - (1.5 * iqr), q3 + (1.5 * iqr)


def remove_outliers(
    data: pd.DataFrame, columns: list, lower_q=0.25, upper_q=0.75, replace_with_nan=True, IQR_adjusted=True
) -> pd.DataFrame:
    """
    Detects, removes or replaces with NaNs numerical outliers. The IQR (interquartile range) method is used.
    Non-numeric columns are skipped.

    Parameters
    ----------
    data: pd.DataFrame, required
    columns: list, columns names, required
    lower_q: float, lower quantile level. Default value 0.25, optional
    upper_q: float, upper quantile level. Default value 0.75, optional
    replace_with_nan: bool, replace outliers with NaNs instead of dropping. Default value True, optional

    Returns
    -------
    data: pd.DataFrame
    """

    if isinstance(data, pd.DataFrame):
        # get numeric columns
        numerics = ["int16", "int32", "int64", "float16", "float32", "float64"]
        numeric_cols = data.select_dtypes(include=numerics).columns
        columns = list(set(columns) & set(numeric_cols))

        if len(columns) > 0:
            lower_range, upper_range = calculate_boundaries(data[columns], lower_q, upper_q, IQR_adjusted)
            constrain = np.logical_or(data[columns] < lower_range, data[columns] > upper_range)

            if replace_with_nan:
                data.loc[:, columns] = data[columns].where(~constrain, np.nan)
            else:
                mask = constrain.any(axis=1)
                data.drop(mask[mask].index, inplace=True, axis=0)
        else:
            raise ValueError("Numerical columns names are missing.")
    else:
        raise TypeError("Data type {0} is not supported. Use Pandas DataFrame.".format(type(data)))

    return data
