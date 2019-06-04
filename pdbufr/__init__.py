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

__version__ = '0.1.1.dev0'

import collections.abc
import logging
import typing as T

import eccodes
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


def match_compiled_filters(message_items, filters):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]], T.Dict[str, T.FrozenSet[T.Any]]) -> bool
    seen = set()
    for key, short_key, value in message_items:
        if short_key in filters:
            if value not in filters[short_key]:
                return False
            else:
                seen.add(short_key)
    if len(seen) != len(filters):
        return False
    return True


def datetime_from_bufr(observation, prefix, datetime_keys):
    return pd.Timestamp(*map(int, [observation[prefix + k] for k in datetime_keys]))


COMPUTED_KEYS = [(['year', 'month', 'day', 'hour', 'minute'], 'datetime', datetime_from_bufr)]


def iter_message_items(message, include=None):
    # type: (BufrMessage, T.Container) -> T.Generator[T.Tuple[str, str, T.Any]]
    for key in message:
        short_key = key.rpartition('#')[2]
        if include is None or short_key in include:
            yield (key, short_key, message[key])


def extract_subsets(message_items, subset_count, is_compressed):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]], int, int) -> T.Generator[T.List[T.Tuple[str, str, T.Any]]]
    if subset_count == 1:
        yield message_items
    elif is_compressed == 1:
        for i in range(subset_count):
            yield [(k, s, v[i] if isinstance(v, list) else v) for k, s, v in message_items]
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


def add_computed(observation_items, include_computed=frozenset()):
    # type: (T.List[T.Tuple[str, str, T.Any]], T.Container) -> T.List[T.Tuple[str, str, T.Any]]
    computed_items = []
    for keys, computed_key, getter in COMPUTED_KEYS:
        if computed_key in include_computed:
            observation = {short_key: value for _, short_key, value in observation_items}
            prefix = '#1#'
            computed_items.append(
                (prefix + computed_key, computed_key, getter(observation, '', keys))
            )
    return observation_items + computed_items


def extract_observations(subset_items, include_computed=frozenset()):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]], T.Container) -> T.Generator[T.List[T.Tuple[str, str, T.Any]]]
    header_keys = set()
    for key, short_key, _ in subset_items:
        if key[0] != '#' or key[:3] == '#1#':
            header_keys.add(key)
        else:
            header_keys.discard('#1#' + short_key)
    header = [(k, s, v) for k, s, v in subset_items if k in header_keys]

    observation_items = []
    observation_seen = set()
    for key, short_key, value in subset_items:
        if key in header_keys:
            continue
        if short_key in observation_seen:
            yield add_computed(header + observation_items, include_computed)
            observation_items = []
            observation_seen = set()
        observation_items.append((key, short_key, value))
        observation_seen.add(short_key)
    yield add_computed(header + observation_items, include_computed)


def filter_stream(file, columns, header_filters={}, observation_filters={}):
    compiled_header_filters = compile_filters(header_filters)
    compiled_observation_filters = compile_filters(observation_filters)
    while True:
        message = BufrMessage(file)
        if message.codes_id is None:
            break
        message_items = list(iter_message_items(message, include=compiled_header_filters))
        if not match_compiled_filters(message_items, compiled_header_filters):
            continue
        message['unpack'] = 1
        included_keys = set(compiled_observation_filters)
        included_keys |= set(columns)
        for keys, computed_key, _ in COMPUTED_KEYS:
            if computed_key in included_keys:
                included_keys |= set(keys)
        message_items = list(iter_message_items(message, include=included_keys))
        for subset_items in extract_subsets(
            message_items, message['numberOfSubsets'], message['compressedData']
        ):
            for observation_items in extract_observations(
                subset_items, include_computed=included_keys
            ):
                if match_compiled_filters(observation_items, compiled_observation_filters):
                    yield {s: v for k, s, v in observation_items if s in columns}


def read_bufr(path, *args, **kwargs):
    with open(path) as file:
        filtered_iterator = filter_stream(file, *args, **kwargs)
        return pd.DataFrame.from_records(filtered_iterator)
