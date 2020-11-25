import os

import metview as mv

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, "perf_aircraft.bufr")

f = mv.read(TEST_DATA)

gpt = mv.bufr_filter(
    data=f,
    output="csv",
    parameter_count=3,
    parameter_1="airTemperature",
    parameter_2="windSpeed",
    parameter_3="windDirection",
    missing_data="include",
)

res = gpt.to_dataframe()
print(len(res))
