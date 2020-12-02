import collections
import typing as T

import attr
import eccodes  # type: ignore


@attr.attrs(auto_attribs=True, slots=True, frozen=True)
class BufrKey:
    level: int
    rank: int
    name: str

    @classmethod
    def from_level_key(cls, level: int, key: str) -> "BufrKey":
        rank_text, sep, short_key = key.rpartition("#")
        if sep == "#":
            rank = int(rank_text[1:])
        else:
            rank = 0
        return cls(level, rank, short_key)

    @property
    def key(self) -> str:
        if self.rank:
            prefix = f"#{self.rank}#"
        else:
            prefix = ""
        return prefix + self.name


IS_KEY_COORD = {"subsetNumber": True}


def message_structure(
    message: T.Mapping[str, T.Any],
    code_source: T.Optional[T.Mapping[str, T.Any]] = None,
) -> T.Iterator[T.Tuple[int, str]]:
    if code_source is None:
        code_source = message

    level = 0
    coords: T.Dict[str, int] = collections.OrderedDict()
    for key in message:
        short_key = key.rpartition("#")[2]

        if short_key in IS_KEY_COORD:
            is_coord = IS_KEY_COORD[short_key]
        else:
            try:
                code = code_source[key + "->code"]
                is_coord = int(code[:3]) < 10
            except (KeyError, eccodes.KeyValueNotFoundError):
                is_coord = False

        while is_coord and short_key in coords:
            _, level = coords.popitem()  # OrderedDict.popitem uses LIFO order

        yield (level, key)

        if is_coord:
            coords[short_key] = level
            level += 1


def filtered_bufr_keys(
    message: T.Mapping[str, T.Any],
    include: T.Optional[T.Container[str]] = None,
    code_source: T.Optional[T.Mapping[str, T.Any]] = None,
) -> T.Iterator[BufrKey]:
    for level, key in message_structure(message, code_source):
        bufr_key = BufrKey.from_level_key(level, key)
        if include is None or bufr_key.name in include or bufr_key.key in include:
            yield bufr_key
