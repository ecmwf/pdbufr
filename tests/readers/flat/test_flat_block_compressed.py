# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import pytest

import pdbufr
from pdbufr.utils.testing import sample_test_data_path

pd = pytest.importorskip("pandas")

# contains 1 message - with 51 compressed subsets with multiple timePeriods
TEST_DATA_9 = sample_test_data_path("ens_multi_subset_compressed.bufr")

# contains 1 message - with 128 compressed subsets with some str values
TEST_DATA_10 = sample_test_data_path("pgps_110.bufr")


@pytest.mark.parametrize("prefilter_headers", [False, True])
@pytest.mark.parametrize(
    "_kwargs,ref_rownum, ref_colnum, ref_keys_include, ref_keys_exclude, ref_value_checks",
    [
        (
            {"columns": "all"},
            51,
            149,
            [
                "edition",
                "#1#latitude",
                *[f"#{i}#timePeriod" for i in range(1, 62)],
                *[f"#{i}#cape" for i in range(1, 62)],
            ],
            [],
            [],
        ),
        # required columns
        (
            {"columns": "all", "required_columns": ["cape"]},
            51,
            149,
            [
                "edition",
                "#1#latitude",
                *[f"#{i}#timePeriod" for i in range(1, 62)],
                *[f"#{i}#cape" for i in range(1, 62)],
            ],
            [],
            [],
        ),
        # test_read_flat_bufr_compressed_subsets_core_3: data with required_columns, filter_columns=False
        (
            {"columns": "data", "required_columns": ["edition", "cape"], "filter_columns": False},
            51,
            131,
            [
                "edition",
                "#1#latitude",
                *[f"#{i}#timePeriod" for i in range(1, 62)],
                *[f"#{i}#cape" for i in range(1, 62)],
            ],
            [],
            [],
        ),
        # required columns with filter_columns=True
        (
            {"columns": "data", "required_columns": ["edition", "cape"], "filter_columns": True},
            51,
            131,
            [
                "edition",
                "#1#latitude",
                *[f"#{i}#timePeriod" for i in range(1, 62)],
                *[f"#{i}#cape" for i in range(1, 62)],
            ],
            [],
            [],
        ),
        # data with invalid required_columns (empty result)
        (
            {"columns": "data", "required_columns": ["xyz", "cape"]},
            0,
            0,
            [],
            [],
            [],
        ),
        # header with required_columns
        (
            {"columns": "header", "required_columns": ["edition", "cape"]},
            51,
            20,
            ["edition", "cape"],
            ["#1#latitude"],
            [],
        ),
        # header filter
        (
            {"columns": "all", "filters": {"observedData": 1}},
            51,
            149,
            ["edition", "#1#latitude"],
            [],
            [("observedData", [1] * 51)],
        ),
        # data filter on ensembleMemberNumber
        (
            {"columns": "all", "filters": {"ensembleMemberNumber": 2}},
            1,
            149,
            ["edition", "#1#latitude"],
            [],
            [("#1#ensembleMemberNumber", [2]), ("#2#cape", [174.2])],
        ),
        # data filter with list
        (
            {"columns": "all", "filters": {"ensembleMemberNumber": [2, 4]}},
            2,
            149,
            ["edition", "#1#latitude"],
            [],
            [("#1#ensembleMemberNumber", [2, 4]), ("#2#cape", [174.2, 200.0])],
        ),
        # header + data filter
        (
            {"columns": "all", "filters": {"observedData": 1, "ensembleMemberNumber": [2, 4]}},
            2,
            149,
            ["edition", "#1#latitude", "#1#cape"],
            [],
            [("#1#ensembleMemberNumber", [2, 4]), ("#2#cape", [174.2, 200.0])],
        ),
        # combining all options together
        (
            {
                "columns": "data",
                "filters": {"observedData": 1, "ensembleMemberNumber": [2, 4]},
                "required_columns": ["edition", "cape"],
            },
            2,
            132,
            ["observedData", "edition", "#1#latitude", "#1#ensembleMemberNumber", "#1#cape"],
            ["masterTableNumber"],
            [("#1#ensembleMemberNumber", [2, 4]), ("#2#cape", [174.2, 200.0])],
        ),
        # header with filters and required_columns
        (
            {
                "columns": "header",
                "filters": {"observedData": 1, "ensembleMemberNumber": [2, 4]},
                "required_columns": ["edition", "cape"],
            },
            2,
            21,
            ["observedData", "edition"],
            ["#1#latitude", "#1#ensembleMemberNumber", "#1#cape"],
            [],
        ),
    ],
)
def test_read_flat_bufr_block_compressed_core(
    prefilter_headers: bool,
    _kwargs: dict,
    ref_rownum: int,
    ref_colnum: int,
    ref_keys_include: list,
    ref_keys_exclude: list,
    ref_value_checks: list,
) -> None:
    res = pdbufr.read_bufr(TEST_DATA_9, **_kwargs, flat=True, prefilter_headers=prefilter_headers)

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


