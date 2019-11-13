#
# Copyright 2019 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import pandas as pd
import numpy as np
import pytest

import pdbufr


SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'sample-data')
TEST_DATA_1 = os.path.join(SAMPLE_DATA_FOLDER, 'obs_3day.bufr')
TEST_DATA_2 = os.path.join(SAMPLE_DATA_FOLDER, 'synop_multi_subset_uncompressed.bufr')
TEST_DATA_3 = os.path.join(SAMPLE_DATA_FOLDER, 'temp.bufr')
TEST_DATA_4 = os.path.join(
    SAMPLE_DATA_FOLDER,
    'M02-HIRS-HIRxxx1B-NA-1.0-20181122114854.000000000Z-20181122132602-1304602.bufr',
)
# contains compressed subsets - each subset with multiple locations
TEST_DATA_5 = os.path.join(SAMPLE_DATA_FOLDER, 'tropical_cyclone.bufr')

# contains uncompressed subsets (1 message)
TEST_DATA_6 = os.path.join(SAMPLE_DATA_FOLDER, 'wave_uncompressed.bufr')

# contains 1 message - each subset with multiple timePeriods
TEST_DATA_7 = os.path.join(SAMPLE_DATA_FOLDER, 'ens_multi_subset_uncompressed.bufr')

# contains 3 messages - each with 128 compressed subsets
TEST_DATA_8 = os.path.join(SAMPLE_DATA_FOLDER, 'compress_3.bufr')

# contains 1 message - with 51 compressed subsets with multiple timePeriods
TEST_DATA_9 = os.path.join(SAMPLE_DATA_FOLDER, 'ens_multi_subset_compressed.bufr')


def test_read_bufr_one_subset_one_filters():
    res = pdbufr.read_bufr(TEST_DATA_1, columns=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in res
    assert len(res) == 50

    res = pdbufr.read_bufr(TEST_DATA_1, columns=('latitude',), filters={'rdbtimeTime': '115557'})

    assert len(res) == 6

    res = pdbufr.read_bufr(TEST_DATA_1, columns=('latitude',), filters={'count': 1})

    assert len(res) == 1

    res = pdbufr.read_bufr(TEST_DATA_1, columns=('latitude',), filters={'stationNumber': 894})

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_1, columns=('latitude',), filters={'stationNumber': [894, 103]}
    )

    assert len(res) == 2


def test_read_bufr_one_subset_one_observation_data():
    columns = (
        'count',
        'stationNumber',
        'data_datetime',
        'latitude',
        'longitude',
        'heightOfStation',
        'airTemperatureAt2M',
        'dewpointTemperatureAt2M',
        'horizontalVisibility',
    )
    expected_first_row = {
        'count': 1,
        'stationNumber': 894.0,
        'data_datetime': pd.Timestamp('2017-04-25 12:00:00'),
        'latitude': 49.43000000000001,
        'longitude': -2.6,
        'heightOfStation': 101.0,
        'airTemperatureAt2M': 282.40000000000003,
        'dewpointTemperatureAt2M': 274.0,
        'horizontalVisibility': 55000.0,
    }

    res = pdbufr.read_bufr(TEST_DATA_1, columns=columns)

    assert len(res) == 50
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_multiple_uncompressed_subsets_one_observation():
    res = pdbufr.read_bufr(TEST_DATA_2, columns=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in dict(res)
    assert len(res) == 12

    res = pdbufr.read_bufr(TEST_DATA_2, columns=('latitude',), filters={'observedData': 1})

    assert len(res) == 12

    res = pdbufr.read_bufr(TEST_DATA_2, columns=('latitude',), filters={'stationNumber': 27})

    assert len(res) == 1

    res = pdbufr.read_bufr(TEST_DATA_2, columns=('latitude',), filters={'stationNumber': [27, 84]})

    assert len(res) == 2

    columns = ['latitude', 'longitude', 'heightOfStationGroundAboveMeanSeaLevel', 'airTemperature']
    expected_first_row = {
        'latitude': 69.65230000000001,
        'longitude': 18.905700000000003,
        'heightOfStationGroundAboveMeanSeaLevel': 20.0,
        'airTemperature': 276.45,
    }

    res = pdbufr.read_bufr(TEST_DATA_2, columns=columns, filters={'stationNumber': 27})

    assert len(res) == 1
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_one_subsets_multiple_observations_filters():
    res = pdbufr.read_bufr(TEST_DATA_3, columns=('latitude',), filters={'stationNumber': 907})

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_3, columns=('latitude',), filters={'pressure': [100000, 26300]}
    )

    assert len(res) == 425


