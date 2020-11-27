import logging
import typing as T

LOG = logging.getLogger(__name__)


class BufrFilter:
    def __init__(self, user_filter):
        # type: (T.Any) -> None
        self.filter = frozenset()  # type: T.Union[slice, T.FrozenSet[T.Any]]
        if isinstance(user_filter, slice):
            if user_filter.step is not None:
                LOG.warning(f"slice filters ignore the step {user_filter.step}")
            self.filter = user_filter
        elif isinstance(user_filter, T.Iterable) and not isinstance(user_filter, str):
            self.filter = frozenset(user_filter)
        elif isinstance(user_filter, T.Callable):
            self.filter = user_filter
        else:
            self.filter = frozenset([user_filter])

    def match(self, value):
        # type: (T.Any) -> bool
        if isinstance(self.filter, slice):
            if self.filter.start is not None and value < self.filter.start:
                return False
            elif self.filter.stop is not None and value >= self.filter.stop:
                return False
        elif isinstance(self.filter, T.Callable):
            return bool(self.filter(value))
        elif value not in self.filter:
            return False
        return True


def compile_filters(filters):
    # type: (T.Mapping[str, T.Any]) -> T.Dict[str, BufrFilter]
    return {key: BufrFilter(user_filter) for key, user_filter in filters.items()}


def match_compiled_filters(message_items, compiled_filters, required=True):
    # type: (T.Iterable[T.Tuple[str, str, T.Any]], T.Dict[str, BufrFilter], bool) -> bool
    seen = set()
    for key, short_key, value in message_items:
        if short_key in compiled_filters:
            if not compiled_filters[short_key].match(value):
                return False
            else:
                seen.add(short_key)
    if required and len(seen) != len(compiled_filters):
        return False
    return True
