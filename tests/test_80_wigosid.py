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
    ],
)
def test_wigos_id_core(wid) -> None:
    assert wid.as_str() == "0-705-0-1931"
    assert wid.as_tuple() == (0, 705, 0, "1931")
    assert wid == "0-705-0-1931"
    assert wid == (0, 705, 0, "1931")
    assert wid == [0, 705, 0, "1931"]


@pytest.mark.parametrize(
    "wid",
    [
        (0, 705, 0, "1931"),
        [0, 705, 0, "1931"],
        ("0", "705", "0", "1931"),
        (0, 705, "0", 1931),
        "0-705-0-1931",
    ],
)
def test_wigos_id_from_user(wid) -> None:
    w = WIGOSId.from_user(wid)

    assert w.as_str() == "0-705-0-1931"
    assert w == WIGOSId(0, 705, 0, "1931")
