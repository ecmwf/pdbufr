# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import typing as T

from .. import bufr_structure
from . import Reader


class GenericReader(Reader):
    def read(
        self,
        bufr_obj,
        columns: T.Union[T.Sequence[str], str] = [],
        filters: T.Mapping[str, T.Any] = {},
        required_columns: T.Union[bool, T.Iterable[str]] = True,
        flat=False,
        **kwargs,
    ):
        if not flat:
            return super().read(
                bufr_obj,
                columns=columns,
                filters=filters,
                required_columns=required_columns,
                flat=flat,
                **kwargs,
            )
        else:

            class ColumnInfo:
                def __init__(self) -> None:
                    self.first_count = 0

            column_info = ColumnInfo()
            df = super().read(
                bufr_obj,
                columns=columns,
                filters=filters,
                required_columns=required_columns,
                column_info=column_info,
                flat=flat,
                **kwargs,
            )

            # compare the column count in the first record to that of the
            # dataframe. If the latter is larger, then there were non-aligned columns,
            # which were appended to the end of the dataframe columns.
            if column_info.first_count > 0 and column_info.first_count < len(df.columns):
                import warnings

                # temporarily overwrite warnings formatter
                ori_formatwarning = warnings.formatwarning
                warnings.formatwarning = lambda msg, *args, **kwargs: f"Warning: {msg}\n"
                warnings.warn(
                    (
                        "not all BUFR messages/subsets have the same structure in the input file. "
                        "Non-overlapping columns (starting with column[{column_info.first_count-1}] ="
                        f"{df.columns[column_info.first_count-1]}) were added to end of the resulting dataframe"
                        "altering the original column order for these messages."
                    )
                )
                warnings.formatwarning = ori_formatwarning

            return df

    def read_records(self, bufr_obj, flat=False, **kwargs):
        if not flat:
            return self.read_hierarchy(bufr_obj, **kwargs)
        else:
            return self.read_flat(bufr_obj, **kwargs)

    def read_hierarchy(self, bufr_obj, **kwargs):
        return bufr_structure.stream_bufr(bufr_obj, **kwargs)

    def read_flat(self, bufr_obj, **kwargs):
        return bufr_structure.stream_bufr_flat(bufr_obj, **kwargs)


reader = GenericReader
