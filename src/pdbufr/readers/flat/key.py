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

from pdbufr.core.filters import BufrFilter
from pdbufr.core.structure import BufrHeader

from .compressed import CompressedValueCache
from .uncompressed import UncompressedExtractor


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


def extract_keys_standard(message, header, data_filters, add_filters, data_columns, data_required_columns_keys):
    result = dict()

    if not header.match_filters():
        # LOG.debug("header filters do not match")
        return

    if add_filters:
        result = header.filters_values()

    if header.columns:
        result.update(header.columns_values())

    # LOG.debug(f"result before data keys: {result}")

    if data_columns or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1
        # LOG.debug("message unpacked")

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

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

            # multi-rank filter columns are not added to the result
            # since they are not associated with a single value (rank)
            if add_filters and not f.column.multi:
                result[f.key] = value

        # LOG.debug(f"result after filters: {result}")

        for key, c in data_columns.items():
            # LOG.debug(f"getting data column key: {key}")
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
    value_cache = CompressedValueCache(message, subset_count)

    result = dict()

    if not header.match_filters():
        return

    if add_filters:
        result = header.filters_values()

    if header.columns:
        result.update(header.columns_values())

    if data_columns or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

        def _get_value(key):
            return value_cache.get(key, subset)

        for subset in range(subset_count):
            current_result = dict(result)

            matched = True
            for f in data_filters.values():
                match, value = f.match_accessor(_get_value)
                if not match:
                    matched = False
                    break

                if add_filters and not f.column.multi:
                    current_result[f.key] = value

            if not matched:
                continue

            for key, c in data_columns.items():
                # LOG.debug(f"getting data column key: {key}")
                if key not in current_result:
                    v = c.get_value(_get_value)
                    current_result[key] = v

            if current_result:
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

    result = dict()

    if not header.match_filters():
        return

    if add_filters:
        result = header.filters_values()

    if header.columns:
        result.update(header.columns_values())

    if data_columns or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

        data = UncompressedExtractor(result, message, subset_count, data_columns, data_filters, add_filters)
        yield from data.extract()

    else:
        if result:
            yield dict(result)
