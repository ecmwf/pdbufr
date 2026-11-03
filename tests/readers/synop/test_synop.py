# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import pdbufr
from pdbufr.readers.synop import _scan_cloud_summary
from pdbufr.utils.testing import sample_test_data_path


def _get_data():
    import os
    import sys

    here = os.path.dirname(__file__)
    sys.path.insert(0, here)
    import _synop_ref_data

    return _synop_ref_data


DATA = _get_data()


def test_synop_reader():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        level_columns=False,
        units_columns=False,
    )
    df = df.replace({None: np.nan})

    # r = df.to_dict()
    # print("r=", r)
    # print("r=", type(r["time"][0]))

    # # assert False

    # use this to create ref
    # r = df.to_json(date_format="iso", orient="records")
    # parsed = json.loads(r)
    # print("parsed=", parsed)

    df_ref = pd.DataFrame.from_dict(DATA.REF)
    df_ref.reset_index(drop=True, inplace=True)
    df_ref = df_ref.replace({None: np.nan})

    print("df=", df.columns.tolist())
    print("df_ref=", df_ref.columns.tolist())

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


@pytest.mark.parametrize(
    "columns, expected_values",
    [
        (["station", "t2m"], {"t2m": 300.45}),
        (["station", "t2m", "rh2m"], {"t2m": 300.45, "rh2m": 73}),
        (["station", "wind10m"], {"wind10m_speed": 1.6, "wind10m_dir": 100}),
        (["station", "wind10m_speed"], {"wind10m_speed": 1.6}),
        (["station", "wind10m_dir"], {"wind10m_dir": 100}),
        (
            ["station", "max_wgust"],
            {
                "max_wgust_speed_10min": 5.3,
                "max_wgust_dir_10min": 110.0,
                "max_wgust_speed_60min": 5.3,
                "max_wgust_dir_60min": 110.0,
                "max_wgust_speed_360min": 7.6,
                "max_wgust_dir_360min": 130.0,
            },
        ),
        (
            ["station", "precipitation"],
            {
                "precipitation_1h": 0.0,
                "precipitation_3h": 0.0,
                "precipitation_6h": 0.0,
                "precipitation_12h": 0.0,
                "precipitation_24h": 0.0,
            },
        ),
        (
            ["station", "global_solar_radiation"],
            {"global_solar_radiation_1h": 2249000, "global_solar_radiation_24h": 23211000},
        ),
        (
            ["station", "total_sunshine", "station_name", "t2m"],
            {
                "total_sunshine_1h": 39,
                "total_sunshine_24h": 535,
                "station_name": "MANGAREVA",
                "t2m": 300.45,
            },
        ),
    ],
)
def test_synop_columns_user(columns, expected_values):
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        filters={"count": 1},
        columns=columns,
    )

    ref_station = {
        "stnid": "91948",
        "lat": -23.13017,
        "lon": -134.96533,
        "elevation": 91.0,
        "time": datetime.datetime.fromisoformat("2020-03-15T00:00:00.000"),
    }

    ref = {**ref_station, **expected_values}

    df_ref = pd.DataFrame.from_dict([ref])
    df_ref.reset_index(drop=True, inplace=True)
    df = df.replace(np.nan, None)

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_columns_station():
    df = pdbufr.read_bufr(sample_test_data_path("syn_new.bufr"), reader="synop", columns="station")

    df_ref = pd.DataFrame.from_dict(DATA.REF_STATION)
    df_ref.reset_index(drop=True, inplace=True)

    df = df.replace(np.nan, None)

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_columns_geometry():
    df = pdbufr.read_bufr(sample_test_data_path("syn_new.bufr"), reader="synop", columns="geometry")

    df_ref = pd.DataFrame.from_dict(DATA.REF_GEOMETRY)
    df_ref.reset_index(drop=True, inplace=True)

    df = df.replace(np.nan, None)

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_columns_location():
    df = pdbufr.read_bufr(sample_test_data_path("syn_new.bufr"), reader="synop", columns="location")

    df_ref = pd.DataFrame.from_dict(DATA.REF_LOCATION)
    df_ref.reset_index(drop=True, inplace=True)

    df = df.replace(np.nan, None)

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_units_1():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        filters={"count": 1},
        level_columns=False,
        units_columns=False,
        units={"mslp": "hPa", "td2m": "degC", "t2m": "degF"},
    )

    ref = {"mslp": 1013.2, "td2m": 22.000000000000057, "t2m": 81.13999999999996}

    for k, v in ref.items():
        assert np.isclose(df[k][0], v), f"{k}={df[k][0]} != {v}"

    for k in ref:
        assert f"{k}_units" not in df, f"{k}_units should not be in df"


def test_synop_units_2():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        filters={"count": 1},
        level_columns=False,
        units_columns=True,
        units={"mslp": "hPa", "td2m": "degC", "t2m": "degF"},
    )

    ref = {"mslp": 1013.2, "td2m": 22.000000000000057, "t2m": 81.13999999999996}

    for k, v in ref.items():
        assert np.isclose(df[k][0], v), f"{k}={df[k][0]} != {v}"

    ref = {"mslp_units": "hPa", "td2m_units": "degC", "t2m_units": "degF"}
    for k, v in ref.items():
        assert df[k][0] == v, f"{k}={df[k][0]} != {v}"


