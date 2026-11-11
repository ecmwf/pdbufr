# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

import pdbufr.core.param as PARAMS
from pdbufr.core.accessor import (
    CoordAccessor,
    parse_period_key,
    resolve_period_key,
)
from pdbufr.core.structure import pair_key_name


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


class _FakeCollector:
    """Pretends to be a BufrSubsetCollector, yielding prepared records.

    The records are in the raw collected form: BUFR key name -> (value, units).
    """

    def __init__(self, records):
        self.records = records
        self.pair_keys = None

    def collect(self, keys, filters, mandatory_keys=None, units_keys=None, value_and_units=True, pair_keys=None):
        self.pair_keys = pair_keys
        yield from self.records


def _make_t2m_accessor():
    return CoordAccessor(
        keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
        coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        period="timePeriod",
        first=False,
    )


def _record(start, end=..., value=291.49, height=1.25):
    record = {
        "timePeriod": (start, "h"),
        "maximumTemperatureAtHeightAndOverPeriodSpecified": (value, None),
        "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": (height, "m"),
    }
    if end is not ...:
        record[pair_key_name("timePeriod")] = (end, "h")
    return record


def test_coord_accessor_declares_the_pair_key() -> None:
    ac = _make_t2m_accessor()

    assert pair_key_name("timePeriod") in ac.keys
    # the paired key is optional: it must not become mandatory and it is not a
    # BUFR key to include in the filtered key list
    assert pair_key_name("timePeriod") not in ac.mandatory
    assert pair_key_name("timePeriod") not in ac.bufr_keys
    assert ac.dynamic_period

    collector = _FakeCollector([_record(-12, 0)])
    ac.collect(collector)
    assert collector.pair_keys == ["timePeriod"]


def test_coord_accessor_single_period() -> None:
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(-12)]), add_coord=True)

    assert resolve_period_key("max_t2m_<12h>") == "max_t2m_12h"
    assert res == {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": 1.25}


def test_coord_accessor_pair_ending_at_observation_time() -> None:
    # D1: (-12, 0) is a 12h period ending at the observation time -> "12h"
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(-12, 0)]), add_coord=True)

    assert res == {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": 1.25}
    assert "max_t2m_<0h>" not in res


def test_coord_accessor_pair_ending_before_observation_time() -> None:
    # D1: (-30, -6) is a 24h period ending 6h before T -> "24h_lag6h"
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(-30, -6)]), add_coord=True)

    assert res == {"max_t2m_<24h_lag6h>": 291.49, "max_t2m_<24h_lag6h>_level": 1.25}
    assert resolve_period_key("max_t2m_<24h_lag6h>_level") == "max_t2m_24h_lag6h_level"
    assert "max_t2m_<6h>" not in res


def test_coord_accessor_positive_period_is_named_by_absolute_value() -> None:
    # A2: no "-" in period-derived names
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(12)]), add_coord=True)
    assert res == {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": 1.25}

    res = ac.collect(_FakeCollector([_record(30, 6)]), add_coord=True)
    assert res == {"max_t2m_<24h_lag6h>": 291.49, "max_t2m_<24h_lag6h>_level": 1.25}


def test_coord_accessor_missing_period_with_present_value_uses_plain_name() -> None:
    # D3: a value without a period gets the plain name (with plain _level)
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(None)]), add_coord=True)

    assert res == {"max_t2m": 291.49, "max_t2m_level": 1.25}


def test_coord_accessor_missing_period_and_value_emits_no_column() -> None:
    # D3: value and period all missing -> no column at all
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(None, value=None)]), add_coord=True)

    assert res == {}


def test_coord_accessor_missing_pair_and_value_emits_no_column() -> None:
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(None, None, value=None)]), add_coord=True)

    assert res == {}


def test_coord_accessor_pair_with_missing_start_uses_plain_name() -> None:
    # D3 (T6): a (MISSING, 0) pair is a missing period, never named "_0h";
    # the present value gets the plain name
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(None, 0)]), add_coord=True)

    assert res == {"max_t2m": 291.49, "max_t2m_level": 1.25}
    assert "max_t2m_<0h>" not in res


