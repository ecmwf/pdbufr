import os

import pandas as pd

from pdbufr import read_bufr


SAMPLE_DATA_FOLDER = os.path.join('/Users/amici/devel/ECM/pdbufr/tests', 'sample-data')
TEST_DATA_1 = os.path.join(SAMPLE_DATA_FOLDER, 'obs_3day.bufr')
TEST_DATA_2 = os.path.join(SAMPLE_DATA_FOLDER, 'synop_multi_subset_uncompressed.bufr')
TEST_DATA_3 = os.path.join(
    SAMPLE_DATA_FOLDER,
    'M02-HIRS-HIRxxx1B-NA-1.0-20181122114854.000000000Z-20181122132602-1304602.bfr',
)


def test_read_bufr_data1():
    res = read_bufr(TEST_DATA_1, selections=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert '#1#latitude' in res
    assert len(res) == 50

    res = read_bufr(TEST_DATA_1, selections=('latitude'), header_filters={'rdbtimeTime': '115557'})

    assert len(res) == 6

    res = read_bufr(
        TEST_DATA_1, selections=('latitude',), observation_filters={'stationNumber': 894}
    )

    assert len(res) == 1

    res = read_bufr(
        TEST_DATA_1, selections=('latitude',), observation_filters={'stationNumber': [894, 103]}
    )

    assert len(res) == 2

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
        '#1#airTemperatureAt2M': 282.40000000000003,
        'datetime': pd.Timestamp('2017-04-25 12:00:00'),
        '#1#dewpointTemperatureAt2M': 274.0,
        '#1#heightOfStation': 101,
        '#1#horizontalVisibility': 55000.0,
        '#1#latitude': 49.43000000000001,
        '#1#longitude': -2.6,
        '#1#stationNumber': 894,
    }

    res = read_bufr(TEST_DATA_1, selections=selections)

    assert len(res) == 50
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_data2():
    res = read_bufr(TEST_DATA_2, selections=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert '#1#latitude' in dict(res)
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
        'datetime',
        'latitude',
        'longitude',
        'heightOfStationGroundAboveMeanSeaLevel',
        'airTemperature',
    ]
    expected_first_row = {
        'datetime': pd.Timestamp('2015-01-26 10:00:00'),
        '#1#latitude': 69.65230000000001,
        '#1#longitude': 18.905700000000003,
        '#1#heightOfStationGroundAboveMeanSeaLevel': 20.0,
        '#1#airTemperature': 276.45,
    }

    res = read_bufr(TEST_DATA_2, selections=selections, observation_filters={'stationNumber': 27})

    assert len(res) == 1
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_data3():
    res = read_bufr(TEST_DATA_3, selections=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert '#1#latitude' in res
    assert len(res) == 51968

    res = read_bufr(
        TEST_DATA_3, selections=('latitude',), header_filters={'numberOfSubsets': 1008}
    )

    assert len(res) == 19152

    res = read_bufr(
        TEST_DATA_3, selections=('latitude',), observation_filters={'hour': 11, 'minute': 48}
    )

    assert len(res) == 56

    res = read_bufr(
        TEST_DATA_3, selections=('latitude',), observation_filters={'hour': 11, 'minute': [48, 49]}
    )

    assert len(res) == 616

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
        '#1#heightOfStation': 828400.0,
        '#1#latitude': 53.354200000000006,
        '#1#longitude': -9.201400000000001,
        '#1#brightnessTemperature': 220.23000000000002,
        '#2#brightnessTemperature': 218.76,
        '#3#brightnessTemperature': 219.02,
        '#4#brightnessTemperature': 221.21,
        '#5#brightnessTemperature': 228.05,
        '#6#brightnessTemperature': 237.18,
        '#7#brightnessTemperature': 247.08,
        '#8#brightnessTemperature': 269.33,
        '#9#brightnessTemperature': 238.66,
        '#10#brightnessTemperature': 265.84000000000003,
        '#11#brightnessTemperature': 243.96,
        '#12#brightnessTemperature': 220.83,
        '#13#brightnessTemperature': 257.1,
        '#14#brightnessTemperature': 241.44,
        '#15#brightnessTemperature': 233.35,
        '#16#brightnessTemperature': 228.98000000000002,
        '#17#brightnessTemperature': 263.14,
        '#18#brightnessTemperature': 273.73,
        '#19#brightnessTemperature': 278.22,
        '#20#brightnessTemperature': 0.74,
        '#21#brightnessTemperature': 0.0,
        '#22#brightnessTemperature': 0.79,
        '#23#brightnessTemperature': 0.75,
        '#24#brightnessTemperature': 0.63,
        '#25#brightnessTemperature': 0.54,
        '#26#brightnessTemperature': 0.62,
        '#27#brightnessTemperature': 0.16,
        '#28#brightnessTemperature': 0.33,
        '#29#brightnessTemperature': 0.5,
        '#30#brightnessTemperature': 0.73,
        '#31#brightnessTemperature': 0.66,
        '#32#brightnessTemperature': 5.75,
        '#33#brightnessTemperature': 5.49,
        '#34#brightnessTemperature': 4.62,
        '#35#brightnessTemperature': 4.61,
        '#36#brightnessTemperature': 5.0,
        '#37#brightnessTemperature': 6.140000000000001,
        '#38#brightnessTemperature': 3.33,
        '#1#channelRadiance': 3,
    }

    res = read_bufr(
        TEST_DATA_3, selections=selections, observation_filters={'hour': 11, 'minute': 48}
    )

    assert len(res) == 56
    assert res.iloc[0].to_dict() == expected_first_row
