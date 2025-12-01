# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import collections
import typing as T

from pdbufr.core.keys import IS_KEY_COORD
from pdbufr.core.keys import BufrKey
from pdbufr.high_level_bufr.bufr import bufr_code_is_coord


class MessageWrapper:
    """Makes it possible to use context manager and additional wrapped methods for all
    types of messages.
    """

    UNWRAPPED_CONTEXT: T.Set[T.Any] = set()
    UNWRAPPED_METHODS: T.Set[T.Any] = set()

    def __init__(self, d: T.Any, wrappers: T.List[T.Any] = []) -> None:
        self.d = d
        self.wrappers = wrappers

    @staticmethod
    def wrap_context(m: T.Any) -> T.Any:
        """Wrap message with context manager and additional methods if needed.

        Parameters
        ----------
        m : Any
            Message object to wrap.

        The object is wrapped to ensure it supports context management, i.e., the `with` statement,
        it has a `get` method, and an `is_coord` method. If the message already has these capabilities,
        it is returned as is. Otherwise, it is wrapped with the appropriate wrappers.

        The returned object is immediately supposed to be used as part of a `with` statement.

        Example:
            with MessageWrapper.wrap_context(message) as msg:
                # use msg here
        """
        t = type(m)
        if t not in MessageWrapper.UNWRAPPED_CONTEXT:
            wrappers = []
            if not hasattr(m, "get"):
                wrappers.append(GetWrapper)
            if not hasattr(m, "is_coord"):
                wrappers.append(IsCoordWrapper)

            if wrappers or not (hasattr(m, "__enter__") and hasattr(m, "__exit__")):
                m = MessageWrapper(m, wrappers=wrappers)

            else:
                MessageWrapper.UNWRAPPED_CONTEXT.add(t)

        return m

    @staticmethod
    def wrap_methods(m: T.Any) -> T.Any:
        """Wrap message with additional methods if needed.

        Parameters
        ----------
        m : Any
            Message object to wrap.

        The object is wrapped to ensure it has the `get` and `is_coord` methods.
        If the message already has these capabilities, it is returned as is. Otherwise, it
        is wrapped with the appropriate wrappers. The returned object is not supposed to be
        used in a `with` statement.

        Example:
            msg = MessageWrapper.wrap_methods(message)
            msg.get("key")
            msg.get("key", None)
            msg.is_coord("key")

        """
        t = type(m)
        if t not in MessageWrapper.UNWRAPPED_METHODS:
            wrapped = False
            if not hasattr(m, "get"):
                m = GetWrapper(m)
                wrapped = True
            if not hasattr(m, "is_coord"):
                m = IsCoordWrapper(m)
                wrapped = True

            if not wrapped:
                MessageWrapper.UNWRAPPED_METHODS.add(t)

        return m

    def __getattr__(self, name):
        return getattr(self.d, name)

    def __iter__(self):  # type: ignore
        return self.d.__iter__()

    def __getitem__(self, key: str) -> T.Any:
        return self.d[key]

    def __setitem__(self, key: str, value: T.Any) -> None:
        self.d[key] = value

    def __enter__(self) -> T.Any:
        if hasattr(self.d, "__enter__"):
            r = self.d.__enter__()
        else:
            r = self.d

        for w in self.wrappers:
            r = w(r)
        return r

    def __exit__(self, *args) -> None:  # type: ignore
        if hasattr(self.d, "__exit__"):
            self.d.__exit__(*args)
        else:
            pass


class GetWrapper(MessageWrapper):
    def get(self, key, default=None):
        try:
            return self.d[key]
        except KeyError:
            return default


class IsCoordWrapper(MessageWrapper):
    def is_coord(self, key: str) -> bool:
        try:
            c = self.d[key + "->code"]
            return bufr_code_is_coord(c)
        except Exception:
            return False


