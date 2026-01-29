################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import logging

import numpy as np

from .general_transformer import AutoAITransformer

logger = logging.getLogger("autoai_libs")


class SmallDataTransformer(AutoAITransformer):
    def __init__(self):
        super().__init__()

    def is_valid(self, X: np.ndarray) -> bool:
        try:
            self.fit_transform(X)
            return True
        except Exception as e:
            logger.warning(
                "Transfomer {0}, error in fit_transform, type(X): {1}, error={2!s}".format(
                    self.__class__.__name__, type(X), e
                ),
                exc_info=e,
            )
            return False
