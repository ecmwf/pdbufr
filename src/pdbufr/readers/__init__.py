# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
import os
import typing as T
from abc import ABCMeta
from abc import abstractmethod
from importlib import import_module

import pandas as pd  # type: ignore

from .. import bufr_structure
from ..high_level_bufr.bufr import BufrFile

LOG = logging.getLogger(__name__)


class Reader(metaclass=ABCMeta):
    def __init__(
        self,
        path_or_messages: T.Union[str, bytes, "os.PathLike[T.Any]", T.Iterable[T.MutableMapping[str, T.Any]]],
    ):
        if isinstance(path_or_messages, (str, bytes, os.PathLike)):
            self.path = path_or_messages
        else:
            self.bufr_obj = path_or_messages

    def read(self, **kwargs):
        if hasattr(self, "path"):
            with BufrFile(self.path) as bufr_obj:
                return self.read_records(bufr_obj, **kwargs)

        return self.read_records(self.bufr_obj, **kwargs)

    def read_records(self, bufr_obj, **kwargs):
        rows = self._read(bufr_obj, **kwargs)
        return pd.DataFrame.from_records(rows)

    @abstractmethod
    def _read(self, bufr_obj, **kwargs):
        pass


# class CustomReader(Reader):
#     @abstractmethod
#     def read_message(self, message):
#         pass

#     @abstractmethod
#     def category_filter(self, message):
#         pass

#     def _read(self, bufr_obj):
#         value_filters = {}

#         # prepare count filter
#         if "count" in value_filters:
#             max_count = value_filters["count"].max()
#         else:
#             max_count = None

#         count_filter = value_filters.pop("count", None)

#         for count, msg in enumerate(bufr_obj, 1):
#             # we use a context manager to automatically delete the handle of the BufrMessage.
#             # We have to use a wrapper object here because a message can also be a dict
#             with MessageWrapper.wrap(msg) as message:
#                 # count filter
#                 if count_filter is not None and not count_filter.match(count):
#                     continue

#                 if not self._category_filter(message):
#                     continue

#                 # message["skipExtraKeyAttributes"] = 1
#                 message["unpack"] = 1

#                 for d in self._read_message(message):
#                     yield d


class ReaderMaker:
    READERS = {}

    def __call__(self, name_or_reader, *args, **kwargs):
        if isinstance(name_or_reader, Reader):
            return name_or_reader

        name = name_or_reader

        if name in self.READERS:
            klass = self.READERS[name]
        else:
            klass = self.get(name)
            self.READERS[name] = klass

        if not klass:
            raise ValueError(f"Unknown reader type: {name}")

        reader = klass(*args, **kwargs)

        if getattr(reader, "name", None) is None:
            reader.name = name

        return reader

    def __getattr__(self, name):
        return self(name.replace("_", "-"))

    def get(self, name):
        here = os.path.dirname(__file__)
        for path in sorted(os.listdir(here)):
            if path[0] in ("_", "."):
                continue

            if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):
                base, _ = os.path.splitext(path)
                p = base.replace("_", "-")
                if p == name:
                    try:
                        module = import_module(f".{name}", package=__name__)
                        if hasattr(module, "reader"):
                            w = getattr(module, "reader")
                            return w
                    except Exception:
                        LOG.exception("Error loading reader %s", name)


get_reader = ReaderMaker()
