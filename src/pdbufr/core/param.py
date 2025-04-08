# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


PARAMETERS = {}


class Parameter:
    def __init__(self, name, desc=None, label=None, units=None):
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

    def is_period(self):
        return False

    def is_fixed(self):
        return False

    def __repr__(self):
        return f"Parameter({self.name}, label={self.label}, units={self.units}"

    # def check_units(self, value, units, target_units):
    #     if self.units is None:
    #         return value

    #     target_u = target_units.get(units, units)
    #     if target_u == units:
    #         return value

    #     from pint import UnitRegistry

    #     ureg = UnitRegistry()
    #     Q_ = ureg.Quantity
    #     pv = Q_(value, PINT_UNITS.get(units, units))
    #     return pv.to(PINT_UNITS.get(target_u, target_u)).magnitude


class PeriodParameter(Parameter):
    def __init__(self, name, bufr_key, desc=None, label=None, units=None):
        super().__init__(name, desc, label, units)
        self.bufr_key = bufr_key

    def is_period(self):
        return True


class CoordParameter(Parameter):
    def __init__(self, name, desc=None, label=None, units=None, suffix=None):
        super().__init__(name, desc, label, units)
        self.suffix = suffix


class FixedParameter(Parameter):
    def __init__(self, name, value, desc=None, label=None, units=None):
        super().__init__(name, desc, label, units)
        self.value = value

    def is_fixed(self):
        return True


# station related parameters
SID = Parameter("sid", desc="station id")
TIME = Parameter("time", desc="datetime")
LATLON = Parameter("latlon", desc="latitude and longitude", units=["deg", "deg"])
LAT = Parameter("lat", desc="latitude", units="deg")
LON = Parameter("lon", desc="longitude", units="deg")
ELEVATION = Parameter("elevation", desc="elevation", units="m")

# time and location offsets for upper air data where each level can have its own time and location
TIME_OFFSET = Parameter("time_offset", desc="datetime offset")
LAT_OFFSET = Parameter("lat_offset", desc="latitude offset", units="deg")
LON_OFFSET = Parameter("lon_offset", desc="latitude offset", units="deg")

# surface parameters
PERIOD = Parameter("period", desc="period")
T2M = Parameter("t2m", desc="2m temperature", units="K")
TD2M = Parameter("td2m", desc="2m dewpoint temperature", units="K")
RH2M = Parameter("rh2m", desc="2m relative humidity", units="%")
Q2M = Parameter("q2m", desc="2m specific humidity", units="kg/kg")
MSLP = Parameter("mslp", desc="mean sea level pressure", units="Pa")
WIND10 = Parameter("wind10", desc="10m wind and direction", units=["m/s", "deg"])
WSPEED10M = Parameter("wspeed10m", desc="10m wind speed", units="m/s")
WDIR10M = Parameter("wdir10m", desc="10m wind direction", units="deg")
WGUST = Parameter("wgust", desc="maximum wind gust", units=["m/s", "deg"])
WSPEEDGUST = Parameter("wspeedgust", desc="maximum wind gust speed", units="m/s")
WDIRGUST = Parameter("wdirgust", desc="maximum wind gust direction", units="deg")
VISIBILITY = Parameter("visibility", desc="visibility", units="m")
PRESENT_WEATHER = Parameter("present_weather", desc="present weather")
PAST_WEATHER_1 = Parameter("past_weather_1", desc="past weather")
PAST_WEATHER_2 = Parameter("past_weather_2", desc="past weather")
PAST_WEATHER = Parameter("past_weather", desc="past weather")
CLOUD_COVER = Parameter("cloud_cover", desc="total cloud cover", units="%")
MAX_T2M = Parameter("max_t2m", desc="max 2m temperature", units="K")
MIN_T2M = Parameter("min_t2m", desc="min 2m temperature", units="K")
PRECIPITATION = Parameter("precipitation", desc="precipitation", units="m")
PRECIPITATION_24h = Parameter("precipitation_24h", desc="precipitation", units="m")
SNOW_DEPTH = Parameter("snow_depth", desc="snow depth", units="m")


# upper air parameters
PRESSURE = Parameter("pressure", desc="pressure", units="Pa")
T = Parameter("t", desc="temperature", units="K")
TD = Parameter("td", desc="dewpoint temperature", units="K")
RH = Parameter("rh", desc="relative humidity", units="%")
Q = Parameter("q", desc="specific humidity", units="kg/kg")
P = Parameter("p", desc="pressure", units="Pa")
Z = Parameter("z", desc="geopotential", units="m2/s2")
ZH = Parameter("zh", desc="geopotentialHeight", units="gpm")
WIND = Parameter("wind", desc="wind", units=["m/s", "deg"])
WSPEED = Parameter("wspeed", desc="wind speed", units="m/s")
WDIR = Parameter("wdir", desc="wind direction", units="deg")
