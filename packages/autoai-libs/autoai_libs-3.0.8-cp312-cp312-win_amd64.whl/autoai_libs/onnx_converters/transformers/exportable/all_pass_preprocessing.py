################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from skl2onnx import update_registered_converter

from autoai_libs.onnx_converters.utils import identity_converter, identity_parser, identity_shape_calculator
from autoai_libs.transformers.exportable import AllPassPreprocessingTransformer

transformer = AllPassPreprocessingTransformer
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    identity_shape_calculator,
    identity_converter,
    parser=identity_parser,
)
