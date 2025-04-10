# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Mapping
from typing import Optional
from typing import Union

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


class Wind10mAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WIND10
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"windSpeedAt10M": PARAMS.WSPEED10M, "windDirectionAt10M": PARAMS.WDIR10M}, fixed_coords=10
        ),
        CoordAccessor(
            keys={"windSpeed": PARAMS.WSPEED10M, "windDirection": PARAMS.WDIR10M},
            coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        ),
    ]


class WindGustAccessor(MultiFirstAccessor):
    param: PARAMS.Parameter = PARAMS.WGUST
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"maximumWindGustSpeed": PARAMS.WSPEEDGUST, "maximumWindGustDirection": PARAMS.WDIRGUST},
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

MANAGER: AccessorManager = AccessorManager(CORE_ACCESSORS, USER_ACCESSORS)


class SynopReader(CustomReader):
    def filter_header(self, message: Mapping[str, Any]) -> bool:
        c = message["dataCategory"]
        return c == 0 or c == 1

    def read_message(
        self,
        message: Mapping[str, Any],
        params: Optional[Union[str, List[str]]] = None,
        m2: Optional[Any] = None,
        m10: Optional[Any] = None,
        add_level: bool = False,
        units_converter: Optional[Any] = None,
        add_units: bool = False,
        filters: Optional[Any] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], None, None]:
        accessors = MANAGER.get(params)

        filtered_keys = self.get_filtered_keys(message, accessors)

        reader = BufrSubsetReader(message, filtered_keys)

        for subset in reader.subsets():
            d = {}
            for ac in accessors.values():
                r = ac.collect(
                    subset,
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
