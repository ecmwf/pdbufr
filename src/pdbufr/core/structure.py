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
    """Makes it possible to use context manager and is_coord method for all
    types of messages.
    """

    WRAP: T.Dict[T.Any, T.Any] = {}

    def __init__(self, d: T.Any):
        self.d = d
        self.wrap_enter = not hasattr(d, "__enter__")
        self.wrap_exit = not hasattr(d, "__exit__")
        self.wrap_is_coord = not hasattr(d, "is_coord")

    @staticmethod
    def wrap(m: T.Any) -> T.Any:
        t = type(m)
        w = MessageWrapper.WRAP.get(t, None)
        if w is None:
            w = not all(
                [
                    hasattr(m, "__enter__"),
                    hasattr(m, "__exit__"),
                    hasattr(m, "is_coord"),
                ]
            )

            MessageWrapper.WRAP[t] = w

        if not w:
            return m
        else:
            return MessageWrapper(m)

    def __enter__(self) -> T.Any:
        if self.wrap_enter:
            return self.d
        else:
            return self.d.__enter__()

    def __exit__(self, *args) -> None:  # type: ignore
        if self.wrap_exit:
            pass
        else:
            self.d.__exit__(*args)

    def __iter__(self):  # type: ignore
        return self.d.__iter__()

    def __getitem__(self, key: str) -> T.Any:
        return self.d[key]

    def __getattr__(self, fname):  # type: ignore
        def call_func(*args, **kwargs):  # type: ignore
            return getattr(self.d, fname, *args, **kwargs)

        return call_func

    def is_coord(self, key: str) -> bool:
        if self.wrap_is_coord:
            try:
                return bufr_code_is_coord(self.d[key + "->code"])
            except Exception:
                return False
        else:
            return self.d.is_coord(key)  # type: ignore


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

    message = MessageWrapper.wrap(message)
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
