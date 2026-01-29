################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import abc


class AutoAIDetector(abc.ABC):
    """A detector determines if the data has some particular feature, such as if it is sparse or dense"""

    @abc.abstractmethod
    def detect(self) -> bool:
        """Do detection."""
        raise NotImplementedError()
