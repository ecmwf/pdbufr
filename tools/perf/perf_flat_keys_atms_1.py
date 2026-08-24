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

path = get_remote_test_data("atms_2018052712_lwda_oper.bufr")

filters = {"#14#brightnessTemperature": slice(None, 233)}

columns = ["satelliteIdentifier", "satelliteZenithAngle", "#2#channelNumber", "~antennaTemperature"]

data = pdbufr.read_bufr(path, columns=columns, filters=filters, reader="flat", prefilter_headers=True)
