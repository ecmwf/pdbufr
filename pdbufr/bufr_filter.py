import typing as T


def compile_filters(filters):
    # type: (T.Mapping[str, T.Any]) -> T.Dict[str, T.FrozenSet[T.Any]]
    compiled_filters = {}
    for key, value in filters.items():
        if isinstance(value, (T.Iterable, T.Iterator)) and not isinstance(value, str):
            uniform_value = frozenset(value)
        else:
            uniform_value = frozenset([value])
        compiled_filters[key] = uniform_value
    return compiled_filters


def match_compiled_filters(message_items, filters, required=True):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]], T.Dict[str, T.FrozenSet[T.Any]], bool) -> bool
    seen = set()
    for key, short_key, value in message_items:
        if short_key in filters:
            if value not in filters[short_key]:
                return False
            else:
                seen.add(short_key)
    if required and len(seen) != len(filters):
        return False
    return True
