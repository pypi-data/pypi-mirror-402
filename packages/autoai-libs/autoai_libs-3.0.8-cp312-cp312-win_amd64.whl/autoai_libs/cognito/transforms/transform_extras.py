################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2019-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################


import uuid

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

import autoai_libs.utils.fc_methods as FC
from autoai_libs.cognito.transforms.sklearn_compat import CognitoTransformer

try:
    from sklearn.preprocessing import Imputer
except ImportError:
    from sklearn.impute import SimpleImputer as Imputer

import logging

logger = logging.getLogger("autoai_libs")


class ImputerWrapper:
    def __init__(self):
        self.sklimputr = Imputer()
        self.name = "Imputer"
        self.uid = "TA2-" + str(self.name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid

    def fit(self, X, y):
        self.sklimputr.fit(X, y)
        self.dtypes_ = X.dtypes
        return self

    def transform(self, X):
        Xnew = self.sklimputr.transform(X)
        Xnewdf = pd.DataFrame(Xnew, columns=X.columns).astype(dtype=dict(self.dtypes_))
        # needs to change where the column names are taken from X noT from saved dtype
        return Xnewdf


class StringLabeler:
    def __init__(self, drop_string_cols=True, datetime_to_epoch=True, col_names=None, col_dtypes=None):
        self.drop_string_cols = drop_string_cols
        self.datetime_to_epoch = datetime_to_epoch
        self.name = "StringLabeler"
        self.uid = "TA2-" + str(self.name) + "_" + str(uuid.uuid4())
        self.long_name = self.uid
        self.col_names = col_names
        self.col_dtypes = col_dtypes
        return

    def fit(self, X, y, col_names=None, col_dtypes=None):
        if col_names is None:
            col_names = self.col_names
        if col_dtypes is None:
            col_dtypes = self.col_dtypes
        self.col_names_ = col_names
        self.col_dtypes_ = col_dtypes
        self.col_count_ = X.shape[1]
        self.string_feats_ = []
        self.string_categorical_feats_ = []
        self.label_maps_ = {}
        self.string_datetime_feats_ = []

        for i in range(self.col_count_):
            if col_dtypes[i] == "object":
                self.string_feats_.append(i)
                if self.datetime_to_epoch is True and FC.is_string_in_datetime_format(X[:, i]):
                    self.string_datetime_feats_.append(i)
                    continue
                if FC.is_categorical(X[:, i]):
                    self.string_categorical_feats_.append(i)
                    lm = self.get_label_map(X[:, i])
                    self.label_maps_[i] = lm

        return self

    def transform(self, X):
        tr_col_count = X.shape[1]
        new_cols_arr = []
        self.new_column_names_ = []
        self.new_column_dtypes_ = []
        if tr_col_count != self.col_count_:
            raise ValueError(
                "Input dimensions not the same as in fit (%s) and predict (%s)"
                % (str(self.col_count_), str(tr_col_count))
            )
        for colid in range(tr_col_count):
            if colid in self.string_categorical_feats_:
                dfc_new = self.get_labels(X[:, colid], self.label_maps_[colid])
                new_cname = str(self.col_names_[colid]) + "__catlist"
                new_dtype = np.dtype(np.int16)
                # new_cat_columns.append(dfc_new)
            elif colid in self.string_datetime_feats_:
                dfc_new = self.get_epochs_from_datetime(X[:, colid])
                new_cname = str(self.col_names_[colid]) + "__dt"
                new_dtype = np.dtype(np.int64)
                # new_dt_columns.append(dfc_new)
            elif colid in self.string_feats_:
                continue
            else:
                dfc_new = X[:, colid].astype(self.col_dtypes_[colid])
                new_cname = self.col_names_[colid]
                new_dtype = self.col_dtypes_[colid]
            new_cols_arr.append(dfc_new[..., None])
            self.new_column_names_.append(new_cname)
            self.new_column_dtypes_.append(new_dtype)

        if self.drop_string_cols is True:
            retained_old_columns = list(set(range(tr_col_count)) - set(self.string_feats_))
        else:
            retained_old_columns = list(range(tr_col_count))

        Xtr = np.concatenate(tuple(new_cols_arr), 1)

        expected_nb_cols = (
            X.shape[1] - len(self.string_feats_) - len(self.string_categorical_feats_ + self.string_datetime_feats_)
        )
        assert Xtr.shape[1] == expected_nb_cols
        return Xtr

    def get_epochs_from_datetime(self, column):
        return pd.to_datetime(column).astype(np.int64).values

    @staticmethod
    def get_labels(column, label_map):
        func = np.vectorize(lambda x: (label_map[x]) if x in label_map.keys() else -1)
        ret = func(column)
        return ret
        ser = pd.Series()
        for val in column:
            if val in label_map.keys():
                ser.append(label_map[val])
            else:
                ser.append(-1)

        return ser

    @staticmethod
    def get_label_map(dfc):
        h = {}
        lab_ctr = 0
        for val in dfc:
            if val in h.keys():
                continue
            else:
                h[val] = lab_ctr
                lab_ctr += 1

        return h


class Frequency:
    def fit(self, X, y=None):
        Xdf = pd.DataFrame(X)
        colname = Xdf.columns[0]
        self.hsh_ = Xdf.groupby([colname])[colname].count()
        return self

    def transform(self, X):
        Xdf = pd.DataFrame(X)
        # fun = lambda x: self.hsh_[x]
        X_tr = self.get_hsh(Xdf.iloc[:, 0])
        return X_tr

    def get_hsh(self, x):
        return self.hsh_[x]


class GroupByMean:
    def fit(self, X, y=None):
        Xdf = pd.DataFrame(X)
        cnames = Xdf.columns
        try:
            self.aggs = Xdf.groupby(cnames[0]).mean()[cnames[1]]
            del Xdf
        except Exception as e:
            logger.debug(X.columns)
            raise e
        return self

    def transform(self, X):
        Xdf = pd.DataFrame(X)
        # fun = lambda x: self.aggs[x]
        X_tr = self.get_val(Xdf.iloc[:, 0])
        del Xdf
        return X_tr

    def get_val(self, x):
        return self.aggs[x]


class GroupByStd:
    def fit(self, X, y=None):
        Xdf = pd.DataFrame(X)
        cnames = Xdf.columns
        try:
            self.aggs = Xdf.groupby(cnames[0]).std(numeric_only=True)[cnames[1]]
            del Xdf
        except Exception as e:
            logger.debug(X.columns)
            raise e
        return self

    def transform(self, X):
        Xdf = pd.DataFrame(X)
        # fun = lambda x: self.aggs[x]
        X_tr = self.get_val(Xdf.iloc[:, 0])
        del Xdf
        return X_tr

    def get_val(self, x):
        return self.aggs[x]


class GroupByMedian:
    def fit(self, X, y=None):
        Xdf = pd.DataFrame(X)
        cnames = Xdf.columns
        try:
            self.aggs = Xdf.groupby(cnames[0]).median(numeric_only=True)[cnames[1]]
            del Xdf
        except Exception as e:
            logger.debug(Xdf.columns)
            raise e
        return self

    def transform(self, X):
        Xdf = pd.DataFrame(X)
        # fun = lambda x: self.aggs[x]
        X_tr = self.get_val(Xdf.iloc[:, 0])
        del Xdf
        return X_tr

    def get_val(self, x):
        return self.aggs[x]


class GroupByMin:
    def fit(self, X, y=None):
        Xdf = pd.DataFrame(X)
        cnames = Xdf.columns
        try:
            self.aggs = Xdf.groupby(cnames[0]).min()[cnames[1]]
            del Xdf
        except Exception as e:
            logger.debug(Xdf.columns)
            raise e
        return self

    def transform(self, X):
        Xdf = pd.DataFrame(X)
        # fun = lambda x: self.aggs[x]
        X_tr = self.get_val(Xdf.iloc[:, 0])
        del Xdf
        return X_tr

    def get_val(self, x):
        return self.aggs[x]


class GroupByMax:
    def fit(self, X, y=None):
        Xdf = pd.DataFrame(X)
        cnames = Xdf.columns
        try:
            self.aggs = Xdf.groupby(cnames[0]).max()[cnames[1]]
            del Xdf
        except Exception as e:
            logger.debug(Xdf.columns)
            raise e
        return self

    def transform(self, X):
        Xdf = pd.DataFrame(X)
        # fun = lambda x: self.aggs[x]
        X_tr = self.get_val(Xdf.iloc[:, 0])
        del Xdf
        return X_tr

    def get_val(self, x):
        return self.aggs[x]


class NXOR:
    def fit(self, X, y=None):
        c1 = X[:, 0]
        c2 = X[:, 1]
        self.m1 = np.mean(c1)
        self.m2 = np.mean(c2)
        return self

    def transform(self, X):
        c1 = X[:, 0]
        c2 = X[:, 1]
        return (c1 - self.m1) * (c2 - self.m2)


class ClusterDBSCAN:
    def fit(self, X, y=None):
        scaler = StandardScaler()
        scaler.fit(X)
        X_scaled = scaler.transform(X)
        clustering = DBSCAN(min_samples=10).fit(X_scaled)
        self.scaler = scaler
        cluster_labels = clustering.labels_
        self.knn = KNeighborsClassifier(n_neighbors=7)
        self.knn.fit(X_scaled, cluster_labels)
        return self

    def transform(self, X):
        X_scaled = self.scaler.transform(X)
        return self.knn.predict(X_scaled)[..., None]


class IsolationForestAnomaly:
    def fit(self, X, y=None):
        self.isoforest = IsolationForest(random_state=0)
        self.isoforest.fit(X)
        return self

    def transform(self, X):
        return self.isoforest.predict(X)[..., None]


class ToValues(CognitoTransformer):
    def __init__(self):
        super().__init__()
        self.uid = "TV-" + "_" + str(uuid.uuid4())
        self.long_name = self.uid
        self.name = self.long_name

    def fit(self, X, y):
        return self

    def transform(self, X):
        return X.values


# class StringLabeler2:
#
#     def __init__(self, method, estimator, scorer, verbose=False):
#         # method values: best, majority, label, target, binary, onehot, backward-diff, sum, polynomial
#         self.method = method
#         self.estimator = estimator
#         self.scorer = scorer
#         self.verbose = verbose
#
#         self.all_methods = ['best', 'majority', 'label', 'target', 'binary', 'onehot', 'backward-diff', 'sum',
#                             'polynomial']
#         self.all_encoders = ['label', 'target', 'binary', 'onehot', 'backward-diff', 'sum', 'polynomial']
#
#         if self.method not in self.all_methods:
#             return None
#
#     def fit(self, X, y, X_bigger=None):
#         # X_bigger possibly includes X_train + X_test (in order to know all labels)
#
#         if self.method not in self.all_encoders:
#             from cognito.eda import EDATools
#             res_df = EDATools().explore_numeric_representations_for_discreet_variables(X, y, self.estimator,
#                                                                                        self.scorer,
#                                                                                        verbose=self.verbose,
#                                                                                        X_bigger=X_bigger)
#
#         # divide into num columns and obj columns and record which ones are which.
#         # for each obj column, check (according to method), which encoder to invoke and call the fit method on that encoder's object
#         # save each encoder object wrt to the column id
#
#         X = pd.DataFrame(X)
#         if X_bigger is not None:
#             X_bigger = pd.DataFrame(X_bigger)
#
#         X_num = X.select_dtypes(include=DataUtils.NumericDataTypes())
#         X_obj = X.select_dtypes(exclude=DataUtils.NumericDataTypes())
#
#         for cname in list(X_obj.columns):
#             most_freq = X_obj[cname].value_counts().keys()[0]
#             X_obj[cname] = X_obj[cname].replace(np.nan, most_freq)
#
#         self.obj_colids_ = []
#         self.num_colids_ = []
#         self.encoders_objects_ = {}
#         for i in range(0, len(X.columns)):
#             if X.columns[i] in list(X_obj.columns):
#                 self.obj_colids_.append(i)
#             else:
#                 self.num_colids_.append(i)
#
#         if self.method == 'majority':
#             majority_method = res_df['Best'].value_counts().keys()[0]
#
#         for i in range(0, len(X.columns)):
#             if i in self.obj_colids_:
#                 if self.method in self.all_encoders:
#                     col_method = self.method
#                 else:
#                     if self.method == 'best':
#                         col_method = list(res_df[res_df['Column_id'] == i]['Best'])[0].lower()
#                     elif self.method == 'majority':
#                         col_method = majority_method
#
#                 if col_method == 'label':
#                     encoder_obj = LabelEncoder()
#                     if X_bigger is not None:
#                         encoder_obj.fit(X_bigger.iloc[:, i].astype(str))
#                     else:
#                         encoder_obj.fit(X.iloc[:, i].astype(str))
#                 if col_method == 'target':
#                     encoder_obj = ce.TargetEncoder(cols=[X.columns[i]])
#                     encoder_obj.fit(pd.DataFrame(X.iloc[:, i]), y)
#                 if col_method == 'binary':
#                     encoder_obj = ce.BinaryEncoder(cols=[X.columns[i]])
#                     encoder_obj.fit(pd.DataFrame(X.iloc[:, i]), y)
#                 if col_method == 'onehot':
#                     encoder_obj = ce.OneHotEncoder(cols=[X.columns[i]])
#                     encoder_obj.fit(pd.DataFrame(X.iloc[:, i]), y)
#                 if col_method == 'backward-diff':
#                     encoder_obj = ce.BackwardDifferenceEncoder(cols=[X.columns[i]])
#                     encoder_obj.fit(pd.DataFrame(X.iloc[:, i]), y)
#                 if col_method == 'sum':
#                     encoder_obj = ce.SumEncoder(cols=[X.columns[i]])
#                     encoder_obj.fit(pd.DataFrame(X.iloc[:, i]), y)
#                 if col_method == 'polynomial':
#                     encoder_obj = ce.PolynomialEncoder(cols=[X.columns[i]])
#                     encoder_obj.fit(pd.DataFrame(X.iloc[:, i]), y)
#
#                 self.encoders_objects_[i] = encoder_obj
#
#         return self
#
#     def transform(self, X):
#         X = pd.DataFrame(X)
#         for i in self.obj_colids_:
#             most_freq = X.iloc[:, i].value_counts().keys()[0]
#             X.iloc[:, i] = X.iloc[:, i].replace(np.nan, most_freq)
#
#         X_num = X.iloc[:, self.num_colids_]
#         for i in self.obj_colids_:
#             tr_X_col_i = self.encoders_objects_[i].transform(pd.DataFrame(X.iloc[:, i]))
#             df_2 = pd.DataFrame(tr_X_col_i)
#             # appropriate naming
#             orig_cname = X.columns[i]
#             for new_cname in list(df_2.columns):
#                 if str(orig_cname) not in str(new_cname):
#                     new_new_cname = str(orig_cname) + '_' + str(new_cname)
#                     df_2 = df_2.rename(columns={new_cname: new_new_cname})
#             X_num = pd.concat([X_num, df_2], axis=1)
#
#         if self.verbose is True:
#             print('Original columns provided to transform(): ' + str(list(X.columns)))
#             print('Returned columns from the transform(): ' + str(list(X_num.columns)))
#
#         return X_num