def test_read_bufr_one_subsets_multiple_observations_data():
    columns = [
        'stationNumber',
        'data_datetime',
        'longitude',
        'latitude',
        'heightOfStation',
        'pressure',
        'airTemperature',
    ]
    expected_first_row = {
        'stationNumber': 907,
        'data_datetime': pd.Timestamp('2008-12-08 12:00:00'),
        'longitude': -78.08000000000001,
        'latitude': 58.470000000000006,
        'heightOfStation': 26,
        'pressure': 100000.0,
        'airTemperature': 259.7,
    }
    expected_second_row = {
        'stationNumber': 823,
        'data_datetime': pd.Timestamp('2008-12-08 12:00:00'),
        'longitude': -73.67,
        'latitude': 53.75000000000001,
        'heightOfStation': 302,
        'pressure': 100000.0,
        'airTemperature': -1e100,
    }

    res = pdbufr.read_bufr(TEST_DATA_3, columns=columns, filters={'pressure': 100000})

    assert len(res) == 408
    assert res.iloc[0].to_dict() == expected_first_row
    assert res.iloc[1].to_dict() == expected_second_row


def test_read_bufr_multiple_compressed_subsets_multiple_observations_filters():
    res = pdbufr.read_bufr(TEST_DATA_4, columns=('latitude',), filters={'hour': 11, 'minute': 48})

    assert len(res) == 56

    res = pdbufr.read_bufr(
        TEST_DATA_4, columns=('latitude',), filters={'hour': 11, 'minute': [48, 49]}
    )

    assert len(res) == 616


def test_read_bufr_multiple_compressed_subsets_multiple_observations_data():
    columns = [
        'data_datetime',
        'longitude',
        'latitude',
        'heightOfStation',
        'tovsOrAtovsOrAvhrrInstrumentationChannelNumber',
        'brightnessTemperature',
    ]
    expected_first_row = {
        'data_datetime': pd.Timestamp('2018-11-22 11:48:54'),
        'longitude': -9.201400000000001,
        'latitude': 53.354200000000006,
        'heightOfStation': 828400.0,
        'tovsOrAtovsOrAvhrrInstrumentationChannelNumber': 2.0,
        'brightnessTemperature': 218.76,
    }

    res = pdbufr.read_bufr(
        TEST_DATA_4,
        columns=columns,
        filters={'hour': 11, 'minute': 48, 'tovsOrAtovsOrAvhrrInstrumentationChannelNumber': 2},
    )

    assert len(res) == 56
    assert res.iloc[0].to_dict() == expected_first_row


