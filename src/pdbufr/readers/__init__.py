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
from typing import List
from typing import MutableMapping
from typing import Optional
from typing import Union

import pandas as pd  # type: ignore

from ..high_level_bufr.bufr import BufrFile

LOG = logging.getLogger(__name__)


class Reader(metaclass=ABCMeta):
    def __init__(
        self,
        path_or_messages: Union[str, bytes, "os.PathLike[Any]", Iterable[MutableMapping[str, Any]]],
        **kwargs: Any,
    ):
        self.path_or_messages = path_or_messages
        if isinstance(path_or_messages, (str, bytes, os.PathLike)):
            self.path = path_or_messages
        else:
            self.bufr_obj = path_or_messages

        self._kwargs = {**kwargs}

    def execute(self) -> pd.DataFrame:
        def _read(bufr_obj) -> pd.DataFrame:
            rows = self.read_records(bufr_obj, **self._kwargs)
            df = pd.DataFrame.from_records(rows)
            df = self.adjust_dataframe(df)
            return df

        if hasattr(self, "path"):
            with BufrFile(self.path) as bufr_obj:
                return _read(bufr_obj)

        return _read(self.bufr_obj)

    # def read(self, **kwargs: Any) -> pd.DataFrame:
    #     if hasattr(self, "path"):
    #         with BufrFile(self.path) as bufr_obj:
    #             return self.read_records(bufr_obj, **kwargs)

    #     return self.read_records(self.bufr_obj, **kwargs)

    # def read_records(self, bufr_obj) -> pd.DataFrame:
    #     rows = self._read(bufr_obj)
    #     return pd.DataFrame.from_records(rows)

    @abstractmethod
    def read_records(
        self, bufr_obj: Iterable[MutableMapping[str, Any]], **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        pass

    @abstractmethod
    def adjust_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        pass


class ReaderMaker:
    READERS = {}

    def __call__(
        self, name_or_reader: Union[str, Reader], *args: Any, flat: bool = False, **kwargs
    ) -> Reader:
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

        reader = klass(*args, **kwargs)

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
