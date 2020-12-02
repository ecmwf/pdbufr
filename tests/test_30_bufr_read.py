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

import eccodes  # type: ignore
import numpy as np  # type: ignore

from pdbufr import bufr_read


def test_datetime_from_bufr():
    obs = {"Y": 2020, "M": 3, "D": 18}

    res = bufr_read.datetime_from_bufr(obs, "", ["Y", "M", "D", "h", "m", "s"])

    assert str(res) == "2020-03-18 00:00:00"


def test_wmo_station_id_from_bufr():
    res = bufr_read.wmo_station_id_from_bufr({"b": "01", "s": "20"}, "", ["b", "s"])

    assert res == 1020


def test_filter_message_items():
    msg = {
        "edition": "1",
        "#1#year": 1,
        "#1#month": 2,
        "#1#day": 3,
        "#1#temperature": eccodes.CODES_MISSING_DOUBLE,
    }
    message_keys = list(msg)
    expected_all = [
        ("edition", "edition", "1"),
        ("#1#year", "year", 1),
        ("#1#month", "month", 2),
        ("#1#day", "day", 3),
        # ("#1#temperature", "temperature", np.nan),
    ]

    res = list(bufr_read.filter_message_items(msg, None, message_keys))

    assert np.isnan(res.pop()[2])
    assert res == expected_all

    include = ["edition", "year", "temperature"]
    expected_include = [
        ("edition", "edition", "1"),
        ("#1#year", "year", 1),
        # ("#1#temperature", "temperature", np.nan),
    ]

    res = list(bufr_read.filter_message_items(msg, include, message_keys))

    assert np.isnan(res.pop()[2])
    assert res == expected_include


def test_extract_subsets():
    message = [
        ("count", "count", 1),
        ('#1#year', 'year', 2020),
        ("#1#lat", "lat", [43.0, eccodes.CODES_MISSING_DOUBLE]),
    ]

    assert list(bufr_read.extract_subsets(message, 1, False)) == [message]

    expected = [
        [("count", "count", 1), ('#1#year', 'year', 2020), ("#1#lat", "lat", 43.0)],
        [("count", "count", 1), ('#1#year', 'year', 2020), ("#1#lat", "lat", np.nan)],
    ]

    res = bufr_read.extract_subsets(message, 2, is_compressed=True)

    assert np.array_equal(list(res), expected)

    message = [
        ("count", "count", 1),
        ('#1#year', 'year', 2020),
        ("subsetNumber", "subsetNumber", [1, 2]),
        ("#1#lat", "lat", 43.0),
        ("subsetNumber", "subsetNumber", [1, 2]),
        ("#2#lat", "lat", np.nan),
    ]
    expected = [
        [("count", "count", 1), ('#1#year', 'year', 2020), ("#1#lat", "lat", 43.0)],
        [("count", "count", 1), ('#1#year', 'year', 2020), ("#2#lat", "lat", np.nan)],
    ]

    res = bufr_read.extract_subsets(message, 2, is_compressed=False)

    assert np.array_equal(list(res), expected)
