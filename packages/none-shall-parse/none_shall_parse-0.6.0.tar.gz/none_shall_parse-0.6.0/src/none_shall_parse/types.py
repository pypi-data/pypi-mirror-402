from datetime import datetime, date
from typing import Protocol, Sequence, Tuple, Union, TypeVar

from pendulum import DateTime, Date


class StringLike(Protocol):
    """
    Protocol that defines the expected behavior for string-like objects.

    This protocol specifies the methods and properties that an object
    must implement to be considered string-like. It defines basic
    string operations such as getting the string representation and
    length, string concatenation, containment checks, and several
    commonly used string manipulation methods. Objects adhering to
    this protocol can mimic the behavior of standard Python strings.
    """

    def __str__(self) -> str: ...
    def __len__(self) -> int: ...
    def __add__(self, other: str) -> str: ...
    def __contains__(self, item: str) -> bool: ...

    # Most commonly used string methods
    def upper(self) -> str: ...
    def lower(self) -> str: ...
    def strip(self) -> str: ...
    def startswith(self, prefix: str) -> bool: ...
    def endswith(self, suffix: str) -> bool: ...
    def replace(self, old: str, new: str) -> str: ...


ChoicesType = Sequence[Tuple[Union[int, str], StringLike]]

DateLike = Union[Date, date]

DateTimeLike = Union[DateTime, datetime]

DateTimeOrDateLike = Union[DateTimeLike, DateLike]

T = TypeVar("T")
