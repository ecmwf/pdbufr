# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from typing import Any
from typing import Dict

Z = "z"
ZH = "zh"
G = 9.80665  # m/s^2, standard acceleration of gravity


def compute_z(d: Dict[str, Any]) -> Dict[str, Any]:
    z = d.get(Z, None)
    if z is None:
        zh = d.get(ZH, None)
        if zh is not None:
            z = zh * G
            d[Z] = z
        else:
            d[Z] = None

    return d


def compute_zh(d: Dict[str, Any]) -> Dict[str, Any]:
    zh = d.get(ZH, None)
    if zh is None:
        z = d.get(Z, None)
        if z is not None:
            zh = z / G
            d[ZH] = zh
        else:
            d[ZH] = None

    return d


METHODS = {
    "z": compute_z,
    "zh": compute_zh,
    "both": lambda d: compute_zh(compute_z(d)),
    "raw": None,
}


class GeopotentialHandler:
    def __init__(self, mode: str = "geopotential") -> None:
        if mode not in METHODS:
            raise ValueError(f"Invalid mode '{mode}'. Valid modes are: {list(METHODS.keys())}")
        self.method = METHODS[mode]

    def __call__(self, d: Dict[str, Any]) -> Dict[str, Any]:
        return self.method(d) if self.method else d
