import os

import pandas as pd

from pdbufr import read_bufr


SAMPLE_DATA_FOLDER = os.path.join('/Users/amici/devel/ECM/pdbufr/tests', 'sample-data')
TEST_DATA_1 = os.path.join(SAMPLE_DATA_FOLDER, 'obs_3day.bufr')
TEST_DATA_2 = os.path.join(SAMPLE_DATA_FOLDER, 'synop_multi_subset_uncompressed.bufr')
TEST_DATA_3 = os.path.join(SAMPLE_DATA_FOLDER, 'temp.bufr')
TEST_DATA_4 = os.path.join(
    SAMPLE_DATA_FOLDER,
    'M02-HIRS-HIRxxx1B-NA-1.0-20181122114854.000000000Z-20181122132602-1304602.bufr',
)


def test_read_bufr_one_subset_one_observation_filters():
    res = read_bufr(TEST_DATA_1, selections=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in res
    assert len(res) == 50

    res = read_bufr(
        TEST_DATA_1, selections=('latitude',), header_filters={'rdbtimeTime': '115557'}
    )

    assert len(res) == 6

    res = read_bufr(
        TEST_DATA_1, selections=('latitude',), observation_filters={'stationNumber': 894}
    )

    assert len(res) == 1

    res = read_bufr(
        TEST_DATA_1, selections=('latitude',), observation_filters={'stationNumber': [894, 103]}
    )

    assert len(res) == 2


def test_read_bufr_one_subset_one_observation_data():
    selections = (
        'stationNumber',
        'datetime',
        'latitude',
        'longitude',
        'heightOfStation',
        'airTemperatureAt2M',
        'dewpointTemperatureAt2M',
        'horizontalVisibility',
    )
    expected_first_row = {
        'stationNumber': 894.0,
        'datetime': pd.Timestamp('2017-04-25 12:00:00'),
        'latitude': 49.43000000000001,
        'longitude': -2.6,
        'heightOfStation': 101.0,
        'airTemperatureAt2M': 282.40000000000003,
        'dewpointTemperatureAt2M': 274.0,
        'horizontalVisibility': 55000.0,
    }

    res = read_bufr(TEST_DATA_1, selections=selections)

    assert len(res) == 50
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_multiple_uncompressed_subsets_one_observation():
    res = read_bufr(TEST_DATA_2, selections=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in dict(res)
    assert len(res) == 12

    res = read_bufr(TEST_DATA_2, selections=('latitude',), header_filters={'observedData': 1})

    assert len(res) == 12

    res = read_bufr(
        TEST_DATA_2, selections=('latitude',), observation_filters={'stationNumber': 27}
    )

    assert len(res) == 1

    res = read_bufr(
        TEST_DATA_2, selections=('latitude',), observation_filters={'stationNumber': [27, 84]}
    )

    assert len(res) == 2

    selections = [
        'latitude',
        'longitude',
        'heightOfStationGroundAboveMeanSeaLevel',
        'airTemperature',
    ]
    expected_first_row = {
        'latitude': 69.65230000000001,
        'longitude': 18.905700000000003,
        'heightOfStationGroundAboveMeanSeaLevel': 20.0,
        'airTemperature': 276.45,
    }

    res = read_bufr(TEST_DATA_2, selections=selections, observation_filters={'stationNumber': 27})

    assert len(res) == 1
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_one_subsets_multiple_observations_filters():
    res = read_bufr(
        TEST_DATA_3, selections=('latitude',), observation_filters={'stationNumber': 907}
    )

    assert len(res) == 1

    res = read_bufr(
        TEST_DATA_3, selections=('latitude',), observation_filters={'pressure': [100000, 26300]}
    )

    assert len(res) == 425


def test_read_bufr_one_subsets_multiple_observations_data():
    selections = [
        'stationNumber',
        'datetime',
        'longitude',
        'latitude',
        'heightOfStation',
        'pressure',
        'airTemperature',
    ]
    expected_first_row = {
        'stationNumber': 907,
        'datetime': pd.Timestamp('2008-12-08 12:00:00'),
        'longitude': -78.08000000000001,
        'latitude': 58.470000000000006,
        'heightOfStation': 26,
        'pressure': 100000.0,
        'airTemperature': 259.7,
    }
    expected_second_row = {
        'stationNumber': 823,
        'datetime': pd.Timestamp('2008-12-08 12:00:00'),
        'longitude': -73.67,
        'latitude': 53.75000000000001,
        'heightOfStation': 302,
        'pressure': 100000.0,
        'airTemperature': -1e100,
    }

    res = read_bufr(TEST_DATA_3, selections=selections, observation_filters={'pressure': 100000})

    assert len(res) == 408
    assert res.iloc[0].to_dict() == expected_first_row
    assert res.iloc[1].to_dict() == expected_second_row


def test_read_bufr_multiple_compressed_subsets_multiple_observations_filters():
    res = read_bufr(
        TEST_DATA_4, selections=('latitude',), observation_filters={'hour': 11, 'minute': 48}
    )

    assert len(res) == 56

    res = read_bufr(
        TEST_DATA_4, selections=('latitude',), observation_filters={'hour': 11, 'minute': [48, 49]}
    )

    assert len(res) == 616


def test_read_bufr_multiple_compressed_subsets_multiple_observations_data():
    selections = [
        'datetime',
        'longitude',
        'latitude',
        'heightOfStation',
        'tovsOrAtovsOrAvhrrInstrumentationChannelNumber',
        'brightnessTemperature',
    ]
    expected_first_row = {
        'datetime': pd.Timestamp('2018-11-22 11:48:00'),
        'longitude': -9.201400000000001,
        'latitude': 53.354200000000006,
        'heightOfStation': 828400.0,
        'tovsOrAtovsOrAvhrrInstrumentationChannelNumber': 2.0,
        'brightnessTemperature': 218.76,
    }

    res = read_bufr(
        TEST_DATA_4,
        selections=selections,
        observation_filters={
            'hour': 11,
            'minute': 48,
            'tovsOrAtovsOrAvhrrInstrumentationChannelNumber': 2,
        },
    )

    assert len(res) == 56
    assert res.iloc[0].to_dict() == expected_first_row
