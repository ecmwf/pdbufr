# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import typing as T

import numpy as np
import pytest

import pdbufr

pd = pytest.importorskip("pandas")
assert_frame_equal = pd.testing.assert_frame_equal

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
URL_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "url-data")

TEST_DATA_1 = os.path.join(SAMPLE_DATA_FOLDER, "obs_3day.bufr")
TEST_DATA_2 = os.path.join(SAMPLE_DATA_FOLDER, "synop_multi_subset_uncompressed.bufr")
TEST_DATA_3 = os.path.join(SAMPLE_DATA_FOLDER, "temp.bufr")
TEST_DATA_4 = os.path.join(
    SAMPLE_DATA_FOLDER,
    "M02-HIRS-HIRxxx1B-NA-1.0-20181122114854.000000000Z-20181122132602-1304602.bufr",
)
# contains compressed subsets - each subset with multiple locations
TEST_DATA_5 = os.path.join(SAMPLE_DATA_FOLDER, "tropical_cyclone.bufr")

# contains uncompressed subsets (1 message)
TEST_DATA_6 = os.path.join(SAMPLE_DATA_FOLDER, "wave_uncompressed.bufr")

# contains 1 message - each subset with multiple timePeriods
TEST_DATA_7 = os.path.join(SAMPLE_DATA_FOLDER, "ens_multi_subset_uncompressed.bufr")

# contains 3 messages - each with 128 compressed subsets
TEST_DATA_8 = os.path.join(SAMPLE_DATA_FOLDER, "compress_3.bufr")

# contains 1 message - with 51 compressed subsets with multiple timePeriods
TEST_DATA_9 = os.path.join(SAMPLE_DATA_FOLDER, "ens_multi_subset_compressed.bufr")

# contains 7 temp messages
TEST_DATA_10 = os.path.join(SAMPLE_DATA_FOLDER, "temp_small.bufr")

# contains aircraft messages
TEST_DATA_11 = os.path.join(SAMPLE_DATA_FOLDER, "aircraft_small.bufr")

# contains new types of synop messages
TEST_DATA_12 = os.path.join(SAMPLE_DATA_FOLDER, "syn_new.bufr")

# contains compressed aircraft messages with strings
TEST_DATA_13 = os.path.join(SAMPLE_DATA_FOLDER, "aircraft_mrar_compressed.bufr")


def download_test_data(filename: str) -> str:
    import requests  # type: ignore

    target = os.path.join(URL_DATA_FOLDER, filename)
    if not os.path.exists(target):
        url_base = "https://get.ecmwf.int/repository/test-data/pdbufr/test-data/"
        url = os.path.join(url_base, filename)
        os.makedirs(URL_DATA_FOLDER, mode=0o755, exist_ok=True)
        target = os.path.join(URL_DATA_FOLDER, filename)
        r = requests.get(url, allow_redirects=True)
        r.raise_for_status()
        open(target, "wb").write(r.content)
    return target


def test_read_bufr_one_subset_one_filters() -> None:
    res = pdbufr.read_bufr(TEST_DATA_1, columns=("latitude",))

    assert isinstance(res, pd.DataFrame)
    assert "latitude" in res
    assert len(res) == 50

    res = pdbufr.read_bufr(
        TEST_DATA_1, columns=("latitude",), filters={"rdbtimeTime": "115557"}
    )

    assert len(res) == 6

    res = pdbufr.read_bufr(
        TEST_DATA_1, columns=("latitude"), filters={"rdbtimeTime": "115557"}
    )

    assert len(res) == 6

    res = pdbufr.read_bufr(TEST_DATA_1, columns=("latitude",), filters={"count": 1})

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_1, columns=("latitude",), filters={"stationNumber": 894}
    )

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_1, columns=("latitude",), filters={"stationNumber": [894, 103]}
    )

    assert len(res) == 2


