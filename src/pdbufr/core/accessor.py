# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
import re
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional, Union

import pdbufr.core.param as PARAMS
from pdbufr.core.keys import COMPUTED_KEYS
from pdbufr.core.structure import pair_key_name
from pdbufr.utils.exception import AllValueMissingException

LOG = logging.getLogger(__name__)


class Accessor(metaclass=ABCMeta):
    keys: Optional[Dict[str, Any]] = None
    param: Optional[Any] = None
    mandatory: Optional[List[str]] = None
    dtype = None

    def __init__(self, keys: Optional[Union[Dict[str, Any], str, List[str]]] = None, dtype: Optional[Any] = None):
        """
        Accessor class to extract values from a BUFR message.

        Parameters
        ----------
        keys : dict, str, list of str, optional
            Mapping between the keys to extract and the corresponding Parameters. When None, the
            static ``keys`` member is used. When not a dict, it is converted to a dict with the
            same key(s) and value(s).
        """
        if keys is None:
            self.keys = self.keys
            if self.keys:
                self.keys = {**self.keys}
            else:
                self.keys = {}
        else:
            self.keys = keys

        assert isinstance(self.keys, dict)

        if self.param is None:
            if len(self.keys) == 1:
                self.param = list(self.keys.values())[0]

        # LOG.debug(f"Accessor {self.__class__.__name__} initialized with keys: {self.keys}")

        self.bufr_keys = list([k for k in self.keys.keys() if not k.startswith("_")])
        self.labels = [v.label for k, v in self.keys.items() if v is not None]
        self.name = self.__class__.__name__

        self.dtype = dtype

        # LOG.debug(f"Accessor {self.name} initialized with labels: {self.labels}")

    @abstractmethod
    def empty_result(self) -> Any:
        pass

    @property
    @abstractmethod
    def needed_keys(self) -> List[str]:
        pass

    @abstractmethod
    def collect(self, collector: Any, **kwargs: Any) -> Any:
        pass


