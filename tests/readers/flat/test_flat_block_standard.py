# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import pytest

import pdbufr
from pdbufr.utils.testing import reference_test_data_path, sample_test_data_path

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

# The message structure is the same in all the messages
# but some have #1#totalPrecipitationPast6Hours while
# others have #1#totalPrecipitationPast24Hours at the
# same position within the message
TEST_DATA_1 = sample_test_data_path("obs_3day.bufr")

REF_DATA_1 = reference_test_data_path("obs_3day_ref_1.csv")


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,ref_rownum, ref_colnum, ref_keys_include, ref_keys_exclude",
    [
        (
            {"columns": "all"},
            50,
            103,
            ["edition", "#1#latitude", "#1#totalPrecipitationPast6Hours", "#1#totalPrecipitationPast24Hours"],
            [],
        ),
        (
            {"columns": "data"},
            50,
            53,
            ["#1#latitude", "#1#totalPrecipitationPast6Hours", "#1#totalPrecipitationPast24Hours"],
            ["edition"],
        ),
        (
            {"columns": "header"},
            50,
            50,
            ["edition"],
            ["#1#latitude", "#1#totalPrecipitationPast6Hours", "#1#totalPrecipitationPast24Hours"],
        ),
        (
            {
                "columns": "header",
            },
            50,
            50,
            ["edition"],
            ["#1#latitude", "#1#totalPrecipitationPast6Hours", "#1#totalPrecipitationPast24Hours"],
        ),
    ],
)
def test_read_flat_bufr_block_standard_core(
    _kwargs: dict,
    ref_rownum: int,
    ref_colnum: int,
    ref_keys_include: list,
    ref_keys_exclude: list,
    prefilter_headers,
) -> None:
    res = pdbufr.read_bufr(TEST_DATA_1, **_kwargs, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert len(res) == ref_rownum
    assert len(res.columns) == ref_colnum

    for k in ref_keys_include:
        assert k in res

    for k in ref_keys_exclude:
        assert k not in res


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,ref_rownum, ref_colnum, ref_keys_include, ref_keys_exclude",
    [
        ({"columns": "all", "required_columns": "latitude"}, 50, 103, ["edition", "#1#latitude"], []),
        ({"columns": "all", "required_columns": ["latitude"]}, 50, 103, ["edition", "#1#latitude"], []),
        (
            {"columns": "all", "required_columns": ["latitude", "edition"]},
            50,
            103,
            ["edition", "#1#latitude"],
            [],
        ),
        (
            {"columns": "all", "required_columns": "totalPrecipitationPast6Hours"},
            43,
            102,
            ["edition", "#1#latitude", "#1#totalPrecipitationPast6Hours"],
            [],
        ),
        (
            {"columns": "all", "required_columns": "totalPrecipitationPast24Hours"},
            7,
            102,
            ["edition", "#1#latitude", "#1#totalPrecipitationPast24Hours"],
            [],
        ),
        ({"columns": "data", "required_columns": "latitude"}, 50, 53, ["#1#latitude"], ["edition"]),
        ({"columns": "data", "required_columns": ["latitude"]}, 50, 53, ["#1#latitude"], ["edition"]),
        (
            {"columns": "data", "required_columns": ["latitude", "edition"]},
            50,
            53,
            ["#1#latitude"],
            ["edition"],
        ),
        ({"columns": "header", "required_columns": "latitude"}, 50, 50, ["edition"], ["#1#latitude"]),
        ({"columns": "header", "required_columns": ["latitude"]}, 50, 50, ["edition"], ["#1#latitude"]),
        (
            {"columns": "header", "required_columns": ["latitude", "edition"]},
            50,
            50,
            ["edition"],
            ["#1#latitude"],
        ),
        ({"columns": "all", "required_columns": "xyz"}, 0, 0, [], []),
    ],
)
def test_read_flat_bufr_block_standard_required_columns(
    _kwargs: dict,
    ref_rownum: int,
    ref_colnum: int,
    ref_keys_include: list,
    ref_keys_exclude: list,
    prefilter_headers,
) -> None:
    res = pdbufr.read_bufr(TEST_DATA_1, **_kwargs, flat=True, prefilter_headers=prefilter_headers)

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


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "_kwargs,ref_rownum, ref_colnum, ref_keys_include, ref_keys_exclude",
    [
        ({"columns": "all", "filters": {"rdbtimeTime": "115557"}}, 6, 103, ["edition", "#1#latitude"], []),
        ({"columns": "all", "filters": {"count": 1}}, 1, 102, ["edition", "#1#latitude"], []),
        ({"columns": "all", "filters": {"count": "1"}}, 0, 0, ["edition", "#1#latitude"], []),
        (
            {"columns": "all", "filters": {"stationNumber": 894}},
            1,
            102,
            ["edition", "#1#latitude", "#1#totalPrecipitationPast6Hours"],
            ["#1#totalPrecipitationPast24Hours"],
        ),
        (
            {"columns": "all", "filters": {"stationNumber": [894, 103]}},
            2,
            103,
            ["edition", "#1#latitude", "#1#totalPrecipitationPast6Hours", "#1#totalPrecipitationPast24Hours"],
            [],
        ),
        (
            {"columns": "all", "filters": {"WMO_station_id": [3894, 7103]}},
            2,
            103,
            ["edition", "#1#latitude", "#1#totalPrecipitationPast6Hours", "#1#totalPrecipitationPast24Hours"],
            [],
        ),
        (
            {"columns": "all", "filters": {"count": slice(None, 2)}},
            2,
            102,
            ["edition", "#1#latitude", "#1#totalPrecipitationPast6Hours"],
            ["#1#totalPrecipitationPast24Hours"],
        ),
        (
            {
                "columns": "all",
                "filters": {"rdbtimeTime": "115557"},
                "required_columns": ["latitude", "edition"],
            },
            6,
            103,
            ["edition", "#1#latitude"],
            [],
        ),
        (
            {
                "columns": "all",
                "filters": {"#1#cloudType": 35, "#2#cloudType": 27},
                "required_columns": ["latitude", "edition"],
            },
            2,
            102,
            ["edition", "#1#latitude", "#1#cloudType", "#2#cloudType"],
            [],
        ),
        (
            {
                "columns": "all",
                "filters": {"~cloudType": 62},
                "required_columns": ["latitude", "edition"],
            },
            3,
            102,
            ["edition", "#1#latitude", "#1#cloudType", "#2#cloudType"],
            [],
        ),
    ],
)
def test_read_flat_bufr_block_standard_filters(
    _kwargs: dict,
    ref_rownum: int,
    ref_colnum: int,
    ref_keys_include: list,
    ref_keys_exclude: list,
    prefilter_headers,
) -> None:
    res = pdbufr.read_bufr(TEST_DATA_1, **_kwargs, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert len(res) == ref_rownum
    assert len(res.columns) == ref_colnum

    if ref_rownum > 0:
        for k in ref_keys_include:
            assert k in res

        for k in ref_keys_exclude:
            assert k not in res


def test_read_flat_bufr_block_standard_compare_csv() -> None:
    res = pdbufr.read_bufr(TEST_DATA_1, "all", flat=True, filters={"count": 2}, prefilter_headers=False)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" not in res
    assert len(res.columns) == 102
    assert len(res) == 1

    # res.to_csv(REF_DATA_1, index=False)
    ref = pd.read_csv(
        REF_DATA_1,
        dtype={"typicalDate": str, "typicalTime": str, "rdbtimeTime": str},
    )

    assert res.columns.to_list() == ref.columns.to_list()
    assert_frame_equal(res.iloc[:, :39], ref.iloc[:, :39])
