# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import collections
import typing as T

import eccodes
import numpy as np


class Collector:
    def __init__(self, message, filtered_keys, subset):
        self.message = message
        self.filtered_keys = filtered_keys
        self.subset = subset
        self.keys = [k.key for k in filtered_keys]
        self.cache = {}
        self.is_compressed = False

    # first
    def _collect_one(self, key):
        for bufr_key in self.filtered_keys:
            name = bufr_key.name
            if name == key:
                try:
                    v = self.message.get(bufr_key.key)
                    if self.subset > 0:
                        v = v[self.subset]
                except Exception:
                    v = None
                return v

    def _collect_multi(self, keys):
        res = {k: None for k in keys}
        cnt = 0
        for bufr_key in self.filtered_keys:
            name = bufr_key.name
            if name in keys:
                try:
                    v = self.message.get(bufr_key.key)
                    if self.subset > 0:
                        v = v[self.subset]
                except Exception:
                    v = None
                res[name] = v
                cnt += 1

            if cnt == len(keys):
                break
        return list(res).values()

        # if key in self.cache:
        #     return self.cache[key]
        # try:
        #     v = self.message.get(key)
        # except Exception:
        #     v = None
        # self.cache[key] = v
        # print("collect_one key=", key, "v=", v)
        # return v

    def collect_one(self, key):
        return self._collect_one(key)

    # def collect(self, keys):
    #     if isinstance(keys, str):
    #         return self._collect_one(keys)
    #     return [self._collect_one(k) for k in keys]

    # def collect(self, keys, valid_only=False, as_dict=False):
    #     if isinstance(keys, str):
    #         return self._collect_one(keys)
    #     else:
    #         if as_dict:
    #             r = {}
    #             for k in keys:
    #                 v = self._collect_one(k)
    #                 if v is not None or not valid_only:
    #                     r[k] = v
    #             return r
    #         else:
    #             r = []
    #             for i, k in enumerate(keys):
    #                 v = self._collect_one(k)
    #                 if v is not None or not valid_only:
    #                     r.append(v)
    #             return r

    # def collect_multi(self, keys, valid_only=False):
    #     r = {}
    #     print("multi keys=", keys)
    #     for k in keys:
    #         v = self._collect_one(k)
    #         if v is not None or not valid_only:
    #             r[k] = v
    #     print("multi r=", r)
    #     return r

    def collect_at_coord(self, key, coord_key):
        if isinstance(key, str):
            return self._collect_at_coord_one(key, coord_key)
        else:
            return self._collect_at_coord_multi(key, coord_key)

        # last_coord = None
        # for bufr_key in self.filtered_keys:
        #     level = bufr_key.level
        #     name = bufr_key.name

        #     if name == coord_key:
        #         last_coord = bufr_key

        #     if name == key and last_coord is not None and last_coord.level <= level:
        #         print("collect_level key=", bufr_key, "coord_key=", coord_key)
        #         coord_value = self._collect_one(last_coord.key)
        #         return self._collect_one(bufr_key.key), coord_value

        # return None, None

    def _collect_at_coord_one(self, key, coord_key):
        last_coord = None
        for bufr_key in self.filtered_keys:
            level = bufr_key.level
            name = bufr_key.name

            if name == coord_key:
                last_coord = bufr_key

            if name == key and last_coord is not None and last_coord.level <= level:
                coord_value = self._collect_one(last_coord.key)
                return self._collect_one(bufr_key.key), coord_value

        return None, None

    def _collect_at_coord_multi(self, key, coord_key):
        last_coord = None
        used_coord = None
        coord_value = None
        r = {}
        keys = set(key)
        for bufr_key in self.filtered_keys:
            level = bufr_key.level
            name = bufr_key.name

            # print("name=", name)

            if name == coord_key:
                last_coord = bufr_key

            if name in keys:
                # print("  name=", name, "last_coord=", last_coord, "used_coord=", used_coord)
                if used_coord is not None:
                    if used_coord.key == last_coord.key:
                        r[name] = self._collect_one(bufr_key.key)
                        keys.remove(name)

                else:
                    if last_coord is not None and last_coord.level <= level:
                        used_coord = last_coord
                        r[name] = self._collect_one(bufr_key.key)
                        keys.remove(name)
                        coord_value = self._collect_one(last_coord.key)

            if len(key) == len(r):
                v = [r[k] for k in key]
                v.append(self._collect_one(last_coord.key))
                return v

            if used_coord and used_coord.level != last_coord.level:
                break

        v = [r.get(k, None) for k in key]
        v.append(coord_value)
        return v

    def collect(self, keys, filters, mandatory_keys=None, units_keys=None):
        value_cache = {}
        current_observation: T.Dict[str, T.Any]
        current_levels: T.List[int] = [0]
        failed_match_level: T.Optional[int] = None

        current_observation: T.Dict[str, T.Any]
        current_observation = collections.OrderedDict({})

        for bufr_key in self.filtered_keys:
            level = bufr_key.level
            name = bufr_key.name

            if failed_match_level is not None and level > failed_match_level:
                continue

            # TODO: make into a function
            if current_observation and (
                # if all(name in current_observation for name in keys) and (
                level < current_levels[-1]
                or (level == current_levels[-1] and name in current_observation)
            ):
                if not mandatory_keys or all(name in current_observation for name in mandatory_keys):

                    # copy the content of current_items
                    yield dict(current_observation)

            while len(current_observation) and (
                level < current_levels[-1] or (level == current_levels[-1] and name in current_observation)
            ):
                current_observation.popitem()  # OrderedDict.popitem uses LIFO order
                current_levels.pop()

            if bufr_key.key not in value_cache:
                try:
                    value_cache[bufr_key.key] = self.message[bufr_key.key]
                except KeyError:
                    value_cache[bufr_key.key] = None
            value = value_cache[bufr_key.key]

            # extract compressed BUFR values. They are either numpy arrays (for numeric types)
            # or lists of strings
            if (
                self.is_compressed
                and name != "unexpandedDescriptors"
                and isinstance(value, (np.ndarray, list))
                and len(value) == self.subset_count
            ):
                value = value[self.subset]

            if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
                value = None
            elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
                value = None

            if name in filters:
                if filters[name].match(value):
                    failed_match_level = None
                else:
                    failed_match_level = level
                    continue

            if name in keys:
                current_observation[name] = value
                if units_keys and name in units_keys:
                    try:
                        v = self.message[bufr_key.key + "->units"]
                    except KeyError:
                        v = None
                    current_observation[name + "->units"] = v
            current_levels.append(level)

        # yield the last observation
        # if all(name in current_observation for name in filters):
        if current_observation and all(name in current_observation for name in filters):
            if not mandatory_keys or all(name in current_observation for name in mandatory_keys):
                yield dict(current_observation)
