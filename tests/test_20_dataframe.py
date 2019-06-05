import os

import pandas as pd
import numpy as np

import pdbufr


SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'sample-data')
TEST_DATA_1 = os.path.join(SAMPLE_DATA_FOLDER, 'obs_3day.bufr')
TEST_DATA_2 = os.path.join(SAMPLE_DATA_FOLDER, 'synop_multi_subset_uncompressed.bufr')
TEST_DATA_3 = os.path.join(SAMPLE_DATA_FOLDER, 'temp.bufr')
TEST_DATA_4 = os.path.join(
    SAMPLE_DATA_FOLDER,
    'M02-HIRS-HIRxxx1B-NA-1.0-20181122114854.000000000Z-20181122132602-1304602.bufr',
)
# contains compressed subsets
TEST_DATA_5 = os.path.join(SAMPLE_DATA_FOLDER, 'tropical_cyclone.bufr')

def test_read_bufr_one_subset_one_observation_filters():
    res = pdbufr.read_bufr(TEST_DATA_1, columns=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in res
    assert len(res) == 50

    res = pdbufr.read_bufr(
        TEST_DATA_1, columns=('latitude',), header_filters={'rdbtimeTime': '115557'}
    )

    assert len(res) == 6

    res = pdbufr.read_bufr(
        TEST_DATA_1, columns=('latitude',), observation_filters={'stationNumber': 894}
    )

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_1, columns=('latitude',), observation_filters={'stationNumber': [894, 103]}
    )

    assert len(res) == 2


def test_read_bufr_one_subset_one_observation_data():
    columns = (
        'stationNumber',
        'datetime',
        'latitude',
        'longitude',
        'heightOfStation',
        'airTemperatureAt2M',
        'dewpointTemperatureAt2M',
        'horizontalVisibility',
        'rdbtimeTime',
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
        'rdbtimeTime': '115225',
    }

    res = pdbufr.read_bufr(TEST_DATA_1, columns=columns)

    assert len(res) == 50
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_multiple_uncompressed_subsets_one_observation():
    res = pdbufr.read_bufr(TEST_DATA_2, columns=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in dict(res)
    assert len(res) == 12

    res = pdbufr.read_bufr(TEST_DATA_2, columns=('latitude',), header_filters={'observedData': 1})

    assert len(res) == 12

    res = pdbufr.read_bufr(
        TEST_DATA_2, columns=('latitude',), observation_filters={'stationNumber': 27}
    )

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_2, columns=('latitude',), observation_filters={'stationNumber': [27, 84]}
    )

    assert len(res) == 2

    columns = ['latitude', 'longitude', 'heightOfStationGroundAboveMeanSeaLevel', 'airTemperature']
    expected_first_row = {
        'latitude': 69.65230000000001,
        'longitude': 18.905700000000003,
        'heightOfStationGroundAboveMeanSeaLevel': 20.0,
        'airTemperature': 276.45,
    }

    res = pdbufr.read_bufr(TEST_DATA_2, columns=columns, observation_filters={'stationNumber': 27})

    assert len(res) == 1
    assert res.iloc[0].to_dict() == expected_first_row


def test_read_bufr_one_subsets_multiple_observations_filters():
    res = pdbufr.read_bufr(
        TEST_DATA_3, columns=('latitude',), observation_filters={'stationNumber': 907}
    )

    assert len(res) == 1

    res = pdbufr.read_bufr(
        TEST_DATA_3, columns=('latitude',), observation_filters={'pressure': [100000, 26300]}
    )

    assert len(res) == 425