def test_coord_accessor_pair_with_missing_start_and_value_emits_no_column() -> None:
    # D3 (T6): (MISSING, 0) pair and MISSING value -> no column, no _level
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(None, 0, value=None)]), add_coord=True)

    assert res == {}


def test_coord_accessor_pair_with_missing_end_uses_plain_name() -> None:
    # D3 (T6): a (-1537, MISSING) pair is a missing period; the known half
    # must not name the column
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(-1537, None)]), add_coord=True)

    assert res == {"max_t2m": 291.49, "max_t2m_level": 1.25}
    assert "max_t2m_<1537h>" not in res


def test_coord_accessor_pair_with_missing_end_and_value_emits_no_column() -> None:
    # D3 (T6): (-1537, MISSING) pair and MISSING value -> no column
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(-1537, None, value=None)]), add_coord=True)

    assert res == {}


def test_coord_accessor_never_emits_nan() -> None:
    ac = _make_t2m_accessor()

    records = [_record(None), _record(None, None, value=None), _record(-12, 0)]
    res = ac.collect(_FakeCollector(records), add_coord=True, add_units=True)

    assert [k for k in res if "nan" in k] == []
    assert [k for k in res if "-" in resolve_period_key(k)] == []


def test_coord_accessor_value_missing_period_present_keeps_suffixed_column() -> None:
    # only a MISSING period suppresses columns; a None value with a known period
    # still yields the suffixed column (handled with the collision rules in T3)
    ac = _make_t2m_accessor()

    res = ac.collect(_FakeCollector([_record(-12, 0, value=None)]), add_coord=True)

    assert res == {"max_t2m_<12h>": None, "max_t2m_<12h>_level": 1.25}


def test_coord_accessor_fixed_period_unaffected_by_d3() -> None:
    ac = CoordAccessor(
        keys={"maximumTemperatureAt2MPast12Hours": PARAMS.MAX_T2M},
        fixed_period="12h",
        fixed_coords=2,
    )
    record = {"maximumTemperatureAt2MPast12Hours": (None, None)}

    res = ac.collect(_FakeCollector([record]), add_coord=True)

    assert not ac.dynamic_period
    assert res == {"max_t2m_<12h>": None, "max_t2m_<12h>_level": 2}


def test_coord_accessor_without_period_unaffected_by_d3() -> None:
    ac = CoordAccessor(
        keys={"airTemperature": PARAMS.T2M},
        coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
    )
    record = {
        "airTemperature": (None, None),
        "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform": (2.0, "m"),
    }

    res = ac.collect(_FakeCollector([record]), add_coord=True)

    assert res == {"t2m": None, "t2m_level": 2.0}


def test_coord_accessor_units_follow_the_period_name() -> None:
    ac = CoordAccessor(
        keys={"totalSunshine": PARAMS.TOTAL_SUNSHINE},
        period="timePeriod",
        first=False,
    )
    record = {"timePeriod": (-30, "min"), pair_key_name("timePeriod"): (-6, "min"), "totalSunshine": (60.0, "min")}

    res = ac.collect(_FakeCollector([record]), add_units=True)

    assert res == {"total_sunshine_<24min_lag6min>": 60.0, "total_sunshine_<24min_lag6min>_units": "min"}


def test_coord_accessor_no_records_emits_no_columns() -> None:
    # the relabel phantom fix: collect_any(first=True, raise_on_missing=False)
    # returns {} when the message has no such key; relabel must then not fabricate
    # a _level column for the fixed coord out of the empty record
    ac = CoordAccessor(
        keys={"maximumTemperatureAt2MPast12Hours": PARAMS.MAX_T2M},
        fixed_period="12h",
        fixed_coords=2,
    )

    res = ac.collect(_FakeCollector([]), add_coord=True, add_units=True)

    assert res == {}


def test_coord_accessor_default_collision_stays_last_wins() -> None:
    # A4: without the opt-in selection flags the merge keeps the old behaviour:
    # the last record wins, also when it is missing and overwrites a real value
    ac = _make_t2m_accessor()

    records = [_record(-12, value=291.49, height=2.0), _record(-12, value=290.05, height=0.05)]
    res = ac.collect(_FakeCollector(records), add_coord=True)
    assert res == {"max_t2m_<12h>": 290.05, "max_t2m_<12h>_level": 0.05}

    records = [_record(-12, value=291.49, height=2.0), _record(-12, value=None, height=0.05)]
    res = ac.collect(_FakeCollector(records), add_coord=True)
    assert res == {"max_t2m_<12h>": None, "max_t2m_<12h>_level": 0.05}


