# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from typing import TYPE_CHECKING
from typing import List
from typing import Optional
from typing import Union

if TYPE_CHECKING:
    pass

PARAMETERS = {}


class Parameter:
    def __init__(
        self,
        name: str,
        desc: Optional[str] = None,
        label: Optional[Union[str, List[str]]] = None,
        units: Optional[Union[str, List[str]]] = None,
    ):
        self.name = name
        self.desc = desc or name
        self.label = label
        if label is None:
            self.label = name

        if not isinstance(label, list):
            label = [label]

        self.units = units

        # register
        PARAMETERS[name] = self

    def is_period(self) -> bool:
        return False

    def is_fixed(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"Parameter({self.name}, label={self.label}, units={self.units}"


class PeriodParameter(Parameter):
    def is_period(self) -> bool:
        return True

    def concat_units(self, v: Optional[Union[int, float]], units: str) -> Optional[str]:
        period = v
        if period is not None:
            period = str(-period)
            # units = value.get(key + "->units", "")
            period = period + units
            v = period
        return v


class CoordParameter(Parameter):
    def __init__(
        self,
        name: str,
        desc: Optional[str] = None,
        label: Optional[Union[str, List[str]]] = None,
        units: Optional[Union[str, List[str]]] = None,
        suffix: Optional[str] = None,
    ):
        super().__init__(name, desc, label, units)
        self.suffix = suffix


class FixedParameter(Parameter):
    def __init__(self, name: str, value: Union[int, float, str], **kwargs):
        super().__init__(name, **kwargs)
        self.value = value

    def is_fixed(self) -> bool:
        return True


class FixedCoordParameter(CoordParameter):
    def __init__(self, name: str, value: Union[int, float, str], **kwargs):
        super().__init__(name, **kwargs)
        self.value = value

    def is_fixed(self) -> bool:
        return True


# station related parameters
SID = Parameter("stnid", desc="station id")
TIME = Parameter("time", desc="datetime")
LATLON = Parameter("latlon", desc="latitude and longitude", units=["deg", "deg"])
LAT = Parameter("lat", desc="latitude", units="deg")
LON = Parameter("lon", desc="longitude", units="deg")
ELEVATION = Parameter("elevation", desc="elevation", units="m")
STATION_NAME = Parameter("station_name", desc="station name")

# time and location offsets for upper air data where each level can have its own time and location
TIME_OFFSET = PeriodParameter("time_offset", desc="datetime offset")
LAT_OFFSET = Parameter("lat_offset", desc="latitude offset", units="deg")
LON_OFFSET = Parameter("lon_offset", desc="latitude offset", units="deg")

# surface parameters
PERIOD = PeriodParameter("period", desc="period")
T2M = Parameter("t2m", desc="2m temperature", units="K")
TD2M = Parameter("td2m", desc="2m dewpoint temperature", units="K")
TWB2M = Parameter("twb2m", desc="2m wet bulb temperature", units="K")
RH2M = Parameter("rh2m", desc="2m relative humidity", units="%")
Q2M = Parameter("q2m", desc="2m specific humidity", units="kg/kg")
MSLP = Parameter("mslp", desc="mean sea level pressure", units="Pa")
WIND10M = Parameter("wind10m", desc="10m wind and direction", units=["m/s", "deg"])
WIND10M_SPEED = Parameter("wind10m_speed", desc="10m wind speed", units="m/s")
WIND10M_DIR = Parameter("wind10m_dir", desc="10m wind direction", units="deg")
WGUST = Parameter("max_wgust", desc="maximum wind gust", units=["m/s", "deg"])
WGUST_SPEED = Parameter("max_wgust_speed", desc="maximum wind gust speed", units="m/s")
WGUST_DIR = Parameter("max_wgust_dir", desc="maximum wind gust direction", units="deg")
VISIBILITY = Parameter("visibility", desc="visibility", units="m")
PRESENT_WEATHER = Parameter("present_weather", desc="present weather")
PAST_WEATHER_1 = Parameter("past_weather_1", desc="past weather")
PAST_WEATHER_2 = Parameter("past_weather_2", desc="past weather")
PAST_WEATHER = Parameter("past_weather", desc="past weather")
CLOUD_COVER = Parameter("cloud_cover", desc="total cloud cover", units="%")
MAX_T2M = Parameter("max_t2m", desc="max 2m temperature", units="K")
MIN_T2M = Parameter("min_t2m", desc="min 2m temperature", units="K")
PRECIPITATION = Parameter("precipitation", desc="precipitation", units="kg m-2")
SNOW_DEPTH = Parameter("snow_depth", desc="snow depth", units="m")
PRESSURE = Parameter("pressure", desc="pressure", units="Pa")
PRESSURE_CHANGE = Parameter("pressure_change", desc="pressure_change", units="Pa")
CHAR_PRESSURE_TENDENCY = Parameter("char_pressure_tendency", desc="characteristic of pressure tendency")
LONG_WAVE_RADIATION = Parameter("lw_radiation", desc="long wave radiation", units="J m-2")
SHORT_WAVE_RADIATION = Parameter("sw_radiation", desc="short wave radiation", units="J m-2")
NET_RADIATION = Parameter("net_radiation", desc="net radiation", units="J m-2")
GLOBAL_SOLAR_RADIATION = Parameter("global_solar_radiation", desc="global solar radiation", units="J m-2")
DIFFUSE_SOLAR_RADIATION = Parameter("diffuse_solar_radiation", desc="diffuse solar radiation", units="J m-2")
DIRECT_SOLAR_RADIATION = Parameter("direct_solar_radiation", desc="direct solar radiation", units="J m-2")
TOTAL_SUNSHINE = Parameter("total_sunshine", desc="total sunshine duration", units="min")

# upper air parameters
# PRESSURE = Parameter("pressure", desc="pressure", units="Pa")
T = Parameter("t", desc="temperature", units="K")
TD = Parameter("td", desc="dewpoint temperature", units="K")
RH = Parameter("rh", desc="relative humidity", units="%")
Q = Parameter("q", desc="specific humidity", units="kg/kg")
Z = Parameter("z", desc="geopotential", units="m2 s-2")
ZH = Parameter("zh", desc="geopotentialHeight", units="gpm")
WIND = Parameter("wind", desc="wind", units=["m/s", "deg"])
WIND_SPEED = Parameter("wind_speed", desc="wind speed", units="m/s")
WIND_DIR = Parameter("wind_dir", desc="wind direction", units="deg")


UNITS = {}
for item in PARAMETERS.values():
    if item.units is not None:
        u = item.units
        if u is not None:
            UNITS[item.name] = u
