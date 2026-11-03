# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
from typing import Any, Dict, Generator, List, Mapping, Optional, Tuple, Union

import pandas as pd

import pdbufr.core.param as PARAMS
from pdbufr.core.accessor import (
    Accessor,
    AccessorManager,
    AccessorManagerCache,
    CoordAccessor,
    DatetimeAccessor,
    ElevationAccessor,
    LatLonAccessor,
    MultiAllAccessor,
    MultiFirstAccessor,
    SidAccessor,
    SimpleAccessor,
    StationNameAccessor,
)
from pdbufr.core.filters import ParamFilter
from pdbufr.core.subset import BufrSubsetCollector, BufrSubsetReader
from pdbufr.utils.exception import AllValueMissingException

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
    """Total cloud cover from ``cloudCoverTotal``.

    Unlike the other :class:`SimpleAccessor` columns, which disappear from the frame when the
    BUFR key is not in the file at all, this column is always emitted: a file without the key
    yields a column of None, just like the cloud summary columns
    (:class:`CloudSummaryAccessor.collect`) and like a file where the key is present but all
    its values are missing.
    """

    param: PARAMS.Parameter = PARAMS.CLOUD_COVER
    keys: Dict[str, PARAMS.Parameter] = {"cloudCoverTotal": PARAMS.CLOUD_COVER}

    def collect(self, collector: Any, add_units: bool = False, **kwargs: Any) -> Dict[str, Any]:
        res = super().collect(collector, add_units=add_units, **kwargs)
        if not res:
            # the message has no cloudCoverTotal key: keep the column, filled with None
            res = self.empty_result()
            if add_units and self.param.units:
                res[self.param.label + "_units"] = None
        return res


# BUFR keys of the cloud summary group (verticalSignificanceSurfaceObservations = 7,
# "low cloud" in WMO Code Table 0 08 002).
CLOUD_SUMMARY_KEYS = [
    "verticalSignificanceSurfaceObservations",
    "cloudAmount",
    "heightOfBaseOfCloud",
    "cloudType",
]


