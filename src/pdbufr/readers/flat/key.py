# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from itertools import chain
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


class RefRank:
    def __init__(self):
        self.value = -1

    def reset(self):
        self.value = -1

    def set(self, value: int):
        if self.value == -1:
            self.value = value


def extract_keys(
    message: Mapping[str, Any],
    header: BufrHeader,
    data_filters: Dict[str, BufrFilter] = {},
    add_filters: bool = True,
    data_columns: Set[str] = set(),
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
        yield from extract_keys_standard(
            message, header, data_filters, add_filters, data_columns, data_required_columns_keys
        )
    elif is_compressed:
        yield from extract_keys_compressed(
            message,
            header,
            subset_count,
            data_filters,
            add_filters,
            data_columns,
            data_required_columns_keys,
        )
    else:
        yield from extract_keys_uncompressed(
            message,
            header,
            subset_count,
            data_filters,
            add_filters,
            data_columns,
            data_required_columns_keys,
        )


def extract_keys_standard(
    message, header, data_filters, add_filters, data_columns, data_required_columns_keys
):
    result = dict()

    if not header.match_filters():
        # LOG.debug("header filters do not match")
        return

    if add_filters:
        result = header.filters_values()

    if header.columns:
        result.update(header.columns_values())

    print("result before data keys:", result)

    # LOG.debug(f"result before data keys: {result}")

    if data_columns or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1
        # LOG.debug("message unpacked")

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

        print("message has all required columns keys")

        # LOG.debug("has all required columns keys")

        def _get_value(key):
            value = message.get(key)
            print(f" -> get_value key: {key}, value: {value}")
            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None
            return value

        for f in data_filters.values():
            match, value = f.match_accessor(_get_value)
            if not match:
                return

            if add_filters:
                result[f.key] = value

        # LOG.debug(f"result after filters: {result}")

        for key, c in data_columns.items():
            # LOG.debug(f"getting data column key: {key}")
            print(f" -> getting data column key: {key}")
            if key not in result:
                v = c.get_value(_get_value)
                result[key] = v

        # LOG.debug(f"result after data columns: {result}")

    if result:
        yield dict(result)


def extract_keys_compressed(
    message,
    header,
    subset_count,
    data_filters,
    add_filters,
    data_columns,
    data_required_columns_keys,
):
    value_cache = {}

    result = dict()

    if not header.match_filters():
        return

    if add_filters:
        result = header.filters_values()

    if header.columns:
        result.update(header.columns_values())

    # print(f"result before data keys: {result}")

    print("data_columns:", data_columns)
    print("data_required_columns_keys:", data_required_columns_keys)
    print("data_filters:", data_filters)

    if data_columns or data_filters or data_required_columns_keys:
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

            # print(f" -> get_value key: {key}, value: {value}")

            # extract compressed BUFR values. They are either numpy arrays (for numeric types)
            # or lists of strings
            if (
                key != "unexpandedDescriptors"
                and isinstance(value, (np.ndarray, list))
                and len(value) == subset_count
            ):
                value = value[subset]

            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None

            return value

        for subset in range(subset_count):
            current_result = dict(result)

            matched = True
            for f in data_filters.values():
                print(f" -> matching filter for key: {f.key}")
                match, value = f.match_accessor(_get_value)
                print(f"    match: {match}, value: {value}")
                if not match:
                    matched = False
                    break

                if add_filters:
                    current_result[f.key] = value

            if not matched:
                continue

            for key, c in data_columns.items():
                # LOG.debug(f"getting data column key: {key}")
                if key not in current_result:
                    v = c.get_value(_get_value)
                    current_result[key] = v

            if current_result:
                # print("yielding:", current_result)
                yield dict(current_result)

    elif result:
        yield dict(result)


def extract_keys_uncompressed(
    message,
    header,
    subset_count,
    data_filters,
    add_filters,
    data_columns,
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

    # value_cache = {}

    result = dict()

    if not header.match_filters():
        return

    if add_filters:
        result = header.filters_values()

    if header.columns:
        result.update(header.columns_values())

    print("result before data keys:", result)

    if data_columns or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            # print(" -> missing required columns keys")
            return

        # create set of all data keys to extract from a given subset
        # contains re-ranked keys
        subset_keys = set()
        ref_rank = {}
        for col in chain(data_filters.values(), data_columns.values()):
            for key in col.keys:
                if key not in subset_keys:
                    b = UncompressedBufrKey1.from_key(key)
                    subset_keys.add(b.ranked_name)
                    if b.name not in ref_rank:
                        ref_rank[b.name] = RefRank()

        print("subset_keys:", subset_keys)
        print("ref_rank:", ref_rank)

        def _get_value(key):
            value = message.get(key)
            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None
            return value

        subset_values = dict()
        current_result = dict()

        def _get_value_subset(key):
            return subset_values.get(key)

        subset_keys_count = 0
        subset_keys_num = len(subset_keys)
        subset = 0
        for key in message:
            # start new subset
            if key == "subsetNumber":
                print(" -> starting new subset")
                subset_keys_count = 0
                if subset >= 1:
                    print("    subset_values:", subset_values)

                    current_result = dict(result)

                    # generate result for previous subset
                    matched = True
                    for f in data_filters.values():
                        match, value = f.match(_get_value_subset)
                        if not match:
                            matched = False
                            break

                        if add_filters:
                            current_result[f.key] = value

                    if matched:
                        for key, c in data_columns.items():
                            # LOG.debug(f"getting data column key: {key}")
                            if key not in current_result:
                                v = c.get_value(_get_value_subset)
                                current_result[key] = v

                        if current_result:
                            # print("yielding:", current_result)
                            yield dict(current_result)

                    print(".    yielded current_result:", current_result)

                subset += 1
                subset_values.clear()
                current_result.clear()
                for x in ref_rank.values():
                    x.reset()

            elif subset >= 1 and subset_keys_count < subset_keys_num:
                b = UncompressedBufrKey1.from_key(key)
                if b.name in ref_rank:
                    ref_rank[b.name].set(b.rank)
                    # if not ref_rank[b.name].is_set():
                    #     ref_rank[b.name].set(b.rank)

                    # print(f" -> key: {key}, name: {b.name}, rank: {b.rank}, ref_rank: {ref_rank[b.name]}")
                    reranked_key = b.rerank(ref_rank[b.name].value)
                    # print(f"    reranked_key: {reranked_key}")
                    if reranked_key in subset_keys:
                        subset_values[reranked_key] = message.get(key)
                        subset_keys_count += 1

        # last subset
        if subset_values:
            current_result = dict(result)

        for f in data_filters.values():
            match, value = f.match(_get_value_subset)
            if not match:
                return

            if add_filters:
                current_result[f.key] = value

        for key, c in data_columns.items():
            # LOG.debug(f"getting data column key: {key}")
            if key not in current_result:
                v = c.get_value(_get_value_subset)
                current_result[key] = v

        if current_result:
            # print("yielding:", current_result)
            yield dict(current_result)
    else:
        if result:
            yield dict(result)
