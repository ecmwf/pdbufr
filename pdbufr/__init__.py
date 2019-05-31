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


class BufrMessage(messages.Message):
    def __iter__(self):
        for key in self.message_bufr_keys():
            yield key


class BufrDict(dict):
    def __getitem__(self, item):
        try:
            return super(BufrDict, self).__getitem__(item)
        except KeyError:
            return super(BufrDict, self).__getitem__('#1#' + item)

    def get(self, item, default=None):
        try:
            return super(BufrDict, self).__getitem__(item)
        except KeyError:
            return super(BufrDict, self).get('#1#' + item, default)


def match_filters(message, filters):
    # type: (T.Mapping, T.Mapping) -> bool
    for key, value in filters.items():
        if message.get(key) != value:
            return False
    return True


def datetime_from_bufr(message):
    return pd.Timestamp(
        *map(int, [message[k] for k in ['year', 'month', 'day', 'hour', 'minute']])
    )

def extract_observations(message):
    # type: (T.Mapping[str, T.Any]) -> T.Generator[T.Dict[str, T.Any]]
    for observation in extract_subsets(message):
        try:
            observation['#1#datetime'] = datetime_from_bufr(observation)
        except Exception:
            # logging.exception("datetime build failed")
            pass
        yield observation


def extract_subsets(message):
    # type: (T.Mapping[str, T.Any]) -> T.Generator[T.Dict[str, T.Any]]
    subset_count = message['numberOfSubsets']
    cached_message = BufrDict(message)
    if subset_count == 1:
        yield cached_message
    else:
        for i in range(subset_count):
            yield BufrDict({
                k: v[i] if isinstance(v, list) and len(v) == subset_count else v
                for k, v in cached_message.items()
            })


def filter_stream(stream, selections, header_filters={}, observation_filters={}):
    for message in stream:
        if match_filters(message, header_filters):
            message['unpack'] = 1
            for observation in extract_observations(message):
                if match_filters(observation, observation_filters):
                    yield {key: observation.get(key) for key in selections}


def read_bufr(path, *args, **kwargs):
    stream = messages.FileStream(
        path, product_kind=eccodes.CODES_PRODUCT_BUFR, message_class=BufrMessage
    )
    filtered_iterator = filter_stream(stream, *args, **kwargs)
    return pd.DataFrame(filtered_iterator)
