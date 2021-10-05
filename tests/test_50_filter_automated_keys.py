# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import typing as T
import math

import pdbufr

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
TEST_DATA_GEOPANDAS = os.path.join(
    SAMPLE_DATA_FOLDER,
    "Z__C_EDZW_20210516120400_bda01,synop_bufr_GER_999999_999999__MW_466.bin",
)
VERBOSE = False


# from pyproj import Geod
# from shapely.geometry import Point

# def distance(center, position):
#     g = Geod(ellps="WGS84")
#     az12, az21, dist = g.inv(position.x, position.y, center.x, center.y)
#     return dist


def distance(center: list, position: list) -> float:
    # Orthodrome - see https://en.wikipedia.org/wiki/Great_circle
    RadiusEarth = 6371000  # Average Radius of Earth in m
    lat1 = math.radians(center[0])
    lat2 = math.radians(position[0])
    lon1 = math.radians(center[1])
    lon2 = math.radians(position[1])
    return (
        math.acos(
            math.sin(lat1) * math.sin(lat2)
            + math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
        )
        * RadiusEarth
    )


def test_computed_keys_filter() -> None:
    center = [11.010754, 47.800864]  # Hohenpeißenberg
    radius = 100 * 1000  # 100 km
    columnsList = [
        (
            "WMO_station_id",
            "stationOrSiteName",
            "geometry",
            "CRS",
            "typicalDate",
            "typicalTime",
            "timeSignificance",
            "timePeriod",
            "windDirection",
            "windSpeed",
        ),
        (
            "WMO_station_id",
            "stationOrSiteName",
            "latitude",
            "longitude",
            "geometry",
            "CRS",
            "typicalDate",
            "typicalTime",
            "timeSignificance",
            "timePeriod",
            "windDirection",
            "windSpeed",
        ),
    ]
    filtersList = [
        dict(),
        dict(windDirection=float, windSpeed=float),
        dict(
            windDirection=float,
            windSpeed=float,
            geometry=lambda x: distance(center, x) < radius,
        ),
    ]
    results = []
    for cIndx, columns in enumerate(columnsList):
        for fIndx, filters in enumerate(filtersList):
            if VERBOSE:
                print(f"columns[{cIndx}]={columns}")
                print(f"filters[{fIndx}]={filters}")
            rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filters)
            if VERBOSE:
                print(rs)
            results.append(dict(cIndx=cIndx, fIndx=fIndx, rs=rs, len=len(rs)))
            if "geometry" in filters:
                for station in rs.to_records():
                    assert distance(center, station["geometry"]) < radius
                if VERBOSE:
                    print(f"Distance check (radius = {radius/1000} km) ok")

    if VERBOSE:
        print("Length Checks and DataFrame Checks")

    for indx, test in enumerate(results):
        if test["cIndx"] in [0, 1] and test["fIndx"] == 0:
            results[indx]["awaitedLength"] = 178
        elif test["cIndx"] in [0, 1] and test["fIndx"] == 1:
            results[indx]["awaitedLength"] = 175
        elif test["cIndx"] in [0, 1] and test["fIndx"] == 2:
            results[indx]["awaitedLength"] = 7

        try:
            assert test["len"] == test["awaitedLength"]
        except:
            print(f"assertion in {indx}: {test}")
            raise
        if VERBOSE:
            print(f"{test['cIndx']} {test['fIndx']} : Length Check ok ({test['len']})")

    if VERBOSE:
        print("all Checks ok")


