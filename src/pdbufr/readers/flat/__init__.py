# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from typing import Any, Dict, Iterable, Iterator, Mapping, MutableMapping, Sequence, Union

import pandas as pd  # type: ignore

from pdbufr.core.filters import BufrFilter
from pdbufr.core.keys import rank_from_key as rank_from_key
from pdbufr.core.structure import BufrHeader, MessageWrapper

from .. import Reader
from .block import extract_blocks
from .column import create_column, create_filter
from .key import extract_keys


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
    ) -> pd.DataFrame:

        df = super().execute()

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
                    f"{df.columns[self.column_info.first_count - 1]}) were added to the end of the resulting dataframe "
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
        """
        Read records from a BUFR message, either by blocks (header and data sections) or by keys.

        Parameters
        ----------
        bufr_obj: Iterable[MutableMapping[str, Any]]
            An iterable of BUFR messages (e.g. a list of eccodes.Message objects or a list of dicts).
        columns: Union[Sequence[str], str]
            The columns to read from the BUFR messages. Can be a list of column names or a single
            string (e.g. "all", "header", "data").
        filters: Mapping[str, Any]
            A mapping of column names to filter values. The filters will be applied to the corresponding
            columns in the BUFR messages. The filter values can be of any type supported by ``BufrFilter.from_user``.
        filter_columns: bool
            Whether to add the columns used in the filters to the output records (default: True).
        required_columns: Union[bool, Iterable[str]]
            The columns that are required to be present in the output records. Can be a boolean (True means
            all columns, False means no columns) or a list of column names (default: True).
        prefilter_headers: bool
            Whether to apply the filters to the header keys before unpacking the data (default: False).
        column_info: Any
        """
        add_filters = filter_columns

        # columns
        if isinstance(columns, str):
            columns = (columns,)

        if not isinstance(columns, Sequence):
            raise TypeError("invalid columns type")
        elif len(columns) == 0 or columns[0] == "":
            columns = ["all"]

        assert len(columns) > 0

        for col in columns:
            if not isinstance(col, str):
                raise TypeError(f"all columns must be strings! {col} is a {type(col)}")

        if "all" in columns:
            if len(columns) > 1:
                raise ValueError("when 'all' is specified no other columns can be specified")
        elif "header" in columns and "data" in columns:
            if len(columns) > 2:
                raise ValueError("when both 'header' and 'data' is specified no other columns can be specified")

        if any(col in ("all", "header", "data") for col in columns):
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

        add_header = False
        add_data = False

        if "all" in columns or "header" in columns:
            add_header = True

        if "all" in columns or "data" in columns:
            add_data = True

        if not add_header and not add_data:
            raise ValueError("at least one of 'header' or 'data' must be specified in columns")

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
            filters[k] = create_filter(k, filters[k])

        # all filters keys must be present so we do not need them in the required columns
        # required_columns = required_columns - set(filters.keys())
        if isinstance(required_columns, bool):
            required_columns = []
        elif isinstance(required_columns, str):
            required_columns = [required_columns]
        elif not isinstance(required_columns, Iterable):
            raise TypeError("required_columns must be a bool, str or an iterable")

        for k in required_columns:
            if k in ("all", "header", "data"):
                raise ValueError(
                    f"invalid required column: {k} (cannot be one of 'all', 'header' or 'data' when using block mode)"
                )

        required_columns, required_columns_keys, required_columns_names = self.prepare_required_columns(
            required_columns, filters
        )

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

                # test filters on header keys before unpacking
                if prefilter_headers and not header.match_filters():
                    continue

                data_required_columns_keys = required_columns_keys
                header_required_columns_keys = set()
                if data_required_columns_keys:
                    data_required_columns_keys = data_required_columns_keys - header.keys
                    data_required_columns_keys = {k for k in data_required_columns_keys}
                    if len(data_required_columns_keys) != required_columns_keys:
                        header_required_columns_keys = required_columns_keys - data_required_columns_keys

                # get full header or data sections
                for record in extract_blocks(
                    message,
                    header,
                    add_header,
                    add_data,
                    data_filters,
                    add_filters,
                    header_required_columns_keys,
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
            columns[k] = create_column(k, allow_multi_rank=True)

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
            filters[k] = create_filter(k, filters[k])

        # define required columns and convert to column objects
        if isinstance(required_columns, bool):
            if required_columns:
                required_columns = []
                for c in columns.values():
                    # multi rank columns are not allowed in the required columns
                    if c.multi:
                        required_columns.append(create_column(c.raw_key, allow_multi_rank=False))
                    else:
                        required_columns.append(c)
            else:
                required_columns = []
        elif isinstance(required_columns, str):
            required_columns = [required_columns]
        elif not isinstance(required_columns, Iterable):
            raise TypeError("required_columns must be a bool, str or an iterable")

        required_columns, required_columns_keys, required_columns_names = self.prepare_required_columns(
            required_columns, filters
        )

        def ensure_rank(key):
            if key.startswith("#"):
                return key
            else:
                return f"#1#{key}"

        for count, msg in enumerate(bufr_obj, 1):
            # We use a context manager to automatically delete the handle of the BufrMessage.
            # We have to use a wrapper object here because a message can also be a dict
            with MessageWrapper.wrap_context(msg) as message:
                # count filter
                if count_filter is not None and not count_filter.match(count):
                    continue

                header = BufrHeader(message, columns, filters)
                data_filters = {k: v for k, v in filters.items() if k not in header.filters}
                data_columns = {k: v for k, v in columns.items() if v not in header.columns}

                # test filters on header keys before unpacking
                if prefilter_headers and not header.match_filters():
                    continue

                data_required_columns_keys = required_columns_keys
                if data_required_columns_keys:
                    data_required_columns_keys = data_required_columns_keys - header.keys
                    data_required_columns_keys = {ensure_rank(k) for k in data_required_columns_keys}

                for record in extract_keys(
                    message,
                    header,
                    data_filters,
                    add_filters,
                    data_columns,
                    data_required_columns_keys,
                ):
                    if record and any(v is not None for v in record.values()):
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
        for col in required_columns:
            r.append(create_column(col, allow_multi_rank=False))

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

        df = df[r]
        return df


reader = FlatReader