def test_temp_single_station_1():
    columns = [
        'WMO_station_id',
        'stationNumber',
        'data_datetime',
        'longitude',
        'latitude',
        'pressure',
        'verticalSoundingSignificance',
        'airTemperature',
    ]

    ref_num = 25

    ref = {
        'WMO_station_id': np.full(ref_num, 71823),
        'stationNumber': np.full(ref_num, 823),
        'latitude': np.full(ref_num, 53.75),
        'longitude': np.full(ref_num, -73.67),
        'pressure': [
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
        'verticalSoundingSignificance': [
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
        'airTemperature': [
            -1e100,
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

    res = pdbufr.read_bufr(TEST_DATA_3, columns=columns, filters={'stationNumber': 823})

    for k in ref.keys():
        assert np.allclose(res[k].values, ref[k])


def test_temp_single_station_2():
    columns = [
        'stationNumber',
        'data_datetime',
        'longitude',
        'latitude',
        'pressure',
        'airTemperature',
    ]

    ref_num = 8

    ref = {
        'stationNumber': np.full(ref_num, 823),
        'latitude': np.full(ref_num, 53.75),
        'longitude': np.full(ref_num, -73.67),
        'pressure': [100000.0, 92500.0, 85000.0, 70000.0, 50000.0, 40000.0, 30000.0, 25000.0],
        'airTemperature': [-1e100, 255.3, 253.3, 241.9, 229.3, 222.9, 218.9, 221.10000000000002],
    }

    res = pdbufr.read_bufr(
        TEST_DATA_3,
        columns=columns,
        filters={'stationNumber': 823, 'verticalSoundingSignificance': 32},
    )

    for k in ref.keys():
        assert np.allclose(res[k].values, ref[k])


def test_temp_single_station_3():
    columns = [
        'stationNumber',
        'data_datetime',
        'longitude',
        'latitude',
        'airTemperature',
        'pressure',
    ]

    ref_num = 2

    ref = {
        'stationNumber': np.full(ref_num, 823),
        'latitude': np.full(ref_num, 53.75),
        'longitude': np.full(ref_num, -73.67),
        'pressure': [92500.0, 40000.0],
        'airTemperature': [255.3, 222.9],
    }

    res = pdbufr.read_bufr(
        TEST_DATA_3,
        columns=columns,
        filters={
            'stationNumber': 823,
            'verticalSoundingSignificance': 32,
            'pressure': [40000.0, 92500.0],
        },
    )

    for k in ref.keys():
        assert np.allclose(res[k].values, ref[k])


def test_tropicalcyclone_1():
    columns = ['data_datetime', 'longitude', 'latitude', 'windSpeedAt10M']

    res = pdbufr.read_bufr(
        TEST_DATA_5, columns=columns, filters={'stormIdentifier': '70E', 'ensembleMemberNumber': 4}
    )

    assert len(res) == 67

    res = pdbufr.read_bufr(
        TEST_DATA_5,
        columns=columns,
        filters={'stormIdentifier': '70E', 'ensembleMemberNumber': 4},
        required_columns=False,
    )

    assert len(res) == 69


def test_tropicalcyclone_2():
    columns = ['data_datetime', 'longitude', 'latitude', 'windSpeedAt10M']

    ref = {
        'latitude': [
            12.700000000000001,
            13.0,
            12.700000000000001,
            -1e100,
            12.5,
            12.200000000000001,
            12.5,
            12.700000000000001,
            12.700000000000001,
            14.1,
            13.6,
            14.1,
            14.1,
            13.9,
            15.3,
            15.0,
            14.700000000000001,
            15.0,
            14.4,
            14.4,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
        ],
        'longitude': [
            -124.9,
            -125.5,
            -125.2,
            -1e100,
            -127.5,
            -128.0,
            -128.0,
            -126.60000000000001,
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
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
        ],
        'windSpeedAt10M': [
            30.400000000000002,
            17.0,
            16.5,
            -1e100,
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
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
            -1e100,
        ],
    }

    res = pdbufr.read_bufr(
        TEST_DATA_5,
        columns=columns,
        filters={
            'stormIdentifier': '70E',
            'ensembleMemberNumber': 4,
            'meteorologicalAttributeSignificance': 3,
        },
    )

    for k in ref.keys():
        assert np.allclose(res[k].values, ref[k])


def test_wave_1():
    columns = ['data_datetime', 'longitude', 'latitude', 'significantWaveHeight']
    expected_0 = {
        'latitude': -28.866670000000003,
        'longitude': 153.38333,
        'significantWaveHeight': 2.34,
        'data_datetime': pd.Timestamp('2017-11-02 10:00:00'),
    }
    expected_1 = {
        'latitude': -30.366670000000003,
        'longitude': 153.36667,
        'significantWaveHeight': -1e100,
        'data_datetime': pd.Timestamp('2017-11-02 10:00:00'),
    }

    res = pdbufr.read_bufr(TEST_DATA_6, columns=columns)

    assert res.iloc[0].to_dict() == expected_0
    assert res.iloc[1].to_dict() == expected_1


def test_ens_uncompressed():
    columns = ['longitude', 'latitude', 'ensembleMemberNumber', 'timePeriod', 'airTemperatureAt2M']

    res = pdbufr.read_bufr(TEST_DATA_7, columns=columns)

    ref = {
        'latitude': [51.52, 51.52],
        'longitude': [0.9700000000000001, 0.9700000000000001],
        'ensembleMemberNumber': [0, 0],
        'timePeriod': [0, 6],
        'airTemperatureAt2M': [292.7, 291.6],
    }

    assert len(res) == 3111

    for k in ref.keys():
        assert np.allclose(res[k].values[0:2], ref[k])

def test_ens_compressed():
    columns = ['longitude', 'latitude', 'ensembleMemberNumber', 'timePeriod', 'cape']

    res = pdbufr.read_bufr(TEST_DATA_9, columns=columns, 
        filters={'timePeriod': [0, 24], 'ensembleMemberNumber': [2, 5]})

    ref = {
        'latitude': [51.52, 51.52, 51.52, 51.52],
        'longitude': [0.9700000000000001, 0.9700000000000001, 0.9700000000000001, 0.9700000000000001],
        'ensembleMemberNumber': [2, 2, 5, 5],
        'timePeriod': [0, 24, 0, 24],
        'cape': [41.9, 0, 14.4, 0],
    }

    assert len(res) == 4

    for k in ref.keys():
        assert np.allclose(res[k].values[0:4], ref[k])


@pytest.mark.xfail
def test_sat_compressed_1():
    columns = [
        'data_datetime',
        'latitude',
        'longitude',
        'nonCoordinateLatitude',
        'nonCoordinateLongitude',
        'significandOfVolumetricMixingRatio',
        'nonCoordinatePressure',
    ]

    expected_first_row = {
        'data_datetime': pd.Timestamp('2015-08-21 01:59:05'),
        'latitude': -44.833890000000004,
        'longitude': 171.16350000000003,
        'nonCoordinateLatitude': -44.82399,
        'nonCoordinateLongitude': 171.05569000000003,
        'nonCoordinatePressure': 8555.0,
        'significandOfVolumetricMixingRatio': 8531573,
    }

    expected_second_row = {
        'data_datetime': pd.Timestamp('2015-08-21 01:59:05'),
        'latitude': -44.833890000000004,
        'longitude': 171.16350000000003,
        'nonCoordinateLatitude': -44.82399,
        'nonCoordinateLongitude': 171.05569000000003,
        'nonCoordinatePressure': 17100.100000000002,
        'significandOfVolumetricMixingRatio': 8486850,
    }

    expected_12_row = {
        'data_datetime': pd.Timestamp('2015-08-21 01:59:05'),
        'latitude': -44.833890000000004,
        'longitude': 171.16350000000003,
        'nonCoordinateLatitude': -44.82399,
        'nonCoordinateLongitude': 171.05569000000003,
        'nonCoordinatePressure': 102550.0,
        'significandOfVolumetricMixingRatio': 6018766,
    }

    res = pdbufr.read_bufr(TEST_DATA_8, columns=columns, filters={'firstOrderStatistics': 15})

    assert len(res) == 4992 
    # assert len(res) == 4224

    assert res.iloc[0].to_dict() == expected_first_row
    assert res.iloc[1].to_dict() == expected_second_row
    assert res.iloc[11].to_dict() == expected_12_row
