# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os

import pdbufr

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, "perf_synop.bufr")

res = pdbufr.read_bufr(
    TEST_DATA,
    columns=[
        "latitude",
        "longitude",
        "data_datetime",
        "airTemperatureAt2M",
        "dewpointTemperatureAt2M",
    ],
)

print(len(res))
