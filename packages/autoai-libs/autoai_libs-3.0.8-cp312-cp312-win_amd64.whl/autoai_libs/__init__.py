################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2019-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import logging.config
from importlib.metadata import PackageNotFoundError, distribution

from lale import register_lale_wrapper_modules

from autoai_libs.version import __version__

logging_cfg = {
    "version": 1,
    "formatters": {},
    "filters": {},
    "handlers": {},
    "loggers": {
        "autoai_libs": {"propagate": False},  # top-level library logger
    },
    "disable_existing_loggers": False,
}

logging.config.dictConfig(logging_cfg)

# In some cases lale module is not registered, so we need to make sure
# it is performed always when we use autoai_libs

register_lale_wrapper_modules("autoai_libs.lale")

# These correspond to the dependencies included in the "onnx" extra. Versions may vary between releases, so they are not specified here.
onnx_extras = [
    "onnx",
    "skl2onnx",
    "onnxruntime-extensions",
    "lightgbm",
    "onnxmltools",
    "onnxconverter-common",
    "snapml",
]

try:
    for pkg in onnx_extras:
        distribution(pkg)
except PackageNotFoundError as e:
    logging.getLogger("autoai_libs").debug(
        f"Package '{e.name}' not installed. ONNX converters not registered. Install install all required packages using the '[onnx]' extras."
    )
else:
    from . import onnx_converters  # Registers ONNX converters on import
