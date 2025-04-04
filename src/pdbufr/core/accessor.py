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


class CoordAccessor(SimpleAccessor):
    def __init__(self, coords=None, fixed_coords=None, period=None, fixed_period=None, **kwargs):
        super().__init__(**kwargs)

        self.mandatory = [*self.bufr_keys]

        # period coords
        self.fixed_period = fixed_period
        self.period_key = None
        self.period_bufr_key = None

        if fixed_period and period:
            raise ValueError("Cannot have both fixed_period and period")

        if period:
            self.period_bufr_key = period
            self.period_key = PARAMS.PeriodParameter("_period", period)
            self.keys[period] = self.period_key
            self.bufr_keys = [period, *self.bufr_keys]
            self.mandatory.append(period)

        self.coords = []
        if coords:
            for c in coords:
                coord_bufr_key = c[0]
                coord_suffix = c[1]
                coord_mandatory = c[2]
                self.coords.append(PARAMS.Parameter(self.labels[0] + "_<p>" + coord_suffix))
                self.keys[coord_bufr_key] = self.coord
                self.bufr_keys = [coord_bufr_key, *self.bufr_keys]
                if coord_mandatory:
                    self.mandatory.append(coord_bufr_key)

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
        if self.period:
            units_keys = [self.period_bufr_key]

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

        return self.relabel(value)


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
        add_coord=False,
        units_converter=None,
        add_units=False,
        **kwargs,
    ):
        skip = []
        print("add_coord=", add_coord)
        if not add_coord:
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


class ValueInPeriodAccessorBase(SimpleAccessor):
    coord_name = None

    def __init__(self, coord_key=None, coord_suffix="_level", **kwargs):
        super().__init__(**kwargs)
        self.coord = None
        self.period = None

        if coord_key:
            self.coord = PARAMS.Parameter(self.labels[0] + "_<p>" + coord_suffix)
            self.keys[coord_key] = self.coord
            self.bufr_keys = [coord_key, *self.bufr_keys]

    def relabel(self, value):
        if isinstance(value, dict):
            value = [value]

        res = {}
        for r in value:
            period = self.get_period(r)
            for k, v in r.items():
                if self.coord and k == self.coord.label:
                    label = self.coord.label.replace("<p>", period)
                    res[label] = v
                else:
                    label = k + "_" + period
                    res[label] = v
        return res

    @abstractmethod
    def get_period(self, record):
        pass

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
        units_keys = []
        if self.period:
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

        return self.relabel(value)


class ValueInPeriodAccessor(ValueInPeriodAccessorBase):
    coord_name = None

    def __init__(self, period_key=None, **kwargs):
        super().__init__(**kwargs)
        if not period_key:
            raise ValueError("period_key is required for ValueInPeriodAccessor")

        self.period = PARAMS.PeriodParameter("_period", period_key)
        self.keys[period_key] = self.period
        self.bufr_keys = [period_key, *self.bufr_keys]

    # def collect(
    #     self,
    #     collector,
    #     raise_on_missing=False,
    #     add_coord=False,
    #     units_converter=None,
    #     add_units=False,
    #     **kwargs,
    # ):
    #     skip = []
    #     if not add_coord and self.coord:
    #         skip = [self.coord]

    #     mandatory = self.bufr_keys
    #     units_keys = [self.period.bufr_key]

    #     value = self.collect_any(
    #         collector,
    #         mandatory=mandatory,
    #         skip=skip,
    #         raise_on_missing=raise_on_missing,
    #         units_keys=units_keys,
    #         units_converter=units_converter,
    #         add_units=add_units,
    #         first=False,
    #         **kwargs,
    #     )

    #     # encode period into the labels
    #     res = {}
    #     for r in value:
    #         period = r.pop("_period", None)
    #         if not period or period is None:
    #             period = "nan"

    #         for k, v in r.items():
    #             if self.coord and k == self.coord.label:
    #                 label = self.coord.label.replace("<p>", period)
    #                 res[label] = v
    #             elif add_units and k.endswith("_units"):
    #                 label = k[:-6] + "_" + period + "_units"
    #                 res[label] = v
    #             else:
    #                 label = k + "_" + period
    #                 res[label] = v

    #     return res

    def get_period(self, record):
        period = record.pop("_period", None)
        if not period or period is None:
            period = "nan"
        return period

    # def relabel(self, value, period):
    #     res = {}
    #     for k, v in value.items():
    #         if self.coord and k == self.coord.label:
    #             label = self.coord.label.replace("<p>", period)
    #             res[label] = v
    #         elif add_units and k.endswith("_units"):
    #             label = k[:-6] + "_" + period + "_units"
    #             res[label] = v
    #         else:
    #             label = k + "_" + period
    #             res[label] = v
    #     return res


