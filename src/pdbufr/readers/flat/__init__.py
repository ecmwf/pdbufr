# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import collections
from email.mime import message
from sys import prefix
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import Mapping
from typing import MutableMapping
from typing import Sequence
from typing import Set
from typing import Union

import eccodes  # type: ignore
import numpy as np
import pandas as pd  # type: ignore

from pdbufr.core import structure
from pdbufr.core.accessor import resolve_period_key
from pdbufr.core.filters import BufrFilter
from pdbufr.core.filters import ComputedKeyFilter
from pdbufr.core.filters import RawKeyFilter
from pdbufr.core.filters import filters_match_header
from pdbufr.core.keys import COMPUTED_KEYS
from pdbufr.core.keys import RankedUncompressedBufrKey
from pdbufr.core.keys import UncompressedBufrKey
from pdbufr.core.keys import rank_from_key
from pdbufr.core.structure import BufrHeader
from pdbufr.core.structure import MessageWrapper
from pdbufr.core.structure import make_message_uid

from .. import Reader
from .block import extract_blocks
from .key import extract_keys


def _parse_key(key) -> None:
    if key.startswith("#"):
        _, _, name = key.rpartition("#")
        return name, key
    else:
        return key, f"#1#{key}"


class SimpleColumn:
    def __init__(self, name: str) -> None:
        self.name = name
        self.raw_key, self.ranked_key = _parse_key(name)

        self.keys = [name]
        self.mandatory_keys = [self.name]
        self.optional_keys = []

        self.header_only = False

    def get_value(self, accessor, ranked=True) -> Any:
        key = self.ranked_key if ranked else self.raw_key
        return accessor(key)

    @staticmethod
    def _parse(key) -> None:
        if key.startswith("#"):
            _, _, name = key.rpartition("#")
            return name, key
        else:
            return key, f"#1#{key}"


class ComputedColumn:
    prefix = ""

    def __init__(self, conf) -> None:
        self.name = conf[1]
        self.keys = conf[0]
        assert len(self.keys) > 0
        self.ranked_keys = [_parse_key(k)[1] for k in self.keys]
        self.method = conf[2]
        self.optional_keys = conf[3]
        self.mandatory_keys = [k for k in self.keys if k not in self.optional_keys]
        self.header_only = conf[4]

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


# class StructureCache:
#     def __init__(self, required_columns, columns) -> None:
#         self.cache = dict()
#         self.required_columns = required_columns
#         self.columns = columns

#     def create_uid(self, message: Mapping[str, Any]) -> str:
#         return make_message_uid(message)

#     def get(self, uid: str) -> Any:
#         return self.cache.get(uid, None)

#     @staticmethod
#     def _keys(message, columns, required_columns):
#         message = MessageWrapper.wrap_methods(message)
#         if required_columns:
#             if not all(key in message for key in required_columns):
#                 return []

#         result = []
#         for key in columns:
#             if key in required_columns or key in message:
#                 result.append(key)

#         return result

#     def add(self, uid: str, message) -> None:
#         if uid in self.cache:
#             return
#         self.cache[uid] = self._keys(message, self.columns, self.required_columns)


COMPUTED_COLUMNS = {conf[1]: ComputedColumn(conf) for conf in COMPUTED_KEYS}


# def test_computed_keys(
#     observation: Dict[str, Any],
#     filters: Dict[str, BufrFilter] = {},
#     prefix: str = "",
# ) -> bool:
#     # print("testing computed keys with filters:", filters, prefix)
#     for keys, computed_key, getter in COMPUTED_KEYS:
#         if computed_key in filters:
#             computed_value = None
#             try:
#                 computed_value = getter(observation, prefix, keys)
#             except Exception:
#                 return False
#             if computed_value is not None:
#                 if not filters[computed_key].match(computed_value):
#                     return False
#             else:
#                 return False
#     return True


