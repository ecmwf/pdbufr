# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import typing as T

import pdbufr.bufr_types.param as PARAMS
from pdbufr.bufr_structure import filter_keys_cached
from pdbufr.utils.convert import period_to_timedelta

from ..bufr_types.accessor import Accessor
from ..bufr_types.accessor import AccessorManager
from ..bufr_types.accessor import DatetimeAccessor
from ..bufr_types.accessor import ElevationAccessor
from ..bufr_types.accessor import LatLonAccessor
from ..bufr_types.accessor import SidAccessor
from ..bufr_types.collector import Collector
from ..bufr_types.subset import BufrSubset
from .custom import CustomReader


class PressureLevelAccessor(Accessor):
    # labels = [
    #     "p",
    #     "z",
    #     "zh",
    #     "t",
    #     "td",
    #     "wdir",
    #     "wspeed",
    # ]

    def __init__(self, ref_date=None, ref_lat=None, ref_lon=None, **kwargs):
        super().__init__(**kwargs)
        self.keys = {
            "pressure": PARAMS.PRESSURE,
            "verticalSoundingSignificance": None,
            "nonCoordinateGeopotential": PARAMS.Z,
            "nonCoordinateGeopotentialHeight": PARAMS.ZH,
            "airTemperature": PARAMS.T,
            "dewpointTemperature": PARAMS.TD,
            "windDirection": PARAMS.WDIR,
            "windSpeed": PARAMS.WSPEED,
        }

    @property
    def needed_keys(self):
        return list(self.keys.keys())

    def empty_result(self):
        return []

    def collect(self, collector, labels=None, ref_date=None, ref_lat=None, ref_lon=None, **kwargs):
        keys = list(self.keys.keys())
        # labels = list(self.keys.values())
        # if labels is None:
        #     labels = self.labels

        r = []
        # print("collect keys=", keys)
        for v in collector.collect(keys, {}, mandatory_keys=["pressure", "verticalSoundingSignificance"]):
            # print("collect v=", v)
            obs = {}
            for k, p in self.keys.items():
                if p is not None:
                    obs[p.name] = v.get(k, None)

            # for label, key in zip(labels, self.keys):
            #     if label is not None:
            #         obs[label] = v.get(key, None)
            r.append(obs)
        return r


class OffsetPressureLevelAccessor(PressureLevelAccessor):
    labels = [
        "time_offset",
        "p",
        "z",
        "zh",
        "t",
        "td",
        "wdir",
        "wspeed",
        "lat_offset",
        "lon_offset",
    ]

    def __init__(self, ref_date=None, ref_lat=None, ref_lon=None, **kwargs):
        super().__init__(**kwargs)
        # self.keys = [
        #     "timePeriod",
        #     "pressure",
        #     "nonCoordinateGeopotential",
        #     "nonCoordinateGeopotentialHeight",
        #     "airTemperature",
        #     "dewpointTemperature",
        #     "windDirection",
        #     "windSpeed",
        #     "latitudeDisplacement",
        #     "longitudeDisplacement",
        # ]

        self.keys = {
            "timePeriod": "time_offset",
            "extendedVerticalSoundingSignificance": None,
            "pressure": "p",
            "nonCoordinateGeopotential": "z",
            "nonCoordinateGeopotentialHeight": "zh",
            "airTemperature": "t",
            "dewpointTemperature": "td",
            "windDirection": "wdir",
            "windSpeed": "wspeed",
            "latitudeDisplacement": "lat_offset",
            "longitudeDisplacement": "lon_offset",
        }

        self.period_key = "timePeriod"
        # self.latlon_delta_keys = ["latitudeDisplacement", "longitudeDisplacement"]
        # self.offset_keys = self.period_key + self.delta

    # @property
    # def needed_keys(self):
    #     return self.keys

    def empty_result(self):
        return []

    def compute_level_date(self, level_data):
        if level_data is None:
            return None

        period = level_data.get(self.period_key, None)
        if period is not None:
            period = str(period)
            units = level_data.get(self.period_key + "->units", "")
            delta = period_to_timedelta(period, units)
            # if delta is not None:
            #     ref_date + delta
            return delta

    # def compute_level_latlon(self, ref_lat, ref_lon, level_data):
    #     if ref_lat is None or ref_lon is None or level_data is None:
    #         return None, None

    #     delta_lat = level_data.get("latitudeDisplacement", None)
    #     delta_lon = level_data.get("longitudeDisplacement", None)
    #     return delta_lat, delta_lon
    #     # if delta_lat is not None and delta_lon is not None:
    #     #     return (ref_lat + delta_lat, ref_lon + delta_lon)

    def collect(self, collector, labels=None, add_offsets=True, **kwargs):
        keys = list(self.keys.keys())
        if labels is None:
            labels = list(self.keys.values())

        r = []
        # filters = {"extendedVerticalSoundingSignificance": 0}
        # !=16384
        obs = {}
        print("collect keys=", keys)
        for v in collector.collect(
            keys,
            {},
            mandatory_keys=["extendedVerticalSoundingSignificance", "pressure"],
            units_keys=[self.period_key],
        ):
            print("collect v=", v)
            obs = {}

            date = self.compute_level_date(v)
            # latlon = self.compute_level_latlon(ref_lat, ref_lon, v)

            for label, key in zip(labels, self.keys):
                if label is not None:
                    obs[label] = v.get(key, None)

            if add_offsets:
                obs["time_offset"] = date
            else:
                obs.pop("time_offset", None)
                obs.pop("lat_offset", None)
                obs.pop("lon_offset", None)

            # obs["lat_offset"] = date
            # obs["lon_offset"] = date

            r.append(obs)
            print("  - >obs=", obs)

        return r


