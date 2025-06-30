# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
from abc import ABCMeta
from abc import abstractmethod
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Mapping
from typing import Union

LOG = logging.getLogger(__name__)

WIGOS_ID_KEY = "WIGOS_station_id"


def normalise_wigos(value):
    if value is not None:
        if isinstance(value, WIGOSId):
            return value
        try:
            return WIGOSId.from_user(value)
        except Exception:
            if isinstance(value, (list, tuple)):
                value = [normalise_wigos(x) for x in value]
                return value

    raise ValueError(f"Invalid WIGOS ID value: {value}")


class BufrFilter(metaclass=ABCMeta):
    @abstractmethod
    def match(self, value: Any) -> bool:
        pass

    @abstractmethod
    def max(self) -> Any:
        pass

    @staticmethod
    def from_user(value: Any, key: Union[str, None] = None) -> "BufrFilter":
        if isinstance(value, slice):
            return SliceBufrFilter(value)
        elif callable(value):
            return CallableBufrFilter(value)
        else:
            if key == WIGOS_ID_KEY:
                value = normalise_wigos(value)
                return WigosValueBufrFilter(value)
            else:
                return ValueBufrFilter(value)


# class EmptyBufrFilter(BufrFilter):
#     def __init__(self) -> None:
#         super().__init__(slice(None, None, None))

#     def match(self, value: Any) -> bool:
#         return True

#     def max(self) -> Any:
#         return None


class SliceBufrFilter(BufrFilter):
    def __init__(self, v: slice) -> None:
        self.slice = v
        if self.slice.step is not None:
            LOG.warning(f"slice filters ignore the step={self.slice.step} in slice={self.slice}")

    def match(self, value: Any) -> bool:
        if value is None:
            return False
        if self.slice.start is not None and value < self.slice.start:
            return False
        elif self.slice.stop is not None and value > self.slice.stop:
            return False
        return True

    def max(self) -> Any:
        return self.slice.stop

    def __repr__(self) -> str:
        return f"SliceBufrFilter({self.slice.start}, {self.slice.stop})"


class CallableBufrFilter(BufrFilter):
    def __init__(self, v: Callable[[Any], bool]) -> None:
        self.callable = v

    def match(self, value: Any) -> bool:
        if value is None:
            return False
        return bool(self.callable(value))

    def max(self) -> Any:
        return None


class ValueBufrFilter(BufrFilter):
    def __init__(self, v: Any) -> None:
        if isinstance(v, Iterable) and not isinstance(v, str):
            self.set = set(v)
        else:
            self.set = {v}

    def match(self, value: Any) -> bool:
        if value is None:
            return False
        return value in self.set

    def max(self) -> Any:
        return max(self.set)


class NotValueBufrFilter(ValueBufrFilter):
    def match(self, value: Any) -> bool:
        if value is None:
            return False
        return value not in self.set

    def max(self) -> Any:
        return None


class WigosValueBufrFilter(ValueBufrFilter):
    def match(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, (str, WIGOSId)):
            return value in self.set
        return False


class WIGOSId:
    def __init__(
        self,
        series: Union[str, int],
        issuer: Union[str, int],
        number: Union[str, int],
        local: str,
    ) -> None:

        def _convert(v):
            return int(v) if v is not None else None

        self.series = _convert(series)
        self.issuer = _convert(issuer)
        self.number = _convert(number)
        self.local = local

        if not isinstance(self.local, str) and self.local is not None:
            raise ValueError("Invalid WIGOS local identifier={self.local}. Must be a string")

    @classmethod
    def from_str(cls, v: str) -> "WIGOSId":
        v = v.split("-")
        if len(v) != 4:
            raise ValueError("Invalid WIGOS ID string")

        return cls(*v)

    @classmethod
    def from_iterable(cls, v):
        return cls(*v)

    def __eq__(self, value):
        if isinstance(value, WIGOSId):
            return all(
                x == y
                for x, y in zip(
                    (self.series, self.issuer, self.number, self.local),
                    (value.series, value.issuer, value.number, value.local),
                )
            )
        elif isinstance(value, (list, tuple)) and len(value) == 4:
            return self == WIGOSId.from_iterable(value)
        elif isinstance(value, str):
            return self.as_str() == value
        return False

    @classmethod
    def from_user(cls, value: Any) -> "WIGOSId":
        if isinstance(value, WIGOSId):
            return cls.from_id(value)
        elif isinstance(value, str):
            return cls.from_str(value)
        elif isinstance(value, (list, tuple)):
            return cls.from_iterable(value)
        raise ValueError(f"Cannot create BufrFilter from value={value} of type={type(value)}")

    def __hash__(self):
        return hash(self.as_str())

    def as_tuple(self):
        return (self.series, self.issuer, self.number, self.local)

    def as_str(self):
        def _convert_str(v):
            return str(v) if v is not None else "*"

        return f"{_convert_str(self.series)}-{_convert_str(self.issuer)}-{_convert_str(self.number)}-{_convert_str(self.local)}"

    def is_valid(self) -> bool:
        return (
            self.series is not None
            and self.issuer is not None
            and self.number is not None
            and isinstance(self.local, str)
        )


def filters_match(
    message: Mapping[str, Any],
    compiled_filters: Dict[str, BufrFilter],
    required: bool = True,
) -> bool:
    matches = 0
    for k in message:
        if k not in compiled_filters:
            continue
        if compiled_filters[k].match(message[k]):
            matches += 1
        else:
            return False
    if required and matches < len(compiled_filters):
        return False
    return True


class ParamFilter(dict):
    def __init__(self, filters, period=False) -> None:
        filters = filters or {}
        super().__init__(filters)
        self.period = period
        self.ignore = set()

    def match(self, data):
        for k, v in data.items():
            if k in self.ignore:
                continue
            self._register_period_key(k)
            if k in self:
                if not self[k].match(v):
                    return False
        return True

    def _register_period_key(self, key: str) -> None:
        from pdbufr.core.accessor import parse_period_key

        if key not in self and self.period:
            simple_name, full_name = parse_period_key(key)
            if simple_name and full_name and simple_name in self:
                self[full_name] = self[simple_name]
            else:
                self.ignore.add(key)