class FlatReader(Reader):
    class ColumnInfo:
        def __init__(self) -> None:
            self.first_count = 0

    def __init__(
        self,
        path_or_messages,
        columns: Union[Sequence[str], str] = [],
        **kwargs: Any,
    ):
        class ColumnInfo:
            def __init__(self) -> None:
                self.first_count = 0

        self.column_info = ColumnInfo()
        self.columns = columns
        super().__init__(path_or_messages, columns=columns, column_info=self.column_info, **kwargs)

    def execute(
        self,
        # columns: Union[Sequence[str], str] = [],
        # filters: Mapping[str, Any] = {},
        # required_columns: Union[bool, Iterable[str]] = True,
        # **kwargs,
    ) -> pd.DataFrame:
        # class ColumnInfo:
        #     def __init__(self) -> None:
        #         self.first_count = 0

        # column_info = ColumnInfo()
        df = super().execute(
            # columns=columns,
            # filters=filters,
            # required_columns=required_columns,
            # column_info=column_info,
            # **kwargs,
        )

        # compare the column count in the first record to that of the
        # dataframe. If the latter is larger, then there were non-aligned columns,
        # which were appended to the end of the dataframe columns.
        if self.column_info.first_count > 0 and self.column_info.first_count < len(df.columns):
            import warnings

            # temporarily overwrite warnings formatter
            ori_formatwarning = warnings.formatwarning
            warnings.formatwarning = lambda msg, *args, **kwargs: f"Warning: {msg}\n"
            warnings.warn(
                (
                    "not all BUFR messages/subsets have the same structure in the input file. "
                    "Non-overlapping columns (starting with column[{column_info.first_count-1}] ="
                    f"{df.columns[self.column_info.first_count-1]}) were added to end of the resulting dataframe"
                    "altering the original column order for these messages."
                )
            )
            warnings.formatwarning = ori_formatwarning

        return df

    def read_records(
        self,
        bufr_obj: Iterable[MutableMapping[str, Any]],
        columns: Union[Sequence[str], str],
        filters: Mapping[str, Any] = {},
        filter_columns: bool = True,
        required_columns: Union[bool, Iterable[str]] = True,
        prefilter_headers: bool = False,
        column_info: Any = None,
    ) -> Iterator[Dict[str, Any]]:

        # we assume computed keys are not using keys from the header

        add_header = False
        add_data = False
        computed_columns = []
        add_filters = filter_columns

        # columns
        if isinstance(columns, str):
            columns = (columns,)

        if not isinstance(columns, Sequence):
            raise TypeError("invalid columns type")
        elif len(columns) == 0 or columns[0] == "":
            columns = ["all"]

        assert len(columns) > 0

        print("columns:", columns)

        if "all" in columns:
            if len(columns) > 1:
                raise ValueError("when 'all' is specified no other columns can be specified")
        elif "header" in columns and "data" in columns:
            if len(columns) > 2:
                raise ValueError(
                    "when both 'header' and 'data' is specified no other columns can be specified"
                )

        if any(col in ("all", "header", "data   ") for col in columns):
            yield from self.read_blocks(
                bufr_obj,
                columns,
                filters,
                add_filters,
                required_columns,
                prefilter_headers,
                column_info,
            )
        else:
            yield from self.read_keys(
                bufr_obj,
                columns,
                filters,
                add_filters,
                required_columns,
                prefilter_headers,
            )
        return

        if "all" in columns or "header" in columns:
            add_header = True

        if "all" in columns or "data" in columns:
            add_data = True

        block_keys = ("all", "header", "data")
        key_columns = [col for col in columns if col not in block_keys]

        block_mode = add_header or add_data

        # convert to column objects
        columns = dict()
        for k in key_columns:
            name = k
            if name in COMPUTED_COLUMNS:
                columns[k] = ComputedColumn(COMPUTED_COLUMNS[name])
            else:
                columns[k] = RawColumn(name)

        # if isinstance(required_columns, bool):
        #     if block_mode:
        #         required_columns = set()
        #     elif required_columns:
        #         required_columns = set(columns.keys())
        #     else:
        #         required_columns = set()
        # elif isinstance(required_columns, str):
        #     required_columns = {required_columns}
        # elif isinstance(required_columns, Iterable):
        #     required_columns = set(required_columns)
        # else:
        #     raise TypeError("required_columns must be a bool, str or an iterable")

        # filters
        filters = dict(filters)
        filters = {k: BufrFilter.from_user(filters[k], key=k) for k in filters}

        # prepare count filter
        if "count" in filters:
            max_count = filters["count"].max()
        else:
            max_count = None

        count_filter = filters.pop("count", None)

        # convert to filter objects
        all_filters_keys = []
        for k in list(filters.keys()):
            name = k
            if name in COMPUTED_COLUMNS:
                filters[name] = ComputedKeyFilter(COMPUTED_COLUMNS[name], filters[name])
                all_filters_keys.extend(filters[name].keys)
            else:
                filters[name] = RawKeyFilter(name, filters[name])
                all_filters_keys.append(name)

        # all filters keys must be present so we do not need them in the required columns
        # required_columns = required_columns - set(filters.keys())

        if isinstance(required_columns, bool):
            if block_mode:
                required_columns = set()
            elif required_columns:
                required_columns = set(columns.keys())
            else:
                required_columns = set()
        elif isinstance(required_columns, str):
            required_columns = {required_columns}
        elif isinstance(required_columns, Iterable):
            required_columns = set(required_columns)
        else:
            raise TypeError("required_columns must be a bool, str or an iterable")

        r = []
        for k in required_columns:
            if isinstance(k, str):
                if k in COMPUTED_COLUMNS:
                    r.append(ComputedColumn(COMPUTED_COLUMNS[k]))
                else:
                    r.append(RawColumn(k).keys)
            else:
                r.append(k)

        for k, v in filters.items():
            r.append(v.column)

        required_columns = r

        if column_info is not None:
            column_info.first_count = 0

        structure_cache = StructureCache(required_columns, columns)

        for count, msg in enumerate(bufr_obj, 1):
            # We use a context manager to automatically delete the handle of the BufrMessage.
            # We have to use a wrapper object here because a message can also be a dict
            with MessageWrapper.wrap_context(msg) as message:
                # count filter
                if count_filter is not None and not count_filter.match(count):
                    continue

                header = BufrHeader(message, columns, filters)
                data_filters = {k: v for k, v in filters.items() if k not in header.filters}
                data_columns = {k: v for k, v in columns.items() if k not in header.columns}

                # test filters on header keys before unpacking
                if prefilter_headers and not header.filters_match():
                    continue

                data_required_columns = required_columns
                if data_required_columns:
                    data_required_columns = data_required_columns - header.keys

                # check computed keys in header
                uid = structure_cache.create_uid(message)
                state = structure_cache.get(uid)
                if uid in structure_cache:
                    if not structure_cache[uid]:
                        return

                # get full header or data sections
                if add_header or add_data:
                    for record in extract_blocks(
                        message,
                        header,
                        add_header,
                        add_data,
                        data_filters,
                        add_filters,
                        data_required_columns,
                    ):
                        if record:
                            if column_info is not None and column_info.first_count == 0:
                                column_info.first_count = len(record)
                            yield record

                # get list of specific keys
                else:
                    for record in extract_keys(
                        message,
                        header,
                        data_filters,
                        add_filters,
                        data_columns,
                        data_required_columns,
                    ):
                        if record:
                            yield record

            # optimisation: skip decoding messages above max_count
            if max_count is not None and count >= max_count:
                break

    def read_blocks(
        self,
        bufr_obj: Iterable[MutableMapping[str, Any]],
        columns: Union[Sequence[str], str],
        filters: Mapping[str, Any] = {},
        add_filters: bool = True,
        required_columns: Union[bool, Iterable[str]] = True,
        prefilter_headers: bool = False,
        column_info: Any = None,
    ):
        # block_keys = ("all", "header", "data")
        # key_columns = [col for col in columns if col not in block_keys]

        # block_mode = add_header or add_data

        # convert to column objects
        # columns = dict()
        # for k in key_columns:
        #     name = k
        #     if name in COMPUTED_COLUMNS:
        #         columns[k] = ComputedColumn(COMPUTED_COLUMNS[name])
        #     else:
        #         columns[k] = SimpleColumn(name)

        # if isinstance(required_columns, bool):
        #     if block_mode:
        #         required_columns = set()
        #     elif required_columns:
        #         required_columns = set(columns.keys())
        #     else:
        #         required_columns = set()
        # elif isinstance(required_columns, str):
        #     required_columns = {required_columns}
        # elif isinstance(required_columns, Iterable):
        #     required_columns = set(required_columns)
        # else:
        #     raise TypeError("required_columns must be a bool, str or an iterable")

        if "all" in columns or "header" in columns:
            add_header = True

        if "all" in columns or "data" in columns:
            add_data = True

        # filters
        filters = dict(filters)
        filters = {k: BufrFilter.from_user(filters[k], key=k) for k in filters}

        # separate count filter
        if "count" in filters:
            max_count = filters["count"].max()
        else:
            max_count = None

        count_filter = filters.pop("count", None)

        # convert to filter objects
        for k in list(filters.keys()):
            name = k
            if name in COMPUTED_COLUMNS:
                filters[name] = ComputedKeyFilter(COMPUTED_COLUMNS[name], filters[name])
            else:
                filters[name] = RawKeyFilter(name, filters[name])

        # all filters keys must be present so we do not need them in the required columns
        # required_columns = required_columns - set(filters.keys())

        if isinstance(required_columns, bool):
            required_columns = set()
        elif isinstance(required_columns, str):
            required_columns = {required_columns}
        elif isinstance(required_columns, Iterable):
            required_columns = set(required_columns)
        else:
            raise TypeError("required_columns must be a bool, str or an iterable")

        required_columns, required_columns_keys, required_columns_names = self.prepare_required_columns(
            required_columns, filters
        )

        # r = []
        # for k in required_columns:
        #     if isinstance(k, str):
        #         if k in COMPUTED_COLUMNS:
        #             r.append(ComputedColumn(COMPUTED_COLUMNS[k]))
        #         else:
        #             r.append(SimpleColumn(k).keys)
        #     else:
        #         r.append(k)

        # for k, v in filters.items():
        #     r.append(v.column)

        # required_columns = r

        # required_columns_keys = set()
        # required_columns_names = set()
        # for col in required_columns:
        #     required_columns_names.add(col.name)
        #     if hasattr(col, "header_only"):
        #         if not col.header_only:
        #             required_columns_keys.update(col.mandatory_keys)
        #     else:
        #         required_columns_keys.update(col.mandatory_keys)

        # def ensure_rank(key):
        #     if key.startswith("#"):
        #         return key
        #     else:
        #         return f"#1#{key}"

        if column_info is not None:
            column_info.first_count = 0

        for count, msg in enumerate(bufr_obj, 1):
            # We use a context manager to automatically delete the handle of the BufrMessage.
            # We have to use a wrapper object here because a message can also be a dict
            with MessageWrapper.wrap_context(msg) as message:
                # count filter
                if count_filter is not None and not count_filter.match(count):
                    continue

                header = BufrHeader(message, None, filters)
                data_filters = {k: v for k, v in filters.items() if k not in header.filters}
                # data_columns = {k: v for k, v in columns.items() if k not in header.columns}

                # test filters on header keys before unpacking
                if prefilter_headers and not header.filters_match():
                    continue

                data_required_columns_keys = required_columns_keys
                if data_required_columns_keys:
                    data_required_columns_keys = data_required_columns_keys - header.keys
                    data_required_columns_keys = {k for k in data_required_columns_keys}

                # data_required_columns = required_columns
                # if data_required_columns:
                #     data_required_columns = data_required_columns - header.keys

                # get full header or data sections

                for record in extract_blocks(
                    message,
                    header,
                    add_header,
                    add_data,
                    data_filters,
                    add_filters,
                    data_required_columns_keys,
                ):
                    if record:
                        if column_info is not None and column_info.first_count == 0:
                            column_info.first_count = len(record)
                        yield record

            # optimisation: skip decoding messages above max_count
            if max_count is not None and count >= max_count:
                break

    def read_keys(
        self,
        bufr_obj: Iterable[MutableMapping[str, Any]],
        columns: Union[Sequence[str], str],
        filters: Mapping[str, Any] = {},
        add_filters: bool = True,
        required_columns: Union[bool, Iterable[str]] = True,
        prefilter_headers: bool = False,
    ) -> Iterator[Dict[str, Any]]:

        assert isinstance(columns, (list, tuple)), f"expected list or tuple, got {type(columns)}"

        # convert to column objects
        columns_input = list(columns)
        columns = dict()
        for k in columns_input:
            name = k
            if name in COMPUTED_COLUMNS:
                columns[k] = COMPUTED_COLUMNS[name]
            else:
                columns[k] = SimpleColumn(name)

        # print("columns:", columns)

        # filters
        filters = dict(filters)
        filters = {k: BufrFilter.from_user(filters[k], key=k) for k in filters}

        # separate count filter
        if "count" in filters:
            max_count = filters["count"].max()
        else:
            max_count = None

        count_filter = filters.pop("count", None)

        # convert filters to objects
        for k in list(filters.keys()):
            name = k
            if name in COMPUTED_COLUMNS:
                filters[name] = ComputedKeyFilter(COMPUTED_COLUMNS[name], filters[name])
            else:
                filters[name] = RawKeyFilter(SimpleColumn(name), filters[name])

        # all filters keys must be present so we do not need them in the required columns
        # required_columns = required_columns - set(filters.keys())

        print("required_columns before processing:", required_columns)
        # define required columns and convert to column objects
        if isinstance(required_columns, bool):
            if required_columns:
                required_columns = columns
            else:
                required_columns = []
        elif isinstance(required_columns, str):
            required_columns = [required_columns]
        elif not isinstance(required_columns, Iterable):
            raise TypeError("required_columns must be a bool, str or an iterable")

        required_columns, required_columns_keys, required_columns_names = self.prepare_required_columns(
            required_columns, filters
        )

        # print("required_columns after processing:", required_columns)
        # r = []
        # for k in required_columns:
        #     if isinstance(k, str):
        #         if k in COMPUTED_COLUMNS:
        #             r.append(COMPUTED_COLUMNS[k])
        #         else:
        #             r.append(SimpleColumn(k))
        #     else:
        #         r.append(k)

        # for k, v in filters.items():
        #     r.append(v.column)

        # print("required_columns after processing:", r)

        # required_columns = r
        # required_columns_keys = set()
        # required_columns_names = set()
        # for col in required_columns:
        #     required_columns_names.add(col.name)
        #     if hasattr(col, "header_only"):
        #         if not col.header_only:
        #             required_columns_keys.update(col.mandatory_keys)
        #     else:
        #         required_columns_keys.update(col.mandatory_keys)

        # columns_keys = set()
        # columns_names = set()
        # for col in columns.values():
        #     columns_keys.update(col.keys)
        #     columns_names.add(col.name)

        # print("columns_keys:", columns_keys)
        # print("columns_names:", columns_names)

        # print("required_columns_keys:", required_columns_keys)
        # print("required_columns_names:", required_columns_names)

        # structure_cache = StructureCache(required_columns, columns)

        def ensure_rank(key):
            if key.startswith("#"):
                return key
            else:
                return f"#1#{key}"

        for count, msg in enumerate(bufr_obj, 1):
            # We use a context manager to automatically delete the handle of the BufrMessage.
            # We have to use a wrapper object here because a message can also be a dict
            with MessageWrapper.wrap_context(msg) as message:
                # print(f"MESSAGE: {count}")

                # count filter
                if count_filter is not None and not count_filter.match(count):
                    continue

                header = BufrHeader(message, columns, filters)
                data_filters = {k: v for k, v in filters.items() if k not in header.filters}
                data_columns = {k: v for k, v in columns.items() if v not in header.columns}

                print("header columns:", header.columns)
                # print("data_filters:", data_filters)
                print("data_columns:", data_columns)

                # test filters on header keys before unpacking
                if prefilter_headers and not header.match_filters():
                    continue

                data_required_columns_keys = required_columns_keys
                if data_required_columns_keys:
                    data_required_columns_keys = data_required_columns_keys - header.keys
                    data_required_columns_keys = {ensure_rank(k) for k in data_required_columns_keys}

                print("data_required_columns_keys:", data_required_columns_keys)
                print("data_filters:", data_filters)
                for record in extract_keys(
                    message,
                    header,
                    data_filters,
                    add_filters,
                    data_columns,
                    data_required_columns_keys,
                ):
                    if record and any(v is not None for v in record.values()):
                        print(" -> yielding record:", record)
                        yield record

            # optimisation: skip decoding messages above max_count
            if max_count is not None and count >= max_count:
                break

    def prepare_required_columns(
        self,
        required_columns: Union[bool, Iterable[str]],
        filters: Mapping[str, Any],
    ) -> None:
        r = []
        for k in required_columns:
            if isinstance(k, str):
                if k in COMPUTED_COLUMNS:
                    r.append(ComputedColumn(COMPUTED_COLUMNS[k]))
                else:
                    r.append(SimpleColumn(k).keys)
            else:
                r.append(k)

        for k, v in filters.items():
            r.append(v.column)

        required_columns = r

        required_columns_keys = set()
        required_columns_names = set()
        for col in required_columns:
            required_columns_names.add(col.name)
            if hasattr(col, "header_only"):
                if not col.header_only:
                    required_columns_keys.update(col.mandatory_keys)
            else:
                required_columns_keys.update(col.mandatory_keys)

        return required_columns, required_columns_keys, required_columns_names

    def adjust_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = df.columns.tolist()

        print(" -> before accessors: columns=", columns)
        print(" -> self.columns=", self.columns)

        r = []
        for name in self.columns:
            for i, c in enumerate(columns):
                if c is None:
                    continue
                if c == name:
                    r.append(c)
                    columns[i] = None

        # add the rest
        for c in columns:
            if c is not None:
                r.append(c)

        # LOG.debug(f" -> after accessors: columns={columns}")
        assert len(r) == len(columns), f"Expected {len(columns)} columns, got {len(r)}"
        print(" -> r=", r)

        df = df[r]
        return df


reader = FlatReader
