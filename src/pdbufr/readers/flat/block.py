# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from typing import Any, Dict, Iterator, Mapping, Set

import eccodes  # type: ignore

from pdbufr.core.filters import BufrFilter

from .compressed import CompressedValueCache
from .header import BufrHeader

SKIP_KEYS = {
    "unexpandedDescriptors",
    "shortDelayedDescriptorReplicationFactor",
    "delayedDescriptorReplicationFactor",
    "extendedDelayedDescriptorReplicationFactor",
    "delayedDescriptorAndDataRepetitionFactor",
    "extendedDelayedDescriptorAndDataRepetitionFactorassociatedFieldSignificance",
    "dataPresentIndicator",
    "operator",
}

SKIP_HEADER_KEYS = {"unexpandedDescriptors"}


def _data_keys_start(header, keys):
    """Return the index of the first data key in the keys of an unpacked message.

    When the header keys are not enumerated yet they are determined here from
    ``keys``, which saves a full key enumeration per message.
    """
    if not header.keys_built:
        data_start = header.build_keys_from_message_keys(keys)
        if data_start is None:
            raise ValueError("could not locate the end of the header in the message keys")
        return data_start

    # the data keys are the ones following the last header key
    last_header_key = header.last_key()
    for i, key in enumerate(keys):
        if key == last_header_key:
            return i + 1
    return len(keys)


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

    # when the header keys are not enumerated yet they are determined from the keys of
    # the unpacked message, so the header values can only be collected after that
    header_values_pending = add_header and not header.keys_built

    if add_header:
        if not header_values_pending:
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

        keys = None
        data_start = 0
        if add_data:
            keys = list(iter(message))
            data_start = _data_keys_start(header, keys)
            if header_values_pending:
                result = header.values()

        for f in data_filters.values():
            match, value = f.match_accessor(_get_value)
            if not match:
                return

            if add_filters and not add_data and not f.column.multi:
                result[f.key] = value

        # extract all the data keys
        if add_data:
            for key in keys[data_start:]:
                name = key.rpartition("#")[2]
                if name in SKIP_KEYS or "->" in key:
                    continue

                result[key] = _get_value(key)

    # yield the result
    if result:
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
    value_cache = CompressedValueCache(message, subset_count)

    if not header.match_filters():
        return

    result = dict()

    # when the header keys are not enumerated yet they are determined from the keys of
    # the unpacked message, so the header values can only be collected after that
    header_values_pending = add_header and not header.keys_built

    if add_header:
        if not header_values_pending:
            result = header.values()
    else:
        if add_filters:
            result = header.filters_values()
        if header_required_columns_keys:
            result.update({k: header._get(k) for k in header_required_columns_keys if k in header})

    if add_data or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

        def _get_value(key):
            return value_cache.get(key, subset)

        # the keys are the same for each subset, so they are only collected once
        data_keys = None
        if add_data:
            keys = list(iter(message))
            data_start = _data_keys_start(header, keys)
            if header_values_pending:
                result = header.values()
            data_keys = [
                key for key in keys[data_start:] if key.rpartition("#")[2] not in SKIP_KEYS and "->" not in key
            ]

        for subset in range(subset_count):
            current_result = dict(result)

            matched = True
            for f in data_filters.values():
                match, value = f.match_accessor(_get_value)
                # print(f"    match: {match}, value: {value}")
                if not match:
                    matched = False
                    break

                if not add_data and add_filters and not f.column.multi:
                    current_result[f.key] = value

            if not matched:
                continue

            # extract all the data keys
            if add_data:
                for key in data_keys:
                    current_result[key] = _get_value(key)
            elif data_required_columns_keys:
                for key in data_required_columns_keys:
                    value = _get_value(key)
                    current_result[key] = value

            # yield the result
            if current_result:
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
    if not header.match_filters():
        return

    result = dict()

    # this extractor does not use the header keys to locate the data section, so they
    # have to be enumerated here, while the message is still packed
    if not header.keys_built:
        header.build_keys()

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

    if add_data or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

        from .uncompressed import UncompressedExtractorAll

        data = UncompressedExtractorAll(
            result, message, subset_count, add_data, data_filters, add_filters, data_required_columns_keys
        )
        yield from data.extract()

    else:
        if result:
            yield dict(result)
