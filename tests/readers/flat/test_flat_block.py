# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import typing as T
import warnings

import numpy as np
import pytest

import pdbufr
from pdbufr.utils.testing import reference_test_data_path
from pdbufr.utils.testing import sample_test_data_path

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")

# The message structure is the same in all the messages
# but some have #1#totalPrecipitationPast6Hours while
# others have #1#totalPrecipitationPast24Hours at the
# same position within the message
TEST_DATA_1 = sample_test_data_path("obs_3day.bufr")


TEST_DATA_2 = sample_test_data_path("synop_multi_subset_uncompressed.bufr")

# contains 1 message - with 51 compressed subsets with multiple timePeriods
TEST_DATA_9 = sample_test_data_path("ens_multi_subset_compressed.bufr")

# contains 1 message - with 128 compressed subsets with some str values
TEST_DATA_10 = sample_test_data_path("pgps_110.bufr")

REF_DATA_1 = reference_test_data_path("obs_3day_ref_1.csv")
REF_DATA_2 = reference_test_data_path("synop_uncompressed_ref_1.csv")


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "columns",
    [
        tuple(),
        ("",),
        ("all",),
    ],
)
def test_read_flat_bufr_block_args_1(columns: T.Union[tuple, str], prefilter_headers: bool) -> None:
    res = pdbufr.read_bufr(TEST_DATA_1, *columns, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 103
    assert len(res) == 50


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "columns",
    [[], "", [""], "all", ["all"]],
)
def test_read_flat_bufr_block_args_2(columns: dict, prefilter_headers: bool) -> None:

    res = pdbufr.read_bufr(TEST_DATA_1, columns=columns, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 103
    assert len(res) == 50


@pytest.mark.parametrize(
    "columns,err",
    [(3, TypeError), ([3], TypeError), ([3, 4], TypeError)],
)
def test_read_flat_bufr_block_args_bad(
    columns: T.Union[tuple, str],
    err: T.Type[Exception],
) -> None:

    with pytest.raises(err):
        pdbufr.read_bufr(TEST_DATA_1, columns, flat=True)


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


def test_read_flat_bufr_warning() -> None:
    def _find_warning(w: T.Any) -> bool:
        for item in w:
            if issubclass(
                item.category, UserWarning
            ) and "not all BUFR messages/subsets have the same structure" in str(item.message):
                return True
        return False

    # non-overlapping messages: warning generated
    with warnings.catch_warnings(record=True) as w:
        res = pdbufr.read_bufr(TEST_DATA_1, flat=True)
        assert len(res.columns) == 103
        assert len(res) == 50
        assert len(w) > 0
        assert _find_warning(w)

    # non-overlapping messages: warning disabled
    warnings.filterwarnings("ignore", module="pdbufr")
    with warnings.catch_warnings(record=True) as w:
        res = pdbufr.read_bufr(TEST_DATA_1, flat=True)
        assert len(res.columns) == 103
        assert len(res) == 50
        assert not _find_warning(w)

    # re-enables warnings
    warnings.filterwarnings("always", module="pdbufr")
    with warnings.catch_warnings(record=True) as w:
        res = pdbufr.read_bufr(TEST_DATA_1, flat=True)
        assert len(res.columns) == 103
        assert len(res) == 50
        assert len(w) > 0
        assert _find_warning(w)

    # overlapping messages: no warnings should be generated
    with warnings.catch_warnings(record=True) as w:
        res = pdbufr.read_bufr(TEST_DATA_2, flat=True)
        assert len(res.columns) == 101
        assert len(res) == 12
        assert not _find_warning(w)
