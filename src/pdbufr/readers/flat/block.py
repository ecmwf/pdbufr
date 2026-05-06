# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from typing import Any
from typing import Dict
from typing import Iterator
from typing import Mapping
from typing import Set

import eccodes  # type: ignore
import numpy as np

from pdbufr.core.filters import BufrFilter
from pdbufr.core.keys import UncompressedBufrKey1
from pdbufr.core.structure import BufrHeader

SKIP_KEYS = {
    "unexpandedDescriptors",
    "shortDelayedDescriptorReplicationFactor",
    "delayedDescriptorReplicationFactor",
    "extendedDelayedDescriptorReplicationFactor",
    "delayedDescriptorAndDataRepetitionFactor",
    "extendedDelayedDescriptorAndDataRepetitionFactor" "associatedFieldSignificance",
    "dataPresentIndicator",
    "operator",
}

SKIP_HEADER_KEYS = {"unexpandedDescriptors"}


class RefRank:
    def __init__(self, value=-1):
        self.value = value

    def reset(self):
        self.value = -1

    def set(self, value: int):
        if self.value == -1:
            self.value = value


def extract_blocks(
    message: Mapping[str, Any],
    header: BufrHeader,
    add_header: bool,
    add_data: bool,
    data_filters: Dict[str, BufrFilter] = {},
    add_filters: bool = True,
    header_required_columns_keys: Set[str] = set(),
    data_required_columns_keys: Set[str] = set(),
) -> Iterator[Dict[str, Any]]:

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

    if not is_uncompressed and not is_compressed:
        yield from extract_blocks_standard(
            message,
            header,
            add_header,
            add_data,
            data_filters,
            add_filters,
            header_required_columns_keys,
            data_required_columns_keys,
        )
    elif is_compressed:
        yield from extract_blocks_compressed(
            message,
            header,
            subset_count,
            add_header,
            add_data,
            data_filters,
            add_filters,
            header_required_columns_keys,
            data_required_columns_keys,
        )
    else:
        yield from extract_blocks_uncompressed(
            message,
            header,
            subset_count,
            add_header,
            add_data,
            data_filters,
            add_filters,
            header_required_columns_keys,
            data_required_columns_keys,
        )


def extract_blocks_standard(
    message,
    header,
    add_header,
    add_data,
    data_filters,
    add_filters,
    header_required_columns_keys,
    data_required_columns_keys,
):
    result = dict()

    if not header.match_filters():
        return

    if add_header:
        result = header.values()
    elif add_filters:
        result = header.filters_values()

    if add_data or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

        def _get_value(key):
            value = message.get(key)
            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None
            return value

        for f in data_filters.values():
            match, value = f.match_accessor(_get_value)
            if not match:
                return

            if add_filters and not add_data:
                result[f.key] = value

        # extract all the data keys
        if add_data:
            in_data = False
            for key in message:
                if not in_data and key == header.last_key():
                    in_data = True
                    continue

                if in_data:
                    name = key.rpartition("#")[2]
                    if name in SKIP_KEYS or "->" in key:
                        continue

                    value = _get_value(key)
                    result[key] = value

    # yield the result
    if result:
        # print("yielding:", dict(result))
        yield dict(result)


