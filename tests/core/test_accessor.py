# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

from pdbufr.core.accessor import parse_period_key
from pdbufr.core.accessor import resolve_period_key


@pytest.mark.parametrize(
    "key,excepted_value",
    [
        ("t2m", "t2m"),
        ("t2m_level", "t2m_level"),
        ("wind10m_speed_level", "wind10m_speed_level"),
        ("max_wgust_speed_<21min>", "max_wgust_speed_21min"),
        ("max_wgust_speed_<21min>_level", "max_wgust_speed_21min_level"),
        ("precip_<2h>", "precip_2h"),
        ("max_wgust_speed_21min", "max_wgust_speed_21min"),
        ("max_wgust_speed_21min_level", "max_wgust_speed_21min_level"),
        ("precip_2h", "precip_2h"),
    ],
)
def test_resolve_period_key(key, excepted_value):
    assert resolve_period_key(key) == excepted_value


@pytest.mark.parametrize(
    "key,excepted_value",
    [
        ("t2m", (None, None)),
        ("t2m_level", (None, None)),
        ("wind10m_speed_level", (None, None)),
        ("max_wgust_speed_<21min>", ("max_wgust_speed_<21min>", "max_wgust_speed")),
        ("max_wgust_speed_<21min>_level", ("max_wgust_speed_<21min>_level", "max_wgust_speed_level")),
        ("precip_<2h>", ("precip_<2h>", "precip")),
        ("max_wgust_speed_21min", (None, None)),
        ("max_wgust_speed_21min_level", (None, None)),
        ("precip_2h", (None, None)),
    ],
)
def test_parse_period_key(key, excepted_value):
    assert parse_period_key(key) == excepted_value
