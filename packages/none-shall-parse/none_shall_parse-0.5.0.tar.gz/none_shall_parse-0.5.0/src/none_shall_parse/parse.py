from typing import Callable, Any
from typing import Union

from .strings import slugify
from .types import ChoicesType, StringLike

_true_set = {"yes", "true", "t", "y", "1"}
_false_set = {"no", "false", "f", "n", "0"}


def str_to_bool(v: Any, raise_exc: bool = False) -> bool | None:
    """
    Convert a string representation of a boolean into a boolean value.

    This function takes a string input and attempts to interpret it as a boolean
    value based on predefined sets of true and false representations. It can
    also raise an exception for invalid inputs if specified.

    :param v: The string value to be interpreted as boolean.
    :type v: str
    :param raise_exc: Determines whether to raise an exception for invalid inputs.
    :type raise_exc: bool
    :return: A boolean value interpreted from the input string or None if invalid.
    :rtype: bool | None
    :raises ValueError: If the input string is invalid and `raise_exc` is True.
    """
    if isinstance(v, str):
        v = v.lower()
        if v in _true_set:
            return True
        if v in _false_set:
            return False

    if raise_exc:
        raise ValueError('Expected "%s"' % '", "'.join(_true_set | _false_set))
    return None


def is_true(v: Any) -> bool:
    """
    Determines whether the given value evaluates to a boolean `True`.

    The function checks if the input value can be converted to a boolean
    representation of `True` using the helper function `str_to_bool`.

    :param v: The value to be evaluated for boolean truthiness
    :type v: Any
    :return: `True` if the value evaluates to boolean `True`, otherwise `False`
    :rtype: bool
    """
    return str_to_bool(v) is True


def is_false(v: Any) -> bool:
    """
    Determines if the given value evaluates to a boolean False.

    This function utilizes the `str_to_bool` conversion to determine whether
    the input value corresponds to a boolean `False`. It is particularly
    useful for interpreting string-based representations of boolean values.

    :param v: The value to be evaluated.
    :type v: Any
    :return: True if the value evaluates to False, otherwise False.
    :rtype: bool
    """
    return str_to_bool(v) is False


def str_to_strs_list(s: str | None) -> list[str]:
    """
    Parses a given string into an array of strings. The input string is split based on
    commas or newline characters. Each resulting element is stripped of leading and
    trailing whitespace, and empty items are excluded from the result. If the input
    string is None, an empty list is returned.

    :param s: The input string to be parsed. May be None.
    :type s: str | None
    :return: A list of non-empty, trimmed strings extracted from the input.
    :rtype: list[str]
    """
    return (
        []
        if s is None
        else [e.strip() for e in s.replace("\n", ",").split(",") if e.strip()]
    )


def int_to_bool(v: int | float) -> bool:
    """
    Given an integer, convert it to bool.
    If the integer is 1, return True, otherwise, return False.

    Will raise an exception if the provided value cannot be cast to an integer.
    :param v:
    :exceptions: ValueError, TypeError
    :return: True or False
    """
    return int(v) == 1


def int_or_none(s: int | float | str | None) -> int | None:
    """
    Parses the input value and attempts to convert it into an integer. If the
    input is invalid (such as being non-numeric), `None` is returned. If the
    input is `-1` or `None`, it also returns `None`. Otherwise, the integer
    value of the input is returned.

    :param s: The input value to be parsed. Can be of type `int`, `float`, `str`,
        or `None`.
    :return: Returns the integer value of the input if successful. If the input
        is invalid, equal to `-1`, or `None`, it returns `None`.
    """
    if s is None:
        return None
    try:
        if int(s) == -1:
            return None
        else:
            return int(s)
    except ValueError:
        return None


def choices_code_to_string(
    choices: ChoicesType, default: str | None = None, to_slug: bool = False
) -> Callable[[Union[int, StringLike]], StringLike | None]:
    """
    Converts a code to a corresponding string representation based on provided choices.
    The function allows optional fallback to a default value and can slugify the resulting string
    if required.

    :param choices: A mapping of codes to string representations.
    :type choices: ChoicesType

    :param default: An optional default string to be returned if the code is not found in the choices.
    :type default: str | None

    :param to_slug: Specifies whether the resulting string should be slugified. If True, the string
                    representation is converted to a slug with hyphens replaced by underscores.
    :type to_slug: bool

    :return: A callable function that takes an input (code) and returns the corresponding string
             representation or the default value. If to_slug is True, it returns the slugified version
             instead.
    :rtype: Callable[[Union[int, str]], str | None]
    """
    dict_map = dict(choices)

    def f(code):
        return dict_map.get(code, default)

    def s(code):
        return slugify(dict_map.get(code, default)).replace("-", "_")

    return s if to_slug else f


def choices_string_to_code(
    choices: ChoicesType, default: Any = None, to_lower: bool = False
) -> Callable[[str], Union[int, str, None]]:
    """
    Converts a dictionary of choices into a callable function that maps input strings
    to their corresponding codes. This helper function is particularly useful for handling
    mappings where string keys need to be converted into codes, while optionally allowing
    the input to be case-insensitive.

    :param choices: A dictionary-like object or sequence of tuples representing the choices.
    :param default: Optional value returned if the input string does not match any key. Defaults to None.
    :param to_lower: A boolean indicating whether to convert keys in the choice dictionary
                     and input string to lowercase for case-insensitive mapping. Defaults to False.
    :return: A callable function that accepts a string input and returns the corresponding code from
             the dictionary, or the default value if the input does not match.
    """
    if to_lower:
        dict_map = {v.lower(): k for k, v in dict(choices).items()}
    else:
        dict_map = {v: k for k, v in dict(choices).items()}

    def f(word):
        return dict_map.get(word, default)

    return f


def none_or_empty(s=None):
    """
    Check if the given thing is not empty and not None
    :param s:
    :return:
    """
    if s is None:
        return True
    if s.strip() == "":
        return True
    return False
