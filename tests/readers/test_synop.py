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

import pdbufr
from pdbufr.utils.testing import sample_test_data_path

REF = [
    {
        "sid": 91948,
        "lat": -23.13017,
        "lon": -134.96533,
        "elevation": 91.0,
        "time": datetime.datetime.fromisoformat("2020-03-15T00:00:00.000"),
        "t2m": 300.45,
        "rh2m": 73,
        "td2m": 295.15,
        "wspeed10m": 1.6,
        "wdir10m": 100,
        "wspeedgust_10min": 5.3,
        "wdirgust_10min": 110.0,
        "wspeedgust_60min": 5.3,
        "wdirgust_60min": 110.0,
        "wspeedgust_360min": 7.6,
        "wdirgust_360min": 130.0,
        "present_weather": 2,
        "precipitation_1h": 0.0,
        "precipitation_3h": 0.0,
        "precipitation_6h": 0.0,
        "precipitation_12h": 0.0,
        "precipitation_24h": 0.0,
        "min_t2m_60min": None,
        "min_t2m_0h": 296.45,
        "max_t2m_60min": 300.75,
        "max_t2m_nan": None,
        "mslp": 101320.0,
        "cloud_cover": 25.0,
        "snow_depth": None,
        "max_t2m_0h": None,
        "visibility": None,
        "wspeedgust_nan": None,
        "wdirgust_nan": None,
        "wspeedgust_720min": None,
        "wdirgust_720min": None,
    },
    {
        "sid": 11766,
        "lat": 49.77722,
        "lon": 17.54194,
        "elevation": 748.1,
        "time": datetime.datetime.fromisoformat("2020-03-15T00:00:00.000"),
        "t2m": 269.25,
        "rh2m": 65,
        "td2m": 263.55,
        "wspeed10m": 4.0,
        "wdir10m": 60.0,
        "wspeedgust_10min": None,
        "wdirgust_10min": None,
        "wspeedgust_60min": None,
        "wdirgust_60min": None,
        "wspeedgust_360min": None,
        "wdirgust_360min": None,
        "present_weather": 508,
        "precipitation_1h": 0.0,
        "precipitation_3h": None,
        "precipitation_6h": 0.0,
        "precipitation_12h": None,
        "precipitation_24h": None,
        "min_t2m_60min": None,
        "min_t2m_0h": None,
        "max_t2m_60min": None,
        "max_t2m_nan": None,
        "mslp": None,
        "cloud_cover": None,
        "snow_depth": None,
        "max_t2m_0h": None,
        "visibility": 30000.0,
        "wspeedgust_nan": None,
        "wdirgust_nan": None,
        "wspeedgust_720min": None,
        "wdirgust_720min": None,
    },
    {
        "sid": 56257,
        "lat": 30.0,
        "lon": 100.27,
        "elevation": 3950.0,
        "time": datetime.datetime.fromisoformat("2020-03-15T00:00:00.000"),
        "t2m": 276.35,
        "rh2m": 37,
        "td2m": 263.05,
        "wspeed10m": 2.5,
        "wdir10m": 229.0,
        "wspeedgust_10min": None,
        "wdirgust_10min": None,
        "wspeedgust_60min": None,
        "wdirgust_60min": None,
        "wspeedgust_360min": None,
        "wdirgust_360min": None,
        "present_weather": 0,
        "precipitation_1h": None,
        "precipitation_3h": None,
        "precipitation_6h": 0.0,
        "precipitation_12h": 0.0,
        "precipitation_24h": 0.0,
        "min_t2m_60min": None,
        "min_t2m_0h": 272.65,
        "max_t2m_60min": None,
        "max_t2m_nan": None,
        "mslp": 100440.0,
        "cloud_cover": 0.0,
        "snow_depth": 0.0,
        "max_t2m_0h": 288.35,
        "visibility": 30000.0,
        "wspeedgust_nan": None,
        "wdirgust_nan": None,
        "wspeedgust_720min": 8.9,
        "wdirgust_720min": 193.0,
    },
]

REF_PARAMS_1 = [
    {
        "sid": 91948,
        "lat": -23.13017,
        "lon": -134.96533,
        "elevation": 91.0,
        "time": datetime.datetime.fromisoformat("2020-03-15T00:00:00.000"),
        "t2m": 300.45,
    }
]

REF_PARAMS_2 = [
    {
        "sid": 91948,
        "lat": -23.13017,
        "lon": -134.96533,
        "elevation": 91.0,
        "time": datetime.datetime.fromisoformat("2020-03-15T00:00:00.000"),
        "t2m": 300.45,
        "rh2m": 73,
    }
]


def test_synop_reader():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"), reader="synop", add_level=False, add_units=False
    )

    # r = df.to_dict()
    # print("r=", r)
    # print("r=", type(r["time"][0]))

    # # assert False

    # use this to create ref
    # r = df.to_json(date_format="iso", orient="records")
    # parsed = json.loads(r)
    # print("parsed=", parsed)

    df_ref = pd.DataFrame.from_dict(REF)
    df_ref.reset_index(drop=True, inplace=True)

    df = df.replace(np.nan, None)

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_params_1():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"), reader="synop", filters={"count": 1}, params=["t2m"]
    )

    df_ref = pd.DataFrame.from_dict(REF_PARAMS_1)
    df_ref.reset_index(drop=True, inplace=True)

    df = df.replace(np.nan, None)

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_params_2():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"), reader="synop", filters={"count": 1}, params=["t2m", "rh2m"]
    )

    df_ref = pd.DataFrame.from_dict(REF_PARAMS_2)
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
        add_level=False,
        add_units=False,
        units={"mslp": "hPa", "td2m": "degC", "t2m": "degF"},
    )

    ref = {"mslp": 1013.2, "td2m": 22.000000000000057, "t2m": -459.49}

    for k, v in ref.items():
        assert np.isclose(df[k][0], v), f"{k}={df[k][0]} != {v}"

    for k in ref:
        assert f"{k}_units" not in df, f"{k}_units should not be in df"


def test_synop_units_2():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        filters={"count": 1},
        add_level=False,
        add_units=True,
        units={"mslp": "hPa", "td2m": "degC", "t2m": "degF"},
    )

    ref = {"mslp": 1013.2, "td2m": 22.000000000000057, "t2m": -459.49}

    for k, v in ref.items():
        assert np.isclose(df[k][0], v), f"{k}={df[k][0]} != {v}"

    ref = {"mslp_units": "hPa", "td2m_units": "degC", "t2m_units": "degF"}
    for k, v in ref.items():
        assert df[k][0] == v, f"{k}={df[k][0]} != {v}"
