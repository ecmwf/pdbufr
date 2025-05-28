# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import numpy as np
import pytest

from pdbufr.utils.units import UnitsConverter


@pytest.mark.parametrize(
    "data,expected_value",
    [
        ((3.6, "km h-1"), (1.0, "m / s")),
        ((3.6, "m s-1"), (3.6, "m / s")),
        ((100, "C"), (373.15, "K")),
        ((100.0, "K"), (100.0, "K")),
        ((1002.32, "hPa"), (100232.0, "kg / m / s ** 2")),
        ((100232, "Pa"), (100232, "kg / m / s ** 2")),
    ],
)
def test_units_si(data, expected_value):
    converter = UnitsConverter.make("si")

    v, u = converter.convert("", data[0], data[1])
    assert np.isclose(v, expected_value[0])
    assert u == expected_value[1]


@pytest.mark.parametrize(
    "data,expected_value",
    [
        (("t2m", 100, "C"), (100, "C")),
        (("t2m", 373, "K"), (99.85000000000002, "C")),
        (("td2m", 100, "C"), (373.15, "K")),
        (("td2m", 373, "K"), (373, "K")),
        (("rh2m", 100, "%"), (100, "%")),
        (("q2m", 0.001, "kg kg-1"), (0.001, "kg/kg")),
        (("q2m", 1, "g kg-1"), (0.001, "kg/kg")),
        (("mslp", 100232, "Pa"), (1002.32, "hPa")),
        (("mslp", 1002.32, "hPa"), (1002.32, "hPa")),
        (("wind10m_speed", 3.6, "km/h"), (3.6, "km/h")),
        (("wind10m_speed", 3.6, "km h-1"), (3.6, "km/h")),
        (("wind10m_speed", 1, "m s-1"), (3.6, "km/h")),
        (("wind10m_speed", 1, "m/s"), (3.6, "km/h")),
        (("wind10m_dir", 100, "deg"), (100, "deg")),
        (("visibility", 100, "m"), (100, "m")),
        (("visibility", 100, "km"), (100000, "m")),
        (("cloud_cover", 80, "%"), (80, "%")),
        (("max_t2m", 100, "C"), (373.15, "K")),
        (("max_t2m", 373, "K"), (373, "K")),
        (("min_t2m", 100, "C"), (373.15, "K")),
        (("min_t2m", 373, "K"), (373, "K")),
        (("precipitation", 100, "kg m-2"), (100, "kg m-2")),
        (("snow_depth", 100, "m"), (100, "m")),
        (("snow_depth", 100, "cm"), (1.0, "m")),
        (("snow_depth", 100, "mm"), (0.1, "m")),
        (("pres", 100232, "Pa"), (100232, "Pa")),
    ],
)
def test_units_user_with_default(data, expected_value):
    rule = {
        "wind10m_speed": "km/h",
        "t2m": "C",
        "mslp": "hPa",
    }

    converter = UnitsConverter.make("pdbufr", units=rule)

    v, u = converter.convert(*data)
    assert np.isclose(v, expected_value[0])
    assert u == expected_value[1]


@pytest.mark.parametrize(
    "data,expected_value",
    [
        (("t2m", 100, "C"), (100, "C")),
        (("t2m", 373, "K"), (99.85000000000002, "C")),
        (("td2m", 100, "C"), (373.15, "K")),
        (("td2m", 373, "K"), (373, "K")),
        # (("rh2m", 100, "%"), (100, "%")),
        (("q2m", 0.001, "kg kg-1"), (0.001, "")),
        (("q2m", 1, "g kg-1"), (0.001, "")),
        (("mslp", 100232, "Pa"), (1002.32, "hPa")),
        (("mslp", 1002.32, "hPa"), (1002.32, "hPa")),
        (("wind10m_speed", 3.6, "km/h"), (3.6, "km/h")),
        (("wind10m_speed", 3.6, "km h-1"), (3.6, "km/h")),
        (("wind10m_speed", 1, "m s-1"), (3.6, "km/h")),
        (("wind10m_speed", 1, "m/s"), (3.6, "km/h")),
        (("wind10m_dir", 100, "deg"), (1.7453292519943295, "rad")),
        (("visibility", 100, "m"), (100, "m")),
        (("visibility", 100, "km"), (100000, "m")),
        # (("cloud_cover", 80, "%"), (80, "%")),
        (("max_t2m", 100, "C"), (373.15, "K")),
        (("max_t2m", 373, "K"), (373, "K")),
        (("min_t2m", 100, "C"), (373.15, "K")),
        (("min_t2m", 373, "K"), (373, "K")),
        (("precipitation", 100, "kg m-2"), (100, "kg / m ** 2")),
        (("snow_depth", 100, "m"), (100, "m")),
        (("snow_depth", 100, "cm"), (1.0, "m")),
        (("snow_depth", 100, "mm"), (0.1, "m")),
        (("pres", 100232, "Pa"), (100232, "kg / m / s ** 2")),
    ],
)
def test_units_user_with_si(data, expected_value):
    rule = {
        "wind10m_speed": "km/h",
        "t2m": "C",
        "mslp": "hPa",
    }

    converter = UnitsConverter.make("si", units=rule)

    v, u = converter.convert(*data)
    assert np.isclose(v, expected_value[0])
    assert u == expected_value[1]


@pytest.mark.parametrize(
    "data,expected_value",
    [
        (("t2m", 100, "C"), (373.15, "K")),
        (("t2m", 373, "K"), (373, "K")),
        (("td2m", 100, "C"), (373.15, "K")),
        (("td2m", 373, "K"), (373, "K")),
        (("rh2m", 100, "%"), (100, "%")),
        (("q2m", 0.001, "kg/kg"), (0.001, "kg/kg")),
        (("q2m", 1, "g/kg"), (0.001, "kg/kg")),
        (("mslp", 100232, "Pa"), (100232, "Pa")),
        (("mslp", 1002.32, "hPa"), (100232, "Pa")),
        (("wind10m_speed", 3.6, "m/s"), (3.6, "m/s")),
        (("wind10m_speed", 3.6, "km h-1"), (1.0, "m/s")),
        (("wind10m_speed", 3.6, "km/h"), (1.0, "m/s")),
        (("wind10m_dir", 100, "deg"), (100, "deg")),
        (("visibility", 100, "m"), (100, "m")),
        (("visibility", 100, "km"), (100000, "m")),
        (("cloud_cover", 80, "%"), (80, "%")),
        (("max_t2m", 100, "C"), (373.15, "K")),
        (("max_t2m", 373, "K"), (373, "K")),
        (("min_t2m", 100, "C"), (373.15, "K")),
        (("min_t2m", 373, "K"), (373, "K")),
        (("precipitation", 100, "kg m-2"), (100, "kg m-2")),
        (("snow_depth", 100, "m"), (100, "m")),
        (("snow_depth", 100, "cm"), (1.0, "m")),
        (("snow_depth", 100, "mm"), (0.1, "m")),
        (("pres", 100232, "Pa"), (100232, "Pa")),
    ],
)
def test_units_default(data, expected_value):
    converter = UnitsConverter.make("pdbufr")

    v, u = converter.convert(*data)
    assert np.isclose(v, expected_value[0])
    assert u == expected_value[1]
