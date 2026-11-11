# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""Tests describing the correct period/height behaviour of the synop reader.

The expectations follow the WMO-306 Vol I.2 rules and the agreed target
behaviour:

- D1: a ``timePeriod`` pair ``(start, end)`` counted back from the observation
  time names the column by its duration; ``-12/0`` -> ``max_t2m_12h``,
  ``-30/-6`` -> ``max_t2m_24h_lag6h`` (level column ``max_t2m_24h_lag6h_level``).
  A complete pair of two EQUAL ``timePeriod`` values (same number and units)
  repeats a single displacement: the second element is dropped, so
  ``-24/-24`` -> ``max_t2m_24h`` (never ``0h_lag24h``).
- D2: for min/max 2 m temperature the value of the sensor height closest to
  2 m is used, sensors below 0.5 m are ignored.
- D3: no column name ever ends in ``_nan``.  When both the value and its
  period are missing no period-suffixed extreme column may appear (the
  plain requested column ``max_t2m``/``min_t2m`` filled with None/NaN is
  acceptable as the generic "requested but not found" result); when the
  value is present but the period is missing the plain name is used.
  A start/end ``timePeriod`` pair with a MISSING element counts as a
  missing period: the known half never names the column (T6).
- A2: a positive period is read by its absolute value (no ``-`` in names).
- ``_level`` columns never appear without their value column.

Two synthetic fixtures complement the real sample files, and a third one is
derived from a real Sri Lankan SYNOP.  They were created
with the following eccodes script (run from the repository root, note the
required ``pack`` step before re-encoding)::

    import eccodes

    def edit(src, dst, sets):
        with open(src, "rb") as f:
            mid = eccodes.codes_bufr_new_from_file(f)
        eccodes.codes_set(mid, "unpack", 1)
        for k, v in sets:
            eccodes.codes_set(mid, k, v)
        eccodes.codes_set(mid, "pack", 1)
        with open(dst, "wb") as f:
            f.write(eccodes.codes_get_message(mid))
        eccodes.codes_release(mid)

    # tests/sample_data/synop_period_end_offset.bufr:
    # both extreme-temperature timePeriod pairs -12/0 -> -30/-6
    edit(
        "tests/sample_data/synop_0_74_M32.bufr",
        "tests/sample_data/synop_period_end_offset.bufr",
        [
            ("#6#timePeriod", -30),
            ("#7#timePeriod", -6),
            ("#8#timePeriod", -30),
            ("#9#timePeriod", -6),
        ],
    )

    # tests/sample_data/synop_period_heights.bufr:
    # the two sensor heights in front of the minimum-temperature occurrences
    # (2.0 m before max #1 = 275.75 / min #1 = 275.45, 0.05 m before
    # min #2 = 274.95) swapped to 1.8 m and 2.6 m, so the FIRST block
    # (275.45 at 1.8 m, closest to 2 m) must win while the buggy
    # last-wins code still returns 274.95
    edit(
        "tests/sample_data/synop_172_98_M29.bufr",
        "tests/sample_data/synop_period_heights.bufr",
        [
            ("#5#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", 1.8),
            ("#6#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", 2.6),
        ],
    )

    # tests/sample_data/synop_period_equal_pair.bufr: the real Sri Lankan
    # SYNOP msg_13738.bufr (ident 43421 ANURADHAPURA, template 307086), whose
    # extreme temperatures are MISSING and whose four 24 h timePeriods form
    # two EQUAL (-24/-24) pairs; the two extreme temperatures were set to
    # 305.15 / 295.15 K and the sensor height #6 (the one in front of the
    # maximum block, kept by both temperature records) to 2 m
    edit(
        "msg_13738.bufr",
        "tests/sample_data/synop_period_equal_pair.bufr",
        [
            ("#6#heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform", 2.0),
            ("#1#maximumTemperatureAtHeightAndOverPeriodSpecified", 305.15),
            ("#1#minimumTemperatureAtHeightAndOverPeriodSpecified", 295.15),
        ],
    )
