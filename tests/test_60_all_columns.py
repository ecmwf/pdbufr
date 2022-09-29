# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import typing as T

import numpy as np  # type: ignore
import pytest

import pdbufr

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")

TEST_DATA_1 = os.path.join(SAMPLE_DATA_FOLDER, "obs_3day.bufr")
TEST_DATA_2 = os.path.join(SAMPLE_DATA_FOLDER, "synop_multi_subset_uncompressed.bufr")

# contains 1 message - with 51 compressed subsets with multiple timePeriods
TEST_DATA_9 = os.path.join(SAMPLE_DATA_FOLDER, "ens_multi_subset_compressed.bufr")


def test_read_bufr_all_one_subset_one_filters() -> None:
    # The message structure is the same in all the messages
    # but some have #1#totalPrecipitationPast6Hours while
    # others have #1#totalPrecipitationPast24Hours at the
    # same position within the message

    res = pdbufr.read_all_bufr(TEST_DATA_1)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 153
    assert len(res) == 50

    # omitting header or data sections
    res = pdbufr.read_all_bufr(TEST_DATA_1, header=False)

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert len(res.columns) == 103
    assert len(res) == 50

    res = pdbufr.read_all_bufr(TEST_DATA_1, data=False)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert len(res.columns) == 50
    assert len(res) == 50

    try:
        res = pdbufr.read_all_bufr(TEST_DATA_1, header=False, data=False)
    except ValueError:
        pass

    # required columns
    required_columns = ["latitude", ["latitude"], ["latitude", "edition"]]
    for r in required_columns:
        res = pdbufr.read_all_bufr(TEST_DATA_1, required_columns=r)
        print(f"r={r}")
        assert isinstance(res, pd.DataFrame)
        assert "edition" in res
        assert "#1#latitude" in res
        assert len(res.columns) == 153
        assert len(res) == 50

    res = pdbufr.read_all_bufr(
        TEST_DATA_1, required_columns="totalPrecipitationPast6Hours"
    )
    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert len(res.columns) == 152
    assert len(res) == 43

    res = pdbufr.read_all_bufr(
        TEST_DATA_1, required_columns="totalPrecipitationPast24Hours"
    )
    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 152
    assert len(res) == 7

    res = pdbufr.read_all_bufr(TEST_DATA_1, required_columns="xyz")

    assert isinstance(res, pd.DataFrame)
    assert res.empty

    # omitting header or data sections + required columns
    required_columns = ["latitude", ["latitude"], ["latitude", "edition"]]
    for r in required_columns:
        res = pdbufr.read_all_bufr(TEST_DATA_1, header=False, required_columns=r)
        print(f"header=False r={r}")
        assert isinstance(res, pd.DataFrame)
        assert "edition" not in res
        assert "#1#latitude" in res
        assert len(res.columns) == 103
        assert len(res) == 50

    required_columns = ["latitude", ["latitude"], ["latitude", "edition"]]
    for r in required_columns:
        res = pdbufr.read_all_bufr(TEST_DATA_1, data=False, required_columns=r)
        print(f"data=False r={r}")
        assert isinstance(res, pd.DataFrame)
        assert "edition" in res
        assert "#1#latitude" not in res
        assert len(res.columns) == 50
        assert len(res) == 50

    # filters
    res = pdbufr.read_all_bufr(TEST_DATA_1, filters={"rdbtimeTime": "115557"})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 153
    assert len(res) == 6

    res = pdbufr.read_all_bufr(
        TEST_DATA_1,
        filters={"rdbtimeTime": "115557"},
        required_columns=["latitude", "edition"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 153
    assert len(res) == 6

    res = pdbufr.read_all_bufr(TEST_DATA_1, filters={"count": 1})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 152
    assert len(res) == 1

    res = pdbufr.read_all_bufr(TEST_DATA_1, filters={"stationNumber": 894})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" not in res
    assert len(res.columns) == 152
    assert len(res) == 1

    res = pdbufr.read_all_bufr(TEST_DATA_1, filters={"stationNumber": [894, 103]})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 153
    assert len(res) == 2


def test_read_all_bufr_uncompressed_subsets() -> None:
    res = pdbufr.read_all_bufr(TEST_DATA_2)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 110
    assert len(res) == 12

    # required columns
    res = pdbufr.read_all_bufr(TEST_DATA_2, required_columns=["airTemperature"])

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 110
    assert len(res) == 12

    res = pdbufr.read_all_bufr(
        TEST_DATA_2, header=False, required_columns=["airTemperature"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert len(res.columns) == 89
    assert len(res) == 12

    res = pdbufr.read_all_bufr(
        TEST_DATA_2, header=False, required_columns=["edition", "airTemperature"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert len(res.columns) == 89
    assert len(res) == 12

    res = pdbufr.read_all_bufr(
        TEST_DATA_2, header=False, required_columns=["xyz", "airTemperature"]
    )

    assert isinstance(res, pd.DataFrame)
    assert res.empty

    res = pdbufr.read_all_bufr(
        TEST_DATA_2, data=False, required_columns=["edition", "airTemperature"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert len(res.columns) == 21
    assert len(res) == 12

    # header filter
    res = pdbufr.read_all_bufr(TEST_DATA_2, filters={"observedData": 1})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 110
    assert len(res) == 12

    # data filter
    res = pdbufr.read_all_bufr(TEST_DATA_2, filters={"stationNumber": 27})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 110
    assert len(res) == 1

    res = pdbufr.read_all_bufr(TEST_DATA_2, filters={"stationNumber": [27, 84]})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#airTemperature" in res
    assert len(res.columns) == 110
    assert len(res) == 2
    ref_val = [276.45, 266.55]
    np.testing.assert_allclose(ref_val, res["#1#airTemperature"])

    # header + data filter
    res = pdbufr.read_all_bufr(
        TEST_DATA_2, filters={"observedData": 1, "stationNumber": [27, 84]}
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#airTemperature" in res
    assert len(res.columns) == 110
    assert len(res) == 2
    ref_val = [276.45, 266.55]
    np.testing.assert_allclose(ref_val, res["#1#airTemperature"])

    # combing all options to together
    res = pdbufr.read_all_bufr(
        TEST_DATA_2,
        header=False,
        filters={"observedData": 1, "stationNumber": [27, 84]},
        required_columns=["edition", "airTemperature"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" not in res
    assert "#1#latitude" in res
    assert "#1#airTemperature" in res
    assert len(res.columns) == 89
    assert len(res) == 2
    ref_val = [276.45, 266.55]
    np.testing.assert_allclose(ref_val, res["#1#airTemperature"])

    res = pdbufr.read_all_bufr(
        TEST_DATA_2,
        data=False,
        filters={"observedData": 1, "stationNumber": [27, 84]},
        required_columns=["edition", "airTemperature"],
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert "#1#airTemperature" not in res
    assert len(res.columns) == 21
    assert len(res) == 2


def test_read_all_bufr_compressed_subsets() -> None:
    res = pdbufr.read_all_bufr(TEST_DATA_9)

    ref_val: T.Any

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    for i in range(1, 62):
        print(i)
        assert f"#{i}#timePeriod" in res
        assert f"#{i}#cape" in res
    assert len(res.columns) == 149
    assert len(res) == 51

    # required columns
    res = pdbufr.read_all_bufr(TEST_DATA_9, required_columns=["cape"])

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    for i in range(1, 62):
        print(i)
        assert f"#{i}#timePeriod" in res
        assert f"#{i}#cape" in res
    assert len(res.columns) == 149
    assert len(res) == 51

    res = pdbufr.read_all_bufr(
        TEST_DATA_9, header=False, required_columns=["edition", "cape"]
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

    res = pdbufr.read_all_bufr(
        TEST_DATA_9, header=False, required_columns=["xyz", "cape"]
    )

    assert isinstance(res, pd.DataFrame)
    assert res.empty

    res = pdbufr.read_all_bufr(
        TEST_DATA_9, data=False, required_columns=["edition", "cape"]
    )

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" not in res
    assert len(res.columns) == 19
    assert len(res) == 51

    # header filter
    res = pdbufr.read_all_bufr(TEST_DATA_9, filters={"observedData": 1})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 149
    assert len(res) == 51
    ref_val = [1] * 51
    np.testing.assert_allclose(ref_val, res["observedData"])

    # data filter
    res = pdbufr.read_all_bufr(TEST_DATA_9, filters={"ensembleMemberNumber": 2})

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert len(res.columns) == 149
    assert len(res) == 1
    ref_val = [2]
    np.testing.assert_allclose(ref_val, res["#1#ensembleMemberNumber"])
    ref_val = [174.2]
    np.testing.assert_allclose(ref_val, res["#2#cape"])

    res = pdbufr.read_all_bufr(TEST_DATA_9, filters={"ensembleMemberNumber": [2, 4]})

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
    res = pdbufr.read_all_bufr(
        TEST_DATA_9, filters={"observedData": 1, "ensembleMemberNumber": [2, 4]}
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
    res = pdbufr.read_all_bufr(
        TEST_DATA_9,
        header=False,
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

    res = pdbufr.read_all_bufr(
        TEST_DATA_9,
        data=False,
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
