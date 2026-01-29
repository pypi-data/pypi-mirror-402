################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from numbers import Number
from typing import Iterable

from autoai_libs.utils.parameter_types import get_param_dist_from_objects, get_param_ranges_from_objects

Category = str
NumberOrCategory = Number | Category


class OptimizationParametersMixin:
    """Detailed description of the hyperparameters that are available to optimize, and the ability to set them"""

    def get_param_objects(self) -> dict:
        raise NotImplementedError()

    # continuous representation
    def get_param_ranges(self) -> tuple[dict, dict]:
        """Returns a dictionary of name: (min, max, default) tuples for numerical parameters, and
        a dictionary of name ["category1", "category2", "category3"] for categorical parameters"""
        param_ranges = {}
        param_categorical_indices = {}
        # if user has implemented get_param_objects, we can use that
        param_objects = self.get_param_objects()
        if param_objects is not None:
            return get_param_ranges_from_objects(param_objects)
        return param_ranges, param_categorical_indices

    # discrete distributions for sklearn optimizers
    def get_param_dist(self) -> dict[str, list[NumberOrCategory]]:
        """Returns a dictionary of name: [min, max, default] lists for numerical parameters, and
        a dictionary of name: ["category1", "category2", "category3"] for categorical parameters"""
        # if user has implemented get_param_objects, we can use that
        param_objects = self.get_param_objects()
        if param_objects is not None:
            return get_param_dist_from_objects(param_objects)
        return {}

    # FIXME set_params needs to return self. Also we cannot risk this being before sklearn's set_params in the __mro__
    def set_params(self, params: dict) -> None:
        """Specify exact hyperparameter values to use"""
        raise NotImplementedError()

    def get_tags(self) -> Iterable[str]:
        """Get descriptive tags"""
        return self.autoai_tags
