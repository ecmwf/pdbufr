# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import collections
import datetime
import typing as T

import attr
import eccodes  # type: ignore
import numpy as np  # type: ignore

from . import bufr_filters


@attr.attrs(auto_attribs=True, frozen=True)
class BufrKey:
    level: int
    rank: int
    name: str

    @classmethod
    def from_level_key(cls, level: int, key: str) -> "BufrKey":
        rank_text, sep, name = key.rpartition("#")
        if sep == "#":
            rank = int(rank_text[1:])
        else:
            rank = 0
        return cls(level, rank, name)

    @property
    def key(self) -> str:
        if self.rank:
            prefix = f"#{self.rank}#"
        else:
            prefix = ""
        return prefix + self.name


IS_KEY_COORD = {"subsetNumber": True, "operator": False}


def message_structure(message: T.Mapping[str, T.Any]) -> T.Iterator[T.Tuple[int, str]]:
    level = 0
    coords: T.Dict[str, int] = collections.OrderedDict()
    for key in message:
        name = key.rpartition("#")[2]

        if name in IS_KEY_COORD:
            is_coord = IS_KEY_COORD[name]
        else:
            try:
                code = message[key + "->code"]
                is_coord = int(code[:3]) < 10
            except (KeyError, eccodes.KeyValueNotFoundError):
                is_coord = False

        while is_coord and name in coords:
            _, level = coords.popitem()  # OrderedDict.popitem uses LIFO order

        yield (level, key)

        if is_coord:
            coords[name] = level
            level += 1


def filter_keys(
    message: T.Mapping[str, T.Any], include: T.Container[str] = (),
) -> T.Iterator[BufrKey]:
    for level, key in message_structure(message):
        bufr_key = BufrKey.from_level_key(level, key)
        if include == () or bufr_key.name in include or bufr_key.key in include:
            yield bufr_key


def make_message_uid(message: T.Mapping[str, T.Any]) -> T.Tuple[T.Optional[int], ...]:
    message_uid: T.Tuple[T.Optional[int], ...]

    message_uid = (
        message["edition"],
        message["masterTableNumber"],
        message["numberOfSubsets"],
    )

    descriptors: T.Union[int, T.List[int]] = message["unexpandedDescriptors"]
    if isinstance(descriptors, int):
        message_uid += (descriptors, None)
    else:
        message_uid += tuple(descriptors) + (None,)

    try:
        delayed_descriptors = message["delayedDescriptorReplicationFactor"]
    except (KeyError, eccodes.KeyValueNotFoundError):
        delayed_descriptors = []

    if isinstance(delayed_descriptors, int):
        message_uid += (delayed_descriptors,)
    else:
        message_uid += tuple(delayed_descriptors)

    return message_uid


def filter_keys_cached(
    message: T.Mapping[str, T.Any],
    cache: T.Dict[T.Tuple[T.Hashable, ...], T.List[BufrKey]],
    include: T.Iterable[str] = (),
) -> T.List[BufrKey]:
    message_uid = make_message_uid(message)
    include_uid = tuple(sorted(include))
    filtered_message_uid: T.Tuple[T.Hashable, ...] = message_uid + include_uid
    if filtered_message_uid not in cache:
        cache[filtered_message_uid] = list(filter_keys(message, include_uid))
    return cache[filtered_message_uid]


def datetime_from_bufr(observation, prefix, datetime_keys):
    # type: (T.Dict[str, T.Any], str, T.List[str]) -> datetime.datetime
    hours = observation.get(prefix + datetime_keys[3], 0)
    minutes = observation.get(prefix + datetime_keys[4], 0)
    seconds = observation.get(prefix + datetime_keys[5], 0.0)
    microseconds = int(seconds * 1_000_000) % 1_000_000
    datetime_list = [observation[prefix + k] for k in datetime_keys[:3]]
    datetime_list += [hours, minutes, int(seconds), microseconds]
    return datetime.datetime(*datetime_list)


def wmo_station_id_from_bufr(observation, prefix, keys):
    # type: (T.Dict[str, T.Any], str, T.List[str]) -> int
    block_number = int(observation[prefix + keys[0]])
    station_number = int(observation[prefix + keys[1]])
    return block_number * 1000 + station_number


