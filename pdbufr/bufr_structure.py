import collections
import typing as T

import attr
import eccodes


@attr.attrs(auto_attribs=True, slots=True)
class BufrKey:
    level: int
    rank: int
    short_key: str

    @classmethod
    def from_level_key(cls, level: int, key: str):
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
        return prefix + self.short_key


IS_KEY_COORD = {"subsetNumber": True}


def iter_message_structure(
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