@pytest.mark.parametrize(
    "columns, expected_values",
    [
        (["t2m"], {"t2m": 300.45, "t2m_level": 1.5}),  # Default units are K
        (["t2m", "rh2m"], {"t2m": 300.45, "t2m_level": 1.5, "rh2m": 73, "rh2m_level": 1.5}),
        (
            ["wind10m"],
            {
                "wind10m_speed": 1.6,
                "wind10m_dir": 100,
                "wind10m_speed_level": 10,
                "wind10m_dir_level": 10,
            },
        ),
        (["wind10m_speed"], {"wind10m_speed": 1.6, "wind10m_speed_level": 10}),
        (["wind10m_dir"], {"wind10m_dir": 100, "wind10m_dir_level": 10}),
        (
            ["max_wgust"],
            {
                "max_wgust_speed_10min": 5.3,
                "max_wgust_dir_10min": 110.0,
                "max_wgust_speed_10min_level": 10,
                "max_wgust_dir_10min_level": 10,
                "max_wgust_speed_60min": 5.3,
                "max_wgust_dir_60min": 110.0,
                "max_wgust_speed_60min_level": 10,
                "max_wgust_dir_60min_level": 10,
                "max_wgust_speed_360min": 7.6,
                "max_wgust_dir_360min": 130.0,
                "max_wgust_speed_360min_level": 10,
                "max_wgust_dir_360min_level": 10,
            },
        ),
        (
            ["precipitation"],
            {
                "precipitation_1h": 0.0,
                "precipitation_1h_level": 1.5,
                "precipitation_3h": 0.0,
                "precipitation_3h_level": 1.5,
                "precipitation_6h": 0.0,
                "precipitation_6h_level": 1.5,
                "precipitation_12h": 0.0,
                "precipitation_12h_level": 1.5,
                "precipitation_24h": 0.0,
                "precipitation_24h_level": 1.5,
            },
        ),
        (
            ["global_solar_radiation"],
            {"global_solar_radiation_1h": 2249000, "global_solar_radiation_24h": 23211000},
        ),
        (
            ["total_sunshine", "station_name", "t2m"],
            {
                "total_sunshine_1h": 39,
                "total_sunshine_24h": 535,
                "station_name": "MANGAREVA",
                "t2m": 300.45,
                "t2m_level": 1.5,
            },
        ),
    ],
)
def test_synop_levels(columns, expected_values):
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        filters={"count": 1},
        columns=columns,
        level_columns=True,
    )

    ref = expected_values
    df_ref = pd.DataFrame.from_dict([ref])
    df_ref.reset_index(drop=True, inplace=True)
    df = df.replace(np.nan, None)

    # print("df=", df.columns.tolist())

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


@pytest.mark.parametrize(
    "columns, expected_values",
    [
        (["t2m"], {"t2m": 300.45, "t2m_units": "K"}),  # Default units are K
        (
            ["t2m", "rh2m"],
            {
                "t2m": 300.45,
                "t2m_units": "K",
                "rh2m": 73,
                "rh2m_units": "%",
            },
        ),
        (
            ["wind10m"],
            {
                "wind10m_speed": 1.6,
                "wind10m_dir": 100,
                "wind10m_speed_units": "m/s",
                "wind10m_dir_units": "deg",
            },
        ),
        (
            ["wind10m_speed"],
            {
                "wind10m_speed": 1.6,
                "wind10m_speed_units": "m/s",
            },
        ),
        (
            ["wind10m_dir"],
            {
                "wind10m_dir": 100,
                "wind10m_dir_units": "deg",
            },
        ),
        (
            ["max_wgust"],
            {
                "max_wgust_speed_10min": 5.3,
                "max_wgust_dir_10min": 110.0,
                "max_wgust_speed_10min_units": "m/s",
                "max_wgust_dir_10min_units": "deg",
                "max_wgust_speed_60min": 5.3,
                "max_wgust_dir_60min": 110.0,
                "max_wgust_speed_60min_units": "m/s",
                "max_wgust_dir_60min_units": "deg",
                "max_wgust_speed_360min": 7.6,
                "max_wgust_dir_360min": 130.0,
                "max_wgust_speed_360min_units": "m/s",
                "max_wgust_dir_360min_units": "deg",
            },
        ),
        (
            ["precipitation"],
            {
                "precipitation_1h": 0.0,
                "precipitation_1h_units": "kg m-2",
                "precipitation_3h": 0.0,
                "precipitation_3h_units": "kg m-2",
                "precipitation_6h": 0.0,
                "precipitation_6h_units": "kg m-2",
                "precipitation_12h": 0.0,
                "precipitation_12h_units": "kg m-2",
                "precipitation_24h": 0.0,
                "precipitation_24h_units": "kg m-2",
            },
        ),
        (
            ["global_solar_radiation"],
            {
                "global_solar_radiation_1h": 2249000,
                "global_solar_radiation_1h_units": "J m-2",
                "global_solar_radiation_24h": 23211000,
                "global_solar_radiation_24h_units": "J m-2",
            },
        ),
        (
            ["total_sunshine", "station_name", "t2m"],
            {
                "total_sunshine_1h": 39,
                "total_sunshine_1h_units": "min",
                "total_sunshine_24h": 535,
                "total_sunshine_24h_units": "min",
                "station_name": "MANGAREVA",
                "t2m": 300.45,
                "t2m_units": "K",
            },
        ),
    ],
)
def test_synop_units(columns, expected_values):
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        filters={"count": 1},
        columns=columns,
        units_columns=True,
    )

    ref = expected_values
    df_ref = pd.DataFrame.from_dict([ref])
    df_ref.reset_index(drop=True, inplace=True)
    df = df.replace(np.nan, None)

    print("df=", df.columns.tolist())

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


