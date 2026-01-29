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
    _hparams_feat_constraints,
    _hparams_fun_pointer,
    _hparams_transformer_name,
)


class _TNoOpImpl:
    def __init__(self, **hyperparams):
        self._wrapped_model = autoai_libs.cognito.transforms.transform_utils.TNoOp(**hyperparams)

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
            "required": ["fun", "name", "datatypes", "feat_constraints", "tgraph"],
            "relevantToOptimizer": [],
            "properties": {
                "fun": _hparams_fun_pointer(description="Function pointer (ignored)."),
                "name": _hparams_transformer_name,
                "datatypes": {
                    "description": "List of datatypes that are valid input (ignored).",
                    "laleType": "Any",
                    "transient": "alwaysPrint",  # since positional argument
                    "default": None,
                },
                "feat_constraints": _hparams_feat_constraints(
                    description="Constraints that must be satisfied by a column to be considered a valid input to this transform (ignored)."
                ),
                "tgraph": {
                    "description": "Should be the invoking TGraph() object.",
                    "anyOf": [{"laleType": "Any"}, {"enum": [None]}],
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
        "X": {"description": "Features; no restrictions on data type."},
        "y": {"laleType": "Any"},
    },
}

_input_transform_schema = {
    "type": "object",
    "required": ["X"],
    "additionalProperties": False,
    "properties": {"X": {"description": "Features; no restrictions on data type."}},
}

_output_transform_schema = {
    "description": "Features; no restrictions on data type.",
    "laleType": "Any",
}

_combined_schemas = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": """Operator from `autoai_libs`_. Passes the data through unchanged.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs""",
    "documentation_url": "https://lale.readthedocs.io/en/latest/modules/lale.lib.autoai_libs.t_no_op.html",
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


TNoOp = lale.operators.make_operator(_TNoOpImpl, _combined_schemas)

lale.docstrings.set_docstrings(TNoOp)
