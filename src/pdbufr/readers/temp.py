# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Mapping
from typing import Optional
from typing import Union

import pandas as pd

import pdbufr.core.param as PARAMS
from pdbufr.core.accessor import Accessor
from pdbufr.core.accessor import AccessorManager
from pdbufr.core.accessor import AccessorManagerCache
from pdbufr.core.accessor import DatetimeAccessor
from pdbufr.core.accessor import ElevationAccessor
from pdbufr.core.accessor import LatLonAccessor
from pdbufr.core.accessor import SidAccessor
from pdbufr.core.accessor import SimpleAccessor
from pdbufr.core.accessor import StationNameAccessor
from pdbufr.core.filters import ParamFilter
from pdbufr.core.param import Parameter
from pdbufr.core.subset import BufrSubsetReader
from pdbufr.utils.convert import period_to_timedelta
from pdbufr.utils.units import UnitsConverter

from .custom import StationReader
from .geopot import GeopotentialHandler

LOG = logging.getLogger(__name__)


class PressureLevelAccessor(SimpleAccessor):
    keys: Dict[str, Optional[Parameter]] = {
        "pressure": PARAMS.PRESSURE,
        "verticalSoundingSignificance": None,
        "nonCoordinateGeopotential": PARAMS.Z,
        "nonCoordinateGeopotentialHeight": PARAMS.ZH,
        "airTemperature": PARAMS.T,
        "dewpointTemperature": PARAMS.TD,
        "windSpeed": PARAMS.WIND_SPEED,
        "windDirection": PARAMS.WIND_DIR,
    }
    param: Parameter = Parameter("plev", "pressure_level")

    def empty_result(self) -> List[Any]:
        return []

    def collect(
        self,
        collector: Any,
        labels: Optional[Any] = None,
        ref_date: Optional[Any] = None,
        ref_lat: Optional[Any] = None,
        ref_lon: Optional[Any] = None,
        raise_on_missing: bool = False,
        units_converter: Optional[UnitsConverter] = None,
        add_units: bool = False,
        **kwargs: Any,
    ) -> List[Any]:
        mandatory = ["pressure", "verticalSoundingSignificance"]
        return self.collect_any(
            collector,
            mandatory=mandatory,
            raise_on_missing=raise_on_missing,
            units_converter=units_converter,
            add_units=add_units,
            first=False,
            **kwargs,
        )


class OffsetPressureLevelAccessor(PressureLevelAccessor):
    keys: Dict[str, Optional[Parameter]] = {
        "timePeriod": PARAMS.TIME_OFFSET,
        "extendedVerticalSoundingSignificance": None,
        "pressure": PARAMS.PRESSURE,
        "nonCoordinateGeopotential": PARAMS.Z,
        "nonCoordinateGeopotentialHeight": PARAMS.ZH,
        "airTemperature": PARAMS.T,
        "dewpointTemperature": PARAMS.TD,
        "windSpeed": PARAMS.WIND_SPEED,
        "windDirection": PARAMS.WIND_DIR,
        "latitudeDisplacement": PARAMS.LAT_OFFSET,
        "longitudeDisplacement": PARAMS.LON_OFFSET,
    }
    param: Parameter = Parameter("plev_offset", "pressure_level_with_offset")

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.time_offset = self.keys["timePeriod"]
        self.lat_offset = self.keys["latitudeDisplacement"]
        self.lon_offset = self.keys["longitudeDisplacement"]

    def parse_collected(
        self,
        value: Optional[Dict[str, Any]],
        skip: List[Any],
        units_converter: Optional[UnitsConverter],
        add_units: bool,
        raise_on_missing: bool,
    ) -> Dict[str, Any]:
        if value is None:
            value = {}

        res = {}
        for key, param in self.keys.items():
            if param is not None:
                label = param.label
                if param in skip:
                    continue

                v, units = value.get(key, (None, None))

                if v is not None and units_converter is not None and param.units:
                    v, units = units_converter.convert(label, v, units)

                if param.is_period():
                    v = period_to_timedelta(v, units)

                res[label] = v

                if add_units and param.units:
                    res[label + "_units"] = units

        return res

    def collect(
        self,
        collector: Any,
        labels: Optional[Any] = None,
        ref_date: Optional[Any] = None,
        ref_lat: Optional[Any] = None,
        ref_lon: Optional[Any] = None,
        raise_on_missing: bool = False,
        units_converter: Optional[UnitsConverter] = None,
        add_units: bool = False,
        add_offsets: bool = True,
        **kwargs: Any,
    ) -> List[Any]:
        mandatory = ["extendedVerticalSoundingSignificance", "pressure"]

        units_keys = []
        if add_offsets:
            skip = [self.lat_offset, self.lon_offset]
            units_keys = ["timePeriod"]
        else:
            skip = [self.time_offset, self.lat_offset, self.lon_offset]

        return self.collect_any(
            collector,
            mandatory=mandatory,
            skip=skip,
            raise_on_missing=raise_on_missing,
            units_converter=units_converter,
            add_units=add_units,
            units_keys=units_keys,
            first=False,
            **kwargs,
        )


