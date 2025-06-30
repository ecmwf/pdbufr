# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import pytest

from pdbufr import WIGOSId


@pytest.mark.parametrize(
    "wid",
    [
        WIGOSId(0, 705, 0, "1931"),
        WIGOSId(series=0, issuer=705, number=0, local="1931"),
        WIGOSId.from_str("0-705-0-1931"),
        WIGOSId.from_iterable([0, 705, 0, "1931"]),
        WIGOSId.from_iterable((0, 705, 0, "1931")),
        WIGOSId.from_iterable(("0", "705", "0", "1931")),
    ],
)
def test_wigos_id_core(wid) -> None:
    assert wid.as_str() == "0-705-0-1931"
    assert wid.as_tuple() == (0, 705, 0, "1931")
    assert wid == "0-705-0-1931"
    assert wid == (0, 705, 0, "1931")
    assert wid == [0, 705, 0, "1931"]


@pytest.mark.parametrize(
    "wid,err",
    [
        ((0, 705, 0, "1931"), None),
        ([0, 705, 0, "1931"], None),
        (("0", "705", "0", "1931"), None),
        ((0, 705, "0", "1931"), None),
        ((0, 705, "0", 1931), ValueError),
        ((0, 705, 0, 1931), ValueError),
        ("0-705-0-1931", None),
        ("705-0-1931", ValueError),
        ("-0---0-1931", ValueError),
    ],
)
def test_wigos_id_from_user(wid, err) -> None:
    if err is None:
        w = WIGOSId.from_user(wid)

        assert w.as_str() == "0-705-0-1931"
        assert w == WIGOSId(0, 705, 0, "1931")
    else:
        with pytest.raises(err):
            WIGOSId.from_user(wid)


@pytest.mark.parametrize(
    "wid1,wid2,eq",
    [
        ((0, 705, 0, "1931"), (0, 705, 0, "01931"), False),
        ((0, 705, 0, "1931"), (0, 705, "00", "1931"), True),
        ((0, 705, 0, "1931"), (0, "0705", "00", "1931"), True),
    ],
)
def test_wigos_id_eq(wid1, wid2, eq) -> None:
    w1 = WIGOSId.from_user(wid1)
    w2 = WIGOSId.from_user(wid2)
    if eq:
        assert w1 == w2
    else:
        assert w1 != w2


@pytest.mark.parametrize(
    "wid,valid",
    [
        ((0, 705, 0, "1931"), True),
        ((None, None, None, "1931"), False),
        ((None, 705, 0, "1931"), False),
        ((None, None, 0, "1931"), False),
        ((0, None, None, "1931"), False),
        ((0, None, 0, "1931"), False),
        ((0, 705, None, "1931"), False),
        ((0, 705, 0, None), False),
    ],
)
def test_wigos_id_valid(wid, valid) -> None:
    w1 = WIGOSId.from_user(wid)
    assert w1.is_valid() == valid
