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
        # only numbers can be missing. ecCodes returns a list for string arrays, so
        # in practice there is nothing to convert and the list can be used as it is
        for v in value:
            if not isinstance(v, str):
                return [convert_missing(v) for v in value]
        return value
    elif isinstance(value, np.ndarray):
        # np.where() with None always builds an object array, which is both slow to
        # create and slow to use. Only pay for it when there are missing values.
        if issubclass(value.dtype.type, np.integer):
            mask = value == eccodes.CODES_MISSING_LONG
        elif issubclass(value.dtype.type, np.floating):
            mask = value == eccodes.CODES_MISSING_DOUBLE
        else:
            return value

        if mask.any():
            value = np.where(mask, None, value)
    return value
