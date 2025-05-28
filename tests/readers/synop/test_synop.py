# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import datetime

import numpy as np
import pandas as pd
import pytest

import pdbufr
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

    df = df.replace(np.nan, None)

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
            ["station", "wgust"],
            {
                "wgust_speed_10min": 5.3,
                "wgust_dir_10min": 110.0,
                "wgust_speed_60min": 5.3,
                "wgust_dir_60min": 110.0,
                "wgust_speed_360min": 7.6,
                "wgust_dir_360min": 130.0,
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
        "stnid": 91948,
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
            ["wgust"],
            {
                "wgust_speed_10min": 5.3,
                "wgust_dir_10min": 110.0,
                "wgust_speed_10min_level": 10,
                "wgust_dir_10min_level": 10,
                "wgust_speed_60min": 5.3,
                "wgust_dir_60min": 110.0,
                "wgust_speed_60min_level": 10,
                "wgust_dir_60min_level": 10,
                "wgust_speed_360min": 7.6,
                "wgust_dir_360min": 130.0,
                "wgust_speed_360min_level": 10,
                "wgust_dir_360min_level": 10,
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
            ["wgust"],
            {
                "wgust_speed_10min": 5.3,
                "wgust_dir_10min": 110.0,
                "wgust_speed_10min_units": "m/s",
                "wgust_dir_10min_units": "deg",
                "wgust_speed_60min": 5.3,
                "wgust_dir_60min": 110.0,
                "wgust_speed_60min_units": "m/s",
                "wgust_dir_60min_units": "deg",
                "wgust_speed_360min": 7.6,
                "wgust_dir_360min": 130.0,
                "wgust_speed_360min_units": "m/s",
                "wgust_dir_360min_units": "deg",
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
            ["wgust"],
            {
                "wgust_speed_10min": 5.3,
                "wgust_dir_10min": 110.0,
                "wgust_speed_10min_units": "m/s",
                "wgust_dir_10min_units": "deg",
                "wgust_speed_10min_level": 10,
                "wgust_dir_10min_level": 10,
                "wgust_speed_60min": 5.3,
                "wgust_dir_60min": 110.0,
                "wgust_speed_60min_units": "m/s",
                "wgust_dir_60min_units": "deg",
                "wgust_speed_60min_level": 10,
                "wgust_dir_60min_level": 10,
                "wgust_speed_360min": 7.6,
                "wgust_dir_360min": 130.0,
                "wgust_speed_360min_units": "m/s",
                "wgust_dir_360min_units": "deg",
                "wgust_speed_360min_level": 10,
                "wgust_dir_360min_level": 10,
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
