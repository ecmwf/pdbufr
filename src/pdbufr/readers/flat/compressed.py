# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import eccodes
import numpy as np


class CompressedValueCache:
    def __init__(self, message, subset_count):
        self.cache = {}
        self.message = message
        self.subset_count = subset_count

    def get_multi_rank_value_mixed(self, key, value):
        # multi-rank key accessed without a rank
        if isinstance(value, np.ndarray):
            r = []
            for i_rank in range(1, 10000):
                rk = f"#{i_rank}#{key}"
                if rk in self.message:
                    v = self.message.get(rk)
                    if isinstance(v, (np.ndarray, list)):
                        r.append(v)
                    else:
                        r.append(np.asarray([v] * self.subset_count))
                else:
                    break
            return np.asarray(r).T

    def get_multi_rank_value_array(self, key, value):
        # multi-rank key accessed without a rank
        if isinstance(value, np.ndarray):
            value = value.reshape((-1, self.subset_count), order="F")
            value = value.T
            return value

    def get(self, key, subset):
        if key not in self.cache:
            value = self.message.get(key)
            if key != "unexpandedDescriptors" and isinstance(value, (np.ndarray, list)) and "#" not in key:
                # multi-rank key
                if len(value) != self.subset_count:
                    # not all ranks are full arrays (some are scalars) so we need to get all ranks
                    if len(value) % self.subset_count != 0:
                        value = self.get_multi_rank_value_mixed(key, value)
                    # all the ranks are full arrays
                    else:
                        value = self.get_multi_rank_value_array(key, value)
        else:
            value = self.value_cache[key]

        # extract compressed BUFR values. They are either numpy arrays (for numeric types)
        # or lists of strings
        if key != "unexpandedDescriptors" and isinstance(value, (np.ndarray, list)) and len(value) == self.subset_count:
            value = value[subset]

        if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
            value = None
        elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
            value = None

        return value
