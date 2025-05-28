# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import collections
from typing import Any
from typing import Container
from typing import Dict
from typing import Hashable
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Mapping
from typing import MutableMapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import eccodes  # type: ignore
import numpy as np

from pdbufr.core.filters import BufrFilter
from pdbufr.core.filters import filters_match
from pdbufr.core.keys import COMPUTED_KEYS
from pdbufr.core.keys import BufrKey
from pdbufr.core.structure import MessageWrapper
from pdbufr.core.structure import filter_keys_cached

from . import Reader


def extract_observations(
    message: Mapping[str, Any],
    filtered_keys: List[BufrKey],
    filters: Dict[str, BufrFilter] = {},
    base_observation: Dict[str, Any] = {},
) -> Iterator[Dict[str, Any]]:
    value_cache = {}
    try:
        is_compressed = bool(message["compressedData"])
    except KeyError:
        is_compressed = False

    if is_compressed:
        subset_count = message["numberOfSubsets"]
    else:
        subset_count = 1

    for subset in range(subset_count):
        current_observation: Dict[str, Any]
        current_observation = collections.OrderedDict(base_observation)
        current_levels: List[int] = [0]
        failed_match_level: Optional[int] = None

        for bufr_key in filtered_keys:
            level = bufr_key.level
            name = bufr_key.name

            if failed_match_level is not None and level > failed_match_level:
                continue

            # TODO: make into a function
            if all(name in current_observation for name in filters) and (
                level < current_levels[-1] or (level == current_levels[-1] and name in current_observation)
            ):
                # copy the content of current_items
                yield dict(current_observation)

            while len(current_observation) and (
                level < current_levels[-1] or (level == current_levels[-1] and name in current_observation)
            ):
                current_observation.popitem()  # OrderedDict.popitem uses LIFO order
                current_levels.pop()

            if bufr_key.key not in value_cache:
                try:
                    value_cache[bufr_key.key] = message[bufr_key.key]
                except KeyError:
                    value_cache[bufr_key.key] = None
            value = value_cache[bufr_key.key]

            # extract compressed BUFR values. They are either numpy arrays (for numeric types)
            # or lists of strings
            if (
                is_compressed
                and name != "unexpandedDescriptors"
                and isinstance(value, (np.ndarray, list))
                and len(value) == subset_count
            ):
                value = value[subset]

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

            current_observation[name] = value
            current_levels.append(level)

        # yield the last observation
        if all(name in current_observation for name in filters):
            yield dict(current_observation)


def add_computed_keys(
    observation: Dict[str, Any],
    included_keys: Container[str],
    filters: Dict[str, BufrFilter] = {},
) -> Dict[str, Any]:
    augmented_observation = observation.copy()
    for keys, computed_key, getter in COMPUTED_KEYS:
        if computed_key not in filters:
            if computed_key not in included_keys:
                continue
            computed_value = None
            try:
                computed_value = getter(observation, "", keys)
            except Exception:
                pass
            if computed_value:
                augmented_observation[computed_key] = computed_value
        else:
            if computed_key not in included_keys:
                return {}
            computed_value = None
            try:
                computed_value = getter(observation, "", keys)
            except Exception:
                pass
            if filters[computed_key].match(computed_value):
                augmented_observation[computed_key] = computed_value
            else:
                return {}

    return augmented_observation


def test_computed_keys(
    observation: Dict[str, Any],
    filters: Dict[str, BufrFilter] = {},
    prefix: str = "",
) -> bool:
    for keys, computed_key, getter in COMPUTED_KEYS:
        if computed_key in filters:
            computed_value = None
            try:
                computed_value = getter(observation, prefix, keys)
            except Exception:
                return False
            if computed_value is not None:
                if not filters[computed_key].match(computed_value):
                    return False
            else:
                return False
    return True


class GenericReader(Reader):
    def _stream_bufr(self, *args, **kwargs):
        return self._read(self.bufr_obj, *args, **kwargs)

    def __init__(
        self,
        path_or_messages,
        columns: Union[Sequence[str], str] = [],
        **kwargs: Any,
    ):
        """
        Generic reader for BUFR files.

        Parameters
        ----------
        :param columns: a list of BUFR keys to return in the DataFrame for every observation
        :param filters: a dictionary of BUFR key / filter definition to filter the observations to return
        :param required_columns: the list of BUFR keys that are required for all observations.
            ``True`` means all ``columns`` are required (default ``True``)
        :param prefilter_headers: filter the header keys before unpacking the data section (default ``False``)
        """
        super().__init__(path_or_messages, columns=columns, **kwargs)

    def read_records(
        self,
        bufr_obj: Iterable[MutableMapping[str, Any]],
        columns: Union[Sequence[str], str] = [],
        filters: Mapping[str, Any] = {},
        required_columns: Union[bool, Iterable[str]] = True,
        prefilter_headers: bool = False,
    ) -> Iterator[Dict[str, Any]]:

        if isinstance(columns, str):
            columns = (columns,)

        if required_columns is True:
            required_columns = set(columns)
        elif required_columns is False:
            required_columns = set()
        elif isinstance(required_columns, Iterable):
            required_columns = set(required_columns)
        else:
            raise TypeError("required_columns must be a bool or an iterable")

        filters = dict(filters)

        value_filters = {k: BufrFilter.from_user(filters[k], key=k) for k in filters}
        included_keys = set(value_filters)
        included_keys |= set(columns)
        computed_keys = []
        for keys, computed_key, _ in COMPUTED_KEYS:
            if computed_key in included_keys:
                included_keys |= set(keys)
                computed_keys.append(computed_key)

        if "count" in value_filters:
            max_count = value_filters["count"].max()
        else:
            max_count = None

        keys_cache: Dict[Tuple[Hashable, ...], List[BufrKey]] = {}
        for count, msg in enumerate(bufr_obj, 1):
            # we use a context manager to automatically delete the handle of the BufrMessage.
            # We have to use a wrapper object here because a message can also be a dict
            with MessageWrapper.wrap(msg) as message:
                if "count" in value_filters and not value_filters["count"].match(count):
                    continue

                if prefilter_headers:
                    # test header keys for failed matches before unpacking
                    if not filters_match(message, value_filters, required=False):
                        continue

                message["skipExtraKeyAttributes"] = 1
                message["unpack"] = 1

                filtered_keys = filter_keys_cached(message, keys_cache, included_keys)
                if "count" in included_keys:
                    observation = {"count": count}
                else:
                    observation = {}

                value_filters_without_computed = {
                    k: v for k, v in value_filters.items() if k not in computed_keys
                }

                for observation in extract_observations(
                    message,
                    filtered_keys,
                    value_filters_without_computed,
                    observation,
                ):
                    augmented_observation = add_computed_keys(observation, included_keys, value_filters)
                    data = {k: v for k, v in augmented_observation.items() if k in columns}
                    if required_columns.issubset(data):
                        yield data

                # optimisation: skip decoding messages above max_count
                if max_count is not None and count >= max_count:
                    break

    def adjust_dataframe(self, df):
        return df


reader = GenericReader


def stream_bufr(bufr_obj, *args, **kwargs):
    reader = GenericReader(bufr_obj, *args, **kwargs)
    return reader.read_records(bufr_obj, **reader._kwargs)
