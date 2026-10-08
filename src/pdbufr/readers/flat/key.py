# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from typing import Any, Dict, Iterator, Mapping, Set

import numpy as np  # type: ignore

from pdbufr.core.filters import BufrFilter

from .column import MultiRankColumn, SimpleColumn
from .compressed import CompressedValueCache
from .header import BufrHeader
from .missing import convert_missing
from .uncompressed import UncompressedExtractor

"""
Methods to extract named keys from a message/subset.
"""

# how a column/filter is evaluated for a subset of a compressed message
_SIMPLE = 0  # a single value per subset, already resolved for all the subsets
_MULTI = 1  # the values of all the ranks per subset, already resolved
_GENERIC = 2  # has to be evaluated subset by subset via the value accessor
_VECTOR = 3  # a filter already matched against the values of all the subsets at once
_COMPUTED = 4  # a computed filter already matched, its value still has to be computed


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

    # all the header values are collected by now. The header must not be used from
    # here on because the message is unpacked below and the header can only be
    # queried while the message is still packed. Setting it to None makes any
    # accidental use fail straight away.
    header = None
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
            value = convert_missing(value)
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
            if not c.multi:
                if key not in result:
                    v = c.get_value(_get_value)
                    result[key] = v
            else:
                for k, v in c.get_ranked_items(_get_value):
                    result[k] = v

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

    # all the header values are collected by now. The header must not be used from
    # here on because the message is unpacked below and the header can only be
    # queried while the message is still packed. Setting it to None makes any
    # accidental use fail straight away.
    header = None

    if data_columns or data_filters or data_required_columns_keys:
        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        if any(key not in message for key in data_required_columns_keys):
            # LOG.debug("missing required columns keys")
            return

        def _get_value(key):
            return value_cache.get(key, subset)

        # a computed column/filter reads several keys for each subset. Resolving those
        # keys for all the subsets in one go turns each of these accesses into a plain
        # list lookup.
        resolved = {}

        def _resolve(keys):
            for key in keys:
                if key not in resolved:
                    resolved[key] = value_cache.get_all_subsets(key)

        def _get_raw_value_resolved(key):
            r = resolved.get(key)
            if r is None:
                return None
            values, per_subset = r
            return np.asarray(values) if per_subset else values

        def _get_value_resolved(key):
            r = resolved.get(key)
            if r is None:
                return value_cache.get(key, subset)
            values, per_subset = r
            return values[subset] if per_subset else values

        # the filters are evaluated first for all the subsets. This way the columns
        # only have to be read from the message when at least one subset matches.
        # A filter on a simple column is resolved for all the subsets in one go, the
        # remaining ones have to be evaluated subset by subset.
        matched_subsets = None
        matched_filter_keys = []
        if data_filters:
            # a filter on a simple column can often be matched against the values of
            # all the subsets at once (_VECTOR), which is much cheaper than matching
            # them one by one
            mask = None
            filter_plan = []
            multi_filters = []
            for f in data_filters.values():
                add_value = add_filters and not f.column.multi
                if add_value:
                    matched_filter_keys.append(f.key)

                if type(f.column) is MultiRankColumn:
                    # resolving a multi-rank filter means reading all the ranks from
                    # the message, so it is left to the second pass below
                    multi_filters.append((len(filter_plan), f))
                    filter_plan.append([_GENERIC, f, None, False])
                    continue

                if type(f.column) is not SimpleColumn:
                    _resolve(getattr(f.column, "ranked_keys", ()))

                    # a computed filter can sometimes be evaluated for all the subsets
                    # at once as well
                    f_mask = None
                    values = None
                    if hasattr(f.column, "get_value_array"):
                        computed = f.column.get_value_array(_get_raw_value_resolved)
                        if computed is not None:
                            computed = np.asarray(computed)
                            if computed.ndim == 0:
                                # the same value in all the subsets
                                computed = np.broadcast_to(computed, (subset_count,))
                            if computed.shape == (subset_count,):
                                f_mask = f.filter.match_array(computed)

                    if f_mask is None:
                        filter_plan.append([_GENERIC, f, None, False])
                    else:
                        mask = f_mask if mask is None else mask & f_mask
                        # the value added to the result is still computed one by one so
                        # that it is exactly the same as without this shortcut
                        filter_plan.append([_COMPUTED, f, None, False])
                    continue

                raw, per_subset = value_cache.get_all_subsets_raw(f.column.ranked_key)
                f_mask = None
                if per_subset and isinstance(raw, np.ndarray) and raw.dtype.kind in "biufc":
                    f_mask = f.filter.match_array(raw)

                # the values are only needed when they have to be added to the result
                values = value_cache.get_all_subsets(f.column.ranked_key)[0] if add_value else None
                filter_plan.append([_VECTOR if f_mask is not None else _SIMPLE, f, values, per_subset])
                if f_mask is not None:
                    mask = f_mask if mask is None else mask & f_mask

            # a multi-rank filter tests all the ranks of a subset, which is even more
            # expensive to do one by one. It is only resolved when the other filters
            # left at least one candidate subset.
            for index, f in multi_filters:
                if mask is not None and not mask.any():
                    return

                raw, per_subset = value_cache.get_all_subsets_multi_raw(f.column.raw_key)
                if per_subset and isinstance(raw, np.ndarray) and raw.ndim == 2 and raw.dtype.kind in "biufc":
                    f_mask = f.filter.match_array_multi(raw)
                    mask = f_mask if mask is None else mask & f_mask
                    filter_plan[index][0] = _VECTOR

            candidate_subsets = np.nonzero(mask)[0] if mask is not None else range(subset_count)

            matched_subsets = []
            for subset in candidate_subsets:
                matched = True
                matched_values = []
                for kind, f, values, per_subset in filter_plan:
                    if kind == _VECTOR:
                        # already matched, only the value is still needed
                        if values is not None:
                            matched_values.append(values[subset] if per_subset else values)
                        continue

                    if kind == _COMPUTED:
                        # already matched, the value is computed the ordinary way
                        if add_filters and not f.column.multi:
                            matched_values.append(f.column.get_value(_get_value_resolved))
                        continue

                    if kind == _SIMPLE:
                        value = values[subset] if per_subset else values
                        match = f.match(value)
                    else:
                        match, value = f.match_accessor(_get_value_resolved)

                    if not match:
                        matched = False
                        break

                    if add_filters and not f.column.multi:
                        matched_values.append(value)

                if matched:
                    matched_subsets.append((subset, matched_values))

            if not matched_subsets:
                return

        # resolve the columns for all the subsets in one go. Only the computed columns
        # (_GENERIC) have to be evaluated subset by subset.
        column_plan = []
        all_simple = True
        for key, c in data_columns.items():
            if type(c) is SimpleColumn:
                values, per_subset = value_cache.get_all_subsets(c.ranked_key)
                column_plan.append((_SIMPLE, key, values, per_subset, None))
            elif type(c) is MultiRankColumn:
                values, per_subset = value_cache.get_all_subsets_multi(c.raw_key)
                column_plan.append((_MULTI, key, values, per_subset, c))
                all_simple = False
            else:
                _resolve(getattr(c, "ranked_keys", ()))
                column_plan.append((_GENERIC, key, None, False, c))
                all_simple = False

        # fast path: when all the columns are simple and no filtering is needed on the
        # data section the whole set of values is already available, so the results can
        # be built by simply iterating over them
        if column_plan and all_simple and not data_filters and not any(key in result for _, key, *_ in column_plan):
            names = [key for _, key, *_ in column_plan]
            columns_values = [v if per_subset else [v] * subset_count for _, _, v, per_subset, _ in column_plan]

            for values in zip(*columns_values):
                current_result = dict(result)
                current_result.update(zip(names, values))
                if current_result:
                    yield current_result
            return

        if matched_subsets is None:
            matched_subsets = [(subset, ()) for subset in range(subset_count)]

        for subset, matched_values in matched_subsets:
            current_result = dict(result)
            if matched_values:
                current_result.update(zip(matched_filter_keys, matched_values))

            for kind, key, values, per_subset, c in column_plan:
                # LOG.debug(f"getting data column key: {key}")
                if kind == _SIMPLE:
                    if key not in current_result:
                        current_result[key] = values[subset] if per_subset else values
                elif kind == _MULTI:
                    ranks = values[subset] if per_subset else values
                    current_result.update(zip(c.ranked_names(len(ranks)), ranks))
                elif not c.multi:
                    if key not in current_result:
                        v = c.get_value(_get_value_resolved)
                        current_result[key] = v
                else:
                    for k, v in c.get_ranked_items(_get_value):
                        current_result[k] = v

            if current_result:
                yield current_result

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
    result = dict()

    if not header.match_filters():
        return

    if add_filters:
        result = header.filters_values()

    if header.columns:
        result.update(header.columns_values())

    # all the header values are collected by now. The header must not be used from
    # here on because the message is unpacked below and the header can only be
    # queried while the message is still packed. Setting it to None makes any
    # accidental use fail straight away.
    header = None

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
