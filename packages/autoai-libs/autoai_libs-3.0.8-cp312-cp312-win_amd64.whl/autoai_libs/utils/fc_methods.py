################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2020-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################


import logging

import numpy as np
import pandas as pd

from autoai_libs.utils.data_utils import DataUtils

logger = logging.getLogger("autoai_libs")


def is_positive(dfc):
    return np.min(dfc) > 0


def is_non_negative(dfc):
    return np.min(dfc) >= 0


def is_not_all_non_negative(dfc):
    return not is_non_negative(dfc)


def is_categorical(dfc):
    try:
        uni = np.unique(dfc)
    except Exception as e:
        logger.error("exception ", exc_info=e)

        logger.debug(type(dfc))
        logger.debug(dfc)
        logger.debug(dfc.isnull().any())
        raise e
    # return dfc.dtype in DataUtils.IntDataTypes() and len(uni) < 20 and len(uni)/len(dfc) < 0.1
    # return len(uni) < 20 and len(uni)/len(dfc) < 0.1
    r = float(len(uni)) / float(len(dfc))
    return (len(uni) < 20 and r < 0.1) or len(uni) == 2


def is_lt80pc_unique_int(dfc):
    try:
        uni = np.unique(dfc)
    except Exception as e:
        logger.error("exception ", exc_info=e)
        logger.debug(type(dfc))
        logger.debug(dfc)
        logger.debug(dfc.isnull().any())
        raise e
    # return dfc.dtype in DataUtils.IntDataTypes() and len(uni) < 20 and len(uni)/len(dfc) < 0.1
    # return len(uni) < 20 and len(uni)/len(dfc) < 0.1
    r = float(len(uni)) / float(len(dfc))
    return r < 0.8


def is_constant(dfc):
    uni = np.unique(dfc)
    if len(uni) == 1:
        return True
    else:
        return False


def is_categorical_mult_cats(dfc):
    return is_categorical(dfc) and len(np.unique(dfc)) > 2


def is_not_categorical(dfc):
    return not is_categorical(dfc)


def is_string_in_datetime_format(column):
    if not str(column.dtype) in ["object", "datetime64[ns]"]:
        return False
    try:
        pd.to_datetime(column)
        return True
    except:
        return False


def is_epoch(column):
    if str(column.dtype) == "int64" and (
        str(column.name).endswith("__dt")
        or str(column.name).lower().__contains__("date")
        or str(column.name).lower().__contains__("time")
        or str(column.name).lower().__contains__("epoch")
    ):
        return True
    return False


def is_longitude(column, name=None):
    if name is None:
        column_name = str(column.name)
    else:
        column_name = name

    if (isinstance(column[0], float) or str(column.dtype) in DataUtils.FloatDataTypes()) and (
        "longitude" in column_name.split("(")[0] or "long" in column_name.split("(")[0]
    ):
        # range_fun = lambda x: x <= 180 and x >= -180
        def lon_range_fun(x):
            return x <= 180 and x >= -180

        if column.sample(1000, replace=True).apply(lon_range_fun).all():
            return True

    return False


def is_latitude(column, name=None):
    if name is None:
        column_name = str(column.name)
    else:
        column_name = name
    if (isinstance(column[0], float) or str(column.dtype) in DataUtils.FloatDataTypes()) and (
        "latitude" in column_name.split("(")[0] or "lat" in column_name.split("(")[0]
    ):

        def lat_range_fun(x):
            return x <= 90 and x >= -90

        if column.sample(1000, replace=True).apply(lat_range_fun).all():
            return True

    return False


def is_distance(column):
    if str(column.dtype) in DataUtils.NumericDataTypes() and "distance" in str(column.name).split("(")[0]:
        return True
    return False
