################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2019-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

"""
Schema-enhanced versions of the operators from `autoai_libs`_ to enable hyperparameter tuning.

.. _`autoai_libs`: https://pypi.org/project/autoai-libs

Operators
=========

Preprocessing any columns:

* autoai_libs.lale. `ColumnSelector`_
* autoai_libs.lale. `NumpyColumnSelector`_
* autoai_libs.lale. `NumpyReplaceMissingValues`_
* autoai_libs.lale. `float32_transform`_
* autoai_libs.lale. `NumpyPermuteArray`_

Preprocessing categorical columns:

* autoai_libs.lale. `CompressStrings`_
* autoai_libs.lale. `NumpyReplaceUnknownValues`_
* autoai_libs.lale. `boolean2float`_
* autoai_libs.lale. `CatImputer`_
* autoai_libs.lale. `CatEncoder`_

Preprocessing numeric columns:

* autoai_libs.lale. `FloatStr2Float`_
* autoai_libs.lale. `NumImputer`_
* autoai_libs.lale. `OptStandardScaler`_

Preprocessing text columns:

* autoai_libs.lale. `TextTransformer`_
* autoai_libs.lale. `TfIdfTransformer`_

Preprocessing date columns:

* autoai_libs.lale. `DateTransformer`_

Feature transformation:

* autoai_libs.lale. `TNoOp`_
* autoai_libs.lale. `TA1`_
* autoai_libs.lale. `TA2`_
* autoai_libs.lale. `TB1`_
* autoai_libs.lale. `TAM`_
* autoai_libs.lale. `TGen`_
* autoai_libs.lale. `FS1`_
* autoai_libs.lale. `FS2`_
* autoai_libs.lale. `NSFA`_

.. _`ColumnSelector`: autoai_libs.lale.column_selector.html
.. _`NumpyColumnSelector`: autoai_libs.lale.numpy_column_selector.html
.. _`CompressStrings`: autoai_libs.lale.compress_strings.html
.. _`NumpyReplaceMissingValues`: autoai_libs.lale.numpy_replace_missing_values.html
.. _`NumpyReplaceUnknownValues`: autoai_libs.lale.numpy_replace_unknown_values.html
.. _`boolean2float`: autoai_libs.lale.boolean2float.html
.. _`CatImputer`: autoai_libs.lale.cat_imputer.html
.. _`CatEncoder`: autoai_libs.lale.cat_encoder.html
.. _`float32_transform`: autoai_libs.lale.float32_transform.html
.. _`FloatStr2Float`: autoai_libs.lale.float_str2_float.html
.. _`NumImputer`: autoai_libs.lale.num_imputer.html
.. _`OptStandardScaler`: autoai_libs.lale.opt_standard_scaler.html
.. _`TextTransformer`: autoai_libs.lale.text_transformer.html
.. _`DateTransformer`: autoai_libs.lale.date_transformer.html
.. _`NumpyPermuteArray`: autoai_libs.lale.numpy_permute_array.html
.. _`TNoOp`: autoai_libs.lale.t_no_op.html
.. _`TA1`: autoai_libs.lale.ta1.html
.. _`TA2`: autoai_libs.lale.ta2.html
.. _`TB1`: autoai_libs.lale.tb1.html
.. _`TAM`: autoai_libs.lale.tam.html
.. _`TGen`: autoai_libs.lale.tgen.html
.. _`FS1`: autoai_libs.lale.fs1.html
.. _`FS2`: autoai_libs.lale.fs2.html
.. _`NSFA`: autoai_libs.lale.nsfa.html
"""

from .boolean2float import boolean2float as boolean2float
from .cat_encoder import CatEncoder as CatEncoder
from .cat_imputer import CatImputer as CatImputer
from .column_selector import ColumnSelector as ColumnSelector
from .compress_strings import CompressStrings as CompressStrings
from .date_transformer import DateTransformer as DateTransformer
from .float32_transform import float32_transform as float32_transform
from .float_str2_float import FloatStr2Float as FloatStr2Float
from .fs1 import FS1 as FS1
from .fs2 import FS2 as FS2
from .nsfa import NSFA as NSFA
from .num_imputer import NumImputer as NumImputer
from .numpy_column_selector import NumpyColumnSelector as NumpyColumnSelector
from .numpy_permute_array import NumpyPermuteArray as NumpyPermuteArray
from .numpy_replace_missing_values import NumpyReplaceMissingValues as NumpyReplaceMissingValues
from .numpy_replace_unknown_values import NumpyReplaceUnknownValues as NumpyReplaceUnknownValues
from .opt_standard_scaler import OptStandardScaler as OptStandardScaler
from .t_no_op import TNoOp as TNoOp
from .ta1 import TA1 as TA1
from .ta2 import TA2 as TA2
from .tam import TAM as TAM
from .tb1 import TB1 as TB1
from .text_transformer import TextTransformer as TextTransformer
from .tf_idf_transformer import TfIdfTransformer as TfIdfTransformer
from .tgen import TGen as TGen
from .util import wrap_pipeline_segments as wrap_pipeline_segments

# Note: all imports should be done as
# from .xxx import XXX as XXX
# this ensures that pyright considers them to be publicly available
# and not private imports (this affects lale users that use pyright)