def test_read_bufr_one_subset_one_observation_data() -> None:
    columns = (
        "count",
        "stationNumber",
        "data_datetime",
        "latitude",
        "longitude",
        "heightOfStation",
        "airTemperatureAt2M",
        "dewpointTemperatureAt2M",
        "horizontalVisibility",
    )
    expected_first_row = {
        "count": 1,
        "stationNumber": 894,
        "data_datetime": pd.Timestamp("2017-04-25 12:00:00"),
        "latitude": 49.43000000000001,
        "longitude": -2.6,
        "heightOfStation": 101.0,
        "airTemperatureAt2M": 282.40000000000003,
        "dewpointTemperatureAt2M": 274.0,
        "horizontalVisibility": 55000.0,
    }

    res = pdbufr.read_bufr(TEST_DATA_1, columns=columns)

    assert len(res) == 50
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_multiple_uncompressed_subsets_one_observation() -> None:
    res = pdbufr.read_bufr(TEST_DATA_2, columns=("latitude",))

    assert isinstance(res, pd.DataFrame)
    assert "latitude" in dict(res)
    assert len(res) == 12

    res = pdbufr.read_bufr(
        TEST_DATA_2, columns=("latitude",), filters={"observedData": 1}
    )

    assert len(res) == 12

    res = pdbufr.read_bufr(
        TEST_DATA_2, columns=("latitude",), filters={"stationNumber": 27}
    )

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_2, columns=("latitude",), filters={"stationNumber": [27, 84]}
    )

    assert len(res) == 2

    columns = [
        "latitude",
        "longitude",
        "heightOfStationGroundAboveMeanSeaLevel",
        "airTemperature",
    ]
    expected_first_row = {
        "latitude": 69.65230000000001,
        "longitude": 18.905700000000003,
        "heightOfStationGroundAboveMeanSeaLevel": 20.0,
        "airTemperature": 276.45,
    }

    res = pdbufr.read_bufr(TEST_DATA_2, columns=columns, filters={"stationNumber": 27})

    assert len(res) == 1
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_one_subsets_multiple_observations_filters() -> None:
    res = pdbufr.read_bufr(
        TEST_DATA_3, columns=("latitude",), filters={"stationNumber": 907}
    )

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_3, columns=("latitude",), filters={"pressure": [100000, 26300]}
    )

    assert len(res) == 425


def test_read_bufr_one_subsets_multiple_observations_data() -> None:
    columns = [
        "stationNumber",
        "data_datetime",
        "longitude",
        "latitude",
        "heightOfStation",
        "pressure",
        "airTemperature",
    ]
    expected_first_rows = pd.DataFrame.from_records(
        [
            {
                "stationNumber": 907,
                "data_datetime": pd.Timestamp("2008-12-08 12:00:00"),
                "longitude": -78.08000000000001,
                "latitude": 58.470000000000006,
                "heightOfStation": 26.0,
                "pressure": 100000.0,
                "airTemperature": 259.7,
            },
            {
                "stationNumber": 823,
                "data_datetime": pd.Timestamp("2008-12-08 12:00:00"),
                "longitude": -73.67,
                "latitude": 53.75000000000001,
                "heightOfStation": 302.0,
                "pressure": 100000.0,
                "airTemperature": None,
            },
        ]
    )

    res = pdbufr.read_bufr(TEST_DATA_3, columns=columns, filters={"pressure": 100000})

    assert len(res) == 408
    assert res.iloc[:2].equals(expected_first_rows[res.columns])


def test_read_bufr_multiple_compressed_subsets_multiple_observations_filters() -> None:
    res = pdbufr.read_bufr(
        TEST_DATA_4, columns=("latitude",), filters={"hour": 11, "minute": 48}
    )

    assert len(res) == 56

    res = pdbufr.read_bufr(
        TEST_DATA_4, columns=("latitude",), filters={"hour": 11, "minute": [48, 49]}
    )

    assert len(res) == 616


