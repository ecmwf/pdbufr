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
from pdbufr.core.accessor import CoordAccessor
from pdbufr.core.accessor import DatetimeAccessor
from pdbufr.core.accessor import ElevationAccessor
from pdbufr.core.accessor import LatLonAccessor
from pdbufr.core.accessor import MultiAllAccessor
from pdbufr.core.accessor import MultiFirstAccessor
from pdbufr.core.accessor import SidAccessor
from pdbufr.core.accessor import SimpleAccessor
from pdbufr.core.accessor import StationNameAccessor
from pdbufr.core.filters import ParamFilter
from pdbufr.core.subset import BufrSubsetReader

from .custom import StationReader

LOG = logging.getLogger(__name__)


class T2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.T2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"airTemperatureAt2M": PARAMS.T2M}, fixed_coords=2),
        CoordAccessor(
            keys={"airTemperature": PARAMS.T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        ),
        CoordAccessor(
            keys={"airTemperature": PARAMS.T2M},
            coords=[("heightAboveStation", "level", True)],
        ),
    ]


class TWB2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.TWB2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"wetBulbTemperatureAt2M": PARAMS.TWB2M}, fixed_coords=2),
        CoordAccessor(
            keys={"wetBulbTemperature": PARAMS.TWB2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        ),
        CoordAccessor(
            keys={"wetBulbTemperature": PARAMS.TWB2M},
            coords=[("heightAboveStation", "level", True)],
        ),
    ]


class RHU2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.RH2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"relativeHumidityAt2M": PARAMS.RH2M}, fixed_coords=2),
        CoordAccessor(
            keys={"relativeHumidity": PARAMS.RH2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        ),
        CoordAccessor(
            keys={"relativeHumidity": PARAMS.RH2M},
            coords=[("heightAboveStation", "level", True)],
        ),
    ]


class Td2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.TD2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"dewpointTemperatureAt2M": PARAMS.TD2M}, fixed_coords=2),
        CoordAccessor(
            keys={"dewpointTemperature": PARAMS.TD2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        ),
        CoordAccessor(
            keys={"dewpointTemperature": PARAMS.TD2M},
            coords=[("heightAboveStation", "level", True)],
        ),
    ]


class Q2mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.Q2M
    accessors: List[Accessor] = [
        CoordAccessor(keys={"specificHumidityAt2M": PARAMS.Q2M}, fixed_coords=2),
        CoordAccessor(
            keys={"specificHumidity": PARAMS.Q2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        ),
        CoordAccessor(
            keys={"specificHumidity": PARAMS.Q2M},
            coords=[("heightAboveStation", "level", True)],
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
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        ),
        CoordAccessor(
            keys={"windSpeed": PARAMS.WIND10M_SPEED, "windDirection": PARAMS.WIND10M_DIR},
            coords=[("heightAboveStation", "level", True)],
        ),
    ]


class Wind10mSpeedAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WIND10M_SPEED
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"windSpeedAt10M": PARAMS.WIND10M_SPEED},
            fixed_coords=10,
        ),
        CoordAccessor(
            keys={"windSpeed": PARAMS.WIND10M_SPEED},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        ),
        CoordAccessor(
            keys={"windSpeed": PARAMS.WIND10M_SPEED},
            coords=[("heightAboveStation", "level", True)],
        ),
    ]


class Wind10mDirAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WIND10M_DIR
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"windDirectionAt10M": PARAMS.WIND10M_DIR},
            fixed_coords=10,
        ),
        CoordAccessor(
            keys={"windDirection": PARAMS.WIND10M_DIR},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        ),
        CoordAccessor(
            keys={"windDirection": PARAMS.WIND10M_DIR},
            coords=[("heightAboveStation", "level", True)],
        ),
    ]


class WindGustAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WGUST
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"maximumWindGustSpeed": PARAMS.WGUST_SPEED, "maximumWindGustDirection": PARAMS.WGUST_DIR},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            period="timePeriod",
            first=False,
        ),
        CoordAccessor(
            keys={"maximumWindGustSpeed": PARAMS.WGUST_SPEED, "maximumWindGustDirection": PARAMS.WGUST_DIR},
            coords=[("heightAboveStation", "level", True)],
            period="timePeriod",
            first=False,
        ),
    ]


class WindGustSpeedAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WGUST_SPEED
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"maximumWindGustSpeed": PARAMS.WGUST_SPEED},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            period="timePeriod",
            first=False,
        ),
        CoordAccessor(
            keys={"maximumWindGustSpeed": PARAMS.WGUST_SPEED},
            coords=[("heightAboveStation", "level", True)],
            period="timePeriod",
            first=False,
        ),
    ]


class WindGustDirAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WGUST_DIR
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"maximumWindGustDirection": PARAMS.WGUST_DIR},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            period="timePeriod",
            first=False,
        ),
        CoordAccessor(
            keys={"maximumWindGustDirection": PARAMS.WGUST_DIR},
            coords=[("heightAboveStation", "level", True)],
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


class MinTAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.MIN_T2M
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"minimumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MIN_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            period="timePeriod",
            first=False,
        ),
        CoordAccessor(
            keys={"minimumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MIN_T2M},
            coords=[("heightAboveStation", "level", True)],
            period="timePeriod",
            first=False,
        ),
        # SimpleAccessor(
        #     keys={"minimumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MIN_T2M},
        # ),
        CoordAccessor(
            keys={"minimumTemperatureAtHeightSpecifiedPast12Hours": PARAMS.MIN_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            fixed_period="12h",
        ),
        CoordAccessor(
            keys={"minimumTemperatureAtHeightSpecifiedPast12Hours": PARAMS.MIN_T2M},
            coords=[("heightAboveStation", "level", True)],
            fixed_period="12h",
        ),
        CoordAccessor(
            keys={"minimumTemperatureAtHeightSpecifiedPast24Hours": PARAMS.MIN_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            fixed_period="24h",
        ),
        CoordAccessor(
            keys={"minimumTemperatureAtHeightSpecifiedPast24Hours": PARAMS.MIN_T2M},
            coords=[("heightAboveStation", "level", True)],
            fixed_period="24h",
        ),
        CoordAccessor(
            keys={"minimumTemperatureAt2MPast12Hours": PARAMS.MIN_T2M},
            fixed_period="12h",
            fixed_coords=2,
            first=True,
        ),
        CoordAccessor(
            keys={"minimumTemperatureAt2MPast24Hours": PARAMS.MIN_T2M},
            fixed_period="24h",
            fixed_coords=2,
            first=True,
        ),
    ]


class MaxTAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.MAX_T2M
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            period="timePeriod",
            first=False,
        ),
        CoordAccessor(
            keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
            coords=[("heightAboveStation", "level", True)],
            period="timePeriod",
            first=False,
        ),
        CoordAccessor(
            keys={"maximumTemperatureAtHeightSpecifiedPast12Hours": PARAMS.MAX_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            fixed_period="12h",
        ),
        CoordAccessor(
            keys={"maximumTemperatureAtHeightSpecifiedPast12Hours": PARAMS.MAX_T2M},
            coords=[("heightAboveStation", "level", True)],
            fixed_period="12h",
        ),
        CoordAccessor(
            keys={"maximumTemperatureAtHeightSpecifiedPast24Hours": PARAMS.MAX_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
            fixed_period="24h",
        ),
        CoordAccessor(
            keys={"maximumTemperatureAtHeightSpecifiedPast24Hours": PARAMS.MAX_T2M},
            coords=[("heightAboveStation", "level", True)],
            fixed_period="24h",
        ),
        CoordAccessor(
            keys={"maximumTemperatureAt2MPast12Hours": PARAMS.MAX_T2M},
            fixed_period="12h",
            fixed_coords=2,
            first=True,
        ),
        CoordAccessor(
            keys={"maximumTemperatureAt2MPast24Hours": PARAMS.MAX_T2M},
            fixed_period="24h",
            fixed_coords=2,
            first=True,
        ),
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


class PressureAccessor(SimpleAccessor):
    param: PARAMS.Parameter = PARAMS.PRESSURE
    keys: Dict[str, PARAMS.Parameter] = {"nonCoordinatePressure": PARAMS.PRESSURE}


class PressureChangeAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.PRESSURE_CHANGE
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"3HourPressureChange": PARAMS.PRESSURE_CHANGE},
            fixed_period="3h",
            first=True,
        ),
        CoordAccessor(
            keys={"24HourPressureChange": PARAMS.PRESSURE_CHANGE},
            fixed_period="24h",
            first=True,
        ),
    ]


class LongWaveRadiationAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.LONG_WAVE_RADIATION
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"longWaveRadiationIntegratedOverPeriodSpecified": PARAMS.LONG_WAVE_RADIATION},
            period="timePeriod",
            first=False,
        ),
    ]


class ShortWaveRadiationAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.SHORT_WAVE_RADIATION
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"netRadiationIntegratedOverPeriodSpecified": PARAMS.NET_RADIATION},
            period="timePeriod",
            first=False,
        ),
    ]


class NetRadiationAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.NET_RADIATION
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"shortWaveRadiationIntegratedOverPeriodSpecified": PARAMS.SHORT_WAVE_RADIATION},
            period="timePeriod",
            first=False,
        ),
    ]


class GlobalSolarRadiationAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.GLOBAL_SOLAR_RADIATION
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"globalSolarRadiationIntegratedOverPeriodSpecified": PARAMS.GLOBAL_SOLAR_RADIATION},
            period="timePeriod",
            first=False,
        ),
    ]


class DiffuseSolarRadiationAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.DIFFUSE_SOLAR_RADIATION
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"diffuseSolarRadiationIntegratedOverPeriodSpecified": PARAMS.DIFFUSE_SOLAR_RADIATION},
            period="timePeriod",
            first=False,
        ),
    ]


class DirectSolarRadiationAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.DIRECT_SOLAR_RADIATION
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"directSolarRadiationIntegratedOverPeriodSpecified": PARAMS.DIRECT_SOLAR_RADIATION},
            period="timePeriod",
            first=False,
        ),
    ]


class TotalSunshineAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.TOTAL_SUNSHINE
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"totalSunshine": PARAMS.TOTAL_SUNSHINE},
            period="timePeriod",
            first=False,
        ),
    ]


LOCATION_ACCESSORS = (LatLonAccessor,)
GEOMETRY_ACCESSORS = (
    LatLonAccessor,
    ElevationAccessor,
)
STATION_ACCESSORS: tuple = (SidAccessor, LatLonAccessor, ElevationAccessor, DatetimeAccessor)
EXTRA_STATION_ACCESSORS = (StationNameAccessor,)

DEFAULT_OBS_ACCESSORS: tuple = (
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
    PressureAccessor,
    CloudCoverAccessor,
    SnowDepthAccessor,
    HorizontalVisibilityAccessor,
)
EXTRA_OBS_ACCESSORS: tuple = (
    PressureChangeAccessor,
    LongWaveRadiationAccessor,
    ShortWaveRadiationAccessor,
    NetRadiationAccessor,
    GlobalSolarRadiationAccessor,
    DiffuseSolarRadiationAccessor,
    DirectSolarRadiationAccessor,
    TotalSunshineAccessor,
    Wind10mSpeedAccessor,
    Wind10mDirAccessor,
    WindGustSpeedAccessor,
    WindGustDirAccessor,
)

DEFAULT_ACCESSORS = STATION_ACCESSORS + DEFAULT_OBS_ACCESSORS


class SynopAccessorManagerCache(AccessorManagerCache):
    def make(self, user_accessors: Optional[Dict[str, Accessor]] = None) -> AccessorManager:
        return AccessorManager(
            DEFAULT_ACCESSORS,
            station=STATION_ACCESSORS,
            location=LOCATION_ACCESSORS,
            geometry=GEOMETRY_ACCESSORS,
            _extra=EXTRA_STATION_ACCESSORS + EXTRA_OBS_ACCESSORS,
            user_accessors=user_accessors,
        )


MANAGER_CACHE = SynopAccessorManagerCache()
MANAGER = MANAGER_CACHE.get()


class SynopReader(StationReader):
    def __init__(
        self,
        *args: Any,
        columns: Optional[Union[str, List[str]]] = "default",
        level_columns: bool = False,
        stnid_keys: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        if columns == []:
            columns = "default"
        self.params = columns
        self.add_level = level_columns

        self.manager = self.make_manager(MANAGER_CACHE, stnid_keys=stnid_keys)

        self.param_filters = {}

        self.accessors = self.manager.get(self.params)

        for name in self.manager.accessors:
            for suffix in ("", "_level", "_units"):
                key = name + suffix
                if key in self.bufr_filters:
                    if name not in self.accessors:
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

        filtered_keys = self.get_filtered_keys(message, self.accessors, self.bufr_filters)
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
            for ac in self.accessors.values():
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
                    d = {}
                    break

            if d:
                yield d

        # print(f"d={d}")

    def reorder_columns(self, columns: List[str]) -> List[str]:
        """Reorder the columns according to the accessors."""
        r = []
        # LOG.debug(f"reorder_columns: columns={columns}")

        # We assume that all the column names start with the accessor name.
        # TODO: find a better solution to handle accessors like "latlon" where the column
        # names do not start with the accessor name
        for name in self.accessors:
            for i, c in enumerate(columns):
                if c is None:
                    continue
                if name == "latlon" and c in ("lat", "lon", "lat_units", "lon_units"):
                    r.append(c)
                    columns[i] = None
                elif c == name or c.startswith(name + "_"):
                    r.append(c)
                    columns[i] = None

        # LOG.debug(f" -> after accessors: columns={columns}")
        assert len(r) == len(columns), f"Expected {len(columns)} columns, got {len(r)}"
        # LOG.debug(f" -> r={r}")

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
            df = df.rename(columns=keys)

        col = self.reorder_columns(df.columns.tolist())
        df = df[col]
        return df


reader = SynopReader