class ValueInFixedPeriodAccessor(ValueInPeriodAccessorBase):
    def __init__(self, fixed_period=None, **kwargs):
        super().__init__(**kwargs)
        if not fixed_period:
            raise ValueError("fixed_period is required for ValueInFixedPeriodAccessor")
        self.fixed_period = fixed_period

    def get_period(self, record):
        return self.fixed_period

    # def collect(
    #     self,
    #     collector,
    #     raise_on_missing=False,
    #     add_coord=False,
    #     units_converter=None,
    #     add_units=False,
    #     **kwargs,
    # ):
    #     value = super().collect(collector, raise_on_missing=raise_on_missing, add_coord=add_coord)
    #     if isinstance(value, dict):
    #         value = [value]

    #     # encode period into the labels
    #     res = {}
    #     period = self.fixed_period
    #     for r in value:
    #         for r in value
    #             for k, v in r.items():
    #                 if self.coord and k == self.coord.label:
    #                     label = self.coord.label.replace("<p>", period)
    #                     res[label] = v
    #                 elif add_units and k.endswith("_units"):
    #                     label = k[:-6] + "_" + period + "_units"
    #                     res[label] = v
    #                 else:
    #                     label = k + "_" + period
    #                     res[label] = v

    #         return res


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


class MultiTryAccessorA(Accessor):
    accessors = []

    def empty_result(self):
        return self.accessors[0].empty_result()

    @property
    def needed_keys(self):
        r = []
        for a in self.accessors:
            r.extend(a.needed_keys)
        return r

    def _collect(self, name, value, level, units):
        if self.collected:
            return

        for a in self.accessors:
            if not a.collected:
                a._collect(name, value, level, units)
                if a.collected:
                    self.collected = True
                    return

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


# class PartAccessor(Accessor):
#     def __init__(self, coords=None, period=None, fixed_period=None, **kwargs):
#         super().__init__(**kwargs)
#         if len

#         self.keys = coords

#     def collect(self, collector, **kwargs):
#         res = {}
#         for p in self.parts:
#             r = p.collect(collector, **kwargs)
#             res.update(r)
#         return res

#     def empty_result(self):
#         res = {}
#         for p in self.parts:
#             r = p.empty_result()
#             res.update(r)
#         return res

#     @property
#     def needed_keys(self):
#         r = []
#         for p in self.parts:
#             r.extend(p.needed_keys)
#         return r


# class ComplexAccessor(Accessor):
#     parts = []

#     def collect(self, collector, **kwargs):
#         res = {}
#         bufr_keys = []
#         coords = []
#         for p in self.parts:
#             bufr_keys.extend(p.keys)
#             coords.extend(p.coords)


#         collector.collect_a()

#         for p in self.parts:
#             r = p.collect_a(collector, **kwargs)
#             res.update(r)
#         return res


