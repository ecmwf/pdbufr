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

__version__ = '0.8.0'

import collections.abc
import itertools
import logging
import typing as T

import eccodes
import numpy as np
import pandas as pd


LOG = logging.getLogger(__name__)


class BufrMessage(collections.abc.MutableMapping):
    def __init__(self, file):
        self.codes_id = eccodes.codes_bufr_new_from_file(file)

    def __del__(self):
        if self.codes_id:
            eccodes.codes_release(self.codes_id)

    def __iter__(self):
        iterator = eccodes.codes_bufr_keys_iterator_new(self.codes_id)
        while eccodes.codes_bufr_keys_iterator_next(iterator):
            yield eccodes.codes_bufr_keys_iterator_get_name(iterator)
        eccodes.codes_bufr_keys_iterator_delete(iterator)

    def __getitem__(self, item):
        # type: (str) -> T.Any
        """Get value of a given key as its native or specified type."""
        try:
            values = eccodes.codes_get_array(self.codes_id, item)
            if values is None:
                values = ['unsupported_key_type']
        except eccodes.KeyValueNotFoundError:
            raise KeyError(item)
        if len(values) == 1:
            if isinstance(values, np.ndarray):
                values = values.tolist()
            return values[0]
        return values

    def __setitem__(self, item, value):
        # type: (str, T.Any) -> None
        set_array = isinstance(value, T.Sequence) and not isinstance(value, str)
        if set_array:
            eccodes.codes_set_array(self.codes_id, item, value)
        else:
            eccodes.codes_set(self.codes_id, item, value)

    def __len__(self):
        return sum(1 for _ in self)

    def __delitem__(self, key):
        raise NotImplementedError()


def compile_filters(filters):
    # type: (T.Mapping[str, T.Any]) -> T.Dict[str, T.FrozenSet[T.Any]]
    compiled_filters = {}
    for key, value in filters.items():
        if isinstance(value, (T.Iterable, T.Iterator)) and not isinstance(value, str):
            uniform_value = frozenset(value)
        else:
            uniform_value = frozenset([value])
        compiled_filters[key] = uniform_value
    return compiled_filters


def match_compiled_filters(message_items, filters, required=True):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]], T.Dict[str, T.FrozenSet[T.Any]], bool) -> bool
    seen = set()
    for key, short_key, value in message_items:
        if short_key in filters:
            if value not in filters[short_key]:
                return False
            else:
                seen.add(short_key)
    if required and len(seen) != len(filters):
        return False
    return True


def datetime_from_bufr(observation, prefix, datetime_keys):
    minute = observation.get(prefix + datetime_keys[4], 0)
    seconds = observation.get(prefix + datetime_keys[5], 0.0)
    second = int(seconds)
    nanosecond = int(seconds * 1000000000) % 1000000000
    return pd.Timestamp(
        *[observation[prefix + k] for k in datetime_keys[:4]] + [minute, second],
        nanosecond=nanosecond
    )


def wmo_station_id_from_bufr(observation, prefix, keys):
    return observation[prefix + keys[0]] * 1000 + observation[prefix + keys[1]]


COMPUTED_KEYS = [
    (['year', 'month', 'day', 'hour', 'minute', 'second'], 'data_datetime', datetime_from_bufr),
    (
        [
            'typicalYear',
            'typicalMonth',
            'typicalDay',
            'typicalHour',
            'typicalMinute',
            'typicalSecond',
        ],
        'typical_datetime',
        datetime_from_bufr,
    ),
    (['blockNumber', 'stationNumber'], 'WMO_station_id', wmo_station_id_from_bufr),
]


def iter_message_items(message, include=None):
    # type: (BufrMessage, T.Container) -> T.Generator[T.Tuple[str, str, T.Any]]
    for key in message:
        short_key = key.rpartition('#')[2]
        if include is None or short_key in include:
            yield (key, short_key, message[key])


