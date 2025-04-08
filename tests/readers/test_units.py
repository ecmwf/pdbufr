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
        (("wspeed", 3.6, "km h-1"), (3.6, "km h-1")),
        (("wspeed", 1, "m s-1"), (3.6, "km/h")),
        (("t2m", 100, "C"), (100, "C")),
        (("t2m", 373, "K"), (99.85000000000002, "C")),
        (("mslp", 100232, "Pa"), (1002.32, "hPa")),
        (("pres", 100232, "Pa"), (100232, "kg / m / s ** 2")),
    ],
)
def test_units_user(data, expected_value):
    rule = {
        "wspeed": "km/h",
        "t2m": "C",
        "mslp": "hPa",
    }

    converter = UnitsConverter.make(rule)

    v, u = converter.convert(*data)
    assert np.isclose(v, expected_value[0])
    assert u == expected_value[1]
