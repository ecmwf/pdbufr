# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import typing as T

import numpy as np
import pytest

pd = pytest.importorskip("pandas")

from pdbufr import read_bufr  # noqa: E402

assert_frame_equal = pd.testing.assert_frame_equal


def build_message_list() -> T.Any:
    messages = [
        {
            "edition": 3,
            "masterTableNumber": 0,
            "numberOfSubsets": 1,
            "unexpandedDescriptors": 0,
            "blockNumber": 1,
            "stationNumber": 128,
            "airTemperature": 289.7,
            "dewpointTemperature": 285.16,
        },
        {
            "edition": 4,
            "masterTableNumber": 1,
            "numberOfSubsets": 1,
            "unexpandedDescriptors": 1,
            "stationNumber": 129,
            "airTemperature": 249.1,
            "dewpointTemperature": 140.12,
        },
    ]

    class _Msg:
        def __init__(self, d: T.Any) -> None:
            self.d = d
            self.codes = {
                "blockNumber": 1001,
                "stationNumber": 1002,
                "airTemperature": 12001,
                "dewpointTemperature": 12003,
            }

        def __enter__(self) -> T.Any:
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
            pass

        def __iter__(self) -> T.Any:
            return iter(self.d)

        def __getitem__(self, key: str) -> T.Any:
            return self.d[key]

        def __setitem__(self, key: str, value: T.Any) -> None:
            self.d[key] = value

        def is_coord(self, key: str) -> bool:
            code = self.codes.get(key, None)
            return code is not None and code < 9999

    class _MsgList:
        def __init__(self, d: T.Any) -> None:
            self.d = d

        def __iter__(self) -> T.Any:
            return iter(self.d)

    lst = _MsgList([_Msg(messages[0]), _Msg(messages[1])])
    return lst


def test_message_list_1() -> None:
    lst = build_message_list()
    res = read_bufr(lst, columns=("airTemperature"))

    ref = {"airTemperature": np.array([289.7, 249.1])}
    ref = pd.DataFrame.from_dict(ref)

    assert_frame_equal(res, ref)


def test_message_list_2() -> None:
    lst = build_message_list()
    res = read_bufr(lst, columns=("airTemperature"), filters={"stationNumber": 129})

    ref = {"airTemperature": np.array([249.1])}
    ref = pd.DataFrame.from_dict(ref)

    assert_frame_equal(res, ref)
