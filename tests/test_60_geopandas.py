# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import typing as T
from importlib import import_module

import pytest

import pdbufr


def modules_installed(modules: T.List[str]) -> bool:
    for module in modules:
        try:
            import_module(module)
        except ImportError:
            return False
    return True


def MISSING(modules: T.List[str]) -> bool:
    return not modules_installed(modules)


SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
TEST_DATA_GEOPANDAS = os.path.join(
    SAMPLE_DATA_FOLDER,
    "Z__C_EDZW_20210516120400_bda01,synop_bufr_GER_999999_999999__MW_466.bin",
)


@pytest.mark.skipif(
    MISSING(["pyproj", "shapely"]), reason="pyproj and/or shapely not installed",
)
def distance(center: T.Any, position: T.Any) -> float:
    # center: Point, position: Point -> float
    from pyproj import Geod

    g = Geod(ellps="WGS84")
    az12, az21, dist = g.inv(position.x, position.y, center.x, center.y)
    return dist


@pytest.mark.skipif(
    MISSING(["geopandas", "shapely"]), reason="geopandas and/or shapely not installed",
)
def read_geo_bufr(
    path: T.Union[str, bytes, "os.PathLike[T.Any]"],
    columns: T.Iterable[str],
    filters: T.Mapping[str, T.Any] = {},
    required_columns: T.Union[bool, T.Iterable[str]] = True,
):  # -> geopandas.GeoDataFrame:
    """
    Read selected observations from a BUFR file into GeoDataFrame.

    :param path: The path to the BUFR file
    :param columns: A list of BUFR keys to return in the DataFrame for every observation
    :param filters: A dictionary of BUFR key / filter definition to filter the observations to return
    :param required_columns: The list BUFR keys that are required for all observations.
        ``True`` means all ``columns`` are required
    """
    import geopandas as gpd
    from shapely.geometry import Point

    for key in ["geometry", "CRS"]:
        if key not in columns:
            if isinstance(columns, list):
                columns.append(key)
            elif isinstance(columns, tuple):
                columns += (key,)
            elif isinstance(columns, set):
                columns |= {key}
            else:
                raise ValueError("columns must be an instance of list or tuple or set")

    dataFrame = pdbufr.read_bufr(path, columns, filters, required_columns)

    if dataFrame.empty:
        return dataFrame

    dataFrame["geometry"] = dataFrame["geometry"].apply(Point)
    CRS = dataFrame.CRS[0]
    if not CRS:
        raise TypeError(
            "pdbufr does currently not support the type of coordinate system reference in BUFR data"
        )
    return gpd.GeoDataFrame(dataFrame, geometry=dataFrame.geometry, crs=CRS)


@pytest.mark.skipif(
    MISSING(["shapely"]), reason="shapely not installed",
)
def test_GeoPandas_without_latlon_with_timesignificance():
    from shapely.geometry import Point

    center = Point([11.010754, 47.800864])  # Hohenpeißenberg
    radius = 100 * 1000  # 100 km
    columns = [
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
    ]
    filter_wind = dict(windDirection=float, windSpeed=float)
    filter_wind_geometry = dict(
        windDirection=float,
        windSpeed=float,
        geometry=lambda x: distance(center, Point(x)) < radius,
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rsg) == 178

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rs) == 178

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rsg) == 175

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rs) == 175

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rsg) == 10
    for station in rsg.to_records():
        assert distance(center, station["geometry"]) < radius

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rs) == 10
    for station in rs.to_records():
        assert distance(center, Point(station["geometry"])) < radius

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )


