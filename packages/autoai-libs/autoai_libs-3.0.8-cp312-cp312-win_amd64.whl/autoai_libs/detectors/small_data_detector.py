################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import logging

from .general_detector import AutoAIDetector

logger = logging.getLogger("autoai_libs")


class SmallDataDetector(AutoAIDetector):
    def is_valid(self, *args, **kwargs) -> bool:
        try:
            self.detect(*args, **kwargs)
        except Exception as e:
            logger.warning("The detector is invalid.", exc_info=e)
            return False

        return True
