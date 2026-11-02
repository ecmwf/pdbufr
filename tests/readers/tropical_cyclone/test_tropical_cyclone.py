# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""Tests for the "tropical-cyclone" reader.

Test data:

- ``tropical_cyclone.bufr``: the old layout (no wind radii). It has 3 compressed messages: storms
  27W, 70E and 71W with 52, 52 and 37 ensemble members (subsets), base time 2015-11-18 00 UTC.
- ``tropical_cyclone_316082.bufr``: the current layout (WMO template 3 16 082) with wind radii. It is
  a small selection of messages from the ECMWF open data tropical cyclone tracks of the forecast
  of 2026-10-29 00 UTC (``ifs/0p25/enfo`` and ``ifs/0p25/oper``,
  https://data.ecmwf.int/forecasts/20261029/00z/ifs/0p25/), which are distributed under the
  CC-BY-4.0 licence (https://creativecommons.org/licenses/by/4.0/). Message 1 is storm 74E
  (compressed, members 3, 23 and 28), message 2 is storm 71W (uncompressed, member 51) and
  message 3 is storm 22E VANCE (uncompressed, member 51, no forecast steps).

All the messages of both files are ECMWF tropical cyclone tracks, i.e. ``dataCategory`` 7,
``dataSubCategory`` 32 and ``bufrHeaderCentre`` 98, which is the input the reader supports (see
``test_tropical_cyclone_supported_header``). ``_messages()`` keeps them apart from the other
messages of a file by checking ``dataCategory`` on its own.

The reference values are not taken from the reader. They were extracted with ecCodes using the ranks
of the BUFR keys (``#<rank>#<key>``), see ``_ranked_rows()``, which only relies on the order of the
keys in the template:

- the header keys have the rank 1
- analysis: observed centre = ``#1#latitude/longitude`` (meteorologicalAttributeSignificance 1),
  analysis centre = ``#2#latitude/longitude`` (significance 4 or 5), max wind position =
  ``#3#latitude/longitude`` (significance 3), pressure ``#1#pressureReducedToMeanSeaLevel`` and
  max wind speed ``#1#windSpeedAt10M``
- step i (1..N): ``#i#timePeriod``, centre ``#(2i+2)#latitude/longitude``, max wind position
  ``#(2i+3)#latitude/longitude``, ``#(i+1)#pressureReducedToMeanSeaLevel``, ``#(i+1)#windSpeedAt10M``
- wind radii (new layout only): for the thresholds 18, 26 and 33 m/s (``#(3i+k+1)#windSpeedThreshold``)
  4 quadrants (bearing start 0, 90, 180, 270 deg) of
  ``#r#effectiveRadiusWithRespectToWindSpeedsAboveThreshold`` with r = (3i+k)*4+q+1

In compressed messages these keys are arrays with one value per subset, in uncompressed
messages each message has one subset.
"""

import datetime
import os

import eccodes
import numpy as np
import pandas as pd
import pytest

import pdbufr
from pdbufr.high_level_bufr.bufr import BufrFile
from pdbufr.readers.tropical_cyclone import BUFR_HEADER_CENTRE, DATA_CATEGORY, DATA_SUB_CATEGORY, TropicalCycloneReader
from pdbufr.utils.testing import sample_test_data_path

OLD_LAYOUT = sample_test_data_path("tropical_cyclone.bufr")
NEW_LAYOUT = sample_test_data_path("tropical_cyclone_316082.bufr")
NOT_CYCLONE = sample_test_data_path("syn_new.bufr")

READER = "tropical-cyclone"


def _get_data():
    import sys

    here = os.path.dirname(__file__)
    sys.path.insert(0, here)
    import _tropical_cyclone_ref_data

    return _tropical_cyclone_ref_data


DATA = _get_data()

DEFAULT_COLUMNS = DATA.DEFAULT_COLUMNS
RADII_COLUMNS = DATA.RADII_COLUMNS
ALL_COLUMNS = DATA.ALL_COLUMNS

THRESHOLDS = (18, 26, 33)
QUADRANTS = ("ne", "se", "sw", "nw")
RADIUS_KEY = "effectiveRadiusWithRespectToWindSpeedsAboveThreshold"


def read(path, **kwargs):
    return pdbufr.read_bufr(path, reader=READER, **kwargs)


# ---------------------------------------------------------------------------------------------
# independent extraction with ecCodes
# ---------------------------------------------------------------------------------------------


class _Message:
    """A BUFR message read with ecCodes and accessed with ranked keys."""

    def __init__(self, handle):
        self.handle = handle
        eccodes.codes_set(handle, "unpack", 1)
        self.number_of_subsets = eccodes.codes_get(handle, "numberOfSubsets")
        self.compressed = bool(eccodes.codes_get(handle, "compressedData"))
        self.cache = {}

    def get(self, key, subset):
        """Value of a ranked key in a subset (0-based). None when it is missing."""
        if key not in self.cache:
            try:
                self.cache[key] = eccodes.codes_get_array(self.handle, key)
            except eccodes.KeyValueNotFoundError:
                self.cache[key] = None
        values = self.cache[key]
        if values is None:
            return None
        if self.compressed and len(values) == self.number_of_subsets > 1:
            value = values[subset]
        else:
            # one value for all the subsets (e.g. a replication factor) or one subset
            assert len(values) == 1, key
            assert self.compressed or subset == 0
            value = values[0]
        if isinstance(value, (str, bytes)):
            return value
        value = value.item()
        if value in (eccodes.CODES_MISSING_DOUBLE, eccodes.CODES_MISSING_LONG):
            return None
        return value

    def has(self, key):
        return eccodes.codes_is_defined(self.handle, key)


def _messages(path):
    """Generate the message number (1-based) and the cyclone messages of a file."""
    with open(path, "rb") as f:
        number = 0
        while True:
            handle = eccodes.codes_bufr_new_from_file(f)
            if handle is None:
                break
            number += 1
            try:
                if eccodes.codes_get(handle, "dataCategory") == 7:
                    yield number, _Message(handle)
            finally:
                eccodes.codes_release(handle)


def _raw(path, message, key, subset):
    """Value of a ranked key of a message (1-based) and subset (0-based) of a file."""
    for number, msg in _messages(path):
        if number == message:
            return msg.get(key, subset)
    raise AssertionError(f"no message {message} in {path}")


def _subset_rows(msg, subset):
    """All the rows (the analysis and the steps, also when missing) of a subset, with all columns."""

    def g(key):
        return msg.get(key, subset)

    n_steps = int(msg.get("#1#delayedDescriptorReplicationFactor", 0))
    base_time = datetime.datetime(g("#1#year"), g("#1#month"), g("#1#day"), g("#1#hour") or 0, g("#1#minute") or 0)
    has_radii = msg.has("#1#windSpeedThreshold")

    rows = []
    for i in range(n_steps + 1):
        if i == 0:
            step = 0
            lat, lon = g("#2#latitude"), g("#2#longitude")
            mslp = g("#1#pressureReducedToMeanSeaLevel")
            max_wind_lat, max_wind_lon = g("#3#latitude"), g("#3#longitude")
            max_wind_speed = g("#1#windSpeedAt10M")
        else:
            step = g(f"#{i}#timePeriod")
            lat, lon = g(f"#{2 * i + 2}#latitude"), g(f"#{2 * i + 2}#longitude")
            mslp = g(f"#{i + 1}#pressureReducedToMeanSeaLevel")
            max_wind_lat, max_wind_lon = g(f"#{2 * i + 3}#latitude"), g(f"#{2 * i + 3}#longitude")
            max_wind_speed = g(f"#{i + 1}#windSpeedAt10M")

        row = {
            "storm_id": g("#1#stormIdentifier").strip(),
            "storm_name": g("#1#longStormName").strip(),
            "member": g("#1#ensembleMemberNumber"),
            "base_time": base_time,
            "step": step,
            "valid_time": None if step is None else base_time + datetime.timedelta(hours=step),
            "lat": lat,
            "lon": lon,
            "mslp": mslp,
            "max_wind_lat": max_wind_lat,
            "max_wind_lon": max_wind_lon,
            "max_wind_speed": max_wind_speed,
            "observed_lat": g("#1#latitude"),
            "observed_lon": g("#1#longitude"),
            "forecast_type": g("#1#ensembleForecastType"),
        }
        for k, threshold in enumerate(THRESHOLDS):
            for q, quadrant in enumerate(QUADRANTS):
                value = None
                if has_radii:
                    rank = (i * 3 + k) * 4 + q + 1
                    # check the layout of the radii
                    assert g(f"#{i * 3 + k + 1}#windSpeedThreshold") == threshold
                    assert g(f"#{2 * rank - 1}#bearingOrAzimuth") == 90 * q
                    value = g(f"#{rank}#{RADIUS_KEY}")
                row[f"radius_{threshold}ms_{quadrant}"] = value
        rows.append(row)
    return rows


def _ranked_rows(path):
    """Extract the rows of all the cyclone messages of a file in the order of the reader."""
    rows = []
    for _, msg in _messages(path):
        for subset in range(msg.number_of_subsets):
            rows.extend(_subset_rows(msg, subset))
    return rows


def _is_valid(row):
    return row["lat"] is not None and row["lon"] is not None


# ---------------------------------------------------------------------------------------------
# helpers to compare
# ---------------------------------------------------------------------------------------------


def _make_frame(rows, columns=None):
    """Build a DataFrame from reference rows (missing values are None)."""
    df = pd.DataFrame(rows, columns=columns)
    for c in df.columns:
        if c in ("base_time", "valid_time"):
            df[c] = pd.to_datetime(df[c])
        elif c in ("step", "member", "forecast_type"):
            df[c] = df[c].astype("float64")
        elif c not in ("storm_id", "storm_name"):
            df[c] = df[c].astype("float64")
    return df.reset_index(drop=True)


def _normalise(df):
    df = df.copy()
    for c in ("step", "member", "forecast_type"):
        if c in df.columns:
            df[c] = df[c].astype("float64")
    return df.reset_index(drop=True)


def assert_same(df, df_ref):
    __tracebackhide__ = True
    pd.testing.assert_frame_equal(
        _normalise(df),
        _make_frame(df_ref) if isinstance(df_ref, list) else df_ref,
        check_dtype=False,
        check_index_type=False,
    )


def _ref(rows, columns=None):
    return _make_frame(rows, columns)


# ---------------------------------------------------------------------------------------------
# default columns, old layout
# ---------------------------------------------------------------------------------------------


def test_tropical_cyclone_old_layout_default_columns():
    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4})
    assert list(df.columns) == DEFAULT_COLUMNS
    assert len(df) == 19
    assert df["step"].tolist() == [*range(0, 18, 6), *range(24, 120, 6)]
    assert_same(df, DATA.REF_OLD_70E_MEMBER_4)

    # types
    assert df["step"].dtype == np.dtype("int64")
    assert df["member"].dtype == np.dtype("int64")
    assert df["base_time"].dtype.kind == "M"
    assert df["valid_time"].dtype.kind == "M"
    for c in ("lat", "lon", "mslp", "max_wind_lat", "max_wind_lon", "max_wind_speed"):
        assert df[c].dtype == np.dtype("float64"), c

    # valid time = base time + step
    assert (df["valid_time"] - df["base_time"]).tolist() == [pd.Timedelta(hours=int(s)) for s in df["step"]]
    assert df["base_time"].iloc[0] == pd.Timestamp("2015-11-18 00:00")
    assert df["storm_id"].unique().tolist() == ["70E"]
    assert df["storm_name"].unique().tolist() == ["70E"]


def test_tropical_cyclone_old_layout_has_no_wind_radii():
    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4}, columns="wind_radii")
    assert list(df.columns) == RADII_COLUMNS
    assert len(df) == 19
    assert df.isna().all().all()


# ---------------------------------------------------------------------------------------------
# new layout: wind radii, "all" columns
# ---------------------------------------------------------------------------------------------


def test_tropical_cyclone_new_layout_all_columns():
    df = read(NEW_LAYOUT, filters={"storm_id": "74E", "member": 28, "step": slice(270, 282)}, columns="all")
    assert list(df.columns) == ALL_COLUMNS
    assert df["step"].tolist() == [270, 276, 282]
    assert_same(df, DATA.REF_NEW_74E_MEMBER_28_FIRST_ROWS)

    assert df["base_time"].iloc[0] == pd.Timestamp("2026-10-29 00:00")
    assert df["valid_time"].tolist() == [
        pd.Timestamp("2026-11-09 06:00"),
        pd.Timestamp("2026-11-09 12:00"),
        pd.Timestamp("2026-11-09 18:00"),
    ]
    # the observed centre and the analysis are not available in this message
    assert df["observed_lat"].isna().all()
    assert (df["forecast_type"] == 4).all()


def test_tropical_cyclone_new_layout_wind_radii():
    df = read(NEW_LAYOUT, filters={"storm_id": "74E", "member": 23}, columns=["step", "wind_radii"])
    assert list(df.columns) == ["step", *RADII_COLUMNS]
    assert_same(df, DATA.REF_NEW_74E_MEMBER_23_RADII)

    # only some of the quadrants are non-zero at step 348
    row = df[df["step"] == 348].iloc[0]
    assert row["radius_18ms_ne"] == 0
    assert row["radius_18ms_se"] == 174100
    assert row["radius_18ms_sw"] == 75900
    assert row["radius_18ms_nw"] == 27800
    assert (row[[c for c in RADII_COLUMNS if not c.startswith("radius_18ms")]] == 0).all()


def test_tropical_cyclone_new_layout_uncompressed_message():
    df = read(NEW_LAYOUT, filters={"storm_id": "71W"})
    assert list(df.columns) == DEFAULT_COLUMNS
    assert df["step"].tolist() == [204, 210, 216, 222, 228, 234, 240, 264]
    assert df["member"].unique().tolist() == [51]
    assert_same(df, DATA.REF_NEW_71W)

    # the other message of the same storm layout is not mixed in
    df = read(NEW_LAYOUT, filters={"count": 2}, columns="all")
    assert df["storm_id"].unique().tolist() == ["71W"]
    assert len(df) == 8
    assert df["radius_18ms_ne"].tolist()[-1] == 931600
    assert df["radius_26ms_ne"].tolist()[-1] == 816700


def test_tropical_cyclone_zero_step_message():
    # storm 22E VANCE has only the analysis, and it has no analysis centre
    df = read(NEW_LAYOUT, filters={"storm_id": "22E"}, columns="all", keep_missing=True)
    assert len(df) == 1
    assert df["step"].tolist() == [0]
    assert df["storm_name"].tolist() == ["VANCE"]
    assert_same(df, DATA.REF_NEW_22E_KEEP_MISSING)
    row = df.iloc[0]
    assert np.isnan(row["lat"]) and np.isnan(row["lon"]) and np.isnan(row["mslp"])
    assert row["observed_lat"] == 20.7
    assert row["observed_lon"] == -108.4

    # no centre, no row
    df = read(NEW_LAYOUT, filters={"storm_id": "22E"})
    assert df.empty
    assert list(df.columns) == DEFAULT_COLUMNS


# ---------------------------------------------------------------------------------------------
# keep_missing
# ---------------------------------------------------------------------------------------------


def test_tropical_cyclone_keep_missing_member_row_counts():
    filters = {"storm_id": "70E", "member": 4}
    assert len(read(OLD_LAYOUT, filters=filters)) == 19
    df = read(OLD_LAYOUT, filters=filters, keep_missing=True)
    # the analysis and the 33 steps
    assert len(df) == 34
    assert df["step"].tolist() == list(range(0, 199, 6))
    assert df["lat"].notna().sum() == 19

    filters = {"storm_id": "74E", "member": 3}
    assert len(read(NEW_LAYOUT, filters=filters)) == 7
    # the analysis and the 60 steps
    assert len(read(NEW_LAYOUT, filters=filters, keep_missing=True)) == 61


@pytest.mark.parametrize(
    "path,n_default,n_keep",
    [
        (OLD_LAYOUT, 2721, 5417),
        (NEW_LAYOUT, 34, 229),
    ],
)
def test_tropical_cyclone_keep_missing_file_row_counts(path, n_default, n_keep):
    rows = _ranked_rows(path)
    # the counts of the independent extraction
    assert len(rows) == n_keep
    assert sum(_is_valid(r) for r in rows) == n_default

    assert len(read(path)) == n_default
    assert len(read(path, columns="all")) == n_default
    assert len(read(path, keep_missing=False)) == n_default
    assert len(read(path, keep_missing=True)) == n_keep


def test_tropical_cyclone_keep_missing_no_values_for_missing_steps():
    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4, "step": [12, 18, 24]}, keep_missing=True)
    assert_same(df, DATA.REF_OLD_70E_MEMBER_4_STEPS_12_18_24)


# ---------------------------------------------------------------------------------------------
# columns
# ---------------------------------------------------------------------------------------------


def test_tropical_cyclone_columns_default_and_all():
    filters = {"storm_id": "27W", "member": 1, "step": 0}
    assert list(read(OLD_LAYOUT, filters=filters).columns) == DEFAULT_COLUMNS
    assert list(read(OLD_LAYOUT, filters=filters, columns="default").columns) == DEFAULT_COLUMNS
    assert list(read(OLD_LAYOUT, filters=filters, columns=[]).columns) == DEFAULT_COLUMNS
    assert list(read(OLD_LAYOUT, filters=filters, columns=["default"]).columns) == DEFAULT_COLUMNS

    assert ALL_COLUMNS == [*DEFAULT_COLUMNS, *RADII_COLUMNS, "observed_lat", "observed_lon", "forecast_type"]
    assert list(read(OLD_LAYOUT, filters=filters, columns="all").columns) == ALL_COLUMNS
    assert len(ALL_COLUMNS) == 27


def test_tropical_cyclone_columns_list():
    filters = {"storm_id": "27W", "member": 1, "step": 0}
    # the output order does not depend on the order in columns
    df = read(OLD_LAYOUT, filters=filters, columns=["lat", "storm_id", "observed_lon"])
    assert list(df.columns) == ["storm_id", "lat", "observed_lon"]
    assert df.iloc[0].tolist() == ["27W", pytest.approx(5.4), pytest.approx(157.2)]

    df = read(NEW_LAYOUT, filters={"storm_id": "71W", "step": 204}, columns=["step", "wind_radii", "lat"])
    assert list(df.columns) == ["step", "lat", *RADII_COLUMNS]

    # groups and names together
    df = read(OLD_LAYOUT, filters=filters, columns=["wind_radii", "forecast_type", "storm_id"])
    assert list(df.columns) == ["storm_id", *RADII_COLUMNS, "forecast_type"]


@pytest.mark.parametrize("columns", ["pressure", ["lat", "latitude"], "radius_18ms", ["all", "wrong"]])
def test_tropical_cyclone_columns_unknown(columns):
    with pytest.raises(ValueError, match="Invalid tropical cyclone column"):
        read(OLD_LAYOUT, columns=columns)


@pytest.mark.parametrize("reader", ["tropical-cyclone", "tropical_cyclone"])
def test_tropical_cyclone_reader_spellings(reader):
    filters = {"storm_id": "70E", "member": 4}
    df = pdbufr.read_bufr(OLD_LAYOUT, reader=reader, filters=filters)
    assert_same(df, DATA.REF_OLD_70E_MEMBER_4)


# ---------------------------------------------------------------------------------------------
# filters
# ---------------------------------------------------------------------------------------------

_REF_70E = pd.DataFrame(DATA.REF_OLD_70E_MEMBER_4)


def _ref_70e(mask):
    return _ref(_REF_70E[mask].to_dict("records"))


def test_tropical_cyclone_filters_scalar():
    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4, "step": 12})
    assert_same(df, _ref_70e(_REF_70E["step"] == 12))
    assert df["lat"].tolist() == pytest.approx([11.7])
    assert df["mslp"].tolist() == [100300.0]

    df = read(NEW_LAYOUT, filters={"storm_name": "VANCE"}, keep_missing=True)
    assert df["storm_id"].tolist() == ["22E"]

    # one member of every storm that has a centre
    df = read(OLD_LAYOUT, filters={"member": 4, "step": 6})
    expected = [r["storm_id"] for r in _ranked_rows(OLD_LAYOUT) if r["member"] == 4 and r["step"] == 6 and _is_valid(r)]
    assert df["storm_id"].tolist() == expected == ["27W", "70E"]


def test_tropical_cyclone_filters_list():
    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4, "step": [0, 12, 120]})
    # no row at step 120
    assert_same(df, _ref_70e(_REF_70E["step"].isin([0, 12])))

    df = read(OLD_LAYOUT, filters={"storm_id": ["27W", "70E"], "member": [1, 2], "step": 0})
    assert list(zip(df["storm_id"], df["member"])) == [("27W", 1), ("27W", 2), ("70E", 1), ("70E", 2)]


def test_tropical_cyclone_filters_slice():
    # the end of the slice is included
    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4, "step": slice(0, 24)})
    assert df["step"].tolist() == [0, 6, 12, 24]
    assert_same(df, _ref_70e(_REF_70E["step"].between(0, 24)))

    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4, "step": slice(100, None)})
    assert df["step"].tolist() == [102, 108, 114]

    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": slice(2, 3), "step": slice(None, 6)})
    assert df["member"].tolist() == [2, 2, 3, 3]
    assert df["step"].tolist() == [0, 6, 0, 6]


def test_tropical_cyclone_filters_callable():
    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4, "step": lambda x: x % 24 == 0})
    assert df["step"].tolist() == [0, 24, 48, 72, 96]
    assert_same(df, _ref_70e(_REF_70E["step"] % 24 == 0))

    df = read(OLD_LAYOUT, filters={"storm_id": "70E", "member": 4, "mslp": lambda x: x < 100400})
    assert_same(df, _ref_70e(_REF_70E["mslp"] < 100400))


def test_tropical_cyclone_filters_count():
    rows = _ranked_rows(OLD_LAYOUT)
    n_70e = sum(1 for r in rows if _is_valid(r) and r["storm_id"] == "70E")
    n_27w = sum(1 for r in rows if _is_valid(r) and r["storm_id"] == "27W")

    df = read(OLD_LAYOUT, filters={"count": 2})
    assert df["storm_id"].unique().tolist() == ["70E"]
    assert len(df) == n_70e
    assert df["member"].max() == 52

    df = read(OLD_LAYOUT, filters={"count": [1, 3]})
    assert df["storm_id"].unique().tolist() == ["27W", "71W"]
    assert len(df[df["storm_id"] == "27W"]) == n_27w

    df = read(NEW_LAYOUT, filters={"count": 1})
    assert df["storm_id"].unique().tolist() == ["74E"]
    assert len(df) == 26

    assert read(OLD_LAYOUT, filters={"count": 4}).empty


def test_tropical_cyclone_filters_column_not_selected():
    # lat is only used in the filter
    df = read(
        OLD_LAYOUT,
        filters={"storm_id": "70E", "member": 4, "lat": slice(11, 11.5), "lon": lambda x: x > -127},
        columns=["step", "mslp"],
    )
    expected = _REF_70E[_REF_70E["lat"].between(11, 11.5) & (_REF_70E["lon"] > -127)]
    assert list(df.columns) == ["step", "mslp"]
    assert len(df) > 0
    assert df["step"].tolist() == expected["step"].tolist()
    assert df["mslp"].tolist() == expected["mslp"].tolist()

    # member, forecast_type and observed centre filters
    df = read(NEW_LAYOUT, filters={"forecast_type": 0}, columns=["storm_id", "member"])
    assert df["storm_id"].unique().tolist() == ["71W"]
    df = read(OLD_LAYOUT, filters={"observed_lat": 5.5, "step": 0}, columns=["storm_id", "member"])
    assert df["storm_id"].unique().tolist() == ["27W"]
    assert len(df) == 52

    # radii column not selected
    df = read(NEW_LAYOUT, filters={"radius_18ms_se": lambda x: x > 100000}, columns=["member", "step"])
    assert df["member"].tolist() == [23, 23]
    assert df["step"].tolist() == [348, 354]


def test_tropical_cyclone_filters_unknown_key():
    with pytest.raises(ValueError, match="Invalid filter key 'foo'"):
        read(OLD_LAYOUT, filters={"foo": 1})

    # a BUFR key gives a hint for the column name
    with pytest.raises(ValueError, match="storm_id"):
        read(OLD_LAYOUT, filters={"stormIdentifier": "70E"})
    with pytest.raises(ValueError, match="step"):
        read(OLD_LAYOUT, filters={"timePeriod": 6})


def test_tropical_cyclone_filters_no_match():
    for filters in ({"storm_id": "00X"}, {"storm_id": "70E", "member": 4, "step": 1000}, {"member": 100}):
        df = read(OLD_LAYOUT, filters=filters)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert list(df.columns) == DEFAULT_COLUMNS

    df = read(NEW_LAYOUT, filters={"storm_id": "00X"}, columns=["storm_id", "lat"], units_columns=True)
    assert df.empty
    assert list(df.columns) == ["storm_id", "lat", "lat_units"]


# ---------------------------------------------------------------------------------------------
# units
# ---------------------------------------------------------------------------------------------


def test_tropical_cyclone_units_dict_and_filter_on_converted_values():
    filters = {"storm_id": "70E", "member": 4}
    df = read(OLD_LAYOUT, filters=filters, columns=["step", "mslp"], units={"mslp": "hPa"})
    np.testing.assert_allclose(df["mslp"], _REF_70E["mslp"] / 100)
    assert df["mslp"].iloc[0] == pytest.approx(1005.0)

    # the filter is applied on the converted values
    df = read(
        OLD_LAYOUT, filters={**filters, "mslp": slice(1004, 1006)}, columns=["step", "mslp"], units={"mslp": "hPa"}
    )
    expected = _REF_70E[(_REF_70E["mslp"] / 100).between(1004, 1006)]
    assert len(df) == len(expected) == 9
    assert df["step"].tolist() == expected["step"].tolist()
    np.testing.assert_allclose(df["mslp"], expected["mslp"] / 100)
    assert df["mslp"].between(1004, 1006).all()

    # a filter on the original values does not match
    df = read(OLD_LAYOUT, filters={**filters, "mslp": slice(100400, 100600)}, units={"mslp": "hPa"})
    assert df.empty

    # without the conversion it is the opposite
    df = read(OLD_LAYOUT, filters={**filters, "mslp": slice(100400, 100600)})
    assert len(df) == 9
    assert read(OLD_LAYOUT, filters={**filters, "mslp": slice(1004, 1006)}).empty

    # the other columns are not converted
    df = read(OLD_LAYOUT, filters=filters, units={"mslp": "hPa"})
    assert_same(df.assign(mslp=df["mslp"] * 100), DATA.REF_OLD_70E_MEMBER_4)


def test_tropical_cyclone_units_si():
    filters = {"storm_id": "70E", "member": 4, "step": [0, 6]}
    df = read(OLD_LAYOUT, filters=filters, unit_system="si")
    assert list(df.columns) == DEFAULT_COLUMNS
    # degrees are converted to radians
    ref = _REF_70E[_REF_70E["step"].isin([0, 6])]
    for c in ("lat", "lon", "max_wind_lat", "max_wind_lon"):
        np.testing.assert_allclose(df[c], np.deg2rad(ref[c]), rtol=1e-6)
    np.testing.assert_allclose(df["mslp"], ref["mslp"])
    np.testing.assert_allclose(df["max_wind_speed"], ref["max_wind_speed"])

    # the default unit system is not changed
    df = read(OLD_LAYOUT, filters=filters, unit_system="pdbufr")
    assert_same(df, _ref_70e(_REF_70E["step"].isin([0, 6])))

    # filter on the converted values
    df = read(OLD_LAYOUT, filters={**filters, "lat": slice(0.18, 0.2)}, unit_system="si")
    assert df["step"].tolist() == [0]


def test_tropical_cyclone_units_columns():
    filters = {"storm_id": "70E", "member": 4, "step": [0, 6]}
    df = read(OLD_LAYOUT, filters=filters, columns=["step", "lat", "lon", "mslp", "max_wind_speed"], units_columns=True)
    assert list(df.columns) == [
        "step",
        "lat",
        "lat_units",
        "lon",
        "lon_units",
        "mslp",
        "mslp_units",
        "max_wind_speed",
        "max_wind_speed_units",
    ]
    assert df["lat_units"].tolist() == ["deg", "deg"]
    assert df["lon_units"].tolist() == ["deg", "deg"]
    assert df["mslp_units"].tolist() == ["Pa", "Pa"]
    assert df["max_wind_speed_units"].tolist() == ["m/s", "m/s"]

    df = read(
        OLD_LAYOUT,
        filters=filters,
        columns=["step", "lat", "mslp"],
        units={"mslp": "hPa"},
        units_columns=True,
    )
    assert list(df.columns) == ["step", "lat", "lat_units", "mslp", "mslp_units"]
    assert df["mslp_units"].tolist() == ["hPa", "hPa"]
    assert df["lat_units"].tolist() == ["deg", "deg"]
    assert df["mslp"].tolist() == pytest.approx([1005.0, 1006.0])

    df = read(OLD_LAYOUT, filters=filters, columns=["lat"], unit_system="si", units_columns=True)
    assert df["lat_units"].tolist() == ["rad", "rad"]

    # the radii are in m, also in the converted values
    df = read(
        NEW_LAYOUT,
        filters={"member": 23},
        columns=["radius_18ms_se"],
        units={"radius_18ms_se": "km"},
        units_columns=True,
    )
    assert df["radius_18ms_se"].tolist() == pytest.approx([0.0, 174.1, 135.2])
    assert df["radius_18ms_se_units"].tolist() == ["km"] * 3

    df = read(NEW_LAYOUT, filters={"member": 23}, columns=["radius_18ms_se"], units_columns=True)
    assert df["radius_18ms_se"].tolist() == [0.0, 174100.0, 135200.0]
    assert df["radius_18ms_se_units"].tolist() == ["m"] * 3

    # the columns without units
    df = read(OLD_LAYOUT, filters=filters, columns=["storm_id", "member", "step", "base_time"], units_columns=True)
    assert list(df.columns) == ["storm_id", "member", "base_time", "step"]


# ---------------------------------------------------------------------------------------------
# non-cyclone data
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("keep_missing", [False, True])
def test_tropical_cyclone_not_a_cyclone_file(keep_missing):
    df = read(NOT_CYCLONE, keep_missing=keep_missing)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert list(df.columns) == DEFAULT_COLUMNS

    df = read(NOT_CYCLONE, columns="all", filters={"storm_id": "70E"})
    assert df.empty
    assert list(df.columns) == ALL_COLUMNS


# ---------------------------------------------------------------------------------------------
# the header filter: only the ECMWF tropical cyclone messages are read
# ---------------------------------------------------------------------------------------------

# the header of the messages the reader supports
CYCLONE_HEADER = {"dataCategory": 7, "dataSubCategory": 32, "bufrHeaderCentre": 98}
SUPPORTED_HEADER_KEYS = tuple(CYCLONE_HEADER)


def test_tropical_cyclone_supported_header():
    # the constants of the reader are the header of the sample files and of the docstrings
    assert (DATA_CATEGORY, DATA_SUB_CATEGORY, BUFR_HEADER_CENTRE) == (7, 32, 98)

    for path in (OLD_LAYOUT, NEW_LAYOUT):
        n_messages = 0
        with open(path, "rb") as f:
            while True:
                handle = eccodes.codes_bufr_new_from_file(f)
                if handle is None:
                    break
                n_messages += 1
                try:
                    values = tuple(eccodes.codes_get(handle, key) for key in SUPPORTED_HEADER_KEYS)
                finally:
                    eccodes.codes_release(handle)
                assert values == (7, 32, 98), (path, n_messages, values)
        assert n_messages > 0


def test_tropical_cyclone_filter_header():
    reader = TropicalCycloneReader(OLD_LAYOUT)

    assert reader.filter_header(dict(CYCLONE_HEADER))

    # all three values are needed, whatever the other ones are
    for key in SUPPORTED_HEADER_KEYS:
        for value in (0, 1, 6, 31, 33, 97, 99, 170, 254):
            assert value != CYCLONE_HEADER[key], (key, value)
            assert not reader.filter_header({**CYCLONE_HEADER, key: value}), (key, value)


class _HeaderMessage(dict):
    """A message with only the header keys, that records whether the reader has unpacked it."""

    def __init__(self, header):
        super().__init__(header)
        self.unpacked = False

    def __setitem__(self, key, value):
        self.unpacked = self.unpacked or key == "unpack"
        super().__setitem__(key, value)


def test_tropical_cyclone_header_is_filtered_before_unpacking(monkeypatch):
    # the messages below have no data section, so the ones that are not cyclones must be skipped
    # before they are unpacked. read_message is replaced to see which messages are accepted
    accepted = []

    def spy(self, message, bufr_filters=None):
        accepted.append(message)
        return iter(())

    monkeypatch.setattr(TropicalCycloneReader, "read_message", spy)

    cyclone = _HeaderMessage(CYCLONE_HEADER)
    other_sub_category = _HeaderMessage({**CYCLONE_HEADER, "dataSubCategory": 3})
    other_centre = _HeaderMessage({**CYCLONE_HEADER, "bufrHeaderCentre": 170})

    df = pdbufr.read_bufr([other_sub_category, cyclone, other_centre], reader=READER)

    assert len(accepted) == 1
    assert cyclone.unpacked
    assert not other_sub_category.unpacked
    assert not other_centre.unpacked

    # the messages that are skipped give no row and no error
    assert df.empty
    assert list(df.columns) == DEFAULT_COLUMNS


@pytest.mark.parametrize(
    "overrides",
    [
        {},  # the messages of the file, as they are
        {"dataCategory": 1},
        {"dataSubCategory": 3},
        {"bufrHeaderCentre": 170},
        {"dataCategory": 0, "dataSubCategory": 172},  # like a synoptic message
    ],
)
def test_tropical_cyclone_real_message_headers(overrides):
    """Only the messages whose header is (7, 32, 98) are read."""
    n_all = len(read(NEW_LAYOUT))
    assert n_all > 0

    # the header of the real messages is changed with ecCodes before reading them
    with BufrFile(NEW_LAYOUT) as bufr_file:
        messages = list(bufr_file)
        for message in messages:
            for key, value in overrides.items():
                message[key] = value
        df = pdbufr.read_bufr(messages, reader=READER)

    if overrides:
        # they are skipped silently, they give no row
        assert df.empty
        assert list(df.columns) == DEFAULT_COLUMNS
    assert len(df) == (n_all if not overrides else 0)


# ---------------------------------------------------------------------------------------------
# whole files against the independent extraction
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("path", [OLD_LAYOUT, NEW_LAYOUT])
def test_tropical_cyclone_matches_ranked_extraction(path):
    rows = _ranked_rows(path)

    df = read(path, columns="all", keep_missing=True)
    assert list(df.columns) == ALL_COLUMNS
    assert_same(df, _ref(rows, ALL_COLUMNS))

    df = read(path, columns="all")
    assert_same(df, _ref([r for r in rows if _is_valid(r)], ALL_COLUMNS))

    df = read(path)
    assert_same(df, _ref([r for r in rows if _is_valid(r)], DEFAULT_COLUMNS))


# ---------------------------------------------------------------------------------------------
# the risks of the implementation, each checked against ranked ecCodes values
# ---------------------------------------------------------------------------------------------

STEP_COLUMNS = ["lat", "lon", "mslp", "max_wind_lat", "max_wind_lon", "max_wind_speed"]


def test_tropical_cyclone_no_values_leak_between_steps():
    # the old file: steps 18 and 120-198 of 70E member 4 are missing, they are in the middle of
    # the subset or at the end of it
    path = OLD_LAYOUT
    message, subset = 2, 3
    df = read(path, filters={"storm_id": "70E", "member": 4}, keep_missing=True, columns=["step", *STEP_COLUMNS])
    assert df["step"].tolist() == list(range(0, 199, 6))
    df = df.set_index("step")

    # step 18 (i=3) has no centre, no pressure, no max wind. The ranks come from the template
    # and the values of step 12 and 24 are in the neighbouring ranks
    assert _raw(path, message, "#3#timePeriod", subset) == 18
    assert _raw(path, message, "#8#latitude", subset) is None
    assert _raw(path, message, "#8#longitude", subset) is None
    assert _raw(path, message, "#4#pressureReducedToMeanSeaLevel", subset) is None
    assert _raw(path, message, "#9#latitude", subset) is None
    assert _raw(path, message, "#4#windSpeedAt10M", subset) is None
    assert df.loc[18].isna().all()
    # the neighbours have their own values
    assert df.loc[12, "lat"] == _raw(path, message, "#6#latitude", subset)
    assert df.loc[12, "lat"] == pytest.approx(11.7)
    assert df.loc[24, "lat"] == _raw(path, message, "#10#latitude", subset)
    assert df.loc[24, "lat"] == pytest.approx(11.9)
    assert df.loc[12, "max_wind_speed"] == _raw(path, message, "#3#windSpeedAt10M", subset)
    assert df.loc[12, "max_wind_speed"] == pytest.approx(16.5)
    assert df.loc[24, "max_wind_speed"] == _raw(path, message, "#5#windSpeedAt10M", subset)
    assert df.loc[24, "max_wind_speed"] == pytest.approx(16.5)
    assert df.loc[24, "mslp"] == _raw(path, message, "#5#pressureReducedToMeanSeaLevel", subset)

    # the end of the subset has no value either
    assert df.loc[120:].isna().all().all()
    assert df.loc[:114].notna().sum().sum() == 18 * 6 + 6
    assert df.loc[:114, STEP_COLUMNS].isna().sum().sum() == 6

    # all the subsets of the file: a row without a centre has no value in any column
    df = read(path, columns=["storm_id", "member", "step", *STEP_COLUMNS, "observed_lat"], keep_missing=True)
    no_centre = df[df["lat"].isna() | df["lon"].isna()]
    assert len(no_centre) == 5417 - 2721
    assert no_centre[STEP_COLUMNS].isna().all().all()

    # and the ranked extraction says the same for all the rows
    rows = _ranked_rows(path)
    assert len(rows) == len(df)
    for row, (_, rec) in zip(rows, df.iterrows()):
        for c in STEP_COLUMNS:
            assert (row[c] is None) == bool(pd.isna(rec[c])), (row["storm_id"], row["member"], row["step"], c)


def test_tropical_cyclone_no_values_leak_between_steps_new_layout():
    # all the steps of the 3 members of 74E until step 264 have no centre: nothing from the
    # steps with a centre (or from the observed or analysis centres of other messages) must
    # appear in the rows without a centre
    path = NEW_LAYOUT
    df = read(path, filters={"storm_id": "74E"}, columns="all", keep_missing=True)
    assert len(df) == 3 * 61
    first = df[df["member"] == 3].set_index("step")
    assert first.loc[:312, STEP_COLUMNS + RADII_COLUMNS].isna().all().all()
    assert first.loc[318:354, STEP_COLUMNS].notna().all().all()
    # step 360 has no centre again
    assert first.loc[360, STEP_COLUMNS + RADII_COLUMNS].isna().all()
    # the first valid step of the member (i=53)
    assert _raw(path, 1, "#52#timePeriod", 0) == 312
    assert _raw(path, 1, "#53#timePeriod", 0) == 318
    assert _raw(path, 1, "#107#latitude", 0) is None
    assert _raw(path, 1, "#108#latitude", 0) == first.loc[318, "lat"]
    assert first.loc[318, "lat"] == pytest.approx(9.2)
    assert _raw(path, 1, "#54#pressureReducedToMeanSeaLevel", 0) == first.loc[318, "mslp"] == 101100.0


def test_tropical_cyclone_step_0_uses_analysis_centre():
    path = OLD_LAYOUT
    df = read(path, filters={"storm_id": "27W", "step": 0}, columns="all")
    assert len(df) == 52
    assert_same(df.iloc[[0]], DATA.REF_OLD_27W_MEMBER_1_STEP_0)

    # message 1 is storm 27W: the analysis centre (#2, significance 4) is not the observed centre
    # (#1, significance 1)
    for subset, member in ((0, 1), (3, 4), (51, 52)):
        row = df[df["member"] == member].iloc[0]
        assert _raw(path, 1, "#1#meteorologicalAttributeSignificance", subset) == 1
        assert _raw(path, 1, "#2#meteorologicalAttributeSignificance", subset) == 4
        assert _raw(path, 1, "#3#meteorologicalAttributeSignificance", subset) == 3
        assert row["lat"] == _raw(path, 1, "#2#latitude", subset)
        assert row["lon"] == _raw(path, 1, "#2#longitude", subset)
        assert row["observed_lat"] == _raw(path, 1, "#1#latitude", subset)
        assert row["observed_lon"] == _raw(path, 1, "#1#longitude", subset)
        assert (row["lat"], row["lon"]) == pytest.approx((5.4, 156.9))
        assert (row["observed_lat"], row["observed_lon"]) == pytest.approx((5.5, 157.2))
        assert row["max_wind_lat"] == _raw(path, 1, "#3#latitude", subset)
        assert row["max_wind_lon"] == _raw(path, 1, "#3#longitude", subset)
        assert row["mslp"] == _raw(path, 1, "#1#pressureReducedToMeanSeaLevel", subset)
        assert row["max_wind_speed"] == _raw(path, 1, "#1#windSpeedAt10M", subset)
    assert (df["lat"] != df["observed_lat"]).all()
    assert (df["lon"] != df["observed_lon"]).all()

    # the analysis centre is never replaced by the observed one when it is missing
    df = read(
        NEW_LAYOUT,
        filters={"storm_id": "22E"},
        columns=["step", "lat", "lon", "observed_lat", "observed_lon"],
        keep_missing=True,
    )
    assert _raw(NEW_LAYOUT, 3, "#1#latitude", 0) == 20.7
    assert _raw(NEW_LAYOUT, 3, "#2#latitude", 0) is None
    assert _raw(NEW_LAYOUT, 3, "#2#meteorologicalAttributeSignificance", 0) == 5
    assert df["lat"].isna().all() and df["lon"].isna().all()
    assert df["observed_lat"].tolist() == [20.7]
    assert df["observed_lon"].tolist() == [-108.4]

    # the observed centre is on all the rows of the member, the analysis centre only on step 0
    df = read(path, filters={"storm_id": "27W", "member": 1}, columns=["step", "lat", "observed_lat", "observed_lon"])
    assert df["observed_lat"].tolist() == pytest.approx([5.5] * len(df))
    assert df["observed_lon"].tolist() == pytest.approx([157.2] * len(df))
    assert df["lat"].iloc[0] == pytest.approx(5.4)
    assert df["lat"].iloc[1] == _raw(path, 1, "#4#latitude", 0)
    assert df["lat"].iloc[1] != df["observed_lat"].iloc[1]


def test_tropical_cyclone_wind_radii_quadrants():
    path = NEW_LAYOUT
    # 74E member 28 (subset 2) step 270 is the 45th step. All the 12 radii are different enough to
    # tell the wrong thresholds or quadrants
    step_number = 45
    assert _raw(path, 1, f"#{step_number}#timePeriod", 2) == 270
    df = read(path, filters={"storm_id": "74E", "member": 28, "step": 270}, columns=["step", "wind_radii"])
    assert len(df) == 1
    row = df.iloc[0]

    expected = {}
    for k, threshold in enumerate(THRESHOLDS):
        assert _raw(path, 1, f"#{step_number * 3 + k + 1}#windSpeedThreshold", 2) == threshold
        for q, quadrant in enumerate(QUADRANTS):
            rank = (step_number * 3 + k) * 4 + q + 1
            # a quadrant is a start and an end bearing: NE 0-90, SE 90-180, SW 180-270, NW 270-360
            assert _raw(path, 1, f"#{2 * rank - 1}#bearingOrAzimuth", 2) == 90 * q
            assert _raw(path, 1, f"#{2 * rank}#bearingOrAzimuth", 2) in (90 * (q + 1), 90 * (q + 1) % 360)
            expected[f"radius_{threshold}ms_{quadrant}"] = _raw(path, 1, f"#{rank}#{RADIUS_KEY}", 2)

    assert list(row.index) == ["step", *RADII_COLUMNS]
    assert expected == {c: row[c] for c in RADII_COLUMNS}
    assert expected["radius_18ms_ne"] == 88900
    assert expected["radius_18ms_se"] == 55600
    assert expected["radius_18ms_sw"] == 63000
    assert expected["radius_18ms_nw"] == 70400
    assert expected["radius_26ms_ne"] == 40700
    assert expected["radius_26ms_sw"] == 37000
    assert expected["radius_33ms_ne"] == 27800
    assert expected["radius_33ms_sw"] == 29600
    assert len(set(expected.values())) >= 8

    # an uncompressed message, 71W step 264 (the 44th)
    step_number = 44
    assert _raw(path, 2, f"#{step_number}#timePeriod", 0) == 264
    df = read(path, filters={"storm_id": "71W", "step": 264}, columns="wind_radii")
    for k, threshold in enumerate(THRESHOLDS):
        for q, quadrant in enumerate(QUADRANTS):
            rank = (step_number * 3 + k) * 4 + q + 1
            assert df[f"radius_{threshold}ms_{quadrant}"].tolist() == [_raw(path, 2, f"#{rank}#{RADIUS_KEY}", 0)]
    assert df["radius_18ms_ne"].tolist() == [931600]
    assert df["radius_26ms_ne"].tolist() == [816700]


@pytest.mark.parametrize(
    "path,message,step,key_ranks",
    [
        # old layout, 70E: step 12 is the 2nd step, step 60 the 10th
        (OLD_LAYOUT, 2, 12, 2),
        (OLD_LAYOUT, 2, 60, 10),
        # new layout, 74E: step 354 is the 59th step
        (NEW_LAYOUT, 1, 354, 59),
    ],
)
def test_tropical_cyclone_compressed_members_are_not_shifted(path, message, step, key_ranks):
    i = key_ranks
    assert _raw(path, message, f"#{i}#timePeriod", 0) == step

    df = read(path, filters={"step": step, "count": message}, columns=["storm_id", "member", "step", *STEP_COLUMNS])
    members = _members(path, message)
    assert len(members) > 1
    df = df.set_index("member")

    n_rows = 0
    lats = []
    for subset, member in enumerate(members):
        lat = _raw(path, message, f"#{2 * i + 2}#latitude", subset)
        if lat is None:
            # the members without a centre at this step have no row
            assert member not in df.index
            continue
        n_rows += 1
        lats.append(lat)
        row = df.loc[member]
        assert row["lat"] == lat
        assert row["lon"] == _raw(path, message, f"#{2 * i + 2}#longitude", subset)
        assert row["max_wind_lat"] == _raw(path, message, f"#{2 * i + 3}#latitude", subset)
        assert row["max_wind_lon"] == _raw(path, message, f"#{2 * i + 3}#longitude", subset)
        assert row["mslp"] == _raw(path, message, f"#{i + 1}#pressureReducedToMeanSeaLevel", subset)
        assert row["max_wind_speed"] == _raw(path, message, f"#{i + 1}#windSpeedAt10M", subset)
    assert len(df) == n_rows > 1
    # the members have different values, so a shift of the subsets would be seen
    assert len(set(lats)) > 1


def _members(path, message):
    for number, msg in _messages(path):
        if number == message:
            return [msg.get("#1#ensembleMemberNumber", s) for s in range(msg.number_of_subsets)]
    raise AssertionError(message)


def test_tropical_cyclone_compressed_members_values():
    # two different members of a compressed message, with the values taken from their own subset
    path = OLD_LAYOUT
    df = read(path, filters={"storm_id": "70E", "member": [1, 4], "step": 12}, columns=["member", *STEP_COLUMNS])
    assert df["member"].tolist() == [1, 4]
    assert df["lat"].tolist() == [_raw(path, 2, "#6#latitude", 0), _raw(path, 2, "#6#latitude", 3)]
    assert df["lat"].iloc[0] == pytest.approx(11.3)
    assert df["lat"].iloc[1] == pytest.approx(11.7)
    assert df["mslp"].tolist() == [_raw(path, 2, "#3#pressureReducedToMeanSeaLevel", s) for s in (0, 3)]

    path = NEW_LAYOUT
    df = read(
        path, filters={"storm_id": "74E", "member": [3, 23, 28], "step": 354}, columns=["member", "lat", "lon", "mslp"]
    )
    assert df["member"].tolist() == [3, 23, 28]
    assert df["lat"].tolist() == pytest.approx([6.5, 21.4, 12.4])
    assert df["lon"].tolist() == pytest.approx([-140.4, -128.0, -101.7])
    assert df["mslp"].tolist() == [101000.0, 100300.0, 97600.0]
    for subset in range(3):
        assert df["lat"].iloc[subset] == _raw(path, 1, "#120#latitude", subset)
        assert df["lon"].iloc[subset] == _raw(path, 1, "#120#longitude", subset)
        assert df["mslp"].iloc[subset] == _raw(path, 1, "#60#pressureReducedToMeanSeaLevel", subset)
