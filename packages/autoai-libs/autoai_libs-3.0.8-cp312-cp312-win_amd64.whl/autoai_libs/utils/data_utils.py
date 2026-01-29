################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2020-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import logging
import random

import numpy as np

logger = logging.getLogger("autoai_libs")


class DataUtils:
    @staticmethod
    def NumericDataTypes():
        return [
            "intc",
            "intp",
            "int_",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "int8",
            "int16",
            "int32",
            "int64",
            "short",
            "long",
            "longlong",
            "float16",
            "float32",
            "float64",
        ]

    @staticmethod
    def IntDataTypes():
        return [
            "intc",
            "intp",
            "int_",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "int8",
            "int16",
            "int32",
            "int64",
            "short",
            "long",
            "longlong",
        ]

    @staticmethod
    def FloatDataTypes():
        return ["float16", "float32", "float64"]

    @staticmethod
    def get_basic_types(cat):
        if cat == "numeric":
            return DataUtils.NumericDataTypes()
        if cat == "float":
            return DataUtils.FloatDataTypes()
        if cat == "int" or cat == "integer":
            return DataUtils.IntDataTypes()
        return [cat]

    @staticmethod
    def replace_nan_and_inf(col):
        """
        Replace nan and inf frmo pandas DataFrame or Series.
            :param col: pandas DataFrame or Series
        """
        if np.isnan(col).any():
            col = col.replace(np.nan, 0)  # np.nan_to_num(col)
            col = col.replace(np.inf, 0)  # np.nan_to_num(col)
            col = col.replace(-np.inf, 0)
            return col
        if np.isinf(col).any():
            col = col.replace(np.inf, 0)  # np.nan_to_num(col)
            col = col.replace(-np.inf, 0)
            return col

        return col

    @staticmethod
    def all_feats_numeric(df):
        for col in df.columns:
            try:
                if not df[col].dtype in DataUtils.NumericDataTypes():
                    return False
            except Exception as e:
                logger.error("", exc_info=e)
                logger.debug(df.columns)
                logger.debug(df[col])
                raise e
        return True

    @staticmethod
    def get_unique_column_name(proposed_name, existing_name_list):
        while proposed_name in existing_name_list:
            proposed_name = proposed_name + "-" + str(random.randint(0, 9))
        return proposed_name
