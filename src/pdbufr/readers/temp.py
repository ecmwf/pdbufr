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
from typing import List
from typing import Mapping
from typing import Optional
from typing import Union

import pdbufr.core.param as PARAMS
from pdbufr.core.accessor import Accessor
from pdbufr.core.accessor import AccessorManager
from pdbufr.core.accessor import DatetimeAccessor
from pdbufr.core.accessor import ElevationAccessor
from pdbufr.core.accessor import LatLonAccessor
from pdbufr.core.accessor import SidAccessor
from pdbufr.core.accessor import SimpleAccessor
from pdbufr.core.param import Parameter
from pdbufr.core.subset import BufrSubsetReader
from pdbufr.utils.convert import period_to_timedelta
from pdbufr.utils.units import UnitsConverter

from .custom import CustomReader

LOG = logging.getLogger(__name__)


class PressureLevelAccessor(SimpleAccessor):
    keys: Dict[str, Optional[Parameter]] = {
        "pressure": PARAMS.PRESSURE,
        "verticalSoundingSignificance": None,
        "nonCoordinateGeopotential": PARAMS.Z,
        "nonCoordinateGeopotentialHeight": PARAMS.ZH,
        "airTemperature": PARAMS.T,
        "dewpointTemperature": PARAMS.TD,
        "windDirection": PARAMS.WDIR,
        "windSpeed": PARAMS.WSPEED,
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
        "windDirection": PARAMS.WDIR,
        "windSpeed": PARAMS.WSPEED,
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


CORE_ACCESSORS: tuple = (SidAccessor, LatLonAccessor, ElevationAccessor, DatetimeAccessor)
USER_ACCESSORS: tuple = (PressureLevelAccessor, OffsetPressureLevelAccessor)
MANAGER: AccessorManager = AccessorManager(CORE_ACCESSORS, USER_ACCESSORS)

STATION_ACCESSORS: List[Accessor] = [MANAGER.get_by_object(ac) for ac in CORE_ACCESSORS]
UPPER_ACCESSORS: Dict[str, Accessor] = {
    "standard": MANAGER.get_by_object(PressureLevelAccessor),
    "extended": MANAGER.get_by_object(OffsetPressureLevelAccessor),
}


class TempReader(CustomReader):
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
        params: Optional[Union[str, List[str]]] = None,
        units_converter: Optional[UnitsConverter] = None,
        add_units: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        params = None

        accessors = MANAGER.get(params)

        filtered_keys = self.get_filtered_keys(message, accessors)

        upper_accessor = self.get_upper_accessor(filtered_keys)
        if upper_accessor is None:
            LOG.warning("No upper accessor found")
            return

        reader = BufrSubsetReader(message, filtered_keys)

        add_offsets = True
        for subset in reader.subsets():
            station = {}
            for ac in STATION_ACCESSORS:
                r = ac.collect(subset, filters=filters)
                station.update(r)

            r = upper_accessor.collect(
                subset,
                add_offsets=add_offsets,
                units_converter=units_converter,
                add_units=add_units,
                filters=filters,
            )

            if r:
                for x in r:
                    d = {**station, **x}
                    if x:
                        yield d
            else:
                d = {**station}
                yield d


TempReader = TempReader
