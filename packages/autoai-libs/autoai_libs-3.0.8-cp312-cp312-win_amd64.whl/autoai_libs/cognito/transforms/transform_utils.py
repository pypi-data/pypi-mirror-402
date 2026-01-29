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
import logging
import multiprocessing
import operator
import random
import uuid
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from sklearn.cluster import FeatureAgglomeration
from sklearn.decomposition import PCA, FastICA
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.kernel_approximation import Nystroem
from sklearn.preprocessing import KBinsDiscretizer, MinMaxScaler, OneHotEncoder, StandardScaler

import autoai_libs.cognito.transforms.textras_methods as TExtras
import autoai_libs.utils.fc_methods as FC
from autoai_libs.cognito.transforms.sklearn_compat import CognitoTransformer
from autoai_libs.utils.exportable_utils import WML_raise_exception

JSON_FUNCTION_NAME_TOKEN = "functionName"
JSON_PARAMETER_TOKEN = "parameter"
JSON_TYPE_TOKEN = "type"
JSON_TYPE_FEATURE_VALUE = "feature"
JSON_TYPE_FUNCTION_VALUE = "function"

logger = logging.getLogger("autoai_libs")


def resolve_basic_datatypes(datatypes):
    basic_datatypes = []
    for dt in datatypes:
        dts = DataUtils.get_basic_types(dt)
        basic_datatypes.extend(dts)
    return basic_datatypes


class AbstractCandidatesSpaceDescriptor(ABC):
    @abstractmethod
    def get_size(self):
        pass

    @abstractmethod
    def get_candidate(self, index):
        pass


class SingletonCandidateSpaceDescriptor(AbstractCandidatesSpaceDescriptor):
    def __init__(self, candidate):
        self.candidate = candidate

    def get_size(self):
        return 1

    def get_candidate(self, index):
        if index == 0:
            return self.candidate
        raise IndexError


class CandidatesSpaceDescriptor(AbstractCandidatesSpaceDescriptor):
    def __init__(self):
        self.matching_colids_by_arg = {}

    def get_size(self):
        if len(self.matching_colids_by_arg) == 0 or len(self.matching_colids_by_arg[0]) == 0:
            return 0
        size = self._get_size()
        return size

    def _get_size(self):
        tree = self.get_tree_desc()
        cumul_tree = self.compute_cumul_left_tree_size(tree)
        return cumul_tree[()][1]

    def add_dimension_spec(self, matching_colids):
        self.matching_colids_by_arg[len(self.matching_colids_by_arg)] = matching_colids

    def get_tree_desc(self):
        return self._build_tree_desc(0, [], {}, None)

    def _build_tree_desc(self, arg_index, colids_on_path, current_tree, current_node_id):
        """
        Tree is represented as a dictionary:
            - key is a tuple representing a path as a sequence of children branches (0, 1,...)
            - entry is a tuple representing:
                - size of subset associated to branch (difference or intersection)
                - current size of sub-search space corresponding to decisions associated to the current path
                - sequence of associated colids subsets on the path
                - sequence of associated subset size on the path after handling duplicates
        :param arg_index:
        :param union_colids_set:
        :param current_tree:
        :param current_node_id:
        :return:
        """
        if self.matching_colids_by_arg.get(arg_index) is None:
            return current_tree

        colids = self.matching_colids_by_arg[arg_index]
        if arg_index == 0:
            current_size = len(colids)
            diff_node_id = (0,)
            colids_on_path = [sorted(colids)]
            current_tree[diff_node_id] = (current_size, current_size, colids_on_path, (len(colids),))
            current_tree = self._build_tree_desc(arg_index + 1, colids_on_path, current_tree, diff_node_id)
        else:
            all_select_combis = np.array(np.meshgrid(*([0, 1],) * arg_index)).T.reshape(-1, arg_index)
            for combi_index, select_combi in enumerate(all_select_combis):
                subset_select = set(colids)
                seq_subset_size = ()
                current_size = 1
                # Remove from current set of colids all colids that are in the selected level of colids_on_path
                for level in range(len(select_combi)):
                    current_subset_size = current_tree[current_node_id][3][level] - select_combi[level]
                    current_size *= current_subset_size

                    seq_subset_size = seq_subset_size + (current_subset_size,)
                    if select_combi[level]:
                        # colids that intersect with colids of the specified level on the path
                        subset_select = subset_select & set(colids_on_path[level])
                    else:
                        # colids that don't overlap with colids of the specified level on the path
                        subset_select = subset_select - set(colids_on_path[level])
                seq_subset_size = seq_subset_size + (len(subset_select),)
                current_size *= len(subset_select)
                if current_size > 0:
                    new_node_id = current_node_id + (combi_index,)
                    current_tree[new_node_id] = (
                        len(subset_select),
                        current_size,
                        colids_on_path + [sorted(subset_select)],
                        seq_subset_size,
                    )
                    current_tree = self._build_tree_desc(
                        arg_index + 1, colids_on_path + [sorted(subset_select)], current_tree, new_node_id
                    )
        return current_tree

    def compute_cumul_left_tree_size(self, tree):
        tree_left_sizes = self._compute_cumul_left_tree_size(tree, (), {}, 0)
        return tree_left_sizes

    def _compute_cumul_left_tree_size(self, tree_desc, current_node_id, current_cumul_tree, current_cumul):
        """
        Cumul_tree is represented as a dictionary:
            - key is a tuple representing a path as a sequence of children branches (0, 1,...)
            - entry is a tuple representing:
                - cumulative size of all left sub-trees
                - cumulative size for current node
        :param current_tree:
        :param current_node_id:
        :param current_tree_size:
        :param current_cumul:
        :return:
        """
        if len(self.matching_colids_by_arg) == len(current_node_id):
            # Leaf
            if tree_desc.get(current_node_id):
                current_cumul_tree[current_node_id] = (current_cumul, tree_desc[current_node_id][1])
            return current_cumul_tree

        subtree_size = None
        level = len(current_node_id) + 1
        first = True
        first_node_id = None
        for idx in range(2**level):
            child_idx = idx
            if tree_desc.get(current_node_id + (child_idx,)):
                curr_node_id = current_node_id + (child_idx,)
                if first:
                    first = False
                    first_node_id = curr_node_id
                    current_cumul_tree = self._compute_cumul_left_tree_size(
                        tree_desc, first_node_id, current_cumul_tree, current_cumul
                    )
                    subtree_size = current_cumul_tree[first_node_id][1]
                else:
                    current_cumul_tree = self._compute_cumul_left_tree_size(
                        tree_desc, curr_node_id, current_cumul_tree, current_cumul_tree[first_node_id][0] + subtree_size
                    )
                    subtree_size += current_cumul_tree[curr_node_id][1]
        if subtree_size is None:
            current_cumul_tree[current_node_id] = (current_cumul, 0)
        else:
            current_cumul_tree[current_node_id] = (current_cumul_tree[first_node_id][0], subtree_size)

        return current_cumul_tree

    def _get_node_id(self, cumul_tree, current_node_id, index):
        if len(self.matching_colids_by_arg) == len(current_node_id):
            # Leaf
            return current_node_id

        level = len(current_node_id) + 1

        for idx in range(2**level):
            curr_node_id = current_node_id + (idx,)
            if not cumul_tree.get(curr_node_id):
                continue
            if cumul_tree[curr_node_id][0] <= index < cumul_tree[curr_node_id][0] + cumul_tree[curr_node_id][1]:
                return self._get_node_id(cumul_tree, curr_node_id, index)

    def get_candidate(self, index):
        tree = self.get_tree_desc()
        cumul_tree = self.compute_cumul_left_tree_size(tree)
        return self._get_candidate(cumul_tree, tree, index)

    def _get_candidate(self, cumul_tree, desc_tree, index):
        associated_node_id = self._get_node_id(cumul_tree, (), index)
        left_cumul = cumul_tree[associated_node_id][0]
        desc_tree_node = desc_tree[associated_node_id]
        seq_colids_subset = desc_tree_node[2].copy()
        seq_colids_subset.reverse()
        actual_index = index - left_cumul
        assert actual_index >= 0
        candidate_seq = []
        for colids_subset in seq_colids_subset:
            colids_subset = sorted(set(colids_subset) - set(candidate_seq))
            idx = actual_index % len(colids_subset)
            candidate_seq = candidate_seq + [colids_subset[idx]]
            actual_index = (actual_index - idx) // len(colids_subset)
        candidate_seq.reverse()  # Reverse order to have properly ordered candidate entries
        return tuple(candidate_seq) if len(candidate_seq) > 1 else candidate_seq[0]


class DatasetS:
    def __init__(self, dataframe):
        self.df = dataframe

    # Returns a new dataset
    def AddNewColumns(self, fun):
        colnames = list(self.df.columns)
        # if 'label' in colnames:
        #     colnames.remove('label')
        for i in range(0, len(colnames)):
            self.df = self.df.withColumn("log" + colnames[i], fun(self.df[colnames[i]]))

    @staticmethod
    def GetTargetType(y):
        if FC.is_not_categorical(y):
            return "regression"
        else:
            return "classification"


