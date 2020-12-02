#
# Copyright 2019 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors:
#   Alessandro Amici - B-Open - https://bopen.eu
#

import logging
import math
import os
import typing as T

import eccodes  # type: ignore
import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from . import bufr_filters

LOG = logging.getLogger(__name__)


def datetime_from_bufr(observation, prefix, datetime_keys):
    # type: (T.Dict[str, T.Any], str, T.List[str]) -> pd.Timestamp
    hours = observation.get(prefix + datetime_keys[3], 0)
    minutes = observation.get(prefix + datetime_keys[4], 0)
    seconds = observation.get(prefix + datetime_keys[5], 0.0)
    nanosecond = int(seconds * 1000000000) % 1000000000
    datetime_list = [observation[prefix + k] for k in datetime_keys[:3]]
    datetime_list += [hours, minutes, int(seconds)]
    return pd.Timestamp(*datetime_list, nanosecond=nanosecond)


def wmo_station_id_from_bufr(observation, prefix, keys):
    # type: (T.Dict[str, T.Any], str, T.List[str]) -> int
    block_number = int(observation[prefix + keys[0]])
    station_number = int(observation[prefix + keys[1]])
    return block_number * 1000 + station_number


COMPUTED_KEYS = [
    (
        ["year", "month", "day", "hour", "minute", "second"],
        "data_datetime",
        datetime_from_bufr,
    ),
    (
        [
            "typicalYear",
            "typicalMonth",
            "typicalDay",
            "typicalHour",
            "typicalMinute",
            "typicalSecond",
        ],
        "typical_datetime",
        datetime_from_bufr,
    ),
    (["blockNumber", "stationNumber"], "WMO_station_id", wmo_station_id_from_bufr),
]


def cached_message_keys(
    message: T.Mapping[str, T.Any],
    keys_cache: T.Dict[T.Tuple[T.Hashable, ...], T.List[str]],
    subset_count: T.Optional[int] = None,
) -> T.List[str]:
    cache_key: T.Tuple[T.Hashable, ...] = (
        message["edition"],
        message["masterTableNumber"],
    )
    if subset_count is not None:
        descriptors = message["unexpandedDescriptors"]
        if isinstance(descriptors, int):
            descriptors = (descriptors, None)
        else:
            descriptors = tuple(descriptors) + (None,)

        try:
            delayed_descriptors = message["delayedDescriptorReplicationFactor"]
        except (KeyError, eccodes.KeyValueNotFoundError):
            delayed_descriptors = []

        if isinstance(delayed_descriptors, int):
            delayed_descriptors = (delayed_descriptors,)
        else:
            delayed_descriptors = tuple(delayed_descriptors)

        cache_key += (subset_count,) + descriptors + delayed_descriptors

    if cache_key not in keys_cache:
        keys_cache[cache_key] = list(message)

    return keys_cache[cache_key]


def filter_message_items(
    message: T.Mapping[str, T.Any],
    include: T.Optional[T.Container[str]],
    message_keys: T.List[str],
) -> T.Iterator[T.Tuple[str, str, T.Any]]:
    for key in message_keys:
        short_key = key.rpartition("#")[2]
        if include is None or short_key in include or short_key == "subsetNumber":
            value = message[key]
            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = math.nan
            yield (key, short_key, value)


def extract_subsets(
    message_items: T.List[T.Tuple[str, str, T.Any]],
    subset_count: int,
    is_compressed: bool,
) -> T.Iterator[T.List[T.Tuple[str, str, T.Any]]]:
    LOG.debug(
        "extracting subsets count %d and is_compressed %d items %d",
        subset_count,
        is_compressed,
        len(message_items),
    )
    if subset_count == 1:
        yield message_items
    elif is_compressed is True:
        for i in range(subset_count):
            subset: T.List[T.Tuple[str, str, T.Any]] = []
            for k, s, v in message_items:
                if isinstance(v, (list, np.ndarray)):
                    v = v[i]
                if v == eccodes.CODES_MISSING_DOUBLE:
                    v = math.nan
                subset.append((k, s, v))
            yield subset
    else:
        header_keys = set()
        for key, short_key, _ in message_items:
            if (key[0] != "#" or key[:3] == "#1#") and key != "subsetNumber":
                header_keys.add(key)
            else:
                header_keys.discard("#1#" + short_key)
        header = [(k, s, v) for k, s, v in message_items if k in header_keys]
        first_subset = True
        subset = []
        for key, short_key, value in message_items:
            if key in header_keys:
                continue
            if key == "subsetNumber":
                if first_subset:
                    first_subset = False
                else:
                    yield header + subset
                    subset = []
            if key != "subsetNumber":
                subset.append((key, short_key, value))
        yield header + subset


def add_computed(
    data_items: T.List[T.Tuple[str, str, T.Any]],
    include_computed: T.Container[str] = frozenset(),
) -> T.List[T.Tuple[str, str, T.Any]]:
    computed_items = []
    for keys, computed_key, getter in COMPUTED_KEYS:
        if computed_key in include_computed:
            observation = {short_key: value for _, short_key, value in data_items}
            prefix = "#1#"
            try:
                computed_value = getter(observation, "", keys)
            except Exception:
                LOG.debug("can't compute key %r", computed_key)
                computed_value = None
            computed_items.append((prefix + computed_key, computed_key, computed_value))
    return data_items + computed_items


