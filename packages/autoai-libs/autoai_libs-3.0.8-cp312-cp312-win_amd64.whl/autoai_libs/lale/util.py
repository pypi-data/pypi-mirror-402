################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2024-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import lale.lib.sklearn


def wrap_pipeline_segments(orig_pipeline):
    """Wrap segments of the pipeline to mark them for pretty_print() and visualize().

    If the pipeline does not look like it came from AutoAI, just return it
    unchanged. Otherwise, find the NumpyPermuteArray operator. Everything
    before that operator is preprocessing. Everything after
    NumpyPermuteArray but before the final estimator is feature
    engineering."""
    from autoai_libs.lale.numpy_permute_array import NumpyPermuteArray

    if len(orig_pipeline.steps_list()) <= 2:
        return orig_pipeline
    estimator = orig_pipeline.get_last()
    prep = orig_pipeline.remove_last()
    cognito = None
    PREP_END = NumpyPermuteArray.class_name()
    while True:
        last = prep.get_last()
        if last is None or not last.class_name().startswith("autoai_libs.lale"):
            return orig_pipeline
        if last.class_name() == PREP_END:
            break
        prep = prep.remove_last()
        if cognito is None:
            cognito = last
        else:
            cognito = last >> cognito
    prep_wrapped = lale.lib.sklearn.Pipeline(steps=[("preprocessing_pipeline", prep)])
    if cognito is None:
        result = prep_wrapped >> estimator
    else:
        cognito_wrapped = lale.lib.sklearn.Pipeline(steps=[("feature_engineering_pipeline", cognito)])
        result = prep_wrapped >> cognito_wrapped >> estimator
    return result
