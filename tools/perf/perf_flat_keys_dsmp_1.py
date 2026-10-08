# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pdbufr
from pdbufr.utils.testing import get_remote_test_data

path = get_remote_test_data("dsmp_compressed.bufr")

filters = {"satelliteID": 286}

columns = [
    "satelliteID",
    "#1#latitude",
    "#1#longitude",
    "fieldOfViewNumber",
    "#9#brightnessTemperature",
    "#10#brightnessTemperature",
    "#11#brightnessTemperature",
    "#12#brightnessTemperature",
    "#13#brightnessTemperature",
    "#14#brightnessTemperature",
    "#15#brightnessTemperature",
    "#16#brightnessTemperature",
    "#17#brightnessTemperature",
    "#18#brightnessTemperature",
]

data = pdbufr.read_bufr(path, columns=columns, filters=filters, reader="flat", prefilter_headers=True)