def merge_data_items(old_data_items, data_items):
    # type: (T.Dict[str, T.Any], T.List[T.Tuple[str, str, T.Any]]) -> T.List[T.Tuple[str, str, T.Any]]
    for _, short_name, _ in data_items:
        old_data_items.pop(short_name, None)
    return data_items + list(old_data_items.values())


def extract_observations(subset_items, include_computed=frozenset()):
    # type: (T.List[T.Tuple[str, str, T.Any]], T.Container[str]) -> T.Iterator[T.List[T.Tuple[str, str, T.Any]]]
    short_key_order: T.List[str] = []
    old_data_items: T.Dict[str, T.Tuple[str, str, T.Any]] = {}
    data_items: T.List[T.Tuple[str, str, T.Any]] = []
    short_key_index_seen = -1
    for key, short_key, value in subset_items:
        try:
            short_key_index = short_key_order.index(short_key)
        except ValueError:
            short_key_order.append(short_key)
            short_key_index = len(short_key_order) - 1
        if short_key_index <= short_key_index_seen:
            all_data_items = merge_data_items(old_data_items, data_items)
            yield add_computed(all_data_items, include_computed)
            old_data_items = {item[1]: item for item in all_data_items}
            data_items = []
        data_items.append((key, short_key, value))
        short_key_index_seen = short_key_index
    if data_items:
        all_data_items = merge_data_items(old_data_items, data_items)
        yield add_computed(all_data_items, include_computed)


def filter_stream(
    bufr_file: T.Iterable[T.MutableMapping[str, T.Any]],
    columns: T.Iterable[str],
    filters: T.Mapping[str, T.Any] = {},
    required_columns: T.Union[bool, T.Iterable[str]] = True,
) -> T.Iterator[T.Dict[str, T.Any]]:
    """
    Iterate over selected observations from a eccodes.BurfFile.

    :param bufr_file: the eccodes.BurfFile object
    :param columns: A list of BUFR keys to return in the DataFrame for every observation
    :param filters: A dictionary of BUFR key / filter definition to filter the observations to return
    :param required_columns: The list BUFR keys that are required for all observations.
        ``True`` means all ``columns`` are required
    """
    if required_columns is True:
        required_columns = set(columns)
    elif required_columns is False:
        required_columns = set()
    elif isinstance(required_columns, T.Iterable):
        required_columns = set(required_columns)
    else:
        raise ValueError("required_columns must be a bool or an iterable")
    columns = list(columns)
    filters = dict(filters)

    max_count = filters.pop("count", float("inf"))

    compiled_filters = bufr_filters.compile_filters(filters)
    included_keys = set(compiled_filters)
    included_keys |= set(columns)
    for keys, computed_key, _ in COMPUTED_KEYS:
        if computed_key in included_keys:
            included_keys |= set(keys)

    keys_cache: T.Dict[T.Tuple[T.Hashable, ...], T.List[str]] = {}
    for count, message in enumerate(bufr_file, 1):
        if count > max_count:
            LOG.debug("stopping processing after max_count: %d", max_count)
            break
        LOG.debug("starting reading message: %d", count)
        header_keys = cached_message_keys(message, keys_cache)
        header_items = list(
            filter_message_items(message, set(compiled_filters), header_keys)
        )
        if "count" in compiled_filters:
            header_items += [("count", "count", count)]
        if not bufr_filters.match_compiled_filters(
            header_items, compiled_filters, required=False
        ):
            continue

        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        subset_count = message["numberOfSubsets"]
        is_compressed = bool(message["compressedData"])
        message_keys = cached_message_keys(message, keys_cache, subset_count)
        message_items = list(filter_message_items(message, included_keys, message_keys))
        if "count" in included_keys:
            message_items += [("count", "count", count)]
        for subset_items in extract_subsets(message_items, subset_count, is_compressed):
            for data_items in extract_observations(subset_items, included_keys):
                if bufr_filters.match_compiled_filters(data_items, compiled_filters):
                    data = {s: v for k, s, v in data_items if s in columns}
                    if required_columns.issubset(data):
                        yield data


def read_bufr(
    path: T.Union[str, bytes, "os.PathLike[T.Any]"],
    columns: T.Iterable[str],
    filters: T.Mapping[str, T.Any] = {},
    required_columns: T.Union[bool, T.Iterable[str]] = True,
) -> pd.DataFrame:
    """
    Read selected observations from a BUFR file into DataFrame.

    :param path: The path to the BUFR file
    :param columns: A list of BUFR keys to return in the DataFrame for every observation
    :param filters: A dictionary of BUFR key / filter definition to filter the observations to return
    :param required_columns: The list BUFR keys that are required for all observations.
        ``True`` means all ``columns`` are required
    """
    with eccodes.BufrFile(path) as bufr_file:
        filtered_iterator = filter_stream(bufr_file, columns, filters, required_columns)
        return pd.DataFrame.from_records(filtered_iterator)
