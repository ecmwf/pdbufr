# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
import re
from abc import ABCMeta
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import pdbufr.core.param as PARAMS
from pdbufr.core.keys import COMPUTED_KEYS
from pdbufr.utils.exception import AllValueMissingException

LOG = logging.getLogger(__name__)


class Accessor(metaclass=ABCMeta):
    keys: Optional[Dict[str, Any]] = None
    param: Optional[Any] = None
    mandatory: Optional[List[str]] = None
    dtype = None

    def __init__(
        self, keys: Optional[Union[Dict[str, Any], str, List[str]]] = None, dtype: Optional[Any] = None
    ):
        """
        Accessor class to extract values from a BUFR message.

        Parameters
        ----------
        keys : dict, str, list of str, optional
            Mapping between the keys to extract and the corresponding Parameters. When None, the
            static ``keys`` member is used. When not a dict, it is converted to a dict with the
            same key(s) and value(s).
        """
        if keys is None:
            self.keys = self.keys
            if self.keys:
                self.keys = {**self.keys}
            else:
                self.keys = {}
        else:
            self.keys = keys

        assert isinstance(self.keys, dict)

        if self.param is None:
            if len(self.keys) == 1:
                self.param = list(self.keys.values())[0]

        # LOG.debug(f"Accessor {self.__class__.__name__} initialized with keys: {self.keys}")

        self.bufr_keys = list([k for k in self.keys.keys() if not k.startswith("_")])
        self.labels = [v.label for k, v in self.keys.items() if v is not None]
        self.name = self.__class__.__name__

        self.dtype = dtype

        # LOG.debug(f"Accessor {self.name} initialized with labels: {self.labels}")

    @abstractmethod
    def empty_result(self) -> Any:
        pass

    @property
    @abstractmethod
    def needed_keys(self) -> List[str]:
        pass

    @abstractmethod
    def collect(self, collector: Any, **kwargs: Any) -> Any:
        pass


