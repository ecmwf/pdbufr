# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from abc import ABCMeta
from abc import abstractmethod
from typing import Any
from typing import Tuple

from pdbufr.core.filters import BufrFilter
from pdbufr.core.keys import COMPUTED_KEYS


def _parse_key(key) -> None:
    if key.startswith("#"):
        r, _, name = key.rpartition("#")
        if key.startswith("#0#"):
            return name, name, 0
        else:
            rank = r[1:]  # remove leading '#'
            rank = int(rank) if rank.isdigit() else 1
            return name, key, rank
    else:
        return key, f"#1#{key}", 1


def create_column(name_or_obj, allow_multi_rank=False) -> Any:
    if isinstance(name_or_obj, str):
        name = name_or_obj
        if name in COMPUTED_COLUMNS:
            return COMPUTED_COLUMNS[name]
        elif name.startswith("~"):
            if not allow_multi_rank:
                raise ValueError(f"Multi-rank columns are not allowed here: {name}")
            else:
                return MultiRankColumn(name)
        else:
            return SimpleColumn(name)
    else:
        return name_or_obj


class BaseColumn(metaclass=ABCMeta):
    name = None
    raw_key = None
    ranked_key = None
    rank = None
    keys = None
    mandatory_keys = None
    optional_keys = None
    header_only = False
    multi = False

    """
    Class representing a column used for the columns, filters and required columns in the flat reader.

    It can be a simple column (e.g. "latitude"), a multi-rank column (e.g. "~cloudType") or a
    computed column (e.g. "WMO_station_id").

    Attributes
    ----------
    name: str
        The name of the column. This is the name used in the output dataframe. May contain a
        rank prefix (e.g. "#1#latitude") or a computed key name (e.g. "WMO_station_id").
        Cannot start with "~".
    raw_key: str
        The raw key name (without rank prefix). E.g. if name is "#1#latitude", raw_key is "latitude".
    ranked_key: str
        The ranked key name (with rank prefix). E.g. if name is "#1#latitude", ranked_key
        is "#1#latitude". When the name does not contain a rank prefix, the rank is assumed
        to be 1 and the ranked_key is "#1#<name>". It does not apply to computed keys
        (e.g. "WMO_station_id") which do not have a rank.
    rank: int
        The rank of the key. E.g. if name is "#1#latitude", rank is 1. It is None if the no rank is
        associated with the column (e.g. for computed keys).
    keys: list
        The list of keys associated with the column. E.g. if name is "#1#latitude", keys is ["#1#latitude"].
        Its mainly used for computed keys which are built from multiple keys (e.g. "WMO_station_id"
        is associated with ["#1#WMO_block_number", "#1#WMO_station_number"]).
    mandatory_keys: list
        The list of mandatory keys
    optional_keys: list
        The list of optional keys
    header_only: bool
        Whether the column is header only
    multi: bool
        Whether the column is multi-rank.
    """

    @abstractmethod
    def get_value(self, accessor, ranked=True) -> Any:
        pass


class SimpleColumn(BaseColumn):
    def __init__(self, name: str) -> None:
        self.name = name
        self.raw_key, self.ranked_key, self.rank = _parse_key(name)

        if self.rank < 1:
            raise ValueError(f"SimpleColumn rank must be > 0, got {self.rank} for key {name}")

        self.keys = [name]
        self.mandatory_keys = [self.name]
        self.optional_keys = []

        self.header_only = False
        self.multi = False

    def get_value(self, accessor, ranked=True) -> Any:
        key = self.ranked_key if ranked else self.raw_key
        return accessor(key)