def test_coord_accessor_missing_last_ranks_values_only() -> None:
    # missing_last without a nominal height: a real value wins a collision and
    # keeps its level/units, equal (both real or both missing) ranks stay
    # last-writer-wins
    ac = CoordAccessor(
        keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
        coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        period="timePeriod",
        first=False,
        missing_last=True,
    )

    records = [_record(-12, value=291.49, height=0.05), _record(-12, value=None, height=2.0)]
    res = ac.collect(_FakeCollector(records), add_coord=True)
    assert res == {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": 0.05}

    records = [_record(-12, value=291.49, height=2.0), _record(-12, value=290.05, height=0.05)]
    res = ac.collect(_FakeCollector(records), add_coord=True)
    assert res == {"max_t2m_<12h>": 290.05, "max_t2m_<12h>_level": 0.05}


def test_coord_accessor_nominal_height_works_without_level_columns() -> None:
    # D2 selection also applies when the _level columns are not requested
    ac = CoordAccessor(
        keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
        coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        period="timePeriod",
        first=False,
        nominal_height=2.0,
        min_height=0.5,
        missing_last=True,
    )

    records = [_record(-12, value=275.45, height=2.0), _record(-12, value=274.95, height=0.05)]
    res = ac.collect(_FakeCollector(records), add_coord=False)

    assert res == {"max_t2m_<12h>": 275.45}


def test_coord_accessor_drops_ground_height_candidate() -> None:
    # reviewer blocker 1 (D2): a candidate with a sensor height below min_height
    # is dropped before ranking: as the sole candidate of its period it is
    # reported like a missing value, without its value and without its level
    ac = CoordAccessor(
        keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
        coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", True)],
        period="timePeriod",
        first=False,
        nominal_height=2.0,
        min_height=0.5,
        missing_last=True,
    )

    res = ac.collect(_FakeCollector([_record(-12, value=272.55, height=0.1)]), add_coord=True)
    assert res == {"max_t2m_<12h>": None, "max_t2m_<12h>_level": None}

    # the dropped candidate can also not keep the level away from a missing
    # value at an eligible height
    records = [_record(-12, value=272.55, height=0.1), _record(-12, value=None, height=2.0)]
    res = ac.collect(_FakeCollector(records), add_coord=True)
    assert res == {"max_t2m_<12h>": None, "max_t2m_<12h>_level": 2.0}


def test_coord_accessor_without_height_descriptor_ranks_after_valid_height() -> None:
    # reviewer blocker 3 (D2): with the coord key optional (mandatory=False) a
    # record without any height occurrence is collected, accepted as a
    # candidate and ranked after values with an eligible height
    ac = CoordAccessor(
        keys={"maximumTemperatureAtHeightAndOverPeriodSpecified": PARAMS.MAX_T2M},
        coords=[("heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", "level", False)],
        period="timePeriod",
        first=False,
        nominal_height=2.0,
        min_height=0.5,
        missing_last=True,
    )
    no_height = {
        "timePeriod": (-12, "h"),
        "maximumTemperatureAtHeightAndOverPeriodSpecified": (291.49, None),
    }

    res = ac.collect(_FakeCollector([no_height]), add_coord=True)
    assert res == {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": None}

    records = [no_height, _record(-12, value=275.45, height=2.5)]
    res = ac.collect(_FakeCollector(records), add_coord=True)
    assert res == {"max_t2m_<12h>": 275.45, "max_t2m_<12h>_level": 2.5}
    res = ac.collect(_FakeCollector(records[::-1]), add_coord=True)
    assert res == {"max_t2m_<12h>": 275.45, "max_t2m_<12h>_level": 2.5}

    # a real value without a height still beats a missing one with a height (A3)
    records = [no_height, _record(-12, value=None, height=2.0)]
    res = ac.collect(_FakeCollector(records), add_coord=True)
    assert res == {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": None}
