import logging
import typing as T

LOG = logging.getLogger(__name__)


class BufrFilter:
    def __init__(self, user_filter):
        if isinstance(user_filter, slice):
            if user_filter.step is not None:
                LOG.warning(
                    "slice filters ignore the value of the step %r", user_filter.step
                )
            self.compiled_filter = user_filter
        elif isinstance(user_filter, (T.Iterable, T.Iterator)) and not isinstance(
            user_filter, str
        ):
            self.compiled_filter = frozenset(user_filter)
        else:
            self.compiled_filter = frozenset([user_filter])

    def match(self, value):
        if isinstance(self.compiled_filter, slice):
            if (
                self.compiled_filter.start is not None
                and value < self.compiled_filter.start
            ):
                return False
            elif (
                self.compiled_filter.stop is not None
                and value >= self.compiled_filter.stop
            ):
                return False
        elif value not in self.compiled_filter:
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
