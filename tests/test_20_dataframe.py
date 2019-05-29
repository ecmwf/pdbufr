
import os

import pandas as pd

from pdbufr import read_bufr


SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'sample-data')
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, 'obs_3day.bufr')


def test_read_bufr():
    res = read_bufr(TEST_DATA, selections=('latitude',))

    assert isinstance(res, pd.DataFrame)
    assert 'latitude' in res
    assert len(res) == 50

    res = read_bufr(TEST_DATA, selections=('latitude',), header_filters={'rdbtimeTime': '115557'})

    assert len(res) == 6

    res = read_bufr(TEST_DATA, selections=('latitude',), data_filters={'cloudAmount': 2})

    assert len(res) == 6
