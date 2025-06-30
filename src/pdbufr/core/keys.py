# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import attr  # type: ignore
import eccodes  # type: ignore

from pdbufr.core.filters import WIGOSId


def rank_from_key(key: str) -> int:
    rank_text, sep, _ = key.rpartition("#")
    if sep == "#":
        return int(rank_text[1:])
    else:
        return 0


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


@attr.attrs(auto_attribs=True)
class UncompressedBufrKey:
    current_rank: int
    ref_rank: int
    name: str

    @classmethod
    def from_key(cls, key: str) -> "UncompressedBufrKey":
        rank_text, sep, name = key.rpartition("#")
        try:
            if sep == "#":
                rank = int(rank_text[1:])
            else:
                rank = 0
        except Exception:
            rank = 0

        return cls(rank, 0, name)

    def update_rank(self, key: str) -> None:
        self.current_rank = rank_from_key(key)

    def adjust_ref_rank(self) -> None:
        self.ref_rank = self.current_rank

    @property
    def relative_key(self) -> str:
        if self.current_rank > 0:
            rel_rank = self.current_rank - self.ref_rank
            prefix = f"#{rel_rank}#"
        else:
            prefix = ""
        return prefix + self.name


IS_KEY_COORD = {"subsetNumber": True, "operator": False}


def datetime_from_bufr(
    observation: Dict[str, Any], prefix: str, datetime_keys: List[str]
) -> datetime.datetime:
    hours = observation.get(prefix + datetime_keys[3], 0)
    minutes = observation.get(prefix + datetime_keys[4], 0)
    seconds = observation.get(prefix + datetime_keys[5], 0.0)
    microseconds = int(seconds * 1_000_000) % 1_000_000
    datetime_list = [observation[prefix + k] for k in datetime_keys[:3]]
    datetime_list += [hours, minutes, int(seconds), microseconds]
    return datetime.datetime(*datetime_list)


def wmo_station_id_from_bufr(observation: Dict[str, Any], prefix: str, keys: List[str]) -> int:
    block_number = int(observation[prefix + keys[0]])
    station_number = int(observation[prefix + keys[1]])
    return block_number * 1000 + station_number


def wmo_station_position_from_bufr(observation: Dict[str, Any], prefix: str, keys: List[str]) -> List[float]:
    longitude = float(observation[prefix + keys[0]])  # easting (X)
    latitude = float(observation[prefix + keys[1]])  # northing (Y)
    heightOfStationGroundAboveMeanSeaLevel = float(observation.get(prefix + keys[2], 0.0))
    return [longitude, latitude, heightOfStationGroundAboveMeanSeaLevel]


def wigos_id_from_bufr(
    observation: Dict[str, Any], prefix: str, keys: List[str], check_valid=False
) -> Union[str, None]:
    try:
        wigos_series = observation.get(prefix + keys[0], "")
        wigos_issuer = observation.get(prefix + keys[1], "")
        wigos_issuer_number = observation.get(prefix + keys[2], "")
        wigos_local_name = observation.get(prefix + keys[3], "")
        wid = WIGOSId(wigos_series, wigos_issuer, wigos_issuer_number, wigos_local_name)
        if check_valid and not wid.is_valid():
            return None
        return wid.as_str()
    except Exception:
        pass

    return None


def CRS_from_bufr(observation: Dict[str, Any], prefix: str, keys: List[str]) -> Optional[str]:
    bufr_CRS = int(observation.get(prefix + keys[0], 0))
    CRS_choices = {
        0: "EPSG:4326",  # WGS84
        1: "EPSG:4258",  # ETRS89
        2: "EPSG:4269",  # NAD83
        3: "EPSG:4314",  # DHDN
        4: None,  # TODO: get ellipsoid axes from descriptors 001152 and 001153
        # and create an CRS using pyproj.crs.CRS.from_cf(...) (s.below)
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
        [
            "longitude",
            "latitude",
            "heightOfStationGroundAboveMeanSeaLevel",
        ],
        "geometry",  # WMO_station_position (predefined to geometry for geopandas)
        wmo_station_position_from_bufr,
    ),
    (
        [
            "wigosIdentifierSeries",
            "wigosIssuerOfIdentifier",
            "wigosIssueNumber",
            "wigosLocalIdentifierCharacter",
        ],
        "WIGOS_station_id",
        wigos_id_from_bufr,
    ),
    (
        [
            "coordinateReferenceSystem",
        ],
        "CRS",
        CRS_from_bufr,
    ),
]