def test_read_bufr_multiple_compressed_subsets_multiple_observations_data() -> None:
    columns = [
        "data_datetime",
        "longitude",
        "latitude",
        "heightOfStation",
        "tovsOrAtovsOrAvhrrInstrumentationChannelNumber",
        "brightnessTemperature",
    ]
    expected_first_row = {
        "data_datetime": pd.Timestamp("2018-11-22 11:48:54.396"),
        "longitude": -9.201400000000001,
        "latitude": 53.354200000000006,
        "heightOfStation": 828400.0,
        "tovsOrAtovsOrAvhrrInstrumentationChannelNumber": 2.0,
        "brightnessTemperature": 218.76,
    }

    res = pdbufr.read_bufr(
        TEST_DATA_4,
        columns=columns,
        filters={
            "hour": 11,
            "minute": 48,
            "tovsOrAtovsOrAvhrrInstrumentationChannelNumber": 2,
        },
    )

    assert len(res) == 56
    assert res.iloc[0].to_dict() == expected_first_row


def test_temp_single_station_1() -> None:
    columns = [
        "WMO_station_id",
        "stationNumber",
        "longitude",
        "latitude",
        "pressure",
        "verticalSoundingSignificance",
        "airTemperature",
    ]

    expected_count = 25

    expected = pd.DataFrame.from_dict(
        {
            "WMO_station_id": np.full(expected_count, 71823),
            "stationNumber": np.full(expected_count, 823),
            "latitude": np.full(expected_count, 53.75000000000001),
            "longitude": np.full(expected_count, -73.67),
            "pressure": [
                100000.0,
                97400.0,
                93700.0,
                92500.0,
                90600.0,
                85000.0,
                84700.0,
                79200.0,
                70000.0,
                69900.0,
                64600.0,
                60700.0,
                59700.0,
                58000.0,
                53400.0,
                50000.0,
                45200.0,
                42300.0,
                40000.0,
                37800.0,
                30000.0,
                29700.0,
                25000.0,
                23200.0,
                20500.0,
            ],
            "verticalSoundingSignificance": [
                32,
                68,
                4,
                32,
                4,
                32,
                4,
                4,
                32,
                4,
                4,
                4,
                4,
                4,
                4,
                32,
                4,
                4,
                32,
                20,
                32,
                4,
                32,
                4,
                4,
            ],
            "airTemperature": [
                None,
                256.7,
                255.10000000000002,
                255.3,
                256.7,
                253.3,
                253.10000000000002,
                248.9,
                241.9,
                241.70000000000002,
                239.70000000000002,
                236.3,
                236.10000000000002,
                234.5,
                230.70000000000002,
                229.3,
                226.3,
                223.10000000000002,
                222.9,
                221.3,
                218.9,
                218.9,
                221.10000000000002,
                223.10000000000002,
                221.5,
            ],
        }
    )

    res = pdbufr.read_bufr(TEST_DATA_3, columns=columns, filters={"stationNumber": 823})

    assert_frame_equal(res, expected[res.columns])


def test_temp_single_station_2() -> None:
    columns = [
        "stationNumber",
        "longitude",
        "latitude",
        "pressure",
        "airTemperature",
    ]

    expected_count = 8

    expected = pd.DataFrame.from_dict(
        {
            "stationNumber": np.full(expected_count, 823),
            "latitude": np.full(expected_count, 53.75000000000001),
            "longitude": np.full(expected_count, -73.67),
            "pressure": [
                100000.0,
                92500.0,
                85000.0,
                70000.0,
                50000.0,
                40000.0,
                30000.0,
                25000.0,
            ],
            "airTemperature": [
                None,
                255.3,
                253.3,
                241.9,
                229.3,
                222.9,
                218.9,
                221.10000000000002,
            ],
        }
    )

    res = pdbufr.read_bufr(
        TEST_DATA_3,
        columns=columns,
        filters={"stationNumber": 823, "verticalSoundingSignificance": 32},
    )

    assert_frame_equal(res, expected[res.columns])