def wmo_station_position_from_bufr(observation, prefix, keys):
    # type: (T.Dict[str, T.Any], str, T.List[str]) -> T.List
    longitude = float(observation[prefix + keys[0]])  # easting (X)
    latitude = float(observation[prefix + keys[1]])  # northing (Y)
    heightOfStationGroundAboveMeanSeaLevel = float(
        observation.get(prefix + keys[2], 0.0)
    )
    return [longitude, latitude, heightOfStationGroundAboveMeanSeaLevel]


def CRS_from_bufr(observation, prefix, keys):
    # type: (T.Dict[str, T.Any], str, T.List[str]) -> str
    bufr_CRS = int(observation.get(prefix + keys[0], 0))
    CRS_choices = {
        0: "EPSG:4326",  # WGS84
        1: "EPSG:4258",  # ETRS89
        2: "EPSG:4269",  # NAD83
        3: "EPSG:4314",  # DHDN
        4: None,  # TODO: get ellipsoid axes from descriptors 001152 and 001153 and create an CRS using pyproj.crs.CRS.from_cf(...) (s.below)
        5: None,  # TODO: create an CRS using pyproj.crs.CRS.from_cf(...) (s. below)
        eccodes.CODES_MISSING_LONG: "EPSG:4326",  # WGS84
    }
    """
    Note to CRS:4
    -------------
    Ellipsoidal datum using the International Reference Meridian and the International
    Reference Pole as the prime meridian and prime pole, respectively, and the origin
    of the International Terrestrial Reference System (ITRS) (see Note 2). The
    International Reference Meridian, International Reference Pole and ITRS are
    maintained by the International Earth Rotation and Reference Systems
    Service (IERS)
    
    (2) When Code figure 4 is used to specify a custom coordinate reference system, the ellipsoidal
        datum shall be an oblate ellipsoid of revolution, where the major axis is uniplanar with the
        equatorial plane and the minor axis traverses the prime meridian towards the prime pole.
        North corresponds to the direction from the Equator to the prime pole. East corresponds to
        the counterclockwise direction from the prime meridian as viewed from above the North Pole.
        In this case, the semi-major and semi-minor axes must be specified (e.g. by descriptors
        0 01 152 and 0 01 153).

    Note to CRS:5
    -------------    
    Earth-centred, Earth-fixed (ECEF) coordinate system or Earth-centred rotational
    (ECR) system. This is a right-handed Cartesian coordinate system (X, Y, Z)
    rotating with the Earth. The origin is defined by the centre of mass of the Earth.
    (Footnote (5) of class 27 does not apply if ECEF coordinates are specified.)
    """
    return CRS_choices[bufr_CRS]


COMPUTED_KEYS = [
    (
        ["year", "month", "day", "hour", "minute", "second"],
        "data_datetime",
        datetime_from_bufr,
    ),
    (
        [
            "typicalYear",
            "typicalMonth",
            "typicalDay",
            "typicalHour",
            "typicalMinute",
            "typicalSecond",
        ],
        "typical_datetime",
        datetime_from_bufr,
    ),
    (["blockNumber", "stationNumber"], "WMO_station_id", wmo_station_id_from_bufr),
    (
        ["longitude", "latitude", "heightOfStationGroundAboveMeanSeaLevel",],
        "geometry",  # WMO_station_position (predefined to geometry for geopandas)
        wmo_station_position_from_bufr,
    ),
    (["coordinateReferenceSystem",], "CRS", CRS_from_bufr,),
]


def extract_observations(
    message: T.Mapping[str, T.Any],
    filtered_keys: T.List[BufrKey],
    filters: T.Dict[str, bufr_filters.BufrFilter] = {},
    base_observation: T.Dict[str, T.Any] = {},
) -> T.Iterator[T.Dict[str, T.Any]]:
    value_cache = {}
    try:
        is_compressed = bool(message["compressedData"])
    except (KeyError, eccodes.KeyValueNotFoundError):
        is_compressed = False
    if is_compressed:
        subset_count = message["numberOfSubsets"]
    else:
        subset_count = 1

    for subset in range(subset_count):
        current_observation: T.Dict[str, T.Any]
        current_observation = collections.OrderedDict(base_observation)
        current_levels: T.List[int] = [0]
        failed_match_level: T.Optional[int] = None
        for bufr_key in filtered_keys:
            level = bufr_key.level
            name = bufr_key.name

            if failed_match_level is not None and level > failed_match_level:
                continue

            # TODO: make into a function
            if all(name in current_observation for name in filters) and (
                level < current_levels[-1]
                or (level == current_levels[-1] and name in current_observation)
            ):
                # copy the content of current_items
                yield dict(current_observation)

            while len(current_observation) and (
                level < current_levels[-1]
                or (level == current_levels[-1] and name in current_observation)
            ):
                current_observation.popitem()  # OrderedDict.popitem uses LIFO order
                current_levels.pop()

            if bufr_key.key not in value_cache:
                value_cache[bufr_key.key] = message[bufr_key.key]
            value = value_cache[bufr_key.key]

            # unpack compressed BUFR values
            if isinstance(value, np.ndarray) and len(value) == subset_count:
                value = value[subset].item()

            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None

            if name in filters:
                if filters[name].match(value):
                    failed_match_level = None
                else:
                    failed_match_level = level
                    continue

            current_observation[name] = value
            current_levels.append(level)

        # yield the last observation
        if all(name in current_observation for name in filters):
            yield dict(current_observation)


