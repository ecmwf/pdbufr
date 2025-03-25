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
from pdbufr.bufr_structure import COMPUTED_KEYS


class Accessor(metaclass=ABCMeta):
    keys = None
    param = None

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

        self.bufr_keys = list(self.keys.keys())
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
                label = param.label
                if param in skip:
                    continue

                v = value.get(key, None)

                # convert units
                units = None
                if v is not None and units_converter is not None and param.units:
                    units = value.get(key + "->units", "")
                    v = units_converter.convert(label, v, units)

                # handle period
                if param.is_period():
                    period = v
                    if period is not None:
                        period = str(-period)
                        units = value.get(key + "->units", "")
                        period = period + units
                        v = period

                    # print(f"{label=} {period=} {value=}")

                res[label] = v

                # add units column
                if add_units and param.units:
                    if units is None:
                        units = value.get(key + "->units", "")
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
                raise ValueError(f"Missing value for {self.name}")
            return {}
        else:
            return multi_res


class ComputedKeyAccessor(Accessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # assert len(self.name) == 1
        # self.name = self.name[0]

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
        for v in collector.collect(self._keys, {}):
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


class ValueAtCoordAccessor(SimpleAccessor):
    def __init__(self, coord_key=None, coord_suffix="_level", **kwargs):
        super().__init__(**kwargs)
        self.coord = PARAMS.Parameter(self.labels[0] + coord_suffix)
        self.keys = {**self.keys, coord_key: self.coord}
        self.bufr_keys = [coord_key, *self.bufr_keys]

    def collect(
        self,
        collector,
        raise_on_missing=False,
        add_height=False,
        units_converter=None,
        add_units=False,
        **kwargs,
    ):
        skip = []
        if not add_height:
            skip = [self.coord]

        mandatory = self.bufr_keys

        return self.collect_any(
            collector,
            mandatory=mandatory,
            skip=skip,
            raise_on_missing=raise_on_missing,
            units_converter=units_converter,
            add_units=add_units,
            **kwargs,
        )


class ValueAtFixedCoordAccessor(SimpleAccessor):
    def __init__(self, fixed_coord=None, coord_suffix="_level", **kwargs):
        super().__init__(**kwargs)
        self.coord = PARAMS.FixedParameter(self.labels[0] + coord_suffix, fixed_coord)

    def collect(self, collector, add_coord=False, **kwargs):
        r = super().collect(collector, **kwargs)
        if add_coord:
            r[self.coord.label] = self.coord.value
        return r


class ValueInPeriodAccessor(SimpleAccessor):
    coord_name = None

    def __init__(self, coord_key=None, coord_suffix="_level", period_key=None, **kwargs):
        super().__init__(**kwargs)
        self.coord = None
        self.period = None

        if coord_key:
            self.coord = PARAMS.Parameter(self.labels[0] + "_<p>" + coord_suffix)
            self.keys[coord_key] = self.coord
            self.bufr_keys = [coord_key, *self.bufr_keys]

        if period_key:
            self.period = PARAMS.PeriodParameter("_period", period_key)
            self.keys[period_key] = self.period
            self.bufr_keys = [period_key, *self.bufr_keys]
        else:
            raise ValueError("period_key is required for ValueInPeriodAccessor")

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
        if not add_coord and self.coord:
            skip = [self.coord]

        mandatory = self.bufr_keys
        units_keys = [self.period.bufr_key]

        value = self.collect_any(
            collector,
            mandatory=mandatory,
            skip=skip,
            raise_on_missing=raise_on_missing,
            units_keys=units_keys,
            units_converter=units_converter,
            add_units=add_units,
            first=False,
            **kwargs,
        )

        # encode period into the labels
        res = {}
        for r in value:
            period = r.pop("_period", None)
            if not period or period is None:
                period = "nan"

            for k, v in r.items():
                if self.coord and k == self.coord.label:
                    label = self.coord.label.replace("<p>", period)
                    res[label] = v
                elif add_units and k.endswith("_units"):
                    label = k[:-6] + "_" + period + "_units"
                    res[label] = v
                else:
                    label = k + "_" + period
                    res[label] = v

        return res


class MultiTryAccessor(Accessor):
    accessors = []

    def empty_result(self):
        return self.accessors[0].empty_result()

    @property
    def needed_keys(self):
        r = []
        for a in self.accessors:
            r.extend(a.needed_keys)
        return r

    def collect(self, collector, **kwargs):
        for a in self.accessors:
            print("  p=", a)
            try:
                r = a.collect(collector, raise_on_missing=True, **kwargs)
                print("  -> r=", r)
                return r
            except Exception as e:
                print("MultiTryAccessor.collect  exception", e)
                pass

        return self.empty_result()


class LatLonAccessor(SimpleAccessor):
    param = PARAMS.LATLON
    keys = {"latitude": PARAMS.LAT, "longitude": PARAMS.LON}


class SidAccessor(MultiTryAccessor):
    param = PARAMS.SID
    accessors = [
        ComputedKeyAccessor(keys={"WMO_station_id": PARAMS.SID}),
        ComputedKeyAccessor(keys={"WIGOS_station_id": PARAMS.SID}),
        SimpleAccessor(keys={"shipOrMobileLandStationIdentifier": PARAMS.SID}),
        SimpleAccessor(keys={"station_id": PARAMS.SID}),
    ]


class ElevationAccessor(MultiTryAccessor):
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
            print("AccessorManager.__init__", a.param.label)
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
                v = list(params)
                accessors = {**self.core}
                for p in v:
                    if p in self.user:
                        accessors[p] = self.user[p]
                    else:
                        raise ValueError(f"Unsupported parameter '{p}'")

                cache_key[cache_key] = accessors

        assert accessors is not None

        return accessors
