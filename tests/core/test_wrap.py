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

from pdbufr.core.structure import GetWrapper
from pdbufr.core.structure import IsCoordWrapper
from pdbufr.core.structure import MessageWrapper

MESSAGES = [
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


def _make_message_list(maker):
    class _MsgList:
        def __init__(self, d: T.Any) -> None:
            self.d = d

        def __iter__(self) -> T.Any:
            return iter(self.d)

    lst = _MsgList([maker(MESSAGES[0].copy()), maker(MESSAGES[1].copy())])
    return lst


@pytest.fixture
def input_data_wrap_context() -> T.Any:
    """Message class without context manager"""

    class _Msg:
        def __init__(self, d: T.Any) -> None:
            self.d = d
            self.codes = {
                "blockNumber": 1001,
                "stationNumber": 1002,
                "airTemperature": 12001,
                "dewpointTemperature": 12003,
            }

        # def __enter__(self) -> T.Any:
        #     return self

        # def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        #     pass

        def get(self, key: str, default=None) -> T.Any:
            return self.d.get(key)

        def __iter__(self) -> T.Any:
            return iter(self.d)

        def __getitem__(self, key: str) -> T.Any:
            return self.d[key]

        # def __setitem__(self, key: str, value: T.Any) -> None:
        #     self.d[key] = value

        def is_coord(self, key: str) -> bool:
            code = self.codes.get(key, None)
            return code is not None and code < 9999

    return _make_message_list(_Msg)


@pytest.fixture
def input_data_wrap_get() -> T.Any:
    """Message class without get method"""

    class _Msg:
        def __init__(self, d: T.Any) -> None:
            self.d = d
            self.codes = {
                "blockNumber": 1001,
                "stationNumber": 1002,
                "airTemperature": 12001,
                "dewpointTemperature": 12003,
            }
            self.context = None

        def __enter__(self) -> T.Any:
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
            if isinstance(self.context, dict):
                self.context["exited"] = True
                self.context = None

        # def get(self, key: str, default=None) -> T.Any:
        #     return self.d.get(key)

        def __iter__(self) -> T.Any:
            return iter(self.d)

        def __getitem__(self, key: str) -> T.Any:
            return self.d[key]

        # def __setitem__(self, key: str, value: T.Any) -> None:
        #     self.d[key] = value

        def is_coord(self, key: str) -> bool:
            code = self.codes.get(key, None)
            return code is not None and code < 9999

    return _make_message_list(_Msg)


@pytest.fixture
def input_data_wrap_is_coord() -> T.Any:
    """Message class without is_coord method"""

    class _Msg:
        def __init__(self, d: T.Any) -> None:
            self.d = d
            codes = {
                "blockNumber": 1001,
                "stationNumber": 1002,
                "airTemperature": 12001,
                "dewpointTemperature": 12003,
            }
            for k, v in codes.items():
                self.d[k + "->code"] = v

            self.context = None

        def __enter__(self) -> T.Any:
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
            if isinstance(self.context, dict):
                self.context["exited"] = True
                self.context = None

        def get(self, key: str, default=None) -> T.Any:
            return self.d.get(key)

        def __iter__(self) -> T.Any:
            return iter(self.d)

        def __getitem__(self, key: str) -> T.Any:
            return self.d[key]

        # def __setitem__(self, key: str, value: T.Any) -> None:
        #     self.d[key] = value

        # def is_coord(self, key: str) -> bool:
        #     code = self.codes.get(key, None)
        #     return code is not None and code < 9999

    return _make_message_list(_Msg)


@pytest.fixture
def input_data_wrap_context_and_get() -> T.Any:
    """Message class without context manager"""

    class _Msg:
        def __init__(self, d: T.Any) -> None:
            self.d = d
            self.codes = {
                "blockNumber": 1001,
                "stationNumber": 1002,
                "airTemperature": 12001,
                "dewpointTemperature": 12003,
            }

        # def __enter__(self) -> T.Any:
        #     return self

        # def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        #     pass

        # def get(self, key: str, default=None) -> T.Any:
        #     return self.d.get(key)

        def __iter__(self) -> T.Any:
            return iter(self.d)

        def __getitem__(self, key: str) -> T.Any:
            return self.d[key]

        # def __setitem__(self, key: str, value: T.Any) -> None:
        #     self.d[key] = value

        def is_coord(self, key: str) -> bool:
            code = self.codes.get(key, None)
            return code is not None and code < 9999

    return _make_message_list(_Msg)


def test_message_wrap_context(input_data_wrap_context) -> None:
    lst = input_data_wrap_context
    lst_iter = iter(lst)
    msg_in = next(lst_iter)

    assert not hasattr(msg_in, "__enter__")
    assert not hasattr(msg_in, "__exit__")

    ref = {"stationNumber": 128, "invalidKey": None}
    vals = dict()
    with MessageWrapper.wrap_context(msg_in) as msg:
        assert msg is msg_in
        assert np.isclose(msg.get("airTemperature"), 289.7)
        assert msg.get("stationNumber") == 128
        assert msg.is_coord("stationNumber")
        assert not msg.is_coord("airTemperature")
        for k in ref:
            assert msg.get(k, default=None) == ref[k]
            vals[k] = msg.get(k, default=None)

        with pytest.raises(KeyError):
            msg["invalidKey"]

    assert vals == ref


def test_message_wrap_get(input_data_wrap_get) -> None:
    lst = input_data_wrap_get
    lst_iter = iter(lst)
    msg_in = next(lst_iter)

    context = {}
    msg_in.context = context
    assert not hasattr(msg_in, "get")

    ref = {"stationNumber": 128, "invalidKey": None}
    vals = dict()
    with MessageWrapper.wrap_context(msg_in) as msg:
        assert isinstance(msg, GetWrapper)
        assert np.isclose(msg.get("airTemperature"), 289.7)
        assert msg.get("stationNumber") == 128
        assert msg["stationNumber"] == 128
        assert msg.is_coord("stationNumber")
        assert not msg.is_coord("airTemperature")
        for k in ref:
            assert msg.get(k, default=None) == ref[k]
            vals[k] = msg.get(k, default=None)

        with pytest.raises(KeyError):
            msg["invalidKey"]

    assert vals == ref
    assert context["exited"] is True


def test_message_wrap_is_coord(input_data_wrap_is_coord) -> None:
    lst = input_data_wrap_is_coord
    lst_iter = iter(lst)
    msg_in = next(lst_iter)

    context = {}
    msg_in.context = context
    assert not hasattr(msg_in, "is_coord")

    ref = {"stationNumber": 128, "invalidKey": None}
    vals = dict()
    with MessageWrapper.wrap_context(msg_in) as msg:
        assert isinstance(msg, IsCoordWrapper)
        assert np.isclose(msg.get("airTemperature"), 289.7)
        assert msg.get("stationNumber") == 128
        assert msg["stationNumber"] == 128
        assert msg.is_coord("stationNumber")
        assert not msg.is_coord("airTemperature")
        for k in ref:
            assert msg.get(k, default=None) == ref[k]
            vals[k] = msg.get(k, default=None)

        with pytest.raises(KeyError):
            msg["invalidKey"]

    assert vals == ref

    assert context["exited"] is True


def test_message_wrap_context_and_get(input_data_wrap_context_and_get) -> None:
    lst = input_data_wrap_context_and_get
    lst_iter = iter(lst)
    msg_in = next(lst_iter)

    assert not hasattr(msg_in, "__enter__")
    assert not hasattr(msg_in, "__exit__")
    assert not hasattr(msg_in, "get")

    ref = {"stationNumber": 128, "invalidKey": None}
    vals = dict()
    with MessageWrapper.wrap_context(msg_in) as msg:
        assert isinstance(msg, GetWrapper)
        assert msg is not msg_in
        assert np.isclose(msg.get("airTemperature"), 289.7)
        assert msg.get("stationNumber") == 128
        assert msg.is_coord("stationNumber")
        assert not msg.is_coord("airTemperature")
        for k in ref:
            assert msg.get(k, default=None) == ref[k]
            vals[k] = msg.get(k, default=None)

        with pytest.raises(KeyError):
            msg["invalidKey"]

    assert vals == ref
