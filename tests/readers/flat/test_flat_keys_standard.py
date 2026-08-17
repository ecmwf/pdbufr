# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import datetime

import numpy as np
import pytest

import pdbufr
from pdbufr.utils.testing import sample_test_data_path

pd = pytest.importorskip("pandas")

TEST_DATA_1 = sample_test_data_path("obs_3day.bufr")


def _compare_df(df, num_rows, ref_rows, ref):
    assert len(df) == num_rows

    if num_rows > 0:
        assert list(df.columns) == list(ref[0].keys())
        # assert len(df) == num_rows

        # assert .iloc[0].to_dict() == names[0], res.iloc[0].to_dict()
        # assert res.iloc[2].to_dict() == names[1], res.iloc[2].to_dict()
        df_ref = pd.DataFrame.from_dict(ref)
        df_ref.reset_index(drop=True, inplace=True)

        df = df.replace(np.nan, None)
        # df = df.reset_index(drop=True)
        df = df.iloc[ref_rows].reset_index(drop=True)

        print("df=", df)
        print("df_ref=", df_ref)

        try:
            pd.testing.assert_frame_equal(
                df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
            )
        except Exception as e:
            print("e=", e)
            raise


@pytest.mark.parametrize("prefilter_headers", [False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {"columns": ["dataSubCategory", "ident", "typical_datetime"]},
            50,
            [0, 2],
            [
                {
                    "dataSubCategory": 1,
                    "ident": "03894",
                    "typical_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000"),
                },
                {
                    "dataSubCategory": 1,
                    "ident": "03379",
                    "typical_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000"),
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_standard_core_header(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_1, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {"columns": ["latitude", "longitude"]},
            50,
            [0, 2],
            [{"latitude": 49.43, "longitude": -2.6}, {"latitude": 53.03, "longitude": -0.5}],
        ),
        (
            {"columns": ["#1#latitude", "#1#longitude", "#1#cloudType", "#3#cloudType"]},
            50,
            [0, 2],
            [
                {"#1#latitude": 49.43, "#1#longitude": -2.6, "#1#cloudType": 32, "#3#cloudType": 11},
                {"#1#latitude": 53.03, "#1#longitude": -0.5, "#1#cloudType": 38, "#3#cloudType": 60},
            ],
        ),
        (
            {"columns": ["data_datetime"]},
            50,
            [0, 2],
            [
                {"data_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000")},
                {"data_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000")},
            ],
        ),
        (
            {"columns": ["#1#cloudType", "#8#cloudType"], "required_columns": ["#1#cloudType"]},
            50,
            [0, 2],
            [
                {"#1#cloudType": 32, "#8#cloudType": None},
                {"#1#cloudType": 38, "#8#cloudType": None},
            ],
        ),
        (
            {"columns": "~cloudType"},
            50,
            [0, 2],
            [
                {
                    "#1#cloudType": 32,
                    "#2#cloudType": 20,
                    "#3#cloudType": 11,
                    "#4#cloudType": 8,
                    "#5#cloudType": None,
                    "#6#cloudType": None,
                    "#7#cloudType": None,
                },
                {
                    "#1#cloudType": 38,
                    "#2#cloudType": 61,
                    "#3#cloudType": 60,
                    "#4#cloudType": 8,
                    "#5#cloudType": 6,
                    "#6#cloudType": None,
                    "#7#cloudType": None,
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_standard_core_data(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_1, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {"columns": ["ident", "cloudType"]},
            50,
            [0, 2],
            [
                {"ident": "03894", "cloudType": 32},
                {"ident": "03379", "cloudType": 38},
            ],
        ),
        (
            {"columns": ["ident", "#1#cloudType"]},
            50,
            [0, 2],
            [
                {"ident": "03894", "#1#cloudType": 32},
                {"ident": "03379", "#1#cloudType": 38},
            ],
        ),
    ],
)
def test_read_flat_bufr_key_standard_core_mixed(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_1, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {"columns": ["latitude", "longitude", "data_datetime"], "filters": {"ident": ["03894", "03379"]}},
            2,
            [
                0,
                1,
            ],
            [
                {
                    "latitude": 49.43,
                    "longitude": -2.6,
                    "data_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000"),
                    "ident": "03894",
                },
                {
                    "latitude": 53.03,
                    "longitude": -0.5,
                    "data_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000"),
                    "ident": "03379",
                },
            ],
        ),
        (
            {
                "columns": ["latitude", "longitude", "data_datetime"],
                "filters": {
                    "ident": ["03894", "03379"],
                    "data_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000"),
                },
                "filter_columns": False,
            },
            2,
            [
                0,
                1,
            ],
            [
                {
                    "latitude": 49.43,
                    "longitude": -2.6,
                    "data_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000"),
                },
                {
                    "latitude": 53.03,
                    "longitude": -0.5,
                    "data_datetime": datetime.datetime.fromisoformat("2017-04-25T12:00:00.000"),
                },
            ],
        ),
        (
            {"columns": ["latitude", "longitude"], "filters": {"#1#cloudType": 35, "#2#cloudType": 27}},
            2,
            [
                0,
                1,
            ],
            [
                {
                    "latitude": 48.72,
                    "longitude": 2.38,
                    "#1#cloudType": 35,
                    "#2#cloudType": 27,
                },
                {
                    "latitude": 48.77,
                    "longitude": 2.01,
                    "#1#cloudType": 35,
                    "#2#cloudType": 27,
                },
            ],
        ),
        (
            {"columns": ["latitude", "longitude", "ident"], "filters": {"~cloudType": 62}},
            3,
            [
                0,
                1,
                2,
            ],
            [
                {"latitude": 55.68, "longitude": -6.25, "ident": "03105"},
                {"latitude": 53.22, "longitude": 3.22, "ident": "06252"},
                {"latitude": 51.44, "longitude": 3.60, "ident": "06310"},
            ],
        ),
    ],
)
def test_read_flat_bufr_key_standard_filters(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_1, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    _compare_df(df, num_rows, ref_rows, ref)
