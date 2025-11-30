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


def extract_blocks(
    message: Mapping[str, Any],
    header: BufrHeader,
    add_header: bool,
    add_data: bool,
    data_filters: Dict[str, BufrFilter] = {},
    add_filters: bool = True,
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
            data_required_columns_keys,
        )
    else:
        # yield from extract_blocks_uncompressed(
        #     message,
        #     subset_count,
        #     filters,
        #     add_filters,
        #     columns,
        #     columns,
        #     required_columns,
        #     prefilter_headers,
        #     header,
        # )
        pass


def extract_blocks_standard(
    message,
    header,
    add_header,
    add_data,
    data_filters,
    add_filters,
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
                if not in_data and key == header.last_key:
                    in_data = True
                    continue

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
    message, header, subset_count, add_header, add_data, data_filters, add_filters, data_required_columns
):
    value_cache = {}

    if not header.match_filters():
        return

    if add_header:
        result = header.values()
    elif add_filters:
        result = header.filters_values()

    if add_data or data_filters or data_required_columns:
        data_required_columns_match_count = 0

        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        def _get_value(key):
            if key not in value_cache:
                value_cache[key] = message.get(key)
            value = value_cache[key]

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

        columns = list(data_filters.keys()) + list(data_required_columns)
        for subset in range(subset_count):
            current_result = dict(result)
            # first check the filters and required columns
            for key in columns:
                value = _get_value(key)

                if key in data_filters:
                    if not data_filters[key].match(value):
                        return

                if key in data_required_columns:
                    data_required_columns_match_count += 1

                if not add_data and add_filters:
                    current_result[key] = value

            if data_required_columns_match_count != len(data_required_columns):
                continue

            # extract all the data keys
            if add_data:
                in_data = False
                for key in message:
                    if not in_data and key == header.last_key:
                        in_data = True
                        continue

                    name = key.rpartition("#")[2]
                    if name in SKIP_KEYS or "->" in key:
                        continue

                    value = _get_value(key)
                    current_result[key] = value

            # yield the result
            if current_result:
                # print("yielding:", dict(current_observation))
                yield dict(current_result)

    elif result:
        yield dict(result)
