# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import collections
import typing as T

import eccodes  # type: ignore
import numpy as np

from pdbufr.core.keys import BufrKey
from pdbufr.core.subset import BufrSubsetReader

MISSING_LONG = eccodes.CODES_MISSING_LONG
MISSING_DOUBLE = eccodes.CODES_MISSING_DOUBLE


class _CountingMessage(dict):
    """Dict-based message counting the number of ``get()`` calls per key."""

    def __init__(self, *args: T.Any, **kwargs: T.Any) -> None:
        super().__init__(*args, **kwargs)
        self.get_calls: T.Dict[str, int] = collections.Counter()

    def get(self, key: str, default: T.Any = None) -> T.Any:
        self.get_calls[key] += 1
        return super().get(key, default)


def _keys(*names: str) -> T.List[BufrKey]:
    return [BufrKey.from_level_key(0, name) for name in names]


def _compressed_message() -> _CountingMessage:
    return _CountingMessage({
        "compressedData": 1,
        "numberOfSubsets": 3,
        "unexpandedDescriptors": np.array([1001, 1002, 12101]),
        "stationNumber": np.array([10, 11, 12], dtype="int64"),
        "airTemperature": np.array([280.5, 281.5, 282.5]),
        "wmoRegion": 6,
        "stationName": ["a", "b", "c"],
        "pressure": np.float64(1013.25),
        "oneElement": np.array([42], dtype="int64"),
    })


def _collect(reader: BufrSubsetReader) -> T.List[T.List[T.Tuple[str, T.Any]]]:
    return [list(subset.iter_values()) for subset in reader.subsets()]


def test_iter_values_compressed_indexing() -> None:
    message = _compressed_message()
    reader = BufrSubsetReader(
        message,
        _keys("wmoRegion", "stationNumber", "airTemperature", "stationName", "pressure", "oneElement"),
    )
    assert reader.is_compressed
    assert reader.subset_count == 3

    result = _collect(reader)

    assert len(result) == 3
    for i, values in enumerate(result):
        # the key order is kept and the names are returned without the rank
        assert [name for name, _ in values] == [
            "wmoRegion",
            "stationNumber",
            "airTemperature",
            "stationName",
            "pressure",
            "oneElement",
        ]
        d = dict(values)
        # arrays/lists of length == subset count are indexed by the subset number
        assert d["stationNumber"] == 10 + i
        assert d["airTemperature"] == 280.5 + i
        assert d["stationName"] == "abc"[i]
        # single values are shared by all the subsets
        assert d["wmoRegion"] == 6
        assert d["pressure"] == 1013.25
        # a length-1 array is not indexed when the subset count is 3
        assert isinstance(d["oneElement"], np.ndarray)
        assert d["oneElement"].tolist() == [42]

    # numpy scalars are converted to python scalars
    d = dict(result[1])
    assert type(d["stationNumber"]) is int
    assert type(d["airTemperature"]) is float
    assert type(d["pressure"]) is float


def test_iter_values_compressed_single_value_length_one_subset_count() -> None:
    # a length-1 array is a "single value" when there is a single subset
    message = _CountingMessage({
        "compressedData": 1,
        "numberOfSubsets": 1,
        "stationNumber": np.array([7], dtype="int64"),
    })
    reader = BufrSubsetReader(message, _keys("stationNumber"))
    assert _collect(reader) == [[("stationNumber", 7)]]


def test_iter_values_missing_values() -> None:
    message = _CountingMessage({
        "compressedData": 1,
        "numberOfSubsets": 3,
        "stationNumber": np.array([MISSING_LONG, 11, MISSING_LONG], dtype="int64"),
        "airTemperature": np.array([280.5, MISSING_DOUBLE, 282.5]),
        "scalarLong": MISSING_LONG,
        "scalarNumpyLong": np.int64(MISSING_LONG),
        "scalarDouble": MISSING_DOUBLE,
    })
    reader = BufrSubsetReader(
        message,
        _keys("stationNumber", "airTemperature", "scalarLong", "scalarNumpyLong", "scalarDouble"),
    )

    result = [dict(values) for values in _collect(reader)]

    assert [d["stationNumber"] for d in result] == [None, 11, None]
    assert [d["airTemperature"] for d in result] == [280.5, None, 282.5]
    # single missing values are None in all the subsets
    for d in result:
        assert d["scalarLong"] is None
        assert d["scalarNumpyLong"] is None
        assert d["scalarDouble"] is None

    # non-missing numpy values are plain python values
    assert type(result[1]["stationNumber"]) is int
    assert type(result[0]["airTemperature"]) is float


