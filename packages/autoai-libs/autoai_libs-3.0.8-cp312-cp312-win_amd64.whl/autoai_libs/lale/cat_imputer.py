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

import autoai_libs.transformers.exportable

from ._common_schemas import (
    _hparam_activate_flag_unmodified,
    _hparam_sklearn_version_family,
)


class _CatImputerImpl:
    def __init__(self, *args, **hyperparams):
        self._wrapped_model = autoai_libs.transformers.exportable.CatImputer(*args, **hyperparams)

    def fit(self, X, y=None, **fit_params):
        self._wrapped_model.fit(X, y, **fit_params)
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
                "strategy",
                "missing_values",
                "sklearn_version_family",
                "activate_flag",
            ],
            "relevantToOptimizer": ["strategy"],
            "properties": {
                "strategy": {
                    "description": "The imputation strategy.",
                    "anyOf": [
                        {
                            "enum": ["mean"],
                            "description": "Replace using the mean along each column. Can only be used with numeric data.",
                        },
                        {
                            "enum": ["median"],
                            "description": "Replace using the median along each column. Can only be used with numeric data.",
                        },
                        {
                            "enum": ["most_frequent"],
                            "description": "Replace using most frequent value each column. Used with strings or numeric data.",
                        },
                        {
                            "enum": ["constant"],
                            "description": "Replace with fill_value. Can be used with strings or numeric data.",
                        },
                    ],
                    "transient": "alwaysPrint",  # since positional argument
                    "default": "mean",
                },
                "missing_values": {
                    "description": "The placeholder for the missing values. All occurrences of missing_values will be imputed.",
                    "anyOf": [
                        {"type": "number"},
                        {"type": "string"},
                        {"enum": [np.nan]},
                        {"enum": [None]},
                    ],
                    "transient": "alwaysPrint",  # since positional argument
                    "default": np.nan,
                },
                "sklearn_version_family": _hparam_sklearn_version_family,
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
    "description": """Operator from `autoai_libs`_. Missing value imputation for categorical features, currently internally uses the sklearn SimpleImputer_.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs
.. _SimpleImputer: https://scikit-learn.org/0.20/modules/generated/sklearn.impute.SimpleImputer.html#sklearn-impute-simpleimputer""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.cat_imputer.html",
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

CatImputer = lale.operators.make_operator(_CatImputerImpl, _combined_schemas)

autoai_libs_version_str = getattr(autoai_libs, "__version__", None)
if isinstance(autoai_libs_version_str, str):  # beware sphinx _MockModule
    import typing

    from lale.schemas import AnyOf, Array, Enum, Float, Not, Null, Object, String

    autoai_libs_version = tuple(map(int, autoai_libs_version_str.split(".")))

    if autoai_libs_version >= (1, 12, 18):
        CatImputer = typing.cast(
            lale.operators.PlannedIndividualOp,
            CatImputer.customize_schema(
                set_as_available=True,
                constraint=[
                    AnyOf(
                        desc="fill_value and fill_values cannot both be specified",
                        forOptimizer=False,
                        types=[Object(fill_value=Null()), Object(fill_values=Null())],
                    ),
                    AnyOf(
                        desc="if strategy=constants, the fill_values cannot be None",
                        forOptimizer=False,
                        types=[
                            Object(strategy=Not(Enum(["constants"]))),
                            Not(Object(fill_values=Null())),
                        ],
                    ),
                ],
                fill_value=AnyOf(
                    types=[Float(), String(), Enum(values=[np.nan]), Null()],
                    desc="The placeholder for fill value used in constant strategy",
                    default=None,
                ),
                sklearn_version_family=_hparam_sklearn_version_family,
                strategy={
                    "description": "The imputation strategy.",
                    "anyOf": [
                        {
                            "enum": ["most_frequent"],
                            "description": "Replace using the mean along each column. Can only be used with numeric data.",
                        },
                        {
                            "enum": ["constant"],
                            "description": "Replace using the median along each column. Can only be used with numeric data.",
                        },
                        {
                            "enum": ["constants"],
                            "description": "Replace using most frequent value each column. Used with strings or numeric data.",
                        },
                    ],
                    "transient": "alwaysPrint",  # since positional argument
                    "default": "most_frequent",
                },
            ),
        )

lale.docstrings.set_docstrings(CatImputer)
