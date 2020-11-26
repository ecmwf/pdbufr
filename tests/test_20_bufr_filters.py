import typing as T
import numpy as np

from pdbufr import bufr_filters


def test_BufrFilter_value():
    assert bufr_filters.BufrFilter(1).match(1) is True
    assert bufr_filters.BufrFilter(1).match(True) is True
    assert bufr_filters.BufrFilter(1).match(1.0) is True

    assert bufr_filters.BufrFilter(1).match(False) is False
    assert bufr_filters.BufrFilter(1).match(float("inf")) is False


def test_BufrFilter_iterators():
    assert bufr_filters.BufrFilter([1, 2]).match(1) is True
    assert bufr_filters.BufrFilter((1, 2)).match(True) is True
    assert bufr_filters.BufrFilter({1, 2}).match(1.0) is True

    assert bufr_filters.BufrFilter([1, 2]).match(False) is False
    assert bufr_filters.BufrFilter({1, 2}).match(float("inf")) is False


def test_BufrFilter_slices():
    assert bufr_filters.BufrFilter(slice(1, None)).match(float("inf")) is True
    assert bufr_filters.BufrFilter(slice(None, 2)).match(True) is True
    assert bufr_filters.BufrFilter(slice(0.1, 1.1)).match(1.0) is True

    assert bufr_filters.BufrFilter(slice(0.1, 1.1, 0.1)).match(1.0) is True

    assert bufr_filters.BufrFilter(slice(1, None)).match(False) is False
    assert bufr_filters.BufrFilter(slice(1000.0)).match(float("inf")) is False


def test_BufrFilter_ranges():
    assert bufr_filters.BufrFilter(range(1, 3)).match(1) is True
    assert bufr_filters.BufrFilter(range(1, 3)).match(True) is True
    assert bufr_filters.BufrFilter(range(1, 3)).match(1.0) is True
    assert bufr_filters.BufrFilter(range(1, 3)).match(2) is True

    assert bufr_filters.BufrFilter(range(1, 3)).match(0) is False
    assert bufr_filters.BufrFilter(range(1, 3)).match(1.5) is False
    assert bufr_filters.BufrFilter(range(1, 3)).match(3) is False

    assert bufr_filters.BufrFilter(np.arange(1, 3, 0.5)).match(1.5) is True


def test_compile_filters():
    user_filters = {
        "station": 234,
        "level": range(1, 12),
        "height": slice(1.5, 2.1),
    }

    res = bufr_filters.compile_filters(user_filters)

    assert isinstance(res, dict)
    assert set(res) == set(user_filters)
    assert all(isinstance(r, bufr_filters.BufrFilter) for r in res.values())


def test_match_compiled_filters():
    compile_filters = {
        "station": bufr_filters.BufrFilter(234),
        "level": bufr_filters.BufrFilter(range(1, 12)),
        "height": bufr_filters.BufrFilter(slice(1.5, 2.1)),
    }

    message_items = [("station", "station", 233)]
    assert bufr_filters.match_compiled_filters(message_items, compile_filters) is False

    message_items = [("station", "station", 234), ("airTemperature", "airTemperature", 300.0)]
    assert bufr_filters.match_compiled_filters(message_items, compile_filters) is False

    message_items += [("#1#level", "level", 1), ("height", "height", 1.5)]
    assert bufr_filters.match_compiled_filters(message_items, compile_filters) is True