@pytest.mark.parametrize(
    "columns, expected_values",
    [
        (["t2m"], {"t2m": 300.45, "t2m_units": "K", "t2m_level": 1.5}),  # Default units are K
        (
            ["t2m", "rh2m"],
            {
                "t2m": 300.45,
                "t2m_units": "K",
                "t2m_level": 1.5,
                "rh2m": 73,
                "rh2m_units": "%",
                "rh2m_level": 1.5,
            },
        ),
        (
            ["wind10m"],
            {
                "wind10m_speed": 1.6,
                "wind10m_dir": 100,
                "wind10m_speed_units": "m/s",
                "wind10m_dir_units": "deg",
                "wind10m_speed_level": 10,
                "wind10m_dir_level": 10,
            },
        ),
        (["wind10m_speed"], {"wind10m_speed": 1.6, "wind10m_speed_units": "m/s", "wind10m_speed_level": 10}),
        (["wind10m_dir"], {"wind10m_dir": 100, "wind10m_dir_units": "deg", "wind10m_dir_level": 10}),
        (
            ["max_wgust"],
            {
                "max_wgust_speed_10min": 5.3,
                "max_wgust_dir_10min": 110.0,
                "max_wgust_speed_10min_units": "m/s",
                "max_wgust_dir_10min_units": "deg",
                "max_wgust_speed_10min_level": 10,
                "max_wgust_dir_10min_level": 10,
                "max_wgust_speed_60min": 5.3,
                "max_wgust_dir_60min": 110.0,
                "max_wgust_speed_60min_units": "m/s",
                "max_wgust_dir_60min_units": "deg",
                "max_wgust_speed_60min_level": 10,
                "max_wgust_dir_60min_level": 10,
                "max_wgust_speed_360min": 7.6,
                "max_wgust_dir_360min": 130.0,
                "max_wgust_speed_360min_units": "m/s",
                "max_wgust_dir_360min_units": "deg",
                "max_wgust_speed_360min_level": 10,
                "max_wgust_dir_360min_level": 10,
            },
        ),
        (
            ["precipitation"],
            {
                "precipitation_1h": 0.0,
                "precipitation_1h_units": "kg m-2",
                "precipitation_1h_level": 1.5,
                "precipitation_3h": 0.0,
                "precipitation_3h_units": "kg m-2",
                "precipitation_3h_level": 1.5,
                "precipitation_6h": 0.0,
                "precipitation_6h_units": "kg m-2",
                "precipitation_6h_level": 1.5,
                "precipitation_12h": 0.0,
                "precipitation_12h_units": "kg m-2",
                "precipitation_12h_level": 1.5,
                "precipitation_24h": 0.0,
                "precipitation_24h_units": "kg m-2",
                "precipitation_24h_level": 1.5,
            },
        ),
        (
            ["global_solar_radiation"],
            {
                "global_solar_radiation_1h": 2249000,
                "global_solar_radiation_1h_units": "J m-2",
                "global_solar_radiation_24h": 23211000,
                "global_solar_radiation_24h_units": "J m-2",
            },
        ),
        (
            ["total_sunshine", "station_name", "t2m"],
            {
                "total_sunshine_1h": 39,
                "total_sunshine_1h_units": "min",
                "total_sunshine_24h": 535,
                "total_sunshine_24h_units": "min",
                "station_name": "MANGAREVA",
                "t2m": 300.45,
                "t2m_units": "K",
                "t2m_level": 1.5,
            },
        ),
    ],
)
def test_synop_levels_units(columns, expected_values):
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        filters={"count": 1},
        columns=columns,
        level_columns=True,
        units_columns=True,
    )

    ref = expected_values
    df_ref = pd.DataFrame.from_dict([ref])
    df_ref.reset_index(drop=True, inplace=True)
    df = df.replace(np.nan, None)

    print("df=", df.columns.tolist())

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_stnid_invalid_wigos():
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_invalid_wigos_id.bufr"),
        reader="synop",
    )

    assert df["stnid"].iloc[0] == "_MI12904"


@pytest.mark.parametrize(
    "stnd_keys,expected_result",
    [
        ("ident", "_MI12904"),
        (["ident"], "_MI12904"),
        ("longStationName", "Ramiola_simnpr"),
        (["longStationName"], "Ramiola_simnpr"),
        (["longStationName", "ident"], "Ramiola_simnpr"),
        (["ident", "longStationName"], "_MI12904"),
        (["wigos_id", "ident", "longStationName"], "_MI12904"),
        ("WMO_station_id", None),
        ("wmo_station_id", None),
        ("WIGOS_id", None),
        ("wigos_id", None),
    ],
)
def test_synop_stnid_keys_1(stnd_keys, expected_result):
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_invalid_wigos_id.bufr"),
        reader="synop",
        stnid_keys=stnd_keys,
    )

    assert df["stnid"].iloc[0] == expected_result, f"Expected {expected_result}, got {df['stnid'].iloc[0]}"


