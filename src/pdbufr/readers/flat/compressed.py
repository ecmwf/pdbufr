# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import numpy as np

from .missing import convert_missing


class CompressedValueCache:
    def __init__(self, message, subset_count):
        self.cache = {}
        self.multi_cache = {}
        self.message = message
        self.subset_count = subset_count

    def get(self, key, subset):
        non_header = key != "unexpandedDescriptors"

        if non_header:
            if key not in self.cache:
                if non_header:
                    # concrete rank key
                    if key.startswith("#"):
                        value = convert_missing(self.message.get(key))
                        self.cache[key] = value
                    # multirank key. The name does not contain the rank, e.g. "timePeriod". The values
                    # are stored as a 2D list/numpy array ach element containing the value for a given subset.
                    # So the values for a given element are the values for each rank with increasing rank
                    # order.
                    else:
                        value = self.get_multi_rank_value(key)
                        self.cache[key] = value
            else:
                value = self.cache[key]

            if isinstance(value, (list, np.ndarray)) and len(value) == self.subset_count:
                return value[subset]
            else:
                return value

        else:
            return self.message.get(key)

    def get_multi_rank_value(self, key):
        # multi-rank key accessed without a rank
        r = []
        for i_rank in range(1, 1000000):
            rk = f"#{i_rank}#{key}"
            if rk in self.message:
                v = self.message.get(rk)
                if isinstance(v, (np.ndarray, list)):
                    r.append(convert_missing(v))
                elif not isinstance(v, str):
                    r.append(np.asarray([convert_missing(v)] * self.subset_count))
                else:
                    r.append([convert_missing(v)] * self.subset_count)
            else:
                break

        try:
            return np.asarray(r).T
        except Exception:
            return [list(row) for row in zip(*r)]
