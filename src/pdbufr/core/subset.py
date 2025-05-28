# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import collections
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple

import eccodes  # type: ignore
import numpy as np


def subset_info(message: Mapping[str, Any]) -> Tuple[int, bool, bool]:
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
        n = int(message["numberOfSubsets"])
        is_uncompressed = n > 1
        if is_uncompressed:
            subset_count = n

    return subset_count, is_uncompressed, is_compressed


def uncompressed_subset_ranges(filtered_keys: List[Any], subset_count: int) -> Tuple[List[int], List[int]]:
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


class BufrSubsetCollector:
    def __init__(
        self,
        owner: "BufrSubsetReader",
        filtered_keys: List[Any],
        subset_number: int,
    ):
        self.owner = owner
        self.filtered_keys = filtered_keys
        self.subset_number = subset_number

    def collect(
        self,
        keys: List[str],
        filters: Dict[str, Any],
        mandatory_keys: Optional[List[str]] = None,
        units_keys: Optional[List[str]] = None,
        value_and_units: bool = True,
    ) -> Generator[Dict[str, Any], None, None]:
        value_cache = {}
        current_observation = collections.OrderedDict({})
        current_levels = [0]
        failed_match_level = None

        for bufr_key in self.filtered_keys:
            name = bufr_key.name

            # stop processing if we reach the firstOrderStatistics key
            if name.startswith("firstOrderStatistics"):
                break

            if name not in keys:
                continue

            level = bufr_key.level

            if failed_match_level is not None and level > failed_match_level:
                continue

            # TODO: make into a function
            if current_observation and (
                # if all(name in current_observation for name in keys) and (
                level < current_levels[-1]
                or (level == current_levels[-1] and name in current_observation)
            ):
                if not mandatory_keys or all(name in current_observation for name in mandatory_keys):

                    # copy the content of current_items
                    yield dict(current_observation)

            while len(current_observation) and (
                level < current_levels[-1] or (level == current_levels[-1] and name in current_observation)
            ):
                current_observation.popitem()  # OrderedDict.popitem uses LIFO order
                current_levels.pop()

            if bufr_key.key not in value_cache:
                try:
                    value_cache[bufr_key.key] = self.owner.message[bufr_key.key]
                except KeyError:
                    value_cache[bufr_key.key] = None
            value = value_cache[bufr_key.key]

            # extract compressed BUFR values. They are either numpy arrays (for numeric types)
            # or lists of strings
            if (
                self.owner.is_compressed
                and name != "unexpandedDescriptors"
                and isinstance(value, (np.ndarray, list))
                and len(value) == self.owner.subset_count
            ):
                value = value[self.subset_number]

            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None

            if name in filters:
                if filters[name].match(value):
                    failed_match_level = None
                else:
                    failed_match_level = level
                    continue

            if name in keys:
                units = None
                if units_keys and name in units_keys:
                    try:
                        units = self.owner.message[bufr_key.key + "->units"]
                    except KeyError:
                        units = None

                if value_and_units:
                    current_observation[name] = (value, units)
                else:
                    current_observation[name] = value
            current_levels.append(level)

        # yield the last observation
        # if all(name in current_observation for name in filters):
        if current_observation and all(name in current_observation for name in filters):
            if not mandatory_keys or all(name in current_observation for name in mandatory_keys):
                yield dict(current_observation)


class BufrSubsetReader:
    def __init__(self, message: Mapping[str, Any], filtered_keys: List[Any]):
        self.message = message
        self.filtered_keys = filtered_keys
        self.subset_count, self.is_uncompressed, self.is_compressed = subset_info(self.message)
        self.cache = {}

    def subsets(self) -> Generator[BufrSubsetCollector, None, None]:
        if not self.is_compressed and not self.is_uncompressed:
            yield BufrSubsetCollector(self, self.filtered_keys, 0)

        elif self.is_compressed:
            for subset in range(self.subset_count):
                yield BufrSubsetCollector(self, self.filtered_keys, subset)

        elif self.is_uncompressed:
            subset_start, subset_end = uncompressed_subset_ranges(self.filtered_keys, self.subset_count)
            for i in range(self.subset_count):
                yield BufrSubsetCollector(self, self.filtered_keys[subset_start[i] : subset_end[i]], i)