def test_temp_single_station_3() -> None:
    columns = [
        "stationNumber",
        "data_datetime",
        "longitude",
        "latitude",
        "airTemperature",
        "pressure",
    ]

    ref_num = 2

    ref = {
        "stationNumber": np.full(ref_num, 823),
        "latitude": np.full(ref_num, 53.75),
        "longitude": np.full(ref_num, -73.67),
        "pressure": [92500.0, 40000.0],
        "airTemperature": [255.3, 222.9],
        "data_datetime": [
            pd.Timestamp("2008-12-08 12:00:00"),
            pd.Timestamp("2008-12-08 12:00:00"),
        ],
    }
    ref = pd.DataFrame.from_dict(ref)

    res = pdbufr.read_bufr(
        TEST_DATA_3,
        columns=columns,
        filters={
            "stationNumber": 823,
            "verticalSoundingSignificance": 32,
            "pressure": [40000.0, 92500.0],
        },
    )

    assert_frame_equal(res, ref)


def test_tropicalcyclone_1() -> None:
    columns = ["data_datetime", "longitude", "latitude", "windSpeedAt10M"]

    expected = pd.DataFrame.from_dict(
        {
            "latitude": [None, 11.3, 12.7, 10.2],
            "longitude": [None, -126.0, -124.9, -126],
            "data_datetime": [
                pd.Timestamp("2015-11-18 00:00:00"),
                pd.Timestamp("2015-11-18 00:00:00"),
                pd.Timestamp("2015-11-18 00:00:00"),
                pd.Timestamp("2015-11-18 00:00:00"),
            ],
            "windSpeedAt10M": [None, None, 30.4, None],
        }
    )

    res = pdbufr.read_bufr(
        TEST_DATA_5,
        columns=columns,
        filters={"stormIdentifier": "70E", "ensembleMemberNumber": 4},
    )

    assert len(res) == 34

    res = pdbufr.read_bufr(
        TEST_DATA_5,
        columns=columns,
        filters={"stormIdentifier": "70E", "ensembleMemberNumber": 4},
        required_columns=False,
    )

    assert len(res) == 69
    assert_frame_equal(res[0:4], expected[0:4])


