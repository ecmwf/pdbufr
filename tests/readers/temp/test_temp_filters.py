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

TEST_DATA_CLASSIC = sample_test_data_path("temp_small.bufr")
TEST_DATA_HIRES = sample_test_data_path("temp_hires.bufr")


def test_temp_filter_classic_stnid_1():
    df = pdbufr.read_bufr(
        TEST_DATA_CLASSIC,
        reader="temp",
        columns="station",
        filters={"stnid": "71907"},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (1, 5)
    assert df["stnid"].iloc[0] == "71907"
    assert np.isclose(df["elevation"].iloc[0], 26)


def test_temp_filter_classic_stnid_2():
    df = pdbufr.read_bufr(
        TEST_DATA_CLASSIC,
        reader="temp",
        columns="station",
        filters={"stnid": ["71907", "89009"]},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (2, 5)
    assert df["stnid"].iloc[0] == "71907"
    assert df["stnid"].iloc[1] == "89009"
    assert np.isclose(df["elevation"].iloc[0], 26)
    assert np.isclose(df["elevation"].iloc[1], 2835)


def test_temp_filter_classic_pres_1():
    df = pdbufr.read_bufr(
        TEST_DATA_CLASSIC,
        reader="temp",
        columns="default",
        filters={"stnid": "71907", "pressure": slice(49000, 51000)},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (1, 11)
    assert df["stnid"].iloc[0] == "71907"
    assert np.isclose(df["elevation"].iloc[0], 26)
    assert np.isclose(df["pressure"].iloc[0], 50000.0)
    assert np.isclose(df["t"].iloc[0], 228.1)


def test_temp_filter_hires_stnid_1():
    df = pdbufr.read_bufr(
        TEST_DATA_HIRES,
        reader="temp",
        columns="station",
        filters={"stnid": "10954"},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (1, 5)
    assert df["stnid"].iloc[0] == "10954"
    assert np.isclose(df["elevation"].iloc[0], 760)


def test_temp_filter_hires_stnid_2():
    df = pdbufr.read_bufr(
        TEST_DATA_HIRES,
        reader="temp",
        columns="station",
        filters={"stnid": 1},
    )

    assert df.empty


def test_temp_filter_hires_pres_1():
    df = pdbufr.read_bufr(
        TEST_DATA_HIRES,
        reader="temp",
        columns="default",
        filters={"stnid": "10954", "pressure": slice(83635, 83637)},
    )

    df = df.replace(np.nan, None)

    assert df.shape == (1, 11)
    assert df["stnid"].iloc[0] == "10954"
    assert np.isclose(df["elevation"].iloc[0], 760)
    assert np.isclose(df["pressure"].iloc[0], 83636)
    assert np.isclose(df["z"].iloc[0], 16804.67544)
    assert np.isclose(df["t"].iloc[0], 274.46)
    assert np.isclose(df["td"].iloc[0], 273.45)
    assert np.isclose(df["wind_speed"].iloc[0], 4.4)
    assert np.isclose(df["wind_dir"].iloc[0], 240)
