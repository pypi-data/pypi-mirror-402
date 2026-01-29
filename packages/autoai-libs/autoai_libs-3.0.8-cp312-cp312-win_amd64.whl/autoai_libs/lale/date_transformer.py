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
import pandas as pd

from autoai_libs.transformers.date_time.date_time_transformer import DateTransformer as model_to_be_wrapped

from ._common_schemas import _hparam_activate_flag_active, _hparam_column_headers_list


class _DateTransformerImpl:
    def __init__(self, **hyperparams):
        self._wrapped_model = model_to_be_wrapped(**hyperparams)

    def fit(self, X, y=None):
        if isinstance(X, pd.DataFrame):
            X = X.to_numpy()
        self._wrapped_model.fit(X, y)
        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            X = X.to_numpy()
        return self._wrapped_model.transform(X)


_hyperparams_schema = {
    "allOf": [
        {
            "description": "This first object lists all constructor arguments with their types, but omits constraints for conditional hyperparameters.",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "options",
                "delete_source_columns",
                "column_headers_list",
                "missing_values_reference_list",
                "activate_flag",
                "float32_processing_flag",
            ],
            "relevantToOptimizer": [],
            "properties": {
                "date_column_indices": {
                    "description": "List specifying indexes for date columns. Providing one omits automatic date column detection in fit() call",
                    "anyOf": [
                        {"type": "array", "items": {"type": "number"}},
                        {"enum": [None]},
                    ],
                    "default": None,
                },
                "options": {
                    "description": """List containing the types of new feature columns to add for each detected datetime column.
Default is None, in this case all the above options are applied""",
                    "anyOf": [
                        {
                            "type": "array",
                            "items": {
                                "enum": [
                                    "all",
                                    "Datetime",
                                    "DateToFloatTimestamp",
                                    "DateToTimestamp",
                                    "Timestamp",
                                    "FloatTimestamp",
                                    "DayOfWeek",
                                    "DayOfMonth",
                                    "Hour",
                                    "DayOfYear",
                                    "Week",
                                    "Month",
                                    "Year",
                                    "Second",
                                    "Minute",
                                ]
                            },
                        },
                        {"enum": [None]},
                    ],
                    "default": None,
                },
                "delete_source_columns": {
                    "description": "Flag determining whether the original date columns will be deleted or not.",
                    "type": "boolean",
                    "default": True,
                },
                "column_headers_list": _hparam_column_headers_list(
                    description="List containing the column names of the input array"
                ),
                "missing_values_reference_list": {
                    "description": "List containing missing values of the input array",
                    "anyOf": [
                        {"type": "array", "items": {"laleType": "Any"}},
                        {"enum": [None]},
                    ],
                    "default": None,
                },
                "activate_flag": _hparam_activate_flag_active,
                "float32_processing_flag": {
                    "description": "Flag that determines whether timestamps will be float32-compatible.",
                    "type": "boolean",
                    "default": True,
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
    "description": """Operator from `autoai_libs`_. Detects date columns on an input array and adds new feature columns for each detected date column.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.date_transformer.html",
    "import_from": "autoai_libs.transformers.date_time.date_time_transformer",
    "type": "object",
    "tags": {"pre": [], "op": ["transformer"], "post": []},
    "properties": {
        "hyperparams": _hyperparams_schema,
        "input_fit": _input_fit_schema,
        "input_transform": _input_transform_schema,
        "output_transform": _output_transform_schema,
    },
}


DateTransformer = lale.operators.make_operator(_DateTransformerImpl, _combined_schemas)

lale.docstrings.set_docstrings(DateTransformer)