@pytest.mark.parametrize(
    "stnd_keys,expected_result",
    [
        ("ident", ["91948", "11766", "56257"]),
        (["ident"], ["91948", "11766", "56257"]),
        ("stationOrSiteName", ["MANGAREVA", "CERVENA U LIBAVE", "LITANG"]),
        (["stationOrSiteName"], ["MANGAREVA", "CERVENA U LIBAVE", "LITANG"]),
        (["ident", "stationOrSiteName"], ["91948", "11766", "56257"]),
        (["stationOrSiteName", "ident"], ["MANGAREVA", "CERVENA U LIBAVE", "LITANG"]),
        (["WIGOS_station_id", "ident", "longStationName"], ["91948", "11766", "56257"]),
        ("WMO_station_id", ["91948", "11766", "56257"]),
        ("WIGOS_station_id", [None, None, None]),
    ],
)
def test_synop_stnid_keys_2(stnd_keys, expected_result):
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        stnid_keys=stnd_keys,
    )
    assert df["stnid"].tolist() == expected_result, f"Expected {expected_result}, got {df['stnid']}"


@pytest.mark.parametrize(
    "stnd_keys,expected_result",
    [
        ("ident", "_MI12904"),
        (["ident"], "_MI12904"),
        ("longStationName", "Ramiola_simnpr"),
        (["longStationName"], "Ramiola_simnpr"),
        (["longStationName", "ident"], "Ramiola_simnpr"),
        (["ident", "longStationName"], "_MI12904"),
        (["wigos_id", "ident", "longStationName"], "_MI12904"),
        ("WMO_station_id", None),
        ("wmo_station_id", None),
        ("WIGOS_id", None),
        ("wigos_id", None),
    ],
)
def test_synop_stnid_keys_3(stnd_keys, expected_result):
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_invalid_wigos_id.bufr"),
        reader="synop",
        columns="station",
        stnid_keys=stnd_keys,
    )

    assert df["stnid"].iloc[0] == expected_result, f"Expected {expected_result}, got {df['stnid'].iloc[0]}"


@pytest.mark.parametrize(
    "columns, expected_values",
    [
        (
            ["station", "sw_radiation"],
            [
                {"sw_radiation_10min": 0.0, "sw_radiation_24h": None, "sw_radiation_1h": None},
                {"sw_radiation_10min": None, "sw_radiation_24h": 9343000.0, "sw_radiation_1h": 0.0},
            ],
        ),
        (
            ["station", "lw_radiation"],
            [
                {"lw_radiation_10min": None, "lw_radiation_24h": None, "lw_radiation_1h": None},
                {"lw_radiation_10min": None, "lw_radiation_24h": None, "lw_radiation_1h": None},
            ],
        ),
        (
            ["station", "net_radiation"],
            [
                {"net_radiation": None, "net_radiation_24h": None, "net_radiation_1h": None},
                {"net_radiation": None, "net_radiation_24h": None, "net_radiation_1h": None},
            ],
        ),
        (
            ["station", "global_solar_radiation"],
            [
                {
                    "global_solar_radiation_10min": 0.0,
                    "global_solar_radiation_24h": None,
                    "global_solar_radiation_1h": None,
                },
                {
                    "global_solar_radiation_10min": None,
                    "global_solar_radiation_24h": None,
                    "global_solar_radiation_1h": None,
                },
            ],
        ),
        (
            ["station", "diffuse_solar_radiation"],
            [
                {
                    "diffuse_solar_radiation_10min": None,
                    "diffuse_solar_radiation_24h": None,
                    "diffuse_solar_radiation_1h": None,
                },
                {
                    "diffuse_solar_radiation_10min": None,
                    "diffuse_solar_radiation_24h": None,
                    "diffuse_solar_radiation_1h": None,
                },
            ],
        ),
        (
            ["station", "direct_solar_radiation"],
            [
                {
                    "direct_solar_radiation_10min": None,
                    "direct_solar_radiation_24h": None,
                    "direct_solar_radiation_1h": None,
                },
                {
                    "direct_solar_radiation_10min": None,
                    "direct_solar_radiation_24h": None,
                    "direct_solar_radiation_1h": None,
                },
            ],
        ),
    ],
)
def test_synop_radiation(columns, expected_values):
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_radiation.bufr"),
        reader="synop",
        columns=columns,
    )
    df = df.replace({None: np.nan})

    ref_stations = [
        {
            "stnid": "_3483d8a",
            "lat": 46.575,
            "lon": 18.8472,
            "elevation": 98.0,
            "time": datetime.datetime.fromisoformat("2024-03-29T23:50:00.000"),
        },
        {
            "stnid": "08579",
            "lat": 38.7662,
            "lon": -9.1275,
            "elevation": 103.9,
            "time": datetime.datetime.fromisoformat("2024-03-30T00:00:00.000"),
        },
    ]

    ref = [{**ref_stations[0], **expected_values[0]}, {**ref_stations[1], **expected_values[1]}]

    df_ref = pd.DataFrame.from_dict(ref)
    df_ref.reset_index(drop=True, inplace=True)
    df_ref = df_ref.replace({None: np.nan})

    try:
        pd.testing.assert_frame_equal(
            df,
            df_ref,
            check_dtype=False,
            check_index_type=False,
            check_datetimelike_compat=True,
        )
    except Exception as e:
        print("e=", e)
        raise


