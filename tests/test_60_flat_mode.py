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

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")

TEST_DATA_1 = os.path.join(SAMPLE_DATA_FOLDER, "obs_3day.bufr")
TEST_DATA_2 = os.path.join(SAMPLE_DATA_FOLDER, "synop_multi_subset_uncompressed.bufr")

# contains 1 message - with 51 compressed subsets with multiple timePeriods
TEST_DATA_9 = os.path.join(SAMPLE_DATA_FOLDER, "ens_multi_subset_compressed.bufr")

# contains 1 message - with 128 compressed subsets with some str values
TEST_DATA_10 = os.path.join(SAMPLE_DATA_FOLDER, "pgps_110.bufr")

REF_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "ref_data")
REF_DATA_1 = os.path.join(REF_DATA_FOLDER, "obs_3day_ref_1.csv")
REF_DATA_2 = os.path.join(REF_DATA_FOLDER, "synop_uncompressed_ref_1.csv")


def test_read_flat_bufr_args() -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # default args
    res = pdbufr.read_bufr(TEST_DATA_1, flat=True)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 103
    assert len(res) == 50

    # various positional args
    for columns in ["", "all"]:
        res = pdbufr.read_bufr(TEST_DATA_1, columns, flat=True)

        assert isinstance(res, pd.DataFrame)
        assert "edition" in res
        assert "#1#latitude" in res
        assert "#1#totalPrecipitationPast6Hours" in res
        assert "#1#totalPrecipitationPast24Hours" in res
        assert len(res.columns) == 103
        assert len(res) == 50

    # various kw args
    for columns in [[], "", [""], "all", ["all"]]:  # type: ignore
        res = pdbufr.read_bufr(TEST_DATA_1, columns=columns, flat=True)

        assert isinstance(res, pd.DataFrame)
        assert "edition" in res
        assert "#1#latitude" in res
        assert "#1#totalPrecipitationPast6Hours" in res
        assert "#1#totalPrecipitationPast24Hours" in res
        assert len(res.columns) == 103
        assert len(res) == 50

    with pytest.raises(ValueError) as exc:
        res = pdbufr.read_bufr(TEST_DATA_1, "a", flat=True)

    with pytest.raises(ValueError) as exc:
        res = pdbufr.read_bufr(TEST_DATA_1, ["a", "a"], flat=True)

    with pytest.raises(TypeError) as exc_t:
        res = pdbufr.read_bufr(TEST_DATA_1, 3, flat=True)  # type: ignore

    with pytest.raises(ValueError) as exc:
        res = pdbufr.read_bufr(TEST_DATA_1, [3], flat=True)  # type: ignore

    with pytest.raises(ValueError) as exc:
        res = pdbufr.read_bufr(TEST_DATA_1, [3, 4], flat=True)  # type: ignore


