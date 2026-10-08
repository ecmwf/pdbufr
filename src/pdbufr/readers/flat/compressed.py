# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import numpy as np

from .missing import convert_missing


class CompressedValueCache:
    def __init__(self, message, subset_count):
        self.cache = {}
        self.multi_cache = {}
        self.subset_cache = {}
        self.multi_subset_cache = {}
        self.message = message
        self.subset_count = subset_count

    def get_all_subsets(self, key):
        """Return all the values of a key with a concrete rank at once.

        Parameters
        ----------
        key: str
            The BUFR key to read. Must contain a rank, e.g. "#1#latitude".

        Returns
        -------
        values: list or Any
            When ``per_subset`` is True this is a list with one value per subset,
            otherwise it is the single value shared by all the subsets.
        per_subset: bool
            Whether ``values`` holds a separate value for each subset.

        Reading the values of a key subset by subset is expensive because each
        access has to go through the cache and index the underlying array. This
        method resolves the whole key in one go so that the caller can simply
        iterate over the values.
        """
        entry = self._all_subsets_entry(key)
        if entry[1] is None:
            value = entry[0]
            if isinstance(value, np.ndarray) and entry[2]:
                # a list of Python scalars is much cheaper to iterate over (and to
                # build a dataframe from) than a numpy array
                value = value.tolist()
            entry[1] = value

        return entry[1], entry[2]

    def get_all_subsets_raw(self, key):
        """Return all the values of a key with a concrete rank as read from the message.

        Same as :meth:`get_all_subsets`, but the values are not converted to a list.
        This makes it possible to match a whole numpy array against a filter at once.

        Parameters
        ----------
        key: str
            The BUFR key to read. Must contain a rank, e.g. "#1#latitude".

        Returns
        -------
        values: Any
            The values as read from the message (with the missing values converted).
        per_subset: bool
            Whether ``values`` holds a separate value for each subset.
        """
        entry = self._all_subsets_entry(key)
        return entry[0], entry[2]

    def _all_subsets_entry(self, key):
        """Read a key for all the subsets. The result is cached as [raw, list, per_subset]."""
        try:
            return self.subset_cache[key]
        except KeyError:
            pass

        value = convert_missing(self.message.get(key))
        if isinstance(value, (np.ndarray, list)):
            per_subset = len(value) == self.subset_count
        else:
            per_subset = False

        entry = [value, None, per_subset]
        self.subset_cache[key] = entry
        return entry

    def get_all_subsets_multi(self, key):
        """Return all the values of a multi-rank key at once.

        Parameters
        ----------
        key: str
            The BUFR key to read. Must not contain a rank, e.g. "cloudType".

        Returns
        -------
        values: list
            When ``per_subset`` is True this is a list with one item per subset, each
            item holding the values of all the ranks for that subset. Otherwise it is
            the list of the rank values shared by all the subsets.
        per_subset: bool
            Whether ``values`` holds a separate item for each subset.

        See :meth:`get_all_subsets` for why the values are resolved in one go.
        """
        entry = self._all_subsets_multi_entry(key)
        if entry[1] is None:
            value = entry[0]
            if isinstance(value, np.ndarray):
                # a list of Python scalars is much cheaper to iterate over (and to
                # build a dataframe from) than a numpy array
                value = value.tolist()
            elif not isinstance(value, list):
                value = [value]
            entry[1] = value

        return entry[1], entry[2]

    def get_all_subsets_multi_raw(self, key):
        """Return all the values of a multi-rank key as read from the message.

        Same as :meth:`get_all_subsets_multi`, but the values are not converted to a
        list. This makes it possible to match a whole numpy array against a filter at
        once.

        Parameters
        ----------
        key: str
            The BUFR key to read. Must not contain a rank, e.g. "cloudType".

        Returns
        -------
        values: Any
            The values as read from the message (with the missing values converted).
            For a numpy array the first dimension is the subset and the second one
            the rank.
        per_subset: bool
            Whether ``values`` holds a separate item for each subset.
        """
        entry = self._all_subsets_multi_entry(key)
        return entry[0], entry[2]

    def _all_subsets_multi_entry(self, key):
        """Read a multi-rank key for all the subsets. Cached as [raw, list, per_subset]."""
        try:
            return self.multi_subset_cache[key]
        except KeyError:
            pass

        value = self.get_multi_rank_value(key)
        if isinstance(value, (np.ndarray, list)):
            per_subset = len(value) == self.subset_count
        else:
            per_subset = False

        entry = [value, None, per_subset]
        self.multi_subset_cache[key] = entry
        return entry

    def get(self, key, subset):
        non_header = key != "unexpandedDescriptors"

        if non_header:
            if key not in self.cache:
                if non_header:
                    # concrete rank key
                    if key.startswith("#"):
                        value = convert_missing(self.message.get(key))
                        self.cache[key] = value
                    # multirank key. The name does not contain the rank, e.g. "timePeriod". The values
                    # are stored as a 2D list/numpy array ach element containing the value for a given subset.
                    # So the values for a given element are the values for each rank with increasing rank
                    # order.
                    else:
                        value = self.get_multi_rank_value(key)
                        self.cache[key] = value
            else:
                value = self.cache[key]

            if isinstance(value, (list, np.ndarray)) and len(value) == self.subset_count:
                return value[subset]
            else:
                return value

        else:
            return self.message.get(key)

    def get_multi_rank_value(self, key):
        r = self._get_multi_rank_value_flat(key)
        if r is not None:
            return r

        # multi-rank key accessed without a rank
        r = []
        for i_rank in range(1, 1000000):
            rk = f"#{i_rank}#{key}"
            if rk in self.message:
                v = self.message.get(rk)
                if isinstance(v, (np.ndarray, list)):
                    r.append(convert_missing(v))
                elif not isinstance(v, str):
                    r.append(np.asarray([convert_missing(v)] * self.subset_count))
                else:
                    r.append([convert_missing(v)] * self.subset_count)
            else:
                break

        try:
            return np.asarray(r).T
        except Exception:
            return [list(row) for row in zip(*r)]

    def _get_multi_rank_value_flat(self, key):
        """Try to read all the ranks of a multi-rank key with a single message access.

        For compressed data ecCodes returns the values of all the ranks of a key in a
        single array, one rank after the other, each holding one value per subset.
        Reading it in one go is much cheaper than reading the ranks one by one, but
        the layout has to be confirmed first: a rank can also be stored as a single
        value when it is the same in all the subsets.

        Parameters
        ----------
        key: str
            The BUFR key to read. Must not contain a rank, e.g. "cloudType".

        Returns
        -------
        numpy.ndarray or None
            The values as a 2D array with the subset as the first and the rank as the
            second dimension, or None when the layout could not be confirmed. The
            caller then has to read the ranks one by one.
        """
        subset_count = self.subset_count
        if subset_count < 1:
            return None

        value = self.message.get(key)
        if not isinstance(value, np.ndarray) or len(value) % subset_count != 0:
            return None

        rank_count = len(value) // subset_count
        if rank_count < 1:
            return None

        # confirm that each rank indeed holds one value per subset
        if f"#{rank_count}#{key}" not in self.message or f"#{rank_count + 1}#{key}" in self.message:
            return None

        return convert_missing(value).reshape(rank_count, subset_count).T