class IsCoordCache:
    """Caches if a BUFR key is a coordinate descriptor"""

    def __init__(self, message: T.Any) -> None:
        self.message = message
        self.cache: T.Dict[str, bool] = {}

    def check(self, key: str, name: str) -> bool:
        c = self.cache.get(name, None)
        if c is None:
            if name in IS_KEY_COORD:
                c = IS_KEY_COORD[name]
                self.cache[name] = c
                return c
            else:
                try:
                    c = self.message.is_coord(key)
                    self.cache[name] = c
                    return c
                except Exception:
                    return False
        return c


def message_structure(message: T.Any) -> T.Iterator[T.Tuple[int, str]]:
    level = 0
    coords: T.Dict[str, int] = collections.OrderedDict()

    message = MessageWrapper.wrap_methods(message)
    is_coord_cache = IsCoordCache(message)

    for key in message:
        name = key.rpartition("#")[2]

        is_coord = is_coord_cache.check(key, name)
        while is_coord and name in coords:
            _, level = coords.popitem()  # OrderedDict.popitem uses LIFO order

        yield (level, key)

        if is_coord:
            coords[name] = level
            level += 1


def filter_keys(
    message: T.Mapping[str, T.Any],
    include: T.Container[str] = (),
) -> T.Iterator[BufrKey]:
    for level, key in message_structure(message):
        bufr_key = BufrKey.from_level_key(level, key)
        if include == () or bufr_key.name in include or bufr_key.key in include:
            yield bufr_key


def make_message_uid(message: T.Mapping[str, T.Any]) -> T.Tuple[T.Optional[int], ...]:
    message_uid: T.Tuple[T.Optional[int], ...]

    message_uid = (
        message["edition"],
        message["masterTableNumber"],
        message["numberOfSubsets"],
    )

    descriptors: T.Union[int, T.List[int]] = message["unexpandedDescriptors"]
    if isinstance(descriptors, int):
        message_uid += (descriptors, None)
    else:
        message_uid += tuple(descriptors) + (None,)

    delayed_keys = (
        "delayedDescriptorReplicationFactor",
        "shortDelayedDescriptorReplicationFactor",
        "extendedDelayedDescriptorReplicationFactor",
    )

    for k in delayed_keys:
        try:
            delayed_descriptors = message[k]
        except KeyError:
            delayed_descriptors = []

        if isinstance(delayed_descriptors, int):
            message_uid += (delayed_descriptors, None)
        else:
            message_uid += tuple(delayed_descriptors) + (None,)

    return message_uid


def filter_keys_cached(
    message: T.Mapping[str, T.Any],
    cache: T.Dict[T.Tuple[T.Hashable, ...], T.List[BufrKey]],
    include: T.Iterable[str] = (),
) -> T.List[BufrKey]:
    message_uid = make_message_uid(message)
    include_uid = tuple(sorted(include))
    filtered_message_uid: T.Tuple[T.Hashable, ...] = message_uid + include_uid
    if filtered_message_uid not in cache:
        cache[filtered_message_uid] = list(filter_keys(message, include_uid))
    return cache[filtered_message_uid]


def filter_keys_1(
    message: T.Mapping[str, T.Any],
    columns: T.Container[str] = (),
) -> T.Iterator[BufrKey]:

    message = MessageWrapper.wrap_methods(message)
    found_cnt = 0
    for key in message:
        if key in columns:
            columns[key] = True  # access to ensure key exists
            found_cnt += 1

        if found_cnt >= len(columns):
            return


def filter_keys_cached_1(
    message: T.Mapping[str, T.Any],
    cache: T.Dict[T.Tuple[T.Hashable, ...], T.List[BufrKey]],
    include: T.Iterable[str] = (),
) -> T.List[BufrKey]:
    message_uid = make_message_uid(message)
    include_uid = tuple(sorted(include))
    filtered_message_uid: T.Tuple[T.Hashable, ...] = message_uid + include_uid
    if filtered_message_uid not in cache:
        cache[filtered_message_uid] = list(filter_keys_1(message, include_uid))
    return cache[filtered_message_uid]


