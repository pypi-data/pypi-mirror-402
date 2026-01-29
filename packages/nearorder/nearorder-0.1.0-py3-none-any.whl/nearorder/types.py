from typing import Callable, Literal, TypeVar

T = TypeVar("T")

Order = Literal["asc", "desc"]
Cmp = Callable[[T, T], int]
