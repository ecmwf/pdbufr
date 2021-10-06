# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import math
import os
import typing as T

import pytest

import pdbufr

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
TEST_DATA_GEOPANDAS = os.path.join(
    SAMPLE_DATA_FOLDER,
    "Z__C_EDZW_20210516120400_bda01,synop_bufr_GER_999999_999999__MW_466.bufr",
)


def distance(center: T.List[float], position: T.List[float]) -> float:
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


def test_computedKeys_Filter_with_latlon() -> None:
    center = [11.010754, 47.800864]  # Hohenpeißenberg
    radius = 100 * 1000  # 100 km
    columns = (
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
    )

    filter_wind = dict(windDirection=float, windSpeed=float)
    filter_wind_geometry = dict(
        windDirection=float,
        windSpeed=float,
        geometry=lambda x: distance(center, x) < radius,
    )

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns)
    assert isinstance(rs, pd.DataFrame)
    assert len(rs) == 178

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert isinstance(rs, pd.DataFrame)
    assert len(rs) == 175

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert isinstance(rs, pd.DataFrame)
    assert len(rs) == 7
    for station in rs.to_records():
        assert distance(center, station["geometry"]) < radius


def test_computedKeys_Filter_without_latlon() -> None:
    center = [11.010754, 47.800864]  # Hohenpeißenberg
    radius = 100 * 1000  # 100 km
    columns = (
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
    )

    filter_wind = dict(windDirection=float, windSpeed=float)
    filter_wind_geometry = dict(
        windDirection=float,
        windSpeed=float,
        geometry=lambda x: distance(center, x) < radius,
    )

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns)
    assert isinstance(rs, pd.DataFrame)
    assert len(rs) == 178

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert isinstance(rs, pd.DataFrame)
    assert len(rs) == 175

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert isinstance(rs, pd.DataFrame)
    assert len(rs) == 7
    for station in rs.to_records():
        assert distance(center, station["geometry"]) < radius
