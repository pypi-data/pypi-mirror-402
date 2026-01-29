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


class _NumpyReplaceUnknownValuesImpl:
    def __init__(self, **hyperparams):
        self._wrapped_model = autoai_libs.transformers.exportable.NumpyReplaceUnknownValues(**hyperparams)

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
                "known_values_list",
                "filling_values",
                "missing_values_reference_list",
                "filling_values_list",
            ],
            "relevantToOptimizer": [],
            "properties": {
                "known_values_list": {
                    "description": "Reference list of lists of known values for each column.",
                    "anyOf": [
                        {"type": "array", "items": {"laleType": "Any"}},
                        {"enum": [None]},
                    ],
                    "transient": True,
                    "default": None,
                },
                "filling_values": {
                    "description": "Special value assigned to unknown values.",
                    "laleType": "Any",
                    "default": None,
                },
                "missing_values_reference_list": {
                    "description": "Reference list of missing values.",
                    "anyOf": [
                        {"type": "array", "items": {"laleType": "Any"}},
                        {"enum": [None]},
                    ],
                    "default": None,
                },
                "filling_values_list": {
                    "description": "list of special value assigned to unknown values.",
                    "anyOf": [
                        {"type": "array", "items": {"laleType": "Any"}},
                        {"enum": [None]},
                    ],
                    "default": None,
                },
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
    "description": """Operator from `autoai_libs`_. Given a numpy array and a reference list of known values for each column, replaces values that are not part of a reference list with a special value (typically np.nan). This is typically used to remove labels for columns in a test dataset that have not been seen in the corresponding columns of the training dataset.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.numpy_replace_unknown_values.html",
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


NumpyReplaceUnknownValues = lale.operators.make_operator(_NumpyReplaceUnknownValuesImpl, _combined_schemas)

lale.docstrings.set_docstrings(NumpyReplaceUnknownValues)
