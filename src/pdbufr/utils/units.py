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

# Mapping from BUFR units to Pint units
PINT_UNITS = {
    "Bq l-1": "Bq/l",
    "Bq m-3": "Bq/m^3",
    "C": "degC",
    "cd m-2": "cd/m^2",
    "g g-1": "g/g",
    "g kg-1": "g/kg",
    "g m-3": "g/m^3",
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
    def __init__(self):
        from pint import UnitRegistry

        ureg = UnitRegistry()
        self._Q = ureg.Quantity

    @staticmethod
    def pint_units(units):
        return PINT_UNITS.get(units, units)

    @abstractmethod
    def convert(self, label, value, units):
        pass

    @staticmethod
    def make(target_units=None):
        if isinstance(target_units, str):
            if target_units.lower() == "si":
                return SIUnitsConverter()
        elif isinstance(target_units, dict):
            return SimpleUnitsConverter(target_units)

        raise ValueError(f"Cannot create units converter for {target_units=}")


class SIUnitsConverter(UnitsConverter):
    def __init__(self):
        super().__init__()

    def convert(self, label, value, units):
        pv = self._Q(value, self.pint_units(units))
        r = pv.to_base_units()
        return r.magnitude, f"{r.units:~}"


class SimpleUnitsConverter(SIUnitsConverter):
    def __init__(self, target_units=None):
        super().__init__()
        self.target_units = target_units or {}

    def convert(self, label, value, units):
        if value is None or not self.target_units:
            return value

        if label in self.target_units:
            t_units = self.target_units[label]
            if t_units == units:
                return value, units
            else:
                p_t_units = self.pint_units(t_units)
                p_s_units = self.pint_units(units)
                if p_t_units == p_s_units:
                    return value, units
                return self._Q(value, p_s_units).to(p_t_units).magnitude, t_units
        else:
            return super().convert(label, value, units)
