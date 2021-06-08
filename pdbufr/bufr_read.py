# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import typing as T

import eccodes  # type: ignore
import pandas as pd  # type: ignore

from . import bufr_structure
from .high_level_bufr.bufr import BufrFile


def read_bufr(
    path: T.Union[str, bytes, "os.PathLike[T.Any]"],
    columns: T.Iterable[str],
    filters: T.Mapping[str, T.Any] = {},
    required_columns: T.Union[bool, T.Iterable[str]] = True,
) -> pd.DataFrame:
    """
    Read selected observations from a BUFR file into DataFrame.

    :param path: The path to the BUFR file
    :param columns: A list of BUFR keys to return in the DataFrame for every observation
    :param filters: A dictionary of BUFR key / filter definition to filter the observations to return
    :param required_columns: The list BUFR keys that are required for all observations.
        ``True`` means all ``columns`` are required
    """
    with BufrFile(path) as bufr_file:  # type: ignore
        observations = bufr_structure.stream_bufr(
            bufr_file, columns, filters, required_columns
        )
        return pd.DataFrame.from_records(observations)
