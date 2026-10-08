# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os

import metview as mv  # type: ignore

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, "perf_sat_compressed.bufr")

f = mv.read(TEST_DATA)

gpt = mv.bufr_filter(
    data=f,
    output="csv",
    parameter_count=2,
    parameter_1="significandOfVolumetricMixingRatio",
    parameter_2="nonCoordinatePressure",
    coordinate_count=1,
    coordinate_1="firstOrderStatistics",
    coordinate_operator_1="=",
    coordinate_value_1=15,
    extract_mode="all",
)

res = gpt.to_dataframe()
print(len(res))