def test_tropicalcyclone_2() -> None:
    columns = ["longitude", "latitude", "windSpeedAt10M"]

    expected = pd.DataFrame.from_dict(
        {
            "latitude": [
                12.7,
                13.0,
                12.7,
                None,
                12.5,
                12.2,
                12.5,
                12.7,
                12.7,
                14.1,
                13.6,
                14.1,
                14.1,
                13.9,
                15.3,
                15.0,
                14.7,
                15.0,
                14.4,
                14.4,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            "longitude": [
                -124.9,
                -125.5,
                -125.2,
                None,
                -127.5,
                -128.0,
                -128.0,
                -126.6,
                -128.3,
                -126.0,
                -128.9,
                -129.4,
                -130.5,
                -131.4,
                -128.9,
                -128.9,
                -130.3,
                -128.9,
                -129.4,
                -127.5,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            "windSpeedAt10M": [
                30.4,
                17.0,
                16.5,
                None,
                16.5,
                15.4,
                14.9,
                12.4,
                10.8,
                11.8,
                11.8,
                12.4,
                10.8,
                11.3,
                10.3,
                11.8,
                11.8,
                11.8,
                11.3,
                11.3,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
        }
    )

    res = pdbufr.read_bufr(
        TEST_DATA_5,
        columns=columns,
        filters={
            "stormIdentifier": "70E",
            "ensembleMemberNumber": 4,
            "meteorologicalAttributeSignificance": 3,
        },
    )

    assert_frame_equal(res, expected)


def test_wave_1() -> None:
    columns = ["data_datetime", "longitude", "latitude", "significantWaveHeight"]
    expected_0 = pd.DataFrame.from_records(
        [
            {
                "latitude": -28.86667,
                "longitude": 153.3833,
                "significantWaveHeight": 2.34,
                "data_datetime": pd.Timestamp("2017-11-02 10:00:00"),
            },
            {
                "latitude": -28.86667,
                "longitude": 153.3833,
                "significantWaveHeight": None,
                "data_datetime": pd.Timestamp("2017-11-02 10:00:00"),
            },
            {
                "latitude": -30.36667,
                "longitude": 153.36667,
                "significantWaveHeight": 1.72,
                "data_datetime": pd.Timestamp("2017-11-02 10:00:00"),
            },
        ]
    )
    expected_1 = pd.DataFrame.from_records(
        [
            {
                "latitude": -35.7,
                "longitude": 150.33333,
                "significantWaveHeight": 1.7,
                "data_datetime": pd.Timestamp("2017-11-02 10:00:00"),
            },
            {
                "latitude": -35.7,
                "longitude": 150.3333,
                "significantWaveHeight": None,
                "data_datetime": pd.Timestamp("2017-11-02 10:00:00"),
            },
        ]
    )

    res = pdbufr.read_bufr(TEST_DATA_6, columns=columns)
    res_end = res[70:].reset_index(drop=True)

    assert len(res) == 72
    assert_frame_equal(res[:3], expected_0)
    assert_frame_equal(res_end, expected_1)


def test_ens_uncompressed() -> None:
    columns = [
        "longitude",
        "latitude",
        "ensembleMemberNumber",
        "timePeriod",
        "airTemperatureAt2M",
    ]

    res = pdbufr.read_bufr(TEST_DATA_7, columns=columns)

    ref = {
        "latitude": [51.52, 51.52],
        "longitude": [0.97, 0.97],
        "ensembleMemberNumber": [0, 0],
        "timePeriod": [0, 6],
        "airTemperatureAt2M": [292.7, 291.6],
    }
    ref = pd.DataFrame.from_dict(ref)

    assert len(res) == 3111
    assert_frame_equal(res[:2], ref[res.columns])


def test_ens_compressed() -> None:
    columns = ["longitude", "latitude", "ensembleMemberNumber", "timePeriod", "cape"]

    res = pdbufr.read_bufr(
        TEST_DATA_9,
        columns=columns,
        filters={"timePeriod": [0, 24], "ensembleMemberNumber": [2, 5]},
    )

    ref = {
        "latitude": [51.52, 51.52, 51.52, 51.52],
        "longitude": [0.97, 0.97, 0.97, 0.97],
        "ensembleMemberNumber": [2, 2, 5, 5],
        "timePeriod": [0, 24, 0, 24],
        "cape": [41.9, 0, 14.4, 0],
    }
    ref = pd.DataFrame.from_dict(ref)

    assert len(res) == 4
    assert_frame_equal(res, ref[res.columns])


def test_sat_compressed_1() -> None:
    columns = [
        "data_datetime",
        "latitude",
        "longitude",
        "nonCoordinateLatitude",
        "nonCoordinateLongitude",
        "significandOfVolumetricMixingRatio",
        "nonCoordinatePressure",
    ]

    expected_first_row = {
        "data_datetime": pd.Timestamp("2015-08-21 01:59:05"),
        "latitude": -44.83389,
        "longitude": 171.1635,
        "nonCoordinateLatitude": -44.82399,
        "nonCoordinateLongitude": 171.05569,
        "nonCoordinatePressure": 8555.0,
        "significandOfVolumetricMixingRatio": 8531573,
    }

    expected_second_row = {
        "data_datetime": pd.Timestamp("2015-08-21 01:59:05"),
        "latitude": -44.83389,
        "longitude": 171.1635,
        "nonCoordinateLatitude": -44.82399,
        "nonCoordinateLongitude": 171.05569,
        "nonCoordinatePressure": 17100.1,
        "significandOfVolumetricMixingRatio": 8486850,
    }

    expected_12_row = {
        "data_datetime": pd.Timestamp("2015-08-21 01:59:05"),
        "latitude": -44.83389,
        "longitude": 171.1635,
        "nonCoordinateLatitude": -44.82399,
        "nonCoordinateLongitude": 171.05569,
        "nonCoordinatePressure": 102550.5,
        "significandOfVolumetricMixingRatio": 6018766,
    }

    expected_13_row = {
        "data_datetime": pd.Timestamp("2015-08-21 01:59:06"),
        "latitude": -44.77121,
        "longitude": 171.1515,
        "nonCoordinateLatitude": -44.76132,
        "nonCoordinateLongitude": 171.04379,
        "nonCoordinatePressure": 8556.9,
        "significandOfVolumetricMixingRatio": 8533734,
    }

    ref_1 = pd.DataFrame(expected_first_row, index=[0])
    ref_2 = pd.DataFrame(expected_second_row, index=[1])
    ref_12 = pd.DataFrame(expected_12_row, index=[11])
    ref_13 = pd.DataFrame(expected_13_row, index=[12])

    res = pdbufr.read_bufr(
        TEST_DATA_8, columns=columns, filters={"firstOrderStatistics": 15}
    )

    assert len(res) == 128 * 12 * 3
    assert_frame_equal(res[0:1], ref_1[res.columns])
    assert_frame_equal(res[1:2], ref_2[res.columns])
    assert_frame_equal(res[11:12], ref_12[res.columns])
    assert_frame_equal(res[12:13], ref_13[res.columns])


def assert_simple_key_core(path, param, key, key_value, ref, part=False):
    # type: (str, str, str, T.Any, T.Any, bool) -> None
    columns = [param, key]
    filters = {key: key_value}

    res = pdbufr.read_bufr(path, columns=columns, filters=filters)

    ref_cnt = len(ref) if ref is not None else 0
    if ref_cnt > 0:
        if part:
            assert len(res) > ref_cnt
            np.allclose(res[param][0:ref_cnt], ref)
        else:
            assert len(res) == ref_cnt
            np.allclose(res[param], ref)
    else:
        assert len(res) == ref_cnt


def test_bufr_header() -> None:
    ref = np.array([26, 302, 2835, 38, 30, 11, 567])
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "edition", 3, ref)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "edition", 4, None)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "edition", [3, 4], ref)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "bufrHeaderCentre", 98, ref)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "bufrHeaderCentre", 1, None)
    # assert_simple_key_core(TEST_DATA_10, "heightOfStation", "bufrHeaderCentre", "ecmf", ref)
    assert_simple_key_core(
        TEST_DATA_10, "heightOfStation", "bufrHeaderSubCentre", 0, ref
    )
    assert_simple_key_core(
        TEST_DATA_10, "heightOfStation", "bufrHeaderSubcentre", 1, None
    )
    assert_simple_key_core(
        TEST_DATA_10, "heightOfStation", "masterTablesVersionNumber", 13, ref
    )
    assert_simple_key_core(
        TEST_DATA_10, "heightOfStation", "masterTablesVersionNumber", 1, None
    )
    assert_simple_key_core(
        TEST_DATA_10, "heightOfStation", "localTablesVersionNumber", 1, ref
    )
    assert_simple_key_core(
        TEST_DATA_10, "heightOfStation", "localTablesVersionNumber", 2, None
    )
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "dataCategory", 2, ref)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "dataCategory", 1, None)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "dataSubCategory", 101, ref)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "dataSubCategory", 1, None)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "rdbType", 5, ref)
    assert_simple_key_core(TEST_DATA_10, "heightOfStation", "rdbType", 1, None)


