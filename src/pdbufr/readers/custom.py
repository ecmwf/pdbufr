# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Union

import pandas as pd  # type: ignore

from pdbufr.core.filters import BufrFilter
from pdbufr.core.structure import MessageWrapper
from pdbufr.core.structure import filter_keys_cached

from . import Reader

LOG = logging.getLogger(__name__)


class CustomReader(Reader):
    count_filter = None

    def __init__(
        self,
        *args: Any,
        filters: Optional[Dict[str, Any]] = None,
        accessors: Optional[Dict[str, Any]] = None,
        unit_system: Optional[str] = None,
        units: Optional[Dict[str, str]] = None,
        units_columns: bool = False,
        **kwargs: Any,
    ):
        super().__init__(*args)

        self.bufr_filters, self.count_filter, self.max_count = self.create_filters(filters)
        self.units_converter = self.create_units_converter(unit_system, units)
        self.add_units = units_columns

    @abstractmethod
    def filter_header(self, message: MessageWrapper) -> bool:
        pass

    @staticmethod
    def get_filtered_keys(
        message: MessageWrapper, accessors: Dict[str, Any], filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        keys_cache = {}
        included_keys = set()
        for _, p in accessors.items():
            included_keys |= set(p.needed_keys)

        included_keys.add("subsetNumber")
        included_keys.add("firstOrderStatistics")

        included_keys |= set(list(filters.keys()))

        return filter_keys_cached(message, keys_cache, included_keys)

    @staticmethod
    def create_units_converter(
        unit_system: Optional[str], units: Optional[Union[Dict[str, str], bool]]
    ) -> Optional[Any]:
        if unit_system or units:
            from ..utils.units import UnitsConverter

            return UnitsConverter.make(unit_system, units=units)
        return None

    @staticmethod
    def create_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
        filters = filters or {}
        filters = dict(filters)
        value_filters = {k: BufrFilter.from_user(filters[k], key=k) for k in filters}

        # prepare count filter
        count_filter = value_filters.pop("count", None)
        if count_filter:
            max_count = count_filter.max()
        else:
            max_count = None

        return value_filters, count_filter, max_count

    def read_records(
        self,
        bufr_obj: Any,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], None, None]:

        for count, msg in enumerate(bufr_obj, 1):
            # we use a context manager to automatically delete the handle of the BufrMessage.
            # We have to use a wrapper object here because a message can also be a dict
            with MessageWrapper.wrap(msg) as message:
                # skip decoding messages above max_count
                if self.max_count is not None and count > self.max_count:
                    break

                # count filter
                if self.count_filter is not None and not self.count_filter.match(count):
                    continue

                # this uses the header so can be called before unpacking
                if not self.filter_header(message):
                    continue

                # message["skipExtraKeyAttributes"] = 1
                message["unpack"] = 1

                for d in self.read_message(message):
                    yield d

    @abstractmethod
    def read_message(
        self,
        message: MessageWrapper,
    ) -> Generator[Dict[str, Any], None, None]:
        pass

    def adjust_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


class StationReader(CustomReader):
    @staticmethod
    def make_manager(manager_cache, stnid_keys: Optional[Union[str, list]] = None) -> None:
        if stnid_keys:
            from pdbufr.core.accessor import SidAccessor

            if isinstance(stnid_keys, str):
                stnid_keys = [stnid_keys]
            if not isinstance(stnid_keys, (list, tuple)):
                raise TypeError(f"Invalid keys type: {type(stnid_keys)}. Expected str, list or tuple.")
            ac = SidAccessor.from_user_keys(stnid_keys)
            name = ac.param.name
            manager_cache_id = name + ":" + ",".join(stnid_keys)

            user_ac = {name: ac}
            manager = manager_cache.get(manager_cache_id, user_accessors=user_ac)

            return manager
        return manager_cache.get()
