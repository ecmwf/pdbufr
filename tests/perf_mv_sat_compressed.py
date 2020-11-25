import os

import metview as mv

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
