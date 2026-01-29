################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
import pandas as pd
from onnxruntime_extensions import PyCustomOpDef, onnx_op

from autoai_libs.transformers.date_time.date_time_utils import apply_date_aggregations
from autoai_libs.utils.exportable_utils import (
    compress_str_column,
    numpy_floatstr2float,
    numpy_permute_array,
    numpy_replace_values,
)


@onnx_op(
    op_type="RemoveWhitespaces",
    inputs=[PyCustomOpDef.dt_string, PyCustomOpDef.dt_string],
    outputs=[PyCustomOpDef.dt_string],
)
def op_remove_whitespaces(X: np.ndarray[str], misslist: np.ndarray[str]) -> np.ndarray[str]:
    Y = X.copy()
    for j in range(X.shape[1]):
        Y[:, j] = compress_str_column(X[:, j], misslist, "string")
    return Y


@onnx_op(
    op_type="CompressToHash",
    inputs=[PyCustomOpDef.dt_string, PyCustomOpDef.dt_string],
    outputs=[PyCustomOpDef.dt_double],
)
def op_compress_to_hash(X: np.ndarray[str], misslist: np.ndarray[str]) -> np.ndarray[np.float64]:
    Y = np.empty(X.shape, np.float64)
    for j in range(X.shape[1]):
        Y[:, j] = compress_str_column(X[:, j], misslist, "hash")
    return Y


@onnx_op(
    op_type="ReplaceFloatValues",
    inputs=[PyCustomOpDef.dt_float, PyCustomOpDef.dt_float],
    outputs=[PyCustomOpDef.dt_float],
    attrs={"filling_values": PyCustomOpDef.dt_float, "invert_flag": PyCustomOpDef.dt_string},
)
def op_replace_missing_values_num(
    X: np.ndarray[np.float32], reference_values_list: np.ndarray[float], **kwargs: float | str
) -> np.ndarray[float]:
    invert_flag = bool(kwargs.get("invert_flag", False))
    filling_values = kwargs.get("filling_values", np.nan)
    return numpy_replace_values(
        X, filling_values=filling_values, reference_values_list=list(reference_values_list), invert_flag=invert_flag
    )


@onnx_op(
    op_type="FloatStr2Float",
    inputs=[PyCustomOpDef.dt_string, PyCustomOpDef.dt_string],
    outputs=[PyCustomOpDef.dt_float],
)
def op_floatstr2float(X: np.ndarray[str], missing_values_reference_list: np.ndarray[str]) -> np.ndarray[float]:
    Y = np.empty(X.shape, np.float32)
    for j in range(X.shape[1]):
        Y[:, j] = numpy_floatstr2float(X[:, j], missing_values_reference_list)
    return Y


@onnx_op(
    op_type="PermuteNumericArrays",
    inputs=[PyCustomOpDef.dt_float, PyCustomOpDef.dt_int64],
    outputs=[PyCustomOpDef.dt_float],
    attrs={"axis": PyCustomOpDef.dt_int64},
)
def op_permute_array_num(
    X: np.ndarray[float], permutation_indices: np.ndarray[np.int64], **kwargs: int
) -> np.ndarray[float]:
    axis = kwargs.get("axis", 0)
    return numpy_permute_array(X, permutation_indices=list(permutation_indices), axis=axis)


@onnx_op(
    op_type="ApplyDateAggregations",
    inputs=[PyCustomOpDef.dt_string, PyCustomOpDef.dt_string],
    outputs=[PyCustomOpDef.dt_double],
    attrs={"one_timestamp_type_flag": PyCustomOpDef.dt_string, "float32_processing_flag": PyCustomOpDef.dt_string},
)
def op_apply_date_aggregations(X: np.ndarray[str], options: np.ndarray[str], **kwargs: str) -> np.ndarray[np.float64]:
    one_timestamp_type_flag = bool(kwargs.get("one_timestamp_type_flag", True))
    float32_processing_flag = bool(kwargs.get("float32_processing_flag", True))
    y, _ = apply_date_aggregations(
        X=X,
        date_column_indices=list(range(X.shape[1])),
        options=list(options),
        delete_source_columns=True,
        one_timestamp_type_flag=one_timestamp_type_flag,
        float32_processing_flag=float32_processing_flag,
    )
    return np.where(pd.isna(y), np.nan, y).astype(np.float64)


@onnx_op(
    op_type="CustomTGenGroupByMapping_float64",
    inputs=[PyCustomOpDef.dt_double, PyCustomOpDef.dt_double],
    outputs=[PyCustomOpDef.dt_double],
)
def op_tgen_fun_mapping(X: np.ndarray, aggs: np.ndarray, **kwargs) -> np.ndarray:
    keys = aggs[:, 0]
    vals = aggs[:, 1]

    idx = np.searchsorted(keys, X, side="left")

    return vals[idx]


@onnx_op(
    op_type="CustomTGenGroupByMapping_float32",
    inputs=[PyCustomOpDef.dt_float, PyCustomOpDef.dt_float],
    outputs=[PyCustomOpDef.dt_float],
)
def op_tgen_fun_mapping(X: np.ndarray, aggs: np.ndarray, **kwargs) -> np.ndarray:
    keys = aggs[:, 0]
    vals = aggs[:, 1]

    idx = np.searchsorted(keys, X, side="left")

    return vals[idx]