def test_ident() -> None:
    assert_simple_key_core(
        TEST_DATA_10, "airTemperature", "ident", "91348", np.array([298.4]), part=True
    )

    assert_simple_key_core(
        TEST_DATA_10,
        "airTemperature",
        "blockNumber",
        91,
        np.array([298.4, 301]),
        part=True,
    )
    assert_simple_key_core(
        TEST_DATA_10,
        "airTemperature",
        "stationNumber",
        348,
        np.array([298.4]),
        part=True,
    )
    assert_simple_key_core(
        TEST_DATA_10,
        "airTemperature",
        "stationNumber",
        [348, 408],
        np.array([298.4, 301]),
        part=True,
    )
    assert_simple_key_core(
        TEST_DATA_11,
        "airTemperature",
        "ident",
        "UOZDOZ2S",
        np.array([216.7, 217.2, 222.4, 222.7]),
    )


def assert_temp_profile_core(path, param, vert_sign_value, ref_param, ref_pressure):
    # type: (str, str, T.Any, T.Any, T.Any) -> None
    columns = [param, "pressure", "verticalSoundingSignificance"]
    filters = {
        "blockNumber": 71,
        "stationNumber": 907,
        "verticalSoundingSignificance": vert_sign_value,
    }

    res = pdbufr.read_bufr(path, columns=columns, filters=filters)

    ref_cnt = len(ref_param) if ref_param is not None else 0
    assert len(res) == ref_cnt
    if ref_cnt > 0:
        np.allclose(res[param], ref_param)
        np.allclose(res["pressure"], ref_pressure)


