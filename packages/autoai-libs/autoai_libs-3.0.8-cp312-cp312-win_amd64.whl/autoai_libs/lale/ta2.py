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


class _TA2Impl:
    def __init__(self, **hyperparams):
        self._wrapped_model = autoai_libs.cognito.transforms.transform_utils.TA2(**hyperparams)

    def fit(self, X, y=None, **fit_params):
        self._wrapped_model.fit(X, y, **fit_params)
        return self

    def transform(self, X):
        result = self._wrapped_model.transform(X)
        return result


_hyperparams_schema = {
    "allOf": [
        {
            "description": "This first object lists all constructor arguments with their types, but omits constraints for conditional hyperparameters.",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "fun",
                "name",
                "datatypes1",
                "feat_constraints1",
                "datatypes2",
                "feat_constraints2",
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
                "datatypes1": _hparams_datatypes(
                    description="List of datatypes that are valid input to the first argument of the transformer function (`numeric`, `float`, `int`, `integer`)."
                ),
                "feat_constraints1": _hparams_feat_constraints(
                    description="All constraints that must be satisfied by a column to be considered a valid first argument to this transform."
                ),
                "datatypes2": _hparams_datatypes(
                    description="List of datatypes that are valid input to the second argument of the transformer function (numeric, float, int, etc.)."
                ),
                "feat_constraints2": _hparams_feat_constraints(
                    description="All constraints that must be satisfied by a column to be considered a valid second argument to this transform."
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
    "description": """Operator from `autoai_libs`_. Feature transformation for binary stateless functions, such as sum or product.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.ta2.html",
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


TA2 = lale.operators.make_operator(_TA2Impl, _combined_schemas)

lale.docstrings.set_docstrings(TA2)