def test_iter_values_cache_reuse() -> None:
    message = _compressed_message()
    reader = BufrSubsetReader(message, _keys("stationNumber", "airTemperature", "wmoRegion"))

    result = _collect(reader)

    assert [dict(v)["stationNumber"] for v in result] == [10, 11, 12]
    assert [dict(v)["airTemperature"] for v in result] == [280.5, 281.5, 282.5]
    # each key is read from the message only once for all the subsets
    assert dict(message.get_calls) == {"stationNumber": 1, "airTemperature": 1, "wmoRegion": 1}
    assert set(reader.cache) == {"stationNumber", "airTemperature", "wmoRegion"}


def test_iter_values_cache_uses_rank_in_key() -> None:
    message = _CountingMessage({
        "compressedData": 1,
        "numberOfSubsets": 2,
        "#1#airTemperature": np.array([1.5, 2.5]),
        "#2#airTemperature": np.array([3.5, 4.5]),
    })
    reader = BufrSubsetReader(message, _keys("#1#airTemperature", "#2#airTemperature"))

    result = _collect(reader)

    assert result == [
        [("airTemperature", 1.5), ("airTemperature", 3.5)],
        [("airTemperature", 2.5), ("airTemperature", 4.5)],
    ]
    assert dict(message.get_calls) == {"#1#airTemperature": 1, "#2#airTemperature": 1}


def test_iter_values_stops_at_first_order_statistics() -> None:
    message = _compressed_message()
    message["firstOrderStatisticsOfAirTemperature"] = np.array([1.0, 2.0, 3.0])
    reader = BufrSubsetReader(
        message,
        _keys("stationNumber", "firstOrderStatisticsOfAirTemperature", "airTemperature"),
    )

    result = _collect(reader)

    assert result == [[("stationNumber", 10)], [("stationNumber", 11)], [("stationNumber", 12)]]
    # the keys after the statistics are not read at all
    assert "firstOrderStatisticsOfAirTemperature" not in message.get_calls
    assert "airTemperature" not in message.get_calls


def test_iter_values_unexpanded_descriptors_not_indexed() -> None:
    # the number of descriptors equals the number of subsets on purpose
    message = _CountingMessage({
        "compressedData": 1,
        "numberOfSubsets": 3,
        "unexpandedDescriptors": np.array([1001, 1002, 12101], dtype="int64"),
    })
    reader = BufrSubsetReader(message, _keys("unexpandedDescriptors"))

    result = _collect(reader)

    assert len(result) == 3
    for values in result:
        assert len(values) == 1
        name, value = values[0]
        assert name == "unexpandedDescriptors"
        assert isinstance(value, np.ndarray)
        assert value.tolist() == [1001, 1002, 12101]


def test_iter_values_uncompressed_single_subset() -> None:
    message = _CountingMessage({
        "compressedData": 0,
        "numberOfSubsets": 1,
        "stationNumber": np.int64(10),
        "airTemperature": np.float64(280.5),
        "pressure": np.float64(MISSING_DOUBLE),
        "windDirection": np.int64(MISSING_LONG),
        # never indexed per subset when the message is not compressed
        "values": np.array([1, 2, 3]),
    })
    reader = BufrSubsetReader(
        message,
        _keys("stationNumber", "airTemperature", "pressure", "windDirection", "values"),
    )
    assert not reader.is_compressed
    assert not reader.is_uncompressed

    result = _collect(reader)

    assert len(result) == 1
    values = result[0]
    assert [name for name, _ in values] == ["stationNumber", "airTemperature", "pressure", "windDirection", "values"]
    d = dict(values)
    assert d["stationNumber"] == 10 and type(d["stationNumber"]) is int
    assert d["airTemperature"] == 280.5 and type(d["airTemperature"]) is float
    assert d["pressure"] is None
    assert d["windDirection"] is None
    assert d["values"].tolist() == [1, 2, 3]
