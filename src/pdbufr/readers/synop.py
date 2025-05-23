# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# from typing import Slice
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
from pdbufr.core.accessor import CoordAccessor
from pdbufr.core.accessor import DatetimeAccessor
from pdbufr.core.accessor import ElevationAccessor
from pdbufr.core.accessor import LatLonAccessor
from pdbufr.core.accessor import MultiAllAccessor
from pdbufr.core.accessor import MultiFirstAccessor
from pdbufr.core.accessor import SidAccessor
from pdbufr.core.accessor import SimpleAccessor
from pdbufr.core.filters import ParamFilter
from pdbufr.core.subset import BufrSubsetReader

from .custom import CustomReader


class T2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.T2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"airTemperatureAt2M": PARAMS.T2M}, fixed_coords=2),
        CoordAccessor(
            keys={"airTemperature": PARAMS.T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class RHU2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.RH2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"relativeHumidityAt2M": PARAMS.RH2M}, fixed_coords=2),
        CoordAccessor(
            keys={"relativeHumidity": PARAMS.RH2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class Td2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.TD2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"dewpointTemperatureAt2M": PARAMS.TD2M}, fixed_coords=2),
        CoordAccessor(
            keys={"dewpointTemperature": PARAMS.TD2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class Q2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.Q2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"specificHumidityAt2M": PARAMS.Q2M}, fixed_coords=2),
        CoordAccessor(
            keys={"specificHumidity": PARAMS.Q2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class Wind10mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WIND10M
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"windSpeedAt10M": PARAMS.WIND10M_SPEED, "windDirectionAt10M": PARAMS.WIND10M_DIR},
            fixed_coords=10,
        ),
        CoordAccessor(
            keys={"windSpeed": PARAMS.WIND10M_SPEED, "windDirection": PARAMS.WIND10M_DIR},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class WindGustAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WGUST
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"maximumWindGustSpeed": PARAMS.WGUST_SPEED, "maximumWindGustDirection": PARAMS.WGUST_DIR},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            period="timePeriod",
            first=False,
        ),
    ]


class PresentWeatherAccessor(SimpleAccessor):
    param: PARAMS.Parameter = PARAMS.PRESENT_WEATHER
    keys: Dict[str, PARAMS.Parameter] = {"presentWeather": PARAMS.PRESENT_WEATHER}


class PastWeatherAccessor(CoordAccessor):
    param: PARAMS.Parameter = PARAMS.PAST_WEATHER
    keys: Dict[str, PARAMS.Parameter] = {
        "pastWeather1": PARAMS.PAST_WEATHER_1,
        "pastWeather2": PARAMS.PAST_WEATHER_2,
    }

    def __init__(self, **kwargs: Any):
        super().__init__(
            period="timePeriod",
            first=False,
            **kwargs,
        )


class TotalPrecipAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.PRECIPITATION
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"totalPrecipitationOrTotalWaterEquivalent": PARAMS.PRECIPITATION},
            coords=[
                ("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False),
            ],
            period="timePeriod",
            first=False,
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast1Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="1h",
            first=False,
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast3Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="3h",
            first=False,
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast6Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="6h",
            first=False,
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast12Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="12h",
            first=False,
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast24Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="24h",
            first=False,
        ),
    ]


class MinTAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.MIN_T2M
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"minimumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MIN_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            period="timePeriod",
            first=False,
        )
    ]


class MaxTAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.MAX_T2M
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            period="timePeriod",
            first=False,
        )
    ]


class MslpAccessor(SimpleAccessor):
    param: PARAMS.Parameter = PARAMS.MSLP
    keys: Dict[str, PARAMS.Parameter] = {"pressureReducedToMeanSeaLevel": PARAMS.MSLP}


class CloudCoverAccessor(SimpleAccessor):
    param: PARAMS.Parameter = PARAMS.CLOUD_COVER
    keys: Dict[str, PARAMS.Parameter] = {"cloudCoverTotal": PARAMS.CLOUD_COVER}


class SnowDepthAccessor(SimpleAccessor):
    param: PARAMS.Parameter = PARAMS.SNOW_DEPTH
    keys: Dict[str, PARAMS.Parameter] = {"totalSnowDepth": PARAMS.SNOW_DEPTH}