@pytest.mark.skipif(
    MISSING(["shapely"]), reason="shapely not installed",
)
def test_GeoPandas_with_latlon_with_timesignificance():
    from shapely.geometry import Point

    center = Point([11.010754, 47.800864])  # Hohenpeißenberg
    radius = 100 * 1000  # 100 km
    columns = [
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
    ]
    filter_wind = dict(windDirection=float, windSpeed=float)
    filter_wind_geometry = dict(
        windDirection=float,
        windSpeed=float,
        geometry=lambda x: distance(center, Point(x)) < radius,
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rsg) == 178

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rs) == 178

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rsg) == 175

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rs) == 175

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rsg) == 10
    for station in rsg.to_records():
        assert distance(center, station["geometry"]) < radius

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rs) == 10
    for station in rs.to_records():
        assert distance(center, Point(station["geometry"])) < radius

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )


@pytest.mark.skipif(
    MISSING(["shapely"]), reason="shapely not installed",
)
def test_GeoPandas_without_latlon_without_timesignificance():
    from shapely.geometry import Point

    center = Point([11.010754, 47.800864])  # Hohenpeißenberg
    radius = 100 * 1000  # 100 km
    columns = [
        "WMO_station_id",
        "stationOrSiteName",
        "geometry",
        "CRS",
        "typicalDate",
        "typicalTime",
        "timePeriod",
        "windDirection",
        "windSpeed",
    ]
    filter_wind = dict(windDirection=float, windSpeed=float)
    filter_wind_geometry = dict(
        windDirection=float,
        windSpeed=float,
        geometry=lambda x: distance(center, Point(x)) < radius,
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rsg) == 204

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rs) == 204

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rsg) == 201

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rs) == 201

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rsg) == 13
    for station in rsg.to_records():
        assert distance(center, station["geometry"]) < radius

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rs) == 13
    for station in rs.to_records():
        assert distance(center, Point(station["geometry"])) < radius

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )


@pytest.mark.skipif(
    MISSING(["shapely"]), reason="shapely not installed",
)
def test_GeoPandas_with_latlon_without_timesignificance():
    from shapely.geometry import Point

    center = Point([11.010754, 47.800864])  # Hohenpeißenberg
    radius = 100 * 1000  # 100 km
    columns = [
        "WMO_station_id",
        "stationOrSiteName",
        "latitude",
        "longitude",
        "geometry",
        "CRS",
        "typicalDate",
        "typicalTime",
        "timePeriod",
        "windDirection",
        "windSpeed",
    ]
    filter_wind = dict(windDirection=float, windSpeed=float)
    filter_wind_geometry = dict(
        windDirection=float,
        windSpeed=float,
        geometry=lambda x: distance(center, Point(x)) < radius,
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rsg) == 204

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rs) == 204

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rsg) == 201

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rs) == 201

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rsg) == 13
    for station in rsg.to_records():
        assert distance(center, station["geometry"]) < radius

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rs) == 13
    for station in rs.to_records():
        assert distance(center, Point(station["geometry"])) < radius

    assert any(
        rs.sort_index().sort_index(axis=1) == rsg.sort_index().sort_index(axis=1)
    )


@pytest.mark.skipif(
    MISSING(["shapely"]), reason="shapely not installed",
)
def test_GeoPandas_without_geometry_without_latlon_without_timesignificance():
    from shapely.geometry import Point

    center = Point([11.010754, 47.800864])  # Hohenpeißenberg
    radius = 100 * 1000  # 100 km
    columns = [
        "WMO_station_id",
        "stationOrSiteName",
        "typicalDate",
        "typicalTime",
        "timePeriod",
        "windDirection",
        "windSpeed",
    ]
    filter_wind = dict(windDirection=float, windSpeed=float)
    filter_wind_geometry = dict(
        windDirection=float,
        windSpeed=float,
        geometry=lambda x: distance(center, Point(x)) < radius,
    )

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rsg) == 204

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns)
    assert len(rs) == 204

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rsg) == 201

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind)
    assert len(rs) == 201

    rsg = read_geo_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rsg) == 13
    for station in rsg.to_records():
        assert distance(center, station["geometry"]) < radius

    rs = pdbufr.read_bufr(TEST_DATA_GEOPANDAS, columns, filter_wind_geometry)
    assert len(rs) == 13
    for station in rs.to_records():
        assert distance(center, Point(station["geometry"])) < radius
