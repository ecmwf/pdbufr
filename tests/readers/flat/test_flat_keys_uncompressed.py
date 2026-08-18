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

TEST_DATA_2 = sample_test_data_path("synop_multi_subset_uncompressed.bufr")


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
def test_read_flat_bufr_key_uncompressed_core_header(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    """Use only header section keys."""
    df = pdbufr.read_bufr(TEST_DATA_2, flat=True, **_kwargs, prefilter_headers=prefilter_headers)
    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [True, False])
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
        (
            {
                "columns": [
                    "latitude",
                    "longitude",
                    "data_datetime",
                    "WMO_station_id",
                    "~cloudType",
                    "~heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
                ]
            },
            12,
            [0, 2, 11],
            [
                {
                    "latitude": 69.6523,
                    "longitude": 18.9057,
                    "data_datetime": datetime.datetime.fromisoformat("2015-01-26T10:00:00.000"),
                    "WMO_station_id": 1027,
                    "#1#cloudType": None,
                    "#2#cloudType": None,
                    "#3#cloudType": None,
                    "#1#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#2#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                    "#3#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#4#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                    "#5#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#6#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#7#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#8#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                },
                {
                    "latitude": 63.4882,
                    "longitude": 10.8795,
                    "data_datetime": datetime.datetime.fromisoformat("2015-01-26T10:00:00.000"),
                    "WMO_station_id": 1270,
                    "#1#cloudType": None,
                    "#2#cloudType": None,
                    "#3#cloudType": None,
                    "#1#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#2#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                    "#3#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#4#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                    "#5#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#6#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#7#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#8#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                },
                {
                    "latitude": 59.6193,
                    "longitude": 10.215,
                    "data_datetime": datetime.datetime.fromisoformat("2015-01-26T10:00:00.000"),
                    "WMO_station_id": 1485,
                    "#1#cloudType": None,
                    "#2#cloudType": None,
                    "#3#cloudType": None,
                    "#1#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#2#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                    "#3#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#4#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                    "#5#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#6#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2.0,
                    "#7#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 10.0,
                    "#8#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": None,
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_uncompressed_core_data(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    """Use only data section keys."""
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
def test_read_flat_bufr_key_uncompressed_core_mixed(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    """Use both header and data section keys."""
    df = pdbufr.read_bufr(TEST_DATA_2, flat=True, **_kwargs, prefilter_headers=prefilter_headers)
    _compare_df(df, num_rows, ref_rows, ref)


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,num_rows,ref_rows,ref",
    [
        (
            {
                "columns": ["latitude", "longitude", "stationNumber", "airTemperature"],
                "filters": {"airTemperature": slice(276, None)},
            },
            4,
            [0],
            [
                {"latitude": 69.6523, "longitude": 18.9057, "stationNumber": 27, "airTemperature": 276.45},
            ],
        ),
        (
            {
                "columns": ["latitude", "longitude", "stationNumber"],
                "filters": {"airTemperature": slice(276, None)},
            },
            4,
            [0],
            [
                {"latitude": 69.6523, "longitude": 18.9057, "stationNumber": 27, "airTemperature": 276.45},
            ],
        ),
        (
            {
                "columns": ["latitude", "longitude", "stationNumber"],
                "filters": {"~airTemperature": slice(276, None)},
            },
            4,
            [0],
            [
                {
                    "latitude": 69.6523,
                    "longitude": 18.9057,
                    "stationNumber": 27,
                },
            ],
        ),
    ],
)
def test_read_flat_bufr_key_uncompressed_filters(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_2, flat=True, **_kwargs, prefilter_headers=prefilter_headers)
    _compare_df(df, num_rows, ref_rows, ref)