def test_read_bufr_one_subsets_multiple_observations_data():
    columns = [
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

    res = pdbufr.read_bufr(TEST_DATA_3, columns=columns, observation_filters={'pressure': 100000})

    assert len(res) == 408
    assert res.iloc[0].to_dict() == expected_first_row
    assert res.iloc[1].to_dict() == expected_second_row


def test_read_bufr_multiple_compressed_subsets_multiple_observations_filters():
    res = pdbufr.read_bufr(
        TEST_DATA_4, columns=('latitude',), observation_filters={'hour': 11, 'minute': 48}
    )

    assert len(res) == 56

    res = pdbufr.read_bufr(
        TEST_DATA_4, columns=('latitude',), observation_filters={'hour': 11, 'minute': [48, 49]}
    )

    assert len(res) == 616


def test_read_bufr_multiple_compressed_subsets_multiple_observations_data():
    columns = [
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

    res = pdbufr.read_bufr(
        TEST_DATA_4,
        columns=columns,
        observation_filters={
            'hour': 11,
            'minute': 48,
            'tovsOrAtovsOrAvhrrInstrumentationChannelNumber': 2,
        },
    )

    assert len(res) == 56
    assert res.iloc[0].to_dict() == expected_first_row


def test_temp_single_station_1():
    columns = [
        'stationNumber',
        'datetime',
        'longitude',
        'latitude',
        'pressure',
        'verticalSoundingSignificance',
        'airTemperature'        
    ]
  
    ref_num = 25
    
    ref = {'stationNumber': np.full(ref_num, 823),
           'latitude': np.full(ref_num, 53.75),
           'longitude': np.full(ref_num, -73.67),
           'pressure': [100000.0, 97400.0, 93700.0, 92500.0,
                90600.0, 85000.0, 84700.0, 79200.0, 70000.0,
                69900.0, 64600.0, 60700.0, 59700.0, 58000.0,
                53400.0, 50000.0, 45200.0, 42300.0, 40000.0,
                37800.0, 30000.0, 29700.0, 25000.0, 23200.0,
                20500.0],
           'verticalSoundingSignificance': [32, 68, 4, 32, 4, 32, 4,
                4, 32, 4, 4, 4, 4, 4, 4, 32, 4, 4, 32, 20, 32, 4,
                32, 4, 4],
           'airTemperature': [-1e+100, 256.7, 255.10000000000002,
                255.3, 256.7, 253.3, 253.10000000000002, 248.9,
                241.9, 241.70000000000002, 239.70000000000002, 236.3,
                236.10000000000002, 234.5, 230.70000000000002, 229.3,
                226.3, 223.10000000000002, 222.9, 221.3, 218.9,
                218.9, 221.10000000000002, 223.10000000000002, 221.5]
    }
    
    res = pdbufr.read_bufr(TEST_DATA_3, columns=columns, observation_filters={'stationNumber': 823})
  
    
    for k in ref.keys():        
        assert(np.allclose(res[k].values, ref[k]))
  
  
def test_temp_single_station_2():
    columns = [
        'stationNumber',
        'datetime',
        'longitude',
        'latitude',
        'pressure',
        'airTemperature'        
    ]
  
    ref_num = 8
    
    ref = {'stationNumber': np.full(ref_num, 823),
           'latitude': np.full(ref_num, 53.75),
           'longitude': np.full(ref_num, -73.67),
           'pressure':   [100000.0, 92500.0, 85000.0, 70000.0, 50000.0, 40000.0, 30000.0, 25000.0],
           'airTemperature': [-1e+100, 255.3, 253.3, 241.9, 229.3, 222.9, 218.9, 221.10000000000002]
    }
    
    res = pdbufr.read_bufr(TEST_DATA_3, columns=columns, 
                        observation_filters={'stationNumber': 823, 'verticalSoundingSignificance': 32})
  
    for k in ref.keys():        
        assert(np.allclose(res[k].values, ref[k]))
   
   
def test_temp_single_station_3():
    columns = [
        'stationNumber',
        'datetime',
        'longitude',
        'latitude',
        'airTemperature',
        'pressure'
    ]
  
    ref_num = 2
    
    ref = {'stationNumber': np.full(ref_num, 823),
           'latitude': np.full(ref_num, 53.75),
           'longitude': np.full(ref_num, -73.67),
           'pressure': [92500.0, 40000.0],
           'airTemperature': [255.3, 222.9]
    }
         
    res = pdbufr.read_bufr(TEST_DATA_3, columns=columns, 
                        observation_filters={'stationNumber': 823,
                                             'verticalSoundingSignificance': 32,
                                             'pressure': [40000.0, 92500.0]})
  
    #print(res['pressure'].tolist())
    #print(res['airTemperature'].tolist())
  
    for k in ref.keys():        
        assert(np.allclose(res[k].values, ref[k]))


def test_tropicalcyclone_1():
    columns = [
        'datetime',
        'longitude',
        'latitude',
        'windSpeedAt10M'
    ]
  
    res = pdbufr.read_bufr(TEST_DATA_5, columns=columns,
                           observation_filters={'stormIdentifier': '70E','ensembleMemberNumber': 4})
  
    # assert len(res) == 34


def test_tropicalcyclone_2():
    columns = [
        'datetime',
        'longitude',
        'latitude',
        'windSpeedAt10M'
    ]
  
    ref_num = 34
    
    ref = {'latitude': [12.700000000000001, 13.0, 12.700000000000001, -1e+100, 12.5, 12.200000000000001, 
                        12.5, 12.700000000000001, 12.700000000000001, 14.1, 13.6, 14.1, 14.1, 13.9, 15.3,
                        15.0, 14.700000000000001, 15.0, 14.4, 14.4, -1e+100, -1e+100, -1e+100, -1e+100,
                        -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, 
                        -1e+100], 
           'longitude': [-124.9, -125.5, -125.2, -1e+100, -127.5, -128.0, -128.0, -126.60000000000001,
                         -128.3, -126.0, -128.9, -129.4, -130.5, -131.4, -128.9, -128.9, -130.3, -128.9,
                         -129.4, -127.5, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100,
                         -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100],
           'windSpeedAt10M': [30.400000000000002, 17.0, 16.5, -1e+100, 16.5, 15.4, 14.9, 12.4, 10.8,
                              11.8, 11.8, 12.4, 10.8, 11.3, 10.3, 11.8, 11.8, 11.8, 11.3, 11.3, -1e+100,
                              -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100, -1e+100,
                              -1e+100, -1e+100, -1e+100, -1e+100, -1e+100]
    }
    
    res = pdbufr.read_bufr(TEST_DATA_5, columns=columns,
                           observation_filters={'stormIdentifier': '70E',
                                                'ensembleMemberNumber': 4, 
                                                'meteorologicalAttributeSignificance': 3})

    for k in ref.keys():        
        assert(np.allclose(res[k].values, ref[k]))