@pytest.mark.parametrize("prefilter_headers", [False, True])
@pytest.mark.parametrize(
    "_kwargs,ref_rownum, ref_colnum, ref_keys_include, ref_keys_exclude, ref_string_checks",
    [
        # all columns without filters
        (
            {"columns": "all"},
            128,
            228,
            ["edition", "#1#latitude", "#1#stationOrSiteName"],
            [],
            [
                ("#1#stationOrSiteName", 128, str, ["ARD2-LPTR"] * 11 + ["DAV2-LPTR"] * 11, slice(0, 22)),
            ],
        ),
        # with stationOrSiteName filter
        (
            {"filters": {"stationOrSiteName": "DAV2-LPTR"}},
            11,
            228,
            ["edition", "#1#latitude", "#1#stationOrSiteName"],
            [],
            [
                ("#1#stationOrSiteName", 11, str, ["DAV2-LPTR"] * 11, slice(None)),
            ],
        ),
    ],
)
def test_read_flat_bufr_block_compressed_with_str(
    prefilter_headers: bool,
    _kwargs: dict,
    ref_rownum: int,
    ref_colnum: int,
    ref_keys_include: list,
    ref_keys_exclude: list,
    ref_string_checks: list,
) -> None:
    res = pdbufr.read_bufr(TEST_DATA_10, **_kwargs, flat=True, prefilter_headers=prefilter_headers)

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

        # Check string values if provided
        for col_name, expected_len, expected_type, expected_values, slice_obj in ref_string_checks:
            assert len(res[col_name]) == expected_len
            assert isinstance(res[col_name][0], expected_type)
            assert list(res[col_name][slice_obj]) == expected_values


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,ref_rownum, ref_colnum, ref_keys_include, ref_keys_exclude",
    [
        (
            {
                "columns": "all",
                "filters": {"ensembleMemberNumber": [0, 2], "~cape": slice(250, None)},
            },
            1,
            149,
            ["edition", "#1#latitude", "#1#cape"],
            [],
        ),
        (
            {
                "columns": "all",
                "filters": {"~cape": slice(250, None)},
            },
            22,
            149,
            ["edition", "#1#latitude", "#1#cape"],
            [],
        ),
    ],
)
def test_read_flat_bufr_block_compressed_filters(
    _kwargs: dict,
    ref_rownum: int,
    ref_colnum: int,
    ref_keys_include: list,
    ref_keys_exclude: list,
    prefilter_headers,
) -> None:
    res = pdbufr.read_bufr(TEST_DATA_9, **_kwargs, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert len(res) == ref_rownum
    assert len(res.columns) == ref_colnum

    if ref_rownum > 0:
        for k in ref_keys_include:
            assert k in res

        for k in ref_keys_exclude:
            assert k not in res