def add_computed_keys(
    observation: T.Dict[str, T.Any],
    included_keys: T.Container[str],
    filters: T.Dict[str, bufr_filters.BufrFilter] = {},
) -> T.Dict[str, T.Any]:
    augmented_observation = observation.copy()
    for keys, computed_key, getter in COMPUTED_KEYS:
        if computed_key not in included_keys:
            continue
        computed_value = None
        try:
            computed_value = getter(observation, "", keys)
        except Exception:
            pass
        if computed_value:
            if computed_key in filters:
                if filters[computed_key].match(computed_value):
                    augmented_observation[computed_key] = computed_value
            else:
                augmented_observation[computed_key] = computed_value
    return augmented_observation


def stream_bufr(
    bufr_file: T.Iterable[T.MutableMapping[str, T.Any]],
    columns: T.Iterable[str],
    filters: T.Mapping[str, T.Any] = {},
    required_columns: T.Union[bool, T.Iterable[str]] = True,
    prefilter_headers: bool = False,
) -> T.Iterator[T.Dict[str, T.Any]]:
    """
    Iterate over selected observations from a eccodes.BurfFile.

    :param bufr_file: the eccodes.BurfFile object
    :param columns: a list of BUFR keys to return in the DataFrame for every observation
    :param filters: a dictionary of BUFR key / filter definition to filter the observations to return
    :param required_columns: the list of BUFR keys that are required for all observations.
        ``True`` means all ``columns`` are required (default ``True``)
    :param prefilter_headers: filter the header keys before unpacking the data section (default ``False``)
    """

    if isinstance(columns, str):
        columns = (columns,)

    if required_columns is True:
        required_columns = set(columns)
    elif required_columns is False:
        required_columns = set()
    elif isinstance(required_columns, T.Iterable):
        required_columns = set(required_columns)
    else:
        raise TypeError("required_columns must be a bool or an iterable")

    filters = dict(filters)

    value_filters = {k: bufr_filters.BufrFilter.from_user(filters[k]) for k in filters}
    included_keys = set(value_filters)
    included_keys |= set(columns)
    computed_keys = []
    for keys, computed_key, _ in COMPUTED_KEYS:
        if computed_key in included_keys:
            included_keys |= set(keys)
            computed_keys.append(computed_key)

    if "count" in value_filters:
        max_count = value_filters["count"].max()
    else:
        max_count = None

    keys_cache: T.Dict[T.Tuple[T.Hashable, ...], T.List[BufrKey]] = {}
    for count, message in enumerate(bufr_file, 1):
        if "count" in value_filters and not value_filters["count"].match(count):
            continue

        if prefilter_headers:
            # test header keys for failed matches before unpacking
            if not bufr_filters.is_match(
                message, value_filters, geopandas, required=False
            ):
                continue

        message["skipExtraKeyAttributes"] = 1
        message["unpack"] = 1

        filtered_keys = filter_keys_cached(message, keys_cache, included_keys)
        if "count" in included_keys:
            observation = {"count": count}
        else:
            observation = {}

        value_filters_without_computed = {
            k: v for k, v in value_filters.items() if not k in computed_keys
        }

        for observation in extract_observations(
            message, filtered_keys, value_filters_without_computed, observation,
        ):
            augmented_observation = add_computed_keys(
                observation, included_keys, value_filters
            )
            data = {k: v for k, v in augmented_observation.items() if k in columns}
            if required_columns.issubset(data):
                yield data

        # optimisation: skip decoding messages above max_count
        if max_count is not None and count >= max_count:
            break
