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

from pdbufr.core.filters import BufrFilter
from pdbufr.core.filters import MultiFilter
from pdbufr.core.structure import MessageWrapper
from pdbufr.core.structure import filter_keys_cached

from . import Reader

LOG = logging.getLogger(__name__)


class CustomReader(Reader):
    @abstractmethod
    def read_message(
        self,
        message: MessageWrapper,
        units_converter: Optional[Any] = None,
        filters: Optional[Any] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], None, None]:
        pass

    @abstractmethod
    def filter_header(self, message: MessageWrapper) -> bool:
        pass

    @staticmethod
    def get_filtered_keys(message: MessageWrapper, accessors: Dict[str, Any]) -> Dict[str, Any]:
        keys_cache = {}
        included_keys = set()
        for _, p in accessors.items():
            included_keys |= set(p.needed_keys)

        included_keys.add("subsetNumber")

        return filter_keys_cached(message, keys_cache, included_keys)

    def _read(
        self,
        bufr_obj: Any,
        units: Optional[Dict[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], None, None]:
        filters = filters or {}
        filters = dict(filters)
        value_filters = {k: BufrFilter.from_user(filters[k], key=k) for k in filters}

        # create units converter
        units_converter = None
        if units is not None:
            from ..utils.units import UnitsConverter

            units_converter = UnitsConverter.make(units)

        # prepare count filter
        if "count" in value_filters:
            max_count = value_filters["count"].max()
        else:
            max_count = None

        count_filter = value_filters.pop("count", None)

        filters = MultiFilter(filters)

        for count, msg in enumerate(bufr_obj, 1):
            # we use a context manager to automatically delete the handle of the BufrMessage.
            # We have to use a wrapper object here because a message can also be a dict
            with MessageWrapper.wrap(msg) as message:
                # skip decoding messages above max_count
                if max_count is not None and count > max_count:
                    break

                # count filter
                if count_filter is not None and not count_filter.match(count):
                    continue

                # this uses the header so can be called before unpacking
                if not self.filter_header(message):
                    continue

                # message["skipExtraKeyAttributes"] = 1
                message["unpack"] = 1

                for d in self.read_message(
                    message, units_converter=units_converter, filters=filters, **kwargs
                ):
                    yield d
