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


class _NSFAImpl:
    def __init__(self, **hyperparams):
        self._wrapped_model = autoai_libs.cognito.transforms.transform_utils.NSFA(**hyperparams)

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
            "required": ["significance"],
            "relevantToOptimizer": [],
            "properties": {
                "significance": {
                    "description": "Array with a feature significance values for each column.",
                    "anyOf": [
                        {"type": "array", "items": {"type": "number", "minimum": 0.0}},
                        {
                            "enum": [None],
                            "description": "Passing None will result in some failure to eliminate insignificant data.",
                        },
                    ],
                    "default": None,
                },
                "protected_cols": {
                    "description": "Array with indices of features that are protected by fairness definition.",
                    "anyOf": [
                        {"type": "array", "items": {"type": "integer", "minimum": 0}},
                        {"enum": [None]},
                    ],
                    "default": None,
                },
                "analyzer": {
                    "description": "A tool used to analyse insignificant columns.",
                    "laleType": "Any",
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
        "X": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
        "y": {"laleType": "Any"},
    },
}

_input_transform_schema = {
    "type": "object",
    "required": ["X"],
    "additionalProperties": False,
    "properties": {"X": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}},
}

_output_transform_schema = {
    "description": "Features; the outer array is over samples.",
    "type": "array",
    "items": {"type": "array", "items": {"type": "number"}},
}

_combined_schemas = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": """Operator from `autoai_libs`_. Feature transformation for dimension reduction by significance analysis.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.nsfa.html",
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


NSFA = lale.operators.make_operator(_NSFAImpl, _combined_schemas)

lale.docstrings.set_docstrings(NSFA)
