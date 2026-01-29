################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2019-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import numpy as np
from sklearn.metrics import mean_squared_error


def neg_root_mean_squared_log_error(y_true, y_pred):
    assert len(y_true) == len(y_pred)
    return -(np.square(np.log(y_pred + 1) - np.log(y_true + 1)).mean() ** 0.5)


def neg_root_mean_squared_error(y_true, y_pred):
    return -np.sqrt(mean_squared_error(y_true=y_true, y_pred=y_pred))
