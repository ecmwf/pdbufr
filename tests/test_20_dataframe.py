import os

import pandas as pd

from pdbufr import read_bufr


SAMPLE_DATA_FOLDER = os.path.join('/Users/amici/devel/ECM/pdbufr/tests', 'sample-data')
TEST_DATA_1 = os.path.join(SAMPLE_DATA_FOLDER, 'obs_3day.bufr')
TEST_DATA_2 = os.path.join(
    SAMPLE_DATA_FOLDER,
    'M02-HIRS-HIRxxx1B-NA-1.0-20181122114854.000000000Z-20181122132602-1304602.bfr',
)


def test_read_bufr_data1():
    res = read_bufr(TEST_DATA_1, selections=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in res
    assert len(res) == 50

    res = read_bufr(
        TEST_DATA_1, selections=('latitude'), header_filters={'rdbtimeTime': '115557'}
    )

    assert len(res) == 6

    res = read_bufr(
        TEST_DATA_1, selections=('latitude',), observation_filters={'stationNumber': 894}
    )

    assert len(res) == 1

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
        'airTemperatureAt2M': 282.40000000000003,
        'datetime': pd.Timestamp('2017-04-25 12:00:00'),
        'dewpointTemperatureAt2M': 274.0,
        'heightOfStation': 101,
        'horizontalVisibility': 55000.0,
        'latitude': 49.43000000000001,
        'longitude': -2.6,
        'stationNumber': 894,
    }

    res = read_bufr(TEST_DATA_1, selections=selections)

    assert len(res) == 50
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_data2():
    res = read_bufr(TEST_DATA_2, selections=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in res
    assert len(res) == 51968

    res = read_bufr(
        TEST_DATA_2, selections=('latitude',), header_filters={'numberOfSubsets': 1008}
    )

    assert len(res) == 19152

    res = read_bufr(
        TEST_DATA_2, selections=('latitude',), observation_filters={'hour': 11, 'minute': 48}
    )

    assert len(res) == 56

    selections = [
        'datetime',
        'latitude',
        'longitude',
        'heightOfStation',
        'brightnessTemperature',
        'channelRadiance',
    ]
    expected_first_row = {
        'datetime': pd.Timestamp('2018-11-22 11:48:00'),
        'heightOfStation': 828400.0,
        'latitude': 53.354200000000006,
        'longitude': -9.201400000000001,
        'brightnessTemperature': 220.23000000000002,
        'channelRadiance': 3,
    }

    res = read_bufr(
        TEST_DATA_2, selections=selections, observation_filters={'hour': 11, 'minute': 48}
    )

    assert len(res) == 56
    assert res.iloc[0].to_dict() == expected_first_row


if __name__ == '__main__':
    test_read_bufr_data2()
