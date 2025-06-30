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
from pdbufr.utils.testing import sample_test_data_path

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

TEST_DATA_UNCOMPRESSED = sample_test_data_path("synop_multi_subset_uncompressed.bufr")
TEST_DATA_NEW = sample_test_data_path("syn_new.bufr")
TEST_DATA_WIGOS = sample_test_data_path("synop_wigos.bufr")


def test_synop_filter_wigos():
    df = pdbufr.read_bufr(
        TEST_DATA_WIGOS,
        reader="synop",
        columns="station",
        filters={"stnid": "0-705-0-1931"},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (1, 5)
    assert df["stnid"].iloc[0] == "0-705-0-1931"
    assert np.isclose(df["elevation"].iloc[0], 673.0)


def test_synop_filter_wmoid_new():
    df = pdbufr.read_bufr(
        TEST_DATA_NEW,
        reader="synop",
        columns="station",
        filters={"stnid": "11766"},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (1, 5)
    assert df["stnid"].iloc[0] == "11766"
    assert np.isclose(df["elevation"].iloc[0], 748.1)


def test_synop_filter_wmoid_uc():
    df = pdbufr.read_bufr(
        TEST_DATA_UNCOMPRESSED,
        reader="synop",
        columns="station",
        filters={"stnid": ["1308", "1084"]},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (2, 5)
    assert df["stnid"].iloc[0] == "1084"
    assert np.isclose(df["elevation"].iloc[0], 27)

    assert df["stnid"].iloc[1] == "1308"
    assert np.isclose(df["elevation"].iloc[1], 7)


@pytest.mark.skipif(True, reason="Not yet implemented")
def test_synop_filter_new_1a():
    df = pdbufr.read_bufr(
        TEST_DATA_NEW,
        reader="synop",
        columns="station",
        filters={"stnid": ["11766", "56257"], "t2m": slice(0, 275), "t2m_level": (0, 1.9)},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (1, 5)
    assert df["stnid"].iloc[0] == "11766"
    assert np.isclose(df["elevation"].iloc[0], 748.1)


def test_synop_filter_new_1b():
    with pytest.raises(ValueError):
        pdbufr.read_bufr(
            TEST_DATA_NEW,
            reader="synop",
            columns="station",
            filters={"stnid": ["11766", "56257"], "t2m": slice(0, 275), "t2m_level": (0, 1.9)},
        )


def test_synop_filter_uc_1():
    df = pdbufr.read_bufr(
        TEST_DATA_UNCOMPRESSED,
        reader="synop",
        columns=["station", "t2m"],
        filters={"stnid": ["1308", "1084"], "t2m": slice(0, 275)},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (1, 6)
    assert df["stnid"].iloc[0] == "1084"
    assert np.isclose(df["elevation"].iloc[0], 27)
    assert np.isclose(df["t2m"].iloc[0], 266.55)