def extract_blocks_compressed(
    message,
    header,
    subset_count,
    add_header,
    add_data,
    data_filters,
    add_filters,
    header_required_columns_keys,
    data_required_columns_keys,
):
    value_cache = {}

    if not header.match_filters():
        return

    result = dict()

    if add_header:
        result = header.values()
    else:
        if add_filters:
            result = header.filters_values()
        if header_required_columns_keys:
            result.update({k: header._get(k) for k in header_required_columns_keys if k in header})

    if add_data or data_filters or data_required_columns_keys:
        # data_required_columns_match_count = 0

        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            # print(" -> missing required columns keys")
            return

        def _get_value(key):
            if key not in value_cache:
                value_cache[key] = message.get(key)
            value = value_cache[key]

            # extract compressed BUFR values. They are either numpy arrays (for numeric types)
            # or lists of strings
            if key != "unexpandedDescriptors" and isinstance(value, (np.ndarray, list)) and len(value) == subset_count:
                value = value[subset]

            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None

            return value

        # columns = list(data_filters.keys()) + list(data_required_columns_keys)

        for subset in range(subset_count):
            current_result = dict(result)

            matched = True
            for f in data_filters.values():
                match, value = f.match_accessor(_get_value)
                # print(f"    match: {match}, value: {value}")
                if not match:
                    matched = False
                    break

                if not add_data and add_filters:
                    current_result[f.key] = value

            if not matched:
                continue

            # # first check the filters and required columns
            # for key in columns:
            #     value = _get_value(key)

            #     if key in data_filters:
            #         if not data_filters[key].match(value):
            #             return

            #     if key in data_required_columns:
            #         data_required_columns_match_count += 1

            #     if not add_data and add_filters:
            #         current_result[key] = value

            # if data_required_columns_match_count != len(data_required_columns):
            #     continue

            # extract all the data keys
            if add_data:
                in_data = False
                for key in message:
                    if not in_data and key == header.last_key():
                        in_data = True
                        continue

                    if in_data:
                        name = key.rpartition("#")[2]
                        if name in SKIP_KEYS or "->" in key:
                            continue

                        value = _get_value(key)
                        current_result[key] = value
            elif data_required_columns_keys:
                for key in data_required_columns_keys:
                    value = _get_value(key)
                    current_result[key] = value

            # print("CURRENT result", current_result)
            # yield the result
            if current_result:
                # print("yielding:", dict(current_observation))
                yield dict(current_result)

    elif result:
        yield dict(result)


def extract_blocks_uncompressed(
    message,
    header,
    subset_count,
    add_header,
    add_data,
    data_filters,
    add_filters,
    header_required_columns_keys,
    data_required_columns_keys,
):
    # For messages with uncompressed subsets consider this:
    # - for each data key we have a single value
    # - there is no way to identify the subset from the key
    # - we cannot directly iterate over a given subset
    # - if we iterate over the keys a new subset is indicated by the
    #   appearance of the "subsetNumber" key, which contains the same array
    #   of values each time (the subset index for all the subsets). This key is
    #   generated by ecCodes and does not contain any ranking so its name is
    #   always "subsetNumber".

    if not header.match_filters():
        return

    result = dict()

    if add_header:
        result = header.values()
    else:
        if add_filters:
            result = header.filters_values()
        if header_required_columns_keys:
            result.update({k: header._get(k) for k in header_required_columns_keys if k in header})

    if result:
        for key in SKIP_HEADER_KEYS:
            result.pop(key, None)

    # print("result", result)
    # print("header.last_key", header.last_key())

    if add_data or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

        # create set of all data keys to extract from a given subset
        # contains re-ranked keys
        ref_rank = {}

        def _get_value(key):
            value = message.get(key)
            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None
            return value

        subset_values = dict()

        allowed_keys = set()
        if not add_data:
            allowed_keys.update(data_filters.keys())
            if data_required_columns_keys:
                allowed_keys.update(data_required_columns_keys)

        def _get_value_subset(key):
            if key.startswith("#"):
                return subset_values.get(key)
            else:
                if key in subset_values:
                    return subset_values[key]
                else:
                    rkey = "#1#" + key
                    if rkey in subset_values:
                        return subset_values[rkey]

            return None

        def _yield_subset():
            current_result = dict(result)

            # apply filters
            matched = True
            matched_keys = {}
            for f in data_filters.values():
                match, value = f.match_accessor(_get_value_subset)
                if not match:
                    matched = False
                    break

                if add_filters:
                    matched_keys[f.key] = value

            if not matched:
                return None

            if not add_data and matched_keys:
                for k in matched_keys:
                    subset_values.pop(k, None)

            if add_data:
                current_result["subsetNumber"] = subset

            current_result.update(subset_values)

            if current_result:
                yield dict(current_result)

        subset = 0
        for key in message:
            if key == "subsetNumber":
                if subset >= 1:
                    yield from _yield_subset()

                subset += 1
                for x in ref_rank.values():
                    x.reset()

            elif subset >= 1:
                b = UncompressedBufrKey1.from_key(key)

                if b.name in SKIP_KEYS:
                    continue

                if allowed_keys and not (key in allowed_keys or b.name in allowed_keys):
                    continue

                if b.name in ref_rank:
                    ref_rank[b.name].set(b.rank)
                else:
                    ref_rank[b.name] = RefRank(b.rank)

                v = _get_value(key)
                reranked_key = b.rerank(ref_rank[b.name].value)
                # print(f" -> processing data key: {reranked_key}")
                subset_values[reranked_key] = v

        # last subset
        if subset_values:
            yield from _yield_subset()

    else:
        if result:
            yield dict(result)
