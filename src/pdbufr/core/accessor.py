# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from abc import ABCMeta
from abc import abstractmethod

import pdbufr.core.param as PARAMS
from pdbufr.core.keys import COMPUTED_KEYS


class Accessor(metaclass=ABCMeta):
    keys = None
    param = None
    mandatory = None

    def __init__(self, keys=None):
        """
        Accessor class to extract values from a BUFR message.

        Parameters
        ----------
        keys : dict, str, list of str, optional
            Mapping between the keys to extract and the corresponding Parameters. When None, the
            static ``keys`` member is used. When not a dict, it is converted to a dict with the
            same key(s) and value(s).
        """
        if keys is None:
            self.keys = self.keys
            if self.keys:
                self.keys = {**self.keys}
            else:
                self.keys = {}
        else:
            self.keys = keys

        assert isinstance(self.keys, dict)

        if self.param is None:
            if len(self.keys) == 1:
                self.param = list(self.keys.values())[0]
            # else:
            #     raise ValueError("Accessor must define a 'param' member")

        self.bufr_keys = list([k for k in self.keys.keys() if not k.startswith("_")])
        self.labels = [v.label for k, v in self.keys.items() if v is not None]
        self.name = self.__class__.__name__

    @abstractmethod
    def empty_result(self):
        pass

    @property
    @abstractmethod
    def needed_keys(self):
        pass

    @abstractmethod
    def collect(self, collector, **kwargs):
        pass


class SimpleAccessor(Accessor):
    def empty_result(self):
        return dict(zip(self.labels, [None] * len(self.labels)))

    @property
    def needed_keys(self):
        return self.bufr_keys

    def collect(self, collector, raise_on_missing=False, units_converter=None, add_units=False, **kwargs):
        return self.collect_any(
            collector,
            raise_on_missing=raise_on_missing,
            units_converter=units_converter,
            add_units=add_units,
            **kwargs,
        )

    def parse_collected(self, value, skip, units_converter, add_units, raise_on_missing):
        if value is None:
            value = {}

        if raise_on_missing and (not value or all(v is None for v in value.values())):
            raise ValueError(f"Missing value for {self.name}")

        res = {}
        for key, param in self.keys.items():
            if param is not None:
                if param.is_fixed():
                    res[param.label] = param.value
                else:
                    label = param.label
                    if param in skip:
                        continue

                    v, units = value.get(key, (None, None))

                    # convert units
                    if v is not None and units_converter is not None and param.units:
                        print("units_converter", label, units, v, param.units)
                        v, units = units_converter.convert(label, v, units)

                    # handle period
                    if param.is_period():
                        v = param.concat_units(v, units)
                        # period = v
                        # if period is not None:
                        #     period = str(-period)
                        #     # units = value.get(key + "->units", "")
                        #     period = period + units
                        #     v = period

                        # print(f"{label=} {period=} {value=}")

                    res[label] = v

                    # add units column
                    if add_units and param.units:
                        res[label + "_units"] = units

        return res

    def collect_any(
        self,
        collector,
        mandatory=None,
        skip=None,
        raise_on_missing=False,
        units_keys=None,
        units_converter=None,
        add_units=False,
        first=True,
        **kwargs,
    ):
        value = None
        mandatory = mandatory or []
        skip = skip or []

        units_keys = units_keys or []
        if units_converter is not None or add_units:
            units_keys.extend(self.bufr_keys)

        multi_res = []

        for v in collector.collect(self.bufr_keys, {}, mandatory_keys=mandatory, units_keys=units_keys):
            value = v
            res = self.parse_collected(value, skip, units_converter, add_units, raise_on_missing)
            if first:
                return res
            else:
                multi_res.append(res)

        if first:
            if raise_on_missing:
                raise ValueError(f"Missing value for {self.name} {self.bufr_keys}")
            return {}
        else:
            return multi_res