def extract_subsets(message_items, subset_count, is_compressed):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]], int, int) -> T.Generator[T.List[T.Tuple[str, str, T.Any]]]
    LOG.debug(
        "extracting subsets count %d and is_compressed %d items %d",
        subset_count,
        is_compressed,
        len(message_items),
    )
    if subset_count == 1:
        yield message_items
    elif is_compressed == 1:
        for i in range(subset_count):
            yield [
                (k, s, v[i] if isinstance(v, (list, np.ndarray)) else v)
                for k, s, v in message_items
            ]
    else:
        header_keys = set()
        for key, short_key, _ in message_items:
            if key[0] != '#' or key[:3] == '#1#':
                header_keys.add(key)
            else:
                header_keys.discard('#1#' + short_key)
        header = [(k, s, v) for k, s, v in message_items if k in header_keys]
        first_subset = True
        subset = []
        for key, short_key, value in message_items:
            if key in header_keys:
                continue
            if key == 'subsetNumber':
                if first_subset:
                    first_subset = False
                else:
                    yield header + subset
                    subset = []
            subset.append((key, short_key, value))
        yield header + subset


def add_computed(data_items, include_computed=frozenset()):
    # type: (T.List[T.Tuple[str, str, T.Any]], T.Container) -> T.List[T.Tuple[str, str, T.Any]]
    computed_items = []
    for keys, computed_key, getter in COMPUTED_KEYS:
        if computed_key in include_computed:
            observation = {short_key: value for _, short_key, value in data_items}
            prefix = '#1#'
            try:
                computed_value = getter(observation, '', keys)
            except Exception:
                LOG.debug("can't compute key %r", computed_key)
                computed_value = None
            computed_items.append((prefix + computed_key, computed_key, computed_value))
    return data_items + computed_items


def merge_data_items(old_data_items, data_items):
    for _, short_name, _ in data_items:
        old_data_items.pop(short_name, None)
    return data_items + list(old_data_items.values())


def extract_observations(subset_items, include_computed=frozenset()):
    # type: (T.List[T.Tuple[str, str, T.Any]], T.Container) -> T.Generator[T.List[T.Tuple[str, str, T.Any]]]
    old_data_items = {}
    data_items = []
    data_seen = set()
    subset_items = add_computed(subset_items, include_computed)
    for key, short_key, value in subset_items:
        if short_key in data_seen:
            all_data_items = merge_data_items(old_data_items, data_items)
            yield add_computed(all_data_items, include_computed)
            old_data_items = {item[1]: item for item in all_data_items}
            data_items = []
            data_seen = set()
        data_items.append((key, short_key, value))
        data_seen.add(short_key)
    if data_items:
        all_data_items = merge_data_items(old_data_items, data_items)
        yield add_computed(all_data_items, include_computed)


def filter_stream(file, columns, filters={}, required_columns=True):
    if required_columns is True:
        required_columns = frozenset(columns)
    elif required_columns is False:
        required_columns = frozenset()
    else:
        required_columns = frozenset(required_columns)
    compiled_filters = compile_filters(filters)
    max_count = max(compiled_filters.get('count', [float('inf')]))
    for count in itertools.count(1):
        if count > max_count:
            LOG.debug("stopping processing after max_count: %d", max_count)
            break
        message = BufrMessage(file)
        if message.codes_id is None:
            break
        LOG.debug("starting reading message: %d", count)
        message_items = [('count', 'count', count)] + list(
            iter_message_items(message, include=compiled_filters)
        )
        if not match_compiled_filters(message_items, compiled_filters, required=False):
            continue
        message['unpack'] = 1
        included_keys = set(compiled_filters)
        included_keys |= set(columns)
        for keys, computed_key, _ in COMPUTED_KEYS:
            if computed_key in included_keys:
                included_keys |= set(keys)
        message_items = list(iter_message_items(message, include=included_keys))
        if 'count' in included_keys:
            message_items += [('count', 'count', count)]
        for subset_items in extract_subsets(
            message_items, message['numberOfSubsets'], message['compressedData']
        ):
            for data_items in extract_observations(subset_items, include_computed=included_keys):
                if match_compiled_filters(data_items, compiled_filters):
                    data = {s: v for k, s, v in data_items if s in columns}
                    if required_columns.issubset(data):
                        yield data


def read_bufr(path, *args, **kwargs):
    with open(path) as file:
        filtered_iterator = filter_stream(file, *args, **kwargs)
        return pd.DataFrame.from_records(filtered_iterator)
