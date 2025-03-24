# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
from abc import abstractmethod

from ..bufr_structure import MessageWrapper
from . import Reader

LOG = logging.getLogger(__name__)


class CustomReader(Reader):
    @abstractmethod
    def read_message(self, message):
        pass

    @abstractmethod
    def match_category(self, message):
        pass

    def create_units_checker(self, params, units):
        if units is None:
            return None

        if isinstance(units, dict):
            r_units = {}
            for k, v in units.items():
                if k in self.ACCESSOR_MANAGER.accessors:
                    r_units[k] = v
                else:
                    raise ValueError(f"Unknown parameter in units: {k}")

    def _read(self, bufr_obj, add_height=False, units=None, add_units=False, **kwargs):
        value_filters = {}

        units_converter = None
        if units is not None:
            from ..utils.units import UnitsConverter

            units_converter = UnitsConverter.make(units)

        # prepare count filter
        # if "count" in value_filters:
        #     max_count = value_filters["count"].max()
        # else:
        #     max_count = None

        count_filter = value_filters.pop("count", None)

        for count, msg in enumerate(bufr_obj, 1):
            # we use a context manager to automatically delete the handle of the BufrMessage.
            # We have to use a wrapper object here because a message can also be a dict
            with MessageWrapper.wrap(msg) as message:
                # count filter
                if count_filter is not None and not count_filter.match(count):
                    continue

                # this uses the header so can be called before unpacking
                if not self.match_category(message):
                    continue

                # message["skipExtraKeyAttributes"] = 1
                message["unpack"] = 1

                for d in self.read_message(
                    message, add_height=add_height, units_converter=units_converter, add_units=add_units
                ):
                    yield d