class SimpleAccessor(Accessor):
    def empty_result(self) -> Dict[str, Optional[Any]]:
        return dict(zip(self.labels, [None] * len(self.labels)))

    @property
    def needed_keys(self) -> List[str]:
        return self.bufr_keys

    def collect(
        self,
        collector: Any,
        raise_on_missing: bool = False,
        units_converter: Optional[Any] = None,
        add_units: bool = False,
        **kwargs: Any,
    ) -> Any:
        return self.collect_any(
            collector,
            raise_on_missing=raise_on_missing,
            units_converter=units_converter,
            add_units=add_units,
            **kwargs,
        )

    def parse_collected(
        self,
        value: Optional[Dict[str, Any]],
        skip: List[Any],
        units_converter: Optional[Any],
        add_units: bool,
        raise_on_missing: bool,
    ) -> Dict[str, Any]:
        if value is None:
            value = {}

        if raise_on_missing and (not value or all(v is None for v in value.values())):
            raise AllValueMissingException(f"No value found for accessor={self.name}")

        res = {}
        for key, param in self.keys.items():
            if param is not None:
                if param.is_fixed():
                    res[param.label] = param.value
                else:
                    label = param.label
                    if param in skip:
                        continue

                    v, units = value.get(key, (None, None))

                    # convert units
                    if v is not None and units_converter is not None and param.units:
                        v, units = units_converter.convert(label, v, units)

                    # handle period
                    if param.is_period():
                        v = param.concat_units(v, units)
                    elif (
                        v is not None and self.dtype is not None and self.param and self.param.label == label
                    ):
                        try:
                            v = self.dtype(v)
                        except Exception:
                            pass

                    res[label] = v

                    # add units column
                    if add_units and param.units:
                        res[label + "_units"] = units

        return res

    def collect_any(
        self,
        collector: Any,
        mandatory: Optional[List[str]] = None,
        skip: Optional[List[Any]] = None,
        raise_on_missing: bool = False,
        units_keys: Optional[List[str]] = None,
        units_converter: Optional[Any] = None,
        add_units: bool = False,
        first: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        value = None
        mandatory = mandatory or []
        skip = skip or []

        units_keys = units_keys or []
        if units_converter is not None or add_units:
            units_keys.extend(self.bufr_keys)

        multi_res = []

        if filters is None:
            filters = {}

        for v in collector.collect(self.bufr_keys, filters, mandatory_keys=mandatory, units_keys=units_keys):
            value = v
            res = self.parse_collected(value, skip, units_converter, add_units, raise_on_missing)
            if first:
                return res
            else:
                multi_res.append(res)

        if first:
            if raise_on_missing:
                raise AllValueMissingException(f"No value found for accessor={self.name}")
            return {}
        else:
            return multi_res


class ComputedKeyAccessor(Accessor):
    def __init__(self, *args: Any, method_kwargs=None, **kwargs: Any):
        super().__init__(*args, **kwargs)

        key = list(self.keys.keys())[0]
        assert isinstance(key, str)
        for k in COMPUTED_KEYS:
            if k[1] == key:
                self._meth = k[2]
                self._keys = k[0]
                break

        if not hasattr(self, "_meth"):
            raise ValueError(f"Unknown computed key {self.keys[0]}")

        self.method_kwargs = method_kwargs or {}

    def empty_result(self) -> Dict[str, Optional[Any]]:
        return dict(zip(self.labels, [None] * len(self.labels)))

    @property
    def needed_keys(self) -> List[str]:
        return self._keys

    def collect(self, collector: Any, raise_on_missing: bool = False, **kwargs: Any) -> Dict[str, Any]:
        value = None
        for v in collector.collect(self._keys, {}, value_and_units=False):
            value = v
            break

        try:
            val = self._meth(value, "", self._keys, **self.method_kwargs)
        except Exception:
            if raise_on_missing:
                raise
            val = None

        if val is not None and self.dtype is not None:
            try:
                val = self.dtype(val)
            except Exception:
                pass

        if val is None and raise_on_missing:
            raise AllValueMissingException(f"Missing value for {self.name}")

        return {self.labels[0]: val}


class CoordAccessor(SimpleAccessor):
    def __init__(
        self,
        coords: Optional[List[Any]] = None,
        fixed_coords: Optional[Any] = None,
        period: Optional[str] = None,
        fixed_period: Optional[Any] = None,
        first: bool = True,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        self.mandatory = [*self.bufr_keys]
        self.key_labels = [*self.labels]
        self.first = first

        # period coords
        self.period_bufr_key = None
        self.period = None

        if fixed_period and period:
            raise ValueError("Cannot have both fixed_period and period")

        if period:
            self.period_bufr_key = period
            self.period = PARAMS.PeriodParameter("_period")
            self.keys[period] = self.period
            # period precedes the param keys in the message
            self.bufr_keys = [period, *self.bufr_keys]
            self.mandatory.append(period)
        elif fixed_period:
            self.period = PARAMS.FixedParameter("_period", fixed_period)

        # other coords
        if fixed_coords and coords:
            raise ValueError("Cannot have both fixed_coords and coords")

        self.coords = {}
        self.extract_coords = []

        if coords:
            for c in coords:
                coord_bufr_key = c[0]
                coord_suffix = c[1]
                coord_mandatory = c[2]

                c = PARAMS.CoordParameter(coord_bufr_key, suffix=coord_suffix)
                self.coords[coord_bufr_key] = c
                self.keys[coord_bufr_key] = c
                # coords precedes the param keys in the message
                self.bufr_keys = [coord_bufr_key, *self.bufr_keys]
                if coord_mandatory:
                    self.mandatory.append(coord_bufr_key)

            self.extract_coords = list(self.coords.values())

        elif fixed_coords:
            coord_suffix = "level"
            c = PARAMS.FixedCoordParameter("_fixed_coords", fixed_coords, suffix=coord_suffix)
            self.coords["_fixed_coords"] = c

    def get_period(self, record: Dict[str, Any]) -> str:
        if self.period:
            if self.period.is_fixed():
                return self.period.value
            period = record.pop("_period", None)
            if not period or period is None:
                period = "nan"
            return period
        return None

    def get_coords(self, record: Dict[str, Any], period) -> Dict[str, Any]:
        if self.coords:
            coords = {}
            if self.extract_coords:
                for coord in self.extract_coords:
                    v = record.pop(coord.label, None)
                    for key in self.key_labels:
                        label = key + period + "_" + coord.suffix
                        coords[label] = v
            else:
                for key in self.key_labels:
                    for k, coord in self.coords.items():
                        label = key + period + "_" + coord.suffix
                        coords[label] = coord.value

            return coords
        return None

    def get_units(self, record: Dict[str, Any], period: str) -> Dict[str, Any]:
        units = {}
        for key in self.key_labels:
            label = key + "_units"
            if label in record:
                v = record.pop(label, None)
                label = key + period + "_units"
                units[label] = v
        return units

    def relabel(
        self, value: Union[Dict[str, Any], List[Dict[str, Any]]], add_coord: bool, add_units: bool
    ) -> Dict[str, Any]:
        if isinstance(value, dict):
            value = [value]

        res = {}
        for r in value:
            # LOG.debug(f"CoordAccessor: relabeling record: {r}")
            period = self.get_period(r)
            coords = None
            units = None

            if period is not None:
                period = "_<" + period + ">"
            else:
                period = ""

            if add_coord:
                coords = self.get_coords(r, period)
            if add_units:
                units = self.get_units(r, period)

            # LOG.debug(f"Period: {period}, coords: {coords}, units: {units}")

            assert len(r) <= len(
                self.key_labels
            ), f"Record {r} has more keys than expected: {self.key_labels}! {len(r)} != {len(self.key_labels)}"

            for k, v in r.items():
                if k in self.key_labels:
                    res[k + period] = v

            if units:
                res.update(units)

            if coords:
                res.update(coords)

        return res

    def collect(
        self,
        collector: Any,
        raise_on_missing: bool = False,
        add_coord: bool = False,
        units_converter: Optional[Any] = None,
        add_units: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        skip = []
        if not add_coord:
            skip = self.extract_coords

        mandatory = self.mandatory

        units_keys = []
        if self.period_bufr_key:
            units_keys = [self.period_bufr_key]

        value = self.collect_any(
            collector,
            mandatory=mandatory,
            skip=skip,
            raise_on_missing=raise_on_missing,
            units_keys=units_keys,
            units_converter=units_converter,
            add_units=add_units,
            first=self.first,
            **kwargs,
        )

        value = self.relabel(value, add_coord, add_units)
        return value

    def __repr__(self):
        return f"{self.__class__.__name__} param={self.param} keys{self.keys}"


class MultiAccessorBase(Accessor):
    accessors: List[Accessor] = []

    def __init__(self, accessors: Optional[List[Accessor]] = None, **kwargs: Any):
        self.accessors = accessors or self.accessors
        super().__init__(**kwargs)

    def empty_result(self) -> Dict[str, Optional[Any]]:
        return self.accessors[0].empty_result()

    @property
    def needed_keys(self) -> List[str]:
        r = []
        for a in self.accessors:
            r.extend(a.needed_keys)
        return r


class MultiFirstAccessor(MultiAccessorBase):
    def collect(self, collector: Any, **kwargs: Any) -> Dict[str, Any]:
        for a in self.accessors:
            try:
                r = a.collect(collector, raise_on_missing=True, **kwargs)
                if r:
                    return r
            except AllValueMissingException:
                pass
            except Exception:
                # LOG.debug(f"Error collecting from {a.name}: {e}")
                # raise
                pass

        return self.empty_result()


class MultiAllAccessor(MultiAccessorBase):
    def collect(self, collector: Any, **kwargs: Any) -> Dict[str, Any]:
        res = {}
        for a in self.accessors:
            r = a.collect(collector, raise_on_missing=False, **kwargs)
            if r:
                res.update(r)

        if res:
            return res
        return self.empty_result()


class LatLonAccessor(SimpleAccessor):
    param: Any = PARAMS.LATLON
    keys: Dict[str, Any] = {"latitude": PARAMS.LAT, "longitude": PARAMS.LON}
    _cache = {}


DEFAULT_SID_ACCESSORS = {
    "ident": SimpleAccessor(keys={"ident": PARAMS.SID}, dtype=str),
    "WMO_station_id": ComputedKeyAccessor(keys={"WMO_station_id": PARAMS.SID}, dtype=str),
    "WIGOS_station_id": ComputedKeyAccessor(
        keys={"WIGOS_station_id": PARAMS.SID}, method_kwargs={"check_valid": True}, dtype=str
    ),
    "shipOrMobileLandStationIdentifier": SimpleAccessor(
        keys={"shipOrMobileLandStationIdentifier": PARAMS.SID}, dtype=str
    ),
    "station_id": SimpleAccessor(keys={"station_id": PARAMS.SID}, dtype=str),
    "icaoLocationIndicator": SimpleAccessor(keys={"icaoLocationIndicator": PARAMS.SID}, dtype=str),
    "stationOrSiteName": SimpleAccessor(keys={"stationOrSiteName": PARAMS.SID}, dtype=str),
    "longStationName": SimpleAccessor(keys={"longStationName": PARAMS.SID}, dtype=str),
}


class SidAccessor(MultiFirstAccessor):
    param: Any = PARAMS.SID
    accessors: List[Accessor] = list(DEFAULT_SID_ACCESSORS.values())
    _cache: Dict[str, "SidAccessor"] = {}

    @classmethod
    def from_user_keys(cls, keys: Union[str, List[str]]) -> "SidAccessor":
        """
        Create a SidAccessor from user-defined keys.

        Parameters
        ----------
        keys : str or list of str
            The keys to use for the SID accessor.

        Returns
        -------
        SidAccessor
            A new SidAccessor instance with the specified keys.
        """
        if isinstance(keys, str):
            keys = [keys]
        if not isinstance(keys, (list, tuple)):
            raise TypeError(f"Invalid keys type: {type(keys)}. Expected str, list or tuple.")

        lst = []
        for k in keys:
            if k in DEFAULT_SID_ACCESSORS:
                lst.append(DEFAULT_SID_ACCESSORS[k])
            else:
                ac = SimpleAccessor(keys={k: PARAMS.SID}, dtype=str)
                lst.append(ac)

        r = cls(accessors=lst)
        key = tuple(keys)
        if key not in cls._cache:
            cls._cache[key] = r
        return cls._cache[key]


class StationNameAccessor(MultiFirstAccessor):
    param: Any = PARAMS.STATION_NAME
    accessors: List[Accessor] = [
        SimpleAccessor(keys={"stationOrSiteName": PARAMS.STATION_NAME}),
        SimpleAccessor(keys={"icaoLocationIndicator": PARAMS.STATION_NAME}),
    ]


class ElevationAccessor(MultiFirstAccessor):
    param: Any = PARAMS.ELEVATION
    accessors: List[Accessor] = [
        SimpleAccessor(keys={"heightOfStationGroundAboveMeanSeaLevel": PARAMS.ELEVATION}),
        SimpleAccessor(keys={"heightOfStation": PARAMS.ELEVATION}),
    ]


class DatetimeAccessor(ComputedKeyAccessor):
    param: Any = PARAMS.TIME
    keys: Dict[str, Any] = {"data_datetime": PARAMS.TIME}


class AccessorManager:
    def __init__(
        self,
        default: List[Accessor],
        user_accessors: Optional[Dict[str, Accessor]] = None,
        **kwargs,
    ):
        if not isinstance(default, (list, tuple)):
            raise ValueError(f"Default accessors must be a list, got {type(default)}")

        accessors = set(default)
        for k, v in kwargs.items():
            if not isinstance(v, (list, tuple)):
                f"Group '{k}' must be a list, got {type(v)}"
            accessors.update(v)

        self.accessors = {a.param.label: a() for a in accessors}

        # replace default accessors with user-defined ones
        if user_accessors:
            for k, v in user_accessors.items():
                if k not in self.accessors:
                    raise ValueError(
                        f"User accessor '{k}' is not in the default accessors. Available: {self.accessors.keys()}"
                    )
                if not isinstance(v, Accessor):
                    raise ValueError(f"User accessor '{k}' must be an Accessor instance, got {type(v)}")
                self.accessors[k] = v

        def _build(lst):
            return {a.param.label: self.accessors[a.param.label] for a in lst}

        self.default = _build(default)
        self.groups = {"default": self.default}
        for k, v in kwargs.items():
            self.groups[k] = _build(v)

        self.cache = {}

    def get(self, params: Optional[Union[str, List[str]]]) -> Dict[str, Accessor]:
        if isinstance(params, str):
            if params.startswith("_"):
                raise ValueError(f"Invalid parameter name '{params}'")
            accessors = self.groups.get(params, None)
            if accessors is not None:
                return accessors

        cache_key = tuple(params)

        if cache_key in self.cache:
            accessors = self.cache[cache_key]
        else:
            if isinstance(params, str):
                params = [params]
            v = list(params)
            accessors = {}
            for param in v:
                if param.startswith("_"):
                    raise ValueError(f"Invalid parameter name '{param}'")
                if param in self.groups:
                    accessors.update(self.groups[param])
                elif param in self.accessors:
                    accessors[param] = self.accessors[param]
                else:
                    raise ValueError(
                        f"Unsupported parameter '{param}'. Available parameters: {self.accessors.keys()}"
                    )

            self.cache[cache_key] = accessors

            assert accessors is not None

        return accessors

    def get_by_object(self, accessor: Any) -> Accessor:
        if not issubclass(accessor, Accessor):
            raise ValueError(f"Invalid accessor type={type(accessor)}")
        label = accessor.param.label
        return self.accessors[label]

    @staticmethod
    def labels(accessors: Dict[str, Accessor]) -> List[str]:
        r = set()
        for name, ac in accessors.items():
            r.add(name)
            labels = ac.labels
            # LOG.debug(f"Accessor {name} has labels: {labels}")
            if isinstance(labels, str):
                labels = [labels]
            if labels:
                r.update(labels)
        return r


class AccessorManagerCache(metaclass=ABCMeta):
    def __init__(self):
        self.cache = {"default": self.make()}

    @abstractmethod
    def make(self, *args, **kwargs):
        pass

    def get(self, key=None, **kwargs) -> AccessorManager:
        """Get the accessor manager for the given key."""
        if key is None or key == "default":
            return self.cache["default"]
        if key in self.cache:
            return self.cache[key]
        else:
            manager = self.make(**kwargs)
            self.cache[key] = manager
            return manager

    def __contains__(self, key: str) -> bool:
        """Check if the accessor manager for the given key exists."""
        return key in self.cache


PERIOD_RX = re.compile(r"(.+)_<(.+)>(.*)")

"""
Period key names are encoded at the accessor level as:

    name_<period>rest

E.g. "wind_gust_<1h>" or "wind_gust_<1h>_units".
"""


def resolve_period_key(key: str) -> Optional[str]:
    """
    Resolve the period key name by removing the <> brackets.

    Parameters
    ----------
    key : str
        The key to resolve.
    """
    m = PERIOD_RX.match(key)
    if m is not None:
        name = m.group(1)
        period = m.group(2)
        rest = m.group(3)
        return name + "_" + period + rest
    return key


def parse_period_key(key: str) -> Optional[str]:
    """
    Parse the period key name.

    Parameters
    ----------
    key : str
        The key to parse.

    Returns
    -------
    tuple
        - the key name
        - the key name without the period

        if the key does not contain a period, return None, None
    """
    m = PERIOD_RX.match(key)
    if m is not None:
        name = m.group(1)
        # period = m.group(2)
        rest = m.group(3)
        return key, name + rest
    return None, None
