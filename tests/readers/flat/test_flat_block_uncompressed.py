# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import numpy as np
import pytest

import pdbufr
from pdbufr.utils.testing import reference_test_data_path, sample_test_data_path

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

TEST_DATA_2 = sample_test_data_path("synop_multi_subset_uncompressed.bufr")

REF_DATA_2 = reference_test_data_path("synop_uncompressed_ref_1.csv")


@pytest.mark.parametrize("prefilter_headers", [False, True])
@pytest.mark.parametrize(
    "_kwargs,ref_rownum, ref_colnum, ref_keys_include, ref_keys_exclude, ref_value_checks",
    [
        # all columns without filters
        (
            {"columns": "all"},
            12,
            101,
            ["edition", "#1#latitude"],
            [],
            [],
        ),
        # all columns with required_columns
        (
            {"columns": "all", "required_columns": ["airTemperature"]},
            12,
            101,
            ["edition", "#1#latitude", "#1#airTemperature"],
            [],
            [],
        ),
        # data with required_columns
        (
            {"columns": "data", "required_columns": ["airTemperature"]},
            12,
            80,
            ["#1#latitude", "#1#airTemperature"],
            ["edition"],
            [],
        ),
        # data with required_columns (edition does appear in data)
        (
            {"columns": "data", "required_columns": ["edition", "airTemperature"]},
            12,
            81,
            ["edition", "#1#latitude", "#1#airTemperature"],
            [],
            [],
        ),
        # data with invalid required_columns (empty result)
        (
            {"columns": "data", "required_columns": ["xyz", "airTemperature"]},
            0,
            0,
            [],
            [],
            [],
        ),
        # header with required_columns
        (
            {"columns": "header", "required_columns": ["edition", "airTemperature"]},
            12,
            22,
            ["edition", "#1#airTemperature"],
            ["#1#latitude"],
            [],
        ),
        # header filter
        (
            {"columns": "all", "filters": {"observedData": 1}},
            12,
            101,
            ["edition", "#1#latitude"],
            [],
            [],
        ),
        # data filter single value
        (
            {"columns": "all", "filters": {"stationNumber": 27}},
            1,
            101,
            ["edition", "#1#latitude", "#1#stationNumber"],
            [],
            [],
        ),
        # data filter with list
        (
            {"columns": "all", "filters": {"stationNumber": [27, 84]}},
            2,
            101,
            ["edition", "#1#latitude", "#1#airTemperature"],
            [],
            [("#1#airTemperature", [276.45, 266.55])],
        ),
        # header + data filter
        (
            {"columns": "all", "filters": {"observedData": 1, "stationNumber": [27, 84]}},
            2,
            101,
            ["edition", "#1#latitude", "#1#airTemperature"],
            [],
            [("#1#airTemperature", [276.45, 266.55])],
        ),
        # combining all options together (data)
        (
            {
                "columns": "data",
                "filters": {"observedData": 1, "stationNumber": [27, 84]},
                "required_columns": ["edition", "airTemperature"],
            },
            2,
            82,
            ["edition", "observedData", "#1#latitude", "#1#airTemperature"],
            ["masterTableNumber"],
            [("#1#airTemperature", [276.45, 266.55])],
        ),
        # header with filters and required_columns
        (
            {
                "columns": "header",
                "filters": {"observedData": 1, "stationNumber": [27, 84]},
                "required_columns": ["edition", "airTemperature"],
            },
            2,
            23,
            ["edition", "observedData", "#1#stationNumber", "#1#airTemperature"],
            ["#1#latitude"],
            [],
        ),
    ],
)
def test_read_flat_bufr_block_uncompressed_core(
    prefilter_headers: bool,
    _kwargs: dict,
    ref_rownum: int,
    ref_colnum: int,
    ref_keys_include: list,
    ref_keys_exclude: list,
    ref_value_checks: list,
) -> None:
    res = pdbufr.read_bufr(TEST_DATA_2, **_kwargs, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert len(res) == ref_rownum
    if ref_rownum == 0:
        assert res.empty
    else:
        assert len(res.columns) == ref_colnum

        for k in ref_keys_include:
            assert k in res

        for k in ref_keys_exclude:
            assert k not in res

        # Check specific values if provided
        for col_name, expected_values in ref_value_checks:
            np.testing.assert_allclose(expected_values, res[col_name])


@pytest.mark.parametrize("_kwargs", [{"prefilter_headers": False}, {"prefilter_headers": True}])
def test_read_flat_bufr_block_uncompressed_csv_compare(_kwargs: dict) -> None:
    # compare to csv
    res = pdbufr.read_bufr(TEST_DATA_2, "all", flat=True, filters={"stationNumber": [27, 84]}, **_kwargs)
    res = res.replace({None: np.nan})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#airTemperature" in res
    assert len(res.columns) == 101
    assert len(res) == 2

    # res.to_csv("REF_DATA_2", index=False)
    ref = pd.read_csv(
        REF_DATA_2,
        dtype={
            "typicalDate": str,
            "typicalTime": str,
            "#1#heightOfBarometerAboveMeanSeaLevel": str,
            "#1#nonCoordinatePressure": str,
            "#1#pressureReducedToMeanSeaLevel": str,
            "#1#3HourPressureChange": str,
            "#1#characteristicOfPressureTendency": str,
            "#1#24HourPressureChange": str,
        },
    )

    assert res.columns.to_list() == ref.columns.to_list()
    assert_frame_equal(res.iloc[:, :39], ref.iloc[:, :39], check_dtype=False)


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,ref_rownum, ref_colnum, ref_keys_include, ref_keys_exclude",
    [
        (
            {
                "columns": "all",
                "filters": {"airTemperature": slice(276, None)},
            },
            4,
            101,
            ["edition", "#1#latitude", "#1#longitude", "#1#stationNumber", "#1#airTemperature"],
            [],
        ),
        (
            {
                "columns": "all",
                "filters": {"#1#airTemperature": slice(276, None)},
            },
            4,
            101,
            ["edition", "#1#latitude", "#1#longitude", "#1#stationNumber", "#1#airTemperature"],
            [],
        ),
        (
            {
                "columns": "all",
                "filters": {"~airTemperature": slice(276, None)},
            },
            4,
            101,
            ["edition", "#1#latitude", "#1#longitude", "#1#stationNumber", "#1#airTemperature"],
            [],
        ),
    ],
)
def test_read_flat_bufr_block_uncompressed_filters(
    _kwargs: dict,
    ref_rownum: int,
    ref_colnum: int,
    ref_keys_include: list,
    ref_keys_exclude: list,
    prefilter_headers,
) -> None:
    res = pdbufr.read_bufr(TEST_DATA_2, **_kwargs, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert len(res) == ref_rownum
    assert len(res.columns) == ref_colnum

    if ref_rownum > 0:
        for k in ref_keys_include:
            assert k in res

        for k in ref_keys_exclude:
            assert k not in res
