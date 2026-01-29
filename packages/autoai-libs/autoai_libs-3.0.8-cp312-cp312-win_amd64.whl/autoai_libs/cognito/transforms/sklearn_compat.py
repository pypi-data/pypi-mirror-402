################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2019-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import copy
import inspect

import numpy
from sklearn.base import TransformerMixin

SEED = 33


class CognitoTransformer(TransformerMixin):
    def __init__(self):
        super().__init__()
        self.rng = numpy.random.default_rng(seed=SEED)

    def get_params(self, deep=True):
        klass = self.__class__
        key = "__" + klass.__name__ + "__"
        sig = inspect.signature(self.__init__)
        param_dict = {}
        for pname in sig.parameters:
            value = self.__dict__[pname]
            param_dict[pname] = value
        return param_dict

    def set_params(self, **params):
        raise (NotImplementedError("set_params not implemented yet"))

    def __repr__(self):
        return CognitoTransformer._get_repr(self)

    @classmethod
    def _get_repr(cls, instance):
        fullpath = str(instance.__class__).split("'")[1]
        param_string = ""
        for k, v in instance.get_params().items():
            if param_string != "":
                param_string += ", "
            quot = ""
            if type(v) is str:
                quot = "'"
            if type(v) is numpy.ufunc:
                param_string += k + " = numpy." + str(v).split("'")[1]
            else:
                if hasattr(v, "get_params"):
                    param_string += k + "=" + CognitoTransformer._get_repr(v)
                else:
                    param_string += k + " = " + quot + str(v) + quot
        return "%s(%s)" % (fullpath, param_string)

    def reduce_count_of_candidates(self, candidates, max_feature_generate_one_node):
        if not max_feature_generate_one_node.__class__.__name__ == "int":
            return candidates

        if len(candidates) <= max_feature_generate_one_node:
            return candidates

        #        return candidates[:max_feature_generate_one_node] #chose first k

        random_indexes = self.rng.choice(range(len(candidates)), max_feature_generate_one_node, replace=False)
        random_indexes.sort()
        new_candidates = [candidates[i] for i in random_indexes]
        return new_candidates

    def reduce_count_of_candidates_from_search_space_descriptor(self, tree_desc, max_feature_generate_one_node):
        """

        :param tree_desc:
        :param max_feature_generate_one_node:
        :return: returns list of candidates or None of this list should be generated explicitly by iterating through all combinations
        """
        if not max_feature_generate_one_node.__class__.__name__ == "int":
            return None

        if tree_desc.get_size() <= max_feature_generate_one_node:
            return None

        random_indexes = self.rng.choice(range(tree_desc.get_size()), max_feature_generate_one_node, replace=False)
        random_indexes.sort()
        new_candidates = [tree_desc.get_candidate(i) for i in random_indexes]
        return new_candidates

    def get_obj_clone_or_new_class_obj(self, class_or_obj):
        if inspect.isclass(class_or_obj):
            return class_or_obj()
        else:
            return copy.deepcopy(class_or_obj)

    @classmethod
    def safe_concat_columns(cls, new_cols, X):
        if new_cols:
            new_cols_as_tuple = tuple(new_cols)
            Xtr = numpy.concatenate(new_cols_as_tuple, axis=1)
        else:
            Xtr = numpy.empty((X.shape[0], 0), numpy.float32)
        return Xtr

    @classmethod
    def safe_computed_columns(cls, new_cols, X, return_only_new):
        # computes columns , checks whether np.concatenate is not called on empty sequence.
        if new_cols:
            new_cols_as_tuple = tuple(new_cols)
            Xtr = numpy.concatenate(new_cols_as_tuple, axis=1)
            if return_only_new:
                return Xtr
            else:
                return numpy.concatenate((X, Xtr), axis=1)
        else:
            if return_only_new:
                return numpy.empty((X.shape[0], 0), numpy.float32)
            else:
                return X