class DataCollector:
    def __init__(self, accessor):
        self.accessor = accessor
        self.collected = True

        import collections

        self.result = []
        self.data = collections.OrderedDict({})
        self.current_levels = []
        self.failed_match_level = None

    def clear(self):
        import collections

        self.collected = False
        self.result = []
        self.data = collections.OrderedDict({})
        self.current_levels = []
        self.failed_match_level = None

    def _collect(self, name, value, level, units):
        if self.collected:
            return

        if name not in self.accessor.keys:
            return

        if self.failed_match_level is not None and level > self.failed_match_level:
            return

        if self.data and (
            # if all(name in current_observation for name in keys) and (
            level < self.current_levels[-1]
            or (level == self.current_levels[-1] and name in self.data)
        ):
            self.result.append(self.data)
            if not self.multi:
                self.collected = True
                return

        while len(self.data) and (
            level < self.current_levels[-1] or (level == self.current_levels[-1] and name in self.data)
        ):
            self.data.popitem()  # OrderedDict.popitem uses LIFO order
            self.current_levels.pop()

        self.data[name] = (value, units)

        # yield the last observation
        # if all(name in current_observation for name in filters):
        if self.data:  # and all(name in self.data for name in filters):
            # if not mandatory_keys or all(name in current_observation for name in mandatory_keys):
            self.result.append(dict(self.data))
            self.collected = True

    def _last_collect(self):
        if not self.collected:
            # yield the last observation
            # if all(name in current_observation for name in filters):
            if self.data:  # and all(name in self.data for name in filters):
                # if not mandatory_keys or all(name in current_observation for name in mandatory_keys):
                self.result.append(dict(self.data))
                self.collected = True


class CDataCollector(DataCollector):
    def _collect(self, name, value, level, units):
        if self.collected:
            return

        for a in self.accessors:
            if not a.collected:
                a._collect(name, value, level, units)
                if a.collected:
                    self.result = a.result
                    self.collected = True
                    return

    def _last_collect(self):
        if self.collected:
            return

        # yield the last observation
        # if all(name in current_observation for name in filters):
        if self.data:  # and all(name in self.data for name in filters):
            for a in self.accessors:
                if not a.collected:
                    a._last_collect()
                    if a.collected:
                        self.result = a.result
                        self.collected = True
                        return


class NewAccessor(Accessor):
    def __init__(self, multi=False, **kwargs):
        super().__init__(**kwargs)
        self.multi = multi
        self.collector = DataCollector(self)

    def get_data(
        self,
        mandatory=None,
        skip=None,
        raise_on_missing=False,
        units_converter=None,
        add_units=False,
    ):
        skip = skip or []
        mandatory = mandatory or []

        value = self.collector.result

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

                v, units = value.get(key, None)

                # convert units
                if v is not None and units_converter is not None and param.units:
                    v = units_converter.convert(label, v, units)

                # handle period
                if param.is_period():
                    period = v
                    if period is not None:
                        period = str(-period)
                        units = units or ""
                        period = period + units
                        v = period

                    # print(f"{label=} {period=} {value=}")

                res[label] = v

                # add units column
                if add_units and param.units:
                    res[label + "_units"] = units

        return res

    def collect(self, collector, **kwargs):
        pass

    # def _collect(self, name, value, level, units):
    #     if self.collected:
    #         return

    #     if name not in self.keys:
    #         return

    #     if self.failed_match_level is not None and level > self.failed_match_level:
    #         return

    #     if self.data and (
    #         # if all(name in current_observation for name in keys) and (
    #         level < self.current_levels[-1]
    #         or (level == self.current_levels[-1] and name in self.data)
    #     ):
    #         self.result.append(self.data)
    #         if not self.multi:
    #             return

    #     while len(self.data) and (
    #         level < self.current_levels[-1] or (level == self.current_levels[-1] and name in self.data)
    #     ):
    #         self.data.popitem()  # OrderedDict.popitem uses LIFO order
    #         self.current_levels.pop()

    #     self.data[name] = (value, units)

    #     # yield the last observation
    #     # if all(name in current_observation for name in filters):
    #     if self.data and all(name in current_observation for name in filters):
    #         if not mandatory_keys or all(name in current_observation for name in mandatory_keys):
    #             yield dict(current_observation)


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
