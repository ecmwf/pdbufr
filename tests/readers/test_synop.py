# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import pdbufr

p = "/Users/cgr/metview/BUFR/surf_land/synop_0_193_M14.bufr"

# ref = {
#     "sid": {0: 91554},
#     "lat": {0: -15.517000000000001},
#     "lon": {0: 167.217},
#     "elevation": {0: 41.0},
#     "time": {0: Timestamp("2024-11-20 09:00:00")},
#     "t2m": {0: 300.35},
#     "rh2m": {0: None},
#     "td2m": {0: 297.15000000000003},
#     "wspeed10m": {0: 5.1000000000000005},
#     "wdir10m": {0: 130},
#     "wspeedgust_nan": {0: None},
#     "wdirgust_nan": {0: None},
#     "present_weather": {0: 2},
#     "past_weather_1_6h": {0: 2},
#     "past_weather_2_6h": {0: 2},
#     "precipitation_nan": {0: None},
#     "min_t2m_0h": {0: None},
#     "max_t2m_0h": {0: None},
#     "mslp": {0: 101230.0},
#     "cloud_cover": {0: 62},
#     "snow_depth": {0: None},
#     "visibility": {0: 20000.0},
# }

# ref = {
#     "sid": 91554,
#     "lat": -15.517000000000001,
#     "lon": 167.217,
#     "elevation": 41.0,
#     "time": datetime.datetime(2024, 11, 20, 9, 0),
#     "t2m": 300.35,
#     "rh2m": None,
#     "td2m": 297.15000000000003,
#     "wspeed10m": 5.1000000000000005,
#     "wdir10m": 130,
#     "wspeedgust_nan": None,
#     "wdirgust_nan": None,
#     "present_weather": 2,
#     "past_weather_1_6h": 2,
#     "past_weather_2_6h": 2,
#     "precipitation_nan": None,
#     "min_t2m_0h": None,
#     "max_t2m_0h": None,
#     "mslp": 101230.0,
#     "cloud_cover": 62,
#     "snow_depth": None,
#     "visibility": 20000.0,
# }
# ref = {
#     "sid": {"0": 91554},
#     "lat": {"0": -15.517},
#     "lon": {"0": 167.217},
#     "elevation": {"0": 41.0},
#     "time": {"0": "2024-11-20T09:00:00.000"},
#     "t2m": {"0": 300.35},
#     "rh2m": {"0": null},
#     "td2m": {"0": 297.15},
#     "wspeed10m": {"0": 5.1},
#     "wdir10m": {"0": 130},
#     "wspeedgust_nan": {"0": null},
#     "wdirgust_nan": {"0": null},
#     "present_weather": {"0": 2},
#     "past_weather_1_6h": {"0": 2},
#     "past_weather_2_6h": {"0": 2},
#     "precipitation_nan": {"0": null},
#     "min_t2m_0h": {"0": null},
#     "max_t2m_0h": {"0": null},
#     "mslp": {"0": 101230.0},
#     "cloud_cover": {"0": 62},
#     "snow_depth": {"0": null},
#     "visibility": {"0": 20000.0},
# }

ref = {
    "sid": {"0": 91554},
    "lat": {"0": -15.517},
    "lon": {"0": 167.217},
    "elevation": {"0": 41.0},
    "time": {"0": "2024-11-20T09:00:00.000"},
    "t2m": {"0": 300.35},
    "rh2m": {"0": None},
    "td2m": {"0": 297.15},
    "wspeed10m": {"0": 5.1},
    "wdir10m": {"0": 130},
    "wspeedgust_nan": {"0": None},
    "wdirgust_nan": {"0": None},
    "present_weather": {"0": 2},
    "past_weather_1_6h": {"0": 2},
    "past_weather_2_6h": {"0": 2},
    "precipitation_nan": {"0": None},
    "min_t2m_0h": {"0": None},
    "max_t2m_0h": {"0": None},
    "mslp": {"0": 101230.0},
    "cloud_cover": {"0": 62},
    "snow_depth": {"0": None},
    "visibility": {"0": 20000.0},
}


def test_synop_r():
    df = pdbufr.read_bufr(p, reader="synop")

    r = df.to_dict()
    print("r=", r)
    print("r=", type(r["time"][0]))

    assert False

    # r = df.to_json(date_format="iso")
    # parsed = loads(r)

    # print("df=", df)

    # d = pd.DataFrame.from_dict(ref)
    # d.reset_index(drop=True, inplace=True)
    # print("d=", d)

    # try:
    #     assert_frame_equal(df, d, check_index_type=False, check_datetimelike_compat=True)
    # except Exception as e:
    #     print("e=", e)
    #     raise
