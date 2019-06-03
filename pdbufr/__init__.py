#
# Copyright 2017-2018 European Centre for Medium-Range Weather Forecasts (ECMWF).
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

__version__ = '0.0.1.dev0'

import logging
import typing as T

import eccodes
from eccodes import messages
import pandas as pd


LOG = logging.getLogger(__name__)


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


def datetime_from_bufr(observation, datetime_keys):
    return pd.Timestamp(*map(int, [observation[k] for k in datetime_keys]))


COMPUTED_KEYS = [
    (['year', 'month', 'day', 'hour', 'minute'], 'datetime', datetime_from_bufr)
]


def iter_message_items(message, include=None):
    # type: (messages.Message, T.Container) -> T.Generator[T.Tuple[str, str, T.Any]]
    for key in message.message_bufr_keys():
        short_key = key.rpartition('#')[2]
        if include is None or short_key in include:
            yield (key, short_key, message[key])


def extract_subsets(message_items):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]]) -> T.Generator[T.List[T.Tuple[str, str, T.Any]]]
    subset_count = None
    is_compressed = None
    for key, short_key, value in message_items:
        if key == 'numberOfSubsets':
            subset_count = value
        elif key == 'compressedData':
            is_compressed = value
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


def extract_observations(subset_items):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]]) -> T.Generator[T.List[T.Tuple[str, str, T.Any]]]
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
            for keys, computed_key, getter in COMPUTED_KEYS:
                try:
                    observation_items.append((computed_key, computed_key, getter(observation_items, keys)))
                except Exception:
                    logging.exception("can't compute key %r", computed_key)
            yield header + observation_items
            observation_items = []
            observation_seen = set()
        observation_items.append((key, short_key, value))
        observation_seen.add(short_key)
    yield header + observation_items


def filter_stream(stream, selections, header_filters={}, observation_filters={}):
    compiled_header_filters = compile_filters(header_filters)
    compiled_observation_filters = compile_filters(observation_filters)
    for message in stream:
        message_items = list(iter_message_items(message, include=compiled_header_filters))
        if not match_compiled_filters(message_items, compiled_header_filters):
            continue
        message['unpack'] = 1
        included_keys = {'numberOfSubsets', 'compressedData'}
        included_keys |= set(compiled_observation_filters)
        included_keys |= set(selections)
        for keys, _, _ in COMPUTED_KEYS:
            included_keys |= set(keys)
        message_items = list(iter_message_items(message, include=included_keys))
        for subset_items in extract_subsets(message_items):
            for observation_items in extract_observations(subset_items):
                if match_compiled_filters(observation_items, compiled_observation_filters):
                    yield {s: v for k, s, v in observation_items if s in selections}


def read_bufr(path, *args, **kwargs):
    stream = messages.FileStream(path, product_kind=eccodes.CODES_PRODUCT_BUFR)
    filtered_iterator = filter_stream(stream, *args, **kwargs)
    return pd.DataFrame.from_records(filtered_iterator)
