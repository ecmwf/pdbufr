# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
import typing as T

import pdbufr.core.param as PARAMS
from pdbufr.core.accessor import AccessorManager
from pdbufr.core.accessor import DatetimeAccessor
from pdbufr.core.accessor import ElevationAccessor
from pdbufr.core.accessor import LatLonAccessor
from pdbufr.core.accessor import SidAccessor
from pdbufr.core.accessor import SimpleAccessor
from pdbufr.core.param import Parameter
from pdbufr.core.subset import BufrSubsetReader

from .custom import CustomReader

LOG = logging.getLogger(__name__)


class PressureLevelAccessor(SimpleAccessor):
    keys = {
        "pressure": PARAMS.PRESSURE,
        "verticalSoundingSignificance": None,
        "nonCoordinateGeopotential": PARAMS.Z,
        "nonCoordinateGeopotentialHeight": PARAMS.ZH,
        "airTemperature": PARAMS.T,
        "dewpointTemperature": PARAMS.TD,
        "windDirection": PARAMS.WDIR,
        "windSpeed": PARAMS.WSPEED,
    }
    param = Parameter("plev", "pressure_level")

    def empty_result(self):
        return []

    def collect(
        self,
        collector,
        labels=None,
        ref_date=None,
        ref_lat=None,
        ref_lon=None,
        raise_on_missing=False,
        units_converter=None,
        add_units=False,
        **kwargs,
    ):
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
    keys = {
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
    param = Parameter("plev_offset", "pressure_level_with_offset")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time_offset = self.keys["timePeriod"]
        self.lat_offset = self.keys["latitudeDisplacement"]
        self.lon_offset = self.keys["longitudeDisplacement"]

    def parse_collected(self, value, skip, units_converter, add_units, raise_on_missing):
        if value is None:
            value = {}

        # if raise_on_missing and (not value or all(v is None for v in value.values())):
        #     raise ValueError(f"Missing value for {self.name}")
        res = {}
        for key, param in self.keys.items():
            # print(f"key={key} param={param}")
            if param is not None:
                label = param.label
                if param in skip:
                    continue

                v, units = value.get(key, (None, None))

                # convert units
                if v is not None and units_converter is not None and param.units:
                    print("units_converter", label, units, v, param.units)
                    v, units = units_converter.convert(label, v, units)

                # handle period
                if param.is_period():
                    v = param.to_timedelta(v, units)

                res[label] = v

                # add units column
                if add_units and param.units:
                    res[label + "_units"] = units

        return res

    def collect(
        self,
        collector,
        labels=None,
        ref_date=None,
        ref_lat=None,
        ref_lon=None,
        raise_on_missing=False,
        units_converter=None,
        add_units=False,
        add_offsets=True,
        **kwargs,
    ):
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


CORE_ACCESSORS = [SidAccessor, LatLonAccessor, ElevationAccessor, DatetimeAccessor]
USER_ACCESSORS = [PressureLevelAccessor, OffsetPressureLevelAccessor]
MANAGER = AccessorManager(CORE_ACCESSORS, USER_ACCESSORS)

STATION_ACCESSORS = [MANAGER.get_by_object(ac) for ac in CORE_ACCESSORS]
UPPER_ACCESSORS = {
    "standard": MANAGER.get_by_object(PressureLevelAccessor),
    "extended": MANAGER.get_by_object(OffsetPressureLevelAccessor),
}


class TempReader(CustomReader):
    def filter_header(self, message):
        return message["dataCategory"] == 2

    # params: T.Union[T.Sequence[str], T.Any] = None,
    # filters: T.Mapping[str, T.Any] = {},

    @staticmethod
    def get_upper_accessor(filtered_keys):
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
        message: T.Mapping[str, T.Any],
        params=None,
        units_converter=None,
        add_units=False,
        filters=None,
    ):
        # TODO: add param selection
        params = None

        accessors = MANAGER.get(params)

        filtered_keys = self.get_filtered_keys(message, accessors)

        upper_accessor = self.get_upper_accessor(filtered_keys)
        if upper_accessor is None:
            LOG.warning("No upper accessor found")
            return

        reader = BufrSubsetReader(message, filtered_keys)

        # raise ValueError("No upper accessor found")
        add_offsets = True
        for subset in reader.subsets():
            # first collect the station data. This will be included in each row
            station = {}
            for ac in STATION_ACCESSORS:
                r = ac.collect(subset, filters=filters)
                station.update(r)

            # now collect the upper data
            r = upper_accessor.collect(
                subset,
                add_offsets=add_offsets,
                units_converter=units_converter,
                add_units=add_units,
                filters=filters,
            )

            # each level is a separate row
            if r:
                for x in r:
                    d = {**station, **x}
                    if x:
                        yield d
            else:
                d = {**station}
                yield d


reader = TempReader
