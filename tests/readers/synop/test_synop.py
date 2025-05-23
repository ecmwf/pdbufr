# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import numpy as np
import pandas as pd

import pdbufr
from pdbufr.utils.testing import sample_test_data_path


def _get_data():
    import os
    import sys

    here = os.path.dirname(__file__)
    sys.path.insert(0, here)
    import _data

    return _data


DATA = _get_data()


def test_synop_reader():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"),
        reader="synop",
        add_level_columns=False,
        add_units_columns=False,
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

    # print("df=", df.columns.tolist())
    # print("df_ref=", df_ref.columns.tolist())

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_columns_user_1():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"), reader="synop", filters={"count": 1}, columns=["t2m"]
    )

    df_ref = pd.DataFrame.from_dict(DATA.REF_PARAMS_1)
    df_ref.reset_index(drop=True, inplace=True)

    df = df.replace(np.nan, None)

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise


def test_synop_columns_user_2():
    df = pdbufr.read_bufr(
        sample_test_data_path("syn_new.bufr"), reader="synop", filters={"count": 1}, columns=["t2m", "rh2m"]
    )

    df_ref = pd.DataFrame.from_dict(DATA.REF_PARAMS_2)
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
        add_level_columns=False,
        add_units_columns=False,
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
        add_level_columns=False,
        add_units_columns=True,
        units={"mslp": "hPa", "td2m": "degC", "t2m": "degF"},
    )

    ref = {"mslp": 1013.2, "td2m": 22.000000000000057, "t2m": 81.13999999999996}

    for k, v in ref.items():
        assert np.isclose(df[k][0], v), f"{k}={df[k][0]} != {v}"

    ref = {"mslp_units": "hPa", "td2m_units": "degC", "t2m_units": "degF"}
    for k, v in ref.items():
        assert df[k][0] == v, f"{k}={df[k][0]} != {v}"