"""

import pytest

import pdbufr
from pdbufr.core.accessor import merge_period_results
from pdbufr.readers.synop import MANAGER_CACHE, MaxTAccessor, MinTAccessor, WindGustSpeedAccessor
from pdbufr.utils.testing import sample_test_data_path

ALL_COLUMNS = sorted(MANAGER_CACHE.get().accessors)

# every new sample file, used by the invariant tests
PERIOD_FILES = [
    "synop_0_74_M32.bufr",
    "synop_176_98_M29.bufr",
    "synop_172_98_M29.bufr",
    "synop_150_85_M22.bufr",
    "synop_0_212_M14.bufr",
    "synop_0_231_M15.bufr",
    "synop_0_236_M16.bufr",
    "buoy_12_98_M13.bufr",
    "synop_period_end_offset.bufr",
    "synop_period_heights.bufr",
    "synop_period_equal_pair.bufr",
    "synop_4_98_M13.bufr",
    "synop_min_t2m_12h.bufr",
]

LEVEL_COLUMNS = [True, False]


class _RecordCollector:
    """Stand-in for BufrSubsetCollector yielding prepared records.

    The records are in the raw collected form: BUFR key name -> (value, units).
    Only records containing all the mandatory keys are yielded, like the real
    collector does.
    """

    def __init__(self, records):
        self.records = records

    def collect(self, keys, filters, mandatory_keys=None, units_keys=None, value_and_units=True, pair_keys=None):
        for record in self.records:
            if mandatory_keys and not all(k in record for k in mandatory_keys):
                continue
            yield record


def read_period_file(name: str, level_columns: bool):
    return pdbufr.read_bufr(
        sample_test_data_path(name),
        reader="synop",
        columns=ALL_COLUMNS,
        level_columns=level_columns,
    )


# ---------------------------------------------------------------------------
# D1: period naming
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_double_timeperiod_pair_named_by_duration(level_columns):
    # synop_0_74_M32.bufr: timePeriod(-12), timePeriod(0) before
    # maximumTemperatureAtHeightAndOverPeriodSpecified=291.49 and before
    # minimumTemperatureAtHeightAndOverPeriodSpecified=289.89, both at
    # heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform=1.25 m
    df = read_period_file("synop_0_74_M32.bufr", level_columns)

    assert df["max_t2m_12h"][0] == pytest.approx(291.49)
    assert df["min_t2m_12h"][0] == pytest.approx(289.89)

    if level_columns:
        assert df["max_t2m_12h_level"][0] == pytest.approx(1.25)
        assert df["min_t2m_12h_level"][0] == pytest.approx(1.25)


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_period_ending_before_observation_has_end_offset_suffix(level_columns):
    # synop_period_end_offset.bufr: the -12/0 pairs of synop_0_74_M32.bufr
    # were replaced by -30/-6, i.e. a 24 h period ending 6 h before the
    # observation time, values 291.49 / 289.89 at 1.25 m
    df = read_period_file("synop_period_end_offset.bufr", level_columns)

    assert df["max_t2m_24h_lag6h"][0] == pytest.approx(291.49)
    assert df["min_t2m_24h_lag6h"][0] == pytest.approx(289.89)

    if level_columns:
        assert df["max_t2m_24h_lag6h_level"][0] == pytest.approx(1.25)
        assert df["min_t2m_24h_lag6h_level"][0] == pytest.approx(1.25)

    # the last element of the pair (offset -6) alone must not name the column
    assert "max_t2m_6h" not in df.columns
    assert "min_t2m_6h" not in df.columns


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_equal_timeperiod_pair_is_a_single_displacement(level_columns):
    # synop_period_equal_pair.bufr: the two extreme-temperature blocks each
    # encode their period as a pair of two consecutive EQUAL timePeriod
    # displacements (-24 h / -24 h, template 307086); such a pair repeats a
    # single displacement, so both columns are named by the 24 h duration
    # and never by the "0h_lag24h" the pair arithmetic would give
    df = pdbufr.read_bufr(
        sample_test_data_path("synop_period_equal_pair.bufr"),
        reader="synop",
        columns=["stnid", "max_t2m", "min_t2m"],
        level_columns=level_columns,
    )

    assert df["max_t2m_24h"][0] == pytest.approx(305.15)
    assert df["min_t2m_24h"][0] == pytest.approx(295.15)

    if level_columns:
        assert df["max_t2m_24h_level"][0] == pytest.approx(2.0)
        assert df["min_t2m_24h_level"][0] == pytest.approx(2.0)

    # the degenerate "0h_lag24h" naming must not appear
    assert [c for c in df.columns if "_lag" in c] == []


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
@pytest.mark.parametrize("name", ["synop_0_74_M32.bufr", "synop_176_98_M29.bufr"])
def test_no_0h_extreme_temperature_columns(name, level_columns):
    # both files encode the extreme-temperature periods as (-12, 0) pairs;
    # the trailing 0 must never become a "_0h" column
    df = read_period_file(name, level_columns)

    bad = [c for c in df.columns if c.startswith(("max_t2m_0h", "min_t2m_0h"))]
    assert bad == []


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_pair_with_missing_start_is_a_missing_period(level_columns):
    # synop_0_236_M16.bufr (template 3 07 096): the first extreme block is a
    # single timePeriod(-60 min) at 2 m with max=275.85 and min=274.85; the
    # second/third blocks each encode the timePeriod pair (MISSING, 0) before
    # a MISSING maximum/minimum temperature. D3/T6: a pair with a missing
    # element is a missing period, so the known 0 must never name a "_0h"
    # column (nor a _level/_units without its value column).
    df = read_period_file("synop_0_236_M16.bufr", level_columns)

    assert df["max_t2m_60min"][0] == pytest.approx(275.85)
    assert df["min_t2m_60min"][0] == pytest.approx(274.85)

    extremes = {c for c in df.columns if c.startswith(("max_t2m_", "min_t2m_"))}
    if level_columns:
        assert extremes == {
            "max_t2m_60min",
            "max_t2m_60min_level",
            "min_t2m_60min",
            "min_t2m_60min_level",
        }
        assert df["max_t2m_60min_level"][0] == pytest.approx(2.0)
        assert df["min_t2m_60min_level"][0] == pytest.approx(2.0)
    else:
        assert extremes == {"max_t2m_60min", "min_t2m_60min"}


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_pair_with_missing_end_is_a_missing_period(level_columns):
    # synop_0_231_M15.bufr is corrupt; one minimum block encodes the
    # timePeriod pair (-1537, MISSING) with a MISSING value: D3/T6 makes the
    # whole period missing, so no "1537" column (value or _level) may appear.
    # The complete pair (-1537, 2046) before the second maximum keeps its
    # duration naming (|start-end| = 3583 h ending 2046 h before the
    # observation time, A2 reads it by absolute size). That maximum 0.0 comes
    # from a sensor at 0.0 m, a ground sensor excluded by D2 (reviewer
    # blocker 1): the column stays but as for a missing value, without the
    # ground value and without the ground level.
    df = read_period_file("synop_0_231_M15.bufr", level_columns)

    assert [c for c in df.columns if "1537" in c] == []
    max_v = df["max_t2m_3583h_lag2046h"][0]
    assert max_v is None or max_v != max_v


# ---------------------------------------------------------------------------
# D2: sensor height selection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_two_heights_pick_the_2m_value(level_columns):
    # synop_172_98_M29.bufr (template 3 07 096): timePeriod(-60 min) with
    # height 2 m before max=275.75 and min=275.45, then a second min block
    # with timePeriod(-60 min) and height 0.05 m with min=274.95, plus a
    # third extreme block with everything missing
    df = read_period_file("synop_172_98_M29.bufr", level_columns)

    assert df["max_t2m_60min"][0] == pytest.approx(275.75)
    assert df["min_t2m_60min"][0] == pytest.approx(275.45)

    if level_columns:
        assert df["min_t2m_60min_level"][0] == pytest.approx(2.0)
        assert df["max_t2m_60min_level"][0] == pytest.approx(2.0)


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_two_heights_pick_closest_to_2m(level_columns):
    # synop_period_heights.bufr: same as synop_172_98_M29.bufr but the two
    # minimum-temperature sensor heights are swapped to 1.8 m (before max
    # 275.75 / min 275.45) and 2.6 m (before the second min 274.95).
    # The first block is closest to 2 m and must win; the buggy last-wins
    # code instead reports the second block's 274.95 at 2.6 m
    df = read_period_file("synop_period_heights.bufr", level_columns)

    assert df["min_t2m_60min"][0] == pytest.approx(275.45)

    if level_columns:
        assert df["min_t2m_60min_level"][0] == pytest.approx(1.8)
        # the maximum only has one non-missing block, now at 1.8 m
        assert df["max_t2m_60min"][0] == pytest.approx(275.75)
        assert df["max_t2m_60min_level"][0] == pytest.approx(1.8)


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_ground_sensor_below_0p5m_ignored(level_columns):
    # synop_150_85_M22.bufr: min block at 1.5 m with min=274.05, then a
    # second min block at 0.1 m with min=272.55; the 0.1 m sensor is below
    # 0.5 m and must be ignored for the 2 m temperature
    df = read_period_file("synop_150_85_M22.bufr", level_columns)

    assert df["max_t2m_60min"][0] == pytest.approx(274.15)
    assert df["min_t2m_60min"][0] == pytest.approx(274.05)

    if level_columns:
        assert df["min_t2m_60min_level"][0] == pytest.approx(1.5)
        assert df["max_t2m_60min_level"][0] == pytest.approx(1.5)


@pytest.mark.parametrize("name", PERIOD_FILES)
def test_no_ground_level_reported_for_t2m(name):
    # reviewer blocker 1 (D2): no min/max_t2m level column may report a
    # sensor below 0.5 m, also when the ground value is the only candidate
    # for its period (then the period is reported as a missing value)
    df = read_period_file(name, True)

    for c in df.columns:
        if c.startswith(("max_t2m_", "min_t2m_")) and c.endswith("_level"):
            v = df[c][0]
            assert v is None or v != v or v >= 0.5, (name, c, v)


# ---------------------------------------------------------------------------
# D3 / A2: naming invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
@pytest.mark.parametrize("name", PERIOD_FILES)
def test_no_nan_suffix_in_any_column_name(name, level_columns):
    df = read_period_file(name, level_columns)

    assert [c for c in df.columns if c.endswith("_nan")] == []


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
@pytest.mark.parametrize("name", ["synop_0_212_M14.bufr", "synop_176_98_M29.bufr"])
def test_extremes_with_missing_values_emit_no_suffixed_column(name, level_columns):
    # synop_0_212_M14.bufr: extreme temperatures with MISSING value AND
    # MISSING own timePeriod; neither may produce a suffixed extreme column
    # (period suffix, _0h, _nan, _level, _units) or a non-null extreme value.
    # The plain requested columns max_t2m/min_t2m may appear as the generic
    # "requested but not found" result, but only filled with None/NaN.
    # synop_176_98_M29.bufr: the -12/0 pairs are present but both extreme
    # values are MISSING; per A8 the suffixed all-None columns with a valid
    # period name (e.g. max_t2m_12h) are allowed here, but _0h, _nan and any
    # non-null value are not.
    df = read_period_file(name, level_columns)

    if name == "synop_0_212_M14.bufr":
        assert [c for c in df.columns if c.startswith(("max_t2m_", "min_t2m_"))] == []
    else:
        suffixed = [c for c in df.columns if c.startswith(("max_t2m_", "min_t2m_"))]
        assert suffixed != []
        for c in suffixed:
            assert "_nan" not in c, c
            assert "_0h" not in c, c
            # the extreme VALUE may not be non-null; its _level/_units columns
            # describe the reported sensor and may carry values
            if not c.endswith(("_level", "_units")):
                assert df[c].isna().all(), f"{c} must be all-None, got\n{df[c]}"

    for base in ("max_t2m", "min_t2m"):
        if base in df.columns:
            value = df[base][0]
            assert value is None or (isinstance(value, float) and value != value)


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_present_value_with_missing_period_uses_plain_name(level_columns):
    # synop_0_212_M14.bufr: total precipitation block with value 0.0 and
    # MISSING timePeriod -> plain "precipitation" column, not
    # "precipitation_nan"
    df = read_period_file("synop_0_212_M14.bufr", level_columns)

    assert df["precipitation"][0] == pytest.approx(0.0)
    assert "precipitation_nan" not in df.columns


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
def test_positive_periods_are_named_without_minus(level_columns):
    # synop_0_231_M15.bufr is corrupt: it encodes positive timePeriod values
    # (53, 1448, 2010, 2046, 1990, 2041, 297, 1156, 476 minutes/hours).
    # Reading must not crash and no period-derived column name may contain
    # a "-" (A2: the period is read by its absolute value).
    df = read_period_file("synop_0_231_M15.bufr", level_columns)

    assert [c for c in df.columns if "-" in c] == []


# ---------------------------------------------------------------------------
# phantom level columns
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
@pytest.mark.parametrize("name", PERIOD_FILES)
def test_level_column_never_appears_without_value_column(name, level_columns):
    # e.g. buoy_12_98_M13.bufr only has maximum/minimumTemperatureAt2MPast12-
    # Hours with MISSING values, so it must not produce
    # max_t2m_12h_level=2 without a max_t2m_12h column
    df = read_period_file(name, level_columns)

    phantom = [c for c in df.columns if c.endswith("_level") and c[: -len("_level")] not in df.columns]
    assert phantom == []


# ---------------------------------------------------------------------------
# D2 / A3: the collision selection helper, tested directly with synthetic
# records (no BUFR file involved)
# ---------------------------------------------------------------------------


MIN_KEY = "minimumTemperatureAtHeightAndOverPeriodSpecified"
MAX_KEY = "maximumTemperatureAtHeightAndOverPeriodSpecified"
GUST_KEY = "maximumWindGustSpeed"
HEIGHT_KEY = "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform"


def _record(key, value, height, period=-60, units="min"):
    """A raw collected record (key name -> (value, units)) for the synthetic tests."""
    return {
        "timePeriod": (period, units),
        key: (value, None),
        HEIGHT_KEY: (height, "m"),
    }


def _mint_dynamic():
    return MinTAccessor().accessors[0]


MIN_FIXED_12H = "minimumTemperatureAtHeightSpecifiedPast12Hours"
MIN_FIXED_24H = "minimumTemperatureAtHeightSpecifiedPast24Hours"
MAX_FIXED_12H = "maximumTemperatureAtHeightSpecifiedPast12Hours"
MAX_FIXED_24H = "maximumTemperatureAtHeightSpecifiedPast24Hours"
STATION_HEIGHT_KEY = "heightAboveStation"


def _fixed_period_accessor(multi, bufr_key, coord_key=HEIGHT_KEY):
    """The sub-accessor of *multi* reading *bufr_key* with the *coord_key* height."""
    return next(a for a in multi.accessors if bufr_key in a.keys and any(c.name == coord_key for c in a.extract_coords))


def _fixed_record(key, value, height, coord_key=HEIGHT_KEY):
    """A raw collected record for a fixed-period AtHeightSpecified temperature key."""
    return {key: (value, None), coord_key: (height, "m")}


def _no_height_record(key, value, period=-60, units="min"):
    """A raw collected record with a value and a period but NO height descriptor."""
    return {"timePeriod": (period, units), key: (value, None)}


def test_height_closest_to_2m_wins() -> None:
    # D2: two eligible heights on the same label+period, the closest to 2 m wins
    # (and its _level follows it), regardless of the message order
    records = [_record(MIN_KEY, 274.05, 2.5), _record(MIN_KEY, 275.45, 2.0)]
    res = _mint_dynamic().collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<60min>": 275.45, "min_t2m_<60min>_level": 2.0}

    records = [_record(MIN_KEY, 275.45, 2.0), _record(MIN_KEY, 274.05, 2.5)]
    res = _mint_dynamic().collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<60min>": 275.45, "min_t2m_<60min>_level": 2.0}


def test_missing_height_ranks_after_valid_height() -> None:
    # D2: a value without a height is accepted, but ranks after any value with
    # an eligible height; the buggy last-wins merge would take the later block
    records = [
        _record(MIN_KEY, 275.45, 2.5),
        _record(MIN_KEY, 274.95, None),  # height present in the message but MISSING
    ]
    res = _mint_dynamic().collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<60min>": 275.45, "min_t2m_<60min>_level": 2.5}


def test_ground_sensor_excluded_for_temperatures_only() -> None:
    # D2: sensors below 0.5 m are ignored for the 2 m temperatures even though
    # 0.1 m would rank first by plain distance to 2 m (|0.1-2| < |4.5-2|)
    records = [_record(MIN_KEY, 272.55, 0.1), _record(MIN_KEY, 274.05, 4.5)]
    res = _mint_dynamic().collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<60min>": 274.05, "min_t2m_<60min>_level": 4.5}

    # for the gust (nominal 10 m, no ground exclusion) the ground sensor is a
    # normal candidate: |0.4-10| < |20-10|
    gust = WindGustSpeedAccessor().accessors[0]
    records = [_record(GUST_KEY, 25.0, 0.4), _record(GUST_KEY, 20.0, 20.0)]
    res = gust.collect(_RecordCollector(records), add_coord=True)
    assert res == {"max_wgust_speed_<60min>": 25.0, "max_wgust_speed_<60min>_level": 0.4}


def test_gust_closest_to_10m_wins() -> None:
    # D2: other period parameters use their own nominal height (gust: 10 m);
    # |6-10| < |15-10| so the 6 m sensor wins
    gust = WindGustSpeedAccessor().accessors[0]
    records = [_record(GUST_KEY, 20.0, 15.0), _record(GUST_KEY, 25.0, 6.0)]
    res = gust.collect(_RecordCollector(records), add_coord=True)
    assert res == {"max_wgust_speed_<60min>": 25.0, "max_wgust_speed_<60min>_level": 6.0}


def test_ground_sensor_is_dropped_not_just_demoted() -> None:
    # reviewer blocker 1 (D2): a candidate below min_height is dropped before
    # ranking; as the sole candidate of its period it must not be emitted as a
    # real value nor with its ground level: the period is reported as a
    # missing value (no ground value, no ground level)
    records = [_record(MIN_KEY, 272.55, 0.1)]
    res = _mint_dynamic().collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<60min>": None, "min_t2m_<60min>_level": None}

    res = _mint_dynamic().collect(_RecordCollector(records), add_coord=False)
    assert res == {"min_t2m_<60min>": None}

    maxt = MaxTAccessor().accessors[0]
    records = [_record(MAX_KEY, 274.95, 0.05)]
    res = maxt.collect(_RecordCollector(records), add_coord=True)
    assert res == {"max_t2m_<60min>": None, "max_t2m_<60min>_level": None}


def test_ground_real_loses_to_missing_value_at_eligible_height() -> None:
    # reviewer blocker 1 (D2): a ground sensor value must not beat a missing
    # reading at 2 m; the period is reported as missing with the 2 m level of
    # the missing reading, in either message order
    for records in (
        [_record(MIN_KEY, 272.55, 0.1), _record(MIN_KEY, None, 2.0)],
        [_record(MIN_KEY, None, 2.0), _record(MIN_KEY, 272.55, 0.1)],
    ):
        res = _mint_dynamic().collect(_RecordCollector(records), add_coord=True)
        assert res == {"min_t2m_<60min>": None, "min_t2m_<60min>_level": 2.0}


def test_value_without_height_descriptor_is_accepted() -> None:
    # reviewer blocker 3 (D2): a temperature reported with NO height descriptor
    # at all must still be collected (the height is optional) and is accepted
    # as a candidate; without a height there is no level to report
    ac = _mint_dynamic()
    res = ac.collect(_RecordCollector([_no_height_record(MIN_KEY, 275.45)]), add_coord=True)
    assert res == {"min_t2m_<60min>": 275.45, "min_t2m_<60min>_level": None}

    res = ac.collect(_RecordCollector([_no_height_record(MIN_KEY, 275.45)]), add_coord=False)
    assert res == {"min_t2m_<60min>": 275.45}

    maxt = MaxTAccessor().accessors[0]
    res = maxt.collect(_RecordCollector([_no_height_record(MAX_KEY, 291.49)]), add_coord=True)
    assert res == {"max_t2m_<60min>": 291.49, "max_t2m_<60min>_level": None}

    # the whole MinT accessor keeps the no-height value as its candidate
    res = MinTAccessor().collect(_RecordCollector([_no_height_record(MIN_KEY, 275.45)]), add_coord=True)
    assert res == {"min_t2m_<60min>": 275.45, "min_t2m_<60min>_level": None}


def test_value_without_height_ranks_after_valid_height() -> None:
    # reviewer blocker 3 (D2): a value without a height ranks after any value
    # with an eligible height (in either order), but still beats a missing
    # value (A3)
    ac = _mint_dynamic()
    records = [_no_height_record(MIN_KEY, 274.95), _record(MIN_KEY, 275.45, 2.0)]
    res = ac.collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<60min>": 275.45, "min_t2m_<60min>_level": 2.0}
    res = ac.collect(_RecordCollector(records[::-1]), add_coord=True)
    assert res == {"min_t2m_<60min>": 275.45, "min_t2m_<60min>_level": 2.0}

    records = [_no_height_record(MIN_KEY, 275.45), _record(MIN_KEY, None, 2.0)]
    res = ac.collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<60min>": 275.45, "min_t2m_<60min>_level": None}


@pytest.mark.parametrize(
    "multi,key,label",
    [
        (MinTAccessor(), MIN_FIXED_12H, "min_t2m_<12h>"),
        (MinTAccessor(), MIN_FIXED_24H, "min_t2m_<24h>"),
        (MaxTAccessor(), MAX_FIXED_12H, "max_t2m_<12h>"),
        (MaxTAccessor(), MAX_FIXED_24H, "max_t2m_<24h>"),
    ],
)
def test_fixed_period_at_height_specified_ranks_all_candidates(multi, key, label) -> None:
    # reviewer blocker 2: the fixed-period height-specified temperature
    # accessors collected only the FIRST record, so with a 4.5 m block in
    # front of the 2 m one the 4.5 m value was returned; they must collect
    # all candidates and take the height closest to 2 m, in either order
    ac = _fixed_period_accessor(multi, key)
    records = [_fixed_record(key, 274.05, 4.5), _fixed_record(key, 275.45, 2.0)]
    expected = {label: 275.45, label + "_level": 2.0}
    assert ac.collect(_RecordCollector(records), add_coord=True) == expected
    assert ac.collect(_RecordCollector(records[::-1]), add_coord=True) == expected


def test_fixed_period_at_height_above_station_ranks_all_candidates() -> None:
    # reviewer blocker 2: same for the heightAboveStation variants
    ac = _fixed_period_accessor(MinTAccessor(), MIN_FIXED_24H, STATION_HEIGHT_KEY)
    records = [
        _fixed_record(MIN_FIXED_24H, 288.5, 4.5, STATION_HEIGHT_KEY),
        _fixed_record(MIN_FIXED_24H, 289.7, 2.0, STATION_HEIGHT_KEY),
    ]
    expected = {"min_t2m_<24h>": 289.7, "min_t2m_<24h>_level": 2.0}
    assert ac.collect(_RecordCollector(records), add_coord=True) == expected
    assert ac.collect(_RecordCollector(records[::-1]), add_coord=True) == expected


def test_fixed_period_ground_sensor_dropped() -> None:
    # blockers 1 + 2 together on the fixed-period path: a sole 0.1 m minimum
    # for the 12 h period must not be emitted, and with a missing value at
    # 2 m behind it the 2 m level wins
    ac = _fixed_period_accessor(MinTAccessor(), MIN_FIXED_12H)
    res = ac.collect(_RecordCollector([_fixed_record(MIN_FIXED_12H, 272.55, 0.1)]), add_coord=True)
    assert res == {"min_t2m_<12h>": None, "min_t2m_<12h>_level": None}

    records = [_fixed_record(MIN_FIXED_12H, 272.55, 0.1), _fixed_record(MIN_FIXED_12H, None, 2.0)]
    res = ac.collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<12h>": None, "min_t2m_<12h>_level": 2.0}


def test_min_t_12h_two_heights_full_accessor() -> None:
    # reviewer blocker 2 reproduction through the whole MinT accessor: a 12 h
    # minimum at 4.5 m followed by the 2 m one must report the 2 m value
    records = [_fixed_record(MIN_FIXED_12H, 274.05, 4.5), _fixed_record(MIN_FIXED_12H, 275.45, 2.0)]
    res = MinTAccessor().collect(_RecordCollector(records), add_coord=True)
    assert res == {"min_t2m_<12h>": 275.45, "min_t2m_<12h>_level": 2.0}


def test_missing_value_never_wins_a_collision() -> None:
    # A3: the real value wins a collision with a missing one and keeps its
    # _level/_units columns; the missing candidate's level does not sneak in
    base = {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": 1.25, "max_t2m_<12h>_units": "K"}
    new = {"max_t2m_<12h>": None, "max_t2m_<12h>_level": 2, "min_t2m_<24h>_level": 2}
    assert merge_period_results(dict(base), new) == base

    # a real value replaces a missing one, with its own level
    merged = merge_period_results(
        {"max_t2m_<12h>": None, "max_t2m_<12h>_level": 2}, {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": 1.25}
    )
    assert merged == {"max_t2m_<12h>": 291.49, "max_t2m_<12h>_level": 1.25}

    # the winner's derived columns replace the previous ones completely
    merged = merge_period_results({"max_t2m_<12h>": 1.0, "max_t2m_<12h>_units": "K"}, {"max_t2m_<12h>": 2.0})
    assert merged == {"max_t2m_<12h>": 2.0}


def test_maxt_keeps_dynamic_and_fixed_periods_side_by_side() -> None:
    # A3: like MinT, MaxT reports every distinct period: a dynamic 12 h value
    # and a fixed-key (maximumTemperatureAt2MPast24Hours) 24 h value coexist,
    # and a MISSING fixed-key fallback value never overwrites the dynamic real
    # value nor its level (this was the phantom/fallback bug)
    records = [
        _record(MAX_KEY, 291.49, 1.25, period=-12, units="h"),
        {"maximumTemperatureAt2MPast24Hours": (288.5, None)},
        {"maximumTemperatureAt2MPast12Hours": (None, None)},
    ]
    res = MaxTAccessor().collect(_RecordCollector(records), add_coord=True)
    assert res == {
        "max_t2m_<12h>": 291.49,
        "max_t2m_<12h>_level": 1.25,
        "max_t2m_<24h>": 288.5,
        "max_t2m_<24h>_level": 2,
    }


# ---------------------------------------------------------------------------
# fixed-period 2 m extremes (minimum/maximumTemperatureAt2MPast12/24Hours)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("level_columns", LEVEL_COLUMNS)
@pytest.mark.parametrize(
    "name,expected",
    [
        # ~/metview/BUFR/surf_land/synop_4_98_M13.bufr: minimumTemperatureAt2MPast24Hours
        # = 275.9 K, maximumTemperatureAt2MPast24Hours MISSING, no timePeriod keys
        ("synop_4_98_M13.bufr", {"min_t2m_24h": 275.9, "max_t2m_24h": None}),
        # message 86 of tests/sample_data/perf_synop.bufr, written out unchanged:
        # minimumTemperatureAt2MPast12Hours = 275.3 K,
        # maximumTemperatureAt2MPast12Hours = 279.0 K
        ("synop_min_t2m_12h.bufr", {"min_t2m_12h": 275.3, "max_t2m_12h": 279.0}),
    ],
)
def test_fixed_period_2m_extremes(name, expected, level_columns):
    # the period comes from the key name and the level is the fixed 2 m
    df = read_period_file(name, level_columns)

    extremes = {c for c in df.columns if c.startswith(("max_t2m", "min_t2m"))}
    if level_columns:
        assert extremes == set(expected) | {c + "_level" for c in expected}
    else:
        assert extremes == set(expected)

    for col, value in expected.items():
        v = df[col][0]
        if value is None:
            assert v is None or v != v
        else:
            assert v == pytest.approx(value)
        if level_columns:
            assert df[col + "_level"][0] == 2