class HorizontalVisibilityAccessor(SimpleAccessor):
    param: PARAMS.Parameter = PARAMS.VISIBILITY
    keys: Dict[str, PARAMS.Parameter] = {"horizontalVisibility": PARAMS.VISIBILITY}


CORE_ACCESSORS: tuple = (SidAccessor, LatLonAccessor, ElevationAccessor, DatetimeAccessor)
STATION_ACCESSORS = CORE_ACCESSORS
LOCATION_ACCESSORS = (LatLonAccessor,)
GEOMETRY_ACCESSORS = (
    LatLonAccessor,
    ElevationAccessor,
)
USER_ACCESSORS: tuple = (
    T2mAccessor,
    RHU2mAccessor,
    Td2mAccessor,
    Wind10mAccessor,
    WindGustAccessor,
    PresentWeatherAccessor,
    PastWeatherAccessor,
    TotalPrecipAccessor,
    MinTAccessor,
    MaxTAccessor,
    MslpAccessor,
    CloudCoverAccessor,
    SnowDepthAccessor,
    HorizontalVisibilityAccessor,
)

MANAGER: AccessorManager = AccessorManager(
    core=CORE_ACCESSORS,
    station=CORE_ACCESSORS,
    location=LOCATION_ACCESSORS,
    geometry=GEOMETRY_ACCESSORS,
    optional=USER_ACCESSORS,
)


class SynopReader(CustomReader):
    def __init__(
        self,
        *args: Any,
        columns: Optional[Union[str, List[str]]] = "all",
        add_level_columns: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        if columns == []:
            columns = "all"
        self.params = columns
        self.add_level = add_level_columns

        self.param_filters = {}

        accessors = MANAGER.get(self.params)
        for name in MANAGER.accessors:
            for suffix in ("", "_level", "_units"):
                key = name + suffix
                if key in self.bufr_filters:
                    if name not in accessors:
                        raise ValueError(
                            f"Parameter={name} cannot be used in filters unless it is in columns"
                        )
                    self.param_filters[key] = self.bufr_filters.pop(key)
        self.param_filters = ParamFilter(self.param_filters, period=True)

    def filter_header(self, message: Mapping[str, Any]) -> bool:
        c = message["dataCategory"]
        return c == 0 or c == 1

    def read_message(
        self,
        message: Mapping[str, Any],
    ) -> Generator[Dict[str, Any], None, None]:
        accessors = MANAGER.get(self.params)

        filtered_keys = self.get_filtered_keys(message, accessors, self.bufr_filters)
        reader = BufrSubsetReader(message, filtered_keys)

        for subset in reader.subsets():
            d = {}

            # check generic filters first, this should be BUFR key filters
            if self.bufr_filters:
                r = subset.collect(
                    keys=list(self.bufr_filters.keys()),
                    filters=self.bufr_filters,
                )
                if not list(r):
                    continue

            # extract the parameters
            for ac in accessors.values():
                r = ac.collect(
                    subset,
                    add_coord=self.add_level,
                    units_converter=self.units_converter,
                    add_units=self.add_units,
                )
                r_1 = {}
                if isinstance(r, list):
                    for rr in r:
                        r_1.update(rr)
                    r = r_1

                if self.param_filters.match(r):
                    d.update(r)
                else:
                    break

            if d:
                yield d

        # print(f"d={d}")

    def reorder_columns(self, columns: List[str]) -> List[str]:
        r = []

        suffixes = ("_level", "_coord", "_units")
        moved = set()
        for c in columns:
            if c in moved:
                continue
            s = []
            for suffix in suffixes:
                name = c + suffix
                if name in columns:
                    s.append(name)
                    moved.add(name)
            r.append(c)
            if s:
                r.extend(s)
        return r

    def adjust_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = df.columns.tolist()
        from pdbufr.core.accessor import resolve_period_key

        keys = {}
        for c in columns:
            name = resolve_period_key(c)

            if name != c:
                keys[c] = name

        if keys:
            return df.rename(columns=keys)
        return df


reader = SynopReader