class MakeDFReady:
    def __init__(self):
        self.name = "SkReady-" + str(uuid.uuid4())
        self.uid = self.name
        self.long_name = self.uid
        self.run_ = None

    def transform(self, X, n_jobs=1):
        if self.run_ is None:
            raise ValueError("MakeDFReady issue")

        try:
            X_tr = X.iloc[:, self.numeric_colids_]
            return X_tr
        except:
            logger.error("present columns: " + str(len(X.columns)))
            logger.error("numeric columns to keep" + str(self.numeric_colids_))
            raise Exception("Issue in MakeDFReady.transform")

    def fit(self, X, y):
        self.run_ = True
        df = pd.DataFrame(X)
        colnames = list(df.columns)
        colcount = len(colnames)
        self.numeric_colids_ = []
        for i in range(colcount):
            try:
                if str(df.iloc[:, i].dtype) in DataUtils.NumericDataTypes():
                    self.numeric_colids_.append(i)
            except:
                logger.debug(df.iloc[:, i])
                logger.debug("colname=" + df.iloc[:, i].name)
        return self


class FS1(CognitoTransformer):
    def __init__(self, cols_ids_must_keep, additional_col_count_to_keep, ptype):
        super().__init__()
        self.long_name = "FS1-" + str(uuid.uuid4())
        self.uid = self.long_name
        self.name = "FS1"
        self.additional_col_count_to_keep = additional_col_count_to_keep
        self.cols_ids_must_keep = cols_ids_must_keep
        self.ptype = ptype

    def transform(self, X, n_jobs=1):
        try:
            X_tr = X[:, self.cols_to_keep_final_]
            return X_tr
        except Exception as e:
            logger.error("Error in executing FS", exc_info=e)
            logger.debug("columns to keep" + str(self.cols_to_keep_final_))
            logger.debug("# of columns in df : " + str(X.shape[1]))
            raise e

    def fit(self, X, y):
        if self.ptype == "classification":
            skb = SelectKBest(f_classif, k="all")
        else:
            skb = SelectKBest(f_regression, k="all")

        # why not just use fit?
        trained_skb = skb.fit(X, y)
        if trained_skb is not None:
            skb = trained_skb
        if self.additional_col_count_to_keep >= 1:
            self.k_ = self.additional_col_count_to_keep
        elif 0 < self.additional_col_count_to_keep < 1:
            self.k_ = int((X.shape[1] - len(self.cols_ids_must_keep)) * self.additional_col_count_to_keep)
        else:
            # <= 0  means features with above average scores
            self.k_ = len([f for f in skb.scores_ if f > np.mean(skb.scores_)])

        if np.isnan(skb.scores_).any():
            skb.scores_ = [0 if np.isnan(x) else x for x in skb.scores_]

        self.find_k_top_indices(skb.scores_)
        del skb
        return self

    def find_k_top_indices(self, fs_scores):
        fs_scores = list(fs_scores)
        self.cols_to_keep_final_ = []

        for i in range(0, len(self.cols_ids_must_keep)):
            ind = self.cols_ids_must_keep[i]
            self.cols_to_keep_final_.append(ind)
            fs_scores[ind] = -np.inf

        for i in range(0, self.k_):
            max_index, max_value = max(enumerate(fs_scores), key=operator.itemgetter(1))
            if max_value == -np.inf:
                break
            self.cols_to_keep_final_.append(max_index)
            fs_scores[max_index] = -np.inf

        self.cols_to_keep_final_.sort()


class FS2(CognitoTransformer):
    score_percentile_threshold = 10

    def __init__(self, cols_ids_must_keep, additional_col_count_to_keep, ptype, eval_algo):
        super().__init__()
        self.long_name = "FS2-" + str(uuid.uuid4())
        self.uid = self.long_name
        self.name = "FS2"
        self.additional_col_count_to_keep = additional_col_count_to_keep
        self.cols_ids_must_keep = cols_ids_must_keep
        self.ptype = ptype
        self.eval_algo = eval_algo

    def transform(self, X, n_jobs=1):
        try:
            X_tr = X[:, self.cols_to_keep_final_]
            return X_tr
        except Exception as e:
            logger.error("Error in executing FS", exc_info=e)
            logger.debug("columns to keep" + str(self.cols_to_keep_final_))
            logger.debug("# of columns in df : " + str(X.shape[1]))
            raise e

    def fit(self, X, y):
        if inspect.isclass(self.eval_algo):
            self.eval_algo_ = self.eval_algo(random_state=7)
        else:
            self.eval_algo_ = copy.deepcopy(self.eval_algo)
        self.eval_algo_.fit(X, y)
        trained_eval_algo_ = copy.deepcopy(self.eval_algo_)
        if trained_eval_algo_ is not None:
            self.eval_algo_ = trained_eval_algo_
        if self.additional_col_count_to_keep >= 1:
            self.k_ = self.additional_col_count_to_keep
        elif 0 < self.additional_col_count_to_keep < 1:
            self.k_ = int((X.shape[1] - len(self.cols_ids_must_keep)) * self.additional_col_count_to_keep)
        else:
            # <= 0  means features with above average scores
            self.k_ = len(
                [f for f in self.eval_algo_.feature_importances_ if f > np.mean(self.eval_algo_.feature_importances_)]
            )
        self.find_k_top_indices(self.eval_algo_.feature_importances_)
        del self.eval_algo_
        return self

    def find_k_top_indices(self, fs_scores):
        fs_scores = list(fs_scores)
        self.cols_to_keep_final_ = []

        for i in range(0, len(self.cols_ids_must_keep)):
            ind = self.cols_ids_must_keep[i]
            self.cols_to_keep_final_.append(ind)
            fs_scores[ind] = -np.inf

        for i in range(0, self.k_):
            max_index, max_value = max(enumerate(fs_scores), key=operator.itemgetter(1))
            if max_value == -np.inf:
                break
            self.cols_to_keep_final_.append(max_index)
            fs_scores[max_index] = -np.inf

        self.cols_to_keep_final_.sort()


class FS3(CognitoTransformer):
    def __init__(self, colids_to_remove):
        super().__init__()
        self.colids_to_remove = colids_to_remove

    def fit(self, X, y):
        return self

    def transform(self, X):
        columns = list(range(0, X.shape[1]))
        for x in list(self.colids_to_remove):
            columns.remove(x)

        return X[:, columns]


class Tproxy(CognitoTransformer):
    def __init__(self, trobj):
        super().__init__()
        self.trobj = trobj
        self.long_name = trobj.long_name
        self.uid = self.long_name
        self.name = trobj.name

    def fit(self, X, y, col_names, col_dtypes):
        return self

    def transform(self, X, n_jobs=1):
        Xtr = self.trobj.transform(X)
        self.new_column_names_ = self.trobj.new_column_names_
        self.new_column_dtypes_ = self.trobj.new_column_dtypes_
        self.new_column_as_json_objects_ = self.trobj.new_column_as_json_objects_
        return Xtr


class DataUtils:
    @staticmethod
    def NumericDataTypes():
        return [
            "intc",
            "intp",
            "int_",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "int8",
            "int16",
            "int32",
            "int64",
            "short",
            "long",
            "longlong",
            "float16",
            "float32",
            "float64",
        ]

    @staticmethod
    def IntDataTypes():
        return [
            "intc",
            "intp",
            "int_",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "int8",
            "int16",
            "int32",
            "int64",
            "short",
            "long",
            "longlong",
        ]

    @staticmethod
    def FloatDataTypes():
        return ["float16", "float32", "float64"]

    @staticmethod
    def get_basic_types(cat):
        if cat == "numeric":
            return DataUtils.NumericDataTypes()
        if cat == "float":
            return DataUtils.FloatDataTypes()
        if cat == "int" or cat == "integer":
            return DataUtils.IntDataTypes()
        return [cat]

    @staticmethod
    def replace_nan_and_inf(col):
        if np.isnan(col).any():
            where_nan = np.isnan(col)
            col[where_nan] = 0
        if np.isinf(col).any():
            where_inf = np.isinf(col)
            col[where_inf] = 0
        if np.isneginf(col).any():
            where_neginf = np.isneginf(col)
            col[where_neginf] = 0

        return col

    @staticmethod
    def all_feats_numeric(df):
        for colid in range(0, df.shape[1]):
            try:
                if not df[:, colid].dtype in DataUtils.NumericDataTypes():
                    return False
            except Exception as e:
                logger.debug(df[:, colid])
                raise e
        return True

    @staticmethod
    def get_unique_column_name(proposed_name, existing_name_list):
        while proposed_name in existing_name_list:
            proposed_name = proposed_name + "-" + str(random.randint(0, 9))
        return proposed_name

    @staticmethod
    def get_json_for_name(name):
        # return {'name': '$' + str(name)}
        return {"featureName": str(name), JSON_TYPE_TOKEN: JSON_TYPE_FEATURE_VALUE}

    @staticmethod
    def build_json_objects(names, name_to_json_map):
        json_objects_list = []
        for name in names:
            json_objects_list.append(name_to_json_map.get(name, DataUtils.get_json_for_name(name)))
        return json_objects_list