# Columns extracted from the cloud summary group (the group with
# verticalSignificanceSurfaceObservations = 7, "low cloud" in WMO Code Table 0 08 002): its
# first three cloudType values are the low, middle and high cloud types (CL, CM, CH), its
# cloudAmount is the cloud amount (Nh, raw code table 020011 value) and its
# heightOfBaseOfCloud is the height of the base of the lowest cloud.
CLOUD_SUMMARY_COLUMNS = [
    "cloud_type_low",
    "cloud_type_middle",
    "cloud_type_high",
    "cloud_amount_nh",
    "cloud_base_lowest",
]

EDZW_FILE = "Z__C_EDZW_20210516120400_bda01,synop_bufr_GER_999999_999999__MW_466.bufr"


def _assert_cloud_frame(df: pd.DataFrame, ref: list) -> None:
    """Compare df against a reference list of dicts, with None and NaN treated as equal."""
    df = df.replace({None: np.nan})
    df_ref = pd.DataFrame.from_dict(ref)
    df_ref.reset_index(drop=True, inplace=True)
    df_ref = df_ref.replace({None: np.nan})

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_cloud_summary():
    """Test the cloud summary columns on all three subsets of syn_new.bufr, combined with cloud_cover."""
    columns = ["station", *CLOUD_SUMMARY_COLUMNS, "cloud_cover"]
    df = pdbufr.read_bufr(sample_test_data_path("syn_new.bufr"), reader="synop", columns=columns)

    assert df["stnid"].tolist() == ["91948", "11766", "56257"]

    ref = [
        {
            # cloud summary group (vertical significance 7): CL/CM/CH = 32/20/10, Nh = 2, base = 600 m
            "cloud_type_low": 32,
            "cloud_type_middle": 20,
            "cloud_type_high": 10,
            "cloud_amount_nh": 2,
            "cloud_base_lowest": 600.0,
            "cloud_cover": 25.0,
        },
        {
            # the subset reports no cloud information at all -> missing values
            "cloud_type_low": None,
            "cloud_type_middle": None,
            "cloud_type_high": None,
            "cloud_amount_nh": None,
            "cloud_base_lowest": None,
            "cloud_cover": None,
        },
        {
            # no vertical significance = 7 group: the vertical significance of the first cloud
            # group is 0 (SYNOP rules), so its values are the summary: the amount and the cloud
            # types are missing and its heightOfBaseOfCloud is the lowest cloud base
            "cloud_type_low": None,
            "cloud_type_middle": None,
            "cloud_type_high": None,
            "cloud_amount_nh": None,
            "cloud_base_lowest": 2500.0,
            "cloud_cover": 0.0,
        },
    ]

    _assert_cloud_frame(df[CLOUD_SUMMARY_COLUMNS + ["cloud_cover"]], ref)


def test_synop_cloud_summary_wigos():
    """Test the cloud summary columns on synop_wigos.bufr (template 307092).

    The WIGOS subsets have no cloudType key and the value of their
    verticalSignificanceSurfaceObservations keys is missing, so the cloud types are missing and
    the amount and base come from the first cloud group of the subset.
    """
    columns = ["station", *CLOUD_SUMMARY_COLUMNS, "cloud_cover"]
    df = pdbufr.read_bufr(sample_test_data_path("synop_wigos.bufr"), reader="synop", columns=columns)

    assert df["stnid"].tolist() == ["0-705-0-1931", "0-705-0-1932", "0-705-0-1933"]

    ref = [
        {
            "cloud_type_low": None,
            "cloud_type_middle": None,
            "cloud_type_high": None,
            "cloud_amount_nh": 8,
            "cloud_base_lowest": 240.0,
            "cloud_cover": 100.0,
        },
        {
            "cloud_type_low": None,
            "cloud_type_middle": None,
            "cloud_type_high": None,
            "cloud_amount_nh": None,
            "cloud_base_lowest": None,
            "cloud_cover": None,
        },
        {
            "cloud_type_low": None,
            "cloud_type_middle": None,
            "cloud_type_high": None,
            "cloud_amount_nh": None,
            "cloud_base_lowest": None,
            "cloud_cover": None,
        },
    ]

    _assert_cloud_frame(df[CLOUD_SUMMARY_COLUMNS + ["cloud_cover"]], ref)


@pytest.mark.parametrize("columns", ["default", ["station", "t2m"]])
def test_synop_cloud_summary_not_in_default_columns(columns):
    """The cloud summary columns are only added to the output when they are explicitly requested."""
    df = pdbufr.read_bufr(sample_test_data_path("syn_new.bufr"), reader="synop", columns=columns)

    cols = df.columns.tolist()
    assert "t2m" in cols
    if columns == "default":
        assert "cloud_cover" in cols
    for name in CLOUD_SUMMARY_COLUMNS:
        assert name not in cols, f"{name} must not be selected by columns={columns}"


def test_synop_cloud_summary_default():
    """The default columns (no columns argument) do not contain the cloud summary columns."""
    df = pdbufr.read_bufr(sample_test_data_path("syn_new.bufr"), reader="synop")

    assert "cloud_cover" in df.columns.tolist()
    for name in CLOUD_SUMMARY_COLUMNS:
        assert name not in df.columns.tolist(), f"{name} must not be in the default columns"


