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


from collections import abc

import attr
import eccodes
from eccodes import messages
import pandas as pd


def datetime_from_bufr(message):
    return pd.Timestamp(
        *map(int, [message[k] for k in ['year', 'month', 'day', 'hour', 'minute']])
    )


COMPUTED_KEYS = {'datetime': (datetime_from_bufr, None)}


@attr.attrs()
class PdMessage(messages.ComputedKeysMessage):
    computed_keys = attr.attrib(default=COMPUTED_KEYS)


@attr.attrs()
class BufrFilter(abc.Iterable):
    stream = attr.attrib()
    selections = attr.attrib()
    header_filters = attr.attrib(default={})
    data_filters = attr.attrib(default={})

    def __iter__(self):
        for message in self.stream:
            if any(message.get(key) != value for key, value in self.header_filters.items()):
                continue
            assert message['numberOfSubsets'] == 1 or message['compressedData'] == 1
            message['unpack'] = 1
            if all(message.get(key) == value for key, value in self.data_filters.items()):
                yield {key: message.get(key) for key in self.selections}


def read_bufr(path, *args, **kwargs):
    stream = messages.FileStream(
        path, product_kind=eccodes.CODES_PRODUCT_BUFR, message_class=PdMessage
    )
    filtered = BufrFilter(stream, *args, **kwargs)
    return pd.DataFrame(filtered)
