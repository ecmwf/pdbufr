import collections
import typing as T

import attr
import eccodes  # type: ignore

from . import bufr_filters


@attr.attrs(auto_attribs=True, frozen=True)
class BufrKey:
    level: int
    rank: int
    name: str

    @classmethod
    def from_level_key(cls, level: int, key: str) -> "BufrKey":
        rank_text, sep, name = key.rpartition("#")
        if sep == "#":
            rank = int(rank_text[1:])
        else:
            rank = 0
        return cls(level, rank, name)

    @property
    def key(self) -> str:
        if self.rank:
            prefix = f"#{self.rank}#"
        else:
            prefix = ""
        return prefix + self.name


IS_KEY_COORD = {"subsetNumber": True}


def message_structure(message: T.Mapping[str, T.Any],) -> T.Iterator[T.Tuple[int, str]]:
    level = 0
    coords: T.Dict[str, int] = collections.OrderedDict()
    for key in message:
        name = key.rpartition("#")[2]

        if name in IS_KEY_COORD:
            is_coord = IS_KEY_COORD[name]
        else:
            try:
                code = message[key + "->code"]
                is_coord = int(code[:3]) < 10
            except (KeyError, eccodes.KeyValueNotFoundError):
                is_coord = False

        while is_coord and name in coords:
            _, level = coords.popitem()  # OrderedDict.popitem uses LIFO order

        yield (level, key)

        if is_coord:
            coords[name] = level
            level += 1


def filtered_keys(
    message: T.Mapping[str, T.Any], include: T.Tuple[str, ...] = (),
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

    try:
        delayed_descriptors = message["delayedDescriptorReplicationFactor"]
    except (KeyError, eccodes.KeyValueNotFoundError):
        delayed_descriptors = []

    if isinstance(delayed_descriptors, int):
        message_uid += (delayed_descriptors,)
    else:
        message_uid += tuple(delayed_descriptors)

    return message_uid


def cached_filtered_keys(
    message: T.Mapping[str, T.Any],
    cache: T.Dict[T.Tuple[T.Hashable, ...], T.List[BufrKey]],
    include: T.Tuple[str, ...] = (),
) -> T.List[BufrKey]:
    message_uid = make_message_uid(message)
    filtered_message_uid: T.Tuple[T.Hashable, ...] = message_uid + include
    if filtered_message_uid not in cache:
        cache[filtered_message_uid] = list(filtered_keys(message, include))
    return cache[filtered_message_uid]


def extract_observations(
    message: T.Mapping[str, T.Any],
    filtered_keys: T.List[BufrKey],
    filters: T.Dict[str, bufr_filters.BufrFilter],
) -> T.Iterator[T.List[T.Tuple[BufrKey, T.Any]]]:
    current_items: T.List[T.Tuple[BufrKey, T.Any]] = []
    current_level = -1
    current_matches = 0
    for bufr_key in filtered_keys:
        level = bufr_key.level
        if current_matches == len(filters) and level < current_level:
            # copy the content of current_items
            yield list(current_items)

        while len(current_items) and (
            level < current_items[-1][0].level
            or (bufr_key.name in filters and bufr_key.name == current_items[-1][0].name)
        ):
            bk, _ = current_items.pop()
            if bk.name in filters:
                current_matches -= 1
                assert current_matches >= 0

        value = message[bufr_key.key]
        if value == eccodes.CODES_MISSING_DOUBLE:
            value = None

        current_items.append((bufr_key, value))

        if bufr_key.name in filters and filters[bufr_key.name].match(value):
            current_matches += 1

        current_level = level

    # yield the last observation
    if current_matches == len(filters):
        yield current_items
