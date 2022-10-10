# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import typing as T

import pandas as pd  # type: ignore

from . import bufr_structure
from .high_level_bufr.bufr import BufrFile


def read_bufr(
    path: T.Union[str, bytes, "os.PathLike[T.Any]"],
    columns: T.Union[T.Iterable[str], str],
    filters: T.Mapping[str, T.Any] = {},
    required_columns: T.Union[bool, T.Iterable[str]] = True,
    mode: str = "tree",
) -> pd.DataFrame:
    """
    Read selected observations from a BUFR file into DataFrame.
    """

    with BufrFile(path) as bufr_file:  # type: ignore
        if mode == "tree":
            observations = bufr_structure.stream_bufr(
                bufr_file, columns, filters=filters, required_columns=required_columns
            )
        elif mode == "flat":
            observations = bufr_structure.stream_bufr_flat(
                bufr_file, columns, filters=filters, required_columns=required_columns
            )
        else:
            raise ValueError(f"Invalid mode value = {mode}")

        return pd.DataFrame.from_records(observations)
