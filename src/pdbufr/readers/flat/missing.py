# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import eccodes  # type: ignore
import numpy as np  # type: ignore


def convert_missing_scalar(value):
    if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
        return None
    elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
        return None
    else:
        return value


def convert_missing(value):
    if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
        return None
    elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
        return None
    elif isinstance(value, list):
        return [convert_missing(v) for v in value]
    elif isinstance(value, np.ndarray):
        if issubclass(value.dtype.type, np.integer):
            value = np.where(value == eccodes.CODES_MISSING_LONG, None, value)
        elif issubclass(value.dtype.type, np.floating):
            value = np.where(value == eccodes.CODES_MISSING_DOUBLE, None, value)
    return value