class TNoOp(CognitoTransformer):
    def __init__(self, fun, name, datatypes, feat_constraints, tgraph=None):
        super().__init__()
        self.tgraph = tgraph
        self.fun = None
        if name is not None:
            self.name = name
        else:
            self.name = self.fun.__name__

        self.datatypes = datatypes

        if feat_constraints is None:
            self.feat_constraints = []
        else:
            self.feat_constraints = feat_constraints

        self.uid = "TNoOp-" + str(name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid

    def transform(self, df, n_jobs=1):
        return df

    def fit(self, X, y):
        # moved from init
        # self.datatypes = resolve_basic_datatypes(self.datatypes)

        self.colids_ = []
        return self


class TA1(CognitoTransformer):
    def __init__(
        self,
        fun,
        name=None,
        datatypes=None,
        feat_constraints=None,
        tgraph=None,
        apply_all=True,
        col_names=None,
        col_dtypes=None,
        col_as_json_objects=None,
    ):
        super().__init__()
        self.fun = fun
        self.tgraph = tgraph
        self.apply_all = apply_all
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_as_json_objects = col_as_json_objects

        self.name = name
        self.datatypes = datatypes
        self.feat_constraints = feat_constraints
        if self.name is None:
            self.name = self.fun.__name__

        if self.feat_constraints is None:
            self.feat_constraints = []

        self.uid = "TA1-" + str(self.name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid

    def transform(self, X, n_jobs=1, return_new_cols_only=False):
        assert isinstance(X, np.ndarray)
        if self.apply_all is False and X.shape[1] != 1:
            logger.warning(
                " More than admissible number of columns provided for transform with apply_all=False for transform "
                + self.name
            )
            return None

        if self.tgraph is not None and self.tgraph.multiprocessing:
            with multiprocessing.Pool(n_jobs) as pool:
                cols = pool.starmap(self.exec_tr, [(colid, X) for colid in self.colids_])
        else:
            cols = []
            for colid in self.colids_:
                cols.append(self.exec_tr(colid, X))

        new_col_names = []
        new_col_dtypes = []
        new_column_as_json_objects = []
        for i in range(0, len(self.colids_)):
            base_col_name = self.col_names_[self.colids_[i]]
            base_col_as_json_object = self.col_as_json_objects_[self.colids_[i]]
            new_full_name = DataUtils.get_unique_column_name(
                self.name + "(" + str(base_col_name) + ")", new_col_names + self.col_names_
            )
            new_col_names.append(new_full_name)
            new_col_dtypes.append(cols[i].dtype)
            new_column_as_json_objects.append(
                {
                    JSON_FUNCTION_NAME_TOKEN: self.name,
                    JSON_TYPE_TOKEN: JSON_TYPE_FUNCTION_VALUE,
                    JSON_PARAMETER_TOKEN: [base_col_as_json_object],
                }
            )

        self.new_column_names_ = new_col_names
        self.new_column_dtypes_ = new_col_dtypes
        self.new_column_as_json_objects_ = new_column_as_json_objects

        return self.safe_computed_columns(cols, X, return_new_cols_only)

    def get_candidates_space_descriptor(self, df, col_names, col_dtypes):
        desc = CandidatesSpaceDescriptor()

        colids = []
        for colid in range(0, df.shape[1]):
            try:
                ty = str(col_dtypes[colid])
            except Exception as e:
                logger.debug(df.shape[1])
                logger.debug(df[:, colid])
                raise e
            # for allowedDT in self.datatypes:
            if ty in resolve_basic_datatypes(self.datatypes) and self.all_fc_satisifed(
                df[:, colid], col_names[(len(col_names) - df.shape[1]) + colid]
            ):
                colids.append(colid)

        desc.add_dimension_spec(colids)
        return desc

    def get_candidates(self, df, col_names, col_dtypes):
        colids = []
        for colid in range(0, df.shape[1]):
            try:
                ty = str(col_dtypes[colid])
            except Exception as e:
                logger.debug(df.shape[1])
                logger.debug(df[:, colid])
                raise e
            # for allowedDT in self.datatypes:
            if ty in resolve_basic_datatypes(self.datatypes) and self.all_fc_satisifed(df[:, colid], col_names[colid]):
                colids.append(colid)

        desc = self.get_candidates_space_descriptor(df, col_names, col_dtypes)
        search_space_size = desc.get_size()
        if search_space_size != len(colids):
            assert search_space_size == len(colids)

        return colids

    def namestr(self, obj, namespace):
        return [name for name in namespace if namespace[name] is obj]

    def fit(self, X, y, col_names=None, col_dtypes=None, col_as_json_objects=None):
        if col_names is None:
            col_names = self.col_names
        if col_dtypes is None:
            col_dtypes = self.col_dtypes
        if col_as_json_objects is None:
            if self.col_as_json_objects is None and col_names is not None:
                col_as_json_objects = [DataUtils.get_json_for_name(name) for name in col_names]
            else:
                col_as_json_objects = self.col_as_json_objects
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_names_ = col_names
        self.col_dtypes_ = col_dtypes
        self.col_as_json_objects_ = col_as_json_objects

        if self.apply_all:
            tree_desc = self.get_candidates_space_descriptor(X, col_names, col_dtypes)
            self.colids_ = None
            if self.tgraph is not None and self.tgraph.max_feature_generate_one_node is not None:
                self.colids_ = self.reduce_count_of_candidates_from_search_space_descriptor(
                    tree_desc, self.tgraph.max_feature_generate_one_node
                )
            if self.colids_ is None:
                self.colids_ = self.get_candidates(X, col_names, col_dtypes)

        else:
            if X.shape[1] != 1:
                logger.warning("More columns than 1 provided for apply_all in transform " + self.name)
                return None
            self.colids_ = [0]

        return self

    def all_fc_satisifed(self, dfc, col_name):
        dfcname = col_name
        for fc in self.feat_constraints:
            fcname = fc.__name__
            if self.tgraph is not None and self.tgraph.fcache_contains_key(fcname, dfcname):
                res = self.tgraph.does_col_satisfy_fc(fcname, dfcname)
            else:
                res = fc(dfc)
                if self.tgraph is not None:
                    self.tgraph.add_to_fc_cache(fcname, dfcname, res)
            if res is False:
                return False
        return True

    def exec_tr(self, colid, df_):
        col = df_[:, colid]
        new_col = DataUtils.replace_nan_and_inf(self.fun(col)[..., None])
        return new_col


class TA2(CognitoTransformer):
    def __init__(
        self,
        fun,
        name,
        datatypes1,
        feat_constraints1,
        datatypes2,
        feat_constraints2,
        tgraph=None,
        apply_all=True,
        col_names=None,
        col_dtypes=None,
        col_as_json_objects=None,
    ):
        super().__init__()
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_as_json_objects = col_as_json_objects
        self.apply_all = apply_all
        self.fun = fun
        self.tgraph = tgraph
        if name is not None:
            self.name = name
        else:
            self.name = self.fun.__name__

        self.datatypes1 = datatypes1

        self.datatypes2 = datatypes2
        self._datatypes_converted = False

        if feat_constraints1 is None:
            self.feat_constraints1 = []
        else:
            self.feat_constraints1 = feat_constraints1

        if feat_constraints2 is None:
            self.feat_constraints2 = []
        else:
            self.feat_constraints2 = feat_constraints2

        self.uid = "TA2-" + str(name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid

    def transform(self, X, n_jobs=1, return_new_cols_only=False):
        if self.tgraph is not None and self.tgraph.multiprocessing:
            with multiprocessing.Pool(n_jobs) as pool:
                cols = pool.starmap(self.exec_tr, [(i, X) for i in range(0, len(self.colid_pairs_))])
        else:
            cols = []
            for i in range(0, len(self.colid_pairs_)):
                col = self.exec_tr(i, X)
                cols.append(col)

        new_col_names = []
        new_col_dtypes = []
        new_column_as_json_objects = []
        for i in range(len(cols)):
            basename1 = self.col_names_[self.colid_pairs_[i][0]]
            basename2 = self.col_names_[self.colid_pairs_[i][1]]
            basename_json_1 = self.col_as_json_objects_[self.colid_pairs_[i][0]]
            basename_json_2 = self.col_as_json_objects_[self.colid_pairs_[i][1]]
            colname = DataUtils.get_unique_column_name(
                self.name + "(" + str(basename1) + "__" + str(basename2) + ")", self.col_names_ + new_col_names
            )
            new_col_names.append(colname)
            new_col_dtypes.append(cols[i].dtype)
            # new_column_as_json_objects.append({'expression': {'op': self.name, 'params': [basename_json_1, basename_json_2]}})
            new_column_as_json_objects.append(
                {
                    JSON_FUNCTION_NAME_TOKEN: self.name,
                    JSON_TYPE_TOKEN: JSON_TYPE_FUNCTION_VALUE,
                    JSON_PARAMETER_TOKEN: [basename_json_1, basename_json_2],
                }
            )

        self.new_column_names_ = new_col_names
        self.new_column_dtypes_ = new_col_dtypes
        self.new_column_as_json_objects_ = new_column_as_json_objects
        return self.safe_computed_columns(cols, X, return_new_cols_only)

    def get_candidates_space_descriptor(self, df, col_names, col_dtypes):
        desc = CandidatesSpaceDescriptor()

        matching_colids1 = []
        for colid1 in range(0, df.shape[1]):
            try:
                ty1 = str(col_dtypes[colid1])
            except Exception as e:
                logger.debug(col_names)
                logger.debug(df[:, colid1])
                raise e
            if ty1 in resolve_basic_datatypes(self.datatypes1) and self.all_fc1_satisifed(
                df[:, colid1], col_names[colid1]
            ):
                matching_colids1.append(colid1)

        matching_colids2 = []
        for colid2 in range(0, df.shape[1]):
            ty2 = str(col_dtypes[colid2])
            if ty2 in resolve_basic_datatypes(self.datatypes2) and self.all_fc2_satisifed(
                df[:, colid2], col_names[colid2]
            ):
                matching_colids2.append(colid2)

        desc.add_dimension_spec(matching_colids1)
        desc.add_dimension_spec(matching_colids2)
        return desc

    def get_candidates(self, df, col_names, col_dtypes):
        col_pair_ids = []
        for colid1 in range(0, df.shape[1]):
            try:
                ty1 = str(col_dtypes[colid1])
            except Exception as e:
                logger.debug(col_names)
                logger.debug(df[:, colid1])
                raise e

            if ty1 in resolve_basic_datatypes(self.datatypes1) and self.all_fc1_satisifed(
                df[:, colid1], col_names[colid1]
            ):
                for colid2 in range(0, df.shape[1]):
                    if colid1 == colid2:
                        continue
                    ty2 = str(col_dtypes[colid2])
                    if ty2 in resolve_basic_datatypes(self.datatypes2) and self.all_fc2_satisifed(
                        df[:, colid2], col_names[colid2]
                    ):
                        col_pair_ids.append((colid1, colid2))

        desc = self.get_candidates_space_descriptor(df, col_names, col_dtypes)
        search_space_size = desc.get_size()
        if search_space_size != len(col_pair_ids):
            assert search_space_size == len(col_pair_ids)

        if self.name in TransformBase.GetCommutativeTransformNames():
            return sorted(set(tuple(sorted(i)) for i in col_pair_ids))
        else:
            return col_pair_ids

    def exec_tr(self, i, df_):
        new_col = DataUtils.replace_nan_and_inf(
            self.fun(df_[:, self.colid_pairs_[i][0]], df_[:, self.colid_pairs_[i][1]])[..., None]
        )
        return new_col

    def namestr(self, obj, namespace):
        return [name for name in namespace if namespace[name] is obj]

    def fit(self, X, y, col_names=None, col_dtypes=None, col_as_json_objects=None):
        if col_names is None:
            col_names = self.col_names
        if col_dtypes is None:
            col_dtypes = self.col_dtypes
        if col_as_json_objects is None:
            if self.col_as_json_objects is None and col_names is not None:
                col_as_json_objects = [DataUtils.get_json_for_name(name) for name in col_names]
            else:
                col_as_json_objects = self.col_as_json_objects
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_names_ = col_names
        self.col_dtypes_ = col_dtypes
        self.col_as_json_objects_ = col_as_json_objects
        # moved from init
        self.datatypes1 = resolve_basic_datatypes(self.datatypes1)
        self.datatypes2 = resolve_basic_datatypes(self.datatypes2)

        df = X

        tree_desc = self.get_candidates_space_descriptor(df, col_names, col_dtypes)
        self.colid_pairs_ = None

        if self.tgraph is not None and self.tgraph.max_feature_generate_one_node is not None:
            self.colid_pairs_ = self.reduce_count_of_candidates_from_search_space_descriptor(
                tree_desc, self.tgraph.max_feature_generate_one_node
            )

        if self.colid_pairs_ is None:
            # self.colid_pairs_ = self.get_candidates(X, col_names, col_dtypes)
            colpairids_ = self.get_candidates(df, col_names, col_dtypes)
            self.colid_pairs_ = []
            for cpair in colpairids_:
                indx1 = cpair[0]
                indx2 = cpair[1]
                self.colid_pairs_.append((indx1, indx2))

        # colpairids_ = self.get_candidates(df, col_names, col_dtypes)
        # self.colid_pairs_ = []
        # for cpair in colpairids_:
        #     indx1 = cpair[0]
        #     indx2 = cpair[1]
        #     self.colid_pairs_.append((indx1, indx2))
        #
        # if self.tgraph is not None and self.tgraph.max_feature_generate_one_node is not None:
        #     self.colid_pairs_ = self.reduce_count_of_candidates(self.colid_pairs_, self.tgraph.max_feature_generate_one_node)
        return self

    def all_fc1_satisifed(self, dfc, dfcname):
        for fc in self.feat_constraints1:
            fcname = fc.__name__
            if self.tgraph is not None and self.tgraph.fcache_contains_key(fcname, dfcname):
                res = self.tgraph.does_col_satisfy_fc(fcname, dfcname)
            else:
                res = fc(dfc)
                if self.tgraph is not None:
                    self.tgraph.add_to_fc_cache(fcname, dfcname, res)
            if res is False:
                return False
        return True

    def all_fc2_satisifed(self, dfc, dfcname):
        for fc in self.feat_constraints2:
            fcname = fc.__name__
            if self.tgraph is not None and self.tgraph.fcache_contains_key(fcname, dfcname):
                res = self.tgraph.does_col_satisfy_fc(fcname, dfcname)
            else:
                res = fc(dfc)
                if self.tgraph is not None:
                    self.tgraph.add_to_fc_cache(fcname, dfcname, res)
            if res is False:
                return False
        return True


class NSFA(CognitoTransformer):
    def __init__(self, significance, protected_cols=None, analyzer=None):
        """
        Non-Significant Feature Analyzer - a class for selection significant features from a dataset.
        NSFA collects a significant columns. Those columns that are insignificant are analyzed
        by an analyzer to retrieve any information about contained data. Retrieved information are
        merged with significant columns as a new columns.

        Parameters
        ----------
        significance: a list with significance values of each column,
        columns are chosen by value in the place corresponding to their index
        protected_cols: indices of columns that a transformer must keep
        analyzer: a tool used to analyze zero-significant columns | Supported: PCA
        """
        super().__init__()
        if protected_cols is None:
            protected_cols = []
        self.significance = significance
        self.protected_cols = protected_cols
        self.protected_cols_transformed_ = None
        self.significant_columns = None
        self.nonsignificant_columns = None
        self.num_of_additional_columns = None
        if analyzer is None:
            self.analyzer = PCA()
        else:
            self.analyzer = analyzer

    def transform(self, X):
        if isinstance(X, np.ndarray):
            if self.significant_columns is not None and self.nonsignificant_columns is not None:
                if hasattr(self.analyzer, "explained_variance_ratio_"):
                    best_components = [
                        i
                        for i in range(self.analyzer.n_components_)
                        if np.sum(self.analyzer.explained_variance_ratio_[:i]) < 0.9
                    ]
                else:
                    best_components = 0
                Xt = self.analyzer.transform(X[:, self.nonsignificant_columns])[:, best_components]
                X_transformed = np.concatenate(
                    (X[:, self.significant_columns], Xt), axis=1
                )  # order of concatenation important for calculating `self.protected_cols_transformed_`
                self.protected_cols_transformed_ = {i: self.significant_columns.index(i) for i in self.protected_cols}
                self.num_of_additional_columns = Xt.shape[1]
                return X_transformed
            else:
                WML_raise_exception(
                    error_message="Missing column indices - transformer needs to be fitted before transformation."
                )
        else:
            WML_raise_exception(
                error_message="Insufficient parameter type {0} (required: {1}).".format("X", np.ndarray),
                exception_type="TypeError",
            )

    def fit(self, X, y=None):
        if isinstance(X, np.ndarray):
            self.significant_columns = [
                i for i in range(X.shape[1]) if self.significance[i] > 0.0 or i in self.protected_cols
            ]
            self.nonsignificant_columns = [i for i in range(X.shape[1]) if i not in self.significant_columns]
            self.analyzer.fit(X[:, self.nonsignificant_columns])
        else:
            WML_raise_exception(
                error_message="Insufficient parameter type {0} (required: {1}).".format("X", np.ndarray),
                exception_type="TypeError",
            )
        return self


class TGen(CognitoTransformer):
    def __init__(
        self,
        fun,
        name,
        arg_count,
        datatypes_list,
        feat_constraints_list,
        tgraph=None,
        apply_all=True,
        col_names=None,
        col_dtypes=None,
        col_as_json_objects=None,
    ):
        super().__init__()
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_as_json_objects = col_as_json_objects
        self.tgraph = tgraph
        self.apply_all = apply_all
        fit_op = getattr(fun, "fit", None)
        transform_op = getattr(fun, "transform", None)

        if callable(fit_op) and callable(transform_op):
            self.transform_type = "B"
        else:
            self.transform_type = "A"

        self.fun = fun
        if name is not None:
            self.name = name
        else:
            self.name = self.fun.__name__
        self.arg_count = arg_count

        self.datatypes_list = datatypes_list
        self.feat_constraints_list = feat_constraints_list

        if arg_count < 1:
            raise ValueError("Need at least 1 argument. Provided " + str(arg_count))
        if len(datatypes_list) != arg_count or len(feat_constraints_list) != arg_count:
            raise ValueError(
                "Argument count does not match datatype_list (%s) or fc_list (%s)"
                % (str(len(datatypes_list)), str(len(feat_constraints_list)))
            )

        self.uid = "Tgen-" + str(name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid

    def transform(self, X, n_jobs=1, return_new_cols_only=False):
        new_col_names = []
        new_col_dtypes = []
        new_column_as_json_objects = []
        final_arrays_list = []

        for i in range(0, len(self.candidates_)):
            candidate_cols = self.candidates_[i]
            column_params = []
            for colid in candidate_cols:
                column_params.append(X[:, colid])

            if self.transform_type == "A":
                fun = self.get_obj_clone_or_new_class_obj(self.fun)
                nc = fun(*column_params)
            else:
                column_params_ids = list(candidate_cols)
                nc = self.tobjects_[i].transform(X[:, column_params_ids])

            if type(nc).__name__ == "csr_matrix":
                outcol_df = nc.toarray()
            elif type(nc).__name__ == "tuple":
                if type(nc[0]).__name__ == "Series":
                    outcol_df = TGen.get_df_from_tuple_of_series([nc[0], nc[1]]).values
                else:
                    ncs = []
                    for i in range(len(nc)):
                        if len(nc[i].shape) == 1:
                            ncs.append(nc[i][..., None])
                        else:
                            ncs.append(nc[i])
                    outcol_df = np.concatenate(ncs, 1)

            elif type(nc).__name__ == "ndarray":
                outcol_df = nc
            elif type(nc).__name__ == "DataFrame":
                outcol_df = nc.values
            elif type(nc).__name__ == "Series":
                outcol_df = nc.values[..., None]
            else:
                outcol_df = nc.toarray()

            if len(outcol_df.shape) == 1:
                ocolcnt = 1
            else:
                ocolcnt = outcol_df.shape[1]

            if True:
                if ocolcnt == 1:
                    outcol_df = DataUtils.replace_nan_and_inf(outcol_df)
                    cname = DataUtils.get_unique_column_name(
                        self.name + "(" + self.combined_param_name(candidate_cols, self.col_names_) + ")",
                        self.col_names_ + new_col_names,
                    )
                    new_col_names.append(cname)
                    new_col_dtypes.append(outcol_df.dtype)
                    # new_column_as_json_objects.append({'expression': {'op': self.name, 'params': [self.col_as_json_objects_[x] for x in candidate_cols]}})
                    new_column_as_json_objects.append(
                        {
                            JSON_FUNCTION_NAME_TOKEN: self.name,
                            JSON_TYPE_TOKEN: JSON_TYPE_FUNCTION_VALUE,
                            JSON_PARAMETER_TOKEN: [self.col_as_json_objects_[x] for x in candidate_cols],
                        }
                    )
                    if len(outcol_df.shape) == 1:
                        final_arrays_list.append(outcol_df[..., None])
                    else:
                        final_arrays_list.append(outcol_df)

                else:
                    for i in range(0, ocolcnt):
                        new_col = DataUtils.replace_nan_and_inf(outcol_df[:, i])
                        final_arrays_list.append(new_col[..., None])
                        cname = DataUtils.get_unique_column_name(
                            self.name
                            + "_"
                            + str(i)
                            + "("
                            + self.combined_param_name(candidate_cols, self.col_names_)
                            + ")",
                            self.col_names_ + new_col_names,
                        )
                        new_col_names.append(cname)
                        new_col_dtypes.append(new_col.dtype)
                        # new_column_as_json_objects.append({'expression': {'op': self.name, 'params': [{'output_index': i}] + [self.col_as_json_objects_[x] for x in candidate_cols]}})
                        new_column_as_json_objects.append(
                            {
                                JSON_FUNCTION_NAME_TOKEN: self.name,
                                JSON_TYPE_TOKEN: JSON_TYPE_FUNCTION_VALUE,
                                JSON_PARAMETER_TOKEN: [{"output_index": i}]
                                + [self.col_as_json_objects_[x] for x in candidate_cols],
                            }
                        )

        self.new_column_dtypes_ = new_col_dtypes
        self.new_column_names_ = new_col_names
        self.new_column_as_json_objects_ = new_column_as_json_objects
        return self.safe_computed_columns(final_arrays_list, X, return_new_cols_only)

    def get_candidates_space_descriptor(self, df, col_names, col_dtypes):
        desc = CandidatesSpaceDescriptor()

        for current_arg in range(self.arg_count):
            datatypes = self.datatypes_list[current_arg]

            matching_colids = []
            for colid in range(0, df.shape[1]):
                ty1 = str(col_dtypes[colid])
                if ty1 in resolve_basic_datatypes(datatypes) and self.all_fc_satisifed(
                    self.feat_constraints_list[current_arg], df[:, colid], col_names[colid]
                ):
                    matching_colids.append(colid)

            desc.add_dimension_spec(matching_colids)
        return desc

    def get_candidates(self, df, col_names, col_dtypes):
        colids_tuple_list = []
        colids_tuple_list = self.get_candidates_sub(df, 0, colids_tuple_list, col_names, col_dtypes)

        desc = self.get_candidates_space_descriptor(df, col_names, col_dtypes)
        search_space_size = desc.get_size()
        if search_space_size != len(colids_tuple_list):
            assert search_space_size == len(colids_tuple_list)

        return colids_tuple_list

    def get_candidates_sub(self, df, current_arg, colids_tuple_list, col_names, col_dtypes):
        if current_arg >= self.arg_count:
            return colids_tuple_list

        datatypes = self.datatypes_list[current_arg]
        fcs = self.feat_constraints_list[current_arg]

        matching_colids = []
        for colid in range(0, df.shape[1]):
            ty1 = str(col_dtypes[colid])
            if ty1 in resolve_basic_datatypes(datatypes) and self.all_fc_satisifed(
                self.feat_constraints_list[current_arg], df[:, colid], col_names[colid]
            ):
                matching_colids.append(colid)

        if len(matching_colids) == 0:
            return []

        updated_colids_tuple_list = []
        if current_arg == 0:
            for latest_colid in matching_colids:
                updated_colids_tuple_list.append((latest_colid,))
        else:
            for colids_tuple in colids_tuple_list:
                for latest_colid in matching_colids:
                    if latest_colid not in colids_tuple:
                        new_tuple = colids_tuple + (latest_colid,)
                        updated_colids_tuple_list.append(new_tuple)

        if len(updated_colids_tuple_list) == 0:
            return []

        return self.get_candidates_sub(df, current_arg + 1, updated_colids_tuple_list, col_names, col_dtypes)

    def combined_param_name(self, candidate_cols_ids, col_names):
        ccn = ""
        for x in candidate_cols_ids:
            ccn = ccn + str(col_names[x]) + "___"

        return ccn

    def namestr(self, obj, namespace):
        return [name for name in namespace if namespace[name] is obj]

    @staticmethod
    def get_df_from_tuple_of_series(tofseries):
        col_count = len(tofseries)
        col_list = []
        new_colnames = []
        for i in range(0, col_count):
            tofseries[i].name = str(i)
            col_list.append(tofseries[i])
            new_colnames.append(str(i))

        return pd.concat(col_list, axis=1)

    def fit(self, X, y, col_names=None, col_dtypes=None, col_as_json_objects=None):
        if col_names is None:
            col_names = self.col_names
        if col_dtypes is None:
            col_dtypes = self.col_dtypes
        if col_as_json_objects is None:
            if self.col_as_json_objects is None and col_names is not None:
                col_as_json_objects = [DataUtils.get_json_for_name(name) for name in col_names]
            else:
                col_as_json_objects = self.col_as_json_objects
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_names_ = col_names
        self.col_dtypes_ = col_dtypes
        self.col_as_json_objects_ = col_as_json_objects
        # moved from init
        # self.datatypes_list = resolve_basic_datatypes(self.datatypes_list)

        tree_desc = self.get_candidates_space_descriptor(X, col_names, col_dtypes)
        self.candidates_ = None
        if self.tgraph is not None and self.tgraph.max_feature_generate_one_node is not None:
            self.candidates_ = self.reduce_count_of_candidates_from_search_space_descriptor(
                tree_desc, self.tgraph.max_feature_generate_one_node
            )

        if self.candidates_ is None:
            self.candidates_ = self.get_candidates(X, col_names, col_dtypes)

        # self.candidates_ = self.get_candidates(X, col_names, col_dtypes)
        # # if self.transform_type == 'B':
        # #     self.tobjects_ = []
        # #     for cols in self.candidates_:
        # #         column_params_ids = list(cols)
        # #         tobj = self.get_obj_clone_or_new_class_obj(self.fun)
        # #         tobj.fit(X[:, column_params_ids])
        # #         self.tobjects_.append(tobj)
        # #
        # if self.tgraph is not None and self.tgraph.max_feature_generate_one_node is not None:
        #     self.candidates_ = self.reduce_count_of_candidates(self.candidates_, self.tgraph.max_feature_generate_one_node)

        if self.transform_type == "B":
            self.tobjects_ = []
            for cols in self.candidates_:
                column_params_ids = list(cols)
                tobj = self.get_obj_clone_or_new_class_obj(self.fun)
                trained_tobj = tobj.fit(X[:, column_params_ids])
                if trained_tobj is not None:
                    tobj = trained_tobj
                self.tobjects_.append(tobj)

        return self

    def all_fc_satisifed(self, fcs, dfc, dfcname):
        for fc in fcs:
            fcname = fc.__name__
            if self.tgraph is not None and self.tgraph.fcache_contains_key(fcname, dfcname):
                res = self.tgraph.does_col_satisfy_fc(fcname, dfcname)
            else:
                res = fc(dfc)
                if self.tgraph is not None:
                    self.tgraph.add_to_fc_cache(fcname, dfcname, res)
            if res is False:
                return False
        return True


# TB1 is actually broken and not used in autoai_core due to the issue in get_candidates_space_descriptor and
# get_candidates methods, they always return empty list with candidates to transform for the experiment via pdcoe.
# The fix for this provided in the branch "feature/cognito-tb1-enable-with-onnx-converter".
# Link: https://github.ibm.com/NGP-TWC/ml-planning/issues/52086#issuecomment-142331516
class TB1(CognitoTransformer):
    def __init__(
        self,
        tans_class,
        name,
        datatypes,
        feat_constraints,
        tgraph=None,
        apply_all=True,
        col_names=None,
        col_dtypes=None,
        col_as_json_objects=None,
    ):
        super().__init__()
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_as_json_objects = col_as_json_objects
        self.tans_class = tans_class
        self.tgraph = tgraph
        self.apply_all = apply_all

        if name is not None:
            self.name = name
        else:
            self.name = tans_class.__class__.__name__

        self.datatypes = datatypes
        if feat_constraints is None:
            self.feat_constraints = []
        else:
            self.feat_constraints = feat_constraints

        self.uid = "TB1-" + str(name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid

    def transform(self, X, n_jobs=1, return_new_cols_only=False):
        if self.apply_all is False and X.shape[1] != 1:
            logger.warning(
                " More than admissible number of columns provided for transform with apply_all=False for transform "
                + self.name
            )
            return None

        new_col_dtypes = []
        new_col_names = []
        new_column_as_json_objects = []
        if self.tgraph is not None and self.tgraph.multiprocessing:
            with multiprocessing.Pool(n_jobs) as pool:
                final_arrays_list = pool.starmap(self.exec_tr, [(i, X) for i in range(0, len(self.colids_))])
        else:
            final_arrays_list = []
            for i in range(0, len(self.colids_)):
                base_col_name = self.col_names_[self.colids_[i]]
                base_col_as_json_object = self.col_as_json_objects_[self.colids_[i]]
                nc = self.exec_tr(i, X)
                if type(nc).__name__ == "csr_matrix":
                    outcol_df = nc.toarray()
                elif type(nc).__name__ == "tuple":
                    outcol_df = TGen.get_df_from_tuple_of_series([nc[0], nc[1]]).values()
                elif type(nc).__name__ == "ndarray":
                    outcol_df = nc
                elif type(nc).__name__ == "DataFrame":
                    outcol_df = nc.values
                elif type(nc).__name__ == "Series":
                    outcol_df = nc.values[..., None]
                else:
                    outcol_df = nc.toarray()

                if len(outcol_df.shape) == 1:
                    ocolcnt = 1
                else:
                    ocolcnt = outcol_df.shape[1]

                if ocolcnt == 1:
                    outcol_df = DataUtils.replace_nan_and_inf(outcol_df)
                    cname = DataUtils.get_unique_column_name(
                        self.name + "(" + str(base_col_name) + ")", self.col_names_ + new_col_names
                    )
                    new_col_names.append(cname)
                    new_col_dtypes.append(outcol_df.dtype)
                    # new_column_as_json_objects.append({'expression': {'op': self.name, 'params': [base_col_as_json_object]}})
                    new_column_as_json_objects.append(
                        {
                            JSON_FUNCTION_NAME_TOKEN: self.name,
                            JSON_TYPE_TOKEN: JSON_TYPE_FUNCTION_VALUE,
                            JSON_PARAMETER_TOKEN: [base_col_as_json_object],
                        }
                    )
                    if len(outcol_df.shape) == 1:
                        final_arrays_list.append(outcol_df[..., None])
                    else:
                        final_arrays_list.append(outcol_df)
                else:
                    for i in range(0, ocolcnt):
                        new_col = DataUtils.replace_nan_and_inf(outcol_df[:, i])
                        final_arrays_list.append(new_col[..., None])
                        cname = DataUtils.get_unique_column_name(
                            self.name + "_" + str(i) + "(" + str(base_col_name) + ")",
                            self.col_names_ + new_col_names,
                        )
                        new_col_names.append(cname)
                        new_col_dtypes.append(nc.dtype)
                        # new_column_as_json_objects.append({'expression': {'op': self.name + "_" + str(i), 'params': [base_col_as_json_object]}})
                        new_column_as_json_objects.append(
                            {
                                JSON_FUNCTION_NAME_TOKEN: self.name + "_" + str(i),
                                JSON_TYPE_TOKEN: JSON_TYPE_FUNCTION_VALUE,
                                JSON_PARAMETER_TOKEN: [base_col_as_json_object],
                            }
                        )

        self.new_column_names_ = new_col_names
        self.new_column_dtypes_ = new_col_dtypes
        self.new_column_as_json_objects_ = new_column_as_json_objects
        return self.safe_computed_columns(final_arrays_list, X, return_new_cols_only)

    def get_candidates_space_descriptor(self, df, col_names, col_dtypes):
        desc = CandidatesSpaceDescriptor()

        col_ids = []
        for col_id in range(0, df.shape[1]):
            ty = str(col_dtypes[col_id])
            if ty in self.datatypes and self.all_fc_satisifed(df[:, col_id], col_names[col_id]):
                col_ids.append(col_id)

        desc.add_dimension_spec(col_ids)
        return desc

    def get_candidates(self, df, col_names, col_dtypes):
        col_ids = []
        for col_id in range(0, df.shape[1]):
            ty = str(col_dtypes[col_id])
            if ty in self.datatypes and self.all_fc_satisifed(df[:, col_id], col_names[col_id]):
                col_ids.append(col_id)

        desc = self.get_candidates_space_descriptor(df, col_names, col_dtypes)
        search_space_size = desc.get_size()
        if search_space_size != len(col_ids):
            assert search_space_size == len(col_ids)

        return col_ids

    def namestr(self, obj, namespace):
        return [name for name in namespace if namespace[name] is obj]

    def fit(self, X, y, col_names=None, col_dtypes=None, col_as_json_objects=None):
        if col_names is None:
            col_names = self.col_names
        if col_dtypes is None:
            col_dtypes = self.col_dtypes
        if col_as_json_objects is None:
            if self.col_as_json_objects is None and col_names is not None:
                col_as_json_objects = [DataUtils.get_json_for_name(name) for name in col_names]
            else:
                col_as_json_objects = self.col_as_json_objects
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_names_ = col_names
        self.col_dtypes_ = col_dtypes
        self.col_as_json_objects_ = col_as_json_objects
        self.datatypes = resolve_basic_datatypes(self.datatypes)

        if self.apply_all:
            tree_desc = self.get_candidates_space_descriptor(X, col_names, col_dtypes)
            self.colids_ = None
            if self.tgraph is not None and self.tgraph.max_feature_generate_one_node is not None:
                self.colids_ = self.reduce_count_of_candidates_from_search_space_descriptor(
                    tree_desc, self.tgraph.max_feature_generate_one_node
                )
            if self.colids_ is None:
                self.colids_ = self.get_candidates(X, col_names, col_dtypes)

        else:
            if X.shape[1] != 1:
                logger.warning("More columns than 1 provided for apply_all in transform " + self.name)
                return None
            self.colids_ = [0]

        # if self.apply_all:
        #     self.colids_ = self.get_candidates(X, col_names, col_dtypes)
        # else:
        #     if X.shape[1] != 1:
        #         return None
        #
        #     self.colids_ = [0]
        #
        # if self.tgraph is not None and self.tgraph.max_feature_generate_one_node is not None:
        #     self.colids_ = self.reduce_count_of_candidates(self.colids_, self.tgraph.max_feature_generate_one_node)

        self.tobjects_ = []
        for col_id in self.colids_:
            tobj = self.tans_class()
            trained_tobj = tobj.fit(X[:, col_id].reshape(-1, 1))
            if trained_tobj is not None:
                tobj = trained_tobj
            self.tobjects_.append(tobj)

        return self

    def all_fc_satisifed(self, dfc, dfcname):
        for fc in self.feat_constraints:
            fcname = fc.__name__
            if self.tgraph is not None and self.tgraph.fcache_contains_key(fcname, dfcname):
                res = self.tgraph.does_col_satisfy_fc(fcname, dfcname)
            else:
                res = fc(dfc)
                if self.tgraph is not None:
                    self.tgraph.add_to_fc_cache(fcname, dfcname, res)
            if res is False:
                return False

        return True

    def exec_tr(self, i, df_):
        in_col = df_[:, self.colids_[i]]
        new_cols = self.tobjects_[i].transform(in_col.reshape(-1, 1))
        new_cols = DataUtils.replace_nan_and_inf(new_cols)
        return new_cols


class TB2(CognitoTransformer):
    def __init__(
        self,
        tans_class,
        name,
        datatypes1,
        feat_constraints1,
        datatypes2,
        feat_constraints2,
        tgraph=None,
        apply_all=True,
    ):
        super().__init__()
        self.apply_all = apply_all
        self.tgraph = tgraph
        self.tans_class = tans_class
        if name is not None:
            self.name = name
        else:
            self.name = tans_class.__class__.__name__

        self.datatypes1 = datatypes1
        self.datatypes2 = datatypes2

        if feat_constraints1 is None:
            self.feat_constraints1 = []
        else:
            self.feat_constraints1 = feat_constraints1

        if feat_constraints2 is None:
            self.feat_constraints2 = []
        else:
            self.feat_constraints2 = feat_constraints2

        self.uid = "TB2-" + str(name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid

    def transform(self, X, n_jobs=1, return_new_cols_only=False):
        df_ = pd.DataFrame(X)
        df1_ = df_.copy(deep=False)
        cnt = -1
        for pair in self.col_id_pairs_:
            cnt += 1
            col1_id = pair[0]
            col2_id = pair[1]
            in_col1 = pd.DataFrame(df_.iloc[:, col1_id])
            in_col2 = pd.DataFrame(df_.iloc[:, col2_id])

            new_cols = self.tobjects_[cnt].transform(in_col1, in_col2)
            if type(new_cols).__name__ == "Series":
                ndf = pd.DataFrame(new_cols.as_matrix())
            elif type(new_cols).__name__ == "csr_matrix":
                ndf = pd.DataFrame(new_cols.todense())
            else:
                ndf = pd.DataFrame(new_cols)

            for n_cname in list(ndf.columns):
                new_col = ndf[n_cname]
                if len(ndf.columns) == 1:
                    new_full_name = (
                        self.name + "(" + str(df_.iloc[:, col1_id].name) + "__" + str(df_.iloc[:, col2_id].name) + ")"
                    )
                else:
                    new_full_name = (
                        self.name
                        + "_"
                        + str(n_cname)
                        + "("
                        + str(df_.iloc[:, col1_id].name)
                        + "__"
                        + str(df_.iloc[:, col2_id].name)
                        + ")"
                    )
                new_full_name = DataUtils.get_unique_column_name(new_full_name, df1_.columns)
                df1_[new_full_name] = new_col.values

        df1_ = df1_.replace([np.nan, np.inf, -np.inf], 0)
        if df1_.isnull().any().any():
            logger.debug(
                "Null values in newly transformed df through %s : %s " % (self.name, str(df1_.isnull().any().any()))
            )

        del df_
        return df1_

    def get_candidates_space_descriptor(self, df, col_names, col_dtypes):
        desc = CandidatesSpaceDescriptor()

        matching_colids1 = []
        for col1 in list(df.columns):
            ty1 = str(df[col1].dtype)
            if ty1 in self.datatypes1 and self.all_fc1_satisifed(df[col1]):
                matching_colids1.append(col1)

        matching_colids2 = []
        for col2 in list(df.columns):
            ty2 = str(df[col2].dtype)
            if ty2 in self.datatypes2 and self.all_fc2_satisifed(df[col2]):
                matching_colids2.append(col2)

        desc.add_dimension_spec(matching_colids1)
        desc.add_dimension_spec(matching_colids2)
        return desc

    def get_candidates(self, df):
        colpairnames = []
        for col1 in list(df.columns):
            ty1 = str(df[col1].dtype)
            if ty1 in self.datatypes1 and self.all_fc1_satisifed(df[col1]):
                for col2 in list(df.columns):
                    if col1 == col2:
                        continue
                    ty2 = str(df[col2].dtype)
                    if ty2 in self.datatypes2 and self.all_fc2_satisifed(df[col2]):
                        colpairnames.append((col1, col2))

        return colpairnames

    def namestr(self, obj, namespace):
        return [name for name in namespace if namespace[name] is obj]

    def fit(self, X, y):
        self.datatypes1 = resolve_basic_datatypes(self.datatypes1)
        self.datatypes2 = resolve_basic_datatypes(self.datatypes2)
        df = pd.DataFrame(X)
        self.col_id_pairs_ = self.get_candidates(df)

        if self.tgraph is not None and self.tgraph.max_feature_generate_one_node is not None:
            self.col_id_pairs_ = self.reduce_count_of_candidates(
                self.col_id_pairs_, self.tgraph.max_feature_generate_one_node
            )

        self.tobjects_ = []
        for col_id_pair in self.col_id_pairs_:
            tobj = self.tans_class()
            trained_tobj = tobj.fit(df[df.iloc[:, col_id_pair[0]].name, df.iloc[:, col_id_pair[1]].name])
            if trained_tobj is not None:
                tobj = trained_tobj
            self.tobjects_.append(tobj)

        return self

    def all_fc1_satisifed(self, dfc):
        dfcname = dfc.name
        for fc in self.feat_constraints1:
            fcname = fc.__name__
            if self.tgraph is not None and self.tgraph.fcache_contains_key(fcname, dfcname):
                res = self.tgraph.does_col_satisfy_fc(fcname, dfcname)
            else:
                res = fc(dfc)
                if self.tgraph is not None:
                    self.tgraph.add_to_fc_cache(fcname, dfcname, res)
            if res is False:
                return False
        return True

    def all_fc2_satisifed(self, dfc):
        dfcname = dfc.name
        for fc in self.feat_constraints2:
            fcname = fc.__name__
            if self.tgraph is not None and self.tgraph.fcache_contains_key(fcname, dfcname):
                res = self.tgraph.does_col_satisfy_fc(fcname, dfcname)
            else:
                res = fc(dfc)
                if self.tgraph is not None:
                    self.tgraph.add_to_fc_cache(fcname, dfcname, res)
            if res is False:
                return False

        return True


class TAM(CognitoTransformer):
    def __init__(
        self, tans_class, name, tgraph=None, apply_all=True, col_names=None, col_dtypes=None, col_as_json_objects=None
    ):
        super().__init__()
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_as_json_objects = col_as_json_objects
        self.apply_all = apply_all
        self.tgraph = tgraph
        self.tans_class = tans_class
        if name is not None:
            self.name = name
        else:
            self.name = tans_class.__class__.__name__
        self.uid = "TAM-" + str(name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid

    def get_candidates_space_descriptor(self, df, col_names, col_dtypes):
        return SingletonCandidateSpaceDescriptor(tuple(range(0, df.shape[1])))

    def get_candidates(self, df, col_names, col_dtypes):
        assert [self.get_candidates_space_descriptor(df, col_names, col_dtypes).get_candidate(0)] == [
            tuple(range(0, df.shape[1]))
        ]

        return [tuple(range(0, df.shape[1]))]

    def fit(self, X, y, col_names=None, col_dtypes=None, col_as_json_objects=None):
        if col_names is None:
            col_names = self.col_names
        if col_dtypes is None:
            col_dtypes = self.col_dtypes
        if col_as_json_objects is None:
            if self.col_as_json_objects is None and col_names is not None:
                col_as_json_objects = [DataUtils.get_json_for_name(name) for name in col_names]
            else:
                col_as_json_objects = self.col_as_json_objects
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        self.col_names_ = col_names
        self.col_dtypes_ = col_dtypes
        self.col_as_json_objects_ = col_as_json_objects
        self.trans_class_obj_ = self.get_obj_clone_or_new_class_obj(self.tans_class)
        cands = self.get_candidates(X, col_names, col_dtypes)
        self.cands = cands

        if np.isinf(X.T @ X).any():
            X = X.astype(np.float64)
            trained_trans_class_obj_ = self.trans_class_obj_.fit(X[:, list(cands[0])])
        else:
            trained_trans_class_obj_ = self.trans_class_obj_.fit(X[:, list(cands[0])])

        if trained_trans_class_obj_ is not None:
            self.trans_class_obj_ = trained_trans_class_obj_
        return self

    def transform(self, X, n_jobs=1, return_new_cols_only=False):
        sel_df = X[:, list(self.cands[0])]
        Xtr = self.trans_class_obj_.transform(sel_df)
        Xtr = DataUtils.replace_nan_and_inf(Xtr)
        new_col_names = []
        new_col_dtypes = []
        new_column_as_json_objects = []
        for i in range(0, Xtr.shape[1]):
            nfullname = self.name + "_" + str(i)
            nfullname = DataUtils.get_unique_column_name(nfullname, new_col_names + self.col_names_)
            new_col_names.append(nfullname)
            new_col_dtypes.append(Xtr[:, i].dtype)
            new_column_as_json_objects.append(DataUtils.get_json_for_name(nfullname))

        self.new_column_names_ = new_col_names
        self.new_column_dtypes_ = new_col_dtypes
        self.new_column_as_json_objects_ = new_column_as_json_objects
        if return_new_cols_only:
            return Xtr
        else:
            return np.concatenate((X, Xtr), 1)


class TransformBase:
    @staticmethod
    def ValidatedTransformNames(list_names):
        n_names = list(set(list_names))
        listAllTr = TransformBase.GetAllTransformNames()
        for name in n_names:
            if name not in listAllTr:
                n_names.remove(name)

        return n_names

    @staticmethod
    def GetAllTransformNames():
        return [
            "sqrt",
            "log",
            "round",
            "square",
            "cbrt",
            "sin",
            "cos",
            "tan",
            "abs",
            "sigmoid",
            "freq",
            "product",
            "max",
            "diff",
            "sum",
            "divide",
            "stdscaler",
            "minmaxscaler",
            "pca",
            "groupbymean",
            "groupbystd",
            "groupbymin",
            "groupbymax",
            "groupbymedian",
            "nxor",
            "cube",
            "nystroem",
            "featureagglomeration",
            "binning",
            "clusterdbscan",
            "isoforestanomaly",
        ]
        # 'dtextr' exp,'onehot', 'pair', 'min', 'tanh', 'distance', 'm_distance', 'speed', 'ica' have been ommitted

    @staticmethod
    def GetAllUnaryTransformNames():
        return [
            "sqrt",
            "log",
            "round",
            "square",
            "cbrt",
            "tanh",
            "sin",
            "cos",
            "tan",
            "abs",
            "sigmoid",
            "freq",
        ]
        # ,'onehot']#, 'stdscaler', 'minmaxscaler']

    @staticmethod
    def GetAllBinaryTransformNames():
        return [
            "product",
            "min",
            "max",
            "diff",
            "sum",
            "divide",
            "groupbystd",
            "groupbymean",
            "groupbymin",
            "groupbymax",
            "groupbymedian",
        ]

    @staticmethod
    def GetCommutativeTransformNames():
        return ["product", "min", "max", "sum"]

    @staticmethod
    def GetTransformObj(trName, tgraph=None, apply_all=True):
        from autoai_libs.cognito.transforms.transform_extras import (
            NXOR,
            ClusterDBSCAN,
            Frequency,
            GroupByMax,
            GroupByMean,
            GroupByMedian,
            GroupByMin,
            GroupByStd,
            IsolationForestAnomaly,
        )

        if trName == "sqrt":
            return TA1(
                np.sqrt,
                "sqrt",
                ["numeric"],
                [FC.is_non_negative, FC.is_not_categorical],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "log":
            return TA1(
                np.log, "log", ["numeric"], [FC.is_positive, FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all
            )
        if trName == "exp":
            return TA1(np.exp, "exp", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "round":
            return TA1(np.rint, "round", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "square":
            return TA1(np.square, "square", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "cube":
            return TA1(TExtras.cube, "cube", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "cbrt":
            return TA1(np.cbrt, "cbrt", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "tanh":
            return TA1(np.tanh, "tanh", ["float"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "sin":
            return TA1(np.sin, "sin", ["float"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "cos":
            return TA1(np.cos, "cos", ["float"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "tan":
            return TA1(np.tan, "tan", ["float"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "abs":
            return TA1(np.absolute, "abs", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all)
        if trName == "sigmoid":
            return TA1(
                TExtras.sigmoid, "sigmoid", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all
            )
        if trName == "freq":
            return TB1(Frequency, "freq", ["int"], [FC.is_lt80pc_unique_int], tgraph=tgraph, apply_all=apply_all)
        if trName == "product":
            return TA2(
                np.multiply,
                "product",
                ["numeric"],
                [FC.is_not_categorical],
                ["numeric"],
                [FC.is_not_categorical],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "sum":
            return TA2(
                np.add,
                "sum",
                ["numeric"],
                [FC.is_not_categorical],
                ["numeric"],
                [FC.is_not_categorical],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "diff":
            return TA2(
                np.subtract,
                "diff",
                ["numeric"],
                [FC.is_not_categorical],
                ["numeric"],
                [FC.is_not_categorical],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "min":
            return TA2(
                np.fmin,
                "min",
                ["numeric"],
                [FC.is_not_categorical],
                ["numeric"],
                [FC.is_not_categorical],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "max":
            return TA2(
                np.fmax,
                "max",
                ["numeric"],
                [FC.is_not_categorical],
                ["numeric"],
                [FC.is_not_categorical],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "divide":
            return TA2(
                np.true_divide,
                "divide",
                ["numeric"],
                [FC.is_not_categorical],
                ["numeric"],
                [FC.is_not_categorical],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "onehot":
            return TB1(
                OneHotEncoder,
                "onehot",
                ["int"],
                [FC.is_categorical, FC.is_positive],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "stdscaler":
            return TB1(
                StandardScaler, "stdscaler", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all
            )
        if trName == "minmaxscaler":
            return TB1(
                MinMaxScaler, "minmaxscaler", ["numeric"], [FC.is_not_categorical], tgraph=tgraph, apply_all=apply_all
            )
        if trName == "pca":
            return TAM(PCA(), "pca", tgraph=tgraph, apply_all=apply_all)
        if trName == "ica":
            return TAM(FastICA(), "ica", tgraph=tgraph, apply_all=apply_all)
        if trName == "nystroem":
            return TAM(Nystroem(n_components=10), "nystroem", tgraph=tgraph, apply_all=apply_all)
        if trName == "featureagglomeration":
            return TAM(FeatureAgglomeration(), "featureagglomeration", tgraph=tgraph, apply_all=apply_all)
        if trName == "groupbymean":
            return TGen(
                GroupByMean,
                "groupbymean",
                2,
                [["int"], ["numeric"]],
                [[FC.is_lt80pc_unique_int], [FC.is_not_categorical]],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "groupbystd":
            return TGen(
                GroupByStd,
                "groupbystd",
                2,
                [["int"], ["numeric"]],
                [[FC.is_lt80pc_unique_int], [FC.is_not_categorical]],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "groupbymin":
            return TGen(
                GroupByMin,
                "groupbymin",
                2,
                [["int"], ["numeric"]],
                [[FC.is_lt80pc_unique_int], [FC.is_not_categorical]],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "groupbymax":
            return TGen(
                GroupByMax,
                "groupbymax",
                2,
                [["int"], ["numeric"]],
                [[FC.is_lt80pc_unique_int], [FC.is_not_categorical]],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "groupbymedian":
            return TGen(
                GroupByMedian,
                "groupbymedian",
                2,
                [["int"], ["numeric"]],
                [[FC.is_lt80pc_unique_int], [FC.is_not_categorical]],
                tgraph=tgraph,
                apply_all=apply_all,
            )

        if trName == "nxor":
            return TGen(
                NXOR,
                "nxor",
                2,
                [["numeric"], ["numeric"]],
                [[FC.is_not_categorical], [FC.is_not_categorical]],
                tgraph=tgraph,
                apply_all=apply_all,
            )
        if trName == "binning":
            return TGen(
                KBinsDiscretizer(n_bins=10, encode="ordinal", strategy="uniform"),
                "binning",
                1,
                [["numeric"]],
                [[FC.is_not_categorical]],
                tgraph=tgraph,
                apply_all=apply_all,
            )

        if trName == "clusterdbscan":
            return TAM(ClusterDBSCAN, "clusterdbscan", tgraph=tgraph, apply_all=apply_all)
        if trName == "isoforestanomaly":
            return TAM(IsolationForestAnomaly, "isoforestanomaly", tgraph=tgraph, apply_all=apply_all)