def _as_code(value: Any) -> Optional[int]:
    """Convert a cloud type value to an int code, keeping missing values as None."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


# The cloud summary group values extracted by :func:`_scan_cloud_summary`: the Nh cloud amount,
# the lowest cloud base, the list of up to 3 cloud type codes and the BUFR units of the cloud base.
CloudSummary = Tuple[Optional[Any], Optional[Any], List[Optional[int]], Optional[str]]


def _cloud_base_units(subset: BufrSubsetCollector, index: int) -> Optional[str]:
    """Return the BUFR units of the ``index``-th heightOfBaseOfCloud key of the subset.

    The units are looked up the same way as :meth:`BufrSubsetCollector.collect` does, from the
    ``<ranked key>->units`` attribute of the message. Returns None when the key or its units
    cannot be found.
    """
    for bufr_key in subset.filtered_keys:
        if bufr_key.name != "heightOfBaseOfCloud":
            continue
        if index == 0:
            units = subset.owner.message.get(bufr_key.key + "->units")
            return None if units is None else str(units)
        index -= 1
    return None


def _scan_cloud_summary(subset: BufrSubsetCollector) -> CloudSummary:
    """Extract the cloud summary group from a subset.

    The summary group is the cloud group with ``verticalSignificanceSurfaceObservations`` = 7
    ("low cloud" in WMO Code Table 0 08 002). Its ``cloudAmount`` is the cloud amount of the low
    cloud (Nh, or of the middle cloud when no low cloud is reported) as a raw code table 0 20 011
    value, its ``heightOfBaseOfCloud`` is the height of the base of the lowest cloud and its
    first three ``cloudType`` values are the cloud types of the low, middle and high clouds
    (CL, CM, CH) in that order. The group ends at the next ``verticalSignificanceSurfaceObservations``
    key, which starts the individual cloud layers.

    When the subset has no vertical significance = 7 group, the fallback uses the first cloud
    group, but only when its vertical significance is missing (e.g. template 307092) or 0 (WMO
    Code Table 0 08 002: in SYNOP reports 0 means that the group follows the SYNOP rules and
    describes the lowest cloud base and the cloud types). Groups with vertical significance 1-6
    are individual cloud layers and never fill the summary values.

    Missing values are returned as None. The units of the cloud base (the BUFR units of its
    ``heightOfBaseOfCloud`` key, normally "m") are captured together with it and are None when
    the cloud summary group has no heightOfBaseOfCloud key.

    The result is cached on the collector because all the cloud summary accessors need it.

    Returns
    -------
    tuple
        The (Nh cloud amount, lowest cloud base, list of up to 3 cloud type codes, cloud base
        units).
    """
    res = getattr(subset, "_cloud_summary", None)
    if res is not None:
        return res

    amount: Optional[Any] = None
    base: Optional[Any] = None
    types: List[Optional[int]] = []
    amount_seen = False
    base_seen = False
    base_index = 0
    base_idx: Optional[int] = None
    in_summary = False
    vs_seen = False
    first_vs: Optional[Any] = None

    for name, value in subset.iter_values():
        if name == "verticalSignificanceSurfaceObservations":
            if in_summary:
                break  # the individual cloud layers start here
            if not vs_seen:
                vs_seen = True
                first_vs = value
            in_summary = value == 7
            continue

        if name == "heightOfBaseOfCloud" and not in_summary:
            base_index += 1  # count the occurrence for the cloud base units lookup
            continue

        if not in_summary:
            continue

        if name == "cloudAmount" and not amount_seen:
            amount, amount_seen = value, True
        elif name == "heightOfBaseOfCloud" and not base_seen:
            base, base_seen, base_idx = value, True, base_index
        elif name == "cloudType" and len(types) < 3:
            types.append(value)
        else:
            break

    if not in_summary and (not vs_seen or first_vs is None or first_vs == 0):
        # no vertical significance = 7 group: the first cloud group is the summary when its
        # vertical significance is missing or 0, collect its keys up to the next group boundary
        past_marker = not vs_seen  # without significance keys the group starts at its first key
        base_index = 0  # the pass restarts at the beginning of the subset
        for name, value in subset.iter_values():
            if name == "verticalSignificanceSurfaceObservations":
                if past_marker:
                    break  # the next cloud group starts here
                past_marker = True
            elif name == "cloudAmount":
                if amount_seen:
                    break  # the next cloud group starts here without a significance key
                amount, amount_seen = value, True
            elif name == "heightOfBaseOfCloud":
                if not base_seen:
                    base, base_seen, base_idx = value, True, base_index
                base_index += 1
            elif name == "cloudType" and len(types) < 3:
                types.append(value)
            if amount_seen and base_seen and len(types) == 3:
                break

    base_units = _cloud_base_units(subset, base_idx) if base_idx is not None else None

    res = (amount, base, [_as_code(t) for t in types], base_units)
    setattr(subset, "_cloud_summary", res)
    return res


class CloudSummaryAccessor(Accessor):
    """Base class for the accessors extracting a column of the cloud summary group.

    The subclasses select one value of the group returned by :func:`_scan_cloud_summary`.
    The cloud amount and the cloud types are raw BUFR code table values (0 20 011 and 0 20 001)
    without units. The cloud base has the BUFR units of its key (metres): like the other
    parameters with units it supports the ``units_columns`` option and the unit conversion
    (``unit_system`` and ``units``).
    """

    needed_keys: List[str] = CLOUD_SUMMARY_KEYS
    param: PARAMS.Parameter

    def empty_result(self) -> Dict[str, Optional[Any]]:
        label: str = self.param.label
        return {label: None}

    def extract(self, summary: CloudSummary) -> Tuple[Any, Optional[str]]:
        """Select the value of the column and its units from the cloud summary group."""
        raise NotImplementedError

    def collect(
        self,
        collector: Any,
        raise_on_missing: bool = False,
        units_converter: Optional[Any] = None,
        add_units: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        value, units = self.extract(_scan_cloud_summary(collector))
        if value is None and raise_on_missing:
            raise AllValueMissingException(f"No value found for accessor={self.name}")
        label: str = self.param.label
        # convert the units exactly like SimpleAccessor.parse_collected does. Only the accessors
        # whose Parameter has units, i.e. not the code table columns, are ever converted.
        if value is not None and units is not None and units_converter is not None and self.param.units:
            value, units = units_converter.convert(label, value, units)
        res: Dict[str, Any] = {label: value}
        # add units column
        if add_units and self.param.units:
            res[label + "_units"] = units
        return res


class CloudTypeAccessor(CloudSummaryAccessor):
    """Base class for the low, middle and high cloud type accessors.

    The cloud types are assigned to the columns positionally, in the order they are reported
    in the cloud summary group (CL, CM, CH). They are raw code table 0 20 001 values without
    units.
    """

    cloud_type_index: int = 0

    def extract(self, summary: CloudSummary) -> Tuple[Any, Optional[str]]:
        types = summary[2]
        value = types[self.cloud_type_index] if self.cloud_type_index < len(types) else None
        return value, None


class CloudTypeLowAccessor(CloudTypeAccessor):
    param: PARAMS.Parameter = PARAMS.CLOUD_TYPE_LOW
    cloud_type_index = 0


class CloudTypeMiddleAccessor(CloudTypeAccessor):
    param: PARAMS.Parameter = PARAMS.CLOUD_TYPE_MIDDLE
    cloud_type_index = 1


class CloudTypeHighAccessor(CloudTypeAccessor):
    param: PARAMS.Parameter = PARAMS.CLOUD_TYPE_HIGH
    cloud_type_index = 2


class CloudAmountNhAccessor(CloudSummaryAccessor):
    """The cloud amount of the low cloud (Nh) of the cloud summary group. It is a raw code
    table 0 20 011 value without units.
    """

    param: PARAMS.Parameter = PARAMS.CLOUD_AMOUNT_NH

    def extract(self, summary: CloudSummary) -> Tuple[Any, Optional[str]]:
        return summary[0], None


class CloudBaseLowestAccessor(CloudSummaryAccessor):
    """The height of the base of the lowest cloud, with the BUFR units of the
    ``heightOfBaseOfCloud`` key (metres), supporting units columns and unit conversion.
    """

    param: PARAMS.Parameter = PARAMS.CLOUD_BASE_LOWEST

    def extract(self, summary: CloudSummary) -> Tuple[Any, Optional[str]]:
        return summary[1], summary[3]


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


class NetRadiationAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.NET_RADIATION
    accessors: List[Accessor] = [
        CoordAccessor(
            keys={"netRadiationIntegratedOverPeriodSpecified": PARAMS.NET_RADIATION},
            period="timePeriod",
            first=False,
        ),
    ]


class ShortWaveRadiationAccessor(MultiAllAccessor):
    param: PARAMS.Parameter = PARAMS.SHORT_WAVE_RADIATION
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
    CloudTypeLowAccessor,
    CloudTypeMiddleAccessor,
    CloudTypeHighAccessor,
    CloudAmountNhAccessor,
    CloudBaseLowestAccessor,
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
                        raise ValueError(f"Parameter={name} cannot be used in filters unless it is in columns")
                    self.param_filters[key] = self.bufr_filters.pop(key)
        self.param_filters = ParamFilter(self.param_filters, period=True)

    def filter_header(self, message: Mapping[str, Any]) -> bool:
        c = message["dataCategory"]
        return c == 0 or c == 1

    def read_message(
        self,
        message: Mapping[str, Any],
        bufr_filters: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:

        bufr_filters = bufr_filters or {}
        filtered_keys = self.get_filtered_keys(message, self.accessors, bufr_filters)
        reader = BufrSubsetReader(message, filtered_keys)

        for subset in reader.subsets():
            d = {}

            # check generic filters first, this should be BUFR key filters
            if bufr_filters:
                r = subset.collect(
                    keys=list(bufr_filters.keys()),
                    filters=bufr_filters,
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
        # TODO: make it less rigid
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
