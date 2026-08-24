# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pdbufr
from pdbufr.utils.testing import sample_test_data_path

path = sample_test_data_path("aircraft_mrar_compressed.bufr")

filters = {"typicalYear": 2021}

columns = [
    "aircraftRegistrationNumberOrOtherIdentification",
    "latitude",
    "longitude",
    "airTemperature",
    "windSpeed",
    "softwareVersionNumber",
]

data = pdbufr.read_bufr(path, columns=columns, filters=filters, reader="flat", prefilter_headers=True)
