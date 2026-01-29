################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2024-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import lale.docstrings
import lale.operators

import autoai_libs.cognito.transforms.transform_utils

from ._common_schemas import (
    _hparam_fs_cols_ids_must_keep,
    _hparams_fs_additional_col_count_to_keep,
    _hparams_fs_ptype,
)


class _FS1Impl:
    def __init__(self, **hyperparams):
        self._wrapped_model = autoai_libs.cognito.transforms.transform_utils.FS1(**hyperparams)

    def fit(self, X, y=None, **fit_params):
        self._wrapped_model.fit(X, y)
        return self

    def transform(self, X):
        result = self._wrapped_model.transform(X)
        try:
            if hasattr(self, "column_names") and len(self.column_names) == len(self._wrapped_model.cols_to_keep_final_):
                self.column_names = [self.column_names[i] for i in self._wrapped_model.cols_to_keep_final_]
            if hasattr(self, "column_dtypes") and len(self.column_dtypes) == len(
                self._wrapped_model.cols_to_keep_final_
            ):
                self.column_dtypes = [self.column_dtypes[i] for i in self._wrapped_model.cols_to_keep_final_]
        except Exception:  # nosec
            pass
        return result

    def set_meta_data(self, meta_data_dict):
        if "column_names" in meta_data_dict.keys():
            self.column_names = meta_data_dict["column_names"]
        if "column_dtypes" in meta_data_dict.keys():
            self.column_dtypes = meta_data_dict["column_dtypes"]

    def get_transform_meta_output(self):
        return_dict = {}
        if hasattr(self, "column_names"):
            return_dict["column_names"] = self.column_names
        if hasattr(self, "column_dtypes"):
            return_dict["column_dtypes"] = self.column_dtypes
        return return_dict


_hyperparams_schema = {
    "allOf": [
        {
            "description": "This first object lists all constructor arguments with their types, but omits constraints for conditional hyperparameters.",
            "type": "object",
            "additionalProperties": False,
            "required": ["cols_ids_must_keep", "additional_col_count_to_keep", "ptype"],
            "relevantToOptimizer": [],
            "properties": {
                "cols_ids_must_keep": _hparam_fs_cols_ids_must_keep,
                "additional_col_count_to_keep": _hparams_fs_additional_col_count_to_keep,
                "ptype": _hparams_fs_ptype,
            },
        }
    ]
}

_input_fit_schema = {
    "type": "object",
    "required": ["X", "y"],
    "additionalProperties": False,
    "properties": {
        "X": {
            "type": "array",
            "items": {"type": "array", "items": {"laleType": "Any"}},
        },
        "y": {
            "type": "array",
            "items": {"laleType": "Any"},
            "description": "Target values.",
        },
    },
}

_input_transform_schema = {
    "type": "object",
    "required": ["X"],
    "additionalProperties": False,
    "properties": {"X": {"type": "array", "items": {"type": "array", "items": {"laleType": "Any"}}}},
}

_output_transform_schema = {
    "description": "Features; the outer array is over samples.",
    "type": "array",
    "items": {"type": "array", "items": {"laleType": "Any"}},
}

_combined_schemas = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": """Operator from `autoai_libs`_. Feature selection, type 1 (using pairwise correlation between each feature and target.)

.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.fs1.html",
    "import_from": "autoai_libs.cognito.transforms.transform_utils",
    "type": "object",
    "tags": {"pre": [], "op": ["transformer"], "post": []},
    "properties": {
        "hyperparams": _hyperparams_schema,
        "input_fit": _input_fit_schema,
        "input_transform": _input_transform_schema,
        "output_transform": _output_transform_schema,
    },
}


FS1 = lale.operators.make_operator(_FS1Impl, _combined_schemas)

lale.docstrings.set_docstrings(FS1)
