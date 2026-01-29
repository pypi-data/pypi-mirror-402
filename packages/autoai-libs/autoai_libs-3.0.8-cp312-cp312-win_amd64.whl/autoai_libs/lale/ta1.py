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
import numpy as np

import autoai_libs.cognito.transforms.transform_utils

from ._common_schemas import (
    _hparam_col_dtypes,
    _hparams_apply_all,
    _hparams_col_as_json_objects,
    _hparams_col_names,
    _hparams_datatypes,
    _hparams_feat_constraints,
    _hparams_fun_pointer,
    _hparams_tgraph,
    _hparams_transformer_name,
)


class _TA1Impl:
    def __init__(self, **hyperparams):
        self._hyperparams = hyperparams

        self._wrapped_model = autoai_libs.cognito.transforms.transform_utils.TA1(**hyperparams)

    def fit(self, X, y=None, **fit_params):
        num_columns = X.shape[1]
        col_dtypes = self._hyperparams["col_dtypes"]

        if len(col_dtypes) < num_columns:
            if hasattr(self, "column_names") and len(self.column_names) == num_columns:
                col_names = self.column_names
            else:
                col_names = self._hyperparams["col_names"]
                for i in range(num_columns - len(col_dtypes)):
                    col_names.append("col" + str(i))
            if hasattr(self, "column_dtypes") and len(self.column_dtypes) == num_columns:
                col_dtypes = self.column_dtypes
            else:
                for i in range(num_columns - len(col_dtypes)):
                    col_dtypes.append(np.float32)
            fit_params["col_names"] = col_names
            fit_params["col_dtypes"] = col_dtypes
        self._wrapped_model.fit(X, y, **fit_params)
        return self

    def transform(self, X):
        result = self._wrapped_model.transform(X)
        return result

    def get_transform_meta_output(self):
        return_meta_data_dict = {}
        if self._wrapped_model.new_column_names_ is not None:
            final_column_names = []
            final_column_names.extend(self._wrapped_model.col_names_)
            final_column_names.extend(self._wrapped_model.new_column_names_)
            return_meta_data_dict["column_names"] = final_column_names
        if self._wrapped_model.new_column_dtypes_ is not None:
            final_column_dtypes = []
            final_column_dtypes.extend(self._wrapped_model.col_dtypes)
            final_column_dtypes.extend(self._wrapped_model.new_column_dtypes_)
            return_meta_data_dict["column_dtypes"] = final_column_dtypes
        return return_meta_data_dict

    def set_meta_data(self, meta_data_dict):
        if "column_names" in meta_data_dict.keys():
            self.column_names = meta_data_dict["column_names"]
        if "column_dtypes" in meta_data_dict.keys():
            self.column_dtypes = meta_data_dict["column_dtypes"]


_hyperparams_schema = {
    "allOf": [
        {
            "description": "This first object lists all constructor arguments with their types, but omits constraints for conditional hyperparameters.",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "fun",
                "name",
                "datatypes",
                "feat_constraints",
                "tgraph",
                "apply_all",
                "col_names",
                "col_dtypes",
                "col_as_json_objects",
            ],
            "relevantToOptimizer": [],
            "properties": {
                "fun": _hparams_fun_pointer(description="The function pointer."),
                "name": _hparams_transformer_name,
                "datatypes": _hparams_datatypes(
                    description="List of datatypes that are valid input to the transformer function (`numeric`, `float`, `int`, `integer`)."
                ),
                "feat_constraints": _hparams_feat_constraints(
                    description="All constraints that must be satisfied by a column to be considered a valid input to this transform."
                ),
                "tgraph": _hparams_tgraph,
                "apply_all": _hparams_apply_all,
                "col_names": _hparams_col_names,
                "col_dtypes": _hparam_col_dtypes,
                "col_as_json_objects": _hparams_col_as_json_objects,
            },
        }
    ]
}

_input_fit_schema = {
    "type": "object",
    "required": ["X"],
    "additionalProperties": False,
    "properties": {
        "X": {
            "type": "array",
            "items": {"type": "array", "items": {"laleType": "Any"}},
        },
        "y": {"laleType": "Any"},
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
    "description": """Operator from `autoai_libs`_. Feature transformation for unary stateless functions, such as square, log, etc.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.ta1.html",
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


TA1 = lale.operators.make_operator(_TA1Impl, _combined_schemas)

lale.docstrings.set_docstrings(TA1)
