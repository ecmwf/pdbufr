# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

from pdbufr.core.param import PeriodParameter

PERIOD = PeriodParameter("_period")


def test_parse_keeps_raw_displacement() -> None:
    assert PERIOD.parse(-12, "h") == (-12, "h")
    assert PERIOD.parse(0, "h") == (0, "h")
    assert PERIOD.parse(-30, None) == (-30, "")
    # an absent displacement is None, a present-but-MISSING one keeps its slot
    # as (None, units) so that a pair with a missing element is detectable
    assert PERIOD.parse(None, "h", present=False) is None
    assert PERIOD.parse(None, "h") == (None, "h")
    assert PERIOD.parse(None, None) == (None, "")


@pytest.mark.parametrize(
    "value, units, expected",
    [
        (-12, "h", "12h"),
        (12, "h", "12h"),  # A2: a positive displacement is named by its absolute size
        (-60, "min", "60min"),
        (0, "h", "0h"),
        (-12.0, "h", "12h"),  # whole floats lose the trailing ".0"
        (None, "h", None),
    ],
)
def test_concat_units(value, units, expected) -> None:
    assert PERIOD.concat_units(value, units) == expected


@pytest.mark.parametrize(
    "start, end, expected",
    [
        # a single displacement names the period ending at the observation time
        ((-12, "h"), None, "12h"),
        ((12, "h"), None, "12h"),
        ((-60, "min"), None, "60min"),
        # a single MISSING displacement (no pair) is a missing period (D3)
        ((None, "h"), None, None),
        # a consecutive (start, end) pair is named by its duration (D1, A2)
        ((-12, "h"), (0, "h"), "12h"),
        ((30, "h"), (6, "h"), "24h_lag6h"),
        ((-30, "h"), (-6, "h"), "24h_lag6h"),
        # a complete pair with equal value and units repeats a single
        # displacement: the second element is dropped and the period is named
        # by that displacement
        ((-24, "h"), (-24, "h"), "24h"),
        ((-6, "h"), (-6, "h"), "6h"),
        ((-30, "min"), (-30, "min"), "30min"),
        ((0, "h"), (0, "h"), "0h"),
        ((-30, "min"), (-6, "min"), "24min_lag6min"),
        # no "-" may appear in a name
        ((-12, "h"), (0, "h"), "12h"),
        # a pair with a MISSING element is a missing period (D3): the known
        # half never names the column
        ((None, "h"), (0, "h"), None),
        ((None, "h"), (-6, "h"), None),
        ((-1537, "h"), (None, "h"), None),
        ((None, "h"), (None, "h"), None),
        # an absent start slot with a present end slot is also an incomplete
        # pair, never named by the known element
        (None, (-6, "h"), None),
        # no displacement at all -> None: the caller must use the plain name
        (None, None, None),
        # a mixed-unit pair is nonsense: fall back to naming by the start value
        ((-12, "h"), (0, "min"), "12h"),
        # equal values in mixed units are NOT a repeated displacement: the
        # mixed-unit fallback names by the start displacement
        ((-24, "h"), (-24, "min"), "24h"),
    ],
)
def test_format(start, end, expected) -> None:
    assert PERIOD.format(start, end) == expected


def test_format_never_returns_nan() -> None:
    slots = (None, (None, "h"), (-12, "h"), (0, "h"))
    for start in slots:
        for end in slots:
            period = PERIOD.format(start, end)
            assert period != "nan"
            assert "nan" not in str(period)
            assert period is None or "-" not in period
