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

import autoai_libs.transformers.text_transformers

from ._common_schemas import _hparam_activate_flag_features, _hparam_column_headers_list


# This is currently needed just to hide get_params so that lale does not call clone
# when doing a defensive copy
class _TfIdfTransformerImpl:
    def __init__(self, **hyperparams):
        if hyperparams.get("column_headers_list", None) is None:
            hyperparams["column_headers_list"] = []
        if hyperparams.get("text_processing_options", None) is None:
            hyperparams["text_processing_options"] = []

        self._wrapped_model = autoai_libs.transformers.text_transformers.TfIdfTransformer(**hyperparams)

    def fit(self, X, y=None):
        self._wrapped_model.fit(X, y)
        return self

    def transform(self, X):
        return self._wrapped_model.transform(X)


_hyperparams_schema = {
    "allOf": [
        {
            "description": """This transformer converts text columns in the dataset to its embedding vectors.
It then performs SVD on those vectors for dimensionality reduction.""",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "output_dim",
                "column_headers_list",
                "min_count",
                "text_columns",
                "drop_columns",
                "activate_flag",
                "text_processing_options",
            ],
            "relevantToOptimizer": [],
            "properties": {
                "output_dim": {
                    "description": "Number of numeric features generated per text column.",
                    "type": "integer",
                    "default": 30,
                },
                "column_headers_list": _hparam_column_headers_list(
                    description="""Column headers passed from autoai_core. The new feature's column headers are
appended to this."""
                ),
                "drop_columns": {
                    "description": "If true, drops text columns",
                    "type": "boolean",
                    "default": False,
                },
                "activate_flag": _hparam_activate_flag_features,
                "min_count": {
                    "description": "TF-IDF model ignores all the words whose frequency is less than this.",
                    "type": "integer",
                    "default": 5,
                },
                "text_columns": {
                    "description": "If passed, then TF-IDF features are applied to these columns.",
                    "anyOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "array", "items": {"type": "integer"}},
                        {"enum": [None]},
                    ],
                    "default": None,
                },
                "text_processing_options": {
                    "description": "The parameter values to initialize this transformer are passed through this dictionary.",
                    "anyOf": [
                        {"type": "object"},
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
    "description": """Operator from `autoai_libs`_. Converts text columns to numeric features using a combination of TF-IDF and SVD.
.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "import_from": "autoai_libs.transformers.text_transformers",
    "type": "object",
    "tags": {"pre": [], "op": ["transformer"], "post": []},
    "properties": {
        "hyperparams": _hyperparams_schema,
        "input_fit": _input_fit_schema,
        "input_transform": _input_transform_schema,
        "output_transform": _output_transform_schema,
    },
}

TfIdfTransformer = lale.operators.make_operator(_TfIdfTransformerImpl, _combined_schemas)

lale.docstrings.set_docstrings(TfIdfTransformer)
