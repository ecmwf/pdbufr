# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import MutableMapping
from typing import Sequence
from typing import Union

if TYPE_CHECKING:
    import pandas as pd  # type: ignore


def read_bufr(
    path_or_messages: Union[str, bytes, "os.PathLike[Any]", Iterable[MutableMapping[str, Any]]],
    columns: Union[Sequence[str], str] = [],
    *,
    reader: str = "generic",
    **kwargs: Any,
) -> "pd.DataFrame":
    """
    Read selected observations from a BUFR file into DataFrame.
    """

    from .readers import get_reader

    kwargs = dict(**kwargs)
    flat = kwargs.pop("flat", False)
    reader = get_reader(reader, path_or_messages, flat=flat, columns=columns, **kwargs)
    return reader.execute()
    # return reader(columns=columns, **kwargs)