class SimpleAccessor(Accessor):
    def empty_result(self) -> Dict[str, Optional[Any]]:
        return dict(zip(self.labels, [None] * len(self.labels)))

    @property
    def needed_keys(self) -> List[str]:
        return self.bufr_keys

    def collect(
        self,
        collector: Any,
        raise_on_missing: bool = False,
        units_converter: Optional[Any] = None,
        add_units: bool = False,
        **kwargs: Any,
    ) -> Any:
        return self.collect_any(
            collector,
            raise_on_missing=raise_on_missing,
            units_converter=units_converter,
            add_units=add_units,
            **kwargs,
        )

    def parse_collected(
        self,
        value: Optional[Dict[str, Any]],
        skip: List[Any],
        units_converter: Optional[Any],
        add_units: bool,
        raise_on_missing: bool,
    ) -> Dict[str, Any]:
        if value is None:
            value = {}

        if raise_on_missing and (not value or all(v is None for v in value.values())):
            raise AllValueMissingException(f"No value found for accessor={self.name}")

        res = {}
        for key, param in self.keys.items():
            if param is not None:
                if param.is_fixed():
                    res[param.label] = param.value
                else:
                    label = param.label
                    if param in skip:
                        continue

                    v, units = value.get(key, (None, None))

                    # convert units
                    if v is not None and units_converter is not None and param.units:
                        v, units = units_converter.convert(label, v, units)

                    # handle period
                    if param.is_period():
                        # keep a present-but-MISSING displacement as a (None,
                        # units) tuple so that a start/end pair with a missing
                        # element can be told apart from a single displacement
                        v = param.parse(v, units, present=key in value)
                    elif v is not None and self.dtype is not None and self.param and self.param.label == label:
                        try:
                            v = self.dtype(v)
                        except Exception:
                            pass

                    res[label] = v

                    # add units column
                    if add_units and param.units:
                        res[label + "_units"] = units

        return res

    def collect_any(
        self,
        collector: Any,
        mandatory: Optional[List[str]] = None,
        skip: Optional[List[Any]] = None,
        raise_on_missing: bool = False,
        units_keys: Optional[List[str]] = None,
        units_converter: Optional[Any] = None,
        add_units: bool = False,
        first: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        pair_keys: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        value = None
        mandatory = mandatory or []
        skip = skip or []

        units_keys = units_keys or []
        if units_converter is not None or add_units:
            units_keys.extend(self.bufr_keys)

        multi_res = []

        if filters is None:
            filters = {}

        for v in collector.collect(
            self.bufr_keys, filters, mandatory_keys=mandatory, units_keys=units_keys, pair_keys=pair_keys
        ):
            value = v
            res = self.parse_collected(value, skip, units_converter, add_units, raise_on_missing)
            if first:
                return res
            else:
                multi_res.append(res)

        if first:
            if raise_on_missing:
                raise AllValueMissingException(f"No value found for accessor={self.name}")
            return {}
        else:
            return multi_res


class ComputedKeyAccessor(Accessor):
    def __init__(self, *args: Any, method_kwargs=None, **kwargs: Any):
        super().__init__(*args, **kwargs)

        key = list(self.keys.keys())[0]
        assert isinstance(key, str)
        for ck in COMPUTED_KEYS.values():
            if ck.column_name == key:
                self._meth = ck.compute_method
                self._keys = ck.bufr_keys
                break

        if not hasattr(self, "_meth"):
            raise ValueError(f"Unknown computed key {self.keys[0]}")

        self.method_kwargs = method_kwargs or {}

    def empty_result(self) -> Dict[str, Optional[Any]]:
        return dict(zip(self.labels, [None] * len(self.labels)))

    @property
    def needed_keys(self) -> List[str]:
        return self._keys

    def collect(self, collector: Any, raise_on_missing: bool = False, **kwargs: Any) -> Dict[str, Any]:
        value = None
        for v in collector.collect(self._keys, {}, value_and_units=False):
            value = v
            break

        try:
            val = self._meth(value, "", self._keys, **self.method_kwargs)
        except Exception:
            if raise_on_missing:
                raise
            val = None

        if val is not None and self.dtype is not None:
            try:
                val = self.dtype(val)
            except Exception:
                pass

        if val is None and raise_on_missing:
            raise AllValueMissingException(f"Missing value for {self.name}")

        return {self.labels[0]: val}


#: column suffixes that only make together with the identically named value column
DERIVED_SUFFIXES = ("_level", "_units")


def candidate_rank(
    value: Optional[Any],
    height: Optional[Any],
    nominal_height: Optional[float] = None,
    min_height: Optional[float] = None,
) -> tuple:
    """Rank one candidate of a colliding (label, period) column; the lowest rank wins.

    The rank is a tuple compared lexicographically:

    * first tier: a real (non-None) value ranks before a missing one. A missing
      value never wins a collision (A3).
    * second tier (only with *nominal_height*): 0 for a sensor height, 1 for no
      height at all, so a value without a height ranks after any value with one.
    * third tier (only with *nominal_height*): the distance to the nominal height,
      so the sensor closest to the nominal height of the parameter wins.

    Without *nominal_height* only the first tier exists, i.e. parameters keep
    their current rule except that missing never beats real. Sensors below
    *min_height* are not ranked here: :meth:`CoordAccessor.relabel` removes them
    from the candidates first (see :func:`is_ground_sensor`); as a safeguard
    they rank after every other candidate.
    """
    has_value = 0 if value is not None else 1
    if nominal_height is None:
        return (has_value,)
    h = _as_height(height)
    if h is None:
        return (has_value, 1, 0.0)
    if min_height is not None and h < min_height:
        return (1, 2, 0.0)
    return (has_value, 0, abs(h - nominal_height))


def _as_height(height: Optional[Any]) -> Optional[float]:
    """The sensor height as a float, or None when it is missing or not a number."""
    if height is None:
        return None
    try:
        return float(height)
    except (TypeError, ValueError):
        return None


def is_ground_sensor(height: Optional[Any], min_height: Optional[float]) -> bool:
    """True when *height* is a valid sensor height below *min_height*.

    Such a sensor (e.g. a ground or grass minimum thermometer at 0.05 m) is not a
    candidate for a parameter with a minimum height, such as the 2 m temperature
    extremes (D2). Without *min_height*, or without a valid height, it is False.
    """
    if min_height is None:
        return False
    h = _as_height(height)
    return h is not None and h < min_height


def _derived_stem(key: str):
    """Split a ``_level``/``_units`` column name into (value column, suffix).

    Returns (None, None) for a value column name.
    """
    for suffix in DERIVED_SUFFIXES:
        if key.endswith(suffix):
            return key[: -len(suffix)], suffix
    return None, None


def merge_period_results(base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two accessor results so that a missing value never overwrites a real one.

    For every value column of *new*: when *base* already has a non-None value and
    *new* only has a missing one, *base* (with its ``_level``/``_units`` columns)
    is kept; otherwise *new* wins and its ``_level``/``_units`` columns replace
    those of *base* (stale derived columns without a new value are dropped). A
    ``_level``/``_units`` column of *new* without its value column is never
    merged, so no phantom derived column can appear. The column order of *new*
    is preserved. *base* is modified and returned.
    """
    winners = {
        key: not (key in base and base[key] is not None and v is None)
        for key, v in new.items()
        if _derived_stem(key)[0] is None
    }
    for key, v in new.items():
        stem, _ = _derived_stem(key)
        if stem is None:
            if winners[key]:
                base[key] = v
        elif stem in winners and winners[stem]:
            base[key] = v
    for key, won in winners.items():
        if won:
            for suffix in DERIVED_SUFFIXES:
                if key + suffix not in new:
                    base.pop(key + suffix, None)
    return base


class CoordAccessor(SimpleAccessor):
    def __init__(
        self,
        coords: Optional[List[Any]] = None,
        fixed_coords: Optional[Any] = None,
        period: Optional[str] = None,
        fixed_period: Optional[Any] = None,
        first: bool = True,
        nominal_height: Optional[float] = None,
        min_height: Optional[float] = None,
        missing_last: bool = False,
        **kwargs: Any,
    ):
        """Accessor of value columns optionally named by a period.

        The value columns of records with a period are suffixed ``_<period>``
        (resolved later to e.g. ``max_t2m_12h``). When several records collide
        on the same (label, period) column the winner is selected with the
        opt-in rules below (see :func:`candidate_rank`); the default keeps the
        previous last-record-wins behaviour.

        Parameters (collision selection, opt-in; see :func:`candidate_rank`)
        ---------------------------------------------------------------
        nominal_height : float, optional
            When set, records colliding on the same (label, period) column are
            selected by sensor height: the height closest to this nominal height
            of the parameter wins; a record without a height ranks after any
            eligible height. Also enables the missing-value rule below.
        min_height : float, optional
            Sensor heights below this value (ground sensors) are not
            candidates: such a record counts as a missing value without a
            height, so it never wins against nor hides another reading.
        missing_last : bool
            A missing (None) value never overwrites a real one when records of
            this accessor collide on the same (label, period) column. Default
            False keeps the previous last-record-wins behaviour.
        """
        self.nominal_height = nominal_height
        self.min_height = min_height
        self.missing_last = missing_last

        super().__init__(**kwargs)

        self.mandatory = [*self.bufr_keys]
        self.key_labels = [*self.labels]
        self.first = first

        # period coords
        self.period_bufr_key = None
        self.period_pair_bufr_key = None
        self.period = None
        self.period_pair = None
        #: True when the period is read from a BUFR key (as opposed to fixed or absent)
        self.dynamic_period = False

        if fixed_period and period:
            raise ValueError("Cannot have both fixed_period and period")

        if period:
            self.period_bufr_key = period
            self.period = PARAMS.PeriodParameter("_period")
            self.keys[period] = self.period
            # the second occurrence of a consecutive pair of period keys (WMO
            # start/end displacements) is collected under this paired key name
            self.period_pair_bufr_key = pair_key_name(period)
            self.period_pair = PARAMS.PeriodParameter("_period_pair")
            self.keys[self.period_pair_bufr_key] = self.period_pair
            # period precedes the param keys in the message
            self.bufr_keys = [period, *self.bufr_keys]
            self.mandatory.append(period)
            self.dynamic_period = True
        elif fixed_period:
            self.period = PARAMS.FixedParameter("_period", fixed_period)

        # other coords
        if fixed_coords and coords:
            raise ValueError("Cannot have both fixed_coords and coords")

        self.coords = {}
        self.extract_coords = []

        if coords:
            for c in coords:
                coord_bufr_key = c[0]
                coord_suffix = c[1]
                coord_mandatory = c[2]

                c = PARAMS.CoordParameter(coord_bufr_key, suffix=coord_suffix)
                self.coords[coord_bufr_key] = c
                self.keys[coord_bufr_key] = c
                # coords precedes the param keys in the message
                self.bufr_keys = [coord_bufr_key, *self.bufr_keys]
                if coord_mandatory:
                    self.mandatory.append(coord_bufr_key)

            self.extract_coords = list(self.coords.values())

        elif fixed_coords:
            coord_suffix = "level"
            c = PARAMS.FixedCoordParameter("_fixed_coords", fixed_coords, suffix=coord_suffix)
            self.coords["_fixed_coords"] = c

    def get_period(self, record: Dict[str, Any]) -> Optional[str]:
        """The period string of the record, or None when the period is missing.

        The (already parsed) ``_period``/``_period_pair`` entries are removed from
        the record. A pair of consecutive period values is named by its duration,
        with an ``_lagNh`` suffix when the period does not end at the observation
        time: it is shifted back and ends N before it. A complete pair with equal
        value and units repeats a single displacement: the second element is
        dropped and the period is named by that displacement, so ``-24 h, -24 h``
        gives "24h". A pair with a missing element (a present-but-MISSING
        ``(None, units)`` slot) is a missing period (D3): the known half never
        names the column.
        A missing period yields None (never "nan").
        """
        if self.period:
            if self.period.is_fixed():
                return self.period.value
            start = record.pop("_period", None)
            end = record.pop("_period_pair", None)
            return self.period.format(start, end)
        return None

    def get_coords(
        self, period: str, coord_values: Dict[Any, Any], present: Optional[set] = None
    ) -> Optional[Dict[str, Any]]:
        """The ``_<suffix>`` columns of one record, from its already extracted coord values."""
        if self.coords:
            coords = {}
            if self.extract_coords:
                for coord, v in coord_values.items():
                    for key in self.key_labels:
                        if present is not None and key not in present:
                            continue
                        label = key + period + "_" + coord.suffix
                        coords[label] = v
            else:
                for key in self.key_labels:
                    if present is not None and key not in present:
                        continue
                    for coord in self.coords.values():
                        label = key + period + "_" + coord.suffix
                        coords[label] = coord.value

            return coords
        return None

    def get_units(self, record: Dict[str, Any], period: str, present: Optional[set] = None) -> Dict[str, Any]:
        units = {}
        for key in self.key_labels:
            label = key + "_units"
            if label in record:
                v = record.pop(label, None)
                if present is not None and key not in present:
                    continue
                label = key + period + "_units"
                units[label] = v
        return units

    def relabel(
        self, value: Union[Dict[str, Any], List[Dict[str, Any]]], add_coord: bool, add_units: bool
    ) -> Dict[str, Any]:
        if isinstance(value, dict):
            if not value:
                # collect_any(first=True, raise_on_missing=False) found no record at
                # all: emit nothing, in particular no _level/_units without a value
                return {}
            value = [value]

        rank_collisions = self.missing_last or self.nominal_height is not None

        res = {}
        ranks: Dict[str, tuple] = {}
        for r in value:
            # LOG.debug(f"CoordAccessor: relabeling record: {r}")
            period = self.get_period(r)
            coords = None
            units = None

            # The sensor height decides which record wins a label+period collision
            # (D2), so it is extracted also when the _level columns are not asked
            # for; when they are, get_coords formats the same values.
            coord_values = {coord: r.pop(coord.label, None) for coord in self.extract_coords}
            height = next((v for v in coord_values.values() if v is not None), None)
            if height is None and not self.extract_coords:
                for coord in self.coords.values():
                    if coord.value is not None:
                        height = coord.value
                        break

            # A sensor below min_height (a ground sensor) is not a candidate (D2):
            # the record is kept only as a missing value without a height, so it
            # can neither win against nor hide a reading at an eligible height.
            if is_ground_sensor(height, self.min_height):
                for k in self.key_labels:
                    if k in r:
                        r[k] = None
                    if k + "_units" in r:
                        r[k + "_units"] = None
                coord_values = dict.fromkeys(coord_values)
                height = None

            # A missing dynamic period is never named "nan": a label that has a
            # value uses the plain name, a label without one emits no columns at
            # all (also no _level/_units for it).
            if period is None and self.dynamic_period:
                present = {k for k in self.key_labels if r.get(k) is not None}
            else:
                present = set(self.key_labels)

            if period is not None:
                period = "_<" + period + ">"
            else:
                period = ""

            if add_coord:
                coords = self.get_coords(period, coord_values, present)
            if add_units:
                units = self.get_units(r, period, present)

            # LOG.debug(f"Period: {period}, coords: {coords}, units: {units}")

            assert len(r) <= len(self.key_labels), (
                f"Record {r} has more keys than expected: {self.key_labels}! {len(r)} != {len(self.key_labels)}"
            )

            derived = {}
            if units:
                derived.update(units)
            if coords:
                derived.update(coords)

            cols = {}
            for k, v in r.items():
                if k in self.key_labels and k in present:
                    out = k + period
                    if rank_collisions:
                        rank = candidate_rank(v, height, self.nominal_height, self.min_height)
                        # a strictly worse candidate loses the column to the current
                        # winner with all of its columns; on equal rank the later
                        # record wins, as before
                        if out in ranks and rank > ranks[out]:
                            continue
                        ranks[out] = rank
                    cols[out] = v

            # keep the historic column insertion order: values, units, coords;
            # the _level/_units columns only follow the winner of their value
            # column (a record that loses a collision also loses its level)
            res.update(cols)
            for dkey, dval in derived.items():
                stem, _ = _derived_stem(dkey)
                if stem in cols:
                    res[dkey] = dval

        return res

    def collect(
        self,
        collector: Any,
        raise_on_missing: bool = False,
        add_coord: bool = False,
        units_converter: Optional[Any] = None,
        add_units: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # the sensor height is needed for the collision ranking also when the
        # _level columns are not requested
        skip = []
        if not add_coord and self.nominal_height is None:
            skip = self.extract_coords

        mandatory = self.mandatory

        units_keys = []
        if self.period_bufr_key:
            units_keys = [self.period_bufr_key]

        value = self.collect_any(
            collector,
            mandatory=mandatory,
            skip=skip,
            raise_on_missing=raise_on_missing,
            units_keys=units_keys,
            units_converter=units_converter,
            add_units=add_units,
            first=self.first,
            pair_keys=[self.period_bufr_key] if self.period_bufr_key else None,
            **kwargs,
        )

        value = self.relabel(value, add_coord, add_units)
        return value

    def __repr__(self):
        return f"{self.__class__.__name__} param={self.param} keys{self.keys}"


class MultiAccessorBase(Accessor):
    accessors: List[Accessor] = []

    def __init__(self, accessors: Optional[List[Accessor]] = None, **kwargs: Any):
        self.accessors = accessors or self.accessors
        super().__init__(**kwargs)

    def empty_result(self) -> Dict[str, Optional[Any]]:
        return self.accessors[0].empty_result()

    @property
    def needed_keys(self) -> List[str]:
        r = []
        for a in self.accessors:
            r.extend(a.needed_keys)
        return r


class MultiFirstAccessor(MultiAccessorBase):
    def collect(self, collector: Any, **kwargs: Any) -> Dict[str, Any]:
        for a in self.accessors:
            try:
                r = a.collect(collector, raise_on_missing=True, **kwargs)
                if r:
                    return r
            except AllValueMissingException:
                pass
            except Exception:
                # LOG.debug(f"Error collecting from {a.name}: {e}")
                # raise
                pass

        return self.empty_result()


class MultiAllAccessor(MultiAccessorBase):
    #: when True, the results of the sub-accessors are merged with
    #: :func:`merge_period_results`: a missing value never overwrites a real one
    #: (or its _level/_units columns) and no _level/_units without a value column
    #: is kept. Default False keeps the previous last-writer-wins merge.
    missing_last = False

    def collect(self, collector: Any, **kwargs: Any) -> Dict[str, Any]:
        res = {}
        for a in self.accessors:
            r = a.collect(collector, raise_on_missing=False, **kwargs)
            if r:
                if self.missing_last:
                    merge_period_results(res, r)
                else:
                    res.update(r)

        if res:
            return res
        return self.empty_result()


class LatLonAccessor(SimpleAccessor):
    param: Any = PARAMS.LATLON
    keys: Dict[str, Any] = {"latitude": PARAMS.LAT, "longitude": PARAMS.LON}
    _cache = {}


DEFAULT_SID_ACCESSORS = {
    "ident": SimpleAccessor(keys={"ident": PARAMS.SID}, dtype=str),
    "WMO_station_id": ComputedKeyAccessor(keys={"WMO_station_id": PARAMS.SID}, dtype=str),
    "WIGOS_station_id": ComputedKeyAccessor(
        keys={"WIGOS_station_id": PARAMS.SID}, method_kwargs={"check_valid": True}, dtype=str
    ),
    "shipOrMobileLandStationIdentifier": SimpleAccessor(
        keys={"shipOrMobileLandStationIdentifier": PARAMS.SID}, dtype=str
    ),
    "station_id": SimpleAccessor(keys={"station_id": PARAMS.SID}, dtype=str),
    "icaoLocationIndicator": SimpleAccessor(keys={"icaoLocationIndicator": PARAMS.SID}, dtype=str),
    "stationOrSiteName": SimpleAccessor(keys={"stationOrSiteName": PARAMS.SID}, dtype=str),
    "longStationName": SimpleAccessor(keys={"longStationName": PARAMS.SID}, dtype=str),
}


class SidAccessor(MultiFirstAccessor):
    param: Any = PARAMS.SID
    accessors: List[Accessor] = list(DEFAULT_SID_ACCESSORS.values())
    _cache: Dict[str, "SidAccessor"] = {}

    @classmethod
    def from_user_keys(cls, keys: Union[str, List[str]]) -> "SidAccessor":
        """
        Create a SidAccessor from user-defined keys.

        Parameters
        ----------
        keys : str or list of str
            The keys to use for the SID accessor.

        Returns
        -------
        SidAccessor
            A new SidAccessor instance with the specified keys.
        """
        if isinstance(keys, str):
            keys = [keys]
        if not isinstance(keys, (list, tuple)):
            raise TypeError(f"Invalid keys type: {type(keys)}. Expected str, list or tuple.")

        lst = []
        for k in keys:
            if k in DEFAULT_SID_ACCESSORS:
                lst.append(DEFAULT_SID_ACCESSORS[k])
            else:
                ac = SimpleAccessor(keys={k: PARAMS.SID}, dtype=str)
                lst.append(ac)

        r = cls(accessors=lst)
        key = tuple(keys)
        if key not in cls._cache:
            cls._cache[key] = r
        return cls._cache[key]


class StationNameAccessor(MultiFirstAccessor):
    param: Any = PARAMS.STATION_NAME
    accessors: List[Accessor] = [
        SimpleAccessor(keys={"stationOrSiteName": PARAMS.STATION_NAME}),
        SimpleAccessor(keys={"icaoLocationIndicator": PARAMS.STATION_NAME}),
    ]


class ElevationAccessor(MultiFirstAccessor):
    param: Any = PARAMS.ELEVATION
    accessors: List[Accessor] = [
        SimpleAccessor(keys={"heightOfStationGroundAboveMeanSeaLevel": PARAMS.ELEVATION}),
        SimpleAccessor(keys={"heightOfStation": PARAMS.ELEVATION}),
    ]


class DatetimeAccessor(ComputedKeyAccessor):
    param: Any = PARAMS.TIME
    keys: Dict[str, Any] = {"data_datetime": PARAMS.TIME}


class AccessorManager:
    def __init__(
        self,
        default: List[Accessor],
        user_accessors: Optional[Dict[str, Accessor]] = None,
        **kwargs,
    ):
        if not isinstance(default, (list, tuple)):
            raise ValueError(f"Default accessors must be a list, got {type(default)}")

        accessors = set(default)
        for k, v in kwargs.items():
            if not isinstance(v, (list, tuple)):
                f"Group '{k}' must be a list, got {type(v)}"
            accessors.update(v)

        self.accessors = {a.param.label: a() for a in accessors}

        # replace default accessors with user-defined ones
        if user_accessors:
            for k, v in user_accessors.items():
                if k not in self.accessors:
                    raise ValueError(
                        f"User accessor '{k}' is not in the default accessors. Available: {self.accessors.keys()}"
                    )
                if not isinstance(v, Accessor):
                    raise ValueError(f"User accessor '{k}' must be an Accessor instance, got {type(v)}")
                self.accessors[k] = v

        def _build(lst):
            return {a.param.label: self.accessors[a.param.label] for a in lst}

        self.default = _build(default)
        self.groups = {"default": self.default}
        for k, v in kwargs.items():
            self.groups[k] = _build(v)

        self.cache = {}

    def get(self, params: Optional[Union[str, List[str]]]) -> Dict[str, Accessor]:
        if isinstance(params, str):
            if params.startswith("_"):
                raise ValueError(f"Invalid parameter name '{params}'")
            accessors = self.groups.get(params, None)
            if accessors is not None:
                return accessors

        cache_key = tuple(params)

        if cache_key in self.cache:
            accessors = self.cache[cache_key]
        else:
            if isinstance(params, str):
                params = [params]
            v = list(params)
            accessors = {}
            for param in v:
                if param.startswith("_"):
                    raise ValueError(f"Invalid parameter name '{param}'")
                if param in self.groups:
                    accessors.update(self.groups[param])
                elif param in self.accessors:
                    accessors[param] = self.accessors[param]
                else:
                    raise ValueError(f"Unsupported parameter '{param}'. Available parameters: {self.accessors.keys()}")

            self.cache[cache_key] = accessors

            assert accessors is not None

        return accessors

    def get_by_object(self, accessor: Any) -> Accessor:
        if not issubclass(accessor, Accessor):
            raise ValueError(f"Invalid accessor type={type(accessor)}")
        label = accessor.param.label
        return self.accessors[label]

    @staticmethod
    def labels(accessors: Dict[str, Accessor]) -> List[str]:
        r = set()
        for name, ac in accessors.items():
            r.add(name)
            labels = ac.labels
            # LOG.debug(f"Accessor {name} has labels: {labels}")
            if isinstance(labels, str):
                labels = [labels]
            if labels:
                r.update(labels)
        return r


class AccessorManagerCache(metaclass=ABCMeta):
    def __init__(self):
        self.cache = {"default": self.make()}

    @abstractmethod
    def make(self, *args, **kwargs):
        pass

    def get(self, key=None, **kwargs) -> AccessorManager:
        """Get the accessor manager for the given key."""
        if key is None or key == "default":
            return self.cache["default"]
        if key in self.cache:
            return self.cache[key]
        else:
            manager = self.make(**kwargs)
            self.cache[key] = manager
            return manager

    def __contains__(self, key: str) -> bool:
        """Check if the accessor manager for the given key exists."""
        return key in self.cache


PERIOD_RX = re.compile(r"(.+)_<(.+)>(.*)")

"""
Period key names are encoded at the accessor level as:

    name_<period>rest

E.g. "wind_gust_<1h>" or "wind_gust_<1h>_units".
"""


def resolve_period_key(key: str) -> Optional[str]:
    """
    Resolve the period key name by removing the <> brackets.

    Parameters
    ----------
    key : str
        The key to resolve.
    """
    m = PERIOD_RX.match(key)
    if m is not None:
        name = m.group(1)
        period = m.group(2)
        rest = m.group(3)
        return name + "_" + period + rest
    return key


def parse_period_key(key: str) -> Optional[str]:
    """
    Parse the period key name.

    Parameters
    ----------
    key : str
        The key to parse.

    Returns
    -------
    tuple
        - the key name
        - the key name without the period

        if the key does not contain a period, return None, None
    """
    m = PERIOD_RX.match(key)
    if m is not None:
        name = m.group(1)
        # period = m.group(2)
        rest = m.group(3)
        return key, name + rest
    return None, None
