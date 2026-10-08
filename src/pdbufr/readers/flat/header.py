# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import typing as T

import eccodes  # type: ignore

MISSING_DOUBLE = eccodes.CODES_MISSING_DOUBLE
MISSING_LONG = eccodes.CODES_MISSING_LONG


class BufrHeader:
    SKIP = {"unexpandedDescriptors"}
    # the last key of section 3, i.e. the last key of the header
    LAST_HEADER_KEY = "unexpandedDescriptors"
    # first bit of section1Flags: the optional local section (section 2) is present
    LOCAL_SECTION_FLAG = 0x80

    def __init__(self, message, columns, filters, lazy_keys: bool = False) -> None:
        """Wraps a BUFR message header with filtering capabilities.

        Parameters
        ----------
        message : Any
            The BUFR message to wrap. It must be packed. For performance reasons, the class does not check
            if the message is packed. The caller is responsible for ensuring this.
        filters : Dict[str, BufrFilter]
            Filters to apply on the message keys. The header related filters are extracted
            from this dictionary and stored internally.
        lazy_keys : bool
            When True the header keys are not enumerated on creation but only when
            :obj:`keys`, :obj:`keys_list` or :meth:`last_key` is first used. Enumerating
            the keys of a message is expensive, so callers only needing to test whether
            a given key belongs to the header (via ``in``) should use this option.
            Since the enumeration is then performed on demand, the caller must ensure
            the message is still packed at that point.
        """
        self.message = message
        # assert not message.get("unpack")
        self._keys: T.Optional[T.Set[str]] = None
        self._keys_list: T.Optional[T.List[str]] = None
        self._contains: T.Dict[str, bool] = {}
        # determined on demand, only when a ranked key is tested
        self._ranked_is_data: T.Optional[bool] = None
        if not lazy_keys:
            self.build_keys()

        # the columns are only classified on demand: a message rejected by the header
        # filters never needs them
        self._columns_input = columns or {}
        self._columns: T.Optional[T.List[T.Any]] = None
        self._columns_values = None

        filters = filters or dict()
        self.filters = {}
        for k, f in filters.items():
            if f.header_only or k in self:
                self.filters[k] = f

        self._matched = None
        self._filters_values = dict()

    @property
    def columns(self) -> T.List[T.Any]:
        """The columns that can be extracted from the header."""
        if self._columns is None:
            self._columns = [c for k, c in self._columns_input.items() if c.header_only or k in self]
        return self._columns

    def build_keys(self) -> T.List[str]:
        """Enumerate the header keys. The message must still be packed."""
        keys = [k for k in self.message if k not in BufrHeader.SKIP]
        self._keys_list = keys
        self._keys = set(keys)
        return keys

    def build_keys_from_message_keys(self, keys: T.List[str]) -> T.Optional[int]:
        """Determine the header keys from the keys of the unpacked message.

        In an unpacked message the header keys come first, followed by the data keys.
        The header always ends with "unexpandedDescriptors", the last key of section 3,
        so everything after it belongs to the data section.

        Parameters
        ----------
        keys: List[str]
            All the keys of the unpacked message, in message order.

        Returns
        -------
        int or None
            The index of the first data key in :obj:`keys`, or None when the end of the
            header could not be located. The caller then has to fall back to
            :meth:`build_keys`, which requires a packed message.

        Using this method instead of :meth:`build_keys` saves a full key enumeration
        per message, since the keys of the unpacked message have to be read anyway to
        extract the data section.
        """
        try:
            data_start = keys.index(BufrHeader.LAST_HEADER_KEY) + 1
        except ValueError:
            return None

        header_keys = [k for k in keys[:data_start] if k not in BufrHeader.SKIP]
        self._keys_list = header_keys
        self._keys = set(header_keys)
        return data_start

    @property
    def keys_built(self) -> bool:
        """Whether the header keys are already known."""
        return self._keys is not None

    @property
    def keys(self) -> T.Set[str]:
        if self._keys is None:
            self.build_keys()
            assert self._keys is not None
        return self._keys

    @property
    def keys_list(self) -> T.List[str]:
        if self._keys_list is None:
            return self.build_keys()
        return self._keys_list

    def ranked_keys_are_data(self) -> bool:
        """Tell whether a ranked key can only belong to the data section.

        The keys of the mandatory header sections are never ranked. The only header
        section that can contain arbitrary keys is the optional local section
        (section 2), whose presence is indicated by the first bit of the
        ``section1Flags`` bitflag. As of today the local section generated by ECMWF
        (``bufrHeaderCentre`` 98) never contains ranked keys, but this cannot be
        assumed for any other centre.
        """
        if self._ranked_is_data is None:
            self._ranked_is_data = False
            # for a dict based message any key can be a header key
            if hasattr(self.message, "codes_id"):
                flags = self.message.get("section1Flags")
                if flags is not None:
                    if not flags & BufrHeader.LOCAL_SECTION_FLAG:
                        self._ranked_is_data = True
                    elif self.message.get("bufrHeaderCentre") == 98:
                        self._ranked_is_data = True

        return self._ranked_is_data

    def __contains__(self, key: str) -> bool:
        if self._keys is not None:
            return key in self._keys

        # the keys are not enumerated yet, so test the membership directly on the
        # message. This is much cheaper than enumerating all the header keys when
        # only a few keys have to be tested.
        if key.startswith("#") and self.ranked_keys_are_data():
            return False

        r = self._contains.get(key)
        if r is None:
            r = key not in BufrHeader.SKIP and key in self.message
            self._contains[key] = r
        return r

    def _get(self, key: str) -> T.Any:
        value = self.message.get(key)

        # print(" -> header key:", key, "value:", value)
        if isinstance(value, float) and value == MISSING_DOUBLE:
            value = None
        elif isinstance(value, int) and value == MISSING_LONG:
            value = None

        return value

    def last_key(self) -> T.Optional[str]:
        keys_list = self.keys_list
        return keys_list[-1] if keys_list else None

    def columns_values(self) -> T.Dict[str, T.Any]:
        if self._columns_values is None:
            self._columns_values = {c.name: c.get_value(self._get, ranked=False) for c in self.columns}
        return self._columns_values

    def _filter(self) -> None:
        for f in self.filters.values():
            value = f.column.get_value(self._get, ranked=False)
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
        _get = self._get
        return {key: _get(key) for key in self.keys_list}