class MultiRankColumn(BaseColumn):
    """
    A column that can have multiple ranks.

    Parameters
    ----------
    name: str
        The name of the column. Must start with "~". The :obj:`name` is the ``name``
        with a leading "~" character. E.g. if name is "~cloudType", the :obj:`name` is "cloudType"..


    The leading "~" is a special notation in pdbufr to indicate that the column rank is not
    specified. The intention is to allow the user
    to define filter conditions that tests all occurrences (i.e. ranks) of the column
    in the message. Note that in the flat reader a column name without a rank prefix
    (e.g. "cloudType") is equivalent to a column with rank 1 (e.g. "#1#cloudType").
    """

    def __init__(self, name: str) -> None:
        if not name.startswith("~"):
            raise ValueError(f"MultiRankColumn name must start with '~', got {name}")

        self.name = name[1:]  # remove leading "~"
        self.raw_key = name[1:]
        self.ranked_key = self.raw_key
        self.rank = None

        self.keys = [name]
        self.mandatory_keys = [self.name]
        self.optional_keys = []

        self.header_only = False
        self.multi = True

    def get_value(self, accessor, ranked=True) -> Any:
        key = self.ranked_key if ranked else self.raw_key
        return accessor(key)

    # @staticmethod
    # def _parse(key) -> None:
    #     if key.startswith("#"):
    #         _, _, name = key.rpartition("#")
    #         return name, key
    #     else:
    #         return key, f"#1#{key}"


class ComputedColumn(BaseColumn):
    prefix = ""

    def __init__(self, conf) -> None:
        self.name = conf.column_name
        self.keys = conf.bufr_keys
        assert len(self.keys) > 0
        self.ranked_keys = [_parse_key(k)[1] for k in self.keys]
        self.method = conf.compute_method
        self.optional_keys = conf.optional_bufr_keys
        self.mandatory_keys = [k for k in self.keys if k not in self.optional_keys]
        self.header_only = conf.header_only
        self.multi = False

    def get_value(self, accessor, ranked=True) -> Any:
        values = dict()
        if ranked:
            for k, rk in zip(self.keys, self.ranked_keys):
                if (v := accessor(rk)) is not None:
                    values[k] = v
        else:
            values = {k: v for k in self.keys if (v := accessor(k)) is not None}

        print(" -> computed column values:", values)
        print("    keys:", self.keys)

        computed_value = None
        try:
            computed_value = self.method(values, ComputedColumn.prefix, self.keys)
        except Exception:
            # print("Error computing value for", self.name, ":", e)
            return None
        return computed_value


COMPUTED_COLUMNS = {conf.column_name: ComputedColumn(conf) for conf in COMPUTED_KEYS.values()}


def create_filter(name, value) -> BufrFilter:
    if name in COMPUTED_COLUMNS:
        return ComputedKeyFilter(COMPUTED_COLUMNS[name], value)
    elif name.startswith("~"):
        return RawKeyFilter(MultiRankColumn(name), value)
    else:
        return RawKeyFilter(SimpleColumn(name), value)


class HighLevelFilter(metaclass=ABCMeta):
    def __init__(self, column, filter_item: BufrFilter) -> None:
        self.column = column
        self.key = column.name
        self.name = column.name
        self.filter = filter_item
        self.header_only = column.header_only

        if self.column.multi:
            if not self.filter._multi_rank:
                raise ValueError(f"Filter for multi-rank column {self.column.name} must be a multi-rank filter")

    def match(self, value: Any) -> Tuple[bool, Any]:
        return self.filter.match(value)

    @abstractmethod
    def match_accessor(self, accessor: Any) -> Tuple[bool, Any]:
        pass


class RawKeyFilter(HighLevelFilter):
    def match_accessor(self, accessor) -> bool:
        value = self.column.get_value(accessor)
        return self.filter.match(value), value


class ComputedKeyFilter(HighLevelFilter):
    def __init__(self, column, filter_item) -> None:
        super().__init__(column, filter_item)
        self.keys = self.column.keys

    def match_accessor(self, accessor) -> bool:
        values = {k: v for k in self.keys if (v := accessor(k)) is not None}
        computed_value = None
        try:
            computed_value = self.column.method(values, "", self.keys)
        except Exception:
            return False, None

        if computed_value is not None:
            return self.filter.match(computed_value), computed_value
        return False, None
