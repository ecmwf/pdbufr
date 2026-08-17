# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import typing as T
import warnings

import pytest

import pdbufr
from pdbufr.utils.testing import sample_test_data_path

pd = pytest.importorskip("pandas")

# The message structure is the same in all the messages
# but some have #1#totalPrecipitationPast6Hours while
# others have #1#totalPrecipitationPast24Hours at the
# same position within the message
TEST_DATA_1 = sample_test_data_path("obs_3day.bufr")

TEST_DATA_2 = sample_test_data_path("synop_multi_subset_uncompressed.bufr")


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "columns",
    [
        tuple(),
        ("",),
        ("all",),
    ],
)
def test_read_flat_bufr_block_args_1(columns: T.Union[tuple, str], prefilter_headers: bool) -> None:
    res = pdbufr.read_bufr(TEST_DATA_1, *columns, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 103
    assert len(res) == 50


@pytest.mark.parametrize("prefilter_headers", [True, False])
@pytest.mark.parametrize(
    "columns",
    [[], "", [""], "all", ["all"]],
)
def test_read_flat_bufr_block_args_2(columns: dict, prefilter_headers: bool) -> None:

    res = pdbufr.read_bufr(TEST_DATA_1, columns=columns, flat=True, prefilter_headers=prefilter_headers)

    assert isinstance(res, pd.DataFrame)
    assert "edition" in res
    assert "#1#latitude" in res
    assert "#1#totalPrecipitationPast6Hours" in res
    assert "#1#totalPrecipitationPast24Hours" in res
    assert len(res.columns) == 103
    assert len(res) == 50


@pytest.mark.parametrize(
    "columns,err",
    [(3, TypeError), ([3], TypeError), ([3, 4], TypeError)],
)
def test_read_flat_bufr_block_args_bad(
    columns: T.Union[tuple, str],
    err: T.Type[Exception],
) -> None:

    with pytest.raises(err):
        pdbufr.read_bufr(TEST_DATA_1, columns, flat=True)


def test_read_flat_bufr_warning() -> None:
    def _find_warning(w: T.Any) -> bool:
        for item in w:
            if issubclass(
                item.category, UserWarning
            ) and "not all BUFR messages/subsets have the same structure" in str(item.message):
                return True
        return False

    # non-overlapping messages: warning generated
    with warnings.catch_warnings(record=True) as w:
        res = pdbufr.read_bufr(TEST_DATA_1, flat=True)
        assert len(res.columns) == 103
        assert len(res) == 50
        assert len(w) > 0
        assert _find_warning(w)

    # non-overlapping messages: warning disabled
    warnings.filterwarnings("ignore", module="pdbufr")
    with warnings.catch_warnings(record=True) as w:
        res = pdbufr.read_bufr(TEST_DATA_1, flat=True)
        assert len(res.columns) == 103
        assert len(res) == 50
        assert not _find_warning(w)

    # re-enables warnings
    warnings.filterwarnings("always", module="pdbufr")
    with warnings.catch_warnings(record=True) as w:
        res = pdbufr.read_bufr(TEST_DATA_1, flat=True)
        assert len(res.columns) == 103
        assert len(res) == 50
        assert len(w) > 0
        assert _find_warning(w)

    # overlapping messages: no warnings should be generated
    with warnings.catch_warnings(record=True) as w:
        res = pdbufr.read_bufr(TEST_DATA_2, flat=True)
        assert len(res.columns) == 101
        assert len(res) == 12
        assert not _find_warning(w)
