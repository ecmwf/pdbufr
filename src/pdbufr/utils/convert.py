# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import datetime
from typing import Optional
from typing import Union

PERIOD_UNITS = {"s": 1, "m": 60, "h": 24 * 60, "d": 86400}


def period_to_timedelta(
    period: Optional[Union[int, float]], units: Optional[str]
) -> Optional[datetime.timedelta]:
    if period is None or units is None:
        return None

    scaling = PERIOD_UNITS.get(units, None)
    if scaling is not None:
        return datetime.timedelta(seconds=int(period) * scaling)

    return None