class BufrHeader:
    def __init__(self, message, columns, filters) -> None:
        """Wraps a BUFR message header with filtering capabilities.

        Parameters
        ----------
        message : Any
            The BUFR message to wrap. It must be unpacked. For performance reasons, the class does not check
            if the message is unpacked. The caller is responsible for ensuring this.
        filters : Dict[str, BufrFilter]
            Filters to apply on the message keys. The header related filters are extracted
            from this dictionary and stored internally.
        """
        SKIP = {"unexpandedDescriptors"}
        self.message = message
        # assert not message.get("unpack")
        self.keys = [k for k in self.message if k not in SKIP]

        columns = columns or {}
        self.columns = []
        for k, c in columns.items():
            if k in self.keys or c.header_only:
                self.columns.append(c)

        # self.columns = [col for col in columns if col in self.keys or col.header_only]
        self._columns_values = None

        filters = filters or dict()
        self.filters = {}
        for k, f in filters.items():
            if k in self.keys or f.header_only:
                self.filters[k] = f

        self._matched = None
        self._filters_values = dict()

    def __contains__(self, key: str) -> bool:
        return key in self.keys

    def _get(self, key: str) -> T.Any:
        import eccodes

        print("Getting header key:", key)

        value = self.message.get(key)
        print(" -> header key:", key, "value:", value)

        # print(" -> header key:", key, "value:", value)
        if isinstance(value, float) and value == eccodes.CODES_MISSING_DOUBLE:
            value = None
        elif isinstance(value, int) and value == eccodes.CODES_MISSING_LONG:
            value = None

        return value

    def last_key(self) -> str:
        if self.keys:
            return self.keys[-1]
        return None

    def columns_values(self) -> T.Dict[str, T.Any]:
        if self._columns_values is None:
            self._columns_values = {c.name: c.get_value(self._get, ranked=False) for c in self.columns}
        return self._columns_values

    def _filter(self) -> None:
        for f in self.filters.values():
            value = f.column.get_value(self._get, ranked=False)
            print(" -> header filter:", f, "name:", f.name, "value:", value)
            if value is not None and f.match(value):
                self._filters_values[f.column.name] = value
            else:
                return False
        return True

    def match_filters(self) -> bool:
        if self._matched is None:
            self._matched = self._filter()
        return self._matched

    def filters_values(self) -> T.Dict[str, T.Any]:
        if self.match_filters():
            return self._filters_values
        return {}

    def values(self) -> T.Dict[str, T.Any]:
        res = {}
        for key in self.keys:
            name = key
            value = self._get(key)
            res[name] = value
        return res


# def add_computed_keys(
#     observation: T.Dict[str, T.Any],
#     included_keys: T.Container[str],
#     filters: T.Dict[str, bufr_filters.BufrFilter] = {},
# ) -> T.Dict[str, T.Any]:
#     augmented_observation = observation.copy()
#     for keys, computed_key, getter in COMPUTED_KEYS:
#         if computed_key not in filters:
#             if computed_key not in included_keys:
#                 continue
#             computed_value = None
#             try:
#                 computed_value = getter(observation, "", keys)
#             except Exception:
#                 pass
#             if computed_value:
#                 augmented_observation[computed_key] = computed_value
#         else:
#             if computed_key not in included_keys:
#                 return {}
#             computed_value = None
#             try:
#                 computed_value = getter(observation, "", keys)
#             except Exception:
#                 pass
#             if filters[computed_key].match(computed_value):
#                 augmented_observation[computed_key] = computed_value
#             else:
#                 return {}

#     return augmented_observation


# def test_computed_keys(
#     observation: T.Dict[str, T.Any],
#     filters: T.Dict[str, bufr_filters.BufrFilter] = {},
#     prefix: str = "",
# ) -> bool:
#     for keys, computed_key, getter in COMPUTED_KEYS:
#         if computed_key in filters:
#             computed_value = None
#             try:
#                 computed_value = getter(observation, prefix, keys)
#             except Exception:
#                 return False
#             if computed_value is not None:
#                 if not filters[computed_key].match(computed_value):
#                     return False
#             else:
#                 return False
#     return True