def test_synop_cloud_summary_multi_subset_uncompressed():
    """Uncompressed file with 12 subsets whose cloud keys are all missing -> missing values, no error."""
    columns = ["station", *CLOUD_SUMMARY_COLUMNS, "cloud_cover"]
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_multi_subset_uncompressed.bufr"),
        reader="synop",
        columns=columns,
    )

    assert len(df) == 12

    sub = df[CLOUD_SUMMARY_COLUMNS + ["cloud_cover"]].replace({None: np.nan})
    assert sub.isna().all().all(), f"expected all cloud values to be missing, got\n{df}"


def test_synop_cloud_cover_no_cloud_cover_key():
    """A file without any cloudCoverTotal key keeps the requested cloud_cover column.

    synop_invalid_wigos_id.bufr (template 307092) has no cloud key at all. The cloud_cover
    column is then emitted with None values, like the cloud summary columns and like a file
    where the key is present but its values are missing, instead of silently disappearing
    from the frame.
    """
    columns = ["station", *CLOUD_SUMMARY_COLUMNS, "cloud_cover"]
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_invalid_wigos_id.bufr"),
        reader="synop",
        columns=columns,
    )

    assert len(df) == 1

    cols = df.columns.tolist()
    for name in [*CLOUD_SUMMARY_COLUMNS, "cloud_cover"]:
        assert name in cols, f"{name} must be in the frame even when no message has the BUFR key"

    assert df["cloud_cover"].isna().all(), f"expected an all-None cloud_cover column, got\n{df['cloud_cover']}"


def test_synop_cloud_cover_no_cloud_cover_key_units_columns():
    """Same as above with units_columns=True: cloud_cover and cloud_cover_units are all None."""
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_invalid_wigos_id.bufr"),
        reader="synop",
        columns=["station", "cloud_cover"],
        units_columns=True,
    )

    assert len(df) == 1
    for name in ["cloud_cover", "cloud_cover_units"]:
        assert name in df.columns, f"{name} missing from\n{df}"
        assert df[name].isna().all(), f"expected all-None {name}, got\n{df[name]}"


@pytest.mark.parametrize(
    "path, filters, expected",
    [
        (
            "syn_new.bufr",
            {"count": 1},
            # the subset also contains a cloud layer with vertical significance 1 which repeats
            # cloudAmount and heightOfBaseOfCloud and adds #4#cloudType=8. None of them may
            # overwrite the values of the cloud summary group.
            [32, 20, 10, 2, 600.0],
        ),
        (
            EDZW_FILE,
            {"stnid": "10038"},
            # the summary group (vertical significance 7) of station 10038 is followed by three
            # cloud layers (vertical significances 1, 2, 3) with cloudTypes 8, 8, 3, cloudAmounts
            # 2, 3, 5 and cloud bases 450, 750, 2700 m; only the summary values are reported.
            [38, 23, 10, 5, 450.0],
        ),
    ],
)
def test_synop_cloud_summary_ignores_cloud_layers(path, filters, expected):
    """The individual cloud layers (vertical significances 1-6) must not overwrite the summary."""
    columns = ["station", *CLOUD_SUMMARY_COLUMNS]
    df = pdbufr.read_bufr(sample_test_data_path(path), reader="synop", columns=columns, filters=filters)

    assert len(df) == 1

    values = [float(df[c].iloc[0]) for c in CLOUD_SUMMARY_COLUMNS]
    assert values == [float(v) for v in expected], f"{values} != {expected}"


def test_synop_cloud_summary_units():
    """Only cloud_base_lowest has units: the code columns have no units and are not converted."""
    columns = ["station", *CLOUD_SUMMARY_COLUMNS]
    df = pdbufr.read_bufr(sample_test_data_path("syn_new.bufr"), reader="synop", columns=columns, units_columns=True)

    # cloud_base_lowest has the BUFR units of its heightOfBaseOfCloud key (m), also for the
    # subset whose value is missing, just like the other parameters with units
    assert float(df["cloud_base_lowest"].iloc[0]) == 600.0
    assert df["cloud_base_lowest_units"].tolist() == ["m", "m", "m"]

    # the cloud types and the cloud amount are raw codes: no units column for them
    for name in ["cloud_type_low", "cloud_type_middle", "cloud_type_high", "cloud_amount_nh"]:
        assert name + "_units" not in df.columns.tolist(), f"{name} must not have a units column"

    # the cloud amount of the first subset is the raw code table 020011 value 2 (two oktas),
    # not a percentage, and neither a unit system nor a units dict converts it or the types
    df_si = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        columns=columns,
        unit_system="si",
        units={"cloud_amount_nh": "ft", "cloud_type_low": "ft"},
    )
    assert float(df_si["cloud_amount_nh"].iloc[0]) == 2.0
    assert float(df_si["cloud_type_low"].iloc[0]) == 32.0


def test_synop_cloud_base_lowest_unit_conversion():
    """cloud_base_lowest supports unit conversion like the other parameters with units."""
    columns = ["station", "cloud_base_lowest"]
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        columns=columns,
        units_columns=True,
        units={"cloud_base_lowest": "ft"},
    )

    assert np.isclose(float(df["cloud_base_lowest"].iloc[0]), 600.0 / 0.3048)
    assert np.isclose(float(df["cloud_base_lowest"].iloc[2]), 2500.0 / 0.3048)
    assert pd.isna(df["cloud_base_lowest"].iloc[1])
    # a missing value is not converted and keeps the BUFR units, like for the other parameters
    assert df["cloud_base_lowest_units"].tolist() == ["ft", "m", "ft"]


