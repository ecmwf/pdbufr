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

        print("Accessor.__init__", self.__class__.__name__)

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

    @staticmethod
    def _output(name, value):
        if isinstance(name, str):
            return {name: value}
        elif isinstance(name, (tuple, list)):
            return dict(zip(name, value))

    def collect_first(self, labels, keys, collector):
        value = None
        print("collect keys=", keys)
        for v in collector.collect(keys, {}):
            print("collect v=", v)
            value = v
            break

        if value is None:
            value = {}

        r = {}
        for kv, lv in zip(keys, labels):
            if labels is not None:
                r[lv] = value.get(kv, None)
        return r


class SimpleAccessor(Accessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def empty_result(self):
        return dict(zip(self.labels, [None] * len(self.labels)))

    @property
    def needed_keys(self):
        return self.bufr_keys

    def collect(self, collector, raise_on_missing=False, units_converter=None, add_units=False, **kwargs):
        return self.collect_first(
            collector,
            raise_on_missing=raise_on_missing,
            units_converter=units_converter,
            add_units=add_units,
            **kwargs,
        )
        # value = None
        # units_keys = None

        # if units_converter is not None or add_units:
        #     units_keys = self.key_names

        # for v in collector.collect(self.key_names, {}, units_keys=units_keys):
        #     value = v
        #     break

        # if value is None:
        #     value = {}

        # r = {}
        # for key, param in self.keys.items():
        #     if param is not None:
        #         label = param.label
        #         v = value.get(key, None)

        #         units = None
        #         if v is not None and units_converter is not None and param.units:
        #             units = value.get(key + "->units", "")
        #             v = units_converter.convert(label, v, units)

        #         r[label] = v

        #         if add_units and param.units:
        #             if units is None:
        #                 units = value.get(key + "->units", "")
        #             r[label + "_units"] = units

        # if raise_on_missing and all(v is None for v in value.values()):
        #     raise ValueError(f"Missing value for {self.name}")

        # return r

    def collect_first(
        self,
        collector,
        mandatory=None,
        skip=None,
        raise_on_missing=False,
        units_converter=None,
        add_units=False,
        **kwargs,
    ):
        value = None
        units_keys = None
        mandatory = mandatory or []
        skip = skip or []

        if units_converter is not None or add_units:
            units_keys = self.key_names

        for v in collector.collect(self.key_names, {}, mandatory_keys=mandatory, units_keys=units_keys):
            value = v
            break

        if value is None:
            value = {}

        r = {}
        for key, param in self.keys.items():
            if param is not None:
                label = param.label
                if param in skip:
                    continue

                v = value.get(key, None)

                units = None
                if v is not None and units_converter is not None and param.units:
                    units = value.get(key + "->units", "")
                    v = units_converter.convert(label, v, units)

                r[label] = v

                if add_units and param.units:
                    if units is None:
                        units = value.get(key + "->units", "")
                    r[label + "_units"] = units

        if raise_on_missing and all(v is None for v in value.values()):
            raise ValueError(f"Missing value for {self.name}")

        return r


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
    coord_name = None

    def __init__(self, coord_bufr_key=None, **kwargs):
        super().__init__(**kwargs)
        self.coord = PARAMS.Param(self.labels[0] + "_level", coord_bufr_key)
        self.keys = {**self.keys, self.coord.label: self.coord}
        self.bufr_keys = [self.coord.key, *self.bufr_keys]
        # self.coord_label = self.labels[0] + "_level"

    # def empty_result(self):
    #     name = [*self.labels, self.coord.label]
    #     value = [None] * (len(name) + 1)
    #     return self._output(name, value)

    # @property
    # def needed_keys(self):
    #     return [*self.bufr_keys, self.coord.key]

    def collect(
        self,
        collector,
        raise_on_missing=False,
        add_height=False,
        units_converter=None,
        add_units=False,
        **kwargs,
    ):

        if not add_height:
            skip = [self.coord]

        mandatory = [self.bufr_keys]

        return self.collect_first(
            collector,
            mandatory=mandatory,
            skip=skip,
            raise_on_missing=raise_on_missing,
            units_converter=units_converter,
            add_units=add_units,
            **kwargs,
        )

        # print("collect ValueAtCoordAccessor", self.keys)

        # value = {}
        # # keys = [self.coord_bufr_key, *self.keys]
        # # labels = self.labels
        # # labels = [*labels, self.coord_label]

        # units_keys = None
        # if units_converter is not None or add_units:
        #     units_keys = self.bufr_keys

        # for v in collector.collect(keys, {}, mandatory_keys=keys, units_keys=units_keys):
        #     value = v
        #     break

        # keys = [*self.keys, self.coord_key]
        # # labels = [*self.labels, self.coord_name]
        # r = {}
        # for key, lv in zip(
        #     keys,
        # ):
        #     if labels is not None:
        #         v = value.get(kv, None)
        #         units = None

        #         if v is not None and units_converter is not None and param.units:
        #             units = value.get(key + "->units", "")
        #             v = units_converter.convert(label, v, units)

        #         r[lv] = v

        #         if add_units and kv in self.keys:
        #             units = value.get(kv + "->units", "")
        #             r[lv + "_units"] = units

        # r = {lv: value.get(kv, None) for kv, lv in zip(keys, labels)}

        # if raise_on_missing and all(v is None for v in r.values()):
        #     raise ValueError(f"Missing value for {self.labels}")
        # # name = [*self.name, self.coord_name]

        # return r

        # value = collector.collect_at_coord(self.keys, self.coord_key)
        # print("  -> value=", value)
        # if raise_on_missing and all(v is None for v in value[:-1]):
        #     raise ValueError(f"Missing value for {self.name}")
        # name = [*self.name, self.coord_name]
        # return self._output(name, value)


class ValueInPeriodAccessor(SimpleAccessor):
    coord_name = None

    def __init__(self, coord_key=None, coord_label=None, period_key=None, **kwargs):
        super().__init__(**kwargs)
        print("ValueInPeriodAccessor.__init__", self.keys)
        self.coord_key = coord_key
        self.coord_label = coord_label or self.labels[0] + "_level"
        self.period_key = period_key

    @property
    def needed_keys(self):
        v = [*self.keys, self.coord_key, self.period_key]
        return [x for x in v if x is not None]

    def collect(self, collector, coord_label=None, raise_on_missing=False, labels=None, **kwargs):
        print("collect ValueInPeriodAccessor", self.keys)

        # value = {}
        keys = [self.coord_key, self.period_key, *self.keys]
        keys = [k for k in keys if k is not None]
        if labels is None:
            labels = self.labels

        r = []

        obs = {}
        print("collect keys=", keys)
        for v in collector.collect(keys, {}, mandatory_keys=self.keys, units_keys=[self.period_key]):
            print("collect v=", v)
            period = v.get(self.period_key, None)
            if period is not None:
                period = str(-period)
                units = v.get(self.period_key + "->units", "")
                period = period + units

            for label, key in zip(labels, self.keys):
                label = label + "_" + period
                obs[label] = v.get(key, None)

            r.append(obs)
            print("  - >obs=", obs)

        # print("  - >value=", value)
        # keys = [*self.keys, self.coord_key]
        # # labels = [*self.labels, self.coord_name]
        # r = {lv: value.get(kv, None) for kv, lv in zip(keys, labels)}
        # print("  -> r=", r)

        # if raise_on_missing and all(v is None for v in r.values()):
        #     raise ValueError(f"Missing value for {self.labels}")
        # # name = [*self.name, self.coord_name]

        return obs


class ValueAtFixedCoordAccessor(SimpleAccessor):
    def __init__(self, fixed_coord=None, **kwargs):
        super().__init__(**kwargs)
        self.coord = PARAMS.FixedParam(self.labels[0] + "_level", value=fixed_coord)

        # self.fixed_coord = fixed_coord
        # self.coord_name = coord_name or self.labels[0] + "_level"

    # def collect(
    #     self,
    #     collector,
    #     raise_on_missing=False,
    #     add_height=False,
    #     units_converter=None,
    #     add_units=False,
    #     **kwargs,
    # ):

    #     if not add_height:
    #         skip = [self.coord]

    #     mandatory = [self.bufr_keys]

    #     return self.collect_first(
    #         collector,
    #         mandatory=mandatory,
    #         skip=skip,
    #         raise_on_missing=raise_on_missing,
    #         units_converter=units_converter,
    #         add_units=add_units,
    #         **kwargs,
    #     )

    # def empty_result(self):
    #     name = [*self.labels, self.coord_name]
    #     return self._output(name, [None] * (len(self.labels) + 1))

    def collect(self, collector, add_height=False, **kwargs):
        r = super().collect(collector, **kwargs)
        if add_height:
            r[self.coord.label] = self.coord.value
        return r

        # # if raise_on_missing and all(v is None for v in value):
        # #     raise ValueError(f"Missing value for {self.labels}")

        # name = [*self.labels, self.coord_name]
        # return self._output(name, value + [self.fixed_coord])


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
                r = a.collect(collector, raise_on_missing=True)
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
