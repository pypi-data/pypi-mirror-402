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

import autoai_libs.transformers.exportable

from ._common_schemas import _hparam_activate_flag_unmodified, _hparam_dtypes_list


class _FloatStr2FloatImpl:
    def __init__(self, **hyperparams):
        self._wrapped_model = autoai_libs.transformers.exportable.FloatStr2Float(**hyperparams)

    def fit(self, X, y=None):
        self._wrapped_model.fit(X, y)
        return self

    def transform(self, X):
        return self._wrapped_model.transform(X)


_hyperparams_schema = {
    "allOf": [
        {
            "description": "This first object lists all constructor arguments with their types, but omits constraints for conditional hyperparameters.",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "dtypes_list",
                "missing_values_reference_list",
                "activate_flag",
            ],
            "relevantToOptimizer": [],
            "properties": {
                "dtypes_list": _hparam_dtypes_list,
                "missing_values_reference_list": {
                    "anyOf": [
                        {
                            "description": "Reference list of missing values in the input numpy array X.",
                            "type": "array",
                            "items": {"laleType": "Any"},
                        },
                        {
                            "description": "If None, default to ``['?', '', '-', np.nan]``.",
                            "enum": [None],
                        },
                    ],
                    "default": None,
                },
                "activate_flag": _hparam_activate_flag_unmodified,
            },
        }
    ]
}

_input_fit_schema = {
    "type": "object",
    "required": ["X"],
    "additionalProperties": False,
    "properties": {
        "X": {  # Handles 1-D arrays as well
            "anyOf": [
                {"type": "array", "items": {"laleType": "Any"}},
                {
                    "type": "array",
                    "items": {"type": "array", "items": {"laleType": "Any"}},
                },
            ]
        },
        "y": {"laleType": "Any"},
    },
}

_input_transform_schema = {
    "type": "object",
    "required": ["X"],
    "additionalProperties": False,
    "properties": {
        "X": {  # Handles 1-D arrays as well
            "anyOf": [
                {"type": "array", "items": {"laleType": "Any"}},
                {
                    "type": "array",
                    "items": {"type": "array", "items": {"laleType": "Any"}},
                },
            ]
        }
    },
}

_output_transform_schema = {
    "description": "Features; the outer array is over samples.",
    "anyOf": [
        {"type": "array", "items": {"laleType": "Any"}},
        {"type": "array", "items": {"type": "array", "items": {"laleType": "Any"}}},
    ],
}

_combined_schemas = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": """Operator from `autoai_libs`_. Replaces columns of strings that represent floats (type ``float_str`` in dtypes_list) to columns of floats and replaces their missing values with np.nan.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.float_str2_float.html",
    "import_from": "autoai_libs.transformers.exportable",
    "type": "object",
    "tags": {"pre": [], "op": ["transformer"], "post": []},
    "properties": {
        "hyperparams": _hyperparams_schema,
        "input_fit": _input_fit_schema,
        "input_transform": _input_transform_schema,
        "output_transform": _output_transform_schema,
    },
}


FloatStr2Float = lale.operators.make_operator(_FloatStr2FloatImpl, _combined_schemas)

lale.docstrings.set_docstrings(FloatStr2Float)