def test_temp_profile() -> None:
    assert_temp_profile_core(
        TEST_DATA_10,
        "airTemperature",
        32,
        np.array([259.7, 258.1, 253.1, 241.7, 228.1, 219.1, 216.3]),
        np.array([100000, 92500, 85000, 70000, 50000, 40000, 30000]),
    )
    assert_temp_profile_core(
        TEST_DATA_10,
        "dewpointTemperature",
        32,
        np.array([258.3, 256.2, 251, 238.3, 220.1, 213.1, 204.3]),
        np.array([100000, 92500, 85000, 70000, 50000, 40000, 30000]),
    )
    assert_temp_profile_core(
        TEST_DATA_10,
        "airTemperature",
        4,
        np.array(
            [
                261.1,
                261.7,
                245.3,
                242.9,
                242.3,
                239.7,
                231.1,
                229.9,
                228.9,
                223.1,
                220.1,
                218.1,
                214.9,
                216.1,
                218.5,
                218.5,
            ]
        ),
        np.array(
            [
                99800,
                99100,
                75100,
                72400,
                71700,
                65800,
                54600,
                53300,
                51200,
                43700,
                40900,
                39100,
                33700,
                28700,
                26300,
                25800,
            ]
        ),
    )
    assert_temp_profile_core(
        TEST_DATA_10, "airTemperature", 68, np.array([258.3]), np.array([100300])
    )
    assert_temp_profile_core(TEST_DATA_10, "airTemperature", 0, None, None)


def assert_nested_coords_core(
    path: str,
    param: str,
    coord_key_1: str,
    coord_value_1: T.Any,
    coord_key_2: str,
    coord_value_2: T.Any,
    ref_param: T.Any,
    ref_level: T.Any,
    part: bool = False,
) -> None:
    columns = [param, coord_key_1]
    if coord_value_2 == "_ANY_":
        columns.append(coord_key_2)
        filters = {coord_key_1: coord_value_1}
    else:
        filters = {coord_key_1: coord_value_1, coord_key_2: coord_value_2}

    res = pdbufr.read_bufr(path, columns=columns, filters=filters)

    ref_cnt = len(ref_param) if ref_param is not None else 0
    if ref_cnt > 0:
        if part:
            assert len(res) > ref_cnt
            np.allclose(res[param][0:ref_cnt], ref_param)
            np.allclose(res[coord_key_1][0:ref_cnt], ref_level)
        else:
            assert len(res) == ref_cnt
            np.allclose(res[param], ref_param)
            np.allclose(res[coord_key_1], ref_level)
    else:
        assert len(res) == ref_cnt


def test_nested_coords() -> None:
    # uncompressed
    assert_nested_coords_core(
        TEST_DATA_7,
        "airTemperatureAt2M",
        "ensembleMemberNumber",
        4,
        "timePeriod",
        24,
        np.array([291.3]),
        np.array([4]),
    )
    assert_nested_coords_core(
        TEST_DATA_7,
        "airTemperatureAt2M",
        "ensembleMemberNumber",
        4,
        "timePeriod",
        [12, 24, 48],
        np.array([291.3, 291.3, 290.9]),
        np.array([4, 4, 4]),
    )

    # compressed
    assert_nested_coords_core(
        TEST_DATA_9,
        "cape",
        "ensembleMemberNumber",
        4,
        "timePeriod",
        66,
        np.array([0.4]),
        np.array([4]),
    )
    assert_nested_coords_core(
        TEST_DATA_9,
        "cape",
        "ensembleMemberNumber",
        4,
        "timePeriod",
        [12, 24, 48],
        np.array([21, 0, 0.3]),
        np.array([4, 4, 4]),
    )

    assert_nested_coords_core(
        TEST_DATA_8,
        "significandOfVolumetricMixingRatio",
        "firstOrderStatistics",
        15,
        "nonCoordinatePressure",
        "_ANY_",
        np.array(
            [
                8531573,
                8486850,
                8493462,
                8505746,
                8512570,
                8518761,
                8525994,
                8528777,
                8479435,
                8246611,
                7677292,
                6018766,
                8533734,
            ]
        ),
        np.array([15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15]),
        part=True,
    )


