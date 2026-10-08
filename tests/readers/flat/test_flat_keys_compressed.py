# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import datetime

import pytest
from flat_fixtures import compare_df

import pdbufr
from pdbufr.utils.testing import sample_test_data_path

pd = pytest.importorskip("pandas")

# contains 1 message - with 51 compressed subsets with multiple timePeriods
TEST_DATA_9 = sample_test_data_path("ens_multi_subset_compressed.bufr")


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
def test_read_flat_bufr_key_compressed_core_header(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_9, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    compare_df(df, num_rows, ref_rows, ref)


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
        (
            {
                "columns": [
                    "latitude",
                    "longitude",
                    "#1#ensembleMemberNumber",
                    "~cape",
                ],
            },
            51,
            [0, 2],
            [
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "#1#ensembleMemberNumber": 0,
                    "#1#cape": 0.1,
                    "#2#cape": 147.0,
                    "#3#cape": 6.4,
                    "#4#cape": 0.0,
                    "#5#cape": 0.0,
                    "#6#cape": 0.0,
                    "#7#cape": 0.0,
                    "#8#cape": 0.0,
                    "#9#cape": 0.4,
                    "#10#cape": 0.0,
                    "#11#cape": 2.8,
                    "#12#cape": 3.7,
                    "#13#cape": 0.1,
                    "#14#cape": 0.3,
                    "#15#cape": 0.0,
                    "#16#cape": 0.0,
                    "#17#cape": 0.0,
                    "#18#cape": 0.0,
                    "#19#cape": 0.0,
                    "#20#cape": 1.3,
                    "#21#cape": 0.0,
                    "#22#cape": 0.0,
                    "#23#cape": 0.0,
                    "#24#cape": 0.0,
                    "#25#cape": 0.0,
                    "#26#cape": 0.0,
                    "#27#cape": 0.0,
                    "#28#cape": 0.0,
                    "#29#cape": 0.0,
                    "#30#cape": 0.0,
                    "#31#cape": 0.0,
                    "#32#cape": 0.0,
                    "#33#cape": 0.0,
                    "#34#cape": 0.0,
                    "#35#cape": 0.0,
                    "#36#cape": 0.0,
                    "#37#cape": 0.0,
                    "#38#cape": 0.0,
                    "#39#cape": 0.0,
                    "#40#cape": 0.0,
                    "#41#cape": 0.0,
                    "#42#cape": 0.0,
                    "#43#cape": 0.0,
                    "#44#cape": 0.0,
                    "#45#cape": 0.0,
                    "#46#cape": 0.0,
                    "#47#cape": 6.6,
                    "#48#cape": 54.1,
                    "#49#cape": 87.9,
                    "#50#cape": 291.2,
                    "#51#cape": 264.7,
                    "#52#cape": 138.8,
                    "#53#cape": 56.6,
                    "#54#cape": 112.5,
                    "#55#cape": 20.4,
                    "#56#cape": 32.0,
                    "#57#cape": 76.8,
                    "#58#cape": 0.1,
                    "#59#cape": 2.9,
                    "#60#cape": 11.4,
                    "#61#cape": 5.2,
                },
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "#1#ensembleMemberNumber": 2,
                    "#1#cape": 41.9,
                    "#2#cape": 174.2,
                    "#3#cape": 52.5,
                    "#4#cape": 0.0,
                    "#5#cape": 0.0,
                    "#6#cape": 0.0,
                    "#7#cape": 0.0,
                    "#8#cape": 0.2,
                    "#9#cape": 1.0,
                    "#10#cape": 0.6,
                    "#11#cape": 119.6,
                    "#12#cape": 30.7,
                    "#13#cape": 229.2,
                    "#14#cape": 77.7,
                    "#15#cape": 0.0,
                    "#16#cape": 0.0,
                    "#17#cape": 0.0,
                    "#18#cape": 0.1,
                    "#19#cape": 0.0,
                    "#20#cape": 0.0,
                    "#21#cape": 0.2,
                    "#22#cape": 0.0,
                    "#23#cape": 0.1,
                    "#24#cape": 0.0,
                    "#25#cape": 0.0,
                    "#26#cape": 0.0,
                    "#27#cape": 0.0,
                    "#28#cape": 0.0,
                    "#29#cape": 0.0,
                    "#30#cape": 0.0,
                    "#31#cape": 19.7,
                    "#32#cape": 4.5,
                    "#33#cape": 2.7,
                    "#34#cape": 0.0,
                    "#35#cape": 0.0,
                    "#36#cape": 0.0,
                    "#37#cape": 3.3,
                    "#38#cape": 0.1,
                    "#39#cape": 0.0,
                    "#40#cape": 0.1,
                    "#41#cape": 0.2,
                    "#42#cape": 0.0,
                    "#43#cape": 0.0,
                    "#44#cape": 0.0,
                    "#45#cape": 0.0,
                    "#46#cape": 0.0,
                    "#47#cape": 0.0,
                    "#48#cape": 15.2,
                    "#49#cape": 5.6,
                    "#50#cape": 0.0,
                    "#51#cape": 0.0,
                    "#52#cape": 0.0,
                    "#53#cape": 4.1,
                    "#54#cape": 0.0,
                    "#55#cape": 2.6,
                    "#56#cape": 4.3,
                    "#57#cape": 119.2,
                    "#58#cape": 92.5,
                    "#59#cape": 0.6,
                    "#60#cape": 0.7,
                    "#61#cape": 0.0,
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

    compare_df(df, num_rows, ref_rows, ref)


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
def test_read_flat_bufr_key_compressed_core_mixed(prefilter_headers, _kwargs, num_rows, ref_rows, ref) -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    df = pdbufr.read_bufr(TEST_DATA_9, flat=True, **_kwargs, prefilter_headers=prefilter_headers)

    compare_df(df, num_rows, ref_rows, ref)


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
        (
            {
                "columns": ["latitude", "longitude", "ensembleMemberNumber", "timePeriod", "cape"],
                "filters": {"ensembleMemberNumber": [0, 2], "~cape": slice(250, None)},
            },
            1,
            [0],
            [
                {
                    "latitude": 51.52,
                    "longitude": 0.97,
                    "ensembleMemberNumber": 0,
                    "timePeriod": 0,
                    "cape": 0.1,
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

    # print("df=", df)
    compare_df(df, num_rows, ref_rows, ref)
