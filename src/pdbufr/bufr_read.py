# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from __future__ import annotations

import os
import typing as T

import pandas as pd  # type: ignore

from .high_level_bufr.bufr import BufrFile
from .readers import get_reader


def read_bufr(
    path_or_messages: T.Union[str, bytes, "os.PathLike[T.Any]", T.Iterable[T.MutableMapping[str, T.Any]]],
    # columns: T.Union[T.Sequence[str], str] = [],
    # filters: T.Mapping[str, T.Any] = {},
    # required_columns: T.Union[bool, T.Iterable[str]] = True,
    # flat: bool = False,
    reader: T.Union[str, None] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Read selected observations from a BUFR file into DataFrame.
    """
    reader = get_reader(reader, path_or_messages)
    return reader.read(**kwargs)

    # if isinstance(path_or_messages, (str, bytes, os.PathLike)):
    #     with BufrFile(path_or_messages) as bufr_file:  # type: ignore
    #         return _read_bufr(
    #             bufr_file,
    #             columns=columns,
    #             filters=filters,
    #             required_columns=required_columns,
    #             flat=flat,
    #         )
    # else:
    #     return _read_bufr(
    #         path_or_messages,
    #         columns=columns,
    #         filters=filters,
    #         required_columns=required_columns,
    #         flat=flat,
    #     )


def read_bufr_synop(
    path_or_messages: T.Union[str, bytes, "os.PathLike[T.Any]", T.Iterable[T.MutableMapping[str, T.Any]]],
    params: T.Union[T.Sequence[str], T.Any] = None,
    columns: T.Union[T.Sequence[str], str] = [],
    filters: T.Mapping[str, T.Any] = {},
) -> pd.DataFrame:
    """
    Read selected observations from a BUFR file into DataFrame.
    """
    kwargs = {"params": params, "columns": columns, "filters": filters}

    def _get(bufr_obj):
        from .readers.synop import stream_bufr_synop

        observations = stream_bufr_synop(bufr_obj, **kwargs)
        return pd.DataFrame.from_records(observations)

    if isinstance(path_or_messages, (str, bytes, os.PathLike)):
        with BufrFile(path_or_messages) as bufr_file:  # type: ignore
            return _get(bufr_file)
    else:
        return _get(path_or_messages)


def read_bufr_temp(
    path_or_messages: T.Union[str, bytes, "os.PathLike[T.Any]", T.Iterable[T.MutableMapping[str, T.Any]]],
    # columns: T.Union[T.Sequence[str], str] = [],
    filters: T.Mapping[str, T.Any] = {},
    offset_mode: str = "add",
) -> pd.DataFrame:
    """
    Read selected observations from a BUFR file into DataFrame.
    """
    kwargs = {"filters": filters}

    def _get(bufr_obj):
        from .readers.temp import stream_bufr_temp

        observations = stream_bufr_temp(bufr_obj, **kwargs)
        return pd.DataFrame.from_records(observations)

    if isinstance(path_or_messages, (str, bytes, os.PathLike)):
        with BufrFile(path_or_messages) as bufr_file:  # type: ignore
            return _get(bufr_file)
    else:
        return _get(path_or_messages)


# def _read_bufr(
#     bufr_obj: T.Iterable[T.MutableMapping[str, T.Any]],
#     columns: T.Union[T.Sequence[str], str] = [],
#     filters: T.Mapping[str, T.Any] = {},
#     required_columns: T.Union[bool, T.Iterable[str]] = True,
#     flat: bool = False,
# ) -> pd.DataFrame:
#     if not flat:
#         observations = bufr_structure.stream_bufr(
#             bufr_obj, columns, filters=filters, required_columns=required_columns
#         )
#         return pd.DataFrame.from_records(observations)
#     else:

#         class ColumnInfo:
#             def __init__(self) -> None:
#                 self.first_count = 0

#         column_info = ColumnInfo()

#         # returns a generator
#         observations = bufr_structure.stream_bufr_flat(
#             bufr_obj,
#             columns,
#             filters=filters,
#             required_columns=required_columns,
#             column_info=column_info,
#         )

#         df = pd.DataFrame.from_records(observations)

#         # compare the column count in the first record to that of the
#         # dataframe. If the latter is larger, then there were non-aligned columns,
#         # which were appended to the end of the dataframe columns.
#         if column_info.first_count > 0 and column_info.first_count < len(df.columns):
#             import warnings

#             # temporarily overwrite warnings formatter
#             ori_formatwarning = warnings.formatwarning
#             warnings.formatwarning = lambda msg, *args, **kwargs: f"Warning: {msg}\n"
#             warnings.warn(
#                 (
#                     "not all BUFR messages/subsets have the same structure in the input file. "
#                     "Non-overlapping columns (starting with column[{column_info.first_count-1}] ="
#                     f"{df.columns[column_info.first_count-1]}) were added to end of the resulting dataframe"
#                     "altering the original column order for these messages."
#                 )
#             )
#             warnings.formatwarning = ori_formatwarning

#         return df
