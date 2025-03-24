# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import typing as T

import pdbufr.core.param as PARAMS
from pdbufr.core.accessor import AccessorManager
from pdbufr.core.accessor import DatetimeAccessor
from pdbufr.core.accessor import ElevationAccessor
from pdbufr.core.accessor import LatLonAccessor
from pdbufr.core.accessor import MultiTryAccessor
from pdbufr.core.accessor import SidAccessor
from pdbufr.core.accessor import SimpleAccessor
from pdbufr.core.accessor import ValueAtCoordAccessor
from pdbufr.core.accessor import ValueAtFixedCoordAccessor
from pdbufr.core.accessor import ValueInPeriodAccessor
from pdbufr.core.collector import Collector
from pdbufr.core.subset import BufrSubset

from ..bufr_structure import filter_keys_cached
from .custom import CustomReader


class T2mAccessor(MultiTryAccessor):
    param = PARAMS.T2M
    accessors = [
        ValueAtFixedCoordAccessor(keys={"airTemperatureAt2M": PARAMS.T2M}, fixed_coord=2),
        ValueAtCoordAccessor(
            keys={"airTemperature": PARAMS.T2M},
            coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
        ),
        ValueAtCoordAccessor(
            keys={"temperature": PARAMS.T2M}, coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform"
        ),
    ]


class RHU2mAccessor(MultiTryAccessor):
    param = PARAMS.RH2M
    accessors = [
        ValueAtFixedCoordAccessor(keys={"relativeHumidityAt2M": PARAMS.RH2M}, fixed_coord=2),
        ValueAtCoordAccessor(
            keys={"relativeHumidity": PARAMS.RH2M},
            coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
        ),
    ]


class Td2mAccessor(MultiTryAccessor):
    param = PARAMS.TD2M
    accessors = [
        ValueAtFixedCoordAccessor(keys={"dewpointTemperatureAt2M": PARAMS.TD2M}, fixed_coord=2),
        ValueAtCoordAccessor(
            keys={"dewpointTemperature": PARAMS.TD2M},
            coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
        ),
    ]


class Wind10mAccessor(MultiTryAccessor):
    param = PARAMS.WIND10
    accessors = [
        ValueAtFixedCoordAccessor(
            keys={"windSpeedAt10M": PARAMS.WSPEED10M, "windDirectionAt10M": PARAMS.WDIR10M}, fixed_coord=10
        ),
        ValueAtCoordAccessor(
            keys={"windSpeed": PARAMS.WSPEED10M, "windDirection": PARAMS.WDIR10M},
            coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
        ),
    ]


class WindGustAccessor(MultiTryAccessor):
    param = PARAMS.WGUST
    accessors = [
        ValueInPeriodAccessor(
            keys={"maximumWindGustSpeed": PARAMS.WSPEEDGUST, "maximumWindGustDirection": PARAMS.WDIRGUST},
            coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
            period_key="timePeriod",
        ),
    ]


class PresentWeatherAccessor(SimpleAccessor):
    param = PARAMS.PRESENT_WEATHER
    keys = {"presentWeather": PARAMS.PRESENT_WEATHER}


class PastWeatherAccessor(ValueInPeriodAccessor):
    param = PARAMS.PAST_WEATHER
    keys = {"pastWeather1": PARAMS.PAST_WEATHER_1, "pastWeather2": PARAMS.PAST_WEATHER_2}

    def __init__(self, **kwargs):
        super().__init__(
            period_key="timePeriod",
            **kwargs,
        )


class TotalPrecipAccessor(MultiTryAccessor):
    param = PARAMS.PRECIPITATION
    accessors = [
        ValueInPeriodAccessor(
            keys={"totalPrecipitationOrTotalWaterEquivalent": PARAMS.PRECIPITATION},
            coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
            period_key="timePeriod",
        )
    ]


class MinTAccessor(MultiTryAccessor):
    param = PARAMS.MIN_T2M
    accessors = [
        ValueInPeriodAccessor(
            keys={"minimumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MIN_T2M},
            coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
            period_key="timePeriod",
        )
    ]


class MaxTAccessor(MultiTryAccessor):
    param = PARAMS.MAX_T2M
    accessors = [
        ValueInPeriodAccessor(
            keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
            coord_key="heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
            period_key="timePeriod",
        )
    ]


class MslpAccessor(SimpleAccessor):
    param = PARAMS.MSLP
    keys = {"pressureReducedToMeanSeaLevel": PARAMS.MSLP}


class CloudCoverAccessor(SimpleAccessor):
    param = PARAMS.CLOUD_COVER
    keys = {"cloudCoverTotal": PARAMS.CLOUD_COVER}


class SnowDepthAccessor(SimpleAccessor):
    param = PARAMS.SNOW_DEPTH
    keys = {"totalSnowDepth": PARAMS.SNOW_DEPTH}


class HorizontalVisibilityAccessor(SimpleAccessor):
    param = PARAMS.VISIBILITY
    keys = {"horizontalVisibility": PARAMS.VISIBILITY}


CORE_ACCESSORS = [SidAccessor, LatLonAccessor, ElevationAccessor, DatetimeAccessor]
USER_ACCESSORS = [
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
]
MANAGER = AccessorManager(CORE_ACCESSORS, USER_ACCESSORS)


class SynopReader(CustomReader):
    def match_category(self, message):
        return message["dataCategory"] == 0

    # params: T.Union[T.Sequence[str], T.Any] = None,
    # filters: T.Mapping[str, T.Any] = {},

    def read_message(
        self,
        message: T.Mapping[str, T.Any],
        params=None,
        m2=None,
        m10=None,
        add_height=False,
        units_converter=None,
        add_units=False,
    ):
        accessors = MANAGER.get(params)

        keys_cache = {}

        included_keys = set()
        for _, p in accessors.items():
            included_keys |= set(p.needed_keys)

        print("included_keys=", included_keys)

        filtered_keys = filter_keys_cached(message, keys_cache, included_keys)

        subsets = BufrSubset(message, filtered_keys)

        for s in subsets.subsets():
            keys, subset = s
            collector = Collector(message, keys, subset)
            d = {}
            for ac in accessors.values():
                r = ac.collect(
                    collector,
                    add_height=add_height,
                    units_converter=units_converter,
                    add_units=add_units,
                )
                d.update(r)

            if d:
                yield d

        print(f"d={d}")


reader = SynopReader
