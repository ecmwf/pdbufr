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
from pdbufr.core.accessor import CoordAccessor
from pdbufr.core.accessor import DatetimeAccessor
from pdbufr.core.accessor import ElevationAccessor
from pdbufr.core.accessor import LatLonAccessor
from pdbufr.core.accessor import MultiAllAccessor
from pdbufr.core.accessor import MultiFirstAccessor
from pdbufr.core.accessor import SidAccessor
from pdbufr.core.accessor import SimpleAccessor
from pdbufr.core.subset import BufrSubsetReader

from ..bufr_structure import filter_keys_cached
from .custom import CustomReader


class T2mAccessor(MultiFirstAccessor):
    param = PARAMS.T2M
    accessors = [
        CoordAccessor(keys={"airTemperatureAt2M": PARAMS.T2M}, fixed_coords=2),
        CoordAccessor(
            keys={"airTemperature": PARAMS.T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class RHU2mAccessor(MultiFirstAccessor):
    param = PARAMS.RH2M
    accessors = [
        CoordAccessor(keys={"relativeHumidityAt2M": PARAMS.RH2M}, fixed_coords=2),
        CoordAccessor(
            keys={"relativeHumidity": PARAMS.RH2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class Td2mAccessor(MultiFirstAccessor):
    param = PARAMS.TD2M
    accessors = [
        CoordAccessor(keys={"dewpointTemperatureAt2M": PARAMS.TD2M}, fixed_coords=2),
        CoordAccessor(
            keys={"dewpointTemperature": PARAMS.TD2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class Wind10mAccessor(MultiFirstAccessor):
    param = PARAMS.WIND10
    accessors = [
        CoordAccessor(
            keys={"windSpeedAt10M": PARAMS.WSPEED10M, "windDirectionAt10M": PARAMS.WDIR10M}, fixed_coords=10
        ),
        CoordAccessor(
            keys={"windSpeed": PARAMS.WSPEED10M, "windDirection": PARAMS.WDIR10M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class WindGustAccessor(MultiFirstAccessor):
    param = PARAMS.WGUST
    accessors = [
        CoordAccessor(
            keys={"maximumWindGustSpeed": PARAMS.WSPEEDGUST, "maximumWindGustDirection": PARAMS.WDIRGUST},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            period="timePeriod",
        ),
    ]


class PresentWeatherAccessor(SimpleAccessor):
    param = PARAMS.PRESENT_WEATHER
    keys = {"presentWeather": PARAMS.PRESENT_WEATHER}


class PastWeatherAccessor(CoordAccessor):
    param = PARAMS.PAST_WEATHER
    keys = {"pastWeather1": PARAMS.PAST_WEATHER_1, "pastWeather2": PARAMS.PAST_WEATHER_2}

    def __init__(self, **kwargs):
        super().__init__(
            period="timePeriod",
            **kwargs,
        )


class TotalPrecipAccessor(MultiAllAccessor):
    param = PARAMS.PRECIPITATION
    accessors = [
        CoordAccessor(
            keys={"totalPrecipitationOrTotalWaterEquivalent": PARAMS.PRECIPITATION},
            coords=[
                ("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False),
            ],
            period="timePeriod",
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast1Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="1h",
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast3Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="3h",
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast6Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="6h",
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast12Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="12h",
        ),
        CoordAccessor(
            keys={"totalPrecipitationPast24Hours": PARAMS.PRECIPITATION},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            fixed_period="24h",
        ),
    ]


class MinTAccessor(MultiFirstAccessor):
    param = PARAMS.MIN_T2M
    accessors = [
        CoordAccessor(
            keys={"minimumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MIN_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            period="timePeriod",
        )
    ]


class MaxTAccessor(MultiFirstAccessor):
    param = PARAMS.MAX_T2M
    accessors = [
        CoordAccessor(
            keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
            period="timePeriod",
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


class MultiFilter:
    def __init__(self, filters):
        self.filters = filters or {}

    # def match(self, name, value):
    #     if name in self.filters:
    #         if self.filters[name].match(value):
    #             return True
    #         else:
    #             return False
    #     return True

    def match(self, data):
        for k, v in data.items():
            if k in self.filters:
                if not self.filters[k].match(v):
                    return False
        return True


class SynopReader(CustomReader):
    def match_category(self, message):
        c = message["dataCategory"]
        return c == 0 or c == 1

    # params: T.Union[T.Sequence[str], T.Any] = None,
    # filters: T.Mapping[str, T.Any] = {},

    def read_message(
        self,
        message: T.Mapping[str, T.Any],
        params=None,
        m2=None,
        m10=None,
        add_level=False,
        units_converter=None,
        add_units=False,
        filters=None,
    ):
        accessors = MANAGER.get(params)

        filters = MultiFilter(filters)
        keys_cache = {}

        included_keys = set()
        for _, p in accessors.items():
            included_keys |= set(p.needed_keys)

        included_keys.add("subsetNumber")

        # print("included_keys=", included_keys)

        filtered_keys = filter_keys_cached(message, keys_cache, included_keys)

        subsets = BufrSubsetReader(message, filtered_keys)
        # collector = Collector(message, filtered_keys, subsets)

        for collector in subsets.subsets():
            # keys, subset = s
            # collector.set_current_subset(subset)
            # collector = Collector(message, keys, subset)
            d = {}
            for ac in accessors.values():
                r = ac.collect(
                    collector,
                    add_coord=add_level,
                    units_converter=units_converter,
                    add_units=add_units,
                    filters=filters,
                )
                r_1 = {}
                if isinstance(r, list):
                    for rr in r:
                        r_1.update(rr)
                    r = r_1

                if filters.match(r):
                    d.update(r)
                else:
                    break

            if d:
                yield d

        # print(f"d={d}")


reader = SynopReader
