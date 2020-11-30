import logging
import typing as T

LOG = logging.getLogger(__name__)


class BufrFilter:
    def __init__(self, user_filter: T.Any) -> None:
        self.filter: T.Union[slice, T.Set[T.Any], T.Callable[[T.Any], bool]]

        if isinstance(user_filter, slice):
            if user_filter.step is not None:
                LOG.warning(f"slice filters ignore the step {user_filter.step}")
            self.filter = user_filter
        elif isinstance(user_filter, T.Iterable) and not isinstance(user_filter, str):
            self.filter = set(user_filter)
        elif callable(user_filter):
            self.filter = user_filter
        else:
            self.filter = {user_filter}

    def match(self, value: T.Any) -> bool:
        if isinstance(self.filter, slice):
            if self.filter.start is not None and value < self.filter.start:
                return False
            elif self.filter.stop is not None and value > self.filter.stop:
                return False
        elif callable(self.filter):
            return bool(self.filter(value))
        elif value not in self.filter:
            return False
        return True


def compile_filters(filters: T.Dict[str, T.Any]) -> T.Dict[str, BufrFilter]:
    return {key: BufrFilter(user_filter) for key, user_filter in filters.items()}


def match_compiled_filters(
    message_items: T.Iterable[T.Tuple[str, str, T.Any]],
    compiled_filters: T.Dict[str, BufrFilter],
    required: bool = True,
) -> bool:
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
