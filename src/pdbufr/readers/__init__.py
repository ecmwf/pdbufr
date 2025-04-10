# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
import os
from abc import ABCMeta
from abc import abstractmethod
from importlib import import_module
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import MutableMapping
from typing import Union

import pandas as pd  # type: ignore

from ..high_level_bufr.bufr import BufrFile

LOG = logging.getLogger(__name__)


class Reader(metaclass=ABCMeta):
    def __init__(
        self,
        path_or_messages: Union[str, bytes, "os.PathLike[Any]", Iterable[MutableMapping[str, Any]]],
    ):
        self.path_or_messages = path_or_messages
        if isinstance(path_or_messages, (str, bytes, os.PathLike)):
            self.path = path_or_messages
        else:
            self.bufr_obj = path_or_messages

    def read(self, **kwargs: Any) -> pd.DataFrame:
        if hasattr(self, "path"):
            with BufrFile(self.path) as bufr_obj:
                return self.read_records(bufr_obj, **kwargs)

        return self.read_records(self.bufr_obj, **kwargs)

    def read_records(self, bufr_obj, **kwargs: Any) -> pd.DataFrame:
        rows = self._read(bufr_obj, **kwargs)
        return pd.DataFrame.from_records(rows)

    @abstractmethod
    def _read(self, bufr_obj: Iterable[MutableMapping[str, Any]], **kwargs: Any) -> Iterator[Dict[str, Any]]:
        pass


class ReaderMaker:
    READERS = {}

    def __call__(self, name_or_reader: Union[str, Reader], *args: Any, flat: bool = False) -> Reader:
        if isinstance(name_or_reader, Reader):
            return name_or_reader

        name = name_or_reader

        # provide backwards compatibility
        if name == "generic" and "flat":
            if flat:
                name = "flat"

        if name in self.READERS:
            klass = self.READERS[name]
        else:
            klass = self.get(name)
            self.READERS[name] = klass

        if not klass:
            raise ValueError(f"Unknown reader type: {name}")

        reader = klass(*args)

        if getattr(reader, "name", None) is None:
            reader.name = name

        return reader

    def __getattr__(self, name: str) -> Reader:
        return self(name.replace("_", "-"))

    def get(self, name: str) -> type[Reader]:
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
                        raise

        raise ValueError(f"Unknown reader type: {name}")


get_reader = ReaderMaker()
