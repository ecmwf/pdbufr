# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


def compare_df(df, num_rows, ref_rows, ref):
    assert len(df) == num_rows

    if num_rows > 0:
        import numpy as np
        import pandas as pd

        assert list(df.columns) == list(ref[0].keys())
        # assert len(df) == num_rows

        # assert .iloc[0].to_dict() == names[0], res.iloc[0].to_dict()
        # assert res.iloc[2].to_dict() == names[1], res.iloc[2].to_dict()
        df_ref = pd.DataFrame.from_dict(ref)
        df_ref.reset_index(drop=True, inplace=True)

        # df = df.replace(np.nan, None)
        df = df.replace({None: np.nan})
        df_ref = df_ref.replace({None: np.nan})

        # df = df.reset_index(drop=True)
        df = df.iloc[ref_rows].reset_index(drop=True)

        # print("df=", df)
        # print("df_ref=", df_ref)

        try:
            pd.testing.assert_frame_equal(
                df, df_ref, check_dtype=False, check_index_type=False, check_datetimelike_compat=True
            )
        except Exception as e:
            print("e=", e)
            raise
