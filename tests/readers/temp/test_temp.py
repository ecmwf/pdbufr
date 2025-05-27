# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import numpy as np
import pandas as pd

import pdbufr
from pdbufr.utils.testing import sample_test_data_path


def _get_data():
    import os
    import sys

    here = os.path.dirname(__file__)
    sys.path.insert(0, here)
    import _temp_ref_data

    return _temp_ref_data


DATA = _get_data()


def test_temp_reader():
    df = pdbufr.read_bufr(sample_test_data_path("temp_small.bufr"), reader="temp", filters={"count": 1})

    # r = df.to_dict()
    # print("r=", r)
    # print("r=", type(r["time"][0]))
    # assert False

    # use this to create ref
    # import json

    # r = df.to_json(date_format="iso", orient="records")
    # parsed = json.loads(r)
    # print("parsed=", parsed)
    # assert False

    df_ref = pd.DataFrame.from_dict(DATA.REF)
    df_ref.reset_index(drop=True, inplace=True)
    df = df.replace(np.nan, None)

    # print("df=", df.columns.tolist())
    # print("df_ref=", df_ref.columns.tolist())

    try:
        pd.testing.assert_frame_equal(
            df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
        )
    except Exception as e:
        print("e=", e)
        raise