def test_read_flat_bufr_one_subset_one_filters() -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    # all
    res = pdbufr.read_bufr(TEST_DATA_1, "all", flat=True)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 103
    assert len(res) == 50

    # omitting header or data sections
    res = pdbufr.read_bufr(TEST_DATA_1, "data", flat=True)

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert len(res.columns) == 53
    assert len(res) == 50

    res = pdbufr.read_bufr(TEST_DATA_1, "header", flat=True)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert len(res.columns) == 50
    assert len(res) == 50

    # required columns
    required_columns = ["latitude", ["latitude"], ["latitude", "edition"]]
    for r in required_columns:
        res = pdbufr.read_bufr(TEST_DATA_1, "all", flat=True, required_columns=r)
        print(f"r={r}")
        assert isinstance(res, pd.DataFrame)
        assert "edition" in res
        assert "#1#latitude" in res
        assert len(res.columns) == 103
        assert len(res) == 50

    res = pdbufr.read_bufr(
        TEST_DATA_1, "all", flat=True, required_columns="totalPrecipitationPast6Hours"
    )
    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert len(res.columns) == 102
    assert len(res) == 43

    res = pdbufr.read_bufr(
        TEST_DATA_1,
        "all",
        flat=True,
        required_columns="totalPrecipitationPast24Hours",
    )
    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 102
    assert len(res) == 7

    res = pdbufr.read_bufr(TEST_DATA_1, "all", flat=True, required_columns="xyz")

    assert isinstance(res, pd.DataFrame)
    assert res.empty

    # omitting header or data sections + required columns
    required_columns = ["latitude", ["latitude"], ["latitude", "edition"]]
    for r in required_columns:
        res = pdbufr.read_bufr(TEST_DATA_1, "data", flat=True, required_columns=r)
        print(f"header=False r={r}")
        assert isinstance(res, pd.DataFrame)
        assert "edition" not in res
        assert "#1#latitude" in res
        assert len(res.columns) == 53
        assert len(res) == 50

    required_columns = ["latitude", ["latitude"], ["latitude", "edition"]]
    for r in required_columns:
        res = pdbufr.read_bufr(TEST_DATA_1, "header", flat=True, required_columns=r)
        print(f"data=False r={r}")
        assert isinstance(res, pd.DataFrame)
        assert "edition" in res
        assert "#1#latitude" not in res
        assert len(res.columns) == 50
        assert len(res) == 50

    # filters
    res = pdbufr.read_bufr(
        TEST_DATA_1, "all", flat=True, filters={"rdbtimeTime": "115557"}
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 103
    assert len(res) == 6

    res = pdbufr.read_bufr(
        TEST_DATA_1,
        "all",
        flat=True,
        filters={"rdbtimeTime": "115557"},
        required_columns=["latitude", "edition"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 103
    assert len(res) == 6

    res = pdbufr.read_bufr(TEST_DATA_1, "all", flat=True, filters={"count": 1})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 102
    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_1, "all", flat=True, filters={"stationNumber": 894}
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" not in res
    assert len(res.columns) == 102
    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_1, "all", flat=True, filters={"stationNumber": [894, 103]}
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 103
    assert len(res) == 2

    res = pdbufr.read_bufr(
        TEST_DATA_1, "all", flat=True, filters={"WMO_station_id": [3894, 7103]}
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 103
    assert len(res) == 2

    # compare to csv
    res = pdbufr.read_bufr(TEST_DATA_1, "all", flat=True, filters={"count": 2})

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


def test_read_flat_bufr_uncompressed_subsets() -> None:
    res = pdbufr.read_bufr(
        TEST_DATA_2,
        "all",
        flat=True,
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 101
    assert len(res) == 12

    # required columns
    res = pdbufr.read_bufr(
        TEST_DATA_2, "all", flat=True, required_columns=["airTemperature"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 101
    assert len(res) == 12

    res = pdbufr.read_bufr(
        TEST_DATA_2, "data", flat=True, required_columns=["airTemperature"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert len(res.columns) == 80
    assert len(res) == 12

    res = pdbufr.read_bufr(
        TEST_DATA_2, "data", flat=True, required_columns=["edition", "airTemperature"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert len(res.columns) == 80
    assert len(res) == 12

    res = pdbufr.read_bufr(
        TEST_DATA_2, "data", flat=True, required_columns=["xyz", "airTemperature"]
    )

    assert isinstance(res, pd.DataFrame)
    assert res.empty

    res = pdbufr.read_bufr(
        TEST_DATA_2,
        "header",
        flat=True,
        required_columns=["edition", "airTemperature"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert len(res.columns) == 21
    assert len(res) == 12

    # header filter
    res = pdbufr.read_bufr(TEST_DATA_2, "all", flat=True, filters={"observedData": 1})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 101
    assert len(res) == 12

    # data filter
    res = pdbufr.read_bufr(TEST_DATA_2, "all", flat=True, filters={"stationNumber": 27})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 101
    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_2, "all", flat=True, filters={"stationNumber": [27, 84]}
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#airTemperature" in res
    assert len(res.columns) == 101
    assert len(res) == 2
    ref_val = [276.45, 266.55]
    np.testing.assert_allclose(ref_val, res["#1#airTemperature"])

    # header + data filter
    res = pdbufr.read_bufr(
        TEST_DATA_2,
        "all",
        flat=True,
        filters={"observedData": 1, "stationNumber": [27, 84]},
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#airTemperature" in res
    assert len(res.columns) == 101
    assert len(res) == 2
    ref_val = [276.45, 266.55]
    np.testing.assert_allclose(ref_val, res["#1#airTemperature"])

    # combing all options to together
    res = pdbufr.read_bufr(
        TEST_DATA_2,
        "data",
        flat=True,
        filters={"observedData": 1, "stationNumber": [27, 84]},
        required_columns=["edition", "airTemperature"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert "#1#airTemperature" in res
    assert len(res.columns) == 80
    assert len(res) == 2
    ref_val = [276.45, 266.55]
    np.testing.assert_allclose(ref_val, res["#1#airTemperature"])

    res = pdbufr.read_bufr(
        TEST_DATA_2,
        "header",
        flat=True,
        filters={"observedData": 1, "stationNumber": [27, 84]},
        required_columns=["edition", "airTemperature"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert "#1#airTemperature" not in res
    assert len(res.columns) == 21
    assert len(res) == 2

    # compare to csv
    res = pdbufr.read_bufr(
        TEST_DATA_2,
        "all",
        flat=True,
        filters={"stationNumber": [27, 84]},
    )

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
    assert_frame_equal(res.iloc[:, :39], ref.iloc[:, :39])


def test_read_flat_bufr_compressed_subsets() -> None:
    res = pdbufr.read_bufr(TEST_DATA_9, "all", flat=True)

    ref_val: T.Any

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    for i in range(1, 62):
        assert f"#{i}#timePeriod" in res
        assert f"#{i}#cape" in res
    assert len(res.columns) == 149
    assert len(res) == 51

    # required columns
    res = pdbufr.read_bufr(TEST_DATA_9, "all", flat=True, required_columns=["cape"])

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    for i in range(1, 62):
        assert f"#{i}#timePeriod" in res
        assert f"#{i}#cape" in res
    assert len(res.columns) == 149
    assert len(res) == 51

    res = pdbufr.read_bufr(
        TEST_DATA_9, "data", flat=True, required_columns=["edition", "cape"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    for i in range(1, 62):
        print(i)
        assert f"#{i}#timePeriod" in res
        assert f"#{i}#cape" in res
    assert len(res.columns) == 130
    assert len(res) == 51

    res = pdbufr.read_bufr(
        TEST_DATA_9, "data", flat=True, required_columns=["xyz", "cape"]
    )

    assert isinstance(res, pd.DataFrame)
    assert res.empty

    res = pdbufr.read_bufr(
        TEST_DATA_9, "header", flat=True, required_columns=["edition", "cape"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert len(res.columns) == 19
    assert len(res) == 51

    # header filter
    res = pdbufr.read_bufr(TEST_DATA_9, "all", flat=True, filters={"observedData": 1})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 149
    assert len(res) == 51
    ref_val = [1] * 51
    np.testing.assert_allclose(ref_val, res["observedData"])

    # data filter
    res = pdbufr.read_bufr(
        TEST_DATA_9, "all", flat=True, filters={"ensembleMemberNumber": 2}
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 149
    assert len(res) == 1
    ref_val = [2]
    np.testing.assert_allclose(ref_val, res["#1#ensembleMemberNumber"])
    ref_val = [174.2]
    np.testing.assert_allclose(ref_val, res["#2#cape"])

    res = pdbufr.read_bufr(
        TEST_DATA_9, "all", flat=True, filters={"ensembleMemberNumber": [2, 4]}
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 149
    assert len(res) == 2
    ref_val = [2, 4]
    np.testing.assert_allclose(ref_val, res["#1#ensembleMemberNumber"])
    ref_val = [174.2, 200.0]
    np.testing.assert_allclose(ref_val, res["#2#cape"])

    # header + data filter
    res = pdbufr.read_bufr(
        TEST_DATA_9,
        "all",
        flat=True,
        filters={"observedData": 1, "ensembleMemberNumber": [2, 4]},
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#cape" in res
    assert len(res.columns) == 149
    assert len(res) == 2
    ref_val = [2, 4]
    np.testing.assert_allclose(ref_val, res["#1#ensembleMemberNumber"])
    ref_val = [174.2, 200.0]
    np.testing.assert_allclose(ref_val, res["#2#cape"])

    # combing all options to together
    res = pdbufr.read_bufr(
        TEST_DATA_9,
        "data",
        flat=True,
        filters={"observedData": 1, "ensembleMemberNumber": [2, 4]},
        required_columns=["edition", "cape"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert "#1#ensembleMemberNumber" in res
    assert "#1#cape" in res
    assert len(res.columns) == 130
    assert len(res) == 2
    ref_val = [2, 4]
    np.testing.assert_allclose(ref_val, res["#1#ensembleMemberNumber"])
    ref_val = [174.2, 200.0]
    np.testing.assert_allclose(ref_val, res["#2#cape"])

    res = pdbufr.read_bufr(
        TEST_DATA_9,
        "header",
        flat=True,
        filters={"observedData": 1, "ensembleMemberNumber": [2, 4]},
        required_columns=["edition", "cape"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert "#1#ensembleMemberNumber" not in res
    assert "#1#cape" not in res
    assert len(res.columns) == 19
    assert len(res) == 2


def test_read_flat_bufr_compressed_subsets_with_str() -> None:
    ref_str: T.Any

    res = pdbufr.read_bufr(TEST_DATA_10, "all", flat=True)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#stationOrSiteName" in res
    assert len(res["#1#stationOrSiteName"]) == 128
    assert isinstance(res["#1#stationOrSiteName"][0], str)
    ref_str = ["ARD2-LPTR"] * 11 + ["DAV2-LPTR"] * 11
    assert list(res["#1#stationOrSiteName"][:22]) == ref_str
    assert len(res.columns) == 228
    assert len(res) == 128

    res = pdbufr.read_bufr(
        TEST_DATA_10, filters={"stationOrSiteName": "DAV2-LPTR"}, flat=True
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#stationOrSiteName" in res
    assert len(res["#1#stationOrSiteName"]) == 11
    assert isinstance(res["#1#stationOrSiteName"][0], str)
    ref_str = ["DAV2-LPTR"] * 11
    assert list(res["#1#stationOrSiteName"]) == ref_str
    assert len(res.columns) == 228
    assert len(res) == 11


def test_read_flat_bufr_warning() -> None:
    def _find_warning(w: T.Any) -> bool:
        for item in w:
            if issubclass(
                item.category, UserWarning
            ) and "not all BUFR messages/subsets have the same structure" in str(
                item.message
            ):
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