ACCESSORS = {
    "sid": SidAccessor,
    "latlon": LatLonAccessor,
    "elevation": ElevationAccessor,
    "time": DatetimeAccessor,
    "plev": PressureLevelAccessor,
    "plev_offset": OffsetPressureLevelAccessor,
}

STATION_PARAMS = ["sid", "latlon", "elevation", "time"]
UPPER_PARAMS = ["plev", "plev_offset"]


STATION_ACCESSORS = {k: ACCESSORS[k]() for k in STATION_PARAMS}
UPPER_ACCESSORS = {"standard": ACCESSORS["plev"](), "extended": ACCESSORS["plev_offset"]()}
DEFAULT_ACCESSORS = {**STATION_ACCESSORS, **UPPER_ACCESSORS}

MANAGER = AccessorManager(ACCESSORS, DEFAULT_ACCESSORS, {})


def find_key(keys, name):
    for k in keys:
        if k.name == name:
            return True
    return False


# def get_temp_station(message: T.Mapping[str, T.Any], included_keys, add_offsets=True):

#     keys_cache = {}

#     filtered_keys = filter_keys_cached(message, keys_cache, included_keys)

#     if find_key(filtered_keys, "extendedVerticalSoundingSignificance"):
#         upper_accessor = UPPER_ACCESSORS["extended"]
#     elif find_key(filtered_keys, "verticalSoundingSignificance"):
#         upper_accessor = UPPER_ACCESSORS["standard"]
#     else:
#         return None

#     # print("filtered_keys")
#     # for f in filtered_keys:
#     #     print(" ", f)

#     subsets = BufrSubset(message, filtered_keys)

#     for s in subsets.subsets():
#         keys, subset = s
#         collector = Collector(message, keys, subset)

#         station = {}
#         for ac in STATION_ACCESSORS.values():
#             r = ac.collect(collector)
#             station.update(r)

#         r = upper_accessor.collect(collector, add_offsets=add_offsets)
#         if r:
#             for x in r:
#                 obs = {**station, **x}
#                 if x:
#                     yield obs
#         else:
#             obs = {**station}
#             yield obs


# def stream_bufr_temp(
#     bufr_file: T.Iterable[T.MutableMapping[str, T.Any]], filters: T.Mapping[str, T.Any] = {}, offsets=True
# ):

#     value_filters = {}

#     # prepare count filter
#     if "count" in value_filters:
#         max_count = value_filters["count"].max()
#     else:
#         max_count = None

#     count_filter = value_filters.pop("count", None)

#     # if offsets:
#     #     upper_accessor = UPPER_ACCESSORS["plev_offset"]
#     # else:
#     #     upper_accessor = UPPER_ACCESSORS["plev"]

#     included_keys = set()
#     for _, p in DEFAULT_ACCESSORS.items():
#         print("labels=", p.labels, "p.needed_keys=", p.needed_keys)
#         included_keys |= set(p.needed_keys)

#     for count, msg in enumerate(bufr_file, 1):
#         # we use a context manager to automatically delete the handle of the BufrMessage.
#         # We have to use a wrapper object here because a message can also be a dict
#         with MessageWrapper.wrap(msg) as message:

#             # count filter
#             if count_filter is not None and not count_filter.match(count):
#                 continue

#             if message["dataCategory"] != 2:
#                 continue

#             # message["skipExtraKeyAttributes"] = 1
#             message["unpack"] = 1

#             for obs in get_temp_station(message, included_keys, add_offsets=offsets):
#                 yield obs


class TempReader(CustomReader):
    def match_category(self, message):
        return message["dataCategory"] == 2

    # params: T.Union[T.Sequence[str], T.Any] = None,
    # filters: T.Mapping[str, T.Any] = {},

    def read_message(self, message: T.Mapping[str, T.Any], params=None, m2=None, m10=None):
        accessors = MANAGER.get(params)

        keys_cache = {}

        included_keys = set()
        for _, p in accessors.items():
            included_keys |= set(p.needed_keys)

        print("included_keys=", included_keys)

        filtered_keys = filter_keys_cached(message, keys_cache, included_keys)

        if find_key(filtered_keys, "extendedVerticalSoundingSignificance"):
            upper_accessor = UPPER_ACCESSORS["extended"]
        elif find_key(filtered_keys, "verticalSoundingSignificance"):
            upper_accessor = UPPER_ACCESSORS["standard"]
        else:
            return None

        subsets = BufrSubset(message, filtered_keys)

        add_offsets = True
        for s in subsets.subsets():
            keys, subset = s
            collector = Collector(message, keys, subset)

            station = {}
            for ac in STATION_ACCESSORS.values():
                r = ac.collect(collector)
                station.update(r)

            r = upper_accessor.collect(collector, add_offsets=add_offsets)
            if r:
                for x in r:
                    obs = {**station, **x}
                    if x:
                        yield obs
            else:
                obs = {**station}
                yield obs


reader = TempReader
