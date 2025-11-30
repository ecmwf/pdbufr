# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import datetime
import os

import numpy as np
import pytest

import pdbufr
from pdbufr.utils.testing import reference_test_data_path
from pdbufr.utils.testing import sample_test_data_path

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")

TEST_DATA_1 = sample_test_data_path("obs_3day.bufr")
TEST_DATA_2 = sample_test_data_path("synop_multi_subset_uncompressed.bufr")

# contains 1 message - with 51 compressed subsets with multiple timePeriods
TEST_DATA_9 = sample_test_data_path("ens_multi_subset_compressed.bufr")

# contains 1 message - with 128 compressed subsets with some str values
TEST_DATA_10 = sample_test_data_path("pgps_110.bufr")

REF_DATA_1 = reference_test_data_path("obs_3day_ref_1.csv")
REF_DATA_2 = reference_test_data_path("synop_uncompressed_ref_1.csv")


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
            {"columns": ["#1#cloudType", "#8#cloudType"]},
            0,
            [],
            [],
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


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {"columns": ["dataSubCategory", "typical_datetime"]},
            1,
            [0],
            [
                {
                    "dataSubCategory": 0,
                    "typical_datetime": datetime.datetime.fromisoformat("2018-07-01T12:00:00.000"),
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_compressed_core_header(
    prefilter_headers, _kwargs, num_rows, ref_rows, ref
) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_9, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {
                "columns": ["latitude", "longitude", "ensembleMemberNumber", "timePeriod", "cape"],
            },
            51,
            [0, 2],
            [
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "ensembleMemberNumber": 0,
                    "timePeriod": 0,
                    "cape": 0.1,
                },
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "ensembleMemberNumber": 2,
                    "timePeriod": 0,
                    "cape": 41.9,
                },
            ],
        ),
        (
            {
                "columns": ["longitude", "latitude", "cape", "ensembleMemberNumber", "timePeriod"],
            },
            51,
            [0, 2],
            [
                {
                    "longitude": 0.97,
                    "latitude": 51.52,
                    "cape": 0.1,
                    "ensembleMemberNumber": 0,
                    "timePeriod": 0,
                },
                {
                    "longitude": 0.97,
                    "latitude": 51.52,
                    "cape": 41.9,
                    "ensembleMemberNumber": 2,
                    "timePeriod": 0,
                },
            ],
        ),
        (
            {
                "columns": ["latitude", "longitude", "#1#ensembleMemberNumber", "#1#timePeriod", "#1#cape"],
            },
            51,
            [0, 2],
            [
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "#1#ensembleMemberNumber": 0,
                    "#1#timePeriod": 0,
                    "#1#cape": 0.1,
                },
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "#1#ensembleMemberNumber": 2,
                    "#1#timePeriod": 0,
                    "#1#cape": 41.9,
                },
            ],
        ),
        (
            {
                "columns": ["latitude", "longitude", "#1#ensembleMemberNumber", "#4#timePeriod", "#4#cape"],
            },
            51,
            [0, 2],
            [
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "#1#ensembleMemberNumber": 0,
                    "#4#timePeriod": 18,
                    "#4#cape": 0,
                },
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "#1#ensembleMemberNumber": 2,
                    "#4#timePeriod": 18,
                    "#4#cape": 0,
                },
            ],
        ),
        (
            {
                "columns": [
                    "latitude",
                    "longitude",
                    "#1#ensembleMemberNumber",
                    "#4#timePeriod",
                    "#4#cape",
                    "#10#timePeriod",
                    "#10#cape",
                ],
            },
            51,
            [0, 2],
            [
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "#1#ensembleMemberNumber": 0,
                    "#4#timePeriod": 18,
                    "#4#cape": 0,
                    "#10#timePeriod": 54,
                    "#10#cape": 0,
                },
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "#1#ensembleMemberNumber": 2,
                    "#4#timePeriod": 18,
                    "#4#cape": 0,
                    "#10#timePeriod": 54,
                    "#10#cape": 0.6,
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_compressed_core_data(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_9, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {
                "columns": [
                    "dataSubCategory",
                    "typical_datetime",
                    "longitude",
                    "latitude",
                    "cape",
                    "ensembleMemberNumber",
                    "timePeriod",
                ],
            },
            51,
            [0, 2],
            [
                {
                    "dataSubCategory": 0,
                    "typical_datetime": datetime.datetime.fromisoformat("2018-07-01T12:00:00.000"),
                    "longitude": 0.97,
                    "latitude": 51.52,
                    "cape": 0.1,
                    "ensembleMemberNumber": 0,
                    "timePeriod": 0,
                },
                {
                    "dataSubCategory": 0,
                    "typical_datetime": datetime.datetime.fromisoformat("2018-07-01T12:00:00.000"),
                    "longitude": 0.97,
                    "latitude": 51.52,
                    "cape": 41.9,
                    "ensembleMemberNumber": 2,
                    "timePeriod": 0,
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_compressed_core_mixed(
    prefilter_headers, _kwargs, num_rows, ref_rows, ref
) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_9, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {
                "columns": ["latitude", "longitude", "ensembleMemberNumber", "timePeriod", "cape"],
                "filters": {"ensembleMemberNumber": [0, 2]},
            },
            2,
            [0, 1],
            [
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "ensembleMemberNumber": 0,
                    "timePeriod": 0,
                    "cape": 0.1,
                },
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "ensembleMemberNumber": 2,
                    "timePeriod": 0,
                    "cape": 41.9,
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_compressed_filters(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_9, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {"columns": ["dataSubCategory", "typical_datetime"]},
            1,
            [0],
            [
                {
                    "dataSubCategory": 0,
                    "typical_datetime": datetime.datetime.fromisoformat("2015-01-26T10:00:00.000"),
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_uncompressed_core_header(
    prefilter_headers, _kwargs, num_rows, ref_rows, ref
) -> None:
    """Use only header section keys"""
    df = pdbufr.read_bufr(TEST_DATA_2, flat=True, **_kwargs, prefilter_headers=prefilter_headers)
    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {
                "columns": ["latitude", "longitude", "stationNumber", "#1#airTemperature"],
            },
            12,
            [0, 2],
            [
                {
                    "latitude": 69.6523,
                    "longitude": 18.9057,
                    "stationNumber": 27,
                    "#1#airTemperature": 276.45,
                },
                {
                    "latitude": 63.4882,
                    "longitude": 10.8795,
                    "stationNumber": 270,
                    "#1#airTemperature": 275.25,
                },
            ],
        ),
        (
            {
                "columns": ["longitude", "latitude", "stationNumber", "#1#airTemperature"],
            },
            12,
            [0, 2],
            [
                {
                    "longitude": 18.9057,
                    "latitude": 69.6523,
                    "stationNumber": 27,
                    "#1#airTemperature": 276.45,
                },
                {
                    "longitude": 10.8795,
                    "latitude": 63.4882,
                    "stationNumber": 270,
                    "#1#airTemperature": 275.25,
                },
            ],
        ),
        (
            {
                "columns": [
                    "#1#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
                    "#6#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
                    "#6#timePeriod",
                    "#7#timePeriod",
                    "#1#maximumTemperatureAtHeightAndOverPeriodSpecified",
                    "#7#timePeriod",
                ],
            },
            12,
            [0, 2],
            [
                {
                    "#1#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2,
                    "#6#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2,
                    "#6#timePeriod": -1,
                    "#7#timePeriod": 0,
                    "#1#maximumTemperatureAtHeightAndOverPeriodSpecified": 276.55,
                },
                {
                    "#1#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2,
                    "#6#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2,
                    "#6#timePeriod": -1,
                    "#7#timePeriod": 0,
                    "#1#maximumTemperatureAtHeightAndOverPeriodSpecified": 275.65,
                },
            ],
        ),
        (
            {"columns": ["latitude", "longitude", "data_datetime", "WMO_station_id"]},
            12,
            [0, 2, 11],
            [
                {
                    "latitude": 69.6523,
                    "longitude": 18.9057,
                    "data_datetime": datetime.datetime.fromisoformat("2015-01-26T10:00:00.000"),
                    "WMO_station_id": 1027,
                },
                {
                    "latitude": 63.4882,
                    "longitude": 10.8795,
                    "data_datetime": datetime.datetime.fromisoformat("2015-01-26T10:00:00.000"),
                    "WMO_station_id": 1270,
                },
                {
                    "latitude": 59.6193,
                    "longitude": 10.215,
                    "data_datetime": datetime.datetime.fromisoformat("2015-01-26T10:00:00.000"),
                    "WMO_station_id": 1485,
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_uncompressed_core_data(
    prefilter_headers, _kwargs, num_rows, ref_rows, ref
) -> None:
    """Use only data section keys"""
    df = pdbufr.read_bufr(TEST_DATA_2, flat=True, **_kwargs, prefilter_headers=prefilter_headers)
    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {
                "columns": ["latitude", "longitude", "dataSubCategory", "stationNumber", "#1#airTemperature"],
            },
            12,
            [0, 2, 11],
            [
                {
                    "latitude": 69.6523,
                    "longitude": 18.9057,
                    "dataSubCategory": 0,
                    "stationNumber": 27,
                    "#1#airTemperature": 276.45,
                },
                {
                    "latitude": 63.4882,
                    "longitude": 10.8795,
                    "dataSubCategory": 0,
                    "stationNumber": 270,
                    "#1#airTemperature": 275.25,
                },
                {
                    "latitude": 59.6193,
                    "longitude": 10.215,
                    "dataSubCategory": 0,
                    "stationNumber": 485,
                    "#1#airTemperature": 275.45,
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_uncompressed_core_mixed(
    prefilter_headers, _kwargs, num_rows, ref_rows, ref
) -> None:
    """Use both header and data section keys"""
    df = pdbufr.read_bufr(TEST_DATA_2, flat=True, **_kwargs, prefilter_headers=prefilter_headers)
    print(df)
    _compare_df(df, num_rows, ref_rows, ref)