def test_new_synop_data() -> None:
    columns_1 = (
        "stationNumber",
        "heightOfStationGroundAboveMeanSeaLevel",
        "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
        "airTemperature",
        "dewpointTemperature",
    )

    expected_first_row = {
        "stationNumber": 948,
        "heightOfStationGroundAboveMeanSeaLevel": 91.0,
        "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 1.5,
        "airTemperature": 300.45,
        "dewpointTemperature": 295.15,
    }

    expected_second_row = {
        "stationNumber": 766,
        "heightOfStationGroundAboveMeanSeaLevel": 748.1,
        "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 2,
        "airTemperature": 269.25,
        "dewpointTemperature": 263.55,
    }

    expected_third_row = {
        "stationNumber": 257,
        "heightOfStationGroundAboveMeanSeaLevel": 3950.0,
        "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": 1.5,
        "airTemperature": 276.35,
        "dewpointTemperature": 263.05,
    }

    ref = pd.DataFrame([expected_first_row, expected_second_row, expected_third_row])

    res = pdbufr.read_bufr(TEST_DATA_12, columns=columns_1)

    assert len(res) == 3
    assert_frame_equal(res, ref[res.columns])

    columns_2 = (
        "stationNumber",
        "heightOfStationGroundAboveMeanSeaLevel",
        "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform",
        "airTemperature",
        "dewpointTemperature",
        "windDirection",
        "windSpeed",
    )
    filters = {
        "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": slice(1, 20),
    }
    res = pdbufr.read_bufr(
        TEST_DATA_12, columns=columns_2, filters=filters, required_columns=False
    )

    assert len(res) == 14


def test_aircraft_compressed_with_string() -> None:
    columns = (
        "latitude",
        "longitude",
        "aircraftRegistrationNumberOrOtherIdentification",
        "airTemperature",
    )

    expected_first_row = {
        "aircraftRegistrationNumberOrOtherIdentification": "M87670b",
        "latitude": 40.6605,
        "longitude": -3.18049,
        "airTemperature": 288.9,
    }

    expected_second_row = {
        "aircraftRegistrationNumberOrOtherIdentification": "M519140",
        "latitude": 40.2453,
        "longitude": 3.94982,
        "airTemperature": 273.65,
    }

    expected_last_row = {
        "aircraftRegistrationNumberOrOtherIdentification": "M08f92c",
        "latitude": 39.8098,
        "longitude": -1.21851,
        "airTemperature": 227.9,
    }

    ref = pd.DataFrame([expected_first_row, expected_second_row, expected_last_row])

    res = pdbufr.read_bufr(TEST_DATA_13, columns=columns)

    assert len(res) == 186
    res = res.iloc[[0, 1, -1]].reset_index(drop=True)
    assert_frame_equal(res, ref[res.columns])


def test_message_structure_cache() -> None:
    columns = (
        "stationNumber",
        "timePeriod",
        "maximumWindGustDirection",
        "maximumWindGustSpeed",
    )

    ref = {
        "stationNumber": {0: 603, 1: 603, 2: 603, 3: 641, 4: 641, 5: 641},
        "timePeriod": {0: -10, 1: -60, 2: -180, 3: -10, 4: -60, 5: -180},
        "maximumWindGustDirection": {0: 130, 1: 130, 2: 50, 3: 40, 4: 40, 5: 40},
        "maximumWindGustSpeed": {
            0: 2.0,
            1: 2.4000000000000004,
            2: 3.5,
            3: 8.9,
            4: 8.9,
            5: 9.5,
        },
    }

    f = download_test_data("message_structure_diff_2.bufr")
    res = pdbufr.read_bufr(f, columns=columns)

    assert len(res) == 6
    assert res.to_dict() == ref