# The synop_<dataSubCategory>_<centre>_M<MTV>.bufr files below are taken unchanged from the WMO
# surf_land BUFR training data set and cover cloud layouts the other cloud tests do not have.
# See .ecmwf-multi-agents/notes/surf-land-cloud-survey.md for the layout families.
@pytest.mark.parametrize(
    "path, stnid, expected",
    [
        (
            "synop_0_193_M14.bufr",
            "91554",
            # template 307080 (MTV 14): the vs=7 summary group is the first group, followed by a
            # cloud layer (vs=1) with its own amount, base and type, three placeholder groups
            # (vs missing) and a cloud drift group; none of them may overwrite the summary.
            (38, 20, 10, 5, 600.0, 62.0),
        ),
        (
            "synop_0_36_M29.bufr",
            "48377",
            # same family with MTV 29, with vs=7/8/9 marker groups after the summary group.
            (32, 20, 15, 2, 800.0, 38.0),
        ),
        (
            "synop_147_98_M32.bufr",
            "KRAS",
            # legacy SYNOP code form (template 307011): cloudCoverTotal plus a bare
            # heightOfBaseOfCloud and no verticalSignificanceSurfaceObservations key at all.
            # Without any vs key the first occurrence of each cloud key is the summary, so the
            # height is the lowest cloud base (survey family F3).
            (None, None, None, None, 120.0, 100.0),
        ),
        (
            "synop_180_85_M22.bufr",
            "7003",
            # template 307096 with CHINA NMC local vs codes: the first group has vs missing and
            # holds cloudAmount=4 and heightOfBaseOfCloud=1020 m (its cloudType values are
            # missing), the following groups are layers with local vs=21/22/23. The first group
            # fallback of the SYNOP rules supplies Nh and the base; the vs=21+ layer values must
            # not surface (survey family F7, vs missing first group).
            (None, None, None, 4, 1020.0, 100.0),
        ),
    ],
)
def test_synop_cloud_summary_surf_land(path, stnid, expected):
    """The cloud summary columns on the surf_land layouts with a recognisable summary group."""
    columns = ["station", *CLOUD_SUMMARY_COLUMNS, "cloud_cover"]
    df = pdbufr.read_bufr(sample_test_data_path(path), reader="synop", columns=columns)

    assert len(df) == 1
    assert df["stnid"].iloc[0] == stnid

    ref = [dict(zip([*CLOUD_SUMMARY_COLUMNS, "cloud_cover"], expected))]
    _assert_cloud_frame(df[CLOUD_SUMMARY_COLUMNS + ["cloud_cover"]], ref)


def test_synop_cloud_summary_surf_land_percent_confidence():
    """surf_land auto-SYNOP file (template 307005, every cloud key with ->percentConfidence).

    Its cloud groups use vs=1..4 and there is no vs=7/0/missing first group, so the reader does
    not recognise a summary group and the 5 summary columns stay missing even though the file
    reports cloudAmount=6, heightOfBaseOfCloud=800 m and cloudTypes 35/20/10 in its vs=1 group
    (known limitation, survey flag 1). Only cloudCoverTotal=75 surfaces, as cloud_cover.
    """
    columns = ["station", *CLOUD_SUMMARY_COLUMNS, "cloud_cover"]
    df = pdbufr.read_bufr(sample_test_data_path("synop_1_98_M13.bufr"), reader="synop", columns=columns)

    assert len(df) == 1
    assert df["stnid"].iloc[0] == "13579"

    ref = [
        {
            "cloud_type_low": None,
            "cloud_type_middle": None,
            "cloud_type_high": None,
            "cloud_amount_nh": None,
            "cloud_base_lowest": None,
            "cloud_cover": 75.0,
        }
    ]
    _assert_cloud_frame(df[CLOUD_SUMMARY_COLUMNS + ["cloud_cover"]], ref)


@pytest.mark.parametrize(
    "path",
    [
        # template 307091: four layer groups (vs, amount, type, base) but no summary group,
        # and all the cloud values in the file are missing
        "synop_6_218_M33.bufr",
        # template 307092 variant with only cloudCoverTotal (with ->associatedField) and no
        # cloud group at all; its value is missing
        "synop_178_98_M33.bufr",
        # WMO regional SYNOP without any cloud key (uncompressed / compressed single subset)
        "synop_2_98_M6.bufr",
        "synop_28_98_M33.bufr",
    ],
)
def test_synop_cloud_summary_surf_land_all_missing(path):
    """surf_land layouts without a usable summary: all cloud columns are missing, no error."""
    columns = ["station", *CLOUD_SUMMARY_COLUMNS, "cloud_cover"]
    df = pdbufr.read_bufr(sample_test_data_path(path), reader="synop", columns=columns)

    assert len(df) == 1

    cols = df.columns.tolist()
    for name in [*CLOUD_SUMMARY_COLUMNS, "cloud_cover"]:
        assert name in cols, f"{name} must be in the frame (columns={columns})"

    sub = df[CLOUD_SUMMARY_COLUMNS + ["cloud_cover"]].replace({None: np.nan})
    assert sub.isna().all().all(), f"expected all cloud values to be missing, got\n{df}"


