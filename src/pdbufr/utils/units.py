# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import ABCMeta
from abc import abstractmethod
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

# Mapping from BUFR units str to Pint units str.
# The rest of the units are handled by Pint.
# See https://github.com/hgrecco/pint/blob/db0247017fd9bd2445db13b694d766880b7e3c20/pint/default_en.txt
PINT_UNITS = {
    "Bq l-1": "Bq/l",
    "Bq m-3": "Bq/m^3",
    "C": "degC",
    "cd m-2": "cd/m^2",
    "g g-1": "g/g",
    "g kg-1": "g/kg",
    "g m-3": "g/m^3",
    "gpm": "m",
    "J kg-1": "J/kg",
    "J m-2": "J/m^2",
    # "K m s-1": "K m/s",
    "kg kg-1": "kg/kg",
    "km h-1": "km/h",
    "kg m-2": "kg/m^2",
    "m s-1": "m/s",
    "m s-2": "m/s^2",
    "m s-3": "m/s^3",
    "m2 s-1": "m^2/s",
    "m2 s-2": "m^2/s^2",
    "m3 m-3": "m^3/m^3",
    "m3 s-1": "m^3/s",
    "mg kg-1": "mg/kg",
    "mm h-1": "mm/h",
    "mol mol-1": "mol/mol",
    "Pa s-1": "Pa/s",
    "W m-2": "W/m^2",
    # "W m-2 nm-1": "W/m^2/nm",
}


class UnitsConverter(metaclass=ABCMeta):
    def __init__(self) -> None:
        from pint import UnitRegistry

        ureg = UnitRegistry()
        self._Q = ureg.Quantity

    @staticmethod
    def pint_units(units: str) -> str:
        return PINT_UNITS.get(units, units)

    @abstractmethod
    def convert(self, label: str, value: Union[int, float], units: str) -> Tuple[Union[int, float], str]:
        pass

    @staticmethod
    def make(
        unit_system: Optional[str], units: Optional[Union[str, Dict[str, str]]] = None
    ) -> "UnitsConverter":
        base = None
        if unit_system is not None:
            if unit_system == "pdbufr":
                base = DefaultUnitsConverter()
            elif unit_system == "si":
                base = SIUnitsConverter()
            else:
                raise ValueError(f"Unknown unit system: {unit_system}")

        if units is None:
            units = {}

        if isinstance(units, dict) and units:
            return UserUnitsConverter({**units}, base=base)

        if not isinstance(units, dict):
            raise ValueError(f"Cannot create units converter for {units=}. Must be a dict or None.")

        return base


class SIUnitsConverter(UnitsConverter):
    def __init__(self) -> None:
        super().__init__()

    def convert(
        self, label: str, value: Union[int, float], units: str, default_units: Optional[str] = None
    ) -> Tuple[Union[int, float], str]:
        pv = self._Q(value, self.pint_units(units))
        r = pv.to_base_units()
        return r.magnitude, f"{r.units:~}"


class DefaultUnitsConverter(UnitsConverter):
    DEFAULTS = None

    def __init__(self) -> None:
        super().__init__()
        if DefaultUnitsConverter.DEFAULTS is None:
            from pdbufr.core.param import UNITS

            DefaultUnitsConverter.DEFAULTS = {**UNITS}

    def convert(self, label: str, value: Union[int, float], units: str) -> Tuple[Union[int, float], str]:
        default_units = self.DEFAULTS.get(label, None)
        if default_units is not None:
            if default_units == units:
                return value, units
            else:
                p_src_units = self.pint_units(units)
                p_target_units = self.pint_units(default_units)
                print(f"DefaultUnitsConverter: {label=} {units=}{p_src_units=} {p_target_units=}")
                if value is None or p_target_units == p_src_units:
                    return value, default_units
                return self._Q(value, p_src_units).to(p_target_units).magnitude, default_units
        return value, units


class UserUnitsConverter(DefaultUnitsConverter):
    def __init__(self, target_units: Optional[Dict[str, str]], base: Optional[UnitsConverter] = None) -> None:
        super().__init__()
        self.base = base
        self.bufr_target_units = target_units or {}
        self.pint_target_units = {k: self.pint_units(v) for k, v in self.bufr_target_units.items()}

    def convert(
        self,
        label: str,
        value: Union[int, float],
        units: str,
    ) -> Tuple[Union[int, float], str]:
        p_target_units = self.pint_target_units.get(label, None)
        if p_target_units is not None:
            b_target_units = self.bufr_target_units[label]
            print(f"UserUnitsConverter: {label=} {units=} {p_target_units=} {b_target_units=}")
            if b_target_units == units:
                return value, units
            else:
                p_src_units = self.pint_units(units)
                if value is None or p_target_units == p_src_units:
                    return value, b_target_units
                return self._Q(value, p_src_units).to(p_target_units).magnitude, b_target_units
        elif self.base is not None:
            return self.base.convert(label, value, units)
        return value, units
