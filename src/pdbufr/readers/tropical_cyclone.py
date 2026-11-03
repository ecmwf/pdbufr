# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""Reader for the ECMWF tropical cyclone track BUFR data.

The supported input is the ECMWF tropical cyclone track BUFR data, i.e. the messages with
``dataCategory`` 7, ``dataSubCategory`` 32 and ``bufrHeaderCentre`` 98 (see ``DATA_CATEGORY``,
``DATA_SUB_CATEGORY`` and ``BUFR_HEADER_CENTRE``). The other messages of a file are silently
skipped, without unpacking their data section, so a file with other data can be passed too.

Each supported BUFR message describes one storm and each subset of the message one ensemble
member. The subset contains the analysis followed by a number of forecast steps, which are turned
into one row per storm, member and step.
"""

import datetime
import itertools
import logging
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union

import pandas as pd  # type: ignore

import pdbufr.core.param as PARAMS
from pdbufr.core.filters import BufrFilter
from pdbufr.core.structure import MessageWrapper, filter_keys_cached
from pdbufr.core.subset import BufrSubsetCollector, BufrSubsetReader

from .custom import CustomReader

LOG = logging.getLogger(__name__)

# the header values of the supported messages: the ECMWF tropical cyclone track data
DATA_CATEGORY = 7
DATA_SUB_CATEGORY = 32
BUFR_HEADER_CENTRE = 98  # ECMWF

DEFAULT_COLUMNS: List[str] = [
    "storm_id",
    "storm_name",
    "member",
    "base_time",
    "step",
    "valid_time",
    "lat",
    "lon",
    "mslp",
    "max_wind_lat",
    "max_wind_lon",
    "max_wind_speed",
]
RADII_COLUMNS: List[str] = list(PARAMS.WIND_RADII)
EXTRA_COLUMNS: List[str] = ["observed_lat", "observed_lon", "forecast_type"]
ALL_COLUMNS: List[str] = DEFAULT_COLUMNS + RADII_COLUMNS + EXTRA_COLUMNS

COLUMN_GROUPS: Dict[str, List[str]] = {
    "default": DEFAULT_COLUMNS,
    "wind_radii": RADII_COLUMNS,
    "all": ALL_COLUMNS,
}

# filters on these columns are evaluated on the storm, on the ensemble member or on each row
STORM_COLUMNS = ("storm_id", "storm_name", "base_time")
MEMBER_COLUMNS = ("member", "forecast_type", "observed_lat", "observed_lon")

# hints for the users filtering on a BUFR key name
BUFR_KEY_COLUMNS: Dict[str, str] = {
    "stormIdentifier": "storm_id",
    "longStormName": "storm_name",
    "ensembleMemberNumber": "member",
    "ensembleForecastType": "forecast_type",
    "timePeriod": "step",
}

# header keys in each subset
HEADER_KEYS = (
    "stormIdentifier",
    "longStormName",
    "ensembleMemberNumber",
    "ensembleForecastType",
    "year",
    "month",
    "day",
    "hour",
    "minute",
)

RADIUS_KEY = "effectiveRadiusWithRespectToWindSpeedsAboveThreshold"
RADII_KEYS = ("windSpeedThreshold", "bearingOrAzimuth", RADIUS_KEY)

# the keys always needed to build the rows
BASE_KEYS = (
    *HEADER_KEYS,
    "subsetNumber",
    "timePeriod",
    "meteorologicalAttributeSignificance",
    "latitude",
    "longitude",
    "pressureReducedToMeanSeaLevel",
    "windSpeedAt10M",
)

# meteorologicalAttributeSignificance values
SIGNIFICANCE_OBSERVED = 1
SIGNIFICANCE_MAX_WIND = 3
SIGNIFICANCE_GROUPS = {1: "centre", 3: "max_wind", 4: "centre", 5: "centre"}

# the start bearing of the quadrants
QUADRANTS = ("ne", "se", "sw", "nw")
QUADRANT_BY_BEARING = {0: "ne", 90: "se", 180: "sw", 270: "nw"}

# the BUFR key giving the units of a column
UNITS_KEYS: Dict[str, str] = {
    "lat": "latitude",
    "lon": "longitude",
    "observed_lat": "latitude",
    "observed_lon": "longitude",
    "max_wind_lat": "latitude",
    "max_wind_lon": "longitude",
    "mslp": "pressureReducedToMeanSeaLevel",
    "max_wind_speed": "windSpeedAt10M",
    **{c: RADIUS_KEY for c in RADII_COLUMNS},
}

ROW_COLUMNS = ["lat", "lon", "mslp", "max_wind_lat", "max_wind_lon", "max_wind_speed", *RADII_COLUMNS]
INT_COLUMNS = ("member", "step", "forecast_type")
FLOAT_COLUMNS = [c for c in ALL_COLUMNS if c in PARAMS.UNITS]
DATETIME_COLUMNS = ("base_time", "valid_time")


def _new_row(step: Optional[int]) -> Dict[str, Any]:
    row: Dict[str, Any] = dict.fromkeys(ROW_COLUMNS)
    row["step"] = step
    return row


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class TropicalCycloneReader(CustomReader):
    """Read ECMWF tropical cyclone track BUFR data.

    Only the messages with ``dataCategory`` 7, ``dataSubCategory`` 32 and ``bufrHeaderCentre`` 98
    are read, the other messages of the input are silently skipped before their data section is
    unpacked.

    The result has one row per storm, ensemble member and forecast step. Step 0 is the analysis.

    Parameters
    ----------
    columns : str or list of str
        The columns to extract. It can be "default", "wind_radii", "all" or the name of a column,
        or a list of these. An empty list means "default". The output columns are always in the
        same order, regardless of the order in ``columns``.

        The default columns are: ``storm_id``, ``storm_name``, ``member``, ``base_time``, ``step``
        (hours), ``valid_time``, ``lat``, ``lon``, ``mslp``, ``max_wind_lat``, ``max_wind_lon``,
        ``max_wind_speed``. The "wind_radii" group has the ``radius_<18|26|33>ms_<ne|se|sw|nw>``
        columns. The other columns are ``observed_lat``, ``observed_lon`` and ``forecast_type``.
    filters : dict
        Filters on the column names (selected or not) and on ``count``, the 1-based index of the
        message. The filters match the values as they appear in the output, i.e. after the units
        conversion. Filters on ``storm_id``, ``storm_name`` and ``base_time`` select storms,
        filters on ``member``, ``forecast_type``, ``observed_lat`` and ``observed_lon`` select
        ensemble members, all the other filters select rows.
    keep_missing : bool
        When False, the rows with a missing ``lat`` or ``lon`` are dropped.
    unit_system : str, optional
        The unit system of the values: "pdbufr" or "si".
    units : dict, optional
        The target units per column.
    units_columns : bool
        When True, a ``<column>_units`` column is added after each column that has units.
    """

    def __init__(
        self,
        *args: Any,
        columns: Optional[Union[str, List[str]]] = "default",
        keep_missing: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.columns = self.parse_columns(columns)
        self.keep_missing = keep_missing
        self.check_filters(self.bufr_filters)

        self.needed_columns = set(self.columns) | set(self.bufr_filters)
        self.unit_columns = [c for c in ALL_COLUMNS if c in self.needed_columns and c in PARAMS.UNITS]
        self.use_units = self.units_converter is not None or self.add_units

        self.bufr_keys = list(BASE_KEYS)
        if self.needed_columns.intersection(RADII_COLUMNS):
            self.bufr_keys.extend(RADII_KEYS)

        self._keys_cache: Dict[Any, Any] = {}
        self._target_units_cache: Dict[Tuple[str, str], Optional[str]] = {}

    @staticmethod
    def parse_columns(columns: Optional[Union[str, Iterable[str]]]) -> List[str]:
        """Convert the user ``columns`` to the list of the output columns in the output order."""
        if columns is None:
            columns = []
        elif isinstance(columns, str):
            columns = [columns]
        columns = list(columns) or ["default"]

        valid = [*COLUMN_GROUPS, *ALL_COLUMNS]
        selected = set()
        for c in columns:
            if not isinstance(c, str) or c not in valid:
                raise ValueError(f"Invalid tropical cyclone column {c!r}. Valid names are: {valid}")
            selected.update(COLUMN_GROUPS.get(c, [c]))

        return [c for c in ALL_COLUMNS if c in selected]

    @staticmethod
    def check_filters(filters: Dict[str, BufrFilter]) -> None:
        for key in filters:
            if key not in ALL_COLUMNS:
                hint = ""
                if key in BUFR_KEY_COLUMNS:
                    hint = f" Did you mean {BUFR_KEY_COLUMNS[key]!r}?"
                raise ValueError(
                    f"Invalid filter key {key!r} for the tropical cyclone reader.{hint} "
                    f"Valid keys are: {ALL_COLUMNS + ['count']}"
                )

    def filter_header(self, message: MessageWrapper) -> bool:
        """Check that the message is ECMWF tropical cyclone track data.

        It only reads header keys, so it can be called before the data section is unpacked. A
        message that does not match is silently skipped.
        """
        return (
            message["dataCategory"] == DATA_CATEGORY
            and message["dataSubCategory"] == DATA_SUB_CATEGORY
            and message["bufrHeaderCentre"] == BUFR_HEADER_CENTRE
        )

    def read_message(
        self,
        message: MessageWrapper,
        bufr_filters: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        if bufr_filters is None:
            bufr_filters = self.bufr_filters

        storm_filters = {k: v for k, v in bufr_filters.items() if k in STORM_COLUMNS}
        member_filters = {k: v for k, v in bufr_filters.items() if k in MEMBER_COLUMNS}
        row_filters = {k: v for k, v in bufr_filters.items() if k not in STORM_COLUMNS and k not in MEMBER_COLUMNS}

        filtered_keys = filter_keys_cached(message, self._keys_cache, self.bufr_keys)
        if not any(k.name == "stormIdentifier" for k in filtered_keys):
            LOG.debug("Skipping message without stormIdentifier")
            return

        source_units = self.get_source_units(message, filtered_keys)

        reader = BufrSubsetReader(message, filtered_keys)
        for subset in reader.subsets():
            yield from self.read_subset(subset, source_units, storm_filters, member_filters, row_filters)

    def get_source_units(self, message: MessageWrapper, filtered_keys: List[Any]) -> Dict[str, Optional[str]]:
        """Get the units of the unit columns as given in the message."""
        if not self.use_units:
            return {}

        keys: Dict[str, str] = {}
        for bufr_key in filtered_keys:
            keys.setdefault(bufr_key.name, bufr_key.key)

        units: Dict[str, Optional[str]] = {}
        for column in self.unit_columns:
            key = keys.get(UNITS_KEYS[column])
            units[column] = message.get(key + "->units") if key else None
        return units

    def convert_units(self, column: str, value: Any, units: Optional[str]) -> Tuple[Any, Optional[str]]:
        """Convert a value to the target units of the column."""
        if self.units_converter is None or units is None:
            return value, units

        if value is None:
            # the target units are needed even when there is no value to convert
            key = (column, units)
            if key not in self._target_units_cache:
                self._target_units_cache[key] = self.units_converter.convert(column, 1.0, units)[1]
            return None, self._target_units_cache[key]

        return self.units_converter.convert(column, value, units)

    @staticmethod
    def match(filters: Dict[str, BufrFilter], record: Dict[str, Any]) -> bool:
        return all(f.match(record[column]) for column, f in filters.items())

    @staticmethod
    def make_storm(header: Dict[str, Any]) -> Dict[str, Any]:
        """Build the storm and member level columns from the header of a subset."""

        def _str(v: Any) -> Optional[str]:
            return None if v is None else str(v).strip()

        base_time = None
        try:
            base_time = datetime.datetime(
                header["year"],
                header["month"],
                header["day"],
                header.get("hour") or 0,
                header.get("minute") or 0,
            )
        except (KeyError, TypeError, ValueError):
            pass

        return {
            "storm_id": _str(header.get("stormIdentifier")),
            "storm_name": _str(header.get("longStormName")),
            "member": _to_int(header.get("ensembleMemberNumber")),
            "base_time": base_time,
            "forecast_type": _to_int(header.get("ensembleForecastType")),
        }

    @staticmethod
    def walk_subset(
        items: Iterable[Tuple[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Collect the rows and the observed centre of a subset from its keys.

        The keys are in this order: the analysis (the observed centre, the analysis centre with the
        pressure, the analysis maximum wind and the wind radii) and then for each step the
        ``timePeriod``, the centre with the pressure, the maximum wind and the wind radii. The
        groups are told apart by ``meteorologicalAttributeSignificance``.

        Returns
        -------
        tuple
            The rows (the first row is the analysis) and the observed ``lat`` and ``lon``.
        """
        analysis = _new_row(0)
        rows = [analysis]
        row = analysis
        observed: Dict[str, Any] = {"lat": None, "lon": None}
        in_steps = False
        group = None

        threshold = None
        bearing_count = 0
        bearing_start = None
        radius_count = 0

        for name, value in items:
            if name == "meteorologicalAttributeSignificance":
                group = SIGNIFICANCE_GROUPS.get(value)
                if value == SIGNIFICANCE_OBSERVED and not in_steps:
                    group = "observed"
            elif name == "timePeriod":
                row = _new_row(_to_int(value))
                rows.append(row)
                in_steps = True
                group = None
            elif name in ("latitude", "longitude"):
                coord = name[:3]
                if group == "observed":
                    observed[coord] = value
                elif group == "centre":
                    row[coord] = value
                elif group == "max_wind":
                    row["max_wind_" + coord] = value
            elif name == "pressureReducedToMeanSeaLevel":
                if group == "centre":
                    row["mslp"] = value
            elif name == "windSpeedAt10M":
                if group == "max_wind":
                    row["max_wind_speed"] = value
            elif name == "windSpeedThreshold":
                threshold = _to_int(value)
                bearing_count = 0
                bearing_start = None
                radius_count = 0
            elif name == "bearingOrAzimuth":
                # the bearings come in start, end pairs
                if bearing_count % 2 == 0:
                    bearing_start = value
                bearing_count += 1
            elif name == RADIUS_KEY:
                quadrant = QUADRANT_BY_BEARING.get(bearing_start)
                if quadrant is None and radius_count < len(QUADRANTS):
                    quadrant = QUADRANTS[radius_count]
                radius_count += 1
                column = f"radius_{threshold}ms_{quadrant}"
                if column in PARAMS.WIND_RADII:
                    row[column] = value

        return rows, observed

    def read_subset(
        self,
        subset: BufrSubsetCollector,
        source_units: Dict[str, Optional[str]],
        storm_filters: Dict[str, BufrFilter],
        member_filters: Dict[str, BufrFilter],
        row_filters: Dict[str, BufrFilter],
    ) -> Generator[Dict[str, Any], None, None]:
        items = subset.iter_values()

        # the header comes first. The values are read lazily, so a subset that does not match the
        # storm or member filters is dropped without reading the rest of its keys
        header: Dict[str, Any] = {}
        pending: List[Tuple[str, Any]] = []
        for name, value in items:
            if name in HEADER_KEYS:
                header.setdefault(name, value)
            elif name != "subsetNumber":
                pending.append((name, value))
                break

        storm = self.make_storm(header)
        if not self.match(storm_filters, storm):
            return
        if not self.match({k: v for k, v in member_filters.items() if k in storm}, storm):
            return

        rows, observed = self.walk_subset(itertools.chain(pending, items))

        # the observed centre is the same on all the rows
        units: Dict[str, Optional[str]] = {}
        storm["observed_lat"] = observed["lat"]
        storm["observed_lon"] = observed["lon"]
        for column in ("observed_lat", "observed_lon"):
            if column in self.unit_columns:
                storm[column], units[column] = self.convert_units(column, storm[column], source_units.get(column))
        if not self.match({k: v for k, v in member_filters.items() if k.startswith("observed_")}, storm):
            return

        base_time = storm["base_time"]
        for row in rows:
            if not self.keep_missing and (row["lat"] is None or row["lon"] is None):
                continue

            record = {**storm, **row}
            step = row["step"]
            record["valid_time"] = (
                base_time + datetime.timedelta(hours=step) if base_time and step is not None else None
            )

            for column in self.unit_columns:
                if column not in storm:
                    record[column], units[column] = self.convert_units(column, record[column], source_units.get(column))

            if row_filters and not self.match(row_filters, record):
                continue

            result: Dict[str, Any] = {}
            for column in self.columns:
                result[column] = record[column]
                if self.add_units and column in PARAMS.UNITS:
                    result[column + "_units"] = units.get(column)
            yield result

    def adjust_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            columns = []
            for column in self.columns:
                columns.append(column)
                if self.add_units and column in PARAMS.UNITS:
                    columns.append(column + "_units")
            df = pd.DataFrame(columns=columns)

        for column in df.columns:
            if column in DATETIME_COLUMNS:
                df[column] = pd.to_datetime(df[column])
            elif column in FLOAT_COLUMNS:
                df[column] = df[column].astype("float64")
            elif column in INT_COLUMNS:
                # a nullable integer is only needed when there are missing values
                df[column] = df[column].astype("Int64" if df[column].isna().any() else "int64")
        return df


reader = TropicalCycloneReader
