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
    # type: (T.Iterable[T.Tuple[str, T.Any]], T.Dict[str, T.FrozenSet[T.Any]]) -> bool
    seen = set()
    for key, value in message_items:
        short_key = key.rpartition('#')[2]
        if short_key in filters:
            if value not in filters[short_key]:
                return False
            else:
                seen.add(short_key)
    if len(seen) != len(filters):
        return False
    return True


def iter_message_items(message, excluded=frozenset(['unexpandedDescriptors', 'operator'])):
    # type: (messages.Message, T.Container) -> T.Generator[T.Tuple[str, T.Any]]
    for k in message.message_bufr_keys():
        if k not in excluded:
            yield (k, message[k])


def datetime_from_bufr(message_items):
    parts = {
        k.rpartition('#')[2]: v
        for k, v in message_items
        if k.rpartition('#')[2] in ['year', 'month', 'day', 'hour', 'minute']
    }
    return pd.Timestamp(*map(int, [parts[k] for k in ['year', 'month', 'day', 'hour', 'minute']]))


def extract_observations(message_items):
    # type: (T.Iterable[T.Tuple[str, T.Any]]) -> T.Generator[T.List[T.Tuple[str, T.Any]]]
    for subset_items in extract_subsets(message_items):
        observation = subset_items
        observation.append(('datetime', datetime_from_bufr(observation)))
        yield observation


def extract_subsets(message_items):
    # type: (T.Iterable[T.Tuple[str, T.Any]]) -> T.Generator[T.List[T.Tuple[str, T.Any]]]
    subset_count = None
    is_compressed = None
    for key, value in message_items:
        if key == 'numberOfSubsets':
            subset_count = value
        elif key == 'compressedData':
            is_compressed = value
    if subset_count == 1:
        yield message_items
    elif is_compressed == 1:
        for i in range(subset_count):
            yield [(k, v[i] if isinstance(v, list) else v) for k, v in message_items]
    else:
        first_subset = True
        subset = []
        header = []
        for key, value in message_items:
            if key == 'subsetNumber':
                if first_subset:
                    header = subset
                    first_subset = False
                else:
                    yield header + subset
                subset = []
            subset.append((key, value))
        yield subset


def filter_stream(stream, selections, header_filters={}, observation_filters={}):
    compiled_header_filters = compile_filters(header_filters)
    compiled_observation_filters = compile_filters(observation_filters)
    for message in stream:
        message_items = list(iter_message_items(message))
        if not match_compiled_filters(message_items, compiled_header_filters):
            continue
        message['unpack'] = 1
        message_items = list(iter_message_items(message))
        for observation in extract_observations(message_items):
            if match_compiled_filters(observation, compiled_observation_filters):
                yield {k: v for k, v in observation if k.rpartition('#')[2] in selections}


def read_bufr(path, *args, **kwargs):
    stream = messages.FileStream(path, product_kind=eccodes.CODES_PRODUCT_BUFR)
    filtered_iterator = filter_stream(stream, *args, **kwargs)
    return pd.DataFrame.from_records(filtered_iterator)
