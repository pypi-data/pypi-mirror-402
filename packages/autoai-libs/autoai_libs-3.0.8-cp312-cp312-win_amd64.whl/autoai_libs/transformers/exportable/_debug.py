################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2019-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import logging

import sklearn

# TODO: Remove sklearn version check in the next RT (25.2 or 26.1)
sklearn_version_list = sklearn.__version__.split(".")
global_sklearn_version_family = sklearn_version_list[1]
if sklearn_version_list[0] == "1":
    global_sklearn_version_family = sklearn_version_list[0]

debug_transform_return = False
debug_timings = False

logger = logging.getLogger("autoai_libs")