LOCATION_ACCESSORS = (LatLonAccessor,)
GEOMETRY_ACCESSORS = (
    LatLonAccessor,
    ElevationAccessor,
)
STATION_ACCESSORS: tuple = (SidAccessor, LatLonAccessor, ElevationAccessor, DatetimeAccessor)
EXTRA_STATION_ACCESSORS = (StationNameAccessor,)
DEFAULT_OBS_ACCESSORS: tuple = (PressureLevelAccessor, OffsetPressureLevelAccessor)

DEFAULT_ACCESSORS = STATION_ACCESSORS + DEFAULT_OBS_ACCESSORS


class TempAccessorManagerCache(AccessorManagerCache):
    def make(self, user_accessors: Optional[Dict[str, Accessor]] = None) -> AccessorManager:
        return AccessorManager(
            DEFAULT_ACCESSORS,
            station=STATION_ACCESSORS,
            location=LOCATION_ACCESSORS,
            geometry=GEOMETRY_ACCESSORS,
            upper=DEFAULT_OBS_ACCESSORS,
            _extra=EXTRA_STATION_ACCESSORS,
            _station=STATION_ACCESSORS + EXTRA_STATION_ACCESSORS,
            user_accessors=user_accessors,
        )


MANAGER_CACHE = TempAccessorManagerCache()
MANAGER = MANAGER_CACHE.get()

UPPER_ACCESSORS: Dict[str, Accessor] = {
    "standard": MANAGER.get_by_object(PressureLevelAccessor),
    "extended": MANAGER.get_by_object(OffsetPressureLevelAccessor),
}


class TempReader(StationReader):
    def __init__(
        self,
        *args: Any,
        columns: Optional[Union[str, List[str]]] = "default",
        stnid_keys: Optional[Union[str, List[str]]] = None,
        bufr_filters: Optional[Dict[str, Any]] = None,
        geopotential: str = "z",
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.add_offsets = False

        if columns == []:
            columns = "default"
        self.params = columns

        self.manager = self.make_manager(MANAGER_CACHE, stnid_keys=stnid_keys)

        self.param_filters = {}
        self.accessors = self.manager.get(self.params)
        labels = self.manager.labels(self.accessors)

        for name in labels:
            for suffix in ("", "_units"):
                key = name + suffix
                if key in self.bufr_filters:
                    self.param_filters[key] = self.bufr_filters.pop(key)

        self.param_filters = ParamFilter(self.param_filters, period=False)

        # separate station and upper accessors
        self.station_accessors = []
        self.upper_accessors = []
        for name, ac in self.accessors.items():
            if name in self.manager.groups["_station"]:
                self.station_accessors.append(ac)
            else:
                self.upper_accessors.append(ac)

        # the concrete upper accessor is determined per message,
        # here wqe only need to know if they should be extracted
        self.upper_accessors = self.upper_accessors or None

        self.geopotential = geopotential
        self.geopot_handler = None
        if self.upper_accessors:
            self.geopot_handler = GeopotentialHandler(self.geopotential)

    def filter_header(self, message: Mapping[str, Any]) -> bool:
        return message["dataCategory"] == 2

    @staticmethod
    def get_upper_accessor(filtered_keys: List[Any]) -> Optional[Accessor]:
        def find_key(keys, name):
            for k in keys:
                if k.name == name:
                    return True
            return False

        if find_key(filtered_keys, "extendedVerticalSoundingSignificance"):
            return UPPER_ACCESSORS["extended"]
        elif find_key(filtered_keys, "verticalSoundingSignificance"):
            return UPPER_ACCESSORS["standard"]
        else:
            return None

    def read_message(
        self,
        message: Mapping[str, Any],
    ) -> Generator[Dict[str, Any], None, None]:
        filtered_keys = self.get_filtered_keys(message, self.accessors, self.param_filters)

        if self.upper_accessors:
            upper_accessor = self.get_upper_accessor(filtered_keys)
        else:
            upper_accessor = None

        reader = BufrSubsetReader(message, filtered_keys)

        for subset in reader.subsets():
            station = {}
            match = True
            for ac in self.station_accessors:
                r = ac.collect(subset)
                if self.param_filters.match(r):
                    station.update(r)
                else:
                    match = False
                    break

            if not match:
                continue

            if upper_accessor:
                r = upper_accessor.collect(
                    subset,
                    add_offsets=self.add_offsets,
                    units_converter=self.units_converter,
                    add_units=self.add_units,
                    # filters=self.filters,
                )

                if r:
                    for x in r:
                        if x:
                            x = self.geopot_handler(x)
                            if self.param_filters.match(x):
                                d = {**station, **x}
                                yield d
                else:
                    d = {**station}
                    yield d

            else:
                yield station

    def adjust_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.geopotential == "z":
            df.drop(columns=["zh", "zh_units"], inplace=True, errors="ignore")
        elif self.geopotential == "zh":
            df.drop(columns=["z", "z_units"], inplace=True, errors="ignore")

        return df


reader = TempReader
