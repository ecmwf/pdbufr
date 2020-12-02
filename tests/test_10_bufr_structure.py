import typing as T

from pdbufr import bufr_structure


def test_BufrKey() -> None:
    res = bufr_structure.BufrKey.from_level_key(0, "edition")

    assert res.level == 0
    assert res.rank == 0
    assert res.short_key == "edition"
    assert res.key == "edition"

    res = bufr_structure.BufrKey.from_level_key(0, "#1#temperature")

    assert res.level == 0
    assert res.rank == 1
    assert res.short_key == "temperature"
    assert res.key == "#1#temperature"


def test_iter_message_structure() -> None:
    message: T.Mapping[str, T.Any] = {
        "edition": 1,
    }

    res = bufr_structure.iter_message_structure(message)

    assert list(res) == [(0, "edition")]

    message = {
        "edition": 1,
        "#1#year": 2020,
        "#1#subsetNumber": 1,
        "#1#latitude": 43.0,
        "#1#temperature": 300.0,
        "#2#latitude": 42.0,
        "#2#temperature": 310.0,
        "#2#subsetNumber": 2,
        "#3#temperature": 300.0,
    }
    code_source = {
        "#1#latitude->code": "005002",
        "#2#latitude->code": "005002",
    }
    expected = [
        (0, "edition"),
        (0, "#1#year"),
        (0, "#1#subsetNumber"),
        (1, "#1#latitude"),
        (2, "#1#temperature"),
        (1, "#2#latitude"),
        (2, "#2#temperature"),
        (0, "#2#subsetNumber"),
        (1, "#3#temperature"),
    ]

    res = bufr_structure.iter_message_structure(message, code_source)

    assert list(res) == expected
