# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


def subset_info(message):
    is_compressed = False
    is_uncompressed = False
    subset_count = 1
    try:
        is_compressed = bool(message["compressedData"])
    except KeyError:
        is_compressed = False

    if is_compressed:
        is_uncompressed = False
        subset_count = message["numberOfSubsets"]
    else:
        is_uncompressed = int(message["numberOfSubsets"]) > 1
        subset_count = 1

    return subset_count, is_uncompressed, is_compressed


def uncompressed_subset_ranges(filtered_keys, subset_count):
    subset_start = []
    subset_end = []
    for i, bufr_key in enumerate(filtered_keys):
        if bufr_key.name == "subsetNumber":
            subset_start.append(i)
            if len(subset_start) > 1:
                subset_end.append(i)

        if len(subset_start) == subset_count:
            subset_end.append(len(filtered_keys))
            break

    return subset_start, subset_end


class BufrSubset:
    def __init__(self, message, filtered_keys):
        self.message = message
        self.filtered_keys = filtered_keys

    def subsets(self):
        subset_count, is_compressed, is_uncompressed = subset_info(self.message)

        if not is_compressed and not is_uncompressed:
            yield self.filtered_keys, 0

        elif is_compressed:
            for subset in range(subset_count):
                yield self.filtered_keys, subset + 1

        elif is_uncompressed:
            subset_start, subset_end = uncompressed_subset_ranges(self.filtered_keys, subset_count)
            for i in range(subset_count):
                self.filtered_keys[subset_start[i] : subset_end[i]], i + 1