class ComputedKeyAccessor(Accessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        key = list(self.keys.keys())[0]
        assert isinstance(key, str)
        for k in COMPUTED_KEYS:
            if k[1] == key:
                self._meth = k[2]
                self._keys = k[0]

        if not hasattr(self, "_meth"):
            raise ValueError(f"Unknown computed key {self.keys[0]}")

    def empty_result(self):
        return dict(zip(self.labels, [None] * len(self.labels)))

    @property
    def needed_keys(self):
        return self._keys

    def collect(self, collector, raise_on_missing=False, **kwargs):
        value = None
        for v in collector.collect(self._keys, {}, value_and_units=False):
            value = v
            break

        try:
            val = self._meth(value, "", self._keys)
        except Exception:
            if raise_on_missing:
                raise
            val = None

        if val is None and raise_on_missing:
            raise ValueError(f"Missing value for {self.name}")

        return {self.labels[0]: val}


class CoordAccessor(SimpleAccessor):
    period_placeholder = "<p>"

    def __init__(self, coords=None, fixed_coords=None, period=None, fixed_period=None, first=True, **kwargs):
        super().__init__(**kwargs)

        self.mandatory = [*self.bufr_keys]
        self.first = first

        # period coords
        # self.fixed_period = fixed_period
        self.period_bufr_key = None
        self.period = None

        if fixed_period and period:
            raise ValueError("Cannot have both fixed_period and period")

        if period:
            self.period_bufr_key = period
            self.period = PARAMS.PeriodParameter("_period")
            self.keys[period] = self.period
            self.bufr_keys = [period, *self.bufr_keys]
            self.mandatory.append(period)
        elif fixed_period:
            self.period = PARAMS.FixedParameter("_period", fixed_period)
            self.keys["_period"] = self.period

        # other coords
        self.coords = []

        if fixed_coords and coords:
            raise ValueError("Cannot have both fixed_coords and coords")

        if coords:
            for c in coords:
                coord_bufr_key = c[0]
                coord_suffix = c[1]
                coord_mandatory = c[2]
                if self.period:
                    label = self.labels[0] + "_" + self.period_placeholder + "_" + coord_suffix
                else:
                    label = self.labels[0] + "_" + coord_suffix
                self.coords.append(PARAMS.Parameter(label))
                self.keys[coord_bufr_key] = self.coords[-1]
                self.bufr_keys = [coord_bufr_key, *self.bufr_keys]
                if coord_mandatory:
                    self.mandatory.append(coord_bufr_key)
        elif fixed_coords:
            coord_suffix = "level"
            if self.period:
                label = self.labels[0] + "_" + self.period_placeholder + "_" + coord_suffix
            else:
                label = self.labels[0] + "_" + coord_suffix
            self.coords.append(PARAMS.FixedParameter(label, fixed_coords))
            self.keys["_fixed_coord"] = self.coords[-1]

    def get_period(self, record):
        period = record.pop("_period", None)
        if not period or period is None:
            period = "nan"
        return period

    def relabel(self, value):
        if isinstance(value, dict):
            value = [value]

        res = {}
        for r in value:
            period = self.get_period(r)
            for k, v in r.items():
                for coord in self.coords:
                    if coord and k == coord.label:
                        label = coord.label.replace(self.period_placeholder, period)
                        res[label] = v
                    else:
                        label = k + "_" + period
                        res[label] = v
        return res

    def collect(
        self,
        collector,
        raise_on_missing=False,
        add_coord=False,
        units_converter=None,
        add_units=False,
        **kwargs,
    ):
        skip = []
        if not add_coord:
            skip = self.coords

        mandatory = self.mandatory

        units_keys = []
        if self.period_bufr_key:
            units_keys = [self.period_bufr_key]

        value = self.collect_any(
            collector,
            mandatory=mandatory,
            skip=skip,
            raise_on_missing=raise_on_missing,
            units_keys=units_keys,
            units_converter=units_converter,
            add_units=add_units,
            first=self.first,
            **kwargs,
        )

        if self.period:
            value = self.relabel(value)

        return value


class MultiAccessorBase(Accessor):
    accessors = []

    def empty_result(self):
        return self.accessors[0].empty_result()

    @property
    def needed_keys(self):
        r = []
        for a in self.accessors:
            r.extend(a.needed_keys)
        return r


class MultiFirstAccessor(MultiAccessorBase):
    def collect(self, collector, **kwargs):
        for a in self.accessors:
            try:
                r = a.collect(collector, raise_on_missing=True, **kwargs)
                if r:
                    return r
            except Exception:
                # print("MultiTryAccessor.collect  exception", e)
                pass
                # raise

        return self.empty_result()


class MultiAllAccessor(MultiAccessorBase):
    def collect(self, collector, **kwargs):
        res = {}
        for a in self.accessors:
            r = a.collect(collector, raise_on_missing=False, **kwargs)
            if r:
                res.update(r)

        if res:
            return res
        return self.empty_result()


class LatLonAccessor(SimpleAccessor):
    param = PARAMS.LATLON
    keys = {"latitude": PARAMS.LAT, "longitude": PARAMS.LON}


class SidAccessor(MultiFirstAccessor):
    param = PARAMS.SID
    accessors = [
        ComputedKeyAccessor(keys={"WMO_station_id": PARAMS.SID}),
        ComputedKeyAccessor(keys={"WIGOS_station_id": PARAMS.SID}),
        SimpleAccessor(keys={"shipOrMobileLandStationIdentifier": PARAMS.SID}),
        SimpleAccessor(keys={"station_id": PARAMS.SID}),
    ]


class ElevationAccessor(MultiFirstAccessor):
    param = PARAMS.ELEVATION
    accessors = [
        SimpleAccessor(keys={"heightOfStationGroundAboveMeanSeaLevel": PARAMS.ELEVATION}),
        SimpleAccessor(keys={"heightOfStation": PARAMS.ELEVATION}),
    ]


class DatetimeAccessor(ComputedKeyAccessor):
    param = PARAMS.TIME
    keys = {"data_datetime": PARAMS.TIME}


class AccessorManager:
    def __init__(self, core_accessors, user_accessors, default_user_accessors=None):
        if default_user_accessors is None:
            default_user_accessors = user_accessors

        self.accessors = set([*core_accessors, *user_accessors, *default_user_accessors])
        aa = {}
        for a in self.accessors:
            aa[a.param.label] = a()
        self.accessors = aa
        # self.accessors = {a.param.label: a() for a in self.accessors}

        def _build(lst):
            return {a.param.label: self.accessors[a.param.label] for a in lst}

        self.core = _build(core_accessors)
        self.user = _build(user_accessors)
        self.default_user = _build(default_user_accessors)
        self.default = {**self.core, **self.default_user}

        self.cache = {}

    def get(self, params):
        if params is None:
            accessors = self.default
        else:
            cache_key = tuple(params)
            if cache_key in self.cache:
                accessors = self.cache[cache_key]
            else:
                if isinstance(params, str):
                    params = [params]
                v = list(params)
                accessors = {**self.core}
                for p in v:
                    if p in self.user:
                        accessors[p] = self.user[p]
                    else:
                        raise ValueError(f"Unsupported parameter '{p}'")

                self.cache[cache_key] = accessors

        assert accessors is not None

        return accessors

    def get_by_object(self, accessor):
        if not issubclass(accessor, Accessor):
            raise ValueError(f"Invalid accessor type={type(accessor)}")
        label = accessor.param.label
        return self.accessors[label]