def test_synop_cloud_summary_surf_land_compressed():
    """Compressed multi-subset surf_land file (template 307080, 6 subsets): the compressed
    per-subset cloud scan runs and every cloud value is missing.

    In the surf_land data set there is no compressed file with populated cloud values, so this
    exercises the compressed path for missingness, not for extraction (survey flag 4).
    """
    columns = ["station", *CLOUD_SUMMARY_COLUMNS, "cloud_cover"]
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_255_50_M29_compressed.bufr"),
        reader="synop",
        columns=columns,
    )

    assert len(df) == 6

    sub = df[CLOUD_SUMMARY_COLUMNS + ["cloud_cover"]].replace({None: np.nan})
    assert sub.isna().all().all(), f"expected all cloud values to be missing, got\n{df}"


class _FakeSubsetCollector:
    """Minimal stand-in for BufrSubsetCollector: yields a fixed key sequence.

    The ``filtered_keys`` mirror the yielded sequence with ranked keys and
    ``owner.message.get`` answers the ``<key>->units`` lookups from the ``units`` dict,
    keyed by full ranked key or by key name.
    """

    class _Key:
        def __init__(self, rank: int, name: str):
            self.level = 0
            self.rank = rank
            self.name = name

        @property
        def key(self) -> str:
            return f"#{self.rank}#{self.name}"

    class _Message:
        def __init__(self, units):
            self._units = units

        def get(self, key, default=None):
            if not key.endswith("->units"):
                return default
            name = key.rpartition("#")[2][: -len("->units")]
            if key in self._units:
                return self._units[key]
            return self._units.get(name, default)

    def __init__(self, values, units=None):
        self._values = list(values)
        ranks: dict = {}
        self.filtered_keys = []
        for name, _ in self._values:
            ranks[name] = ranks.get(name, 0) + 1
            self.filtered_keys.append(self._Key(ranks[name], name))
        self.owner = SimpleNamespace(message=self._Message(units if units is not None else {}))

    def iter_values(self):
        return iter(self._values)


VS = "verticalSignificanceSurfaceObservations"


@pytest.mark.parametrize(
    "values, expected",
    [
        # a subset with only individual cloud layers (vertical significances 1-6) has no
        # summary: the layers must never fill the columns (regression test)
        (
            [
                (VS, 1),
                ("cloudAmount", 2),
                ("cloudType", 8),
                ("heightOfBaseOfCloud", 600.0),
                (VS, 2),
                ("cloudAmount", 3),
                ("cloudType", 6),
                ("heightOfBaseOfCloud", 1500.0),
            ],
            (None, None, [], None),
        ),
        # the vertical significance = 7 group is the summary, it ends at the next group
        (
            [
                (VS, 7),
                ("cloudAmount", 2),
                ("heightOfBaseOfCloud", 600.0),
                ("cloudType", 32),
                ("cloudType", 20),
                ("cloudType", 10),
                (VS, 1),
                ("cloudAmount", 5),
                ("cloudType", 8),
            ],
            (2, 600.0, [32, 20, 10], "m"),
        ),
        # a vertical significance = 7 group after individual layers is still the summary
        (
            [(VS, 1), ("cloudAmount", 9), ("heightOfBaseOfCloud", 100.0), (VS, 7), ("cloudAmount", 3)],
            (3, None, [], None),
        ),
        # vertical significance 0: the first group follows the SYNOP rules and ends at the
        # next group, the amount of the layer group must not be used
        (
            [(VS, 0), ("heightOfBaseOfCloud", 2500.0), (VS, 1), ("cloudAmount", 7), ("heightOfBaseOfCloud", 900.0)],
            (None, 2500.0, [], "m"),
        ),
        # missing vertical significance (template 307092): the first group ends at the
        # second significance key, like with vertical significance 0
        (
            [(VS, None), ("cloudAmount", 8), ("heightOfBaseOfCloud", 240.0), (VS, None), ("cloudAmount", 3)],
            (8, 240.0, [], "m"),
        ),
        # no vertical significance key at all: the first occurrence of each key is the summary
        (
            [("cloudAmount", 5), ("heightOfBaseOfCloud", 1000.0), ("cloudType", 30)],
            (5, 1000.0, [30], "m"),
        ),
        # a repeated cloudAmount without a significance key starts a new group
        (
            [("cloudAmount", 2), ("heightOfBaseOfCloud", 600.0), ("cloudAmount", 3)],
            (2, 600.0, [], "m"),
        ),
        # empty subset
        ([], (None, None, [], None)),
    ],
)
def test_scan_cloud_summary(values, expected):
    """Unit test of the cloud summary group selection with a fake key sequence."""
    collector = _FakeSubsetCollector(values, units={"heightOfBaseOfCloud": "m"})
    assert _scan_cloud_summary(collector) == expected


def test_scan_cloud_summary_base_units():
    """The cloud base units are read from the heightOfBaseOfCloud key of the summary group."""
    # a cloud layer before the summary group must not shift the lookup to its key
    values = [(VS, 1), ("heightOfBaseOfCloud", 100.0), (VS, 7), ("heightOfBaseOfCloud", 600.0)]
    units = {"#1#heightOfBaseOfCloud->units": "ft", "#2#heightOfBaseOfCloud->units": "m"}
    collector = _FakeSubsetCollector(values, units=units)
    assert _scan_cloud_summary(collector) == (None, 600.0, [], "m")

    # without units information in the message the cloud base units are None
    collector = _FakeSubsetCollector(values, units={})
    assert _scan_cloud_summary(collector) == (None, 600.0, [], None)
