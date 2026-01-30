import collections
from typing import Iterable, Generator, Any, List

from .types import T


def flatten(some_list: Iterable) -> Generator[Any, None, None]:
    """
    Flattens a nested iterable into a one-dimensional generator.

    This function takes an iterable, which may contain nested iterables,
    and returns a generator that yields each element in a flattened order.
    Strings and bytes are treated as atomic elements and will not be traversed
    further as nested iterables.

    :param some_list: A potentially nested iterable to be flattened.
    :type some_list: Iterable
    :return: A generator that yields elements from the input iterable in a
        flattened order.
    :rtype: Generator[Any, None, None]
    """
    for el in some_list:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def safe_list_get(lst: List[T], idx: int, default: T = None) -> T:
    """
    Retrieve an element from a list by its index or return a default value if the index
    is out of range or the input is not subscriptable. This function ensures safe retrieval
    by providing a fallback value when access fails.

    :param lst: The list from which the element is to be retrieved (may be None).
    :type lst: List[T]
    :param idx: The index of the element to retrieve from the list.
    :type idx: int
    :param default: The fallback value to be returned if retrieval fails.
    :type default: T
    :return: The element at the specified index, or the default value
             if the index is out of range or lst is None/not subscriptable.
    :rtype: T
    """
    try:
        return lst[idx]
    except (IndexError, TypeError):
        return default
